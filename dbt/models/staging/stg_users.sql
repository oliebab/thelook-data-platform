with source as (

    select *
    from {{ source('thelook_raw', 'users') }}
    where dt = {{ latest_dt('users') }}

)

-- Names, e-mail, street address, postal code and coordinates are left out:
-- nothing downstream needs them, and this keeps PII out of analytics.
select
    cast(id as int64)                as user_id,
    cast(age as int64)               as age,
    cast(gender as string)           as gender,
    cast(city as string)             as city,
    cast(state as string)            as state,
    cast(country as string)          as country,
    cast(traffic_source as string)   as traffic_source,
    cast(created_at as timestamp)    as created_at,
    _ingested_at
from source
