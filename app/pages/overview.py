"""Overview: the week at a glance, the review headline, and links to the other pages."""

import streamlit as st

import data
import ui

week = ui.week()

st.title(":material/storefront: TheLook Weekly")
st.markdown(
    "Weekly e-commerce performance of TheLook, built with dbt on BigQuery, "
    "with an LLM-written review of the week. **Pick a week in the sidebar**: every page follows it."
)
st.caption(f"Week of {ui.week_range(week)} · source `{data.DATASET}`")

# --- The week at a glance ----------------------------------------------------------
st.subheader("The week at a glance")
kpis = ui.load(data.get_kpis, week, what="KPIs")
history = ui.load(data.get_kpi_history, 52, what="KPI history")

if kpis is None:
    ui.missing("KPIs", data.KPI_TABLE_NAME)
elif kpis.empty:
    st.warning("No KPI row for this week.", icon=":material/event_busy:")
else:
    row = kpis.iloc[0]
    glance = ["net_revenue", "orders", "session_conversion_rate", "return_rate"]
    for col, key in zip(st.columns(4), glance):
        with col:
            ui.kpi_card(ui.KPI_BY_KEY[key], row, history, week)

# --- Review headline ----------------------------------------------------------------
st.subheader("This week in one sentence")
review = ui.load(data.get_review, week, what="the review")
headline = None
if review is not None and not review.empty:
    md = review.iloc[0].get("output_md") or ""
    for title, body in ui.split_sections(md):
        if ui.section_kind(title) == "headline" and body:
            headline = body
            break
if headline:
    st.info(ui.escape_md(headline), icon=":material/campaign:")
    st.page_link("pages/2_Review.py", label="Read the full review", icon=":material/arrow_forward:")
else:
    st.caption("No review generated for this week yet.")

# --- Explore ---------------------------------------------------------------------------
st.subheader("Explore")
cards = [
    ("pages/1_KPIs.py", ":material/monitoring:", "KPIs",
     "Six weekly KPIs with week-on-week and year-on-year changes, trends and top categories."),
    ("pages/2_Review.py", ":material/article:", "Weekly review",
     "The LLM's written review of the week, with the numbers it was given."),
    ("pages/3_Funnel_and_channels.py", ":material/filter_alt:", "Funnel & channels",
     "Where sessions drop off, and how each traffic source converts."),
]
for col, (page, icon, label, text) in zip(st.columns(3), cards):
    with col, st.container(border=True):
        st.markdown(f"**{icon} {label}**")
        st.caption(text)
        st.page_link(page, label=f"Open {label}", icon=":material/arrow_forward:")

with st.expander(":material/info: About the data"):
    st.markdown(
        """
- TheLook is a **synthetic** e-commerce dataset: conversion rates are far above real benchmarks.
- The most recent days before each snapshot are denser than earlier ones, so the **latest week is inflated**.
- Rates are percentages (0–100); their changes are shown in **points**.
- The last loaded day of the funnel is **provisional**: sessions continuing past midnight aren't loaded yet.
"""
    )
