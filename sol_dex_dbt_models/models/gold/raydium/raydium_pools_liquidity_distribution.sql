{{ config
(
    materialized = 'table',
)
}}


with
active_liquidity as (select * from {{ ref('int_raydium_active_liquidity') }}),

active_liq as (
    select
        poolId,
        tick_index,
        sum(liquidity_net)
            over (
                partition by poolId
                order by tick_index
                rows between unbounded preceding and current row
            ) as active_liquidity
    from active_liquidity
),

final as (
    select
        poolId,
        tick_index,
        active_liquidity
    from active_liq
)

select * from final
