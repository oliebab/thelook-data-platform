"""Review page: the LLM's written review of the selected week.

Reads reports.llm_business_review (PR #14): the review text (output_md), a
caption with model / prompt version / generation time, and the input JSON the
model was given. Placeholder until the table exists or has a row for the week.
"""

import datetime as dt
import json

import pandas as pd
import streamlit as st

import data

st.set_page_config(page_title="Review · TheLook Weekly", page_icon="📝", layout="wide")

# Selected week from Home; fall back to the latest week if the user landed here first.
if "week" not in st.session_state:
    st.session_state["week"] = data.get_weeks()[0]
week: dt.date = st.session_state["week"]

st.title("Weekly review")
st.caption(f"Week of {week:%d %b %Y} · change the week on the Home page")

# Column names in reports.llm_business_review.
TEXT_COL = "output_md"
MODEL_COL = "model"
PROMPT_COL = "prompt_version"
GENERATED_COL = "generated_at"
INPUT_COL = "input_json"

review = data.get_review(week)

if review is None:
    st.info("The review table doesn't exist yet: no review to show.")
    st.stop()

if review.empty:
    st.warning("No review generated for this week yet.")
    st.stop()

row = review.iloc[0]


def get(col):
    value = row.get(col)
    if value is None or (not isinstance(value, (dict, list)) and pd.isna(value)):
        return None
    return value


st.markdown(get(TEXT_COL) or "_Review text missing._")

generated = get(GENERATED_COL)
generated_txt = "—" if generated is None else f"{pd.Timestamp(generated):%d %b %Y %H:%M} UTC"
st.caption(
    f"Model: {get(MODEL_COL) or '—'} · "
    f"Prompt version: {get(PROMPT_COL) or '—'} · "
    f"Generated: {generated_txt}"
)

with st.expander("Input data sent to the model"):
    payload = get(INPUT_COL)
    if payload is None:
        st.write("No input JSON stored.")
    elif isinstance(payload, str):
        try:
            st.json(json.loads(payload))
        except json.JSONDecodeError:
            st.code(payload)
    else:
        st.json(payload)
