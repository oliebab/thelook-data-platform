-- One row per complete ISO week x product category: net revenue, the week before, and the rank within the week.
-- Weeks come from mart_kpi_weekly so both marts agree; the Gemini job reads rank <= 5.

with lines as (
    select * from {{ ref('fct_order_items') }}
),

weekly as (
    select
        order_week                                                              as week_start,
        category,
        sum(if(not is_cancelled, sale_price, 0)) - sum(if(is_returned, sale_price, 0))  as net_revenue
    from lines
    group by week_start, category
),

joined as (
    select
        cur.week_start,
        cur.category,
        cur.net_revenue                as net_revenue_current,
        prev.net_revenue               as net_revenue_previous
    from weekly as cur
    left join weekly as prev
        on  prev.category   = cur.category
        and prev.week_start = date_sub(cur.week_start, interval 7 day)
    where cur.week_start in (select week_start from {{ ref('mart_kpi_weekly') }})
)

select
    concat(cast(week_start as string), '|', category)                                  as category_week_key,
    week_start,
    date_add(week_start, interval 6 day)                                               as week_end,
    category,
    round(cast(net_revenue_current as float64), 2)                                     as net_revenue_current,
    round(cast(net_revenue_previous as float64), 2)                                    as net_revenue_previous,
    row_number() over (partition by week_start order by net_revenue_current desc, category) as net_revenue_rank
from joined