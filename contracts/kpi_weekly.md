# KPI contract: mart_kpi_weekly

Owner: Olivier (mart) and Clemens (LLM job). Changing a column name = tell the other first.

## Grain and columns
- One row per ISO week, `week_start` (Monday, DATE) and `week_end` (Sunday, DATE).
- Only complete weeks; the current week is excluded.
- For each KPI below, three columns: `<kpi>_current`, `<kpi>_previous` (week before), `<kpi>_year_ago` (same ISO week, 52 weeks earlier).
- `_year_ago` is NULL when there is no data a year earlier.

## Units and rounding
- Money: USD, 2 decimals.
- Counts: integers.
- Rates: percentages from 0 to 100, 1 decimal (2.8 means 2.8%).
- Changes are NOT stored in the mart; the LLM job computes them:
  - money and counts: `wow_change_pct`, `yoy_change_pct` (relative change, %, 1 decimal);
  - rates: `wow_change_pts`, `yoy_change_pts` (difference in percentage points, 1 decimal).

## KPIs
| KPI | Formula | Built from |
| --- | --- | --- |
| gross_revenue | Sum of sale_price on order lines, excluding Cancelled | fct_order_items |
| net_revenue | gross_revenue minus sale_price of Returned lines | fct_order_items |
| orders | Distinct order_id, excluding Cancelled | fct_orders |
| average_order_value | gross_revenue / orders | fct_order_items, fct_orders |
| items_per_order | Non-cancelled order lines / orders | fct_order_items |
| gross_margin_pct (rate) | (net_revenue - cost of kept lines) / net_revenue | fct_order_items |
| cancellation_rate (rate) | Cancelled orders / orders created in the week | fct_orders |
| return_rate (rate) | Returned orders / orders created in the week (recent weeks understated) | fct_orders |
| signups | Users created in the week | dim_customers |
| new_buyers | Customers whose first order is in the week | fct_orders (is_first_order) |
| repeat_order_share (rate) | Orders from customers who had ordered before / orders | fct_orders |
| sessions | Sessions starting in the week, anonymous included | fct_sessions |
| session_conversion_rate (rate) | Sessions with a purchase / sessions | fct_sessions |
| cart_abandonment_rate (rate) | Sessions with a cart and no purchase / sessions with a cart | fct_sessions |
| product_to_cart_rate (rate) | Sessions reaching cart / sessions reaching product | fct_sessions |
| cart_to_purchase_rate (rate) | Sessions reaching purchase / sessions reaching cart | fct_sessions |

Funnel steps mean "the session reached this step", not "went through every previous step":
most sessions skip home (see dbt/analyses/explore_events.sql).

## Read alongside the mart (by the LLM job)
- Channels: sessions and session conversion by traffic_source for the week, from fct_sessions.
- Top 5 categories by net revenue, with week-on-week change, from mart_category_weekly.

## Highlight rule (computed by the LLM job, not the model)
- `highlight: true` when the week-on-week change reaches 5% or more for amounts and counts,
  or 1 point or more for rates. Same rule for channels (sessions) and categories (net revenue).
- The prompt only takes wins and concerns from highlighted items.
- Review order: net revenue (headline), then orders x average order value, then sessions x
  session conversion, then margin / cancellations / returns, then customers, then at most
  two channels and two categories.
- Rate changes are written in "pts", amount changes in "%".
