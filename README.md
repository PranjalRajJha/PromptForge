# PromptForge - Lecture Notes to Study Pack (Prompt Engineering mini-project, C2)

Working Demo Link(deployed): https://promptforgebypranjal.streamlit.app/

Prompt workflow (v0-v3), test set (12 inputs), rubric, Streamlit prototype and experiment harness.

## Run
```
pip install streamlit
export GEMINI_API_KEY=...     # or OPENAI_API_KEY ; optional MODEL=...
streamlit run app.py          # prototype
python run_experiments.py     # all versions x all tests -> outputs/, evaluation/test_table.csv, scoring_sheet.csv
python analyze_scores.py evaluation/scoring_sheet.csv
python build_reports.py       # regenerates docs/*.pdf with real numbers
```
## Folders
prompts/ (v0, v1, v2, v3a, v3b, v3c) | test_data/ | evaluation/ | outputs/ | docs/



## Data
Only public / non-confidential lecture content. No personal data.
