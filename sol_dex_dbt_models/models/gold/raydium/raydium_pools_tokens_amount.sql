{{ config
(
    materialized = 'table',
)
}}


with
pool_metadata as (select * from {{ ref('int_raydium_pool_metadata') }})

select
    pool_address,
    token_mint_0 as tokenA_mint,
    token_mint_1 as tokenB_mint,
    token_vault_0_amount as token_A_balance,
    token_vault_1_amount as token_B_balance
from pool_metadata
