# Monday 2 PM Delivery Plan (Code -> Report)

## Objective
Submit a CAQM-ready package containing:
- Evidence-backed analysis outputs from CPCB CAAQMS data
- Draft narrative report with problem-wise recommendations
- Traceable code and reproducible run steps

## Roles
- Coordinator: Vinayak
- Analysis/code owner: Data analysis lead
- Report owner: Technical writing lead
- QA reviewer: Committee internal reviewer

## Work Breakdown and Timeline

### Block 1: Data and metrics freeze (T-6h to T-4h)
1. Re-run analysis script on final data snapshot.
2. Verify file count and row count consistency.
3. Freeze outputs folder and timestamp it.

Acceptance check:
- outputs/issue_summary.csv and outputs/issue_by_site_year.csv regenerated successfully.

### Block 2: Report finalization (T-4h to T-2h)
1. Insert finalized numbers into report sections.
2. Add committee language and institutional context.
3. Add annex references to flagged example files.

Acceptance check:
- No unresolved placeholders in report text.
- All six committee problem statements addressed with QA/QC actions.

### Block 3: Internal review and correction (T-2h to T-1h)
1. Quick technical review of methods and thresholds.
2. Correct wording, definitions, and caveats.
3. Confirm consistency between code outputs and report tables.

Acceptance check:
- All metrics in report match output CSV files.
- Review comments resolved.

### Block 4: Submission package assembly (T-1h to T-0h)
1. Bundle report, summary tables, and script.
2. Add a one-page cover note with key findings and recommendations.
3. Deliver by Monday 2:00 PM.

Acceptance check:
- Package contains report, script, and outputs.
- Final handoff acknowledged by coordinator.

## Submission Checklist
- report/CAQM_CPCB_Data_Issues_Report_Draft.md (or final version)
- scripts/analyze_caaqms_issues.py
- outputs/issue_summary.csv
- outputs/issue_by_site_year.csv
- outputs/run_summary.txt
- Selected annex tables for each issue

## Risk Controls
1. Risk: Last-minute metric changes.
- Control: Freeze data snapshot before report lock.

2. Risk: Inconsistent numbers across tables.
- Control: One person performs final numeric cross-check against output CSV.

3. Risk: Scope drift before deadline.
- Control: Keep Monday submission to six mandatory issues only; defer extra analyses to addendum.
