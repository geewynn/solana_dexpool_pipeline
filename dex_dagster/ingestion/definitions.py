import dagster as dg
from dagster_aws.s3 import S3Resource

from dex_dagster.ingestion.src.common.utility import get_timestamp
from dex_dagster.ingestion.src.protocols.orca import run_orca
from dex_dagster.ingestion.src.protocols.raydium import run_raydium

# pull secrets from the environment so they never appear in logs
s3_resource = S3Resource(
    aws_access_key_id=dg.EnvVar("STORAGE_ACCESS_KEY"),
    aws_secret_access_key=dg.EnvVar("STORAGE_SECRET_KEY"),
    region_name="auto",
)


class SolanaConfig(dg.ConfigurableResource):
    token_mint: str = dg.EnvVar("token")
    raydium_rpc: str = dg.EnvVar("rpc_url")
    orca_rpc: str = dg.EnvVar("orca_rpc_url")


solana_config = SolanaConfig()


AWS_BUCKET = dg.EnvVar("STORAGE_BUCKET_NAME")
RAYDIUM_STORAGE_KEY = dg.EnvVar("RAYDIUM_STORAGE_KEY").get_value()
ORCA_STORAGE_KEY = dg.EnvVar("ORCA_STORAGE_KEY").get_value()


@dg.asset(
    group_name="solana_ingestion",
    automation_condition=dg.AutomationCondition.on_cron("*/10 * * * *"),
    kinds={"python"},
)
def raydium_snapshot(
    solana: SolanaConfig,
) -> dg.MaterializeResult:
    """
    Calls `run_raydium` (writes a set of JSON files to S3)
    then records the filenames as Dagster metadata.
    """
    run_raydium(solana.token_mint, solana.raydium_rpc)

    ts = get_timestamp()
    meta = {
        "pool_key": f"{RAYDIUM_STORAGE_KEY}/pool/{solana.token_mint}_{ts}_pools.json",
        "tick_key": f"{RAYDIUM_STORAGE_KEY}/tick/{solana.token_mint}_{ts}_ticks.json",
        "protocol_pos_key": f"{RAYDIUM_STORAGE_KEY}/protocol_position/{solana.token_mint}_{ts}_protocol_position.json",
        "personal_pos_key": f"{RAYDIUM_STORAGE_KEY}/personal_position/{solana.token_mint}_{ts}_personal_position.json",
    }
    return dg.MaterializeResult(metadata=meta)


@dg.asset(
    group_name="solana_ingestion",
    automation_condition=dg.AutomationCondition.on_cron("*/10 * * * *"),
    kinds={"python"},
)
def orca_snapshot(
    solana: SolanaConfig,
) -> dg.MaterializeResult:
    """Same idea for Orca."""
    import asyncio

    asyncio.run(run_orca(solana.token_mint, solana.orca_rpc))

    ts = get_timestamp()
    meta = {
        "pool_key": f"{ORCA_STORAGE_KEY}/pool/{solana.token_mint}_{ts}_pools.json",
        "tick_key": f"{ORCA_STORAGE_KEY}/tick/{solana.token_mint}_{ts}_ticks.json",
        "position_key": f"{ORCA_STORAGE_KEY}/position/{solana.token_mint}_{ts}_positions.json",
    }
    return dg.MaterializeResult(metadata=meta)
