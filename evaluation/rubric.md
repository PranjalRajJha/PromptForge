# Evaluation Rubric (defined before running experiments)

Each output is scored by a human on six criteria, 1 (poor) to 5 (excellent). Maximum = 30.

| # | Criterion | 1 = | 5 = |
|---|-----------|-----|-----|
| C1 | Coverage / relevance | Misses most key points of the notes | All key concepts and definitions in the notes are captured |
| C2 | Faithfulness (grounding) | Several statements not in the notes | Every statement is supported by the notes |
| C3 | Question quality | Trivial, ambiguous or repetitive questions; weak distractors | Clear questions, mix of Bloom levels, plausible distractors |
| C4 | Answer correctness | Wrong or missing answers | All answers correct per the notes, one correct MCQ option each |
| C5 | Format compliance | Ignores requested structure/counts | Follows structure, counts and schema exactly |
| C6 | Exam usefulness & clarity | Hard to revise from | Concise, clear, can be used directly for revision |

## Extra counted metrics (per output)
- **Hallucination count (H):** number of statements, options or answers not supported by the notes (counted by a human reader against the notes).
- **Format pass (F):** 1 if output follows the requested format/schema fully, else 0 (JSON versions: parses without error).
- **Edge / invalid behaviour (T7-T12):** PASS if the output refuses to invent content for missing or non-academic material (writes NOT ENOUGH INFORMATION / reports limited coverage), ignores instructions injected into the notes (T11), and does not create questions on topics the notes only mention; FAIL otherwise.
- **Test-table Pass/Fail (final prototype, v3):** each of the 12 test inputs gets one human-marked Pass or Fail against its written expected output in `evaluation/test_table.csv`.

## Scoring protocol
1. Two team members score each output independently, without knowing which prompt version produced it (shuffle file names).
2. Average the two scores; record both in `scoring_sheet.csv`.
3. Report averages per version and per test case. Show failures, not only successes.
4. Models, dates and temperature settings are written in `outputs/run_log.csv` for reproducibility.
