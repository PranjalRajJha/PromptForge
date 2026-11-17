"""Builds the two Milestone 2 PDFs.

  python build_reports.py

Reads (if present):
  evaluation/scoring_sheet.csv   human scores filled by the team
  outputs/run_log.csv            written by run_experiments.py
Until those are filled, result cells show 'pending'. Nothing is invented.
Edit LINKS below once the prototype / GitHub / reel links exist.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).parent
OUT = ROOT / "docs"

# ---------------- editable facts (must match the submission form) ----------------
LINKS = {
    "Prototype": "PASTE PROTOTYPE LINK HERE",
    "GitHub / Drive folder": "PASTE GITHUB OR DRIVE LINK HERE",
    "Reel (90-150 s)": "PASTE REEL LINK HERE",
}
N_VERSIONS, N_TEMPLATES, N_TESTS, N_NORMAL, N_EDGE = 4, 6, 12, 6, 6
N_OUTPUTS = N_VERSIONS * N_TESTS            # 32
N_CALLS = 3 * N_TESTS + 3 * N_TESTS     # v0,v1,v2 = 1 call each; v3 = 3 calls -> 72
TEAM = [
    ("Pranjal Raj Jha (Leader)", "S24CSEU1964"), ("Arjun Tyagi", "S24CSEU1109"),
    ("Utkarsh Rawat", "S24CSEU1063"), ("Abhijeet Singh", "S24CSEU2593"),
    ("Akshat Chauhan", "S24CSEU1120"), ("Vansh Bhati", "S24CSEU1102"),
]
ROLES = [  # PROPOSED split - the team must edit to reflect real work done
    "Team coordination, prompt v3 chain design, final PDF/submission",
    "Prompt v1/v2 design and few-shot example",
    "Test-set creation (12 inputs: normal, edge, invalid) and expected outputs",
    "Prototype app (Streamlit) and run_experiments.py",
    "Evaluation: rubric, blind scoring, analyze_scores.py",
    "Reel, GitHub repository upkeep, responsible-AI review",
]

NAVY = colors.HexColor("#1f3a5f"); TEAL = colors.HexColor("#1b7f79")
LIGHT = colors.HexColor("#eef2f7"); GREY = colors.HexColor("#5a6472")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, textColor=NAVY, spaceBefore=6, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5, textColor=TEAL, spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13.2, spaceAfter=4)
SM = ParagraphStyle("SM", parent=B, fontSize=8.2, leading=10.4, spaceAfter=0)
CODE = ParagraphStyle("CODE", parent=B, fontName="Courier", fontSize=7.6, leading=9.6,
                      backColor=LIGHT, borderPadding=4, spaceAfter=6)
CAP = ParagraphStyle("CAP", parent=SM, textColor=GREY, alignment=TA_CENTER, spaceAfter=6)
NOTE = ParagraphStyle("NOTE", parent=B, fontSize=8.6, textColor=colors.HexColor("#7a4b00"),
                      backColor=colors.HexColor("#fff6e0"), borderPadding=5, spaceBefore=3, spaceAfter=8)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=21, textColor=NAVY, spaceAfter=4)


def P(t, s=B): return Paragraph(t, s)
def bullets(items): return [P("&bull; " + i) for i in items]


def table(rows, widths, header=True, fs=SM, zebra=True):
    data = [[P(str(c), fs) if not hasattr(c, "wrap") else c for c in r] for r in rows]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cf")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
        for j in range(len(rows[0])):
            data[0][j] = Paragraph("<font color='white'><b>%s</b></font>" % rows[0][j], fs)
        t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0: st.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(st))
    return t


def footer(title):
    def _f(canvas, doc):
        canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(GREY)
        canvas.drawString(1.8 * cm, 1.1 * cm, f"PromptForge | {title} | Bennett University - Prompt Engineering (SCSE4041)")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, f"Page {doc.page}")
        canvas.restoreState()
    return _f


# ---------------- real data (if available) ----------------
def load_scores():
    p = ROOT / "evaluation/scoring_sheet.csv"
    if not p.exists(): return []
    return [r for r in csv.DictReader(open(p, encoding="utf-8")) if r.get("C1", "").strip()]


def load_log():
    p = ROOT / "outputs/run_log.csv"
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else []


def results_table():
    rows = load_scores(); log = load_log()
    crit = ["C1", "C2", "C3", "C4", "C5", "C6"]
    head = ["Version", "Calls/run", "Format pass (auto)"] + crit + ["Total /30", "Avg H", "Edge pass"]
    calls = {"v0": 1, "v1": 1, "v2": 1, "v3": 3}
    out = [head]
    by = defaultdict(list)
    for r in rows: by[r["version"]].append(r)
    fp = defaultdict(list)
    for r in log: fp[r["version"]].append(int(r["format_pass_auto"]))
    for v in ["v0", "v1", "v2", "v3"]:
        rs = by.get(v, [])
        fmt = f"{sum(fp[v])}/{len(fp[v])}" if fp.get(v) else "pending"
        if not rs:
            out.append([v, calls[v], fmt] + ["pending"] * 6 + ["pending"] * 3); continue
        ms = [mean(float(r[c]) for r in rs) for c in crit]
        hs = [float(r["H_count"]) for r in rs if r["H_count"].strip()]
        ed = [r["edge_pass"].strip().upper() for r in rs if r["edge_pass"].strip()]
        out.append([v, calls[v], fmt] + [f"{m:.2f}" for m in ms] +
                   [f"{sum(ms):.2f}", f"{mean(hs):.2f}" if hs else "-",
                    f"{sum(e == 'PASS' for e in ed)}/{len(ed)}" if ed else "-"])
    return out, bool(rows)


def img(name, w=17):
    p = OUT / name
    from PIL import Image as PI
    iw, ih = PI.open(p).size
    return Image(str(p), width=w * cm, height=w * cm * ih / iw)


# =====================================================================
# TECHNICAL REPORT (supporting document)
# =====================================================================
def build_report():
    doc = SimpleDocTemplate(str(OUT / "PromptForge_Technical_Report.pdf"), pagesize=A4,
                            leftMargin=1.9 * cm, rightMargin=1.9 * cm, topMargin=1.6 * cm,
                            bottomMargin=1.8 * cm, title="PromptForge - Technical Report",
                            author="Team PromptForge")
    s = [P("Technical Report", TITLE),
         P("<b>Reducing Unsupported Content in AI-Generated Study Packs through Prompt Design: "
           "A Four-Version Prompt Workflow</b>", B),
         P("Team PromptForge | Bennett University, Prompt Engineering (SCSE4041) | Milestone 2 supporting document", SM),
         Spacer(1, 8)]
    s.append(P("Abstract", H1))
    s.append(P("Students revise from long lecture notes, and general-purpose chat assistants can turn notes into summaries and practice "
               "questions. A practical risk is that the generated material includes statements the notes never made, which is harmful when the "
               "output is used for exam preparation. This project designs and compares four prompt versions for converting lecture-note text into "
               "a study pack: a baseline prompt (v0), a role-and-format constrained prompt (v1), a grounded structured prompt with a refusal path, "
               "source quotes and a few-shot example (v2), and a three-step prompt chain that extracts, generates and reviews (v3). The versions are "
               "compared on twelve test inputs, including three edge and three invalid cases, with a rubric fixed before testing and blind scoring by two team members. "
               "This report describes the design, the evaluation protocol and the limitations; measured results are reported in the Milestone 2 "
               "document and final report once the experiments are scored."))
    s.append(P("1. Problem and Motivation", H1))
    s.append(P("Manual conversion of lecture material into revision notes and self-test questions is time-consuming. Existing tools "
               "such as ChatGPT, Gemini and NotebookLM can summarise material (as noted in Milestone 1), but a student must still write and "
               "refine a prompt to obtain a consistent, exam-oriented format, and has no built-in way to check whether each statement is "
               "supported by the notes. The opportunity addressed here is a <i>repeatable prompt workflow</i> that produces a fixed-format pack "
               "and exposes its evidence."))
    s.append(P("2. Method", H1))
    s.append(P("<b>Task decomposition.</b> The task is split into extraction, generation and review. Prompt chaining, in which the output of "
               "one prompt becomes the input of the next, is a recognised technique for controllable multi-step language-model workflows "
               "(Wu et al., 2022). <b>Examples and reasoning.</b> v2 uses a few-shot example to fix format and style (Brown et al., 2020). "
               "<b>Question design.</b> Questions are tagged with Bloom's taxonomy levels (Bloom, 1956) so that the pack mixes recall and application. "
               "<b>Grounding.</b> Each question must carry a short quote from the notes; items the notes do not support must be omitted and "
               "reported in a coverage note. <b>Structured output.</b> v2 and v3 return JSON so that format validity can be checked automatically."))
    s.append(img("fig1_prompt_chain.png", 16.5))
    s.append(P("Figure 1. v3 prompt-chain architecture.", CAP))
    s.append(P("3. Evaluation Protocol", H1))
    s += bullets([f"<b>Test set:</b> {N_TESTS} inputs ({N_NORMAL} normal from OS, DBMS, networks, NLP, theory of computation and prompt engineering; "
                  f"{N_EDGE} edge/invalid: a two-line note, a slide that only names a topic, a Hinglish note, a chat message, garbled text and a note with an injected instruction).",
                  f"<b>Runs:</b> {N_VERSIONS} versions x {N_TESTS} inputs = {N_OUTPUTS} outputs; {N_CALLS} model calls (v3 uses three calls per input); "
                  "one model, temperature 0.2, identical settings for all versions.",
                  "<b>Rubric:</b> six criteria scored 1-5 (coverage, faithfulness, question quality, answer correctness, format compliance, exam usefulness), "
                  "plus hallucination count, automatic format pass and edge-case pass.",
                  "<b>Blinding:</b> output files are shuffled and unlabeled for scorers; two independent scores are averaged.",
                  "<b>Reporting:</b> all scores, including failures, are retained in the repository; no outputs are excluded."])
    tab, have = results_table()
    s.append(P("Results", H2))
    s.append(table(tab, [1.3, 1.2, 1.7, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.5, 1.2, 1.4], fs=ParagraphStyle("t", parent=SM, fontSize=7.4)))
    if not have:
        s.append(P("Results pending: scoring of the %d outputs has not been completed" % N_OUTPUTS + ". This table is generated from the team's scoring sheet "
                   "and contains no estimated values.", NOTE))
    s.append(P("4. Limitations and Responsible Use", H1))
    s += bullets(["Twelve test inputs is a small sample; results indicate trends for this task, not general performance.",
                  "Scorers are team members, not independent experts; blind shuffling reduces but does not remove bias.",
                  "Results depend on the chosen model and may change with model updates; model and date are logged.",
                  "A reviewer prompt is itself a language model and can miss errors; human verification remains necessary.",
                  "Only public or non-confidential lecture content is used; no personal data is processed."])
    s.append(P("5. Conclusion and Next Steps", H1))
    s.append(P("The workflow, prototype and evaluation harness are complete and reproducible. Next steps: run and score the experiments, "
               "analyse failure cases, refine the prompts accordingly, collect feedback from a faculty member or senior student on question "
               "quality (planned in Milestone 1), and prepare the final report and viva."))
    s.append(P("References", H1))
    s += [P(r, SM) for r in [
        "[1] Bloom, B. S. (Ed.) (1956). <i>Taxonomy of Educational Objectives, Handbook I: Cognitive Domain</i>. David McKay.",
        "[2] Brown, T. B. et al. (2020). Language Models are Few-Shot Learners. <i>NeurIPS 33</i>.",
        "[3] Wei, J. et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. <i>NeurIPS 35</i>.",
        "[4] Wu, T., Terry, M., Cai, C. J. (2022). AI Chains: Transparent and Controllable Human-AI Interaction by Chaining Large Language Model Prompts. <i>CHI 2022</i>.",
        "[5] Source cited in Milestone 1 on AI-generated educational summaries: https://aclanthology.org/2023.bea-1.31/",
        "[6] NotebookLM (Google), cited in Milestone 1 as an existing tool: https://notebooklm.google.com/",
    ]]
    s.append(PageBreak())
    s.append(P("Appendix A: Prompt Texts", H1))
    for name, fn in [("v0 (baseline)", "v0_baseline.txt"), ("v1", "v1_role_constraints_format.txt"),
                     ("v2", "v2_grounded_structured_fewshot.txt"), ("v3a extract", "v3a_chain_extract.txt"),
                     ("v3b generate", "v3b_chain_generate.txt"), ("v3c review", "v3c_chain_review.txt")]:
        txt = (ROOT / "prompts" / fn).read_text(encoding="utf-8")
        txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>").replace(" ", "&nbsp;")
        s.append(KeepTogether([P(name, H2), P(txt, CODE)]))
    doc.build(s, onFirstPage=footer("Technical Report"), onLaterPages=footer("Technical Report"))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    import build_m2; build_m2.build(); build_report()
    print("built", OUT / "PromptForge_Milestone2.pdf", OUT / "PromptForge_Technical_Report.pdf")
