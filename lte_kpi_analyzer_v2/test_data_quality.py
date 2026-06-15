# ============================================================
# Verification test for the data-quality feature.
# Run from inside lte_kpi_analyzer_v2:  python test_data_quality.py
# Exit code 0 = all checks passed.
# ============================================================
import sys
import numpy as np
import pandas as pd

from data_quality import validate_columns, compute_baseline_imputed
from main_function_for_selected_kpi import analyze_selected_kpi
from combined_degraded_kpi import analyze_all_kpis

SITE, CELL, LC, DATE = "eNodeB Name", "Cell Name", "LocalCell Id", "Date"
CC = [SITE, CELL, LC]
TGT = "(HU) DL Traffic Volume (GBytes)"
THR = "(HU) User DL Average Throughput (Mbps)"
PRB = "(HU) DL PRB Utilization(%)"
CQI = "DL Average CQI"
passed = failed = 0

def check(name, cond):
    global passed, failed
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    if cond: passed += 1
    else: failed += 1

# ---- 1. unit validation ----
v = pd.DataFrame({SITE:["e"]*3, CELL:["c"]*3, LC:[0]*3,
                  DATE:pd.date_range("2024-02-25",periods=3),
                  TGT:[10.0,-2.0,4294967295], PRB:[99.0,150.0,50.0]})
clean,q = validate_columns(v,[TGT,PRB],"DL Traffic",CC,DATE)
check("negative counter quarantined", "negative value for non-negative metric" in set(q["reason"]))
check("sentinel quarantined", (q["bad_value"]==4294967295).any())
check("percentage>100 quarantined", "percentage above 100" in set(q["reason"]))
check("bad values nulled in returned frame", pd.isna(clean[TGT].iloc[1]) and pd.isna(clean[PRB].iloc[1]))

# ---- 2. weekday-median baseline imputation ----
mondays = pd.to_datetime(["2024-01-08","2024-01-15","2024-01-22","2024-01-29","2024-02-05"])
rows = [("e","A",0,d,100.0) for d in mondays]
rows += [("e","B",0,d,50.0) for d in mondays if d != pd.Timestamp("2024-02-05")]
daily = pd.DataFrame(rows, columns=CC+[DATE,"val"])
res = compute_baseline_imputed(daily,"val",CC,DATE,[pd.Timestamp("2024-02-05")])
b = res[res[CELL]=="B"].iloc[0]
check("missing baseline day imputed from 4-week median", b["baseline_avg"]==50.0)
check("imputed day counted", int(b["imputed_days_count"])==1)

# ---- 3. end-to-end: degraded + quarantine + incomplete ----
np.random.seed(0)
dates = pd.date_range(end="2024-03-31", periods=40, freq="D")
recent = pd.to_datetime(["2024-03-29","2024-03-30","2024-03-31"])
rows = []
def add(c,d,t,th,p,cq): rows.append(("eNB1",c,0,d,t,th,p,cq))
for d in dates:
    r = d in recent
    add("Cell-A",d,np.random.normal(45 if r else 100,2),np.random.normal(8 if r else 25,1),
        np.random.normal(80 if r else 50,2),np.random.normal(7 if r else 11,.3))
    if d != pd.Timestamp("2024-03-23"):  # B missing one baseline Saturday -> imputed
        add("Cell-B",d,np.random.normal(48 if r else 100,2),np.random.normal(9 if r else 24,1),
            np.random.normal(78 if r else 52,2),np.random.normal(7 if r else 11,.3))
    if d != pd.Timestamp("2024-03-30"):  # C missing a recent day -> incomplete
        add("Cell-C",d,np.random.normal(100,2),np.random.normal(25,1),
            np.random.normal(50,2),np.random.normal(11,.3))
df = pd.DataFrame(rows, columns=CC+[DATE,TGT,THR,PRB,CQI])
df.loc[(df[CELL]=="Cell-A")&(df[DATE]==pd.Timestamp("2024-03-31")),PRB]=150.0

out,meta = analyze_selected_kpi(df,"DL Traffic",num_days=3,degradation_threshold=30.0,
    require_complete_days=True,baseline_mode="last_week",enable_significance_test=True,
    log_callback=lambda m: None)
deg = set(out[CELL])
check("A and B degraded, C excluded", deg=={"Cell-A","Cell-B"})
check("Cell-B shows imputed baseline day", int(out.loc[out[CELL]=="Cell-B","baseline_imputed_days"].iloc[0])>=1)
check("invalid PRB recorded in quarantine_df", (meta["quarantine_df"]["bad_value"]==150).any())
check("Cell-C recorded in incomplete_df", "Cell-C" in set(meta["incomplete_df"][CELL]))

# ---- 4. combined mode returns the new arity ----
check("analyze_all_kpis returns 5 items",
      len(analyze_all_kpis(df,num_days=3,require_complete_days=True,baseline_mode="last_week",
                           enable_significance_test=True,log_callback=lambda m: None))==5)

print("\n" + "="*50)
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
