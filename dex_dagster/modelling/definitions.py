import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional
from dex_dagster.ingestion.definitions import raydium_snapshot, orca_snapshot, s3_resource, solana_config

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets, build_schedule_from_dbt_selection

dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..", "sol_dex_dbt_models").resolve(),
    target=os.getenv("DBT_TARGET"),
)
dbt_project.prepare_if_dev()
dbt_resource = DbtCliResource(project_dir=dbt_project)


class CustomizedDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        asset_path = dbt_resource_props["fqn"][1:-1]
        if asset_path:
            return "_".join(asset_path)
        return "default"

    def get_asset_key(self, dbt_resource_props):
        resource_type = dbt_resource_props["resource_type"]
        name = dbt_resource_props["name"]
        if resource_type == "source":
            return dg.AssetKey(name)
        else:
            return super().get_asset_key(dbt_resource_props)


@dbt_assets(
    name="dbt_soldex",  
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
)
def dbt_soldex(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from (dbt.cli(["build"], context=context).stream().fetch_row_counts())


dbt_build_job = dg.define_asset_job(
    "dbt_build_job",
    selection=[dbt_soldex], 
)


@dg.multi_asset_sensor(
    monitored_assets=[dg.AssetKey("raydium_snapshot"), dg.AssetKey("orca_snapshot")],
    job=dbt_build_job,
)
def snapshot_sensor(context):
    asset_events = context.latest_materialization_records_by_key()
    if all(asset_events.values()):
        context.advance_all_cursors()
        return dg.RunRequest(run_key=context.cursor, run_config={})
    return None


defs = dg.Definitions(
    assets=[raydium_snapshot, orca_snapshot, dbt_soldex],
    resources={
        "s3_resource": s3_resource,
        "solana": solana_config,
        "dbt": dbt_resource,  # Adding the dbt resource
    },
    jobs=[dbt_build_job],
    sensors=[snapshot_sensor],
)
