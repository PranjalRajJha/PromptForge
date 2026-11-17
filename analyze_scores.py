"""Average human scores per prompt version after the team fills scoring_sheet.csv.

Usage: python analyze_scores.py evaluation/scoring_sheet.csv
Prints a per-version table (mean C1-C6, total /30, mean hallucinations,
edge-case pass rate) so the numbers in the report come straight from the sheet.
"""
import csv
import sys
from collections import defaultdict
from statistics import mean

path = sys.argv[1] if len(sys.argv) > 1 else "evaluation/scoring_sheet.csv"
rows = [r for r in csv.DictReader(open(path, encoding="utf-8")) if r["C1"].strip()]
by = defaultdict(list)
for r in rows:
    by[r["version"]].append(r)

crit = ["C1", "C2", "C3", "C4", "C5", "C6"]
print("version | n | " + " | ".join(crit) + " | total/30 | H mean | edge pass")
for v in sorted(by):
    rs = by[v]
    means = [mean(float(r[c]) for r in rs) for c in crit]
    h = mean(float(r["H_count"]) for r in rs if r["H_count"].strip()) if any(r["H_count"].strip() for r in rs) else float("nan")
    ed = [r["edge_pass"].strip().upper() for r in rs if r["edge_pass"].strip()]
    edge = f"{sum(e == 'PASS' for e in ed)}/{len(ed)}" if ed else "-"
    print(f"{v} | {len(rs)} | " + " | ".join(f"{m:.2f}" for m in means) +
          f" | {sum(means):.2f} | {h:.2f} | {edge}")
