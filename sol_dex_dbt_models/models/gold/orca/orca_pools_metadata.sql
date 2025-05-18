{{ config
(
    materialized = 'table',
)
}}


with
pool_metadata as (select * from {{ ref('int_raydium_pool_metadata') }})

select * from pool_metadata
