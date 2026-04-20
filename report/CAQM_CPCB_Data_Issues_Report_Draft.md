# ASSESSMENT OF DATA QUALITY ISSUES IN CPCB CAAQMS NETWORKS
## With Evidence-Based QA/QC Recommendations

**Commission for Air Quality Management (CAQM)**  
**NCR and Adjoining Areas**

**Date:** 20 April 2026  
**Status:** FINAL

---

## 1 DATASET SCOPE

| Metric | Value |
|---|---|
| Data folder | Raw_data_1Hr_CAAQMS |
| Files analyzed | 440 |
| Total hourly records | 3,754,704 |
| Time span | 2009–2025 |
| Sites covered | Multi-agency (CPCB, DPCC, IMD, IITM, MHUA) |
| Coverage | Delhi NCR hourly monitoring network |

## 2 EXECUTIVE SUMMARY

This automated assessment identifies and quantifies six recurring data quality issues reported by the CAQM Technical Committee in CPCB CAAQMS networks. Analysis confirms all issue classes are present, with varying operational severity.

### Key Findings

**High prevalence issues requiring immediate QA/QC adoption:**
- Continuous flat-line values: 14.18% of monitored pollutant points across network
- Sudden spikes/drops: 3.28% of monitored points (453K spike events)
- Humidity-linked PM inflation: 54% of screened site-years show PM2.5 bias at high RH

**Moderate prevalence requiring diagnostic protocols:**
- NO/NO2/NOx unit inconsistencies: 4.65% of chemically-checkable points
- PM2.5 > PM10 logical errors: 0.47% of paired PM availability

**Non-issue in supplied data:**
- Transmission continuity: 100% of timestamps valid, no gaps or duplicates detected

### Recommended Action

Deploy the attached 3-tier automated + diagnostic + expert QA/QC workflow. Tier 1 automated flags should reach QA analysts within 24 hours of collection. Tier 2/3 review cycles require staffing allocation.

## 3 METHODOLOGY

Automated screening was applied across all 440 files using a unified Python analysis pipeline. All checks operate at the hourly record level and are stateless (no external reference data required). Screening results are indexed by file and site-year for rapid drill-down and prioritization.

### Check Procedures by Issue

| Issue | Procedure | Threshold | Output |
|---|---|---|---|
| **Flat-line** | Detect consecutive non-null values with step ≤ tolerance | 6+ hrs, ±0.5 unit tolerance | Point count + event count |
| **Spike/drop** | Robust outlier on first differences (MAD-based z-score) | z > 8 on normalized differences | Point count + event count |
| **Unit consistency** | Stoichiometric check NO + NO2 ≈ NOx after conversion | Ratio [0.6–1.4] and absolute |diff| > 20 ppb | Point count + checked denominator |
| **PM logic** | Hard rule PM2.5 ≤ PM10 | Any PM2.5 > PM10 with both non-null | Point count + checked denominator |
| **Transmission** | Parse timestamp, check duplicates and gaps | Hourly cadence expected | Gap count + missing hour slots |
| **Humidity bias** | Site-year level PM2.5 median ratio (RH > 85% vs RH < 60%) | Ratio ≥ 1.5, n ≥ 100 per group | Flagged site-years |

## 4 QUANTITATIVE RESULTS

### 4.1 Summary by Issue

| Issue | Affected Records | Events | Checked Total | % Affected |
|---|---:|---:|---:|---:|
| Continuous flat-line values | 3,346,863 | 195,635 | 23,605,750 | 14.18% |
| Sudden spikes or drops | 765,489 | 453,635 | 23,363,482 | 3.28% |
| NO/NO2/NOx unit inconsistency | 129,514 | — | 2,785,052 | 4.65% |
| PM2.5 > PM10 logical error | 11,474 | — | 2,433,714 | 0.47% |
| Transmission gaps/duplicates | 0 | 0 | 3,754,704 | 0.00% |
| RH-linked PM inflation** | 148 site-yrs | — | 276 site-yrs screened | 53.62% |

*Events = distinct contiguous anomaly clusters*  
** Flags indicate potential instrument drift or sampling artifact under high humidity; not a network failure.

### 4.2 High-Impact File Examples

**Flat-line dominant (most affected):**
- Raw_data_1Hr_2025_site_119_Sirifort_Delhi_CPCB_1Hr.csv (29.8K points, 1,776 events)
- Raw_data_1Hr_2024_site_119_Sirifort_Delhi_CPCB_1Hr.csv (21.6K points)

**Spike/drop dominant:**
- Raw_data_1Hr_2018_site_105_North_Campus_DU_Delhi_IMD_1Hr.csv (4.8K points, 1,913 events)
- Raw_data_1Hr_2021_site_105_North_Campus_DU_Delhi_IMD_1Hr.csv (4.8K points)

**Unit inconsistency dominant:**
- Raw_data_1Hr_2016_site_125_Punjabi_Bagh_Delhi_DPCC_1Hr.csv (5.1K points / 6.95K checked)
- Raw_data_1Hr_2016_site_301_Anand_Vihar_Delhi_DPCC_1Hr.csv (4.7K points / 6.18K checked)

**PM2.5 > PM10 dominant:**
- Raw_data_1Hr_2024_site_5395_Lodhi_Road_Delhi_IITM_1Hr.csv (579 points)
- Raw_data_1Hr_2021_site_103_CRRI_Mathura_Road_Delhi_IMD_1Hr.csv (450 points)

**Humidity bias suspects (highest ratio):**
- Raw_data_1Hr_2023_site_1429_Nehru_Nagar_Delhi_DPCC_1Hr.csv (ratio 4.56x)
- Raw_data_1Hr_2023_site_1422_Dwarka-Sector_8_Delhi_DPCC__1Hr.csv (ratio 4.49x)

## 5 RECOMMENDED QA/QC WORKFLOWS

The USEPA, EEA, and WHO frameworks recommend a three-tier data validation hierarchy that CAQM may adopt for Delhi NCR CAAQMS:

- **Level 1 (Automated):** Immediate machine screening; no human judgment needed; results logged to QA database.
- **Level 2 (Diagnostic):** QA specialist reviews flagged data against instrument logs, meteorology, neighboring stations, and maintenance records.
- **Level 3 (Expert):** Domain expert (analyst + supervisor or committee) validates anomaly classification, applies corrections per approved protocol, or marks for deletion.

This report provides problem-specific recommendations for each tier, below.

### 5.1 Problem 1: Continuous Identical or Near-Identical Values  
**14.18% of monitored points | 195,635 events**

| Tier | Action | Owner | Reference |
|---|---|---|---|
| L1 Automated | Apply flat-line detector (≤±0.5 unit, ≥6 hrs); auto-flag in database | Data pipeline | USEPA/EEA Tier 1 |
| L2 Diagnostic | QA analyst reviews: analyzer calibration status, zero/span checks, co-located pollutants, meteorology | QA specialist | WHO/DEFRA diagnostics |
| L3 Expert | Domain expert: retain (valid), correct (calibration artifact), or delete (equipment failure); document reason code | Analyst + supervisor | Regulatory standard |

### 5.2 Problem 2: Sudden Spikes or Sharp Drops  
**3.28% of monitored points | 453,635 events**

| Tier | Action | Owner | Reference |
|---|---|---|---|
| L1 Automated | Apply robust first-difference outlier detector (MAD-based z > 8); flag spike clusters | Data pipeline | USEPA Tier 1 |
| L2 Diagnostic | QA analyst: compare with wind shift, rainfall, nearby stations, maintenance logs | QA specialist | EEA spatial consistency |
| L3 Expert | Classify as true pollution event vs. instrument artifact; annotate with event type code | Expert panel | WHO/DEFRA governance |

### 5.3 Problem 3: Unit Inconsistencies (NO/NO2/NOx)  
**4.65% of chemically-checkable points | 129,514 records**

| Tier | Action | Owner | Reference |
|---|---|---|---|
| L1 Automated | Enforce canonical units at ingestion; validate NO + NO₂ ≈ NOx after conversion; flag deviations | ETL pipeline | USEPA metadata control |
| L2 Diagnostic | QA analyst: stoichiometric consistency review; check instrument reporting configuration | QA specialist | EEA consistency check |
| L3 Expert | Confirm instrument firmware and sensor setup; back-correct if justified; document code | Instrument tech + panel | Regulatory traceability |

### 5.4 Problem 4: PM2.5 > PM10 Logical Inconsistency  
**0.47% of paired PM observations | 11,474 records**

| Tier | Action | Owner | Reference |
|---|---|---|---|
| L1 Automated | Apply hard rule: PM₂.₅ ≤ PM₁₀; flag violations; note exception class | Data pipeline | Universal physics |
| L2 Diagnostic | QA analyst: validate data merge, channel mapping, sampler integrity | QA specialist | EEA/DEFRA data integrity |
| L3 Expert | Decision: retain as exception, correct, suppress, or delete; document justification | Expert panel | Regulatory reporting |

### 5.5 Problem 5: Delayed or Missing Data Transmission  
**0% of hourly slots in supplied data**

| Tier | Action | Owner | Reference |
|---|---|---|---|
| L1 Automated | Monitor timestamp continuity, duplicates, and hourly slot completeness in real-time | Platform ops | USEPA completeness standard |
| L2 Diagnostic | Investigate network/telemetry downtime, logger backlog, station outages | IT ops + station ops | Operational QA |
| L3 Expert | Set publication policy for late-arriving vs. real-time vs. imputed data | Data governance committee | Regulatory requirements |

### 5.6 Problem 6: High-RH Impact on PM Readings  
**53.62% of screened site-years flagged | 148 of 276 site-year pairs**

| Tier | Action | Owner | Reference |
|---|---|---|---|
| L1 Automated | Site-year-level RH-PM ratio screening (>1.5x ratio high RH vs. low RH); flag for follow-up | Data pipeline | WHO/EEA advisory |
| L2 Diagnostic | QA analyst: compare with gravimetric references; assess sampler desiccation; seasonal trend analysis | QA specialist + lab | Instrument diagnostics |
| L3 Expert | Adopt approved humidity correction (if available) or stratify flag by RH regime for separate interpretation | Expert + instrument vendor | Regulatory defensibility |

---

##6 DELIVERABLES

**Code & Configuration:**
- `scripts/analyze_caaqms_issues.py` — One-command reproducible analysis (Python 3.10+, pandas, numpy)

**Output Data (CSV):**
- `outputs/issue_summary.csv` — Aggregate findings across all 6 issues
- `outputs/issue_by_site_year.csv` — Issue counts by file
- `outputs/flatline_examples.csv` — Sample flagged flat-line records
- `outputs/spike_examples.csv` — Sample flagged spike records
- `outputs/unit_inconsistency_examples.csv` — Sample flagged NO/NO2/NOx mismatches
- `outputs/pm25_gt_pm10_examples.csv` — Sample flagged PM logic errors
- `outputs/missing_data_gap_examples.csv` — Transmission gap details (none in current data)
- `outputs/humidity_bias_screening.csv` — Site-year humidity-PM bias results
- `outputs/run_summary.txt` — Human-readable processing summary

**Documentation:**
- This report (CAQM_CPCB_Data_Issues_Report_Draft.md)
- Executive summary one-pager (Executive_Summary_One_Pager.md)
- Code-to-report runbook (Code_to_Report_Runbook.md)

---

## 7 LIMITATIONS & CAVEATS

1. **Screening, not adjudication:** All flags are automated and presumptive. Final decisions require human validation per Tier 2/3 above.
2. **Global thresholds:** Settings (e.g., ±0.5 units for flat-line, z > 8 for spikes) are network-wide and not tuned per pollutant, season, or microsite. Fine-tuning recommended.
3. **Completeness assumption:** Analysis assumes that missing values in CSV cells represent genuinely missing measurements, not data transmission errors. Timestamp continuity is independent of pollutant availability.
4. **No spatial cross-checks:** Analysis does not yet correlate anomalies across nearby stations. Such spatial consistency checks (EEA/DEFRA standard) would strengthen spike and flat-line adjudication.
5. **Humidity bias screening is an indicator:** 54% high-RH-PM-ratio site-years should be inspected for instrument calibration issues, desiccant status, and artifact patterns; not all represent true air quality.

---

## 8 NEXT STEPS & RECOMMENDATIONS

**Immediate (Week 1):**
1. Adopt the 3-tier QA/QC framework above; assign staffing.
2. Update station telemetry metadata to record current unit reporting (µg/m³ vs ppb) and confirm with equipment manuals.
3. Trigger Level 2 diagnostics for top 20 high-impact files identified in Section 4.2.

**Short-term (Weeks 2–4):**
1. Implement Level 1 automated scanning in live data pipeline.
2. Build QA database to log all flagged records with reason codes and dispositions.
3. Pilot humidity-PM correction protocol on highest-ratio site-years (e.g., Nehru Nagar, Dwarka-Sector 8) pending vendor consultation.

**Medium-term (Quarter 2):**
1. Add spatial consistency cross-checks (nearest-neighbor stations).
2. Develop seasonal and pollutant-specific threshold refinements.
3. Integrate Tier 2/3 expert review workflow into monthly data review cycles.

---

**Report prepared:** 20 April 2026  
**Analysis script version:** 1.0  
**Data currency:** 2025-04-20  
**Intended recipient:** CAQM Technical Committee, Air Quality Data Management Group
