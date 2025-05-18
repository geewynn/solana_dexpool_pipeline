with source as (
    select *
    from {{ source('raw', 'raydium_pools_raw') }}
),

raydium_data as (
    select *
    from source
),

final as (
    select
        pool.address::String as pool_address,
        pool.program::String as program,
        pool.space::String as space,
        pool.parsed.data.bump as bump,

        -- Pool configuration
        pool.parsed.data.ammConfig::String as amm_config,
        pool.parsed.data.owner::String as owner,
        pool.parsed.data.observationKey::String as observation_key,
        pool.parsed.data.openTime::String as open_time,
        pool.parsed.data.status::Int64 as status,

        -- Token configuration
        pool.parsed.data.tokenMint0::String as token_mint_0,
        pool.parsed.data.tokenMint1::String as token_mint_1,
        pool.parsed.data.tokenVault0::String as token_vault_0,
        pool.parsed.data.tokenVault1::String as token_vault_1,
        pool.parsed.data.mintDecimals0::UInt8 as mint_decimals_0,
        pool.parsed.data.mintDecimals1::UInt8 as mint_decimals_1,
        toFloat64(tokenVault0.amount) as token_vault_0_amount,
        toFloat64(tokenVault1.amount) as token_vault_1_amount,
        toInt64OrNull(tokenVault0.balance) as token_vault_0_balance,
        toInt64OrNull(tokenVault1.balance) as token_vault_1_balance,

        -- Swap amounts
        pool.parsed.data.swapInAmountToken0::UInt128 as swap_in_amount_token_0,
        pool.parsed.data.swapInAmountToken1::UInt128 as swap_in_amount_token_1,
        pool.parsed.data.swapOutAmountToken0::UInt128 as swap_out_amount_token_0,
        pool.parsed.data.swapOutAmountToken1::UInt128 as swap_out_amount_token_1,

        -- Fee metrics
        pool.parsed.data.feeGrowthGlobal0X64::UInt128 as fee_growth_global_0_x64,
        pool.parsed.data.feeGrowthGlobal1X64::UInt128 as fee_growth_global_1_x64,
        pool.parsed.data.fundFeesToken0::UInt64 as fund_fees_token_0,
        pool.parsed.data.fundFeesToken1::UInt64 as fund_fees_token_1,
        pool.parsed.data.protocolFeesToken0::UInt64 as protocol_fees_token_0,
        pool.parsed.data.protocolFeesToken1::UInt64 as protocol_fees_token_1,
        pool.parsed.data.totalFeesToken0::UInt64 as total_fees_token_0,
        pool.parsed.data.totalFeesToken1::UInt64 as total_fees_token_1,
        pool.parsed.data.totalFeesClaimedToken0::UInt64 as total_fees_claimed_token_0,
        pool.parsed.data.totalFeesClaimedToken1::UInt64 as total_fees_claimed_token_1,

        -- Pool metrics
        pool.parsed.data.liquidity::UInt128 as liquidity,
        pool.parsed.data.sqrtPriceX64::UInt128 as sqrt_price_x64,
        pool.parsed.data.tickCurrent::UInt32 as tick_current,
        pool.parsed.data.tickSpacing::UInt16 as tick_spacing,

        pool.parsed.data.padding as padding,
        pool.parsed.data.padding1 as padding_1,
        pool.parsed.data.padding2 as padding_2,
        pool.parsed.data.padding3 as padding_3,
        pool.parsed.data.padding4 as padding_4,

        pool.parsed.data.recentEpoch as recent_epoch,
        pool.parsed.data.rewardInfos as reward_infos,

        pool.parsed.data.tickArrayBitmap as tick_array_bitmap,

        pool.parsed.name as pool_name,
        pool.parsed.type as pool_type,
        raydium_data.extraction_timestamp

    from
        raydium_data

)

select * from final
