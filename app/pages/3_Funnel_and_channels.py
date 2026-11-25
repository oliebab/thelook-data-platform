"""Funnel + channels page for the selected week.

- Funnel: fct_funnel_daily (one row per day and traffic source, session counts per
  step). Counts are summed over the week and step rates recomputed from the sums.
- Channels: mart_channel_weekly (one row per week and traffic source, with sessions
  and session conversion for this week and the previous one).

Rates are 0-100 percentages; changes in rates are shown in points, changes in
counts in relative %.
"""

import datetime as dt

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data

st.set_page_config(page_title="Funnel & channels · TheLook Weekly", page_icon="🔻", layout="wide")

# Selected week from Home; fall back to the latest week if the user landed here first.
if "week" not in st.session_state:
    st.session_state["week"] = data.get_weeks()[0]
week: dt.date = st.session_state["week"]

st.title("Funnel and channels")
st.caption(f"Week of {week:%d %b %Y} · change the week on the Home page · source `{data.DATASET}`")

STEPS = [
    ("Sessions", "sessions"),
    ("Viewed a product", "product_sessions"),
    ("Added to cart", "cart_sessions"),
    ("Purchased", "purchase_sessions"),
]
COUNT_COLS = [col for _, col in STEPS]


def pct(num, den):
    if den is None or pd.isna(den) or den == 0:
        return None
    return 100 * num / den


def rel_change(cur, prev) -> str | None:
    if prev is None or pd.isna(prev) or prev == 0:
        return None
    return f"{(cur - prev) / prev:+.1%}"


funnel = data.get_funnel_daily(week)
channels = data.get_channels(week)

# --- Traffic source filter (applies to both sections) ---------------------------
sources = set()
if funnel is not None:
    sources |= set(funnel["traffic_source"].dropna())
if channels is not None:
    sources |= set(channels["traffic_source"].dropna())
sources = sorted(sources)

if not sources:
    st.info("`fct_funnel_daily` and `mart_channel_weekly` have no data for this week yet.")
    st.stop()

selected = st.multiselect("Traffic sources", sources, default=sources)
if not selected:
    st.warning("Select at least one traffic source.")
    st.stop()

# =============================================================================
# Funnel
# =============================================================================
st.header("Funnel")

if funnel is None:
    st.info("`fct_funnel_daily` isn't built yet.")
else:
    funnel["session_date"] = pd.to_datetime(funnel["session_date"]).dt.date
    funnel = funnel[funnel["traffic_source"].isin(selected)]
    this = funnel[funnel["session_date"] >= week]
    last = funnel[funnel["session_date"] < week]

    if this.empty:
        st.warning("No funnel data for this week.")
    else:
        cur = this[COUNT_COLS].sum()
        prev = last[COUNT_COLS].sum() if not last.empty else None

        week_is_provisional = bool(this["is_provisional"].any())

        cards = st.columns(5)
        for col, (label, name) in zip(cards, STEPS):
            delta = None if prev is None else rel_change(cur[name], prev[name])
            with col:
                st.metric(label, f"{cur[name]:,.0f}", delta=None if delta is None else f"{delta} WoW")

        conv_cur = pct(cur["purchase_sessions"], cur["sessions"])
        conv_prev = None if prev is None else pct(prev["purchase_sessions"], prev["sessions"])
        with cards[4]:
            st.metric(
                "Session conversion" + (" (provisional)" if week_is_provisional else ""),
                "—" if conv_cur is None else f"{conv_cur:.1f}%",
                delta=None if conv_cur is None or conv_prev is None else f"{conv_cur - conv_prev:+.1f} pts WoW",
            )
        if week_is_provisional:
            st.caption(
                "This week includes the last loaded day. Sessions that continue past midnight "
                "aren't loaded yet for that day, so its conversion is under-counted."
            )

        left, right = st.columns([3, 2])
        with left:
            values = [cur[name] for _, name in STEPS]
            fig = go.Figure(
                go.Funnel(
                    y=[label for label, _ in STEPS],
                    x=values,
                    textinfo="value+percent previous",
                    hovertemplate="%{y}: %{x:,.0f} sessions<br>"
                    "%{percentPrevious:.1%} of previous step<extra></extra>",
                )
            )
            fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.markdown("**Step conversion**")
            step_rates = pd.DataFrame(
                {
                    "Step": ["Session → product", "Product → cart", "Cart → purchase"],
                    "This week": [pct(values[i + 1], values[i]) for i in range(3)],
                    "Last week": [
                        None if prev is None else pct(prev[STEPS[i + 1][1]], prev[STEPS[i][1]])
                        for i in range(3)
                    ],
                }
            )
            st.dataframe(
                step_rates,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "This week": st.column_config.NumberColumn(format="%.1f%%"),
                    "Last week": st.column_config.NumberColumn(format="%.1f%%"),
                },
            )
            st.caption("In TheLook every session views a product, so the first step is always 100%.")

        # --- Daily conversion, last loaded day marked as provisional ---------------
        st.subheader("Daily session conversion")
        daily = this.groupby(["session_date", "is_provisional"])[COUNT_COLS].sum().reset_index()
        daily["conversion_pct"] = 100 * daily["purchase_sessions"] / daily["sessions"]
        daily = daily.sort_values("session_date")
        final = daily[~daily["is_provisional"]]
        provisional = daily[daily["is_provisional"]]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=final["session_date"],
                y=final["conversion_pct"],
                mode="lines+markers",
                name="Conversion",
                hovertemplate="%{x|%a %d %b}: %{y:.1f}%<extra></extra>",
            )
        )
        if not provisional.empty:
            fig.add_trace(
                go.Scatter(
                    x=provisional["session_date"],
                    y=provisional["conversion_pct"],
                    mode="markers",
                    name="Provisional (last loaded day)",
                    marker=dict(symbol="circle-open", size=11),
                    hovertemplate="%{x|%a %d %b}: %{y:.1f}% (provisional)<extra></extra>",
                )
            )
        fig.update_yaxes(title_text="Session conversion (%)")
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=1.12, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# Channels
# =============================================================================
st.header("Channels")

if channels is None:
    st.info("`mart_channel_weekly` isn't built yet.")
else:
    ch = channels[channels["traffic_source"].isin(selected)].copy()
    if ch.empty:
        st.warning("No channel data for this week.")
    else:
        ch["sessions_wow"] = [
            rel_change(c, p) for c, p in zip(ch["sessions_current"], ch["sessions_previous"])
        ]
        ch["conversion_change_pts"] = (
            ch["session_conversion_rate_current"] - ch["session_conversion_rate_previous"]
        )

        left, right = st.columns(2)
        with left:
            st.subheader("Sessions by channel")
            fig = px.bar(
                ch.sort_values("sessions_current"),
                x="sessions_current",
                y="traffic_source",
                orientation="h",
                text="sessions_current",
                labels={"sessions_current": "Sessions", "traffic_source": ""},
            )
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_layout(height=320, margin=dict(l=0, r=40, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Session conversion by channel")
            conv = ch.melt(
                id_vars="traffic_source",
                value_vars=["session_conversion_rate_previous", "session_conversion_rate_current"],
                var_name="period",
                value_name="conversion",
            )
            conv["period"] = conv["period"].map(
                {
                    "session_conversion_rate_previous": "Last week",
                    "session_conversion_rate_current": "This week",
                }
            )
            fig = px.bar(
                conv,
                x="conversion",
                y="traffic_source",
                color="period",
                barmode="group",
                orientation="h",
                labels={"conversion": "Session conversion (%)", "traffic_source": "", "period": ""},
                category_orders={"period": ["This week", "Last week"]},
            )
            fig.update_traces(hovertemplate="%{y}: %{x:.1f}%<extra></extra>")
            fig.update_layout(
                height=320,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=1.08, x=0),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            ch[
                [
                    "traffic_source",
                    "sessions_current",
                    "sessions_wow",
                    "session_conversion_rate_current",
                    "conversion_change_pts",
                ]
            ],
            hide_index=True,
            use_container_width=True,
            column_config={
                "traffic_source": "Channel",
                "sessions_current": st.column_config.NumberColumn("Sessions", format="%d"),
                "sessions_wow": "Sessions WoW",
                "session_conversion_rate_current": st.column_config.NumberColumn(
                    "Conversion", format="%.1f%%"
                ),
                "conversion_change_pts": st.column_config.NumberColumn(
                    "Conversion WoW (pts)", format="%+.1f"
                ),
            },
        )
