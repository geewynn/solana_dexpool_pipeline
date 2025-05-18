{{ config
(
    materialized = 'table',
)
}}


with
orca_pool_metadata as (select * from {{ ref('int_orca_pool_metadata') }})

select
    pool_address,
    token_mint_a as token_mint_a,
    token_mint_b as token_mint_b,
    token_a_amount as token_a_amount,
    token_b_amount as token_b_amount
from orca_pool_metadata
