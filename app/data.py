"""Data layer for the TheLook Streamlit app.

Every BigQuery query lives here, one function per query, each cached for an hour
so switching pages is instant. Pages never talk to BigQuery directly.

Configuration (environment variables):
    APP_DATASET        dataset of the dbt marts (default: analytics)
    APP_REPORTS_TABLE  LLM review table (default: thelook-dp-2611.reports.llm_business_review)

If a table doesn't exist yet, a function returns None: the page shows a clear
message instead of a traceback. Other BigQuery errors are raised and turned into
a readable message by ui.load().
"""

import datetime as dt
import os

import pandas as pd
import streamlit as st
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

PROJECT = os.getenv("GCP_PROJECT", "thelook-dp-2611")
DATASET = os.getenv("APP_DATASET", "analytics")

KPI_TABLE_NAME = "mart_kpi_weekly"
CATEGORY_TABLE_NAME = "mart_category_weekly"
FUNNEL_TABLE_NAME = "fct_funnel_daily"
CHANNEL_TABLE_NAME = "mart_channel_weekly"
REPORTS_TABLE_ID = os.getenv(
    "APP_REPORTS_TABLE", f"{PROJECT}.reports.llm_business_review"
)

KPI_TABLE = f"`{PROJECT}.{DATASET}.{KPI_TABLE_NAME}`"
CATEGORY_TABLE = f"`{PROJECT}.{DATASET}.{CATEGORY_TABLE_NAME}`"
FUNNEL_TABLE = f"`{PROJECT}.{DATASET}.{FUNNEL_TABLE_NAME}`"
CHANNEL_TABLE = f"`{PROJECT}.{DATASET}.{CHANNEL_TABLE_NAME}`"
REPORTS_TABLE = f"`{REPORTS_TABLE_ID}`"

# Column holding the week (a DATE, the Monday of the week) in the weekly marts.
WEEK_COL = "week_start"

CACHE_TTL = 3600  # seconds


@st.cache_resource
def get_client() -> bigquery.Client:
    """One BigQuery client for the whole app (uses the VM's identity)."""
    return bigquery.Client(project=PROJECT)


def _query(sql: str, params: list | None = None) -> pd.DataFrame | None:
    """Run a query and return a DataFrame, or None if a table doesn't exist yet."""
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    try:
        return get_client().query(sql, job_config=job_config).to_dataframe()
    except NotFound:
        return None


def _week_param(week: dt.date) -> list:
    return [bigquery.ScalarQueryParameter("week", "DATE", week)]


def _recent_mondays(n: int = 12) -> list[dt.date]:
    """Fallback week list while mart_kpi_weekly doesn't exist."""
    today = dt.date.today()
    last_monday = today - dt.timedelta(days=today.weekday() + 7)  # last complete week
    return [last_monday - dt.timedelta(weeks=i) for i in range(n)]


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_weeks() -> list[dt.date]:
    """Weeks available for the selector, most recent first."""
    df = _query(
        f"select distinct {WEEK_COL} as week from {KPI_TABLE} order by week desc limit 52"
    )
    if df is None or df.empty:
        return _recent_mondays()
    return [pd.Timestamp(w).date() for w in df["week"]]


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_kpis(week: dt.date) -> pd.DataFrame | None:
    """One row of weekly KPIs for the selected week (None if the mart isn't built).

    Each KPI has three columns: <kpi>_current, <kpi>_previous, <kpi>_year_ago.
    """
    return _query(
        f"select * from {KPI_TABLE} where {WEEK_COL} = @week",
        _week_param(week),
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_kpi_history(weeks: int = 52) -> pd.DataFrame | None:
    """Last N weeks of KPIs, oldest first. week_start is returned as a pandas Timestamp."""
    df = _query(
        f"""
        select *
        from {KPI_TABLE}
        order by {WEEK_COL} desc
        limit @n
        """,
        [bigquery.ScalarQueryParameter("n", "INT64", weeks)],
    )
    if df is None:
        return None
    df[WEEK_COL] = pd.to_datetime(df[WEEK_COL])
    return df.sort_values(WEEK_COL).reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_top_categories(week: dt.date, n: int = 5) -> pd.DataFrame | None:
    """Top N categories by net revenue for the selected week (uses the mart's rank)."""
    return _query(
        f"""
        select *
        from {CATEGORY_TABLE}
        where {WEEK_COL} = @week
          and net_revenue_rank <= @n
        order by net_revenue_rank
        """,
        _week_param(week) + [bigquery.ScalarQueryParameter("n", "INT64", n)],
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_review(week: dt.date) -> pd.DataFrame | None:
    """Latest LLM review for the selected week.

    A review that passed the guardrail (numbers checked against the KPIs) always wins
    over one that didn't; among those, the newest one. The page shows a badge from
    guardrail_passed, and a warning when only an unchecked review exists.
    """
    return _query(
        f"""
        select *
        from {REPORTS_TABLE}
        where period_type = 'week'
          and period_start = @week
        order by guardrail_passed desc, generated_at desc
        limit 1
        """,
        _week_param(week),
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_funnel_daily(week: dt.date) -> pd.DataFrame | None:
    """Daily funnel rows (one per day and traffic source) for the selected week
    and the week before it, so the page can compute week-on-week changes.

    Only the session counts are read: rates are recomputed from the sums,
    because averaging daily percentages would weight a quiet day like a busy one.
    """
    return _query(
        f"""
        select
            session_date,
            traffic_source,
            sessions,
            product_sessions,
            cart_sessions,
            purchase_sessions,
            -- Sessions running past midnight only show up the next day, so the
            -- last loaded day under-counts conversion: flag it as provisional.
            session_date = (select max(session_date) from {FUNNEL_TABLE}) as is_provisional
        from {FUNNEL_TABLE}
        where session_date between date_sub(@week, interval 7 day)
                               and date_add(@week, interval 6 day)
        """,
        _week_param(week),
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_channels(week: dt.date) -> pd.DataFrame | None:
    """One row per traffic source for the selected week, with sessions and
    session conversion (0-100) for this week and the previous one."""
    return _query(
        f"""
        select
            traffic_source,
            sessions_current,
            sessions_previous,
            session_conversion_rate_current,
            session_conversion_rate_previous
        from {CHANNEL_TABLE}
        where {WEEK_COL} = @week
        order by sessions_current desc
        """,
        _week_param(week),
    )
