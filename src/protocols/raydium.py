# src/protocols/raydium.py
import struct
from datetime import datetime
from time import sleep
from typing import Dict, List, Optional

from dotenv import load_dotenv
from tenacity import (
    retry, retry_if_exception_type,
    wait_exponential, stop_after_attempt
)
from httpx import HTTPStatusError
from solana.exceptions import SolanaRpcException
from solana.rpc.api import Client
from solana.rpc.commitment import Processed
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey

from decoders.raydium_decoder import AnchorRaydiumDecoder
from common.utility import get_s3_bucket, get_timestamp, upload_to_s3

load_dotenv()

PROTOCOL_POSITION_SIZE = 225
POOL_ID_OFFSET = 9
TICK_ARRAY_SIZE = 60
POOL_ACCOUNT_SIZE = 1544
TOKEN_MINT_A_OFFSET = 73
TOKEN_MINT_B_OFFSET = 105


class RaydiumDataFetcher:
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.client = Client(rpc_url)
        self.decoder = AnchorRaydiumDecoder(rpc_url)
        self.PROGRAM_ID = Pubkey.from_string(
            "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
        )

    def initialize(self) -> None:
        self.decoder.initialize()

    SyncRetry = retry(
        retry=retry_if_exception_type((SolanaRpcException, HTTPStatusError)),
        wait=wait_exponential(multiplier=0.8, min=1, max=30),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    @SyncRetry
    def fetch_pools_for_token(
        self,
        token_mint: str,
        quote_offset: int,
        base_offset: int,
        data_length: int,
    ) -> List[str]:
        memcmp_base  = MemcmpOpts(offset=base_offset, bytes=token_mint)
        memcmp_quote = MemcmpOpts(offset=quote_offset, bytes=token_mint)
        found = set()

        resp_base = self.client.get_program_accounts(
            self.PROGRAM_ID,
            commitment=Processed,
            filters=[data_length, memcmp_base],
        )
        for account in resp_base.value:
            found.add(str(account.pubkey))

        resp_quote = self.client.get_program_accounts(
            self.PROGRAM_ID,
            commitment=Processed,
            filters=[data_length, memcmp_quote],
        )
        for account in resp_quote.value:
            found.add(str(account.pubkey))

        return list(found)

    # ---------- PDA helpers --------------------------------------
    @staticmethod
    def get_array_start_index(tick_index: int, tick_spacing: int) -> int:
        ticks_in_array = TICK_ARRAY_SIZE * tick_spacing
        start = tick_index // ticks_in_array
        if tick_index < 0 and tick_index % ticks_in_array != 0:
            start -= 1
        return start * ticks_in_array

    def get_extension_address(self, pool_id: Pubkey) -> str:
        seeds = [b"pool_tick_array_bitmap_extension", bytes(pool_id)]
        address, _ = Pubkey.find_program_address(seeds, self.PROGRAM_ID)
        return str(address)

    def get_tick_array_address(self, pool_id: Pubkey, start_index: int) -> str:
        seed_index = struct.pack(">i", start_index)
        seeds = [b"tick_array", bytes(pool_id), seed_index]
        pda, _ = Pubkey.find_program_address(seeds, self.PROGRAM_ID)
        return str(pda)

    def get_account_data(self, address: str) -> Optional[Dict]:
        try:
            pubkey = Pubkey.from_string(address)
            response = self.client.get_account_info(pubkey)
            if not response.value:
                print(f"No account data found for {address}")
                return None
            return self.decoder.decode_account(response.value.data, address)
        except Exception as exc:
            print(f"Error fetching account {address}: {exc}")
            return None

    @SyncRetry
    def fetch_protocol_positions(self, pool_pubkey: str) -> List[dict]:
        pool_key = Pubkey.from_string(pool_pubkey)
        filters = [
            PROTOCOL_POSITION_SIZE,
            MemcmpOpts(offset=POOL_ID_OFFSET, bytes=str(pool_key)),
        ]
        resp = self.client.get_program_accounts(
            self.PROGRAM_ID, commitment=Processed, filters=filters
        )

        decoded: List[dict] = []
        for acct in resp.value:
            dec = self.decoder.decode_account(acct.account.data, str(acct.pubkey))
            if "error" not in dec:
                decoded.append(dec["parsed"]["data"])
        return decoded

    @SyncRetry
    def fetch_personal_positions(self, pool_pubkey: str) -> list[dict]:
        pool_key = Pubkey.from_string(pool_pubkey)
        filters = [281, MemcmpOpts(offset=41, bytes=str(pool_key))]

        resp = self.client.get_program_accounts(
            self.PROGRAM_ID,
            commitment=Processed,
            filters=filters,
        )
        decoded: list[dict] = []
        for acct in resp.value:
            parsed = self.decoder.decode_account(acct.account.data, str(acct.pubkey))
            if parsed and "error" not in parsed:
                decoded.append(parsed["parsed"]["data"])
        return decoded

    @SyncRetry
    def fetch_pool_data(self, pool_address: str) -> Dict:
        pool_account = self.get_account_data(pool_address)
        if not pool_account or "error" in pool_account:
            return {"error": "Failed to fetch pool data"}

        try:
            data = pool_account["parsed"]["data"]
            current_tick = int(data["tickCurrent"])
            tick_spacing = int(data["tickSpacing"])
            bitmap = data.get("tickArrayBitmap", [])

            token_vault0 = data["tokenVault0"]
            token_vault1 = data["tokenVault1"]

            token_vault0_balance = self.client.get_token_account_balance(
                Pubkey.from_string(token_vault0)
            )
            token_vault1_balance = self.client.get_token_account_balance(
                Pubkey.from_string(token_vault1)
            )

            pool_pubkey = Pubkey.from_string(pool_address)
            ext_addr = self.get_extension_address(pool_pubkey)
            ext_data = self.get_account_data(ext_addr)

            bitmap_ints = [int(w) for w in bitmap]
            ticks_per_array = TICK_ARRAY_SIZE * tick_spacing
            initialized = []
            total_bits = len(bitmap_ints) * 64
            mid = total_bits // 2
            for bit in range(total_bits):
                if (bitmap_ints[bit // 64] >> (bit % 64)) & 1:
                    start_idx = (bit - mid) * ticks_per_array
                    initialized.append(start_idx)

            tick_arrays = {}
            for start in initialized:
                arr_addr = self.get_tick_array_address(pool_pubkey, start)
                arr_data = self.get_account_data(arr_addr)
                if arr_data and "error" not in arr_data:
                    tick_arrays[arr_addr] = arr_data
                sleep(0.3)

            return {
                "timestamp": str(datetime.now()),
                "pool": pool_account,
                "tickArrays": tick_arrays,
                "extension": ext_data,
                "currentTick": current_tick,
                "tickSpacing": tick_spacing,
                "currentArrayStart": self.get_array_start_index(
                    current_tick, tick_spacing
                ),
                "tokenVault0": {
                    "address": token_vault0,
                    "balance": token_vault0_balance.value.amount,
                    "decimals": token_vault0_balance.value.decimals,
                    "amount": token_vault0_balance.value.ui_amount_string,
                },
                "tokenVault1": {
                    "address": token_vault1,
                    "balance": token_vault1_balance.value.amount,
                    "decimals": token_vault1_balance.value.decimals,
                    "amount": token_vault1_balance.value.ui_amount_string,
                },
            }
        except Exception as exc:
            print(f"Error processing pool {pool_address}: {exc}")
            return {"error": str(exc)}

    def run(self, token: str,
            quote_offset: int,
            base_offset: int,
            length: int) -> None:

        pools = self.fetch_pools_for_token(token, quote_offset, base_offset, length)
        extraction_time = str(datetime.now())
        print(extraction_time)

        print(f"Found {len(pools)} pools for token {token}")

        pool_rows: list[dict]      = []
        tick_rows: list[dict]      = []
        proto_pos_rows: list[dict] = []
        pers_pos_rows:  list[dict] = []

        for p in pools:
            print(f"\n── {p}")
            
            proto_pos = self.fetch_protocol_positions(p)
            if proto_pos:
                proto_pos_rows.extend(
                    {**pos, "extraction_timestamp": extraction_time}
                    for pos in proto_pos
                )
            else:
                print("no protocol positions")

            pers_pos = self.fetch_personal_positions(p)
            if pers_pos:
                pers_pos_rows.extend(
                    {**pos, "extraction_timestamp": extraction_time}
                    for pos in pers_pos
                )
            else:
                print("no personal positions")

            pool_blob = self.fetch_pool_data(p)
            if pool_blob and "error" not in pool_blob:
                tick_rows.append({
                    "pool": p,
                    "tickArrays": pool_blob.pop("tickArrays", {}),
                    "extraction_timestamp": extraction_time
                })
                pool_blob["extraction_timestamp"] = extraction_time
                pool_rows.append(pool_blob)
            else:
                print(f"Failed pool fetch: {pool_blob}")

            sleep(0.7)

        timestamp = get_timestamp()
        bucket    = get_s3_bucket()

        key_pool            = f"raydium_raw_new/pool/{token}_{timestamp}_pools.json"
        key_tick            = f"raydium_raw_new/tick/{token}_{timestamp}_ticks.json"
        key_proto_position  = f"raydium_raw_new/protocol_position/{token}_{timestamp}_protocol_position.json"
        key_pers_position   = f"raydium_raw_new/personal_position/{token}_{timestamp}_personal_position.json"

        upload_to_s3(bucket, key_pool,           pool_rows)
        upload_to_s3(bucket, key_tick,           tick_rows)
        upload_to_s3(bucket, key_proto_position, proto_pos_rows)
        upload_to_s3(bucket, key_pers_position,  pers_pos_rows)


def run_raydium(token: str, rpc_url: str) -> None:
    fetcher = RaydiumDataFetcher(rpc_url)
    fetcher.initialize()
    fetcher.run(token, TOKEN_MINT_A_OFFSET, TOKEN_MINT_B_OFFSET, POOL_ACCOUNT_SIZE)
