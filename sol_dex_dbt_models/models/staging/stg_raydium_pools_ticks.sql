with source as (
    select *
    from {{ source('raw', 'raydium_ticks_raw') }}
),

flatten_tick_data as (
    select
        arrayJoin(JSONExtractKeysAndValuesRaw(tickArrays) .2) as tick_data,
        extraction_timestamp
    from source
),

flat_parse as (
    select
        JSONExtractString(tick_data, 'address') as address,
        JSONExtractString(tick_data, 'parsed') as parsed,
        extraction_timestamp
    from flatten_tick_data
),

parse_data as (
    select
        address,
        parsed,
        JSONExtractString(parsed, 'name') as name,
        JSONExtractString(parsed, 'data') as data,
        JSONExtractString(parsed, 'type') as type,
        extraction_timestamp
    from flat_parse
),

final as (
    select
        address,
        parsed,
        type,
        name,
        JSONExtractString(data, 'poolId') as poolId,
        JSONExtractInt(data, 'startTickIndex') as startTickIndex,
        JSONExtractString(data, 'ticks') as ticks,
        extraction_timestamp
    from parse_data
)

select * from final
