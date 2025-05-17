with source as (
    select *
    from {{ source('raw', 'raydium_pools_raw') }}
),

raydium_data as (
    select *
    from source
),


final as (
SELECT 
    pool.address::String AS pool_address, 
    pool.program::String AS program,
    pool.space::String AS space,
    pool.parsed.data.bump AS bump,

    -- Pool configuration
    pool.parsed.data.ammConfig::String AS amm_config,
    pool.parsed.data.owner::String  AS owner,
    pool.parsed.data.observationKey::String AS observation_key,
    pool.parsed.data.openTime::String AS open_time,
    pool.parsed.data.status::Int64 AS status,


    -- Token configuration
    pool.parsed.data.tokenMint0::String AS token_mint_0,
    pool.parsed.data.tokenMint1::String AS token_mint_1,
    pool.parsed.data.tokenVault0::String AS token_vault_0,
    pool.parsed.data.tokenVault1::String AS token_vault_1,
    pool.parsed.data.mintDecimals0::UInt8 AS mint_decimals_0,
    pool.parsed.data.mintDecimals1::UInt8 AS mint_decimals_1,
    toFloat64(tokenVault0.amount) as token_vault_0_amount,
    toFloat64(tokenVault1.amount) as token_vault_1_amount,
    toInt64OrNull(tokenVault0.balance) as token_vault_0_balance,
    toInt64OrNull(tokenVault1.balance) as token_vault_1_balance,

    -- Swap amounts
    pool.parsed.data.swapInAmountToken0::UInt128 AS swap_in_amount_token_0,
    pool.parsed.data.swapInAmountToken1::UInt128 AS swap_in_amount_token_1,
    pool.parsed.data.swapOutAmountToken0::UInt128 AS swap_out_amount_token_0,
    pool.parsed.data.swapOutAmountToken1::UInt128 AS swap_out_amount_token_1,

    -- Fee metrics
    pool.parsed.data.feeGrowthGlobal0X64::UInt128 AS fee_growth_global_0_x64,
    pool.parsed.data.feeGrowthGlobal1X64::UInt128 AS fee_growth_global_1_x64,
    pool.parsed.data.fundFeesToken0::UInt64 AS fund_fees_token_0,
    pool.parsed.data.fundFeesToken1::UInt64 AS fund_fees_token_1,
    pool.parsed.data.protocolFeesToken0::UInt64 AS protocol_fees_token_0,
    pool.parsed.data.protocolFeesToken1::UInt64 AS protocol_fees_token_1,
    pool.parsed.data.totalFeesToken0::UInt64 AS total_fees_token_0,
    pool.parsed.data.totalFeesToken1::UInt64 AS total_fees_token_1,
    pool.parsed.data.totalFeesClaimedToken0::UInt64 AS total_fees_claimed_token_0,
    pool.parsed.data.totalFeesClaimedToken1::UInt64 AS total_fees_claimed_token_1,

    -- Pool metrics
    pool.parsed.data.liquidity::UInt128 AS liquidity,
    pool.parsed.data.sqrtPriceX64::UInt128 AS sqrt_price_x64,
    pool.parsed.data.tickCurrent::UInt32 AS tick_current,
    pool.parsed.data.tickSpacing::UInt16 AS tick_spacing,
    
    pool.parsed.data.padding AS padding,
    pool.parsed.data.padding1 AS padding_1,
    pool.parsed.data.padding2 AS padding_2,
    pool.parsed.data.padding3 AS padding_3,
    pool.parsed.data.padding4 AS padding_4,
    
    pool.parsed.data.recentEpoch AS recent_epoch,
    pool.parsed.data.rewardInfos AS reward_infos,
    
    pool.parsed.data.tickArrayBitmap AS tick_array_bitmap,
    
    pool.parsed.name AS pool_name,
    pool.parsed.type AS pool_type,
    extraction_timestamp
    
FROM 
    raydium_data

)

select * from final