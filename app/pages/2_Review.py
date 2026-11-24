"""Review page: the LLM's written review of the week.

Shows the review text, a caption with model / prompt version / generation time,
and the input JSON the model was given. Placeholder until the reports table exists.
"""

import json

import pandas as pd
import streamlit as st

import data

st.set_page_config(page_title="Review · TheLook Weekly", page_icon="📝", layout="wide")

st.title("Weekly review")

# Column names in the reports table. 
TEXT_COL = "review_text"
MODEL_COL = "model"
PROMPT_COL = "prompt_version"
GENERATED_COL = "generated_at"
INPUT_COL = "input_json"

review = data.get_latest_review()

if review is None:
    st.info("The `reports` table doesn't exist yet: no review to show.")
    st.markdown("_The review of the week will appear here._")
    st.stop()

if review.empty:
    st.warning("The `reports` table is empty: no review generated yet.")
    st.stop()

row = review.iloc[0]


def get(col):
    value = row.get(col)
    return None if value is None or (not isinstance(value, (dict, list)) and pd.isna(value)) else value


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
    else:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                st.code(payload)
                payload = None
        if payload is not None:
            st.json(payload)
