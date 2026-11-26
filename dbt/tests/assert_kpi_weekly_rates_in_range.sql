-- _previous and _year_ago are other weeks' _current, so checking _current covers every value.
-- A rate outside 0-100 fails in any week. A NULL rate (no orders or carts that week) is allowed in
-- the early history, but fails in the last 52 weeks, which the app and the LLM show.
with kpis as (
    select *
    from {{ ref('mart_kpi_weekly') }}
),

recent as (
    select date_sub(max(week_start), interval 52 week) as since
    from kpis
)

select k.week_start
from kpis as k
cross join recent as r
where
    -- out of range: a NULL compares to NULL, so it is not selected here
    k.session_conversion_rate_current not between 0 and 100
    or k.cart_abandonment_rate_current not between 0 and 100
    or k.product_to_cart_rate_current not between 0 and 100
    or k.cart_to_purchase_rate_current not between 0 and 100
    or k.gross_margin_pct_current not between 0 and 100
    or k.cancellation_rate_current not between 0 and 100
    or k.return_rate_current not between 0 and 100
    or k.repeat_order_share_current not between 0 and 100
    -- missing in a recent week
    or (
        k.week_start >= r.since
        and (
            k.session_conversion_rate_current is null
            or k.cart_abandonment_rate_current is null
            or k.product_to_cart_rate_current is null
            or k.cart_to_purchase_rate_current is null
            or k.gross_margin_pct_current is null
            or k.cancellation_rate_current is null
            or k.return_rate_current is null
            or k.repeat_order_share_current is null
        )
    )