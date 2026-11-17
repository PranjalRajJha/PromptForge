"""Prompt versions v0-v3 for the Lecture Notes -> Study Pack generator."""
import json
import re
from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompts"
VERSIONS = ["v0", "v1", "v2", "v3"]
FILES = {
    "v0": "v0_baseline.txt",
    "v1": "v1_role_constraints_format.txt",
    "v2": "v2_grounded_structured_fewshot.txt",
    "v3a": "v3a_chain_extract.txt",
    "v3b": "v3b_chain_generate.txt",
    "v3c": "v3c_chain_review.txt",
}


def load(name: str) -> str:
    return (PROMPT_DIR / FILES[name]).read_text(encoding="utf-8")


def fill(template: str, **kw) -> str:
    # str.replace (not format) because prompts contain JSON braces
    for k, v in kw.items():
        template = template.replace("{" + k + "}", v)
    return template


def extract_json(text: str):
    """Parse JSON from a model reply, tolerating ```json fences."""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    return json.loads(t)


def validate_notes(notes: str):
    """Input guard: returns an error message, or None if the input can be processed."""
    if not notes or not notes.strip():
        return "No notes provided. Paste lecture-note text first."
    if len(notes) > 12000:
        return "Notes are too long (limit 12,000 characters). Split them by topic."
    return None


def run_version(version: str, notes: str, llm) -> dict:
    """Returns {'text': final output, 'calls': n, 'trace': {...}}."""
    if version in ("v0", "v1", "v2"):
        out = llm(fill(load(version), NOTES=notes))
        return {"text": out, "calls": 1, "trace": {}}
    # v3 = 3-step chain: extract -> generate -> review/repair
    ext = llm(fill(load("v3a"), NOTES=notes))
    ext_json = json.dumps(extract_json(ext), indent=2)
    pack = llm(fill(load("v3b"), EXTRACTED=ext_json))
    rev = llm(fill(load("v3c"), NOTES=notes, PACK=pack))
    return {"text": rev, "calls": 3,
            "trace": {"extract": ext, "generate": pack, "review": rev}}


# ---------- automatic checks (supplement, not replace, human scoring) ----------
def format_pass(version: str, text: str) -> int:
    if version == "v0":
        return int(all(k in text.lower() for k in ["summary", "key concept", "definition"]))
    if version == "v1":
        heads = ["## 1. Summary", "## 2. Key Concepts", "## 3. Key Definitions",
                 "## 4. Likely Exam Points", "## 5. Practice Questions", "## 6. Answer Key"]
        return int(all(h in text for h in heads))
    try:  # v2 / v3: must parse as JSON with the expected keys
        data = extract_json(text)
        pack = data.get("final_pack", data)
        need = {"summary", "key_concepts", "definitions", "mcqs", "short_questions"}
        return int(need.issubset(pack.keys()))
    except Exception:
        return 0


def unsupported_term_ratio(notes: str, text: str) -> float:
    """Crude hallucination signal: share of capitalised/technical words in the
    output that never appear in the notes. Humans still count hallucinations."""
    words = set(re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text))
    base = set(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", notes))
    stop = {"summary", "concepts", "definition", "definitions", "question", "answer",
            "questions", "option", "options", "term", "true", "false", "none",
            "bloom", "remember", "understand", "apply", "source", "supported",
            "verdict", "reason", "review", "item", "final", "pack", "string",
            "mcqs", "short", "exam", "points", "coverage", "note", "following",
            "which", "what", "that", "this", "with", "from", "about", "does",
            "partly", "unsupported", "hallucination", "count", "notes", "information",
            "enough", "evidence", "concept", "facts", "topic", "mentioned", "only"}
    cand = [w for w in words if w.lower() not in stop and len(w) > 4]
    if not cand:
        return 0.0
    miss = [w for w in cand if w.lower() not in base]
    return round(len(miss) / len(cand), 2)
