from datetime import datetime, time
import json
from time import sleep
import struct
from typing import List, Dict, Optional, Union

from solana.rpc.api import Client
from solana.rpc.types import MemcmpOpts
from solana.rpc.commitment import Processed
from solders.pubkey import Pubkey

from decoders.raydium_decoder import AnchorRaydiumDecoder

from utility import upload_to_s3, get_timestamp, get_s3_bucket #, upload_to_storage
from dotenv import load_dotenv

load_dotenv()


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
        # Decoder initialization is synchronous after async init
        # assuming AnchorRaydiumDecoder supports sync init
        self.decoder.initialize()

    def fetch_pools_for_token(
        self,
        token_mint: str,
        quote_offset: int,
        base_offset: int,
        data_length: int,
    ) -> List[str]:
        """
        Find all pool PDAs where either base or quote equals token_mint.
        """
        memcmp_base = MemcmpOpts(offset=base_offset, bytes=token_mint)
        memcmp_quote = MemcmpOpts(offset=quote_offset, bytes=token_mint)
        found = set()

        # Query pools where base matches
        resp_base = self.client.get_program_accounts(
            self.PROGRAM_ID,
            commitment=Processed,
            filters=[data_length, memcmp_base],
        )
    
        for account in resp_base.value:
            found.add(str(account.pubkey))

        # Query pools where quote matches
        resp_quote = self.client.get_program_accounts(
            self.PROGRAM_ID,
            commitment=Processed,
            filters=[data_length, memcmp_quote],
        )
        for account in resp_quote.value:
            found.add(str(account.pubkey))
        return list(found)

    def get_array_start_index(self, tick_index: int, tick_spacing: int) -> int:
        ticks_in_array = TICK_ARRAY_SIZE * tick_spacing
        start = tick_index // ticks_in_array
        if tick_index < 0 and tick_index % ticks_in_array != 0:
            start -= 1
        return start * ticks_in_array

    def get_extension_address(self, pool_id: Pubkey) -> str:
        seeds = [b"pool_tick_array_bitmap_extension", bytes(pool_id)]
        address, _ = Pubkey.find_program_address(seeds, self.PROGRAM_ID)
        return str(address)

    def get_tick_array_address(
        self,
        pool_id: Pubkey,
        start_index: int,
    ) -> str:
        seed_index = struct.pack(
            ">i", start_index
        )
        seeds = [b"tick_array", bytes(pool_id), seed_index]
        pda, _ = Pubkey.find_program_address(seeds, self.PROGRAM_ID)
        return str(pda)
        
    def get_account_data(self, address: str) -> Optional[Dict]:
        try:
            # print(f"Fetching account data for {address}")
            pubkey = Pubkey.from_string(address)
            response = self.client.get_account_info(pubkey)
            if not response.value:
                print(f"No account data found for {address}")
                return None
            decoded = self.decoder.decode_account(response.value.data, address)
            return decoded
        except Exception as e:
            print(f"Error fetching account {address}: {e}")
            return None

    def fetch_pool_data(self, pool_address: str) -> Dict:
        pool_account = self.get_account_data(pool_address)
        if not pool_account or "error" in pool_account:
            return {"error": "Failed to fetch pool data"}

        try:
            data = pool_account['parsed']['data']
            current_tick = int(data["tickCurrent"])
            tick_spacing = int(data["tickSpacing"])
            bitmap = data.get("tickArrayBitmap", [])

            # Fetch extension bitmap
            pool_pubkey = Pubkey.from_string(pool_address)
            ext_addr = self.get_extension_address(pool_pubkey)
            ext_data = self.get_account_data(ext_addr)

            # Parse bitmap words
            bitmap_ints = [int(w) for w in bitmap]
            TICKS_PER_ARRAY = TICK_ARRAY_SIZE * tick_spacing
            initialized = []
            total_bits = len(bitmap_ints) * 64
            mid = total_bits // 2
            for bit in range(total_bits):
                if (bitmap_ints[bit // 64] >> (bit % 64)) & 1:
                    start_idx = (bit - mid) * TICKS_PER_ARRAY
                    initialized.append(start_idx)

            # Fetch tick arrays
            tick_arrays = {}
            for start in initialized:
                arr_addr = self.get_tick_array_address(pool_pubkey, start)
                arr_data = self.get_account_data(arr_addr)
                if arr_data and "error" not in arr_data:
                    tick_arrays[arr_addr] = arr_data
                sleep(0.3)
            result = {
                "timestamp": str(datetime.now()),
                "pool": pool_account,
                "tickArrays": tick_arrays,
                "extension": ext_data,
                "currentTick": current_tick,
                "tickSpacing": tick_spacing,
                "currentArrayStart": self.get_array_start_index(current_tick, tick_spacing)
            }
            return result
        except Exception as e:
            print(f"Error processing pool data: {e}")
            return {"error": str(e)}
        

    def run(self, token: str, quote_offset: int, base_offset: int, length: int) -> None:
        pools = self.fetch_pools_for_token(token, quote_offset, base_offset, length)
        print(f"Found {len(pools)} pools for token {token}")

        collected = []
        for p in pools:
            res = self.fetch_pool_data(p)
            if res and "error" not in res:
                collected.append(res)
            else:
                print(f"Failed fetching pool {p}: {res}")
        sleep(0.3)

        # Build S3 key
        timestamp = get_timestamp()
        bucket = get_s3_bucket()
        key = f"raydiums/raydium_clmm_{token}_{timestamp}.json"

        # Upload
        upload_to_s3(bucket=bucket, key=key, data=collected)


def run_raydium(token, rpc_url):
    fetcher = RaydiumDataFetcher(rpc_url)
    fetcher.initialize()
    fetcher.run(token, TOKEN_MINT_A_OFFSET, TOKEN_MINT_B_OFFSET, POOL_ACCOUNT_SIZE)

