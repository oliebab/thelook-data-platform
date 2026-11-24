-- Grain: one row per order line.
-- Items follow their order: the inner join drops lines of orders that stg_orders filtered out (future-dated),
-- and all dates come from the order, because an item's own created_at is 0-96 h after it.

with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select order_id, created_at, status from {{ ref('stg_orders') }}
),

products as (
    select product_id, category, department, brand, cost from {{ ref('stg_products') }}
)

select
    i.order_item_id,
    i.order_id,
    i.user_id,
    i.product_id,
    o.created_at                                as order_created_at,
    date(o.created_at)                          as order_date,
    date_trunc(date(o.created_at), isoweek)     as order_week,
    o.status                                    as order_status,  -- item status always equals order status (checked)
    o.status = 'Cancelled'                      as is_cancelled,
    o.status = 'Returned'                       as is_returned,
    i.sale_price,
    p.cost                                      as product_cost,
    p.category,
    p.department,
    p.brand
from items as i
inner join orders as o on o.order_id = i.order_id
left join products as p on p.product_id = i.product_id