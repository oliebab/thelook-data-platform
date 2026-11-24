"""Data layer for the TheLook Streamlit app.

Every BigQuery query lives here, one function per query, each cached for an hour.
Pages never talk to BigQuery directly.

The dataset is read from the APP_DATASET environment variable (default: analytics).
While developing, point it at your own dbt dataset:

    APP_DATASET=dbt_gabriel poetry run streamlit run app/Home.py

The review table is read from APP_REPORTS_TABLE
(default: thelook-dp-2611.reports.llm_business_review).

If a table doesn't exist yet, the function returns None so the page can show
a placeholder instead of crashing.
"""

import datetime as dt
import os

import pandas as pd
import streamlit as st
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

PROJECT = "thelook-dp-2611"
DATASET = os.getenv("APP_DATASET", "analytics")

# Table names. Change here if the dbt models are named differently.
KPI_TABLE = f"`{PROJECT}.{DATASET}.mart_kpi_weekly`"
CATEGORY_TABLE = f"`{PROJECT}.{DATASET}.mart_category_weekly`"
FUNNEL_TABLE = f"`{PROJECT}.{DATASET}.fct_funnel_daily`"
CHANNEL_TABLE = f"`{PROJECT}.{DATASET}.mart_channel_weekly`"
# LLM review table written by the review job (PR #14). Lives in its own dataset.
REPORTS_TABLE = "`" + os.getenv("APP_REPORTS_TABLE", f"{PROJECT}.reports.llm_business_review") + "`"

# Column holding the week (a DATE, the Monday of the week) in the weekly marts.
WEEK_COL = "week_start"


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


@st.cache_data(ttl=3600)
def get_weeks() -> list[dt.date]:
    """Weeks available for the selector, most recent first."""
    df = _query(
        f"select distinct {WEEK_COL} as week from {KPI_TABLE} order by week desc limit 52"
    )
    if df is None or df.empty:
        return _recent_mondays()
    return [pd.Timestamp(w).date() for w in df["week"]]


@st.cache_data(ttl=3600)
def get_kpis(week: dt.date) -> pd.DataFrame | None:
    """One row of weekly KPIs for the selected week (None if the mart isn't built).

    Each KPI has three columns: <kpi>_current, <kpi>_previous, <kpi>_year_ago.
    """
    return _query(
        f"select * from {KPI_TABLE} where {WEEK_COL} = @week",
        _week_param(week),
    )


@st.cache_data(ttl=3600)
def get_kpi_history(weeks: int = 52) -> pd.DataFrame | None:
    """Last N weeks of KPIs, oldest first, for the line chart."""
    df = _query(
        f"""
        select *
        from {KPI_TABLE}
        order by {WEEK_COL} desc
        limit @n
        """,
        [bigquery.ScalarQueryParameter("n", "INT64", weeks)],
    )
    return None if df is None else df.sort_values(WEEK_COL)


@st.cache_data(ttl=3600)
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


@st.cache_data(ttl=3600)
def get_review(week: dt.date) -> pd.DataFrame | None:
    """Latest LLM review generated for the selected week (a re-run adds a row)."""
    return _query(
        f"""
        select *
        from {REPORTS_TABLE}
        where period_type = 'week'
          and period_start = @week
        order by generated_at desc
        limit 1
        """,
        _week_param(week),
    )


@st.cache_data(ttl=3600)
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


@st.cache_data(ttl=3600)
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
