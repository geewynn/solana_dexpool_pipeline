{{ config
(
    materialized = 'table',
)
}}


with
active_orca_liquidity as (select * from {{ ref('int_orca_active_liquidity') }}),

active_liq as (
    select
        pool,
        tick_index,
        sum(liquidity_net)
            over (
                partition by pool
                order by tick_index
                rows between unbounded preceding and current row
            ) as active_liquidity
    from active_orca_liquidity
    order by tick_index
),

final as (
    select
        pool,
        tick_index,
        active_liquidity
    from active_liq
)

select * from final
