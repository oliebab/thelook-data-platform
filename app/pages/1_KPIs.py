"""KPI page: six weekly KPI cards, then (Thursday) charts.

mart_kpi_weekly has one row per week and, for each KPI, three columns:
<kpi>_current, <kpi>_previous and <kpi>_year_ago. Week-on-week change is the
card's delta; year-on-year change is shown underneath.

Money and counts change in relative %. Rates are stored as 0-100 percentages
with 1 decimal, so their changes are shown in points (pts).
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

# (label, KPI name in mart_kpi_weekly without the _current/_previous/_year_ago suffix, kind)
KPIS = [
    ("Net revenue", "net_revenue", "money"),
    ("Orders", "orders", "int"),
    ("Average order value", "average_order_value", "money"),
    ("Session conversion", "session_conversion_rate", "rate"),
    ("New buyers", "new_buyers", "int"),
    ("Return rate", "return_rate", "rate"),
]


def is_missing(value) -> bool:
    return value is None or pd.isna(value)


def fmt(value, kind: str) -> str:
    if is_missing(value):
        return "—"
    if kind == "money":
        return f"${value:,.0f}"
    if kind == "rate":
        return f"{value:.1f}%"  # already 0-100
    return f"{value:,.0f}"


def change(current, other, kind: str) -> str | None:
    """Change vs another period: points for rates, relative % otherwise."""
    if is_missing(current) or is_missing(other):
        return None
    if kind == "rate":
        return f"{current - other:+.1f} pts"
    if other == 0:
        return None
    return f"{(current - other) / other:+.1%}"


def value_of(df: pd.DataFrame | None, col: str):
    if df is None or df.empty or col not in df.columns:
        return None
    return df.iloc[0][col]


kpis = data.get_kpis(week)

if kpis is None:
    st.info("`mart_kpi_weekly` isn't built yet: showing placeholders.")
elif kpis.empty:
    st.warning("No KPI row for this week.")

# --- KPI cards: 2 rows of 3 -------------------------------------------------
for row in (KPIS[:3], KPIS[3:]):
    for col, (label, name, kind) in zip(st.columns(3), row):
        current = value_of(kpis, f"{name}_current")
        wow = change(current, value_of(kpis, f"{name}_previous"), kind)
        yoy = change(current, value_of(kpis, f"{name}_year_ago"), kind)
        with col:
            st.metric(
                label,
                fmt(current, kind),
                delta=None if wow is None else f"{wow} WoW",
                delta_color="inverse" if name == "return_rate" else "normal",
            )
            st.caption(f"YoY: {yoy or '—'}")

st.divider()

# --- Charts (built on Thursday) ---------------------------------------------
left, right = st.columns(2)
with left:
    st.subheader("Net revenue and orders, last 52 weeks")
    history = data.get_kpi_history(52)
    if history is None:
        st.info("Placeholder: line chart once `mart_kpi_weekly` exists.")
    else:
        st.dataframe(
            history[[data.WEEK_COL, "net_revenue_current", "orders_current"]],
            use_container_width=True,
            hide_index=True,
        )

with right:
    st.subheader("Top 5 categories")
    top = data.get_top_categories(week)
    if top is None:
        st.info("Placeholder: bar chart once `mart_category_weekly` exists.")
    else:
        st.dataframe(top, use_container_width=True, hide_index=True)
