{{ config
(
    materialized = 'table',
)
}}


with
orca_ticks as (select * from {{ ref('stg_orca_pools_ticks_raw') }}),

orca_pools as (select * from {{ ref('stg_orca_pools_raw') }}),

latest_time as (
    select *
    from orca_ticks
    where extraction_timestamp = (
        select max(extraction_timestamp) from orca_ticks
    )
),

flatten_ticks as (
    select
        pool,
        startindex,
        index_flattened.1 as slot_index_1_based,
        index_flattened.2 as tick_tuple,
        extraction_timestamp
    from latest_time
    array join arrayZip(arrayEnumerate(ticks), ticks) as index_flattened
),

with_spacing as (
    select
        ticks_flat.pool,
        ticks_flat.startindex,
        ticks_flat.slot_index_1_based,
        pools.tick_spacing,
        ticks_flat.tick_tuple,
        ticks_flat.extraction_timestamp
    from flatten_ticks as ticks_flat
    left join orca_pools as pools
        on ticks_flat.pool = pools.pool_address
),

active_liquidity_tick_index as (
    select
        with_spacing.pool,
        with_spacing.startindex + (with_spacing.slot_index_1_based - 1) * with_spacing.tick_spacing as tick_index,
        toInt128OrNull(tick_tuple.liquidity_net) as liquidity_net,
        toInt128OrNull(tick_tuple.liquidity_gross) as liquidity_gross,
        with_spacing.extraction_timestamp
    from with_spacing
    where
        tick_tuple.initialized = 1
        or toInt128OrNull(tick_tuple.liquidity_net) != 0
),

final as (
    select
        pool,
        tick_index,
        liquidity_net,
        liquidity_gross,
        extraction_timestamp
    from active_liquidity_tick_index
)

select * from final
