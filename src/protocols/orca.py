from time import sleep
from typing import List

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from dotenv import load_dotenv
from orca_whirlpool.accounts import AccountFetcher, AccountFinder
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey
from solana.exceptions import SolanaRpcException

from common.constants import ORCA_WHIRLPOOL_PROGRAM
from common.serializers import (serialize_position, serialize_tick_array,
                                    serialize_token_accounts,
                                    serialize_whirlpool)
from common.utility import get_s3_bucket, get_timestamp, upload_to_s3

load_dotenv()

# Whirlpool layout constants
POOL_ACCOUNT_SIZE = 653
TOKEN_MINT_A_OFFSET = 101
TOKEN_MINT_B_OFFSET = 181
PROGRAM_ID = ORCA_WHIRLPOOL_PROGRAM


# Fetch pools matching token mint
@retry(
    retry=retry_if_exception_type(SolanaRpcException),   # only RPC errors
    wait=wait_exponential(multiplier=0.8, min=1, max=30),# 1s → 2s → 4s …
    stop=stop_after_attempt(6),                          # give up after 6 tries
    reraise=True,
)
def fetch_pool_addresses(rpc_url: str, token_mint: str) -> List[str]:
    client = Client(rpc_url)
    found = set()

    filters_base = [
        POOL_ACCOUNT_SIZE,
        MemcmpOpts(offset=TOKEN_MINT_A_OFFSET, bytes=token_mint),
    ]
    filters_quote = [
        POOL_ACCOUNT_SIZE,
        MemcmpOpts(offset=TOKEN_MINT_B_OFFSET, bytes=token_mint),
    ]

    resp_base = client.get_program_accounts(
        PROGRAM_ID, commitment=Processed, filters=filters_base
    )
    for acc in resp_base.value:
        found.add(str(acc.pubkey))

    resp_quote = client.get_program_accounts(
        PROGRAM_ID, commitment=Processed, filters=filters_quote
    )
    for acc in resp_quote.value:
        found.add(str(acc.pubkey))

    print(f"Found {len(found)} matching pools.")
    # print(len(found))
    return list(found)


async def run_orca(token: str, rpc_url: str):
    pool_addresses = fetch_pool_addresses(rpc_url, token)
    if not pool_addresses:
        print("No pools found for token.")
        return

    conn = AsyncClient(rpc_url)
    fetcher = AccountFetcher(conn)
    finder = AccountFinder(conn)

    pool_rows: list[dict] = []  # pool‑level, no ticks
    tick_rows: list[dict] = []  # tick arrays only
    position_rows: list[dict] = []  # personal positions

    for addr in pool_addresses:
        pubkey = Pubkey.from_string(addr)
        try:
            whirlpool = await fetcher.get_whirlpool(pubkey)
            tick_arrays_data = await finder.find_tick_arrays_by_whirlpool(
                ORCA_WHIRLPOOL_PROGRAM_ID, pubkey
            )
            token_vault_a = await fetcher.get_token_account(whirlpool.token_vault_a)
            token_vault_b = await fetcher.get_token_account(whirlpool.token_vault_b)

            # personal positions
            positions_data = await finder.find_positions_by_whirlpool(
                ORCA_WHIRLPOOL_PROGRAM_ID, pubkey
            )
            position_rows.extend(serialize_position(p) for p in positions_data)

            # pool row (minus tick arrays)
            pool_rows.append(
                {
                    "whirlpool": serialize_whirlpool(whirlpool, pubkey, token),
                    "token_vault_a_amount": serialize_token_accounts(token_vault_a),
                    "token_vault_b_amount": serialize_token_accounts(token_vault_b),
                }
            )

            # tick arrays with pool id for join
            tick_rows.append(
                {
                    "pool": str(pubkey),
                    "tick_arrays": [serialize_tick_array(ta) for ta in tick_arrays_data],
                }
            )

            print(f"{addr}: {len(tick_arrays_data)} tick arrays, {len(positions_data)} positions")
            sleep(0.8)

        except Exception as e:
            print(f"Failed to fetch {addr}: {e}")

    # ── upload three separate objects ─────────────────────────────────
    ts = get_timestamp() 
    bucket = get_s3_bucket()
    key_pool = f"orca_raw/pool/{token}_{ts}.json"
    key_tick = f"orca_raw/tick/{token}_{ts}.json"
    key_position = f"orca_raw/position/{token}_{ts}.json"

    upload_to_s3(bucket, key_pool, pool_rows)
    upload_to_s3(bucket, key_tick, tick_rows)
    upload_to_s3(bucket, key_position, position_rows)

    print("uploaded", key_pool, key_tick, key_position, sep="\n ‣ ")

    await conn.close()
