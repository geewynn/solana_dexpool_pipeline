with source as (
    select *
    from {{ source('raw', 'orca_positions_raw') }}
),

ticks_data as (
    select
        pubkey,
        position_mint,
        liquidity,
        tick_lower_index,
        tick_upper_index,
        fee_growth_ckpt_a,
        fee_growth_ckpt_b,
        fee_owed_a,
        fee_owed_b,
        reward_infos,
        extraction_timestamp
    from
        source
)

select * from ticks_data
