with source as (
    select *
    from {{ source('raw', 'raydium_ticks_raw') }}
),

flatten_tick_data AS (
    SELECT
        arrayJoin(JSONExtractKeysAndValuesRaw(tickArrays).2) AS tick_data,
        extraction_timestamp
    FROM source
),

flat_parse AS (
    SELECT
        JSONExtractString(tick_data, 'address') AS address,
        JSONExtractString(tick_data, 'parsed') AS parsed,
        extraction_timestamp
    FROM flatten_tick_data
),

parse_data AS (
    SELECT
        address,
        parsed,
        JSONExtractString(parsed, 'name') AS name,
        JSONExtractString(parsed, 'data') AS data,
        JSONExtractString(parsed, 'type') AS type,
        extraction_timestamp
    FROM flat_parse
),
final as (
SELECT
    address,
    parsed,
    type,
    name,
    JSONExtractString(data, 'poolId') AS poolId,
    JSONExtractInt(data, 'startTickIndex') AS startTickIndex,
    JSONExtractString(data, 'ticks') AS ticks,
    extraction_timestamp
FROM parse_data
)
SELECT * FROM final