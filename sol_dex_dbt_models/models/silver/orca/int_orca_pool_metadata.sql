{{ config
(
    materialized = 'table',
)
}}


with
orca_pools_raw as (select * from {{ ref('stg_orca_pools_raw') }}),

latest_pool_snapshot as (
    select *
    from orca_pools_raw
    where extraction_timestamp = (
        select MAX(extraction_timestamp)
        from orca_pools_raw
    )
),

final as (
    select
        pool_address,
        pool_token,
        whirlpool_bump,
        whirlpools_config,
        token_mint_a,
        token_mint_b,
        token_vault_a,
        token_vault_b,
        token_a_amount,
        token_b_amount,
        tick_spacing,
        tick_spacing_seed,
        sqrt_price,
        liquidity,
        tick_current_index,
        fee_rate,
        protocol_fee_rate,
        fee_growth_global_a,
        fee_growth_global_b,
        protocol_fee_owed_a,
        protocol_fee_owed_b,
        reward_infos,
        reward_last_updated_timestamp,
        extraction_timestamp

    from
        latest_pool_snapshot

)

select * from final
