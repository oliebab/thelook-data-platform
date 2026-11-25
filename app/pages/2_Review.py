"""Review page: the LLM's business review of the selected week.

Layout:
- badges: week, prompt version, model, and "numbers checked" from guardrail_passed;
- the headline as a callout, the caveats ("read with care") as a warning;
- "what went well" and "things to watch" side by side, then the suggested actions;
- a side panel with the week's KPIs, to cross-check the figures, and a download button;
- the input JSON the model was given, in an expander.

If the markdown has no headings, it is shown as-is.
"""

import json

import pandas as pd
import streamlit as st

import data
import ui

week = ui.week()
ui.header("Weekly review", ":material/article:")

review = ui.load(data.get_review, week, what="the review")

if review is None:
    ui.missing("review", data.REPORTS_TABLE_ID)
    st.stop()
if review.empty:
    st.info(
        "No review generated for this week yet. Pick another week in the sidebar.",
        icon=":material/hourglass_empty:",
    )
    st.stop()

row = review.iloc[0]


def get(col):
    value = row.get(col)
    return None if ui.is_missing(value) else value


md = get("output_md") or ""
passed = bool(get("guardrail_passed"))
generated = get("generated_at")
generated_txt = "—" if generated is None else f"{pd.Timestamp(generated):%d %b %Y, %H:%M} UTC"

# --- Badges -------------------------------------------------------------------------------
badges = [
    f":blue-badge[:material/calendar_month: {ui.week_range(week)}]",
    f":violet-badge[:material/description: Prompt {get('prompt_version') or '—'}]",
    f":gray-badge[:material/smart_toy: {get('model') or '—'}]",
    ":green-badge[:material/verified: Numbers checked]" if passed
    else ":red-badge[:material/gpp_maybe: Numbers not checked]",
]
st.markdown(" ".join(badges))
if not passed:
    st.error(
        "This review didn't pass the numbers check: some figures may not match the KPIs. "
        "Read it with caution.",
        icon=":material/warning:",
    )

main, side = st.columns([3, 1], gap="large")

# --- Review body --------------------------------------------------------------------------
with main:
    sections = ui.split_sections(md)
    by_kind: dict[str, list] = {}
    for title, body in sections:
        by_kind.setdefault(ui.section_kind(title), []).append((title, ui.escape_md(body)))

    if not any(title for title, _ in sections):
        # No headings: show the markdown as written.
        with st.container(border=True):
            st.markdown(ui.escape_md(md) or "_Review text missing._")
    else:
        for _, body in by_kind.get("headline", []):
            st.info(f"**{body}**", icon=":material/campaign:")

        for title, body in by_kind.get("care", []):
            st.warning(f"**{title}**\n\n{body}", icon=":material/info:")

        well, watch = by_kind.get("well", []), by_kind.get("watch", [])
        if well or watch:
            left, right = st.columns(2)
            with left:
                for title, body in well:
                    with st.container(border=True):
                        st.markdown(f"#### :green[:material/trending_up:] {title}")
                        st.markdown(body)
            with right:
                for title, body in watch:
                    with st.container(border=True):
                        st.markdown(f"#### :orange[:material/visibility:] {title}")
                        st.markdown(body)

        for title, body in by_kind.get("actions", []):
            with st.container(border=True):
                st.markdown(f"#### :blue[:material/task_alt:] {title}")
                st.markdown(body)

        for title, body in by_kind.get("other", []):
            if title:
                st.markdown(f"#### {title}")
            st.markdown(body)

    st.caption(f"Generated {generated_txt}")

    with st.expander(":material/data_object: Input data sent to the model"):
        payload = get("input_json")
        if payload is None:
            st.write("No input JSON stored.")
        elif isinstance(payload, str):
            try:
                st.json(json.loads(payload))
            except json.JSONDecodeError:
                st.code(payload)
        else:
            st.json(payload)

# --- Side panel: the week's numbers, to cross-check the review ----------------------------
with side:
    with st.container(border=True):
        st.markdown("**:material/fact_check: This week's numbers**")
        kpis = ui.load(data.get_kpis, week, what="KPIs")
        if kpis is None or kpis.empty:
            st.caption("KPIs not available for this week.")
        else:
            k = kpis.iloc[0]
            for kpi in ui.KPIS:
                current = ui.value_of(k, f"{kpi['key']}_current")
                wow = ui.change(current, ui.value_of(k, f"{kpi['key']}_previous"), kpi["kind"])
                st.markdown(
                    f"{kpi['label']}  \n**{ui.escape_md(ui.fmt(current, kpi['kind']))}** "
                    + ui.change_md(wow, kpi["kind"], kpi["good_up"], "WoW")
                )
        st.page_link("pages/1_KPIs.py", label="See all KPIs", icon=":material/arrow_forward:")

    st.download_button(
        ":material/download: Download review (.md)",
        data=md,
        file_name=f"thelook_review_{week:%Y-%m-%d}.md",
        mime="text/markdown",
        width="stretch",
    )
