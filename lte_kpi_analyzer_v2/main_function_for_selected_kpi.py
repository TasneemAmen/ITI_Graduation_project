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

    # require complete days -> exclude incomplete from the degraded set (kept in incomplete_df)
    if require_complete_days:
        comparison = comparison[
            (comparison["recent_days_count"] == expected_recent) &
            (comparison["baseline_days_count"] == expected_baseline)].copy()

    incomplete_df = pd.concat(incomplete_records, ignore_index=True) if incomplete_records else _empty_incomplete()

    # Degradation
    comparison["kpi_degradation_ratio_%"] = comparison.apply(
        lambda r: calculate_degradation(r["recent_avg_kpi"], r["baseline_avg_kpi"], bad_direction), axis=1)

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
        "kpi_degradation_ratio_%", "kpi_status", "stat_significant", "p_value",
        "main_cause_counter_or_kpi", "main_cause_recent_value", "main_cause_baseline_value",
        "main_cause_change_%", "main_root_cause_category", "main_degradation_reason",
        "main_recommended_action", "number_of_detected_causes", "multi_cause_flag",
        "all_detected_causes", "all_cause_categories", "all_recommended_actions",
    ]
    available_final_cols = [c for c in final_cols if c in degraded_with_causes.columns]
    return degraded_with_causes[available_final_cols].copy(), metadata
