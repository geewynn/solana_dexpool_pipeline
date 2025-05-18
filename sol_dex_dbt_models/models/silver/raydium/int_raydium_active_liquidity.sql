{{ config
(
    materialized = 'table',
)
}}


with
pools_tick as (select * from {{ ref('stg_raydium_pools_ticks') }}),

latest_time as (
    select *
    from pools_tick
    where extraction_timestamp = (
        select MAX(extraction_timestamp)
        from pools_tick
    )
),

flatten_ticks as (
    select
        poolId,
        startTickIndex,
        arrayJoin(JSONExtractArrayRaw(ticks)) as tick_raw,
        extraction_timestamp
    from latest_time
),

active_liquidity_tick_index as (
    select
        poolId,
        JSONExtractInt(tick_raw, 'tick') as tick_index,
        toInt128OrNull(JSONExtractString(tick_raw, 'liquidityNet')) as liquidity_net,
        toInt128OrNull(JSONExtractString(tick_raw, 'liquidityGross')) as liquidity_gross,
        extraction_timestamp
    from flatten_ticks
    where JSONExtractBool(tick_raw, 'initialized') = true
    -- keep inactive but non-zero rows too (defensive)
    or (liquidity_net != 0) or (liquidity_gross != 0)
),

final as (
    select
        poolId,
        tick_index,
        liquidity_net,
        liquidity_gross,
        extraction_timestamp
    from active_liquidity_tick_index
)

select * from final
