with source as (
    select *
    from {{ source('raw', 'orca_ticks_raw') }}
),


ticks_data AS (
    SELECT
        pool,
        tick_array.pubkey AS tick_array_address,
        tick_array.start_tick_index AS startindex,
        tick_array.ticks AS ticks,
        tick_array.whirlpool AS whirlpool,
        extraction_timestamp
    FROM
        source
        ARRAY JOIN tick_arrays AS tick_array
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