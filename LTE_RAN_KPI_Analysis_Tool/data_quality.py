# ============================================================
# LTE KPI Degradation Analyzer - Data Quality
# ============================================================
# Three responsibilities:
#   1. validate_columns(): flag values that violate their unit criteria
#      (negative counters, % outside 0-100, positive dBm, vendor sentinels),
#      record them for the operator, and null them so they cannot poison the
#      averages.
#   2. compute_baseline_imputed(): for the BASELINE window only, fill a cell's
#      missing days with the median of the same weekday over the previous N
#      weeks. Recent window is never imputed (that could hide a real outage).
#   3. compute_baseline_fallback_from_history(): for cells with zero/NaN
#      baseline average, use median of same weekday from N weeks ago.
# Both return tidy frames so the pipeline stays auditable.
# ============================================================

import numpy as np
import pandas as pd

from KPI_Configuration import (
    SENTINEL_VALUES,
    IMPUTATION_CONFIG,
    classify_unit,
)


# ------------------------------------------------------------
# 1. Unit validation / quarantine
# ------------------------------------------------------------
def _invalid_mask_and_reason(values: pd.Series, unit: str):
    """Return (boolean invalid-mask, reason Series) for a numeric series."""
    v = pd.to_numeric(values, errors="coerce")
    reason = pd.Series(np.nan, index=v.index, dtype="object")

    sentinel = v.isin(list(SENTINEL_VALUES))
    reason[sentinel] = "vendor null/sentinel marker"

    if unit == "nonneg":
        bad = v < 0
        reason[bad & reason.isna()] = "negative value for non-negative metric"
    elif unit == "pct":
        low = v < 0
        high = v > 100
        reason[low & reason.isna()] = "percentage below 0"
        reason[high & reason.isna()] = "percentage above 100"
        bad = low | high
    elif unit == "dbm":
        bad = v > 0
        reason[bad & reason.isna()] = "positive dBm (received power should be <= 0)"
    else:  # 'db' -> cannot bound safely (SINR can be +/-), sentinels only
        bad = pd.Series(False, index=v.index)

    invalid = (sentinel | bad) & v.notna()
    return invalid, reason


def validate_columns(df, columns, kpi_name, cell_cols, date_col, log=None):
    """Null out invalid values and collect quarantine records.

    Returns (df_with_bad_values_nulled, quarantine_df).
    quarantine_df columns: cell_cols + [Date, kpi, counter, bad_value, reason].
    """
    df = df.copy()
    records = []
    for col in columns:
        if col not in df.columns:
            continue
        unit = classify_unit(col)
        invalid, reason = _invalid_mask_and_reason(df[col], unit)
        n_bad = int(invalid.sum())
        if n_bad:
            bad_rows = df.loc[invalid, cell_cols + [date_col]].copy()
            bad_rows["kpi"] = kpi_name
            bad_rows["counter"] = col
            bad_rows["bad_value"] = pd.to_numeric(df.loc[invalid, col], errors="coerce").values
            bad_rows["reason"] = reason[invalid].values
            records.append(bad_rows)
            df.loc[invalid, col] = np.nan  # null so it can't skew the mean
            if log:
                log(f"DQ: {n_bad} invalid value(s) quarantined in '{col}' ({unit})")
    if records:
        quarantine_df = pd.concat(records, ignore_index=True)
        quarantine_df = quarantine_df[cell_cols + [date_col, "kpi", "counter", "bad_value", "reason"]]
    else:
        quarantine_df = pd.DataFrame(
            columns=cell_cols + [date_col, "kpi", "counter", "bad_value", "reason"]
        )
    return df, quarantine_df


# ------------------------------------------------------------
# 2. Baseline gap imputation (same-weekday median over N weeks)
# ------------------------------------------------------------
def compute_baseline_imputed(
    daily_df,
    value_col,
    cell_cols,
    date_col,
    baseline_dates,
    lookback_weeks=None,
    min_samples=None,
):
    """Per-cell baseline aggregates with missing days filled by the median of
    the same weekday from the previous `lookback_weeks` weeks.

    `daily_df` must contain history BEFORE the baseline window (the lookback
    source). Returns a DataFrame indexed-reset on cell_cols with columns:
        baseline_avg, baseline_max, baseline_total,
        baseline_days_count, imputed_days_count
    """
    cfg = IMPUTATION_CONFIG
    lookback_weeks = cfg["lookback_weeks"] if lookback_weeks is None else lookback_weeks
    min_samples = cfg["min_impute_samples"] if min_samples is None else min_samples
    enable = cfg.get("enable_imputation", True)

    baseline_dates = sorted(pd.to_datetime(pd.Series(baseline_dates)).dt.normalize().unique())

    # cell x date matrix of values (mean collapses any duplicate cell/date)
    piv = daily_df.pivot_table(index=cell_cols, columns=date_col, values=value_col, aggfunc="mean")

    filled = pd.DataFrame(index=piv.index)   # baseline values after imputation
    imputed_flags = pd.DataFrame(index=piv.index)  # True where a day was imputed

    for d in baseline_dates:
        present = piv[d].copy() if d in piv.columns else pd.Series(np.nan, index=piv.index)
        imp_flag = pd.Series(False, index=piv.index)

        if enable:
            lookback_cols = [d - pd.Timedelta(days=7 * k) for k in range(1, lookback_weeks + 1)]
            lookback_cols = [c for c in lookback_cols if c in piv.columns]
            if lookback_cols:
                hist = piv[lookback_cols]
                med = hist.median(axis=1, skipna=True)
                cnt = hist.notna().sum(axis=1)
                need = present.isna() & (cnt >= min_samples)
                present = present.where(~need, med)
                imp_flag = need & present.notna()

        filled[d] = present
        imputed_flags[d] = imp_flag

    out = pd.DataFrame(index=piv.index)
    out["baseline_avg"] = filled.mean(axis=1, skipna=True)
    out["baseline_max"] = filled.max(axis=1, skipna=True)
    out["baseline_total"] = filled.sum(axis=1, skipna=True, min_count=1)
    out["baseline_days_count"] = filled.notna().sum(axis=1)
    out["imputed_days_count"] = imputed_flags.sum(axis=1)
    return out.reset_index()


# ------------------------------------------------------------
# 3. Baseline fallback from historical data (for zero/NaN baselines)
# ------------------------------------------------------------
def compute_baseline_fallback_from_history(
    df,
    target_kpi,
    cell_cols,
    date_col,
    baseline_start,
    baseline_end,
    lookback_weeks=5,
    min_samples=1,
):
    """
    Compute fallback baseline values for cells with zero/NaN baseline average.
    
    Uses the median of the same weekday from N weeks ago (default: 5 weeks).
    This provides a more accurate baseline than a static min_baseline_value.
    
    Edge cases handled:
    - If no data from exact week, tries previous weeks (cascading fallback)
    - If no historical data at all, returns NaN (caller should use min_baseline_value)
    - Uses median to be robust against outliers
    
    Args:
        df: Full DataFrame with all historical data
        target_kpi: Column name of the KPI
        cell_cols: List of columns identifying a cell
        date_col: Name of date column
        baseline_start: Start date of baseline period
        baseline_end: End date of baseline period
        lookback_weeks: How many weeks back to look (default 5)
        min_samples: Minimum samples needed for valid median (default 1)
        
    Returns:
        DataFrame with columns: cell_cols + ['baseline_fallback', 'fallback_weeks_back', 'fallback_samples']
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
    
    baseline_dates = pd.date_range(baseline_start, baseline_end, freq='D')
    
    # Collect all lookback dates (same weekdays from previous weeks)
    all_lookback_dates = []
    for d in baseline_dates:
        for week in range(1, lookback_weeks + 1):
            lookback_date = d - pd.Timedelta(days=7 * week)
            all_lookback_dates.append(lookback_date)
    
    all_lookback_dates = pd.to_datetime(all_lookback_dates).unique()
    
    # Filter to available dates in data
    df_hist = df[df[date_col].isin(all_lookback_dates)].copy()
    
    if df_hist.empty:
        # No historical data available
        result = pd.DataFrame(columns=cell_cols + ['baseline_fallback', 'fallback_weeks_back', 'fallback_samples'])
        return result
    
    # Get the target KPI values from historical data
    df_hist[target_kpi] = pd.to_numeric(df_hist[target_kpi], errors='coerce')
    
    # For each cell, calculate median of same-weekday values
    # Also track which weeks contributed and sample count
    result_list = []
    
    for cell_key, cell_df in df_hist.groupby(list(cell_cols)):
        values = cell_df[target_kpi].dropna()
        
        if len(values) >= min_samples:
            median_val = values.median()
            weeks_back = lookback_weeks  # How many weeks we looked back
            sample_count = len(values)
        else:
            median_val = np.nan
            weeks_back = 0
            sample_count = 0
        
        row = dict(zip(cell_cols, cell_key))
        row['baseline_fallback'] = median_val
        row['fallback_weeks_back'] = weeks_back
        row['fallback_samples'] = sample_count
        result_list.append(row)
    
    if result_list:
        result_df = pd.DataFrame(result_list)
    else:
        result_df = pd.DataFrame(columns=list(cell_cols) + ['baseline_fallback', 'fallback_weeks_back', 'fallback_samples'])
    
    return result_df


def apply_baseline_fallback(
    comparison_df,
    df_full,
    target_kpi,
    cell_cols,
    date_col,
    baseline_start,
    baseline_end,
    min_baseline_value,
    lookback_weeks=5,
    min_samples=1,
    log_callback=None,
):
    """
    Apply baseline fallback for cells with zero/NaN baseline average.
    
    This function:
    1. Identifies cells with zero/NaN baseline_avg_kpi
    2. Attempts to get fallback from historical data (same weekday, N weeks ago)
    3. If no historical data, uses min_baseline_value as last resort
    4. Flags cells where fallback was used for transparency
    
    Args:
        comparison_df: DataFrame with baseline_avg_kpi column
        df_full: Full DataFrame with all historical data
        target_kpi: Column name of the KPI
        cell_cols: List of columns identifying a cell
        date_col: Name of date column
        baseline_start: Start date of baseline period
        baseline_end: End date of baseline period
        min_baseline_value: Fallback value if no history available
        lookback_weeks: How many weeks back to look (default 5)
        min_samples: Minimum samples needed for valid median (default 1)
        log_callback: Optional logging function
        
    Returns:
        DataFrame with updated baseline_avg_kpi and new flag columns:
        - baseline_fallback_used: True if fallback was applied
        - baseline_fallback_source: 'history' or 'min_baseline_value'
        - baseline_fallback_value: The fallback value used
    """
    comparison_df = comparison_df.copy()
    
    # Initialize flag columns
    comparison_df['baseline_fallback_used'] = False
    comparison_df['baseline_fallback_source'] = None
    comparison_df['baseline_fallback_value'] = np.nan
    
    # Identify cells needing fallback (baseline is zero or NaN)
    needs_fallback = comparison_df['baseline_avg_kpi'].fillna(0) == 0
    
    if not needs_fallback.any():
        if log_callback:
            log_callback("No cells need baseline fallback")
        return comparison_df
    
    n_needs_fallback = needs_fallback.sum()
    if log_callback:
        log_callback(f"Attempting baseline fallback for {n_needs_fallback} cells with zero/NaN baseline")
    
    # Get fallback values from history
    fallback_df = compute_baseline_fallback_from_history(
        df_full, target_kpi, cell_cols, date_col,
        baseline_start, baseline_end, lookback_weeks, min_samples
    )
    
    if not fallback_df.empty:
        # Merge fallback values into comparison_df
        comparison_df = comparison_df.merge(
            fallback_df[list(cell_cols) + ['baseline_fallback', 'fallback_weeks_back', 'fallback_samples']],
            on=list(cell_cols), how='left'
        )
        
        # Apply historical fallback where available
        has_history = needs_fallback & comparison_df['baseline_fallback'].notna()
        comparison_df.loc[has_history, 'baseline_avg_kpi'] = comparison_df.loc[has_history, 'baseline_fallback']
        comparison_df.loc[has_history, 'baseline_fallback_used'] = True
        comparison_df.loc[has_history, 'baseline_fallback_source'] = 'history'
        comparison_df.loc[has_history, 'baseline_fallback_value'] = comparison_df.loc[has_history, 'baseline_fallback']
        
        n_from_history = has_history.sum()
        if log_callback:
            log_callback(f"  - {n_from_history} cells got fallback from historical data")
    
    # For cells still without baseline, use min_baseline_value
    still_zero = comparison_df['baseline_avg_kpi'].fillna(0) == 0
    n_from_min = still_zero.sum()
    
    if n_from_min > 0:
        comparison_df.loc[still_zero, 'baseline_avg_kpi'] = min_baseline_value
        comparison_df.loc[still_zero, 'baseline_fallback_used'] = True
        comparison_df.loc[still_zero, 'baseline_fallback_source'] = 'min_baseline_value'
        comparison_df.loc[still_zero, 'baseline_fallback_value'] = min_baseline_value
        
        if log_callback:
            log_callback(f"  - {n_from_min} cells using min_baseline_value ({min_baseline_value}) as fallback")
    
    # Clean up temporary columns
    cols_to_drop = ['baseline_fallback', 'fallback_weeks_back', 'fallback_samples']
    comparison_df = comparison_df.drop(columns=[c for c in cols_to_drop if c in comparison_df.columns], errors='ignore')
    
    return comparison_df
