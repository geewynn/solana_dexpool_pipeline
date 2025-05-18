with source as (
    select *
    from {{ source('raw', 'orca_pools_raw') }}
),

orca_data as (
    select *
    from source
),

final as (
    select
        whirlpool.pubkey::String as pool_address,
        whirlpool.token::String as pool_token,

        -- Core Configuration
        whirlpool.whirlpool_bump as whirlpool_bump,
        whirlpool.whirlpools_config::String as whirlpools_config,

        -- Token Configuration
        whirlpool.token_mint_a::String as token_mint_a,
        whirlpool.token_mint_b::String as token_mint_b,
        whirlpool.token_vault_a::String as token_vault_a,
        whirlpool.token_vault_b::String as token_vault_b,
        token_vault_a_amount.amount::Int64 as token_a_amount,
        token_vault_b_amount.amount::Int64 as token_b_amount,

        -- Pool State
        whirlpool.tick_spacing::UInt16 as tick_spacing,
        whirlpool.tick_spacing_seed as tick_spacing_seed,
        whirlpool.sqrt_price::UInt128 as sqrt_price,
        whirlpool.liquidity::UInt128 as liquidity,
        whirlpool.tick_current_index::Int32 as tick_current_index,

        -- Fee Data
        whirlpool.fee_rate::UInt16 as fee_rate,
        whirlpool.protocol_fee_rate::UInt16 as protocol_fee_rate,
        whirlpool.fee_growth_global_a::UInt128 as fee_growth_global_a,
        whirlpool.fee_growth_global_b::UInt128 as fee_growth_global_b,
        whirlpool.protocol_fee_owed_a::UInt64 as protocol_fee_owed_a,
        whirlpool.protocol_fee_owed_b::UInt64 as protocol_fee_owed_b,

        -- Reward Configuration
        whirlpool.reward_infos as reward_infos,
        whirlpool.reward_last_updated_timestamp::UInt64 as reward_last_updated_timestamp,
        orca_data.extraction_timestamp

    from
        orca_data
)

select * from final
