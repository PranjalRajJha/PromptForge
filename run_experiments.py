"""Run all prompt versions on all test notes and write outputs + scoring sheet.

Usage:
  export GEMINI_API_KEY=...        # or OPENAI_API_KEY
  python run_experiments.py                 # all versions, all tests
  python run_experiments.py --versions v0 v3 --tests T1 T7
  python run_experiments.py --out outputs   # output folder (default: outputs)

Outputs:
  outputs/<version>_<test>.txt   raw model output (v3 also saves each stage)
  outputs/run_log.csv            model, provider, timestamp, calls, auto-checks
  evaluation/test_table.csv      final-prototype (v3) test table: input, expected, actual; fill pass_fail
  evaluation/scoring_sheet.csv   blank sheet for human scoring (C1-C6, H, edge)
"""
import argparse
import csv
import datetime as dt
import json
import random
import time
from pathlib import Path

from llm import call_llm, provider_info
from pipeline import VERSIONS, extract_json, format_pass, run_version, unsupported_term_ratio

ROOT = Path(__file__).parent


def compact_actual(text: str) -> str:
    """Short, faithful excerpt of the real output for the test table (full text stays in outputs/)."""
    try:
        d = extract_json(text); p = d.get("final_pack", d)
        return (f"summary: {p.get('summary','')[:160]} | MCQs: {len(p.get('mcqs', []))} | "
                f"short Qs: {len(p.get('short_questions', []))} | coverage_note: {p.get('coverage_note','')[:120]}")
    except Exception:
        return "UNPARSEABLE: " + text[:200].replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versions", nargs="*", default=VERSIONS)
    ap.add_argument("--tests", nargs="*")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--sleep", type=float, default=4.0, help="pause between model calls (seconds)")
    args = ap.parse_args()

    tests = json.loads((ROOT / "test_data/test_notes.json").read_text(encoding="utf-8"))
    if args.tests:
        tests = [t for t in tests if t["id"] in args.tests]
    out = ROOT / args.out
    out.mkdir(exist_ok=True)
    provider, model = provider_info()

    log_rows, sheet_rows, table_rows = [], [], []
    complete, tag = True, f"{provider}:{model}"
    for t in tests:
        if not complete:
            break
        for v in args.versions:
            f, meta = out / f"{v}_{t['id']}.txt", out / f"{v}_{t['id']}.meta"
            if f.exists() and meta.exists() and meta.read_text().strip() == tag:
                res = {"text": f.read_text(encoding="utf-8"), "calls": 3 if v == "v3" else 1, "trace": {}}
                print("cached", v, t["id"])      # resume: same model already produced this output
            else:
                try:
                    res = run_version(v, t["notes"], call_llm)
                except RuntimeError as e:
                    print("\nSTOPPED:", e); complete = False; break
                f.write_text(res["text"], encoding="utf-8")
                for stage, txt in res["trace"].items():
                    (out / f"{v}_{t['id']}_{stage}.txt").write_text(txt, encoding="utf-8")
                meta.write_text(tag)
                print("done", v, t["id"]); time.sleep(args.sleep)
            log_rows.append({
                "version": v, "test": t["id"], "type": t["type"], "provider": provider,
                "model": model, "time": dt.datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"),
                "llm_calls": res["calls"], "format_pass_auto": format_pass(v, res["text"]),
                "unsupported_term_ratio": unsupported_term_ratio(t["notes"], res["text"])})
            if v == "v3":  # final prototype -> test table (Pass/Fail is marked by a human)
                table_rows.append({"test_id": t["id"], "type": t["type"], "input": t["notes"],
                                   "expected_output": t["expected"],
                                   "actual_output": compact_actual(res["text"]), "pass_fail": ""})
            sheet_rows.append({"blind_id": f"S{random.randint(1000, 9999)}", "version": v, "test": t["id"],
                               "scorer": "", "C1": "", "C2": "", "C3": "", "C4": "",
                               "C5": "", "C6": "", "H_count": "", "edge_pass": ""})

    if not complete:
        print("Run incomplete: outputs so far are saved. Rerun the same command later (same MODEL) to resume.")
        return
    with open(out / "run_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(log_rows[0].keys()))
        w.writeheader(); w.writerows(log_rows)
    if table_rows:
        with open(ROOT / "evaluation/test_table.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(table_rows[0].keys()))
            w.writeheader(); w.writerows(table_rows)
    random.shuffle(sheet_rows)  # blind scoring order
    with open(ROOT / "evaluation/scoring_sheet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sheet_rows[0].keys()))
        w.writeheader(); w.writerows(sheet_rows)


if __name__ == "__main__":
    main()