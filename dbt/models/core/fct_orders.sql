-- Grain: one row per order (future-dated orders already dropped in stg_orders).
-- Line amounts are aggregated BEFORE joining, so order rows are never multiplied by their lines.

with orders as (
    select * from {{ ref('stg_orders') }}
),

lines as (
    select
        order_id,
        count(*)           as num_lines,
        sum(sale_price)    as order_amount,
        sum(product_cost)  as order_cost
    from {{ ref('fct_order_items') }}
    group by order_id
),

purchase_rank as (
    -- Cancelled orders are not purchases, so they never count as a first or repeat order.
    select
        order_id,
        row_number() over (partition by user_id order by created_at, order_id) as user_order_number
    from orders
    where status != 'Cancelled'
)

select
    o.order_id,
    o.user_id,
    o.status,
    o.created_at,
    date(o.created_at)                          as order_date,
    date_trunc(date(o.created_at), isoweek)     as order_week,
    o.status = 'Cancelled'                      as is_cancelled,
    o.status = 'Returned'                       as is_returned,
    coalesce(l.num_lines, 0)                    as num_lines,
    coalesce(l.order_amount, 0)                 as order_amount,
    coalesce(l.order_cost, 0)                   as order_cost,
    r.user_order_number,
    coalesce(r.user_order_number = 1, false)    as is_first_order,
    coalesce(r.user_order_number > 1, false)    as is_repeat_order
from orders as o
left join lines as l on l.order_id = o.order_id
left join purchase_rank as r on r.order_id = o.order_id