with source as (
    select *
    from {{ source('raw', 'orca_pools_raw') }}
),

orca_data as (
    select *
    from source
),


final as (
SELECT 
    whirlpool.pubkey::String AS pool_address,
    whirlpool.token::String AS pool_token,

    -- Core Configuration
    whirlpool.whirlpool_bump AS whirlpool_bump,
    whirlpool.whirlpools_config::String AS whirlpools_config,

    -- Token Configuration
    whirlpool.token_mint_a::String AS token_mint_a,
    whirlpool.token_mint_b::String AS token_mint_b,
    whirlpool.token_vault_a::String AS token_vault_a,
    whirlpool.token_vault_b::String AS token_vault_b,
    token_vault_a_amount.amount::Int64 AS token_a_amount,
    token_vault_b_amount.amount::Int64 AS token_b_amount,

    -- Pool State
    whirlpool.tick_spacing::UInt16 AS tick_spacing,
    whirlpool.tick_spacing_seed AS tick_spacing_seed,
    whirlpool.sqrt_price::UInt128 AS sqrt_price,
    whirlpool.liquidity::UInt128 AS liquidity,
    whirlpool.tick_current_index::Int32 AS tick_current_index,

    -- Fee Data
    whirlpool.fee_rate::UInt16 AS fee_rate,
    whirlpool.protocol_fee_rate::UInt16 AS protocol_fee_rate,
    whirlpool.fee_growth_global_a::UInt128 AS fee_growth_global_a,
    whirlpool.fee_growth_global_b::UInt128 AS fee_growth_global_b,
    whirlpool.protocol_fee_owed_a::UInt64 AS protocol_fee_owed_a,
    whirlpool.protocol_fee_owed_b::UInt64 AS protocol_fee_owed_b,

    -- Reward Configuration
    whirlpool.reward_infos AS reward_infos,
    whirlpool.reward_last_updated_timestamp::UInt64 AS reward_last_updated_timestamp,
    extraction_timestamp
    
FROM 
    orca_data
)

select * from final