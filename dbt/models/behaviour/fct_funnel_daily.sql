-- Grain: one row per session_date x traffic_source. Truncated sessions excluded.
-- Rates are row-level: when aggregating (week, all sources), sum the counts and recompute.

with sessions as (
    select * from {{ ref('fct_sessions') }}
    where not is_truncated
),

daily as (
    select
        session_date,
        traffic_source,
        count(*)                    as sessions,
        countif(reached_product)    as product_sessions,
        countif(reached_cart)       as cart_sessions,
        countif(reached_purchase)   as purchase_sessions
    from sessions
    group by session_date, traffic_source
)

select
    concat(cast(session_date as string), '|', traffic_source)              as funnel_key,
    session_date,
    traffic_source,
    sessions,
    product_sessions,
    cart_sessions,
    purchase_sessions,
    round(100 * safe_divide(product_sessions, sessions), 1)               as product_rate_pct,
    round(100 * safe_divide(cart_sessions, product_sessions), 1)          as product_to_cart_pct,
    round(100 * safe_divide(purchase_sessions, cart_sessions), 1)         as cart_to_purchase_pct,
    round(100 * safe_divide(purchase_sessions, sessions), 1)              as session_conversion_pct
from daily