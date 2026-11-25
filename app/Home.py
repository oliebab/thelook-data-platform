"""TheLook Weekly: Streamlit entry point.

Run from the app/ folder, so Streamlit picks up .streamlit/config.toml:
    cd app
    APP_DATASET=dbt_olivier poetry run streamlit run Home.py --server.port 8502

This file runs on every interaction: it sets up the page, the Plotly template and the
sidebar (week selector shared by every page), then runs the selected page.
"""

import streamlit as st

import ui

st.set_page_config(
    page_title="TheLook Weekly",
    page_icon=":material/storefront:",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.setup_plotly()

pages = [
    st.Page("pages/overview.py", title="Overview", icon=":material/home:", url_path="overview", default=True),
    st.Page("pages/1_KPIs.py", title="KPIs", icon=":material/monitoring:", url_path="kpis"),
    st.Page("pages/2_Review.py", title="Weekly review", icon=":material/article:", url_path="review"),
    st.Page("pages/3_Funnel_and_channels.py", title="Funnel & channels", icon=":material/filter_alt:", url_path="funnel"),
]
# Navigation as a bar at the top; the sidebar holds the week selector.
navigation = st.navigation(pages, position="top")

with st.sidebar:
    st.markdown("### :material/storefront: TheLook Weekly")
    st.caption("E-commerce KPIs · dbt on BigQuery")

ui.sidebar()
navigation.run()
