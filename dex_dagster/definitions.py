import dagster as dg

# start_def
import dex_dagster.ingestion.definitions as ingestion_definitions

defs = dg.Definitions.merge(ingestion_definitions.defs)
