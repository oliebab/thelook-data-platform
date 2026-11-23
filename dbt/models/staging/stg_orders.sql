with source as (

    select *
    from {{ source('thelook_raw', 'orders') }}
    where dt = (select max(dt) from {{ source('thelook_raw', 'orders') }})

)

select
    cast(order_id as int64)          as order_id,
    cast(user_id as int64)           as user_id,
    cast(status as string)           as status,
    cast(gender as string)           as gender,
    cast(num_of_item as int64)       as num_of_item,
    cast(created_at as timestamp)    as created_at,
    cast(shipped_at as timestamp)    as shipped_at,
    cast(delivered_at as timestamp)  as delivered_at,
    cast(returned_at as timestamp)   as returned_at,
    _ingested_at
from source
