{{ config(
    partition_by={'field': 'session_date', 'data_type': 'date'},
    cluster_by=['traffic_source']
) }}

with events as (
    select * from {{ ref('stg_events') }}
    where not is_future
),

sessions as (
    select
        session_id,
        max(user_id)                                           as user_id,  -- one user per session at most (checked)
        min(created_at)                                        as session_start,
        max(created_at)                                        as session_end,
        count(*)                                               as n_events,
        any_value(traffic_source having min sequence_number)   as traffic_source,
        any_value(browser having min sequence_number)          as browser,
        any_value(event_type having min sequence_number)       as landing_event_type,
        logical_or(event_type = 'product')                     as reached_product,
        logical_or(event_type = 'cart')                        as reached_cart,
        logical_or(event_type = 'purchase')                    as reached_purchase,
        min(sequence_number) > 1                               as is_truncated  -- started before the backfill window
    from events
    group by session_id
)

select
    session_id,
    user_id,
    user_id is not null                                        as is_known_user,
    session_start,
    session_end,
    date(session_start)                                        as session_date,
    timestamp_diff(session_end, session_start, second)         as duration_seconds,
    n_events,
    traffic_source,
    browser,
    landing_event_type,
    reached_product,
    reached_cart,
    reached_purchase,
    is_truncated
from sessions