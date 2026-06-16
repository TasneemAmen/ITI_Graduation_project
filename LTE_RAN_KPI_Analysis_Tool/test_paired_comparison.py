"""
test_paired_comparison.py
=========================

Verifies that the commit

    feat(stats): day-aligned paired comparison with scaled floors,
                 custom-mode fallback, and numeric audit columns

actually does what its message claims. Each test maps to a specific
promise in the commit body. Runs against the REAL analyze_selected_kpi.

Run:  pytest test_paired_comparison.py -v
"""
import numpy as np
import pandas as pd
import pytest

from main_function_for_selected_kpi import analyze_selected_kpi
from kpi_test_utils import build_frame, one_row, parse_daily_ratios, ANCHOR

DL = "DL Throughput"      # bad_direction = "low"  (a drop is bad)
DROP = "Drop Rate"        # bad_direction = "high" (an increase is bad)

# A large negative threshold makes every cell "Degraded" so we can read the
# raw degradation% off the output regardless of significance/threshold logic.
SHOW_ALL = -1e9


def run(df, kpi=DL, threshold=SHOW_ALL, **kw):
    kw.setdefault("baseline_mode", "last_week")
    kw.setdefault("enable_significance_test", False)
    kw.setdefault("require_complete_days", False)
    return analyze_selected_kpi(df, kpi, kw.pop("num_days", 7), threshold, **kw)


# ----------------------------------------------------------------------------
# 1. Core: degradation is the MEAN OF PER-DAY RATIOS, not (mean-mean)/mean
# ----------------------------------------------------------------------------
def test_paired_ratio_is_mean_of_daily_ratios():
    # 50 -> 40 on a "low-is-bad" KPI is a clean 20% degradation every day.
    df = build_frame([{"site": "S1", "recent": [40] * 7, "baseline": [50] * 7}], DL)
    r = one_row(run(df)[0])
    assert r["kpi_degradation_ratio_%"] == pytest.approx(20.0)
    assert r["paired_days_count"] == 7
    assert parse_daily_ratios(r["daily_ratios"]) == [20.0] * 7


def test_paired_differs_from_naive_under_seasonality():
    """The headline claim: day-alignment removes day-of-week bias.

    Baseline has strong weekday/weekend seasonality; the recent window is
    missing its (low) weekend days. The naive (avg-avg)/avg formula is fooled
    into reporting an *improvement*; the paired method reports the true ~20%
    weekday degradation.
    """
    rows = []
    for off in range(7):
        d = ANCHOR - pd.Timedelta(days=off)
        if d.weekday() < 5:                       # recent: weekdays only, 50->40
            rows.append({"off": off, "v": 40.0})
    recent = {x["off"]: x["v"] for x in rows}
    baseline_abs = {}
    for off in range(7):
        d = (ANCHOR - pd.Timedelta(days=7)) - pd.Timedelta(days=off)
        baseline_abs[d] = 50.0 if d.weekday() < 5 else 10.0
    df = build_frame([{"site": "S1", "recent": recent, "baseline_abs": baseline_abs}], DL)

    r = one_row(run(df)[0])
    naive = (r["baseline_avg_kpi"] - r["recent_avg_kpi"]) / r["baseline_avg_kpi"] * 100
    assert naive < 0                               # naive: looks like improvement
    assert r["kpi_degradation_ratio_%"] == pytest.approx(20.0, abs=1e-6)  # paired: correct


# ----------------------------------------------------------------------------
# 2. Missing recent days produce no pair (don't distort), and are counted
# ----------------------------------------------------------------------------
def test_missing_recent_days_simply_drop_out():
    # only 4 of 7 recent days present, all degraded 50->40 (=20%)
    df = build_frame([{"site": "S1", "recent": {0: 40, 1: 40, 2: 40, 3: 40},
                       "baseline": [50] * 7}], DL)
    r = one_row(run(df)[0])
    assert r["paired_days_count"] == 4
    assert r["kpi_degradation_ratio_%"] == pytest.approx(20.0)
    assert r["confidence_score_%"] == pytest.approx(round(4 / 7 * 100, 1))


# ----------------------------------------------------------------------------
# 3. Scaled floors (MIN_PAIRED_DAYS): small num_days must not exclude all cells
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("num_days", [1, 2])
def test_small_window_not_excluded_by_floor(num_days):
    recent = {i: 40 for i in range(num_days)}
    baseline = {i: 50 for i in range(num_days)}
    df = build_frame([{"site": "S1", "recent": recent, "baseline": baseline}], DL)
    out, meta = run(df, num_days=num_days)
    assert out.shape[0] == 1, "tiny recent window was wrongly excluded"
    assert one_row(out)["kpi_degradation_ratio_%"] == pytest.approx(20.0)


def test_floor_excludes_single_day_when_window_is_large():
    # num_days=7 -> needs ceil(7*0.5)=4 pairs; give only 1 -> excluded + logged.
    df = build_frame([{"site": "S1", "recent": {0: 40}, "baseline": [50] * 7}], DL)
    out, meta = run(df, num_days=7)
    assert out.shape[0] == 0
    inc = meta["incomplete_df"]
    assert (inc["reason"].str.contains("too few paired days")).any()


# ----------------------------------------------------------------------------
# 4. Custom-mode fallback: closest-weekday median when 7-day offset misses
# ----------------------------------------------------------------------------
def test_custom_mode_falls_back_to_weekday_median():
    recent = {off: 40.0 for off in range(7)}
    # custom baseline window sits ~30 days back, so r_date-7d never lands in it
    cb_end = ANCHOR - pd.Timedelta(days=30)
    cb_start = cb_end - pd.Timedelta(days=6)
    baseline_abs = {cb_start + pd.Timedelta(days=i): 50.0 for i in range(7)}
    df = build_frame([{"site": "S1", "recent": recent, "baseline_abs": baseline_abs}], DL)
    out, _ = run(df, baseline_mode="custom_range",
                 custom_baseline_start=cb_start, custom_baseline_end=cb_end)
    r = one_row(out)
    assert r["paired_days_count"] == 7              # fallback found a twin for each day
    assert r["kpi_degradation_ratio_%"] == pytest.approx(20.0)


# ----------------------------------------------------------------------------
# 5. 4-week mode pairs each recent day to the median of matching weekdays
# ----------------------------------------------------------------------------
def test_4week_mode_uses_weekday_median():
    recent = {off: 40.0 for off in range(7)}
    baseline = {off: 50.0 for off in range(28)}    # 4 full weeks at 50
    df = build_frame([{"site": "S1", "recent": recent, "baseline": baseline}], DL)
    out, _ = run(df, baseline_mode="4week_rolling_avg")
    r = one_row(out)
    assert r["kpi_degradation_ratio_%"] == pytest.approx(20.0)
    assert r["paired_days_count"] == 7


# ----------------------------------------------------------------------------
# 6. Numeric audit columns exist and are correct
# ----------------------------------------------------------------------------
def test_audit_columns_present_and_correct():
    # daily ratios: 10%, 20%, 30% -> mean 20, min 10, max 30
    df = build_frame([{"site": "S1",
                       "recent": {0: 45, 1: 40, 2: 35},
                       "baseline": {0: 50, 1: 50, 2: 50}}], DL)
    r = one_row(run(df, num_days=3)[0])
    for col in ["paired_days_count", "confidence_score_%",
                "min_pair_ratio_%", "max_pair_ratio_%", "daily_ratios"]:
        assert col in r.index, f"missing audit column {col}"
    assert r["min_pair_ratio_%"] == pytest.approx(10.0)
    assert r["max_pair_ratio_%"] == pytest.approx(30.0)
    assert r["kpi_degradation_ratio_%"] == pytest.approx(20.0)
    assert r["confidence_score_%"] == pytest.approx(100.0)


# ----------------------------------------------------------------------------
# 7. NaN handling: NaN recent values are skipped, not propagated
# ----------------------------------------------------------------------------
def test_nan_recent_values_are_skipped():
    df = build_frame([{"site": "S1",
                       "recent": {0: 40, 1: np.nan, 2: 40, 3: 40, 4: 40},
                       "baseline": [50] * 7}], DL)
    r = one_row(run(df, num_days=7)[0])
    # 4 valid recent days survive; NaN day contributes no pair
    assert r["paired_days_count"] == 4
    assert r["kpi_degradation_ratio_%"] == pytest.approx(20.0)


# ----------------------------------------------------------------------------
# 8. Transient vs consistent degradation
# ----------------------------------------------------------------------------
def test_transient_vs_consistent_pattern():
    # consistent: every day degraded; transient: one bad day among normals
    consistent = build_frame([{"site": "S1", "recent": [40] * 7, "baseline": [50] * 7}], DL)
    transient = build_frame([{"site": "S2",
                              "recent": {0: 25, 1: 50, 2: 50, 3: 50, 4: 50, 5: 50, 6: 50},
                              "baseline": [50] * 7}], DL)
    rc = one_row(run(consistent)[0])
    rt = one_row(run(transient)[0])
    assert rc["kpi_degradation_ratio_%"] > rt["kpi_degradation_ratio_%"]
    # The transient spike must be visible in the max audit column
    assert rt["max_pair_ratio_%"] == pytest.approx(50.0)
    assert rt["min_pair_ratio_%"] == pytest.approx(0.0)


# ----------------------------------------------------------------------------
# 9. bad_direction = "high" (Drop Rate): an INCREASE is the degradation
# ----------------------------------------------------------------------------
def test_bad_direction_high_drop_rate():
    # drop rate 1.0 -> 2.0 is a +100% degradation on a "high-is-bad" KPI
    df = build_frame([{"site": "S1", "recent": [2.0] * 7, "baseline": [1.0] * 7}], DROP)
    r = one_row(run(df, kpi=DROP)[0])
    assert r["kpi_degradation_ratio_%"] == pytest.approx(100.0)


# ----------------------------------------------------------------------------
# 10. Zero / undefined baseline is excluded and recorded
# ----------------------------------------------------------------------------
def test_zero_baseline_excluded_and_recorded():
    df = build_frame([{"site": "S1", "recent": [40] * 7, "baseline": [0.0] * 7}], DL)
    out, meta = run(df)
    assert out.shape[0] == 0
    assert (meta["incomplete_df"]["reason"].str.contains("zero baseline")).any()


# ----------------------------------------------------------------------------
# 11. Threshold + status wiring (no significance test)
# ----------------------------------------------------------------------------
def test_threshold_status_classification():
    df = build_frame([
        {"site": "BIG", "recent": [40] * 7, "baseline": [50] * 7},   # 20% -> Degraded @15
        {"site": "SMALL", "recent": [48] * 7, "baseline": [50] * 7}, # 4%  -> Normal  @15
    ], DL)
    out, _ = run(df, threshold=15.0)
    statuses = dict(zip(out["eNodeB Name"], out["kpi_status"]))
    # SMALL is Normal -> the degraded-only output keeps just BIG
    assert "BIG" in out["eNodeB Name"].values
    assert out[out["eNodeB Name"] == "BIG"]["kpi_status"].iloc[0] == "Degraded"
