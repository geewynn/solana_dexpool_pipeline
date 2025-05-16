import os

from solders.pubkey import Pubkey

RAYDIUM_RPC = os.getenv("rpc_url")
ORCA_RPC = os.getenv("orca_rpc_url")
RAYDIUM_STORAGE_KEY =str(os.getenv("RAYDIUM_STORAGE_KEY"))
ORCA_STORAGE_KEY = str(os.getenv("ORCA_STORAGE_KEY"))
# print(f"Default RPC URL: {RAYDIUM_RPC}")

RAYDIUM_CLMM_PROGRAM = Pubkey.from_string(
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
)
ORCA_WHIRLPOOL_PROGRAM = Pubkey.from_string(
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
)
TOKEN_MINT = "USDSwr9ApdHk5bvJKMjzff41FfuX8bSxdKcR81vTwcA"

S3_BUCKET = os.getenv("STORAGE_BUCKET_NAME")
