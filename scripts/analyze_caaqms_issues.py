from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


DATA_DIR = Path("Raw_data_1Hr_CAAQMS")
OUTPUT_DIR = Path("outputs")

POLLUTANT_COLS = [
    "PM2.5 (µg/m³)",
    "PM10 (µg/m³)",
    "NO (µg/m³)",
    "NO2 (µg/m³)",
    "NOx (ppb)",
    "NH3 (µg/m³)",
    "SO2 (µg/m³)",
    "CO (mg/m³)",
    "Ozone (µg/m³)",
]

SITE_YEAR_PATTERN = re.compile(r"Raw_data_1Hr_(\d{4})_site_(\d+)_")


@dataclass
class AggregateStats:
    files_processed: int = 0
    rows_processed: int = 0
    duplicate_timestamps: int = 0
    invalid_timestamps: int = 0
    missing_hour_slots: int = 0
    gap_events: int = 0

    flatline_points: int = 0
    flatline_events: int = 0
    flatline_checked_points: int = 0

    spike_points: int = 0
    spike_events: int = 0
    spike_checked_points: int = 0

    pm25_gt_pm10_points: int = 0
    pm25_pm10_checked_points: int = 0

    unit_inconsistent_points: int = 0
    unit_checked_points: int = 0

    humidity_screened_site_years: int = 0
    humidity_suspect_site_years: int = 0


def parse_site_year(file_name: str) -> Tuple[Optional[int], Optional[int]]:
    match = SITE_YEAR_PATTERN.search(file_name)
    if not match:
        return None, None
    return int(match.group(2)), int(match.group(1))


def detect_flatline(series: pd.Series, tolerance: float = 0.5, min_run: int = 6) -> Tuple[int, int, int]:
    x = pd.to_numeric(series, errors="coerce")
    valid = x.notna().to_numpy()
    vals = x.to_numpy(dtype=float)
    checked = int(valid.sum())

    points = 0
    events = 0
    run_start = None

    for i in range(len(vals)):
        if not valid[i]:
            if run_start is not None:
                run_len = i - run_start
                if run_len >= min_run:
                    events += 1
                    points += run_len
                run_start = None
            continue

        if i == 0 or not valid[i - 1] or abs(vals[i] - vals[i - 1]) > tolerance:
            if run_start is not None:
                run_len = i - run_start
                if run_len >= min_run:
                    events += 1
                    points += run_len
            run_start = i

    if run_start is not None:
        run_len = len(vals) - run_start
        if run_len >= min_run:
            events += 1
            points += run_len

    return points, events, checked


def detect_spikes(series: pd.Series) -> Tuple[int, int, int, pd.Series]:
    x = pd.to_numeric(series, errors="coerce")
    diff = x.diff()
    valid = diff.notna()
    checked = int(valid.sum())

    if valid.sum() < 20:
        return 0, 0, checked, pd.Series(False, index=x.index)

    d = diff[valid]
    med = d.median()
    mad = (d - med).abs().median()

    if mad == 0 or np.isnan(mad):
        std = d.std()
        if np.isnan(std) or std == 0:
            return 0, 0, checked, pd.Series(False, index=x.index)
        z = (d - med).abs() / std
        spike_idx = z > 6
    else:
        robust_sigma = 1.4826 * mad
        z = (d - med).abs() / robust_sigma
        spike_idx = z > 8

    flags = pd.Series(False, index=x.index)
    flags.loc[d.index[spike_idx]] = True

    points = int(flags.sum())
    events = int(((flags) & (~flags.shift(1, fill_value=False))).sum())
    return points, events, checked, flags


def unit_consistency_check(df: pd.DataFrame) -> Tuple[int, int, pd.Series]:
    required = ["NO (µg/m³)", "NO2 (µg/m³)", "NOx (ppb)"]
    for col in required:
        if col not in df.columns:
            return 0, 0, pd.Series(False, index=df.index)

    no_ug = pd.to_numeric(df["NO (µg/m³)"], errors="coerce")
    no2_ug = pd.to_numeric(df["NO2 (µg/m³)"], errors="coerce")
    nox_ppb = pd.to_numeric(df["NOx (ppb)"], errors="coerce")

    no_ppb_est = no_ug * 24.45 / 30.0
    no2_ppb_est = no2_ug * 24.45 / 46.0
    nox_est = no_ppb_est + no2_ppb_est

    valid = nox_ppb.notna() & nox_est.notna() & (nox_ppb > 0)
    checked = int(valid.sum())
    if checked == 0:
        return 0, 0, pd.Series(False, index=df.index)

    ratio = nox_est[valid] / nox_ppb[valid]
    abs_diff = (nox_est[valid] - nox_ppb[valid]).abs()
    flag_valid = ((ratio < 0.6) | (ratio > 1.4)) & (abs_diff > 20)

    flags = pd.Series(False, index=df.index)
    flags.loc[ratio.index[flag_valid]] = True

    return int(flags.sum()), checked, flags


def pm25_gt_pm10_check(df: pd.DataFrame) -> Tuple[int, int, pd.Series]:
    if "PM2.5 (µg/m³)" not in df.columns or "PM10 (µg/m³)" not in df.columns:
        return 0, 0, pd.Series(False, index=df.index)

    pm25 = pd.to_numeric(df["PM2.5 (µg/m³)"], errors="coerce")
    pm10 = pd.to_numeric(df["PM10 (µg/m³)"], errors="coerce")

    checked = pm25.notna() & pm10.notna()
    flags = checked & (pm25 > pm10)
    return int(flags.sum()), int(checked.sum()), flags


def missing_transmission_check(df: pd.DataFrame) -> Tuple[int, int, int, int, pd.DataFrame]:
    ts = pd.to_datetime(df["Timestamp"], errors="coerce")
    invalid_ts = int(ts.isna().sum())

    ts_valid = ts.dropna().sort_values()
    if ts_valid.empty:
        return invalid_ts, 0, 0, 0, pd.DataFrame(columns=["gap_start", "gap_end", "missing_hours"])

    dup = int(ts_valid.duplicated().sum())
    unique_ts = ts_valid.drop_duplicates()

    diffs = unique_ts.diff().dropna()
    gap_mask = diffs > pd.Timedelta(hours=1)

    gap_events = int(gap_mask.sum())
    missing_slots = int((diffs[gap_mask] / pd.Timedelta(hours=1) - 1).sum())

    gap_rows = []
    for idx in diffs[gap_mask].index:
        gap_end = unique_ts.loc[idx]
        pos = unique_ts.index.get_loc(idx)
        gap_start = unique_ts.iloc[pos - 1]
        gap_rows.append(
            {
                "gap_start": gap_start,
                "gap_end": gap_end,
                "missing_hours": int((gap_end - gap_start) / pd.Timedelta(hours=1) - 1),
            }
        )

    return invalid_ts, dup, gap_events, missing_slots, pd.DataFrame(gap_rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_DIR.resolve()}")

    agg = AggregateStats()

    site_year_records: List[Dict[str, object]] = []
    flatline_examples: List[Dict[str, object]] = []
    spike_examples: List[Dict[str, object]] = []
    unit_examples: List[Dict[str, object]] = []
    pm_logic_examples: List[Dict[str, object]] = []
    gap_examples: List[Dict[str, object]] = []
    humidity_site_records: List[Dict[str, object]] = []

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
        except Exception:
            continue

        if "Timestamp" not in df.columns:
            continue

        site_id, year = parse_site_year(file_path.name)
        agg.files_processed += 1
        agg.rows_processed += len(df)

        ts = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.copy()
        df["Timestamp"] = ts

        flatline_points_file = 0
        flatline_events_file = 0
        flatline_checked_file = 0
        spike_points_file = 0
        spike_events_file = 0
        spike_checked_file = 0

        for col in POLLUTANT_COLS:
            if col not in df.columns:
                continue

            f_points, f_events, f_checked = detect_flatline(df[col])
            flatline_points_file += f_points
            flatline_events_file += f_events
            flatline_checked_file += f_checked

            s_points, s_events, s_checked, s_flags = detect_spikes(df[col])
            spike_points_file += s_points
            spike_events_file += s_events
            spike_checked_file += s_checked

            if s_points > 0 and len(spike_examples) < 3000:
                ex = df.loc[s_flags, ["Timestamp", col]].copy()
                ex = ex.head(8)
                for _, row in ex.iterrows():
                    spike_examples.append(
                        {
                            "file": file_path.name,
                            "site_id": site_id,
                            "year": year,
                            "pollutant": col,
                            "timestamp": row["Timestamp"],
                            "value": row[col],
                        }
                    )

        agg.flatline_points += flatline_points_file
        agg.flatline_events += flatline_events_file
        agg.flatline_checked_points += flatline_checked_file
        agg.spike_points += spike_points_file
        agg.spike_events += spike_events_file
        agg.spike_checked_points += spike_checked_file

        unit_points, unit_checked, unit_flags = unit_consistency_check(df)
        agg.unit_inconsistent_points += unit_points
        agg.unit_checked_points += unit_checked

        pm_points, pm_checked, pm_flags = pm25_gt_pm10_check(df)
        agg.pm25_gt_pm10_points += pm_points
        agg.pm25_pm10_checked_points += pm_checked

        invalid_ts, dup_ts, gap_events, missing_slots, gaps_df = missing_transmission_check(df)
        agg.invalid_timestamps += invalid_ts
        agg.duplicate_timestamps += dup_ts
        agg.gap_events += gap_events
        agg.missing_hour_slots += missing_slots

        if flatline_points_file > 0 and len(flatline_examples) < 3000:
            flatline_examples.append(
                {
                    "file": file_path.name,
                    "site_id": site_id,
                    "year": year,
                    "flatline_points": flatline_points_file,
                    "flatline_events": flatline_events_file,
                }
            )

        if unit_points > 0 and len(unit_examples) < 3000:
            ex = df.loc[unit_flags, ["Timestamp", "NO (µg/m³)", "NO2 (µg/m³)", "NOx (ppb)"]].head(8)
            for _, row in ex.iterrows():
                unit_examples.append(
                    {
                        "file": file_path.name,
                        "site_id": site_id,
                        "year": year,
                        "timestamp": row["Timestamp"],
                        "no_ugm3": row["NO (µg/m³)"],
                        "no2_ugm3": row["NO2 (µg/m³)"],
                        "nox_ppb": row["NOx (ppb)"],
                    }
                )

        if pm_points > 0 and len(pm_logic_examples) < 3000:
            ex = df.loc[pm_flags, ["Timestamp", "PM2.5 (µg/m³)", "PM10 (µg/m³)"]].head(8)
            for _, row in ex.iterrows():
                pm_logic_examples.append(
                    {
                        "file": file_path.name,
                        "site_id": site_id,
                        "year": year,
                        "timestamp": row["Timestamp"],
                        "pm25": row["PM2.5 (µg/m³)"],
                        "pm10": row["PM10 (µg/m³)"],
                    }
                )

        if not gaps_df.empty and len(gap_examples) < 3000:
            for _, row in gaps_df.head(8).iterrows():
                gap_examples.append(
                    {
                        "file": file_path.name,
                        "site_id": site_id,
                        "year": year,
                        "gap_start": row["gap_start"],
                        "gap_end": row["gap_end"],
                        "missing_hours": row["missing_hours"],
                    }
                )

        if "RH (%)" in df.columns and "PM2.5 (µg/m³)" in df.columns:
            rh = pd.to_numeric(df["RH (%)"], errors="coerce")
            pm25 = pd.to_numeric(df["PM2.5 (µg/m³)"], errors="coerce")

            high = pm25[(rh > 85) & pm25.notna()]
            low = pm25[(rh < 60) & pm25.notna()]

            if len(high) >= 100 and len(low) >= 100:
                med_high = float(high.median())
                med_low = float(low.median())
                ratio = med_high / med_low if med_low > 0 else np.nan
                suspected = bool(ratio >= 1.5) if not np.isnan(ratio) else False
                agg.humidity_screened_site_years += 1
                agg.humidity_suspect_site_years += int(suspected)
                humidity_site_records.append(
                    {
                        "file": file_path.name,
                        "site_id": site_id,
                        "year": year,
                        "high_rh_count": int(len(high)),
                        "low_rh_count": int(len(low)),
                        "median_pm25_high_rh": med_high,
                        "median_pm25_low_rh": med_low,
                        "high_low_ratio": ratio,
                        "suspected_humidity_bias": suspected,
                    }
                )

        site_year_records.append(
            {
                "file": file_path.name,
                "site_id": site_id,
                "year": year,
                "rows": int(len(df)),
                "flatline_points": flatline_points_file,
                "flatline_events": flatline_events_file,
                "flatline_checked_points": flatline_checked_file,
                "spike_points": spike_points_file,
                "spike_events": spike_events_file,
                "spike_checked_points": spike_checked_file,
                "unit_inconsistent_points": unit_points,
                "unit_checked_points": unit_checked,
                "pm25_gt_pm10_points": pm_points,
                "pm25_pm10_checked_points": pm_checked,
                "invalid_timestamps": invalid_ts,
                "duplicate_timestamps": dup_ts,
                "gap_events": gap_events,
                "missing_hour_slots": missing_slots,
            }
        )

    issues_summary = pd.DataFrame(
        [
            {
                "issue": "Continuous identical or near-identical values",
                "affected_points": agg.flatline_points,
                "events": agg.flatline_events,
                "denominator": agg.flatline_checked_points,
                "affected_percent": (100 * agg.flatline_points / agg.flatline_checked_points)
                if agg.flatline_checked_points
                else np.nan,
            },
            {
                "issue": "Sudden spikes or sharp drops",
                "affected_points": agg.spike_points,
                "events": agg.spike_events,
                "denominator": agg.spike_checked_points,
                "affected_percent": (100 * agg.spike_points / agg.spike_checked_points)
                if agg.spike_checked_points
                else np.nan,
            },
            {
                "issue": "Unit inconsistencies (NO/NO2/NOx)",
                "affected_points": agg.unit_inconsistent_points,
                "events": np.nan,
                "denominator": agg.unit_checked_points,
                "affected_percent": (100 * agg.unit_inconsistent_points / agg.unit_checked_points)
                if agg.unit_checked_points
                else np.nan,
            },
            {
                "issue": "PM2.5 > PM10 logical inconsistency",
                "affected_points": agg.pm25_gt_pm10_points,
                "events": np.nan,
                "denominator": agg.pm25_pm10_checked_points,
                "affected_percent": (100 * agg.pm25_gt_pm10_points / agg.pm25_pm10_checked_points)
                if agg.pm25_pm10_checked_points
                else np.nan,
            },
            {
                "issue": "Delayed or missing data transmission",
                "affected_points": agg.missing_hour_slots,
                "events": agg.gap_events,
                "denominator": agg.rows_processed,
                "affected_percent": (100 * agg.missing_hour_slots / agg.rows_processed) if agg.rows_processed else np.nan,
            },
            {
                "issue": "High RH conditions impacting PM readings",
                "affected_points": agg.humidity_suspect_site_years,
                "events": np.nan,
                "denominator": agg.humidity_screened_site_years,
                "affected_percent": (100 * agg.humidity_suspect_site_years / agg.humidity_screened_site_years)
                if agg.humidity_screened_site_years
                else np.nan,
            },
        ]
    )

    pd.DataFrame(site_year_records).to_csv(OUTPUT_DIR / "issue_by_site_year.csv", index=False)
    issues_summary.to_csv(OUTPUT_DIR / "issue_summary.csv", index=False)

    pd.DataFrame(flatline_examples).to_csv(OUTPUT_DIR / "flatline_examples.csv", index=False)
    pd.DataFrame(spike_examples).to_csv(OUTPUT_DIR / "spike_examples.csv", index=False)
    pd.DataFrame(unit_examples).to_csv(OUTPUT_DIR / "unit_inconsistency_examples.csv", index=False)
    pd.DataFrame(pm_logic_examples).to_csv(OUTPUT_DIR / "pm25_gt_pm10_examples.csv", index=False)
    pd.DataFrame(gap_examples).to_csv(OUTPUT_DIR / "missing_data_gap_examples.csv", index=False)
    pd.DataFrame(humidity_site_records).to_csv(OUTPUT_DIR / "humidity_bias_screening.csv", index=False)

    summary_txt = [
        "CAAQMS Issue Screening Summary",
        f"Files processed: {agg.files_processed}",
        f"Rows processed: {agg.rows_processed}",
        f"Invalid timestamps: {agg.invalid_timestamps}",
        f"Duplicate timestamps: {agg.duplicate_timestamps}",
        f"Missing hourly slots: {agg.missing_hour_slots}",
        "",
        "Issue summary (affected points / denominator):",
    ]

    for _, row in issues_summary.iterrows():
        pct = row["affected_percent"]
        pct_txt = f"{pct:.2f}%" if pd.notna(pct) else "NA"
        summary_txt.append(
            f"- {row['issue']}: {int(row['affected_points'])} / {int(row['denominator']) if pd.notna(row['denominator']) else 'NA'} ({pct_txt})"
        )

    (OUTPUT_DIR / "run_summary.txt").write_text("\n".join(summary_txt), encoding="utf-8")


if __name__ == "__main__":
    main()
