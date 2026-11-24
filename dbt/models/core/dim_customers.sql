-- Grain: one row per user. PII is already dropped in stg_users.

with users as (
    select * from {{ ref('stg_users') }}
),

purchases as (
    select
        user_id,
        min(created_at)    as first_order_at,
        count(*)           as n_orders,
        sum(order_amount)  as lifetime_gross_revenue
    from {{ ref('fct_orders') }}
    where not is_cancelled
    group by user_id
)

select
    u.user_id,
    u.created_at                                as signup_at,
    date(u.created_at)                          as signup_date,
    date_trunc(date(u.created_at), isoweek)     as signup_week,
    u.age,
    u.gender,
    u.country,
    u.state,
    u.city,
    u.traffic_source                            as acquisition_source,
    p.first_order_at,
    coalesce(p.n_orders, 0)                     as n_orders,
    coalesce(p.lifetime_gross_revenue, 0)       as lifetime_gross_revenue,
    p.user_id is not null                       as is_buyer
from users as u
left join purchases as p on p.user_id = u.user_id