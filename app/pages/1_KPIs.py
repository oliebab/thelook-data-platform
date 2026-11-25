"""KPI page: six KPI cards with coloured WoW / YoY badges and 12-week trend lines,
an interactive trend explorer, and the top categories.

mart_kpi_weekly has one row per week and, for each KPI, three columns:
<kpi>_current, <kpi>_previous and <kpi>_year_ago.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data
import ui

week = ui.week()
ui.header("Weekly KPIs", ":material/monitoring:")

kpis = ui.load(data.get_kpis, week, what="KPIs")
history = ui.load(data.get_kpi_history, 52, what="KPI history")

if kpis is None:
    ui.missing("KPIs", data.KPI_TABLE_NAME)
    st.stop()
if kpis.empty:
    st.warning("No KPI row for this week. Pick another week in the sidebar.", icon=":material/event_busy:")
    st.stop()

row = kpis.iloc[0]

# --- KPI cards: 2 rows of 3 ---------------------------------------------------------
for chunk in (ui.KPIS[:3], ui.KPIS[3:]):
    for col, kpi in zip(st.columns(3), chunk):
        with col:
            ui.kpi_card(kpi, row, history, week)
st.caption(
    "Badges: change vs last week (WoW) and the same week last year (YoY). "
    "Green is good news, red is bad (a rising return rate is red). Rates change in points. "
    "Lines: last 12 weeks."
)

st.divider()
left, right = st.columns([3, 2], gap="large")

# --- Trend explorer ------------------------------------------------------------------
with left:
    st.subheader(":material/show_chart: Trend explorer")
    labels = [k["label"] for k in ui.KPIS]
    c1, c2 = st.columns([3, 2])
    choice = c1.selectbox("Metric", labels, key="trend_metric")
    span = c2.segmented_control(
        "Period", [12, 26, 52], default=26, format_func=lambda n: f"{n} wk", key="trend_span"
    ) or 26
    compare = st.toggle("Compare with the same week last year", value=True, key="trend_compare")

    if history is None or history.empty:
        ui.missing("KPI history", data.KPI_TABLE_NAME)
    else:
        kpi = next(k for k in ui.KPIS if k["label"] == choice)
        current_col, year_ago_col = f"{kpi['key']}_current", f"{kpi['key']}_year_ago"
        h = history[history[data.WEEK_COL] <= pd.Timestamp(week)].tail(span)
        hover = {"money": "$%{y:,.0f}", "rate": "%{y:.1f}%", "int": "%{y:,.0f}"}[kpi["kind"]]

        fig = go.Figure()
        if compare and year_ago_col in h.columns:
            fig.add_trace(
                go.Scatter(
                    x=h[data.WEEK_COL], y=h[year_ago_col], name="Same week last year",
                    mode="lines", line=dict(color=ui.GREY, width=2, dash="dot"),
                    hovertemplate=hover,
                )
            )
        fig.add_trace(
            go.Scatter(
                x=h[data.WEEK_COL], y=h[current_col], name=choice,
                mode="lines+markers", line=dict(color=ui.BLUE, width=3), marker=dict(size=5),
                hovertemplate=hover,
            )
        )
        # Highlight the selected week (the last point)
        fig.add_trace(
            go.Scatter(
                x=h[data.WEEK_COL].tail(1), y=h[current_col].tail(1), name="Selected week",
                mode="markers", marker=dict(color=ui.BLUE, size=12, line=dict(color="white", width=2)),
                hoverinfo="skip", showlegend=False,
            )
        )
        fig.update_layout(hovermode="x unified")
        fig.update_xaxes(hoverformat="Week of %d %b %Y")
        if kpi["kind"] == "money":
            fig.update_yaxes(tickprefix="$", tickformat="~s")
        elif kpi["kind"] == "rate":
            fig.update_yaxes(ticksuffix="%")
        ui.chart(fig, key="trend", height=380)

# --- Top categories --------------------------------------------------------------------
with right:
    st.subheader(":material/category: Top categories")
    n = st.slider("Number of categories", 3, 10, 5, key="top_n")
    top = ui.load(data.get_top_categories, week, n, what="categories")
    if top is None:
        ui.missing("categories", data.CATEGORY_TABLE_NAME)
    elif top.empty:
        st.info("No category data for this week.", icon=":material/hourglass_empty:")
    else:
        d = top.sort_values("net_revenue_rank", ascending=False)  # rank 1 at the top
        fig = go.Figure()
        if "net_revenue_previous" in d.columns:
            fig.add_trace(
                go.Bar(
                    y=d["category"], x=d["net_revenue_previous"], name="Last week",
                    orientation="h", marker_color=ui.LIGHT_BLUE,
                    hovertemplate="%{y}: $%{x:,.0f}<extra>Last week</extra>",
                )
            )
        fig.add_trace(
            go.Bar(
                y=d["category"], x=d["net_revenue_current"], name="This week",
                orientation="h", marker_color=ui.BLUE,
                text=d["net_revenue_current"], texttemplate="$%{text:,.0f}",
                textposition="outside", cliponaxis=False,
                hovertemplate="%{y}: $%{x:,.0f}<extra>This week</extra>",
            )
        )
        fig.update_layout(barmode="group", bargap=0.25, margin=dict(l=0, r=60, t=30, b=0))
        fig.update_xaxes(tickprefix="$", tickformat="~s", showgrid=True, gridcolor=ui.GRID)
        ui.chart(fig, key="categories", height=120 + 45 * len(d))
