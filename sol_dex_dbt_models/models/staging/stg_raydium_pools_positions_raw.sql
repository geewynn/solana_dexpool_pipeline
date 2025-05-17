with source as (
    select *
    from {{ source('raw', 'raydium_pools_positions_raw') }}
),


final as (
SELECT 
  poolId, 
  tickLowerIndex, 
  tickUpperIndex, 
  liquidity, 
  tokenFeesOwed0, 
  tokenFeesOwed1 
  feeGrowthInside0LastX64, 
  feeGrowthInside1LastX64, 
  rewardGrowthInside, 
  extraction_timestamp, 
FROM 
  source
)

select * from final