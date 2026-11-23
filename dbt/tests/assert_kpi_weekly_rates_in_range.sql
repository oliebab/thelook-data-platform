-- _previous and _year_ago are other weeks' _current, so checking _current covers every value.
select week_start
from {{ ref('mart_kpi_weekly') }}
where session_conversion_rate_current not between 0 and 100
   or cart_abandonment_rate_current   not between 0 and 100
   or product_to_cart_rate_current    not between 0 and 100
   or cart_to_purchase_rate_current   not between 0 and 100