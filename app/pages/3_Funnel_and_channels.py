"""Funnel + channels page for the selected week.

- Funnel: fct_funnel_daily (one row per day and traffic source, session counts per
  step). Counts are summed over the week and step rates recomputed from the sums.
- Channels: mart_channel_weekly (one row per week and traffic source, with sessions
  and session conversion for this week and the previous one).

Rates are 0-100 percentages; changes in rates are shown in points, changes in
counts in relative %. The last loaded day is provisional (sessions continuing past
midnight aren't loaded yet).
"""

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data
import ui

week: dt.date = ui.week()
ui.header("Funnel & channels", ":material/filter_alt:")

STEPS = [
    ("Sessions", "sessions", ":material/group:"),
    ("Viewed a product", "product_sessions", ":material/visibility:"),
    ("Added to cart", "cart_sessions", ":material/add_shopping_cart:"),
    ("Purchased", "purchase_sessions", ":material/shopping_bag:"),
]
COUNT_COLS = [col for _, col, _ in STEPS]


def pct(num, den):
    if den is None or pd.isna(den) or den == 0:
        return None
    return 100 * num / den


funnel = ui.load(data.get_funnel_daily, week, what="the funnel")
channels = ui.load(data.get_channels, week, what="channels")

# --- Traffic source filter (applies to both sections) ---------------------------
sources = set()
if funnel is not None:
    sources |= set(funnel["traffic_source"].dropna())
if channels is not None:
    sources |= set(channels["traffic_source"].dropna())
sources = sorted(sources)

if not sources:
    ui.missing("funnel or channel data", f"{data.FUNNEL_TABLE_NAME} / {data.CHANNEL_TABLE_NAME}")
    st.stop()

selected = st.pills(
    ":material/tune: Traffic sources",
    sources,
    selection_mode="multi",
    default=sources,
    key="sources",
)
if not selected:
    st.warning("Select at least one traffic source.", icon=":material/touch_app:")
    st.stop()

# =============================================================================
# Funnel
# =============================================================================
st.subheader(":material/filter_alt: Funnel")

if funnel is None:
    ui.missing("funnel data", data.FUNNEL_TABLE_NAME)
else:
    funnel["session_date"] = pd.to_datetime(funnel["session_date"]).dt.date
    funnel = funnel[funnel["traffic_source"].isin(selected)]
    this = funnel[funnel["session_date"] >= week]
    last = funnel[funnel["session_date"] < week]

    if this.empty:
        st.info("No funnel data for this week.", icon=":material/hourglass_empty:")
    else:
        cur = this[COUNT_COLS].sum()
        prev = last[COUNT_COLS].sum() if not last.empty else None
        provisional = bool(this["is_provisional"].any())

        # Step cards + conversion card
        cards = st.columns(5)
        for col, (label, name, icon) in zip(cards, STEPS):
            wow = None if prev is None else ui.change(cur[name], prev[name], "int")
            with col, st.container(border=True):
                st.metric(f"{icon} {label}", f"{cur[name]:,.0f}")
                st.markdown(ui.change_md(wow, "int", True, "WoW"))

        conv_cur = pct(cur["purchase_sessions"], cur["sessions"])
        conv_prev = None if prev is None else pct(prev["purchase_sessions"], prev["sessions"])
        with cards[4], st.container(border=True):
            st.metric(":material/ads_click: Session conversion", ui.fmt(conv_cur, "rate"))
            badges = ui.change_md(ui.change(conv_cur, conv_prev, "rate"), "rate", True, "WoW")
            if provisional:
                badges += " :orange-badge[:material/schedule: Provisional]"
            st.markdown(badges)
        if provisional:
            st.caption(
                ":material/schedule: This week includes the last loaded day. Sessions that continue "
                "past midnight aren't loaded yet for that day, so its conversion is under-counted."
            )

        left, right = st.columns([3, 2], gap="large")
        with left:
            values = [cur[name] for _, name, _ in STEPS]
            fig = go.Figure(
                go.Funnel(
                    y=[label for label, _, _ in STEPS],
                    x=values,
                    textinfo="value+percent previous",
                    marker=dict(color=[ui.BLUE, "#3B82F6", "#60A5FA", ui.LIGHT_BLUE]),
                    connector=dict(fillcolor="#E5EDFF"),
                    hovertemplate="%{y}: %{x:,.0f} sessions<br>"
                    "%{percentPrevious:.1%} of previous step<extra></extra>",
                )
            )
            ui.chart(fig, key="funnel", height=340)

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
            step_rates["Change (pts)"] = step_rates["This week"] - step_rates["Last week"]
            st.dataframe(
                step_rates,
                hide_index=True,
                width="stretch",
                column_config={
                    "This week": st.column_config.NumberColumn(format="%.1f%%"),
                    "Last week": st.column_config.NumberColumn(format="%.1f%%"),
                    "Change (pts)": st.column_config.NumberColumn(format="%+.1f"),
                },
            )
            st.caption("In TheLook every session views a product, so the first step is always 100%.")

        # Daily conversion, last loaded day marked as provisional
        st.markdown("**Daily session conversion**")
        daily = this.groupby(["session_date", "is_provisional"])[COUNT_COLS].sum().reset_index()
        daily["conversion_pct"] = 100 * daily["purchase_sessions"] / daily["sessions"]
        daily = daily.sort_values("session_date")
        final, prov = daily[~daily["is_provisional"]], daily[daily["is_provisional"]]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=final["session_date"], y=final["conversion_pct"], name="Conversion",
                mode="lines+markers", line=dict(color=ui.BLUE, width=3),
                hovertemplate="%{x|%a %d %b}: %{y:.1f}%<extra></extra>",
            )
        )
        if not prov.empty:
            fig.add_trace(
                go.Scatter(
                    x=prov["session_date"], y=prov["conversion_pct"],
                    name="Provisional (last loaded day)", mode="markers",
                    marker=dict(symbol="circle-open", size=12, color=ui.BLUE, line=dict(width=2)),
                    hovertemplate="%{x|%a %d %b}: %{y:.1f}% (provisional)<extra></extra>",
                )
            )
        fig.update_yaxes(ticksuffix="%")
        ui.chart(fig, key="daily_conversion", height=280)

st.divider()

# =============================================================================
# Channels
# =============================================================================
st.subheader(":material/hub: Channels")

if channels is None:
    ui.missing("channel data", data.CHANNEL_TABLE_NAME)
else:
    ch = channels[channels["traffic_source"].isin(selected)].copy()
    if ch.empty:
        st.info("No channel data for this week.", icon=":material/hourglass_empty:")
    else:
        ch["sessions_wow"] = [
            ui.change(c, p, "int") for c, p in zip(ch["sessions_current"], ch["sessions_previous"])
        ]
        ch["conversion_change_pts"] = (
            ch["session_conversion_rate_current"] - ch["session_conversion_rate_previous"]
        )

        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("**Sessions by channel**")
            d = ch.sort_values("sessions_current")
            fig = go.Figure(
                go.Bar(
                    y=d["traffic_source"], x=d["sessions_current"], orientation="h",
                    marker_color=ui.BLUE, text=d["sessions_current"], texttemplate="%{text:,.0f}",
                    textposition="outside", cliponaxis=False,
                    hovertemplate="%{y}: %{x:,.0f} sessions<extra></extra>",
                )
            )
            fig.update_layout(margin=dict(l=0, r=50, t=10, b=0))
            fig.update_xaxes(showgrid=True, gridcolor=ui.GRID)
            ui.chart(fig, key="channel_sessions", height=320)

        with right:
            st.markdown("**Session conversion by channel**")
            d = ch.sort_values("session_conversion_rate_current")
            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    y=d["traffic_source"], x=d["session_conversion_rate_previous"], name="Last week",
                    orientation="h", marker_color=ui.LIGHT_BLUE,
                    hovertemplate="%{y}: %{x:.1f}%<extra>Last week</extra>",
                )
            )
            fig.add_trace(
                go.Bar(
                    y=d["traffic_source"], x=d["session_conversion_rate_current"], name="This week",
                    orientation="h", marker_color=ui.BLUE,
                    text=d["session_conversion_rate_current"], texttemplate="%{text:.1f}%",
                    textposition="outside", cliponaxis=False,
                    hovertemplate="%{y}: %{x:.1f}%<extra>This week</extra>",
                )
            )
            fig.update_layout(barmode="group", bargap=0.25, margin=dict(l=0, r=50, t=30, b=0))
            fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=ui.GRID)
            ui.chart(fig, key="channel_conversion", height=320)

        st.dataframe(
            ch[["traffic_source", "sessions_current", "sessions_wow",
                "session_conversion_rate_current", "conversion_change_pts"]],
            hide_index=True,
            width="stretch",
            column_config={
                "traffic_source": "Channel",
                "sessions_current": st.column_config.NumberColumn("Sessions", format="%d"),
                "sessions_wow": st.column_config.NumberColumn("Sessions WoW", format="percent"),
                "session_conversion_rate_current": st.column_config.NumberColumn(
                    "Conversion", format="%.1f%%"
                ),
                "conversion_change_pts": st.column_config.NumberColumn(
                    "Conversion WoW (pts)", format="%+.1f"
                ),
            },
        )
