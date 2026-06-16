# ============================================================
# LTE KPI Degradation Analyzer - Main Function for Selected KPI
# ============================================================
# Adds a data-quality layer:
#   * invalid counter values (unit violations / sentinels) are nulled and
#     recorded in metadata["quarantine_df"];
#   * baseline gaps are imputed from the same-weekday median over 4 weeks
#     (recent window is NOT imputed);
#   * cells with incomplete/insufficient data are recorded in
#     metadata["incomplete_df"] instead of being silently dropped.
# Output columns are unchanged except a new "baseline_imputed_days" column.
# ============================================================

import numpy as np
import pandas as pd

from KPI_Configuration import (
    DATE_COL,
    SITE_COL,
    CELL_COL,
    CELL_ID_COLS,
    KPI_CONFIGS,
    BASELINE_MODE_LAST_WEEK,
    BASELINE_MODE_4WEEK_AVG,
    BASELINE_MODE_CUSTOM,
)
from clean_excel_and_helpers import (
    clean_excel_columns,
    clean_numeric_series,
    find_matching_column,
    calculate_degradation,
    perform_ttest,
    get_periods_enhanced,
)
from cause_detect_functions import (
    find_degradation_causes_vectorized,
    find_degradation_causes_row,
)
from data_quality import validate_columns, compute_baseline_imputed


def _empty_quarantine():
    return pd.DataFrame(columns=CELL_ID_COLS + [DATE_COL, "kpi", "counter", "bad_value", "reason"])


def _empty_incomplete():
    return pd.DataFrame(columns=CELL_ID_COLS + [
        "kpi", "recent_days_count", "baseline_days_count",
        "expected_recent_days", "expected_baseline_days", "reason"])


def analyze_selected_kpi(
    df,
    selected_kpi_name,
    num_days,
    degradation_threshold,
    require_complete_days=True,
    baseline_mode="last_week",
    custom_baseline_start=None,
    custom_baseline_end=None,
    enable_significance_test=True,
    log_callback=None,
):
    """Main analysis function for a single KPI. Returns (output_df, metadata).

    metadata additionally carries:
        quarantine_df  - invalid counter values (operator action needed)
        incomplete_df  - cells with missing/insufficient days
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)

    config = KPI_CONFIGS[selected_kpi_name]
    df = clean_excel_columns(df)

    original_target_kpi = config["target_kpi"]
    target_kpi = find_matching_column(df, original_target_kpi)
    if target_kpi is None:
        raise ValueError(f"Target KPI column not found in Excel: {original_target_kpi}")

    bad_direction = config["bad_direction"]
    related_rules = config["related_rules"]
    min_baseline_value = config.get("min_baseline_value", 0.0)

    needed_cols = CELL_ID_COLS + [DATE_COL, target_kpi]
    missing_cols = [c for c in needed_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df_kpi = df[needed_cols].copy()
    df_kpi[DATE_COL] = pd.to_datetime(df_kpi[DATE_COL], errors="coerce").dt.normalize()
    df_kpi[target_kpi] = clean_numeric_series(df_kpi[target_kpi])
    df_kpi = df_kpi.dropna(subset=[DATE_COL])

    # ---- Data quality: validate target, quarantine invalid values (-> NaN) ----
    quarantine_frames = []
    df_kpi, q_target = validate_columns(
        df_kpi, [target_kpi], selected_kpi_name, CELL_ID_COLS, DATE_COL, log_msg)
    quarantine_frames.append(q_target)

    # Periods
    last_date, recent_start, recent_end, baseline_start, baseline_end = get_periods_enhanced(
        df_kpi, DATE_COL, num_days, baseline_mode, custom_baseline_start, custom_baseline_end)

    recent_dates = list(pd.date_range(recent_start, recent_end, freq="D"))
    baseline_dates = list(pd.date_range(baseline_start, baseline_end, freq="D"))
    expected_recent = len(recent_dates)
    expected_baseline = len(baseline_dates)

    target_obs = df_kpi.dropna(subset=[target_kpi])

    # Recent aggregation (observed only - never imputed)
    recent_df = target_obs[(target_obs[DATE_COL] >= recent_start) & (target_obs[DATE_COL] <= recent_end)].copy()
    recent_agg = recent_df.groupby(CELL_ID_COLS).agg({
        target_kpi: ["mean", "max", "sum"], DATE_COL: "nunique"}).reset_index()
    recent_agg.columns = CELL_ID_COLS + ["recent_avg_kpi", "recent_max_kpi", "recent_total_kpi", "recent_days_count"]

    # Observed baseline slice (used ONLY for the significance test)
    baseline_obs_df = target_obs[(target_obs[DATE_COL] >= baseline_start) & (target_obs[DATE_COL] <= baseline_end)].copy()

    # Baseline aggregation WITH same-weekday median imputation
    base_imp = compute_baseline_imputed(target_obs, target_kpi, CELL_ID_COLS, DATE_COL, baseline_dates)
    base_imp = base_imp.rename(columns={
        "baseline_avg": "baseline_avg_kpi", "baseline_max": "baseline_max_kpi",
        "baseline_total": "baseline_total_kpi", "baseline_days_count": "baseline_days_count",
        "imputed_days_count": "baseline_imputed_days"})

    # ---- Track cells (don't drop silently) ----
    incomplete_records = []
    merged_all = recent_agg.merge(base_imp, on=CELL_ID_COLS, how="outer", indicator=True)

    def _record(sub, reason):
        if sub.empty:
            return
        rec = sub[CELL_ID_COLS].copy()
        rec["kpi"] = selected_kpi_name
        rec["recent_days_count"] = sub.get("recent_days_count")
        rec["baseline_days_count"] = sub.get("baseline_days_count")
        rec["expected_recent_days"] = expected_recent
        rec["expected_baseline_days"] = expected_baseline
        rec["reason"] = reason
        incomplete_records.append(rec)

    _record(merged_all[merged_all["_merge"] == "left_only"], "no baseline data (even after imputation)")
    _record(merged_all[merged_all["_merge"] == "right_only"], "no recent data")

    comparison = merged_all[merged_all["_merge"] == "both"].drop(columns="_merge").copy()

    # zero baseline -> degradation undefined; record and exclude
    zero_baseline = comparison[comparison["baseline_avg_kpi"].fillna(0) == 0]
    _record(zero_baseline, "zero baseline value (degradation undefined)")
    comparison = comparison[comparison["baseline_avg_kpi"].fillna(0) != 0].copy()

    # incomplete day counts (after imputation for baseline)
    inc_mask = (comparison["recent_days_count"] < expected_recent) | (comparison["baseline_days_count"] < expected_baseline)
    _record(comparison[inc_mask], "incomplete day count (recent or baseline)")

    # min baseline value filter (unchanged behavior)
    if min_baseline_value > 0:
        excluded_by_min = int((comparison["baseline_avg_kpi"] < min_baseline_value).sum())
        if excluded_by_min:
            log_msg(f"INFO: {excluded_by_min} cells excluded by min_baseline_value filter (< {min_baseline_value})")
        comparison = comparison[comparison["baseline_avg_kpi"] >= min_baseline_value].copy()
    else:
        excluded_by_min = 0

    # require_complete_days now applies strictly to BASELINE only.
    # Recent windows are allowed to be partial — the paired comparison
    # below transparently handles missing recent days without bias.
    if require_complete_days:
        comparison = comparison[
            comparison["baseline_days_count"] == expected_baseline].copy()

    # ================================================================
    # ADVANCED: Day-aligned paired comparison with confidence scoring
    # ================================================================
    #
    # Why this replaces the naive degradation calculation:
    #
    # The old approach computed degradation as:
    #   (mean(baseline) - mean(recent)) / mean(baseline)
    #
    # When recent has missing days, those mean values come from different
    # day samples, which introduces bias from day-of-week seasonality
    # (LTE traffic varies a lot between weekdays/weekends).
    #
    # The new approach pairs each recent day with its baseline twin:
    #   - last_week mode : recent Monday <-> baseline Monday (date - 7d)
    #   - 4-week mode    : recent Monday <-> median of all baseline Mondays
    #   - custom mode    : treated like last_week (7-day offset)
    #
    # Missing recent days simply produce no pair — they don't distort
    # the result. Two transparency columns are added so the RF engineer
    # can judge data quality:
    #   paired_days_count   : how many real day-pairs backed the result
    #   confidence_score_%  : paired_days_count / expected_recent * 100
    #   daily_ratios        : per-pair list, for audit / debugging
    #
    # Note: paired comparison uses OBSERVED data only. The imputed
    # baseline_avg_kpi summary column is kept for the report, but the
    # degradation% uses real pair-wise comparisons.
    # ================================================================

    # ── Quality floors ───────────────────────────────────────────────
    # MIN_PAIRED_DAYS: absolute minimum number of real day-pairs needed.
    # Scaled to expected_recent so small recent windows aren't impossible:
    #   expected_recent <= 2 → floor of 1 (single pair acceptable)
    #   expected_recent  > 2 → floor of 2 (avoid trusting a single day)
    # MIN_RECENT_COVERAGE: also need at least this fraction of recent days
    # to be paired. Combined with the floor via max().
    # FIX (Flaw 5): for very small num_days (1-2), the old fixed floor of 2
    # made the tool exclude every cell. Now it scales sensibly.
    MIN_PAIRED_DAYS = 1 if expected_recent <= 2 else 2
    MIN_RECENT_COVERAGE = 0.5

    # Pre-build per-cell-per-date lookups (one row per cell+date).
    # This makes per-cell lookup O(1) instead of repeated filtering.
    recent_per_day = (recent_df.groupby(CELL_ID_COLS + [DATE_COL])[target_kpi]
                      .mean())
    baseline_per_day = (baseline_obs_df.groupby(CELL_ID_COLS + [DATE_COL])[target_kpi]
                        .mean())

    # In 4-week mode AND custom mode (when the offset doesn't land in the
    # custom window), we need a weekday-keyed baseline. Pre-compute median
    # of matching weekdays for each cell.
    # FIX (Flaw 4): custom mode now also uses this fallback when the strict
    # 7-day offset doesn't find a twin in the custom baseline window.
    needs_weekday_fallback = baseline_mode in (
        BASELINE_MODE_4WEEK_AVG, BASELINE_MODE_CUSTOM)
    baseline_weekday_median = {}
    if needs_weekday_fallback:
        # Build {cell_tuple: {weekday: median_value}}
        tmp = baseline_obs_df.copy()
        tmp["_wd"] = tmp[DATE_COL].dt.weekday
        wd_grouped = (tmp.groupby(CELL_ID_COLS + ["_wd"])[target_kpi]
                      .median())
        for idx, val in wd_grouped.items():
            cell_key = idx[:-1]   # cell id tuple
            wd = idx[-1]
            baseline_weekday_median.setdefault(cell_key, {})[wd] = val

    paired_degradations = []
    paired_counts = []
    daily_ratios_strs = []
    min_pair_ratios = []        # FIX (Flaw 8): numeric audit column
    max_pair_ratios = []        # FIX (Flaw 8): numeric audit column
    rows_to_drop = []           # indices of cells that fail the paired-days check

    for idx, row in comparison.iterrows():
        # Build the cell identity tuple to look up by
        cell_key = tuple(row[c] for c in CELL_ID_COLS)

        # Fetch this cell's per-day recent and baseline values.
        # .loc on a MultiIndex Series with a partial key returns a sub-series.
        try:
            cell_recent_series = recent_per_day.loc[cell_key]
            cell_recent_dict = cell_recent_series.to_dict() \
                if hasattr(cell_recent_series, "to_dict") \
                else {cell_recent_series.name: cell_recent_series}
        except KeyError:
            cell_recent_dict = {}

        try:
            cell_baseline_series = baseline_per_day.loc[cell_key]
            cell_baseline_dict = cell_baseline_series.to_dict() \
                if hasattr(cell_baseline_series, "to_dict") \
                else {cell_baseline_series.name: cell_baseline_series}
        except KeyError:
            cell_baseline_dict = {}

        # Run paired comparison for this cell
        ratios = []
        for r_date, r_val in cell_recent_dict.items():
            if pd.isna(r_val):
                continue

            # ── Find the baseline twin for this recent date ──
            if baseline_mode == BASELINE_MODE_4WEEK_AVG:
                # Compare against median of matching weekdays in baseline
                wd_map = baseline_weekday_median.get(cell_key, {})
                b_val = wd_map.get(r_date.weekday())

            elif baseline_mode == BASELINE_MODE_CUSTOM:
                # FIX (Flaw 4): try strict 7-day offset first, then fall
                # back to closest matching weekday if that lands outside
                # the custom baseline window.
                b_date = r_date - pd.Timedelta(days=7)
                b_val = cell_baseline_dict.get(b_date)
                if b_val is None or pd.isna(b_val):
                    # Fall back to median of matching weekdays
                    wd_map = baseline_weekday_median.get(cell_key, {})
                    b_val = wd_map.get(r_date.weekday())

            else:
                # last_week mode (and any unknown mode): exact 7-day offset
                b_date = r_date - pd.Timedelta(days=7)
                b_val = cell_baseline_dict.get(b_date)

            if b_val is None or pd.isna(b_val) or b_val == 0:
                continue

            ratio = calculate_degradation(r_val, b_val, bad_direction)
            if not pd.isna(ratio):
                ratios.append(ratio)

        paired_count = len(ratios)
        mean_ratio = float(np.mean(ratios)) if ratios else np.nan
        # FIX (Flaw 8): expose min/max as numeric columns for downstream
        # analysis (Excel formulas, etc.). NaN when no pairs exist.
        min_ratio = float(np.min(ratios)) if ratios else np.nan
        max_ratio = float(np.max(ratios)) if ratios else np.nan

        # Check quality floors. A cell must have at least min_pairs_needed
        # real day-pairs to be trusted.
        min_pairs_needed = max(
            MIN_PAIRED_DAYS,
            int(np.ceil(expected_recent * MIN_RECENT_COVERAGE)))

        if paired_count < min_pairs_needed or pd.isna(mean_ratio):
            # Mark for removal and record in incomplete_df
            rows_to_drop.append(idx)
            inc_rec = pd.DataFrame({
                **{c: [row[c]] for c in CELL_ID_COLS},
                "kpi": [selected_kpi_name],
                "recent_days_count": [row.get("recent_days_count")],
                "baseline_days_count": [row.get("baseline_days_count")],
                "expected_recent_days": [expected_recent],
                "expected_baseline_days": [expected_baseline],
                "reason": [f"too few paired days ({paired_count} < {min_pairs_needed})"],
            })
            incomplete_records.append(inc_rec)
            paired_degradations.append(np.nan)
            paired_counts.append(paired_count)
            daily_ratios_strs.append(str([round(r, 2) for r in ratios]))
            min_pair_ratios.append(min_ratio)
            max_pair_ratios.append(max_ratio)
        else:
            paired_degradations.append(mean_ratio)
            paired_counts.append(paired_count)
            daily_ratios_strs.append(str([round(r, 2) for r in ratios]))
            min_pair_ratios.append(min_ratio)
            max_pair_ratios.append(max_ratio)

    # Attach paired results as new columns
    comparison["paired_days_count"] = paired_counts
    comparison["daily_ratios"] = daily_ratios_strs
    # FIX (Flaw 8): numeric audit columns. Round to 2dp for readability.
    comparison["min_pair_ratio_%"] = pd.Series(min_pair_ratios,
                                                index=comparison.index).round(2)
    comparison["max_pair_ratio_%"] = pd.Series(max_pair_ratios,
                                                index=comparison.index).round(2)
    comparison["confidence_score_%"] = (
        comparison["paired_days_count"] / expected_recent * 100).round(1)
    comparison["_paired_degradation"] = paired_degradations

    # Drop the cells that failed the paired-days check
    if rows_to_drop:
        log_msg(f"INFO: {len(rows_to_drop)} cells excluded from paired "
                f"comparison (too few day-pairs). See incomplete_df.")
        comparison = comparison.drop(index=rows_to_drop).copy()

    incomplete_df = pd.concat(incomplete_records, ignore_index=True) if incomplete_records else _empty_incomplete()

    # Degradation: use the paired result computed above. This is the
    # accurate day-aligned ratio, not the naive (mean - mean) / mean.
    comparison["kpi_degradation_ratio_%"] = comparison["_paired_degradation"]
    comparison = comparison.drop(columns=["_paired_degradation"])

    # Significance test on OBSERVED values only (never on imputed data)
    if enable_significance_test and not comparison.empty:
        results = []
        for idx, row in comparison.iterrows():
            cid = (row[SITE_COL], row[CELL_COL])
            cr = recent_df[(recent_df[SITE_COL] == cid[0]) & (recent_df[CELL_COL] == cid[1])][target_kpi]
            cb = baseline_obs_df[(baseline_obs_df[SITE_COL] == cid[0]) & (baseline_obs_df[CELL_COL] == cid[1])][target_kpi]
            is_sig, p_val, t_stat = perform_ttest(cr, cb)
            results.append({"index": idx, "stat_significant": is_sig, "p_value": p_val, "t_statistic": t_stat})
        sig_df = pd.DataFrame(results).set_index("index")
        comparison["stat_significant"] = sig_df["stat_significant"].reindex(comparison.index).fillna(False)
        comparison["p_value"] = sig_df["p_value"].reindex(comparison.index)
        comparison["t_statistic"] = sig_df["t_statistic"].reindex(comparison.index)

    if enable_significance_test:
        comparison["kpi_status"] = np.where(
            (comparison["kpi_degradation_ratio_%"] >= degradation_threshold) &
            (comparison.get("stat_significant", False) == True), "Degraded", "Normal")
    else:
        comparison["kpi_status"] = np.where(
            comparison["kpi_degradation_ratio_%"] >= degradation_threshold, "Degraded", "Normal")

    comparison["selected_kpi_name"] = selected_kpi_name
    comparison["target_kpi_column"] = target_kpi
    comparison["kpi_category"] = config["category"]
    comparison["kpi_bad_direction"] = bad_direction
    comparison["selected_threshold_%"] = degradation_threshold
    comparison["recent_period"] = f"{recent_start.date()} to {recent_end.date()}"
    comparison["baseline_period"] = f"{baseline_start.date()} to {baseline_end.date()}"
    comparison["baseline_mode"] = baseline_mode

    degraded_cells = comparison[comparison["kpi_status"] == "Degraded"].copy()
    degraded_cells = degraded_cells.sort_values("kpi_degradation_ratio_%", ascending=False)

    debug_info = {
        "cells_after_merge": comparison.shape[0],
        "max_degradation": comparison["kpi_degradation_ratio_%"].max() if not comparison.empty else None,
        "min_degradation": comparison["kpi_degradation_ratio_%"].min() if not comparison.empty else None,
        "mean_degradation": comparison["kpi_degradation_ratio_%"].mean() if not comparison.empty else None,
        "min_baseline_excluded": excluded_by_min,
        "incomplete_cells": int(incomplete_df.shape[0]),
        "quarantined_values": int(sum(f.shape[0] for f in quarantine_frames)),
    }
    metadata = {
        "last_date": last_date,
        "recent_start": recent_start, "recent_end": recent_end,
        "baseline_start": baseline_start, "baseline_end": baseline_end,
        "baseline_mode": baseline_mode,
        "available_related_features": [], "missing_related_features": [],
        "debug_info": debug_info,
        "quarantine_df": _empty_quarantine(),
        "incomplete_df": incomplete_df,
    }

    if degraded_cells.empty:
        metadata["quarantine_df"] = pd.concat(quarantine_frames, ignore_index=True) if quarantine_frames else _empty_quarantine()
        return degraded_cells, metadata

    # ---- Related counters (cause detection) ----
    available_related_rules, missing_related_features = [], []
    for rule in related_rules:
        matched = find_matching_column(df, rule["feature"])
        if matched is not None:
            nr = rule.copy(); nr["feature"] = matched
            available_related_rules.append(nr)
        else:
            missing_related_features.append(rule["feature"])
    available_related_features = [r["feature"] for r in available_related_rules]
    metadata["available_related_features"] = available_related_features
    metadata["missing_related_features"] = missing_related_features

    if available_related_features:
        reason_cols = CELL_ID_COLS + [DATE_COL] + available_related_features
        df_reason = df[reason_cols].copy()
        df_reason[DATE_COL] = pd.to_datetime(df_reason[DATE_COL], errors="coerce").dt.normalize()
        for col in available_related_features:
            df_reason[col] = clean_numeric_series(df_reason[col])

        # validate + quarantine related counters
        df_reason, q_feat = validate_columns(
            df_reason, available_related_features, selected_kpi_name, CELL_ID_COLS, DATE_COL, log_msg)
        quarantine_frames.append(q_feat)

        # restrict to degraded cells for efficiency
        deg_keys = degraded_cells[CELL_ID_COLS].drop_duplicates()
        df_reason = df_reason.merge(deg_keys, on=CELL_ID_COLS, how="inner")

        recent_reason_df = df_reason[(df_reason[DATE_COL] >= recent_start) & (df_reason[DATE_COL] <= recent_end)].copy()

        recent_reason_agg = recent_reason_df.groupby(CELL_ID_COLS).agg(
            {c: ["mean", "max"] for c in available_related_features}).reset_index()
        rcols = CELL_ID_COLS.copy()
        for c in available_related_features:
            rcols += [f"recent_{c}_mean", f"recent_{c}_max"]
        recent_reason_agg.columns = rcols

        # imputed baseline per feature
        baseline_reason_agg = deg_keys.copy()
        for c in available_related_features:
            bi = compute_baseline_imputed(
                df_reason.dropna(subset=[c])[CELL_ID_COLS + [DATE_COL, c]], c,
                CELL_ID_COLS, DATE_COL, baseline_dates)
            bi = bi.rename(columns={"baseline_avg": f"baseline_{c}_mean", "baseline_max": f"baseline_{c}_max"})
            baseline_reason_agg = baseline_reason_agg.merge(
                bi[CELL_ID_COLS + [f"baseline_{c}_mean", f"baseline_{c}_max"]], on=CELL_ID_COLS, how="left")

        for c in available_related_features:
            recent_reason_agg[f"recent_{c}"] = recent_reason_agg[f"recent_{c}_mean"]
            baseline_reason_agg[f"baseline_{c}"] = baseline_reason_agg[f"baseline_{c}_mean"]

        degraded_with_causes = degraded_cells.merge(recent_reason_agg, on=CELL_ID_COLS, how="left")
        degraded_with_causes = degraded_with_causes.merge(baseline_reason_agg, on=CELL_ID_COLS, how="left")
        degraded_with_causes = degraded_with_causes.reset_index(drop=True)

        try:
            cause_results = find_degradation_causes_vectorized(degraded_with_causes, available_related_rules)
            degraded_with_causes = pd.concat([degraded_with_causes.reset_index(drop=True), cause_results.reset_index(drop=True)], axis=1)
        except Exception as vec_error:
            log_msg(f"Vectorized cause detection failed, using fallback: {vec_error}")
            cause_results = degraded_with_causes.apply(
                lambda row: find_degradation_causes_row(row, available_related_rules), axis=1)
            degraded_with_causes = pd.concat([degraded_with_causes, cause_results], axis=1)
    else:
        degraded_with_causes = degraded_cells.copy()
        degraded_with_causes["main_cause_counter_or_kpi"] = "No related counters available in sheet"
        degraded_with_causes["main_cause_recent_value"] = np.nan
        degraded_with_causes["main_cause_baseline_value"] = np.nan
        degraded_with_causes["main_cause_change_%"] = np.nan
        degraded_with_causes["main_root_cause_category"] = "Unknown"
        degraded_with_causes["main_degradation_reason"] = "No related counters from the config were found in the uploaded sheet."
        degraded_with_causes["main_recommended_action"] = "Check KPI manually or update KPI_CONFIGS with available counters."
        degraded_with_causes["number_of_detected_causes"] = 0
        degraded_with_causes["multi_cause_flag"] = "No"
        degraded_with_causes["all_detected_causes"] = "None"
        degraded_with_causes["all_cause_categories"] = "Unknown"
        degraded_with_causes["all_recommended_actions"] = "Manual investigation needed"

    metadata["quarantine_df"] = pd.concat(quarantine_frames, ignore_index=True) if quarantine_frames else _empty_quarantine()

    final_cols = CELL_ID_COLS + [
        "selected_kpi_name", "target_kpi_column", "kpi_category", "kpi_bad_direction",
        "selected_threshold_%", "recent_period", "baseline_period", "baseline_mode",
        "recent_avg_kpi", "baseline_avg_kpi", "recent_max_kpi", "baseline_max_kpi",
        "recent_total_kpi", "baseline_total_kpi", "recent_days_count", "baseline_days_count",
        "baseline_imputed_days",
        # --- NEW: paired comparison transparency columns ---
        "paired_days_count", "confidence_score_%",
        "min_pair_ratio_%", "max_pair_ratio_%", "daily_ratios",
        # ----------------------------------------------------
        "kpi_degradation_ratio_%", "kpi_status", "stat_significant", "p_value",
        "main_cause_counter_or_kpi", "main_cause_recent_value", "main_cause_baseline_value",
        "main_cause_change_%", "main_root_cause_category", "main_degradation_reason",
        "main_recommended_action", "number_of_detected_causes", "multi_cause_flag",
        "all_detected_causes", "all_cause_categories", "all_recommended_actions",
    ]
    available_final_cols = [c for c in final_cols if c in degraded_with_causes.columns]
    return degraded_with_causes[available_final_cols].copy(), metadata
