# ============================================================
# Verification test for the unit-aware negative-value filter.
# Run from inside lte_kpi_analyzer_v2:  python test_negative_filter.py
# Exit code 0 = all checks passed.
# ============================================================
import sys
import numpy as np
import pandas as pd

from KPI_Configuration import KPI_CONFIGS, allows_negative
from clean_excel_and_helpers import clean_numeric_series
import main_function_for_selected_kpi as mfsk  # must import cleanly after Edit B

DATE_COL, SITE_COL, CELL_COL = "Date", "eNodeB Name", "Cell Name"
passed, failed = [], []

def check(name, cond):
    (passed if cond else failed).append(name)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")

# ------------------------------------------------------------
# CHECK 1: no-op for every current target (existing reports unchanged)
# ------------------------------------------------------------
neg_targets = [c["target_kpi"] for c in KPI_CONFIGS.values()
               if allows_negative(c["target_kpi"])]
check("All current targets keep >=0 filtering (no behavior change)",
      neg_targets == [])
if neg_targets:
    print("    Unexpectedly negative-allowed targets:", neg_targets)

# ------------------------------------------------------------
# CHECK 2: a dBm/dB target IS recognized as negative-allowed
# ------------------------------------------------------------
check("dBm target recognized as negative-allowed",
      allows_negative("Cell Avg RSRP (dBm)") is True)
check("dB target recognized as negative-allowed",
      allows_negative("Serving RSRQ (dB)") is True)
check("Interference feature recognized",
      allows_negative("(HU) Avg UL Interference(dBm)") is True)

# ------------------------------------------------------------
# CHECK 3: reproduce the exact cleaning step (lines 98-100) OLD vs NEW
#          on a dBm target whose values are legitimately negative.
# ------------------------------------------------------------
RSRP = "Cell Avg RSRP (dBm)"
df = pd.DataFrame({
    SITE_COL: ["eNB1"] * 5,
    CELL_COL: ["Cell-A"] * 5,
    "LocalCell Id": [0] * 5,
    DATE_COL: pd.date_range("2024-01-01", periods=5, freq="D"),
    RSRP: [-85.0, -92.5, -105.0, -110.0, -78.0],   # all valid, all negative
})
df[RSRP] = clean_numeric_series(df[RSRP])
df = df.dropna(subset=[DATE_COL, RSRP])

# OLD logic (unconditional) -- what the code did before the fix
old_rows = df[df[RSRP] >= 0].copy().shape[0]

# NEW logic (uses the real allows_negative from the patched module)
new_df = df.copy()
if not allows_negative(RSRP):
    new_df = new_df[new_df[RSRP] >= 0]
new_rows = new_df.copy().shape[0]

print(f"    input rows={len(df)}  OLD-surviving={old_rows}  NEW-surviving={new_rows}")
check("OLD logic destroyed all negative dBm rows", old_rows == 0)
check("NEW logic preserved all negative dBm rows", new_rows == len(df))

# ------------------------------------------------------------
# CHECK 4: a true non-negative target still gets cleaned (glitch removed)
# ------------------------------------------------------------
TRAF = "(HU) DL Traffic Volume (GBytes)"
t = pd.Series([12.5, -3.0, 0.0, 4.2])
kept = t[t >= 0] if not allows_negative(TRAF) else t
check("Counter target still drops the impossible negative",
      list(kept) == [12.5, 0.0, 4.2])

# ------------------------------------------------------------
# CHECK 5: patched main module exposes the analysis entry point
# ------------------------------------------------------------
check("main_function_for_selected_kpi imports and exposes analyze_selected_kpi",
      hasattr(mfsk, "analyze_selected_kpi"))

print("\n" + "=" * 50)
print(f"RESULT: {len(passed)} passed, {len(failed)} failed")
if failed:
    print("FAILED:", failed)
    sys.exit(1)
print("ALL CHECKS PASSED")
sys.exit(0)
