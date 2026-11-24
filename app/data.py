"""Data layer for the TheLook Streamlit app.

Every BigQuery query lives here, one function per query, each cached for an hour.
Pages never talk to BigQuery directly.

The dataset is read from the APP_DATASET environment variable (default: analytics).
While developing, I'm pointing it at my own dbt dataset:

    APP_DATASET=dbt_gabriel poetry run streamlit run app/Home.py

If a table doesn't exist yet (e.g. mart_kpi_weekly or reports), the function
returns None so the page can show a placeholder instead of crashing.
"""

import datetime as dt
import os

import pandas as pd
import streamlit as st
from google.api_core.exceptions import NotFound
from google.cloud import bigquery

PROJECT = "thelook-dp-2611"
DATASET = os.getenv("APP_DATASET", "analytics")
REPORTS_DATASET = os.getenv("APP_REPORTS_DATASET", DATASET)

# Table names
KPI_TABLE = f"`{PROJECT}.{DATASET}.mart_kpi_weekly`"
CATEGORY_TABLE = f"`{PROJECT}.{DATASET}.mart_category_weekly`"
REPORTS_TABLE = f"`{PROJECT}.{REPORTS_DATASET}.reports`"

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
    """One row of weekly KPIs for the selected week (None if the mart isn't built)."""
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
    """Top N categories by net revenue for the selected week."""
    return _query(
        f"""
        select *
        from {CATEGORY_TABLE}
        where {WEEK_COL} = @week
        order by net_revenue desc
        limit @n
        """,
        _week_param(week) + [bigquery.ScalarQueryParameter("n", "INT64", n)],
    )


@st.cache_data(ttl=3600)
def get_latest_review() -> pd.DataFrame | None:
    """Most recent LLM review (text, model, prompt version, input JSON)."""
    return _query(
        f"select * from {REPORTS_TABLE} order by generated_at desc limit 1"
    )