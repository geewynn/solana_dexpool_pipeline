# src/protocols/orca.py
import asyncio
import logging
from datetime import datetime
from time import time  # no blocking sleep
from typing import List

from dotenv import load_dotenv
from httpx import HTTPStatusError
from orca_whirlpool.accounts import AccountFetcher, AccountFinder
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
from solana.exceptions import SolanaRpcException
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey
from tenacity import (
    AsyncRetrying,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from dex_dagster.ingestion.src.common.constants import (
    ORCA_STORAGE_KEY,
    ORCA_WHIRLPOOL_PROGRAM,
)
from dex_dagster.ingestion.src.common.serializers import (
    serialize_position,
    serialize_tick_array,
    serialize_token_accounts,
    serialize_whirlpool,
)
from dex_dagster.ingestion.src.common.utility import (
    get_s3_bucket,
    get_timestamp,
    upload_to_s3,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dex")
load_dotenv()

POOL_ACCOUNT_SIZE = 653
TOKEN_MINT_A_OFFSET = 101
TOKEN_MINT_B_OFFSET = 181
PROGRAM_ID = ORCA_WHIRLPOOL_PROGRAM  # Pubkey object


SyncRetry = retry(
    retry=retry_if_exception_type((SolanaRpcException, HTTPStatusError)),
    wait=wait_exponential(multiplier=0.8, min=1, max=30),
    stop=stop_after_attempt(6),
    reraise=True,
)


@SyncRetry
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

    for acc in client.get_program_accounts(
        PROGRAM_ID, commitment=Processed, filters=filters_base
    ).value:
        found.add(str(acc.pubkey))

    for acc in client.get_program_accounts(
        PROGRAM_ID, commitment=Processed, filters=filters_quote
    ).value:
        found.add(str(acc.pubkey))

    logger.info(f"Found {len(found)} matching Orca pools for mint {token_mint}")
    return list(found)


rpc_limiter = asyncio.Semaphore(10)  # max 30 concurrent RPCs


async def with_retry(func, *args, **kwargs):
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type((SolanaRpcException, HTTPStatusError)),
        wait=wait_exponential(multiplier=0.8, min=1, max=30),
        stop=stop_after_attempt(6),
        reraise=True,
    ):
        with attempt:
            async with rpc_limiter:
                return await func(*args, **kwargs)


async def run_orca(token: str, rpc_url: str) -> None:

    pool_addresses = fetch_pool_addresses(rpc_url, token)
    if not pool_addresses:
        logger.info("No pools found for token.")
        return

    connection = AsyncClient(rpc_url)
    fetcher = AccountFetcher(connection)
    finder = AccountFinder(connection)

    pool_rows: list[dict] = []
    tick_rows: list[dict] = []
    position_rows: list[dict] = []

    extraction_time = str(datetime.now())
    # logger.info(extraction_time)

    for addr in pool_addresses:
        pubkey = Pubkey.from_string(addr)
        try:
            whirlpool = await with_retry(fetcher.get_whirlpool, pubkey)
            tick_arrays_data = await with_retry(
                finder.find_tick_arrays_by_whirlpool, ORCA_WHIRLPOOL_PROGRAM_ID, pubkey
            )
            token_vault_a = await with_retry(
                fetcher.get_token_account, whirlpool.token_vault_a
            )
            token_vault_b = await with_retry(
                fetcher.get_token_account, whirlpool.token_vault_b
            )
            positions_data = await with_retry(
                finder.find_positions_by_whirlpool, ORCA_WHIRLPOOL_PROGRAM_ID, pubkey
            )

            position_rows.extend(
                {**serialize_position(p), "extraction_timestamp": extraction_time}
                for p in positions_data
            )

            pool_rows.append(
                {
                    "whirlpool": serialize_whirlpool(whirlpool, pubkey, token),
                    "token_vault_a_amount": serialize_token_accounts(token_vault_a),
                    "token_vault_b_amount": serialize_token_accounts(token_vault_b),
                    "extraction_timestamp": extraction_time,
                }
            )

            tick_rows.append(
                {
                    "pool": str(pubkey),
                    "tick_arrays": [
                        serialize_tick_array(ta) for ta in tick_arrays_data
                    ],
                    "extraction_timestamp": extraction_time,
                }
            )

            logger.info(
                f"{addr[:6]}…  tick_arrays={len(tick_arrays_data):<3} "
                f"positions={len(positions_data):<4}"
            )

        except Exception as exc:
            logger.info(f"Failed to fetch {addr}: {exc}")

    timestamp = get_timestamp()
    bucket = get_s3_bucket()

    key_pool = f"{ORCA_STORAGE_KEY}/pool/{token}_{timestamp}_pools.json"
    key_tick = f"{ORCA_STORAGE_KEY}/tick/{token}_{timestamp}_ticks.json"
    key_position = f"{ORCA_STORAGE_KEY}/position/{token}_{timestamp}_positions.json"

    upload_to_s3(bucket=bucket, key=key_pool, data=pool_rows)
    upload_to_s3(bucket=bucket, key=key_tick, data=tick_rows)
    upload_to_s3(bucket=bucket, key=key_position, data=position_rows)
    await connection.close()
