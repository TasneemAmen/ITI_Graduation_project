# ============================================================
# LTE KPI Degradation Analyzer - Main Function for Selected KPI
# ============================================================
# This file contains the main analysis function for a single KPI.
# ============================================================

import numpy as np
import pandas as pd

from KPI_Configuration import (
    DATE_COL,
    SITE_COL,
    CELL_COL,
    CELL_ID_COLS,
    KPI_CONFIGS,
    allows_negative,
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
    log_callback=None
):
    """
    Main analysis function for a single KPI.
    
    Features:
    - Configurable baseline window (7-day, 4-week rolling, custom)
    - Minimum baseline value filter per KPI
    - Statistical significance test (Welch's t-test)
    - Max/percentile aggregation for failure counters
    - Severity weighting for cause ranking
    
    Args:
        df: Input DataFrame with KPI data
        selected_kpi_name: Name of KPI to analyze (must be in KPI_CONFIGS)
        num_days: Number of days for recent period
        degradation_threshold: Threshold percentage for degradation detection
        require_complete_days: Whether to require complete data for both periods
        baseline_mode: Baseline calculation mode
        custom_baseline_start: Custom baseline start date (for CUSTOM mode)
        custom_baseline_end: Custom baseline end date (for CUSTOM mode)
        enable_significance_test: Whether to perform t-test significance check
        log_callback: Optional callback function for logging messages
        
    Returns:
        Tuple of (output_df, metadata)
        - output_df: DataFrame with degraded cells and cause analysis
        - metadata: Dict with analysis metadata and debug info
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    config = KPI_CONFIGS[selected_kpi_name]
    
    # Clean Excel column names
    df = clean_excel_columns(df)
    
    # Smart target KPI matching
    original_target_kpi = config["target_kpi"]
    target_kpi = find_matching_column(df, original_target_kpi)
    
    if target_kpi is None:
        raise ValueError(f"Target KPI column not found in Excel: {original_target_kpi}")
    
    bad_direction = config["bad_direction"]
    related_rules = config["related_rules"]
    min_baseline_value = config.get("min_baseline_value", 0.0)
    
    needed_cols = CELL_ID_COLS + [DATE_COL, target_kpi]
    missing_cols = [col for col in needed_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    df_kpi = df[needed_cols].copy()
    # Normalize date to handle hourly data
    df_kpi[DATE_COL] = pd.to_datetime(df_kpi[DATE_COL], errors="coerce").dt.normalize()
    df_kpi[target_kpi] = clean_numeric_series(df_kpi[target_kpi])
    df_kpi = df_kpi.dropna(subset=[DATE_COL, target_kpi])
    # Filter negatives only when the metric unit forbids them (no-op for
    # all current targets; protects a future RSRP/RSRQ/dBm target).
    if not allows_negative(target_kpi):
        df_kpi = df_kpi[df_kpi[target_kpi] >= 0]
    df_kpi = df_kpi.copy()
    
    # Get periods with enhanced baseline mode
    last_date, recent_start, recent_end, baseline_start, baseline_end = get_periods_enhanced(
        df_kpi, DATE_COL, num_days, baseline_mode, custom_baseline_start, custom_baseline_end
    )
    
    recent_df = df_kpi[(df_kpi[DATE_COL] >= recent_start) & (df_kpi[DATE_COL] <= recent_end)].copy()
    baseline_df = df_kpi[(df_kpi[DATE_COL] >= baseline_start) & (df_kpi[DATE_COL] <= baseline_end)].copy()
    
    # Aggregation
    recent_agg = recent_df.groupby(CELL_ID_COLS).agg({
        target_kpi: ["mean", "max", "sum"],
        DATE_COL: "nunique"
    }).reset_index()
    recent_agg.columns = CELL_ID_COLS + ["recent_avg_kpi", "recent_max_kpi", "recent_total_kpi", "recent_days_count"]
    
    baseline_agg = baseline_df.groupby(CELL_ID_COLS).agg({
        target_kpi: ["mean", "max", "sum"],
        DATE_COL: "nunique"
    }).reset_index()
    baseline_agg.columns = CELL_ID_COLS + ["baseline_avg_kpi", "baseline_max_kpi", "baseline_total_kpi", "baseline_days_count"]
    
    comparison = recent_agg.merge(baseline_agg, on=CELL_ID_COLS, how="inner")
    
    if require_complete_days:
        comparison = comparison[
            (comparison["recent_days_count"] == num_days) &
            (comparison["baseline_days_count"] == num_days)
        ].copy()
    
    # Log warning for zero baseline cells
    zero_baseline_mask = comparison["baseline_avg_kpi"] == 0
    zero_baseline_count = zero_baseline_mask.sum()
    if zero_baseline_count > 0:
        zero_baseline_cells = comparison[zero_baseline_mask][CELL_COL].head(10).tolist()
        log_msg(f"WARNING: {zero_baseline_count} cells have zero baseline value and will be excluded")
        log_msg(f"Examples: {zero_baseline_cells}")
    
    comparison = comparison[comparison["baseline_avg_kpi"] != 0].copy()
    
    # Apply minimum baseline value filter
    if min_baseline_value > 0:
        min_baseline_mask = comparison["baseline_avg_kpi"] >= min_baseline_value
        excluded_by_min = (~min_baseline_mask).sum()
        if excluded_by_min > 0:
            log_msg(f"INFO: {excluded_by_min} cells excluded by min_baseline_value filter (< {min_baseline_value})")
        comparison = comparison[min_baseline_mask].copy()
    else:
        excluded_by_min = 0
    
    # Calculate degradation
    comparison["kpi_degradation_ratio_%"] = comparison.apply(
        lambda row: calculate_degradation(row["recent_avg_kpi"], row["baseline_avg_kpi"], bad_direction),
        axis=1,
    )
    
    # Statistical significance test
    if enable_significance_test:
        significance_results = []
        for idx, row in comparison.iterrows():
            cell_id = (row[SITE_COL], row[CELL_COL])
            
            cell_recent = recent_df[
                (recent_df[SITE_COL] == cell_id[0]) & 
                (recent_df[CELL_COL] == cell_id[1])
            ][target_kpi]
            cell_baseline = baseline_df[
                (baseline_df[SITE_COL] == cell_id[0]) & 
                (baseline_df[CELL_COL] == cell_id[1])
            ][target_kpi]
            
            is_sig, p_val, t_stat = perform_ttest(cell_recent, cell_baseline)
            significance_results.append({
                "index": idx,
                "stat_significant": is_sig,
                "p_value": p_val,
                "t_statistic": t_stat
            })
        
        sig_df = pd.DataFrame(significance_results).set_index("index")
        comparison["stat_significant"] = sig_df["stat_significant"].reindex(comparison.index).fillna(False)
        comparison["p_value"] = sig_df["p_value"].reindex(comparison.index)
        comparison["t_statistic"] = sig_df["t_statistic"].reindex(comparison.index)
    
    comparison["kpi_status"] = np.where(
        comparison["kpi_degradation_ratio_%"] >= degradation_threshold,
        "Degraded",
        "Normal",
    )
    
    # If significance test enabled, require both threshold AND significance
    if enable_significance_test:
        comparison["kpi_status"] = np.where(
            (comparison["kpi_degradation_ratio_%"] >= degradation_threshold) & 
            (comparison["stat_significant"] == True),
            "Degraded",
            "Normal",
        )
    
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
        "recent_days_distribution": comparison["recent_days_count"].value_counts().sort_index().to_dict(),
        "baseline_days_distribution": comparison["baseline_days_count"].value_counts().sort_index().to_dict(),
        "max_degradation": comparison["kpi_degradation_ratio_%"].max() if not comparison.empty else None,
        "min_degradation": comparison["kpi_degradation_ratio_%"].min() if not comparison.empty else None,
        "mean_degradation": comparison["kpi_degradation_ratio_%"].mean() if not comparison.empty else None,
        "zero_baseline_excluded": zero_baseline_count,
        "min_baseline_excluded": excluded_by_min if min_baseline_value > 0 else 0,
    }
    
    metadata = {
        "last_date": last_date,
        "recent_start": recent_start,
        "recent_end": recent_end,
        "baseline_start": baseline_start,
        "baseline_end": baseline_end,
        "baseline_mode": baseline_mode,
        "available_related_features": [],
        "missing_related_features": [],
        "debug_info": debug_info,
    }
    
    if degraded_cells.empty:
        return degraded_cells, metadata
    
    # Smart related counter matching
    available_related_rules = []
    missing_related_features = []
    
    for rule in related_rules:
        matched_col = find_matching_column(df, rule["feature"])
        if matched_col is not None:
            new_rule = rule.copy()
            new_rule["feature"] = matched_col
            available_related_rules.append(new_rule)
        else:
            missing_related_features.append(rule["feature"])
    
    available_related_features = [rule["feature"] for rule in available_related_rules]
    metadata["available_related_features"] = available_related_features
    metadata["missing_related_features"] = missing_related_features
    
    if available_related_features:
        reason_cols = CELL_ID_COLS + [DATE_COL] + available_related_features
        df_reason = df[reason_cols].copy()
        df_reason[DATE_COL] = pd.to_datetime(df_reason[DATE_COL], errors="coerce").dt.normalize()
        
        for col in available_related_features:
            df_reason[col] = clean_numeric_series(df_reason[col])
        
        recent_reason_df = df_reason[(df_reason[DATE_COL] >= recent_start) & (df_reason[DATE_COL] <= recent_end)].copy()
        baseline_reason_df = df_reason[(df_reason[DATE_COL] >= baseline_start) & (df_reason[DATE_COL] <= baseline_end)].copy()
        
        # Aggregation for related counters
        agg_dict = {}
        for col in available_related_features:
            agg_dict[col] = ["mean", "max"]
        
        recent_reason_agg = recent_reason_df.groupby(CELL_ID_COLS).agg(agg_dict).reset_index()
        baseline_reason_agg = baseline_reason_df.groupby(CELL_ID_COLS).agg(agg_dict).reset_index()
        
        # Flatten column names
        new_cols = CELL_ID_COLS.copy()
        for col in available_related_features:
            new_cols.append(f"recent_{col}_mean")
            new_cols.append(f"recent_{col}_max")
        recent_reason_agg.columns = new_cols
        
        new_cols = CELL_ID_COLS.copy()
        for col in available_related_features:
            new_cols.append(f"baseline_{col}_mean")
            new_cols.append(f"baseline_{col}_max")
        baseline_reason_agg.columns = new_cols
        
        # Create aliases for compatibility with cause detection
        for col in available_related_features:
            recent_reason_agg[f"recent_{col}"] = recent_reason_agg[f"recent_{col}_mean"]
            baseline_reason_agg[f"baseline_{col}"] = baseline_reason_agg[f"baseline_{col}_mean"]
        
        degraded_with_causes = degraded_cells.merge(recent_reason_agg, on=CELL_ID_COLS, how="left")
        degraded_with_causes = degraded_with_causes.merge(baseline_reason_agg, on=CELL_ID_COLS, how="left")
        
        degraded_with_causes = degraded_with_causes.reset_index(drop=True)
        
        # Use vectorized cause detection with fallback
        try:
            cause_results = find_degradation_causes_vectorized(degraded_with_causes, available_related_rules)
            degraded_with_causes = pd.concat([degraded_with_causes.reset_index(drop=True), cause_results.reset_index(drop=True)], axis=1)
        except Exception as vec_error:
            log_msg(f"Vectorized cause detection failed, using fallback: {vec_error}")
            cause_results = degraded_with_causes.apply(
                lambda row: find_degradation_causes_row(row, available_related_rules),
                axis=1,
            )
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
    
    final_cols = CELL_ID_COLS + [
        "selected_kpi_name", "target_kpi_column", "kpi_category", "kpi_bad_direction",
        "selected_threshold_%", "recent_period", "baseline_period", "baseline_mode",
        "recent_avg_kpi", "baseline_avg_kpi", "recent_max_kpi", "baseline_max_kpi",
        "recent_total_kpi", "baseline_total_kpi", "recent_days_count", "baseline_days_count",
        "kpi_degradation_ratio_%", "kpi_status", "stat_significant", "p_value",
        "main_cause_counter_or_kpi", "main_cause_recent_value", "main_cause_baseline_value",
        "main_cause_change_%", "main_root_cause_category", "main_degradation_reason",
        "main_recommended_action", "number_of_detected_causes", "multi_cause_flag",
        "all_detected_causes", "all_cause_categories", "all_recommended_actions",
    ]
    
    available_final_cols = [col for col in final_cols if col in degraded_with_causes.columns]
    
    return degraded_with_causes[available_final_cols].copy(), metadata
