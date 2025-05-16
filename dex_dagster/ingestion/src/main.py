import asyncio

from common.constants import ORCA_RPC, RAYDIUM_RPC, TOKEN_MINT
from dotenv import load_dotenv
from protocols.orca import run_orca
from protocols.raydium import run_raydium

load_dotenv()


def main():

    print("Fetching from Raydium...")
    run_raydium(TOKEN_MINT, RAYDIUM_RPC)

    print("Fetching from Orca...")
    asyncio.run(run_orca(TOKEN_MINT, ORCA_RPC))


if __name__ == "__main__":
    main()
