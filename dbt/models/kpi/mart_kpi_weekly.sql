-- One row per complete ISO week. For each KPI: _current, _previous (week before), _year_ago (52 weeks earlier).
-- Contract: contracts/kpi_weekly.md. Commerce KPIs are added to `kpis` once WS2 core models land.

{%- set kpis = ['sessions', 'session_conversion_rate', 'cart_abandonment_rate', 'product_to_cart_rate', 'cart_to_purchase_rate'] %}

with sessions as (
    select * from {{ ref('fct_sessions') }}
    where not is_truncated
),

bounds as (
    select
        date_trunc(date_add(min(session_date), interval 6 day), isoweek) as first_full_week,  -- first Monday with a full week of data
        date_trunc(current_date(), isoweek)                              as current_week     -- excluded: not complete
    from sessions
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
      and session_date <  bounds.current_week
    group by week_start
),

weekly as (
    select
        week_start,
        date_add(week_start, interval 6 day)                                   as week_end,
        sessions,
        round(100 * safe_divide(purchase_sessions, sessions), 1)               as session_conversion_rate,
        round(100 * safe_divide(abandoned_cart_sessions, cart_sessions), 1)    as cart_abandonment_rate,
        round(100 * safe_divide(cart_sessions, product_sessions), 1)           as product_to_cart_rate,
        round(100 * safe_divide(purchase_sessions, cart_sessions), 1)          as cart_to_purchase_rate
    from behaviour
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