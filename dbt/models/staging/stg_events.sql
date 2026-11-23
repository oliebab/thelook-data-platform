with source as (
    select * from {{ source('thelook_raw', 'events') }}
),

deduplicated as (
    -- daily partitions can re-deliver the same event: keep the latest load
    select *
    from source
    qualify row_number() over (partition by id order by _ingested_at desc) = 1
),

renamed as (
    select
        id                                as event_id,
        session_id,
        user_id,
        sequence_number,
        created_at,
        date(created_at)                  as event_date,
        event_type,
        traffic_source,
        browser,
        uri,
        created_at > current_timestamp()  as is_future,
        _ingested_at
    from deduplicated
)

select * from renamed