"""KPI page: six weekly KPI cards, then charts.

Week-on-week change is shown as the card's delta, year-on-year underneath.
Until mart_kpi_weekly exists, the page shows placeholder cards.
"""

import datetime as dt

import pandas as pd
import streamlit as st

import data

st.set_page_config(page_title="KPIs · TheLook Weekly", page_icon="📊", layout="wide")

# Selected week from Home; fall back to the latest week if the user landed here first.
if "week" not in st.session_state:
    st.session_state["week"] = data.get_weeks()[0]
week: dt.date = st.session_state["week"]

st.title("Weekly KPIs")
st.caption(f"Week of {week:%d %b %Y} · change the week on the Home page · source `{data.DATASET}`")

# (label, column in mart_kpi_weekly, kind). Change the column names here if the mart differs.
KPIS = [
    ("Net revenue", "net_revenue", "money"),
    ("Orders", "orders", "int"),
    ("Average order value", "aov", "money"),
    ("Session conversion", "session_conversion", "pct"),
    ("New buyers", "new_buyers", "int"),
    ("Return rate", "return_rate", "pct"),
]


def fmt(value, kind: str) -> str:
    if value is None or pd.isna(value):
        return "—"
    if kind == "money":
        return f"${value:,.0f}"
    if kind == "pct":
        return f"{value:.1%}"
    return f"{value:,.0f}"


def change(current, previous):
    """Relative change, or None if it can't be computed."""
    if current is None or previous is None or pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return (current - previous) / previous


def value_of(df: pd.DataFrame | None, col: str):
    if df is None or df.empty or col not in df.columns:
        return None
    return df.iloc[0][col]


this_week = data.get_kpis(week)
last_week = data.get_kpis(week - dt.timedelta(weeks=1))
last_year = data.get_kpis(week - dt.timedelta(weeks=52))

if this_week is None:
    st.info("`mart_kpi_weekly` isn't built yet: showing placeholders.")
elif this_week.empty:
    st.warning("No KPI row for this week.")

# --- KPI cards: 2 rows of 3 -------------------------------------------------
for row in (KPIS[:3], KPIS[3:]):
    for col, (label, name, kind) in zip(st.columns(3), row):
        current = value_of(this_week, name)
        wow = change(current, value_of(last_week, name))
        yoy = change(current, value_of(last_year, name))
        with col:
            st.metric(
                label,
                fmt(current, kind),
                delta=None if wow is None else f"{wow:+.1%} WoW",
                delta_color="inverse" if name == "return_rate" else "normal",
            )
            st.caption("YoY: —" if yoy is None else f"YoY: {yoy:+.1%}")

st.divider()

# --- Charts ---------------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("Net revenue and orders, last 52 weeks")
    history = data.get_kpi_history(52)
    if history is None:
        st.info("Placeholder: line chart once `mart_kpi_weekly` exists.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)

with right:
    st.subheader("Top 5 categories")
    top = data.get_top_categories(week)
    if top is None:
        st.info("Placeholder: bar chart once `mart_category_weekly` exists.")
    else:
        st.dataframe(top, use_container_width=True, hide_index=True)
