with source as (
    select *
    from {{ source('raw', 'raydium_personal_position_raw') }}
),


final as (
select 
    nftMint,
    poolId,
    tickLowerIndex,
    tickUpperIndex,
    liquidity,
    feeGrowthInside0LastX64,
    feeGrowthInside1LastX64,
    tokenFeesOwed0,
    tokenFeesOwed1,
    rewardInfos
    extraction_timestamp
from source
)

select * from final