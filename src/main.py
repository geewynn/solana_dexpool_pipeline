import asyncio
from protocols.raydium import run_raydium
from protocols.orca import run_orca
from common.constants import TOKEN_MINT, DEFAULT_RPC
from dotenv import load_dotenv
import os


load_dotenv()
def main():

    # print("Fetching from Raydium...")
    # run_raydium(TOKEN_MINT, DEFAULT_RPC)

    print("Fetching from Orca...")
    asyncio.run(run_orca(TOKEN_MINT, DEFAULT_RPC))

if __name__ == "__main__":
    main()
