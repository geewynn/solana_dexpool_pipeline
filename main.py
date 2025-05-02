import asyncio
from raydium import run_raydium
from orca import run_orca
from dotenv import load_dotenv
import os

load_dotenv()
def main():
    token = os.getenv("token")
    rpc_url = os.getenv("rpc_url")

    print("Fetching from Raydium...")
    run_raydium(token, rpc_url)

    print("Fetching from Orca...")
    asyncio.run(run_orca(token, rpc_url))

if __name__ == "__main__":
    main()
