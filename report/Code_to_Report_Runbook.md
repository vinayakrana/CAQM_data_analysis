# Code to Report Runbook

## 1) Environment
Python environment used: workspace .venv
Required packages: pandas, numpy

## 2) Run analysis
From workspace root:

PowerShell command:
.\.venv\Scripts\python.exe scripts\analyze_caaqms_issues.py

## 3) Generated outputs
- outputs/issue_summary.csv
- outputs/issue_by_site_year.csv
- outputs/flatline_examples.csv
- outputs/spike_examples.csv
- outputs/unit_inconsistency_examples.csv
- outputs/pm25_gt_pm10_examples.csv
- outputs/missing_data_gap_examples.csv
- outputs/humidity_bias_screening.csv
- outputs/run_summary.txt

## 4) Build report
1. Open report/CAQM_CPCB_Data_Issues_Report_Draft.md
2. Validate all summary numbers against outputs/issue_summary.csv
3. Add committee-specific context and final sign-off text

## 5) Quality checks before submission
1. Confirm files processed count in outputs/run_summary.txt is 440
2. Confirm report issue table matches outputs/issue_summary.csv
3. Confirm all six problem statements have Level 1 to Level 3 recommendations
