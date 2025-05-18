{{ config
(
    materialized = 'table',
)
}}


with
pools_raw as (select * from {{ ref('stg_raydium_pools_raw') }}),

latest_pool_snapshot as (
    select *
    from pools_raw
    where extraction_timestamp = (
        select MAX(extraction_timestamp)
        from pools_raw
    )
),

final as (
    select
        pool_address,
        program,
        owner,
        observation_key,
        open_time,
        status,
        token_mint_0,
        token_mint_1,
        token_vault_0,
        token_vault_1,
        mint_decimals_0,
        mint_decimals_1,
        token_vault_0_amount,
        token_vault_1_amount,
        token_vault_0_balance,
        token_vault_1_balance,
        swap_in_amount_token_0,
        swap_in_amount_token_1,
        swap_out_amount_token_0,
        swap_out_amount_token_1,
        fee_growth_global_0_x64,
        fee_growth_global_1_x64,
        fund_fees_token_0,
        fund_fees_token_1,
        protocol_fees_token_0,
        protocol_fees_token_1,
        total_fees_token_0,
        total_fees_token_1,
        total_fees_claimed_token_0,
        total_fees_claimed_token_1,
        liquidity,
        sqrt_price_x64,
        tick_current,
        tick_spacing,

        reward_infos,
        tick_array_bitmap,
        pool_name,
        pool_type,
        extraction_timestamp

    from
        latest_pool_snapshot

)

select * from final
