# ============================================================
# LTE KPI Degradation Analyzer - Data Quality
# ============================================================
# Two responsibilities:
#   1. validate_columns(): flag values that violate their unit criteria
#      (negative counters, % outside 0-100, positive dBm, vendor sentinels),
#      record them for the operator, and null them so they cannot poison the
#      averages.
#   2. compute_baseline_imputed(): for the BASELINE window only, fill a cell's
#      missing days with the median of the same weekday over the previous N
#      weeks. Recent window is never imputed (that could hide a real outage).
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
