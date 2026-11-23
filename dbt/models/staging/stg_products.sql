with source as (

    select *
    from {{ source('thelook_raw', 'products') }}
    where dt = (select max(dt) from {{ source('thelook_raw', 'products') }})

)

select
    cast(id as int64)                      as product_id,
    cast(name as string)                   as product_name,
    cast(brand as string)                  as brand,
    cast(category as string)               as category,
    cast(department as string)             as department,
    cast(sku as string)                    as sku,
    cast(cost as numeric)                  as cost,
    cast(retail_price as numeric)          as retail_price,
    cast(distribution_center_id as int64)  as distribution_center_id,
    _ingested_at
from source
