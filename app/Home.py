"""TheLook Data Platform: Streamlit entry point.

Run from the repo root:
    APP_DATASET=dbt_gabriel poetry run streamlit run app/Home.py --server.port 8501 --server.headless true

Each file in pages/ becomes a page in the sidebar. The selected week is kept in
st.session_state["week"] so every page shows the same week.
"""

import streamlit as st

import data

st.set_page_config(page_title="TheLook Weekly", page_icon="📊", layout="wide")

st.title("TheLook Weekly")
st.write(
    "Weekly e-commerce KPIs and an LLM-written review of the week, "
    "built from TheLook data with dbt on BigQuery."
)

# --- Week selector, shared with the other pages -----------------------------
# The widget uses its own key ("_week_picker") and copies its value into
# st.session_state["week"]. Streamlit deletes a widget's key when you switch to
# a page that doesn't draw that widget, so the plain "week" key is what survives.

weeks = data.get_weeks()

if "week" not in st.session_state or st.session_state["week"] not in weeks:
    st.session_state["week"] = weeks[0]  # most recent week


def _store_week() -> None:
    st.session_state["week"] = st.session_state["_week_picker"]


st.selectbox(
    "Week (starting Monday)",
    options=weeks,
    index=weeks.index(st.session_state["week"]),
    format_func=lambda d: d.strftime("%d %b %Y"),
    key="_week_picker",
    on_change=_store_week,
)

st.caption(f"Data source: `{data.PROJECT}.{data.DATASET}`")

st.divider()
st.markdown(
    """
- **KPIs**: net revenue, orders, average order value, conversion, new buyers and return rate for the selected week.
- **Review**: the LLM's written review of the week, with the data it was given.
"""
)
st.info("Pick a page in the sidebar.")