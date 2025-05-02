import asyncio
import json
from typing import List
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.api import Client
from solana.rpc.types import MemcmpOpts
from solana.rpc.commitment import Processed

from orca_whirlpool.accounts import AccountFinder, AccountFetcher
from orca_whirlpool.constants import ORCA_WHIRLPOOL_PROGRAM_ID
# from decoders.orca_decoder import AnchorWhirlpoolDecoder
from time import sleep

from utility import get_s3_bucket, get_timestamp, upload_to_s3
from dotenv import load_dotenv

load_dotenv()

# Whirlpool layout constants
POOL_ACCOUNT_SIZE = 653
TOKEN_MINT_A_OFFSET = 101
TOKEN_MINT_B_OFFSET = 181
PROGRAM_ID = Pubkey.from_string("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc")

# Serialization utils
def serialize_whirlpool_reward_info(reward_info):
    return {
        "mint": str(reward_info.mint),
        "vault": str(reward_info.vault),
        "authority": str(reward_info.authority),
        "emissions_per_second_x64": str(reward_info.emissions_per_second_x64),
        "growth_global_x64": str(reward_info.growth_global_x64),
    }

def serialize_whirlpool(whirlpool, whirlpool_pubkey, token):
    return {
        "pubkey": str(whirlpool_pubkey),
        "token": token,
        "whirlpools_config": str(whirlpool.whirlpools_config),
        "whirlpool_bump": [int(b) for b in whirlpool.whirlpool_bump],
        "tick_spacing": whirlpool.tick_spacing,
        "tick_spacing_seed": [int(s) for s in whirlpool.tick_spacing_seed],
        "fee_rate": whirlpool.fee_rate,
        "protocol_fee_rate": whirlpool.protocol_fee_rate,
        "liquidity": str(whirlpool.liquidity),
        "sqrt_price": str(whirlpool.sqrt_price),
        "tick_current_index": whirlpool.tick_current_index,
        "protocol_fee_owed_a": str(whirlpool.protocol_fee_owed_a),
        "protocol_fee_owed_b": str(whirlpool.protocol_fee_owed_b),
        "token_mint_a": str(whirlpool.token_mint_a),
        "token_vault_a": str(whirlpool.token_vault_a),
        "fee_growth_global_a": str(whirlpool.fee_growth_global_a),
        "token_mint_b": str(whirlpool.token_mint_b),
        "token_vault_b": str(whirlpool.token_vault_b),
        "fee_growth_global_b": str(whirlpool.fee_growth_global_b),
        "reward_last_updated_timestamp": whirlpool.reward_last_updated_timestamp,
        "reward_infos": [serialize_whirlpool_reward_info(ri) for ri in whirlpool.reward_infos],
    }

def serialize_tick_array(tick_array):
    return {
        "pubkey": str(tick_array.pubkey),
        "start_tick_index": tick_array.start_tick_index,
        "ticks": [
            {
                "initialized": tick.initialized,
                "liquidity_net": str(tick.liquidity_net),
                "liquidity_gross": str(tick.liquidity_gross),
                "fee_growth_outside_a": str(tick.fee_growth_outside_a),
                "fee_growth_outside_b": str(tick.fee_growth_outside_b),
                "reward_growths_outside": [str(g) for g in tick.reward_growths_outside],
            }
            for tick in tick_array.ticks
        ],
        "whirlpool": str(tick_array.whirlpool),
    }

# Fetch pools matching token mint
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

    resp_base = client.get_program_accounts(PROGRAM_ID, commitment=Processed, filters=filters_base)
    for acc in resp_base.value:
        found.add(str(acc.pubkey))

    resp_quote = client.get_program_accounts(PROGRAM_ID, commitment=Processed, filters=filters_quote)
    for acc in resp_quote.value:
        found.add(str(acc.pubkey))

    print(f"Found {len(found)} matching pools.")
    print(len(found))
    return list(found)


async def run_orca(token, rpc_url):
    pool_addresses = fetch_pool_addresses(rpc_url, token)

    if not pool_addresses:
        print("No pools found for token.")
        return

    connection = AsyncClient(rpc_url)
    fetcher = AccountFetcher(connection)
    finder = AccountFinder(connection)

    all_data = []

    for address in pool_addresses:
        whirlpool_pubkey = Pubkey.from_string(address)
        try:
            whirlpool = await fetcher.get_whirlpool(whirlpool_pubkey)
            tick_arrays = await finder.find_tick_arrays_by_whirlpool(
                ORCA_WHIRLPOOL_PROGRAM_ID, whirlpool_pubkey
            )

            data = {
                "whirlpool": serialize_whirlpool(whirlpool, whirlpool_pubkey, token),
                "tick_arrays": [serialize_tick_array(ta) for ta in tick_arrays],
            }

            all_data.append(data)
            print(f"Collected {address} with {len(tick_arrays)} tick arrays.")
            sleep(0.5)

        except Exception as e:
            print(f"Failed to fetch data for {address}: {e}")


    # Build S3 key
    timestamp = get_timestamp()
    bucket = get_s3_bucket()
    key = f"orca/raydium_clmm_{token}_{timestamp}.json"

    # Upload
    upload_to_s3(bucket=bucket, key=key, data=all_data)


    await connection.close()
