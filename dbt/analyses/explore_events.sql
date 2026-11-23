-- Exploration of the source events table, before modelling stg_events and fct_sessions.
-- Run each query in the BigQuery console; write the answer under it.
-- dbt compiles the analyses/ folder but never runs it.

-- Q1. What does one row represent, and is id unique?
SELECT
  COUNT(*)           AS n_rows,
  COUNT(DISTINCT id) AS n_distinct_ids
FROM `bigquery-public-data.thelook_ecommerce.events`;
-- Q1 Answer: 2,431,475 rows = 2,431,475 distinct ids. One row = one event; id is unique.

-- Q2a. Can one session belong to several users?
SELECT
  COUNTIF(n_users > 1)                    AS sessions_with_several_users,
  COUNTIF(n_null > 0 AND n_users > 0)     AS sessions_mixing_anonymous_and_known,
  COUNT(*)                                AS sessions
FROM (
  SELECT
    session_id,
    COUNT(DISTINCT user_id)    AS n_users,   -- COUNT(DISTINCT) ignores NULLs
    COUNTIF(user_id IS NULL)   AS n_null
  FROM `bigquery-public-data.thelook_ecommerce.events`
  GROUP BY session_id
);
-- Q2a Answer: 0 sessions with several users, 0 mixing anonymous and known users (681,719 sessions). user_id is constant within a session.

-- Q2b. Does sequence_number restart at 1 in each session, without gaps?
-- ROW_NUMBER() numbers the events 1, 2, 3... inside each session in time order;
-- if sequence_number always equals it, the answer is yes.
SELECT
  COUNTIF(sequence_number != rn) AS mismatches,
  COUNT(*)                       AS events
FROM (
  SELECT
    sequence_number,
    ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at, sequence_number) AS rn
  FROM `bigquery-public-data.thelook_ecommerce.events`
);
-- Q2b Answer: 0 mismatches. sequence_number starts at 1, has no gaps and follows time order within each session.

-- Q3. How many events per session, and do sessions span several days?
SELECT
  MIN(n_events)                                AS min_events,
  APPROX_QUANTILES(n_events, 2)[OFFSET(1)]     AS median_events,
  MAX(n_events)                                AS max_events,
  COUNTIF(n_days > 1)                          AS multi_day_sessions,
  COUNT(*)                                     AS sessions
FROM (
  SELECT
    session_id,
    COUNT(*)                          AS n_events,
    COUNT(DISTINCT DATE(created_at))  AS n_days
  FROM `bigquery-public-data.thelook_ecommerce.events`
  GROUP BY session_id
);
-- Q3 Answer: min 1, median 3, max 13 events per session. 76,085 sessions (11%) span several days -> session_date = date of the first event.

-- Q4a. In what order do event types appear? The 15 most common session paths.
SELECT path, COUNT(*) AS sessions
FROM (
  SELECT
    session_id,
    STRING_AGG(event_type, ' > ' ORDER BY sequence_number) AS path
  FROM `bigquery-public-data.thelook_ecommerce.events`
  GROUP BY session_id
)
GROUP BY path
ORDER BY sessions DESC
LIMIT 15;
-- Q4a Answer: most sessions start at department or product; home appears in ~87k sessions only. Funnel steps = "session reached this step", not a strict sequence. cancel follows cart (abandoned cart).

-- Q4b. Are there purchases without a cart event before them?
SELECT COUNT(*) AS purchase_sessions_without_prior_cart
FROM (
  SELECT
    session_id,
    MIN(IF(event_type = 'purchase', sequence_number, NULL)) AS first_purchase,
    MIN(IF(event_type = 'cart',     sequence_number, NULL)) AS first_cart
  FROM `bigquery-public-data.thelook_ecommerce.events`
  GROUP BY session_id
)
WHERE first_purchase IS NOT NULL
  AND (first_cart IS NULL OR first_cart > first_purchase);
-- Q4b Answer: 0 purchases without a prior cart event.

-- Q5a. How could a purchase event be linked to order_items? First, compare the counts.
SELECT
  (SELECT COUNTIF(event_type = 'purchase') FROM `bigquery-public-data.thelook_ecommerce.events`) AS purchase_events,
  (SELECT COUNT(*) FROM `bigquery-public-data.thelook_ecommerce.order_items`)                  AS order_items;
-- Q5a Answer: 181,719 purchase events = 181,719 order_items: one purchase event per order line.

-- Q5b. Test a link on user and exact timestamp.
SELECT
  COUNT(*)                   AS purchase_events,
  COUNTIF(oi.id IS NOT NULL) AS matched_to_an_order_item
FROM `bigquery-public-data.thelook_ecommerce.events` AS e
LEFT JOIN `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  ON  e.user_id    = oi.user_id
  AND e.created_at = oi.created_at
WHERE e.event_type = 'purchase';
-- Q5b Answer: only 94,809 / 181,719 (52%) match on user_id + exact created_at. No reliable key between events and orders; KPIs don't need one.

-- Q6. How many events are timestamped in the future, and on which days?
SELECT
  DATE(created_at) AS event_date,
  COUNT(*)         AS events
FROM `bigquery-public-data.thelook_ecommerce.events`
WHERE created_at > CURRENT_TIMESTAMP()
GROUP BY event_date
ORDER BY event_date;
-- Q6 Answer: 1,524 events timestamped in the future (2026-11-23 to 2026-11-26). The source generates events ahead of time; stg_events flags them with is_future.