-- One row per complete ISO week x traffic_source, with the week before for WoW. Read by the Gemini review.

with daily as (
    select * from {{ ref('fct_funnel_daily') }}
),

bounds as (
    select
        date_trunc(date_add(min(session_date), interval 6 day), isoweek) as first_full_week,
        date_trunc(current_date(), isoweek)                              as current_week
    from daily
),

weekly as (
    select
        date_trunc(session_date, isoweek)  as week_start,
        traffic_source,
        sum(sessions)                      as sessions,
        sum(purchase_sessions)             as purchase_sessions
    from daily
    cross join bounds
    where session_date >= bounds.first_full_week
      and session_date <  bounds.current_week
    group by week_start, traffic_source
)

select
    concat(cast(cur.week_start as string), '|', cur.traffic_source)          as channel_week_key,
    cur.week_start,
    date_add(cur.week_start, interval 6 day)                                 as week_end,
    cur.traffic_source,
    cur.sessions                                                             as sessions_current,
    prev.sessions                                                            as sessions_previous,
    round(100 * safe_divide(cur.purchase_sessions, cur.sessions), 1)         as session_conversion_rate_current,
    round(100 * safe_divide(prev.purchase_sessions, prev.sessions), 1)       as session_conversion_rate_previous
from weekly as cur
left join weekly as prev
    on  prev.traffic_source = cur.traffic_source
    and prev.week_start     = date_sub(cur.week_start, interval 7 day)