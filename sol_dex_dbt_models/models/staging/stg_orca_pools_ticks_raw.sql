with source as (
    select *
    from {{ source('raw', 'orca_ticks_raw') }}
),

ticks_data as (
    select
        source.pool,
        tick_array.pubkey as tick_array_address,
        tick_array.start_tick_index as startindex,
        tick_array.ticks as ticks,
        tick_array.whirlpool as whirlpool,
        source.extraction_timestamp
    from
        source
    array join tick_arrays as tick_array
),

final as (
    select
        pool,
        tick_array_address,
        startindex,
        ticks,
        whirlpool,
        extraction_timestamp
    from ticks_data
)

select * from final
