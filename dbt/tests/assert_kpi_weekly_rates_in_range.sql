-- _previous and _year_ago are other weeks' _current, so checking _current covers every value.
-- A NULL rate fails too: every complete week has orders, carts and sessions.
select week_start
from {{ ref('mart_kpi_weekly') }}
where not coalesce(session_conversion_rate_current between 0 and 100, false)
   or not coalesce(cart_abandonment_rate_current   between 0 and 100, false)
   or not coalesce(product_to_cart_rate_current    between 0 and 100, false)
   or not coalesce(cart_to_purchase_rate_current   between 0 and 100, false)
   or not coalesce(gross_margin_pct_current        between 0 and 100, false)
   or not coalesce(cancellation_rate_current       between 0 and 100, false)
   or not coalesce(return_rate_current             between 0 and 100, false)
   or not coalesce(repeat_order_share_current      between 0 and 100, false)