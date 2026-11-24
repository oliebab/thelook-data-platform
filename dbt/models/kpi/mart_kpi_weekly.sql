-- One row per complete ISO week. For each KPI: _current, _previous (week before), _year_ago (52 weeks earlier).
-- Contract: contracts/kpi_weekly.md. Money and rates are FLOAT64 so the Python job gets floats, not Decimal.

{%- set kpis = [
    'gross_revenue', 'net_revenue', 'orders', 'average_order_value', 'items_per_order',
    'gross_margin_pct', 'cancellation_rate', 'return_rate',
    'signups', 'new_buyers', 'repeat_order_share',
    'sessions', 'session_conversion_rate', 'cart_abandonment_rate', 'product_to_cart_rate', 'cart_to_purchase_rate'
] %}

with sessions as (
    select * from {{ ref('fct_sessions') }}
    where not is_truncated
),

orders as (
    select * from {{ ref('fct_orders') }}
),

order_lines as (
    select * from {{ ref('fct_order_items') }}
),

customers as (
    select * from {{ ref('dim_customers') }}
),

session_bounds as (
    select min(session_date) as first_day, max(session_date) as last_session_day
    from sessions
),

order_bounds as (
    select max(order_date) as last_order_day
    from orders
),

bounds as (
    select
        date_trunc(date_add(first_day, interval 6 day), isoweek)                                  as first_full_week,
        -- a week counts only once its Sunday is loaded for both events and orders
        date_trunc(date_add(least(last_session_day, last_order_day), interval 1 day), isoweek)    as first_incomplete_week
    from session_bounds
    cross join order_bounds
),

behaviour as (
    select
        date_trunc(session_date, isoweek)                  as week_start,
        count(*)                                           as sessions,
        countif(reached_product)                           as product_sessions,
        countif(reached_cart)                              as cart_sessions,
        countif(reached_purchase)                          as purchase_sessions,
        countif(reached_cart and not reached_purchase)     as abandoned_cart_sessions
    from sessions
    cross join bounds
    where session_date >= bounds.first_full_week
      and session_date <  bounds.first_incomplete_week
    group by week_start
),

commerce as (
    select
        order_week                    as week_start,
        count(*)                      as orders_created,
        countif(not is_cancelled)     as orders,
        countif(is_cancelled)         as cancelled_orders,
        countif(is_returned)          as returned_orders,
        countif(is_first_order)       as new_buyers,
        countif(is_repeat_order)      as repeat_orders
    from orders
    group by week_start
),

lines as (
    select
        order_week                                                          as week_start,
        sum(if(not is_cancelled, sale_price, 0))                            as gross_revenue,
        sum(if(is_returned, sale_price, 0))                                 as returned_revenue,
        sum(if(not is_cancelled and not is_returned, product_cost, 0))      as kept_cost,
        countif(not is_cancelled)                                           as kept_lines
    from order_lines
    group by week_start
),

signups as (
    select signup_week as week_start, count(*) as signups
    from customers
    group by week_start
),

weekly as (
    -- the behaviour CTE is the week spine: it already holds only complete weeks
    select
        b.week_start,
        date_add(b.week_start, interval 6 day)                                                          as week_end,
        round(cast(l.gross_revenue as float64), 2)                                                      as gross_revenue,
        round(cast(l.gross_revenue - l.returned_revenue as float64), 2)                                 as net_revenue,
        c.orders,
        round(cast(safe_divide(l.gross_revenue, c.orders) as float64), 2)                               as average_order_value,
        round(safe_divide(l.kept_lines, c.orders), 2)                                                   as items_per_order,
        round(cast(100 * safe_divide(l.gross_revenue - l.returned_revenue - l.kept_cost,
                                     l.gross_revenue - l.returned_revenue) as float64), 1)              as gross_margin_pct,
        round(100 * safe_divide(c.cancelled_orders, c.orders_created), 1)                               as cancellation_rate,
        round(100 * safe_divide(c.returned_orders, c.orders_created), 1)                                as return_rate,
        s.signups,
        c.new_buyers,
        round(100 * safe_divide(c.repeat_orders, c.orders), 1)                                          as repeat_order_share,
        b.sessions,
        round(100 * safe_divide(b.purchase_sessions, b.sessions), 1)                                    as session_conversion_rate,
        round(100 * safe_divide(b.abandoned_cart_sessions, b.cart_sessions), 1)                         as cart_abandonment_rate,
        round(100 * safe_divide(b.cart_sessions, b.product_sessions), 1)                                as product_to_cart_rate,
        round(100 * safe_divide(b.purchase_sessions, b.cart_sessions), 1)                               as cart_to_purchase_rate
    from behaviour as b
    left join commerce as c on c.week_start = b.week_start
    left join lines    as l on l.week_start = b.week_start
    left join signups  as s on s.week_start = b.week_start
)

select
    cur.week_start,
    cur.week_end
    {%- for kpi in kpis %},
    cur.{{ kpi }}   as {{ kpi }}_current,
    prev.{{ kpi }}  as {{ kpi }}_previous,
    ya.{{ kpi }}    as {{ kpi }}_year_ago
    {%- endfor %}
from weekly as cur
left join weekly as prev on prev.week_start = date_sub(cur.week_start, interval 7 day)
left join weekly as ya   on ya.week_start   = date_sub(cur.week_start, interval 364 day)