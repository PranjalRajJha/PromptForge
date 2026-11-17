"""Milestone 2 PDF, 7 sections (matches the six marked M2 components + contribution table = Section 7)."""
import csv
import json
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.pagesizes import A4

import build_reports as R
from build_reports import (B, CAP, CODE, H1, H2, NOTE, OUT, ROOT, SM, TITLE, P, bullets,
                           footer, img, results_table, table, LINKS, TEAM, ROLES)

N_TESTS, N_VERSIONS, N_PROMPTS_FINAL = 12, 4, 3
TINY = ParagraphStyle("tiny", parent=SM, fontSize=7.2, leading=8.8)


def short(t, n):
    t = " ".join(t.split())
    return t if len(t) <= n else t[: n - 1] + "..."


def test_rows():
    p = ROOT / "evaluation/test_table.csv"
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert len(rows) == N_TESTS, "test table must have exactly %d rows" % N_TESTS
    return rows


def build():
    rows = test_rows()
    scored = sum(1 for r in rows if r["pass_fail"].strip())
    doc = SimpleDocTemplate(str(OUT / "PromptForge_Milestone2.pdf"), pagesize=A4, leftMargin=1.8 * cm,
                            rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.8 * cm,
                            title="PromptForge - Milestone 2", author="Team PromptForge")
    s = [P("Milestone 2 Submission", TITLE),
         P("<b>AI-Powered Lecture Notes to Study Pack Generator</b> | Prompt Design, Implementation, Demonstration", B),
         P("Team <b>PromptForge</b> | Team ID: <b>[enter Team ID from Milestone 1 result]</b> | Problem C2 | "
           "Prompt Engineering (SCSE4041) | Deadline 22 November 2026", SM), Spacer(1, 5)]
    s.append(P("Figures used in the submission form (they match this PDF)", H2))
    s.append(table([["Form item", "Value", "Where in this PDF"],
                    ["Prompts in the final solution", N_PROMPTS_FINAL, "Sec. 1: v3a extract, v3b generate, v3c review"],
                    ["Prompt versions in iteration log", N_VERSIONS, "Sec. 4: v0, v1, v2, v3"],
                    ["Test inputs in test table", N_TESTS, "Sec. 3: T1-T12 (6 normal, 3 edge, 3 invalid)"],
                    ["Reel length (seconds)", "[enter actual length]", "Sec. 6"]], [5.4, 3.6, 8.4]))

    # ---------------- 1 Design
    s.append(P("1. Prompt / Solution Design Description and Diagrams", H1))
    s.append(P("<b>Problem and task.</b> Students revise from long lecture notes; making summaries and practice questions by hand is slow. "
               "Input: lecture-note or slide text (public, non-confidential). Output: summary, key concepts, definitions, exam points, "
               "MCQs and short-answer questions with answers. The key quality requirement is <i>faithfulness</i>: nothing in the pack may go beyond the notes."))
    s.append(P("<b>Task decomposition.</b> The single request \"make a study pack\" is split into three jobs, each with its own prompt: "
               "(1) extract what the notes state, with evidence quotes; (2) generate study material only from that extraction; "
               "(3) review the pack against the original notes and repair it."))
    s.append(img("fig1_prompt_chain.png", 16.6))
    s.append(P("Figure 1. Input-output flow of the final v3 prompt chain (three prompts).", CAP))
    s.append(P("Prompt techniques used", H2))
    s += bullets(["<b>Role and audience</b> (B.Tech student, exam orientation) in every prompt.",
                  "<b>Constraints</b>: use only the notes; allowed to produce fewer items; items the notes merely mention get no questions.",
                  "<b>Structured output</b>: JSON schema with source quote and Bloom level per question.",
                  "<b>Few-shot example</b> (v2) to fix format; <b>prompt chaining</b> and <b>reviewer prompt</b> (v3) to separate generation from checking.",
                  "<b>Safety</b>: instructions embedded in the notes are treated as data, not commands (tested in T11)."])
    s.append(img("fig2_eval_workflow.png", 16.6))
    s.append(P("Figure 2. Experiment and evaluation workflow.", CAP))

    # ---------------- 2 Implementation
    s.append(PageBreak())
    s.append(P("2. Running / Partial Build / Implementation", H1))
    s.append(P("The prototype is a Python application whose logic is intentionally thin: the prompts are the main work. "
               "Modules and their status at the time of writing:"))
    s.append(table([["#", "Module", "File", "What it does", "Status"],
                    ["1", "Prompt library", "prompts/*.txt", "Six versioned prompt templates", "Complete"],
                    ["2", "Input guard", "pipeline.py: validate_notes", "Rejects empty or over-long input before any model call", "Complete"],
                    ["3", "Prompt-chain engine", "pipeline.py: run_version", "Runs v0-v3; chains extract, generate, review; parses JSON", "Complete"],
                    ["4", "Model adapter", "llm.py", "Calls Gemini or OpenAI API (temperature 0.2)", "Complete; needs API key"],
                    ["5", "Web app", "app.py (Streamlit)", "Paste notes, pick version, view rendered pack and reviewer report", "[confirm after running]"],
                    ["6", "Experiment runner", "run_experiments.py", "Runs all versions on all tests; writes outputs, run log, test table", "[confirm after running]"],
                    ["7", "Score analysis", "analyze_scores.py", "Averages human scores per version", "Complete"]],
                   [0.6, 3.0, 3.8, 6.6, 3.4], fs=TINY))
    s.append(P("Status note: modules 1-4 and 7 were checked with a stub model (wiring, JSON parsing, placeholder substitution). "
               "Modules 5 and 6 need a live model key; the team marks them working after a real run and updates this table and form Q19-Q20.", NOTE))
    s.append(P("How to run", H2))
    s.append(P("pip install streamlit<br/>export GEMINI_API_KEY=...   (or OPENAI_API_KEY; optional MODEL=...)<br/>streamlit run app.py<br/>"
               "python run_experiments.py<br/>python analyze_scores.py evaluation/scoring_sheet.csv<br/>python build_reports.py", CODE))
    s.append(P("<b>Model/tool:</b> [enter model, e.g. Gemini 2.5 Flash via API]. Same model, temperature 0.2 and no hidden system prompt for all versions; "
               "model name and timestamp are logged per run in outputs/run_log.csv. Only public or non-confidential content is processed.", B))

    # ---------------- 3 Demo / pilot
    s.append(P("3. Demonstration / Pilot Run of Available Modules", H1))
    s.append(P(f"The final prototype (v3) is tested on {N_TESTS} inputs: 6 normal, 3 edge (T7 very short, T8 topic only mentioned, "
               "T12 Hinglish) and 3 invalid (T9 chat message, T10 garbled text, T11 prompt injection). Expected outputs were written "
               "<b>before</b> running. Actual output is a short excerpt of the real model reply (full text in outputs/ in the repository); "
               "Pass/Fail is marked by a team member against the expected output."))
    trows = [["ID", "Type", "Test input (excerpt)", "Expected output", "Actual output (excerpt)", "P/F"]]
    for r in rows:
        trows.append([r["test_id"], r["type"].replace("_", " "), short(r["input"], 90), short(r["expected_output"], 150),
                      short(r["actual_output"], 190) if r["actual_output"].strip() else "pending (run required)",
                      r["pass_fail"].strip() or "pending"])
    s.append(table(trows, [0.9, 1.5, 3.7, 4.7, 4.9, 1.2], fs=TINY))
    if scored < N_TESTS:
        s.append(P(f"Status: {scored} of {N_TESTS} rows have a recorded Pass/Fail. Rows marked pending have not been run or marked yet; "
                   "nothing in this table is estimated.", NOTE))
    s.append(P("Evaluation rubric (fixed before testing)", H2))
    s.append(P("Six criteria scored 1-5 by two members on shuffled, unlabeled outputs: coverage, faithfulness, question quality, answer correctness, "
               "format compliance, exam usefulness (max 30); plus hallucination count, automatic format pass and edge/invalid pass. "
               "Full rubric: evaluation/rubric.md.", B))
    tab, have = results_table()
    s.append(P("Prompt-version comparison (all 4 versions on the same 12 inputs)", H2))
    s.append(table(tab, [1.3, 1.2, 1.7, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.5, 1.2, 1.4], fs=TINY))
    if not have:
        s.append(P("Comparison pending: scoring has not been done, so cells read 'pending'. They are filled automatically from "
                   "evaluation/scoring_sheet.csv when build_reports.py is re-run.", NOTE))
    s.append(P("Failure analysis (to be completed from real runs)", H2))
    s.append(table([["Anticipated failure", "Likely in", "Detected by", "Mitigation"],
                    ["Facts not in the notes", "v0, v1", "H count", "v2 grounding; v3 reviewer"],
                    ["Invented questions for short notes (T7)", "v0-v2", "T7 Pass/Fail", "Refusal path; fewer-items rule"],
                    ["Questions on mentioned-only topic (T8)", "v1, v2", "T8 Pass/Fail", "v3a mentioned_only list"],
                    ["Follows injected instruction (T11)", "v0, v1", "T11 Pass/Fail", "Notes treated as data"],
                    ["Invalid JSON", "v2, v3", "Format pass", "Schema in prompt; tolerant parser"]],
                   [6.0, 2.0, 3.4, 5.8], fs=TINY))
    s.append(P("Responsible AI: no personal or confidential data; hallucination reduced but not removed, so a human verifies before exam use; "
               "users paste only notes they may use; source quotes and the reviewer report support human oversight.", B))

    # ---------------- 4 Repo + iteration log
    s.append(PageBreak())
    s.append(P("4. Updated Git Repository / Source Files and Iteration Log", H1))
    s.append(P("promptforge-study-pack/<br/>&nbsp;&nbsp;prompts/ (v0, v1, v2, v3a, v3b, v3c)<br/>&nbsp;&nbsp;test_data/test_notes.json (12 inputs with expected behaviour)<br/>"
               "&nbsp;&nbsp;evaluation/ (rubric.md, test_table.csv, scoring_sheet.csv)<br/>&nbsp;&nbsp;outputs/ (raw outputs, run_log.csv)<br/>"
               "&nbsp;&nbsp;docs/ (figures, PDFs, reel_script.md)<br/>&nbsp;&nbsp;pipeline.py, llm.py, app.py, run_experiments.py, analyze_scores.py, build_reports.py, build_m2.py, README.md", CODE))
    s.append(P(f"Prompt iteration log ({N_VERSIONS} versions)", H2))
    s.append(table([["Ver.", "What changed (on purpose)", "Why (design reason)", "Evidence from runs"],
                    ["v0", "Milestone 1 baseline prompt, unchanged", "Reference point", "[add observed weakness]"],
                    ["v1", "Added role, six fixed headings, 5 MCQ + 3 short Q, word limit, no-outside-knowledge rule", "Consistent, exam-oriented format", "[add observation]"],
                    ["v2", "Added grounding rules, refusal path, source quote, Bloom level, JSON schema, one few-shot example", "Reduce unsupported content; make output checkable", "[add observation]"],
                    ["v3", "Split into extract / generate / review prompts; mentioned-only topics barred; reviewer repairs pack", "Locate and fix errors by stage", "[add observation]"]],
                   [1.0, 6.2, 5.0, 5.2], fs=TINY))
    s.append(P("The 'Evidence from runs' column is completed by the team after running the experiments: record what actually went wrong in each version, "
               "which is the reason for the next version. Do not fill it with expected behaviour.", NOTE))

    # ---------------- 5 Supporting doc
    s.append(P("5. Supporting Document", H1))
    s.append(P("Document type: <b>Technical Report</b> (separate file <b>PromptForge_Technical_Report.pdf</b>): architecture, tools and model, prompt design, "
               "evaluation protocol, test results, limitations, references and full prompt texts."))

    # ---------------- 6 Video
    s.append(P("6. Video / Reel (90-150 seconds)", H1))
    s.append(table([["Item", "Link (opens for anyone with the link)"]] + [[k, v] for k, v in LINKS.items()], [5, 12.4]))
    s.append(P("Reel content: problem (10 s), baseline weakness (20 s), v3 chain walk-through (35 s), live app demo (35 s), edge/invalid cases (20 s), "
               "results and next steps (15 s). Script: docs/reel_script.md.", B))

    # ---------------- 7 Contribution
    s.append(P("7. Team Contribution Table", H1))
    s.append(P("Proposed allocation, <b>to be edited by the team so it states what each member actually did</b> (the form asks all members to confirm it).", SM))
    s.append(table([["Enrollment no.", "Name", "Main task"]] + [[TEAM[i][1], TEAM[i][0].replace(" (Leader)", ""), ROLES[i]] for i in range(6)], [3.0, 3.8, 10.6]))
    doc.build(s, onFirstPage=footer("Milestone 2"), onLaterPages=footer("Milestone 2"))


if __name__ == "__main__":
    build()
