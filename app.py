"""Streamlit prototype: paste lecture notes -> study pack using prompt versions v0-v3.

Run:  pip install streamlit
      export GEMINI_API_KEY=...   (or OPENAI_API_KEY)
      streamlit run app.py
"""
import json

import streamlit as st

from llm import call_llm, provider_info
from pipeline import extract_json, format_pass, run_version, validate_notes

st.set_page_config(page_title="PromptForge - Study Pack Generator", layout="wide")
st.title("PromptForge: Lecture Notes -> Study Pack")
st.caption("Prompt-engineering prototype. Use public / non-confidential notes only. "
           "AI output can contain mistakes: verify against your notes.")

try:
    provider, model = provider_info()
    st.sidebar.success(f"Provider: {provider} | Model: {model}")
except RuntimeError as e:
    st.sidebar.error(str(e))

version = st.sidebar.selectbox(
    "Prompt version",
    ["v3", "v2", "v1", "v0"],
    format_func=lambda v: {
        "v0": "v0 - Baseline",
        "v1": "v1 - Role + constraints + format",
        "v2": "v2 - Grounded + JSON + few-shot",
        "v3": "v3 - 3-step chain (extract > generate > review)"}[v])
notes = st.text_area("Paste lecture notes (text from notes / PPT)", height=260)

def render_pack(pack: dict):
    st.subheader("Summary"); st.write(pack.get("summary", ""))
    st.subheader("Key concepts")
    for c in pack.get("key_concepts", []): st.markdown(f"- {c}")
    st.subheader("Definitions")
    for d in pack.get("definitions", []): st.markdown(f"**{d['term']}**: {d['definition']}")
    st.subheader("Exam points")
    for p in pack.get("exam_points", []): st.markdown(f"- {p}")
    st.subheader("MCQs")
    for i, q in enumerate(pack.get("mcqs", []), 1):
        st.markdown(f"**Q{i}. {q['question']}**")
        for o, txt in zip("ABCD", q["options"]): st.markdown(f"- {o}. {txt}")
        with st.expander("Answer"):
            st.write(f"Correct: {q['answer']}  |  Source: \"{q.get('source','')}\"")
    st.subheader("Short-answer questions")
    for i, q in enumerate(pack.get("short_questions", []), 1):
        st.markdown(f"**S{i}. {q['question']}**")
        with st.expander("Model answer"):
            st.write(f"{q['answer']}  |  Source: \"{q.get('source','')}\"")
    if pack.get("coverage_note"): st.info(pack["coverage_note"])

if st.button("Generate study pack", type="primary"):
  err = validate_notes(notes)
  if err:
    st.warning(err)
  else:
    try:
        with st.spinner("Running prompt workflow..."):
            res = run_version(version, notes, call_llm)
    except Exception as e:
        st.error("The model call failed (often a free-tier rate or daily quota limit). "
                 "Please wait a minute and try again. Details: " + str(e)[:300])
        st.stop()
    st.success(f"Done in {res['calls']} model call(s). Format check: "
               f"{'PASS' if format_pass(version, res['text']) else 'FAIL'}")
    if version in ("v0", "v1"):
        st.markdown(res["text"])
    else:
        try:
            data = extract_json(res["text"])
            if version == "v3":
                with st.expander("Reviewer report (what was checked / removed)"):
                    st.json(data.get("review", []))
                    st.write("Hallucinations flagged:", data.get("hallucination_count"))
            render_pack(data.get("final_pack", data))
        except Exception as e:
            st.error(f"Could not parse JSON ({e}). Raw output below.")
            st.code(res["text"])
    st.download_button("Download raw output", res["text"], file_name=f"study_pack_{version}.txt")