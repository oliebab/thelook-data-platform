"""Shared UI for every page: sidebar week selector, page header, Plotly template,
KPI cards with coloured WoW / YoY badges and sparklines, and friendly errors.
"""

import datetime as dt
import re

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from google.api_core.exceptions import GoogleAPIError

import data

# --- Colours and Plotly template ------------------------------------------------
BLUE = "#2563EB"
LIGHT_BLUE = "#93C5FD"
GREY = "#9CA3AF"
TEXT = "#1F2937"
GRID = "#EEF0F4"
COLORWAY = [BLUE, "#F59E0B", "#10B981", "#8B5CF6", "#EF4444", LIGHT_BLUE]


def setup_plotly() -> None:
    """Register one Plotly template and make it the default for every chart."""
    pio.templates["thelook"] = go.layout.Template(
        layout=dict(
            font=dict(family="Source Sans Pro, sans-serif", size=13, color=TEXT),
            colorway=COLORWAY,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
            hoverlabel=dict(bgcolor="white", font_size=13),
            xaxis=dict(showgrid=False, linecolor=GRID, ticks="", title=None),
            yaxis=dict(gridcolor=GRID, zeroline=False, ticks="", title=None),
        )
    )
    pio.templates.default = "plotly_white+thelook"


def chart(fig: go.Figure, key: str, height: int | None = None) -> None:
    """Draw a Plotly figure with our template (theme=None keeps Streamlit from overriding it)."""
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(
        fig,
        theme=None,
        width="stretch",
        config={"displayModeBar": False},
        key=key,
    )


# --- KPIs -----------------------------------------------------------------------
# key = KPI name in mart_kpi_weekly without the _current/_previous/_year_ago suffix.
# good_up = whether an increase is good news (green).
KPIS = [
    dict(label="Net revenue", key="net_revenue", kind="money", icon=":material/payments:", good_up=True),
    dict(label="Orders", key="orders", kind="int", icon=":material/shopping_bag:", good_up=True),
    dict(label="Average order value", key="average_order_value", kind="money", icon=":material/receipt_long:", good_up=True),
    dict(label="Session conversion", key="session_conversion_rate", kind="rate", icon=":material/ads_click:", good_up=True),
    dict(label="New buyers", key="new_buyers", kind="int", icon=":material/person_add:", good_up=True),
    dict(label="Return rate", key="return_rate", kind="rate", icon=":material/assignment_return:", good_up=False),
]
KPI_BY_KEY = {k["key"]: k for k in KPIS}


def is_missing(value) -> bool:
    return value is None or (not isinstance(value, (list, dict)) and pd.isna(value))


def fmt(value, kind: str) -> str:
    if is_missing(value):
        return "—"
    if kind == "money":
        return f"${value:,.0f}"
    if kind == "rate":
        return f"{value:.1f}%"  # rates are already 0-100
    return f"{value:,.0f}"


def change(current, other, kind: str):
    """Change vs another period: points for rates, relative fraction otherwise."""
    if is_missing(current) or is_missing(other):
        return None
    if kind == "rate":
        return current - other
    if other == 0:
        return None
    return (current - other) / other


def change_md(value, kind: str, good_up: bool, suffix: str) -> str:
    """Coloured Streamlit badge for a change, e.g. green '▲ +15.8% WoW'."""
    if value is None:
        return f":gray-badge[— {suffix}]"
    text = f"{value:+.1f} pts" if kind == "rate" else f"{value:+.1%}"
    flat = abs(value) < (0.05 if kind == "rate" else 0.0005)
    if flat:
        return f":gray-badge[■ {text} {suffix}]"
    arrow = "▲" if value > 0 else "▼"
    color = "green" if (value > 0) == good_up else "red"
    return f":{color}-badge[{arrow} {text} {suffix}]"


def value_of(row, col: str):
    if row is None or col not in row.index:
        return None
    value = row[col]
    return None if is_missing(value) else value


def kpi_card(kpi: dict, row, history: pd.DataFrame | None, week: dt.date, sparkline: bool = True) -> None:
    """Bordered card: value, coloured WoW and YoY badges, 12-week trend line."""
    key, kind = kpi["key"], kpi["kind"]
    current = value_of(row, f"{key}_current")
    wow = change(current, value_of(row, f"{key}_previous"), kind)
    yoy = change(current, value_of(row, f"{key}_year_ago"), kind)
    with st.container(border=True):
        st.metric(f"{kpi['icon']} {kpi['label']}", fmt(current, kind))
        st.markdown(
            change_md(wow, kind, kpi["good_up"], "WoW") + " " + change_md(yoy, kind, kpi["good_up"], "YoY")
        )
        if sparkline:
            _sparkline(kpi, history, week)


def _sparkline(kpi: dict, history: pd.DataFrame | None, week: dt.date, weeks: int = 12) -> None:
    col = f"{kpi['key']}_current"
    if history is None or col not in history.columns:
        return
    h = history[history[data.WEEK_COL] <= pd.Timestamp(week)].tail(weeks)
    if h.empty:
        return
    hover = {"money": "$%{y:,.0f}", "rate": "%{y:.1f}%", "int": "%{y:,.0f}"}[kpi["kind"]]
    fig = go.Figure(
        go.Scatter(
            x=h[data.WEEK_COL],
            y=h[col],
            mode="lines",
            line=dict(color=BLUE, width=2, shape="spline", smoothing=0.6),
            hovertemplate="%{x|%d %b}: " + hover + "<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=h[data.WEEK_COL].tail(1),
            y=h[col].tail(1),
            mode="markers",
            marker=dict(color=BLUE, size=7),
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=4, b=0),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        hovermode="x",
    )
    chart(fig, key=f"spark_{kpi['key']}_{week}", height=60)


# --- Week selector (sidebar, shared by every page) ----------------------------------
def week() -> dt.date:
    return st.session_state["week"]


def week_range(w: dt.date) -> str:
    """Week as 'DD Mmm YYYY - DD Mmm YYYY', e.g. '16 Nov 2026 - 22 Nov 2026'."""
    end = w + dt.timedelta(days=6)
    return f"{w:%d %b %Y} - {end:%d %b %Y}"


def _shift_week(weeks: list[dt.date], step: int) -> None:
    i = weeks.index(st.session_state["week"]) + step
    if 0 <= i < len(weeks):
        st.session_state["week"] = weeks[i]


def sidebar() -> None:
    """Week selector, previous/next buttons, data source and refresh, in the sidebar."""
    try:
        weeks = data.get_weeks()
    except GoogleAPIError as e:
        st.sidebar.error(f"Couldn't load the list of weeks. {_short(e)}", icon=":material/error:")
        weeks = data._recent_mondays()

    if st.session_state.get("week") not in weeks:
        st.session_state["week"] = weeks[0]
    i = weeks.index(st.session_state["week"])

    with st.sidebar:
        st.selectbox(
            ":material/calendar_month: Week",
            options=weeks,
            key="week",
            format_func=week_range,
        )
        prev_col, next_col = st.columns(2)
        prev_col.button(
            "◀ Previous", on_click=_shift_week, args=(weeks, 1),
            disabled=i == len(weeks) - 1, width="stretch",
        )
        next_col.button(
            "Next ▶", on_click=_shift_week, args=(weeks, -1),
            disabled=i == 0, width="stretch",
        )
        st.divider()
        st.caption(f":material/database: Data: `{data.PROJECT}.{data.DATASET}`")
        if st.button(":material/refresh: Refresh data", width="stretch",
                     help="Queries are cached for an hour. Clear the cache after a new load."):
            st.cache_data.clear()
            st.rerun()


# --- Page header, loading and friendly errors --------------------------------------------
def header(title: str, icon: str, subtitle: str | None = None) -> None:
    st.title(f"{icon} {title}")
    parts = [f"Week of {week_range(week())}", f"source `{data.DATASET}`"]
    if subtitle:
        parts.append(subtitle)
    st.caption(" · ".join(parts))


def _short(error: Exception) -> str:
    message = getattr(error, "message", None) or str(error)
    return message.splitlines()[0][:300]


def load(fn, *args, what: str):
    """Call a data function; on a BigQuery error show a readable message instead of a traceback."""
    try:
        with st.spinner(f"Loading {what}…"):
            return fn(*args)
    except GoogleAPIError as e:
        st.error(f"Couldn't load {what} from BigQuery. {_short(e)}", icon=":material/error:")
        return None


def missing(what: str, table: str) -> None:
    st.info(
        f"No {what} yet: `{table}` isn't built in `{data.DATASET}`. "
        "It will appear here after the next pipeline run.",
        icon=":material/hourglass_empty:",
    )


# --- Review markdown helpers ----------------------------------------------------
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")


def split_sections(md: str) -> list[tuple[str | None, str]]:
    """Split markdown into (heading, body) pairs. Text before the first heading has heading None."""
    sections, title, buf = [], None, []
    for line in md.splitlines():
        match = _HEADING.match(line)
        if match:
            if title is not None or "".join(buf).strip():
                sections.append((title, "\n".join(buf).strip()))
            title, buf = match.group(1).strip(), []
        else:
            buf.append(line)
    if title is not None or "".join(buf).strip():
        sections.append((title, "\n".join(buf).strip()))
    return sections


def section_kind(title: str | None) -> str:
    t = (title or "").lower()
    if "headline" in t or "summary" in t:
        return "headline"
    if "care" in t or "caveat" in t or "caution" in t:
        return "care"
    if "well" in t:
        return "well"
    if "watch" in t or "risk" in t:
        return "watch"
    if "action" in t or "next step" in t or "recommend" in t:
        return "actions"
    return "other"


def escape_md(text: str) -> str:
    """Escape dollar signs so Streamlit doesn't render amounts like $1,200 ... $3 as LaTeX."""
    return text.replace("$", "\\$")
