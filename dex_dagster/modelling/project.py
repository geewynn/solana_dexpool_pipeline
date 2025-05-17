import os
from pathlib import Path
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, DbtProject, dbt_assets

dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..", "sol_dex_dbt_models").resolve(),
    target=os.getenv("DBT_TARGET"),
)
dbt_project.prepare_if_dev()