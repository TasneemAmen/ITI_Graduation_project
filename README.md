# Data-Driven & Automation-Based RF Optimization for Modern 4G/5G Mobile Networks

> **LTE KPI Degradation Analyzer v2.0**  
> **Graduation Project — Information Technology Institute (ITI) 2026**  
> **Team: Musketeers_Team**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Core Concepts & Methodology](#3-core-concepts--methodology)
4. [Project Structure](#4-project-structure)
5. [Installation & Dependencies](#5-installation--dependencies)
6. [Configuration Guide](#6-configuration-guide)
7. [Usage Guide](#7-usage-guide)
8. [Data Quality Framework](#8-data-quality-framework)
9. [KPI Configuration Reference](#9-kpi-configuration-reference)
10. [Root Cause Analysis Engine](#10-root-cause-analysis-engine)
11. [Visualization & Reporting](#11-visualization--reporting)
12. [Testing & Validation](#12-testing--validation)
13. [Extending the System](#13-extending-the-system)
14. [Troubleshooting](#14-troubleshooting)
15. [License & Attribution](#15-license--attribution)

---

## 1. Project Overview

### 1.1 Mission Statement

This project addresses the critical challenge of **Radio Frequency (RF) optimization** in modern 4G LTE and 5G NR mobile networks through an **automated, data-driven analytical framework**. Traditional RF optimization relies heavily on manual counter inspection, engineer expertise, and reactive troubleshooting. Our system transforms this paradigm by:

- **Automating** the detection of KPI degradation across the entire network
- **Intelligently correlating** degraded KPIs with related network counters
- **Pinpointing root causes** with severity-weighted scoring
- **Generating actionable recommendations** for RF engineers
- **Providing statistical confidence** via Welch's t-test significance testing

### 1.2 Problem Domain

Modern cellular networks generate massive volumes of performance data:
- **Traffic volumes** (DL/UL GBytes)
- **Throughput metrics** (Mbps per cell/user)
- **Accessibility KPIs** (RRC/ERAB Setup Success Rates)
- **Retainability KPIs** (Drop Rates, Abnormal Releases)
- **Mobility KPIs** (Handover Success Rates)
- **Quality metrics** (CQI, BLER, MCS, Interference)
- **Coverage indicators** (TA Distribution, CEU metrics)
- **Carrier Aggregation** (CA activation, SCell metrics)

**The Challenge:** When a KPI degrades, engineers must manually inspect dozens of related counters, compare against baselines, and determine the root cause — a process that is time-consuming, error-prone, and unscalable for large networks.

### 1.3 Solution Approach

Our analyzer implements a **three-layer analytical pipeline**:

```
+-------------------------------------------------------------+
|  LAYER 1: DATA INGESTION & QUALITY ASSURANCE                |
|  +-- Excel/CSV import with smart column matching            |
|  +-- Unit-aware validation (negative counters, % bounds)    |
|  +-- Sentinel value detection (vendor null markers)         |
|  +-- Baseline gap imputation (same-weekday median)          |
+-------------------------------------------------------------+
|  LAYER 2: DEGRADATION DETECTION & STATISTICAL VALIDATION    |
|  +-- Configurable baseline windows (last week / 4-week avg) |
|  +-- Degradation ratio calculation with direction awareness |
|  +-- Welch's t-test for statistical significance            |
|  +-- Minimum baseline value filtering                       |
+-------------------------------------------------------------+
|  LAYER 3: ROOT CAUSE ANALYSIS & RECOMMENDATION ENGINE       |
|  +-- Severity-weighted cause scoring (1-5 scale)            |
|  +-- Multi-cause detection with ranking                     |
|  +-- Category-based classification (Radio, Capacity, etc.)  |
|  +-- Actionable RF optimization recommendations             |
+-------------------------------------------------------------+
```

### 1.4 Key Features (v2.0 Enhanced)

| Feature | Description |
|---------|-------------|
| **13 KPI Categories** | Traffic, Integrity, Accessibility, Retainability, Mobility, Availability, CSFB, VoLTE, RRC Re-establishment |
| **142 Detection Rules** | Correlated counter analysis with configurable thresholds |
| **3 Baseline Modes** | Last-week parallel, 4-week rolling average, custom date range |
| **Statistical Significance** | Welch's t-test with p-value reporting |
| **Data Quality Engine** | Unit validation, sentinel detection, baseline imputation |
| **Coverage Analysis** | TA Distribution bins (0-156m to 6.6-14km) |
| **Cell Edge Analysis** | CEU throughput and border UE metrics |
| **Carrier Aggregation** | SCell activation, 3CC CA, FDD-TDD CA tracking |
| **MIMO/Rank Analysis** | Rank 2 reporting, CQI codeword tracking |
| **Interactive Dashboard** | Tkinter GUI with real-time charts |
| **Word Report Generation** | Automated DOCX export with formatted tables |
| **Batch CSV Export** | Per-KPI and combined output files |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
                    +---------------------+
                    |   User Interface    |
                    |   (Tkinter GUI)     |
                    +----------+----------+
                               |
                    +----------v----------+
                    |  Analysis Engine    |
                    |  (Core Pipeline)    |
                    +----------+----------+
                               |
        +----------------------+----------------------+
        |                      |                      |
+-------v--------+    +--------v---------+    +------v-------+
|  Data Quality  |    |  Degradation     |    |   Cause      |
|  Validator     |    |  & Baseline Eng. |    |  Detection   |
+-------+--------+    +--------+---------+    +------+-------+
        |                      |                    |
        +----------------------+----------------------+
                               |
                    +----------v----------+
                    |  Output Generators  |
                    |  (CSV / Word / Viz) |
                    +---------------------+
```

### 2.2 Module Interaction Diagram

```
main.py
  |
  +---> initialization.py  ---> LTEKPIAnalyzerApp (GUI Controller)
  |       |
  |       +---> main_function_for_selected_kpi.py
  |       |       +---> KPI_Configuration.py      (Rules & Thresholds)
  |       |       +---> clean_excel_and_helpers.py (Data Cleaning)
  |       |       +---> data_quality.py            (Validation & Imputation)
  |       |       +---> cause_detect_functions.py    (Root Cause Engine)
  |       |
  |       +---> combined_degraded_kpi.py           (Multi-KPI Orchestrator)
  |       +---> Visualization_Functions.py         (Charts & Dashboards)
  |       +---> Generate_Word_Report.py            (DOCX Export)
  |       +---> Save_Results.py                    (CSV Export)
  |       +---> Loading_file_inputs_outputs.py     (File I/O)
  |
  +---> test_data_quality.py    (Integration Tests)
  +---> test_negative_filter.py  (Unit Tests)
```

### 2.3 Data Flow

```
Raw Excel Data
      |
      v
+-----------------+
| Column Cleaning |  <- clean_excel_columns()
| (spaces, breaks)|
+--------+--------+
         |
         v
+-----------------+
| Smart Matching  |  <- find_matching_column()
| (fuzzy names)   |
+--------+--------+
         |
         v
+-----------------+
| Data Quality    |  <- validate_columns()
| Validation      |     compute_baseline_imputed()
+--------+--------+
         |
         v
+-----------------+
| Period Splitting|  <- get_periods_enhanced()
| (Recent vs Baseline)
+--------+--------+
         |
         v
+-----------------+
| Aggregation     |  <- groupby().agg()
| (mean/max/sum)  |
+--------+--------+
         |
         v
+-----------------+
| Degradation     |  <- calculate_degradation()
| Calculation     |
+--------+--------+
         |
         v
+-----------------+
| Significance    |  <- perform_ttest()
| Testing         |
+--------+--------+
         |
         v
+-----------------+
| Cause Detection |  <- find_degradation_causes_vectorized()
| & Scoring       |
+--------+--------+
         |
         v
+-----------------+
| Output Gen.     |  <- CSV / Word / Dashboard
+-----------------+
```

---

## 3. Core Concepts & Methodology

### 3.1 Degradation Detection Formula

For a given KPI with **bad direction** defined:

**If bad_direction = "low"** (degradation when value decreases):
```
Degradation % = ((baseline_value - recent_value) / baseline_value) x 100
```

**If bad_direction = "high"** (degradation when value increases):
```
Degradation % = ((recent_value - baseline_value) / baseline_value) x 100
```

A cell is flagged as **degraded** when:
```
Degradation % >= Threshold AND (statistical_significance = True OR disabled)
```

### 3.2 Baseline Window Strategies

| Mode | Description | Use Case |
|------|-------------|----------|
| **Last Week** | Same N days from previous week | Detecting sudden incidents |
| **4-Week Rolling** | Average of same weekdays over 4 weeks | Smoothing weekly patterns |
| **Custom Range** | User-defined start/end dates | Special event analysis |

### 3.3 Statistical Significance Testing

**Welch's t-test** (unequal variance) is performed between recent and baseline value distributions:

```python
t_stat, p_value = scipy.stats.ttest_ind(
    recent_values, baseline_values, equal_var=False
)
```

- **Significant** if `p_value < 0.05`
- Prevents false positives from high-variability cells
- Can be disabled for faster processing

### 3.4 Severity-Weighted Cause Scoring

Each detected cause receives a **score** for ranking:

```
Score = Degradation_Percentage x Severity_Level
```

| Severity | Level | Examples |
|----------|-------|----------|
| 1 | Low | Traffic demand variations |
| 2 | Medium | Capacity indicators, CA issues |
| 3 | High | Throughput degradation, interference |
| 4 | Critical | Radio failures, MME issues |
| 5 | Emergency | Availability loss, abnormal releases |

The cause with the **highest score** is reported as the main root cause.

### 3.5 Data Quality Framework

#### 3.5.1 Unit-Aware Validation

Columns are classified by physical unit:

| Unit Type | Valid Range | Example Columns |
|-----------|-------------|-----------------|
| `nonneg` | >= 0 | Traffic volumes, counters, throughput |
| `pct` | [0, 100] | Success rates, utilization percentages |
| `dbm` | <= 0 | RSRP, interference (received power) |
| `db` | Any | SINR, RSRQ (can be positive or negative) |

#### 3.5.2 Sentinel Value Detection

Vendor-specific "no data" markers are identified and nullified:
- `4294967295` (0xFFFFFFFF — unsigned int max)
- `4294967294` (0xFFFFFFFE)

#### 3.5.3 Baseline Imputation

For missing baseline days, the system imputes using:
```
imputed_value = median(same_weekday_values_over_last_N_weeks)
```

**Constraints:**
- Minimum 2 historical samples required
- Recent window is NEVER imputed (preserves real outage detection)
- Imputation count is tracked in output (`baseline_imputed_days`)

---

## 4. Project Structure

```
lte_kpi_analyzer_v2/
|
+-- main.py                              # Application entry point
+-- initialization.py                    # Tkinter GUI & app controller
|
+-- KPI_Configuration.py                 # KPI definitions, rules, thresholds
|   +-- 13 KPI configurations
|   +-- 142 related detection rules
|   +-- Unit classification & validation
|
+-- main_function_for_selected_kpi.py    # Core analysis pipeline
|   +-- Data loading & cleaning
|   +-- Period splitting & aggregation
|   +-- Degradation calculation
|   +-- Significance testing
|   +-- Cause detection integration
|
+-- combined_degraded_kpi.py             # Multi-KPI batch analysis
|
+-- cause_detect_functions.py            # Root cause analysis engine
|   +-- Vectorized cause detection
|   +-- Row-by-row fallback
|
+-- data_quality.py                      # Data validation & imputation
|   +-- validate_columns()
|   +-- compute_baseline_imputed()
|
+-- clean_excel_and_helpers.py           # Data cleaning utilities
|   +-- Column name normalization
|   +-- Smart column matching
|   +-- Numeric cleaning
|   +-- Degradation calculation
|
+-- Visualization_Functions.py           # Charts & dashboards
|   +-- show_dashboard()
|   +-- show_trend_dashboard()
|
+-- Generate_Word_Report.py              # DOCX report generation
|
+-- Save_Results.py                      # CSV export functionality
|
+-- Loading_file_inputs_outputs.py       # File I/O dialogs
|
+-- test_data_quality.py                 # Integration tests
+-- test_negative_filter.py              # Unit tests
|
+-- requirements.txt                     # Python dependencies
+-- KPI_and_its_related_counters.md      # Complete KPI reference
```

---

## 5. Installation & Dependencies

### 5.1 System Requirements

- **Python:** 3.8 or higher
- **OS:** Windows 10/11, Linux, macOS
- **RAM:** 4GB minimum (8GB recommended for large datasets)
- **Display:** 1366x768 minimum resolution for GUI

### 5.2 Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/lte-kpi-analyzer.git
cd lte-kpi-analyzer

# 2. Create virtual environment (recommended)
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python test_data_quality.py
python test_negative_filter.py
```

### 5.3 Dependency Reference

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | >=1.20.0 | Numerical operations, array handling |
| `pandas` | >=1.3.0 | DataFrame manipulation, Excel I/O |
| `scipy` | >=1.7.0 | Statistical testing (Welch's t-test) |
| `matplotlib` | >=3.4.0 | Chart visualization |
| `python-docx` | >=0.8.11 | Word document generation (optional) |
| `openpyxl` | >=3.0.0 | Excel .xlsx file reading |
| `xlrd` | >=2.0.0 | Excel .xls file reading |

---

## 6. Configuration Guide

### 6.1 KPI Configuration (KPI_Configuration.py)

Each KPI follows this structure:

```python
"KPI Name": {
    "target_kpi": "(HU) DL Traffic Volume (GBytes)",  # Exact or fuzzy column name
    "bad_direction": "low",                           # "low" or "high"
    "default_threshold": 30.0,                        # Degradation trigger %
    "category": "Traffic",                            # Classification
    "output_prefix": "dl_traffic",                    # File naming
    "min_baseline_value": 1.0,                        # Minimum baseline filter
    "related_rules": [
        {
            "feature": "(HU) Cell DL Average Throughput (Mbps)",
            "bad_direction": "low",
            "threshold": 20,                          # Rule-specific threshold
            "severity": 3,                            # 1-5 severity scale
            "category": "DL Throughput Degradation",
            "reason": "Cell DL throughput decreased.",
            "recommended_action": "Check DL scheduler, bandwidth..."
        },
        # ... more rules
    ]
}
```

### 6.2 Adding a New KPI

```python
# 1. Add to KPI_CONFIGS dictionary
"My New KPI": {
    "target_kpi": "My Counter Name",
    "bad_direction": "low",
    "default_threshold": 10.0,
    "category": "Custom",
    "output_prefix": "my_kpi",
    "min_baseline_value": 0.0,
    "related_rules": [
        {
            "feature": "Related Counter 1",
            "bad_direction": "high",
            "threshold": 20,
            "severity": 3,
            "category": "Custom Category",
            "reason": "Description of why this indicates degradation",
            "recommended_action": "What the engineer should check"
        }
    ]
}

# 2. Run validation (automatic on import)
# validate_kpi_configs() is called at module load

# 3. Restart the application
```

### 6.3 Imputation Configuration

```python
# In KPI_Configuration.py
IMPUTATION_CONFIG = {
    "enable_imputation": True,      # Master switch
    "lookback_weeks": 4,            # Historical weeks for median
    "min_impute_samples": 2,        # Minimum samples to impute
}
```

### 6.4 Sentinel Values

```python
# In KPI_Configuration.py
SENTINEL_VALUES = (4294967295, 4294967294)  # Add vendor-specific markers
```

---

## 7. Usage Guide

### 7.1 Starting the Application

```bash
python main.py
```

### 7.2 GUI Overview

```
+-----------------------------------------------------------------------------+
| LTE KPI Degradation Analyzer v2.0 -- Developed by Musketeers_Team          |
+-----------------------------------------------------------------------------+
| [Browse] C:\data\kpi_export.xlsx  [Sheet: v Sheet1]                        |
+-----------------------------------------------------------------------------+
| KPI: [v DL Traffic        ]  Days: [4 ^]  Threshold: [30.0  ]            |
| Baseline Mode: (*) Last Week  ( ) 4-Week Avg  ( ) Custom Range             |
| [x] Require complete days    [x] Enable t-test significance filter         |
|                                                                              |
| [Run Selected KPI] [Analyze All KPIs] [Generate Report] [Save CSV]         |
| [Show Dashboard] [Trend Dashboard]                                         |
+-----------------------------------------------------------------------------+
| Results Preview                                                              |
| +-----------------+-----------------+----------------------+----------------+|
| | eNodeB Name     | Cell Name       | kpi_degradation_%    | main_cause... ||
| +-----------------+-----------------+----------------------+----------------+|
| | eNB001          | Cell-A          | 45.23                | Radio Quality  ||
| | eNB001          | Cell-B          | 38.91                | Capacity Issue ||
| +-----------------+-----------------+----------------------+----------------+|
+-----------------------------------------------------------------------------+
| Log                                                                          |
| [10%] Loading Excel sheet: Sheet1...                                         |
| [35%] Analyzing KPI: DL Traffic...                                           |
| [100%] Analysis completed.                                                   |
+-----------------------------------------------------------------------------+
```

### 7.3 Analysis Workflow

1. **Select File:** Click "Browse" and choose your Excel file
2. **Select Sheet:** Choose the appropriate sheet from the dropdown
3. **Configure Analysis:**
   - Select KPI from dropdown
   - Set comparison days (1-14)
   - Adjust threshold if needed
   - Choose baseline mode
4. **Run Analysis:** Click "Run Selected KPI" or "Analyze All KPIs"
5. **Review Results:** Examine degraded cells in the preview table
6. **Visualize:** Click "Show Dashboard" for charts
7. **Export:** Save as CSV or generate Word report

### 7.4 Output Columns Reference

| Column | Description |
|--------|-------------|
| `eNodeB Name` / `Cell Name` / `LocalCell Id` | Cell identifiers |
| `selected_kpi_name` | Name of analyzed KPI |
| `target_kpi_column` | Actual matched column name |
| `kpi_category` | KPI classification |
| `kpi_bad_direction` | "low" or "high" |
| `selected_threshold_%` | Applied degradation threshold |
| `recent_period` / `baseline_period` | Analysis date ranges |
| `recent_avg_kpi` / `baseline_avg_kpi` | Aggregated values |
| `recent_days_count` / `baseline_days_count` | Data completeness |
| `baseline_imputed_days` | Days imputed in baseline |
| `kpi_degradation_ratio_%` | Calculated degradation |
| `kpi_status` | "Degraded" or "Normal" |
| `stat_significant` | True if p < 0.05 |
| `p_value` / `t_statistic` | Test statistics |
| `main_cause_counter_or_kpi` | Top-ranked root cause |
| `main_root_cause_category` | Cause classification |
| `main_degradation_reason` | Human-readable explanation |
| `main_recommended_action` | Engineering action item |
| `number_of_detected_causes` | Total causes found |
| `multi_cause_flag` | "Yes" if multiple causes |
| `all_detected_causes` | Top 5 causes with values |
| `all_cause_categories` | Categories of top 5 causes |
| `all_recommended_actions` | Actions for top 5 causes |

---

## 8. Data Quality Framework

### 8.1 Validation Pipeline

```
Input Data
    |
    +---> Column Name Matching (fuzzy)
    |
    +---> Unit Classification
    |       +-- nonneg -> check < 0
    |       +-- pct -> check < 0 or > 100
    |       +-- dbm -> check > 0
    |       +-- db -> sentinel only
    |
    +---> Sentinel Detection (4294967295, 4294967294)
    |
    +---> Invalid Value Nullification
    |
    +---> Quarantine Recording
```

### 8.2 Quarantine Output

Invalid values are saved to `data_quality_quarantine.csv`:

| Column | Description |
|--------|-------------|
| `eNodeB Name` / `Cell Name` / `LocalCell Id` | Cell identifiers |
| `Date` | Timestamp of invalid value |
| `kpi` | KPI being analyzed |
| `counter` | Column with invalid value |
| `bad_value` | The invalid raw value |
| `reason` | Why it was quarantined |

### 8.3 Incomplete Cell Tracking

Cells with insufficient data are saved to `data_quality_incomplete_cells.csv`:

| Column | Description |
|--------|-------------|
| `recent_days_count` / `baseline_days_count` | Actual available days |
| `expected_recent_days` / `expected_baseline_days` | Required days |
| `reason` | Why excluded (no baseline, no recent, incomplete, zero baseline) |

---

## 9. KPI Configuration Reference

### 9.1 Complete KPI Listing

| # | KPI Name | Target Column | Direction | Threshold | Category | Rules |
|---|----------|---------------|-----------|-----------|----------|-------|
| 1 | DL Traffic | `(HU) DL Traffic Volume (GBytes)` | low | 30% | Traffic | 24 |
| 2 | UL Traffic | `(HU) UL Traffic Volume (GBytes)` | low | 30% | Traffic | 13 |
| 3 | DL Throughput | `(HU) User DL Average Throughput (Mbps)` | low | 20% | Integrity | 14 |
| 4 | UL Throughput | `(HU) User UL Average Throughput (Mbps)` | low | 20% | Integrity | 8 |
| 5 | RRC Setup SR | `(TE) RRC Setup SR%` | low | 5% | Accessibility | 8 |
| 6 | ERAB Setup SR | `ERAB Setup Success Rate` | low | 5% | Accessibility | 6 |
| 7 | Drop Rate | `E-RAB Drop Rate (E-NodeB + MME) %` | high | 20% | Retainability | 15 |
| 8 | HO Success Rate | `HO SR% Overall` | low | 5% | Mobility | 14 |
| 9 | Availability | `Availability` | low | 1% | Availability | 4 |
| 10 | RACH Success Rate | `(HU) RACH Success Rate(%)` | low | 5% | Accessibility | 5 |
| 11 | CSFB KPI | `CSFB SR%` | low | 5% | CSFB / Voice | 9 |
| 12 | VoLTE KPIs | `BA_Voice E2E VQI` | low | 5% | VoLTE | 14 |
| 13 | RRC Re-establishment | `RRC Reestablish Setup Success Rate(%)` | low | 10% | Mobility | 8 |

### 9.2 Feature Categories

| Category | Description | Example Features |
|----------|-------------|------------------|
| Radio Quality | Signal quality issues | CQI, IBLER, RBLER |
| Throughput | Cell/user throughput | DL/UL throughput metrics |
| Capacity | Resource utilization | PRB utilization, CCE failures |
| Interference | Uplink/downlink noise | UL interference, UpPTS |
| Availability | Cell/site outages | Unavailable time, S1 failures |
| Carrier Aggregation | CA performance | SCell activation, CA traffic |
| Coverage | Distance/cell edge | TA distribution, CEU metrics |
| MIMO | Spatial multiplexing | Rank 2, CQI codewords |
| Accessibility | Access failures | RRC/ERAB setup failures |
| Retainability | Drop issues | Abnormal releases |
| Mobility | Handover problems | HO preparation/execution |
| RACH | Random access | Contention failures |
| CSFB | Circuit switch fallback | Redirection, flash CSFB |
| VoLTE | Voice over LTE | VoIP ERAB, QCI-1/7 |
| SRVCC | Voice continuity | SRVCC HO success |
| Transport | Backhaul issues | TNL failures |
| Core | MME problems | MME overload, failures |

---

## 10. Root Cause Analysis Engine

### 10.1 Vectorized Detection Algorithm

```python
def find_degradation_causes_vectorized(df, rules):
    # 1. Reset index for alignment
    df_work = df.reset_index(drop=True).copy()

    # 2. For each rule, vectorized numpy operations
    for rule in rules:
        # Calculate change percentage for ALL cells at once
        change_pct = np.where(
            baseline_values != 0,
            ((recent - baseline) / baseline) * 100,
            np.nan
        )

        # Vectorized threshold mask
        mask = change_pct >= threshold

        # Severity-weighted scoring
        score = change_pct * severity

    # 3. Aggregate per cell, sort by score
    # 4. Return top cause + top 5 all causes
```

### 10.2 Cause Ranking Example

For a cell with DL Traffic degradation:

| Rank | Feature | Change % | Severity | Score | Category |
|------|---------|----------|----------|-------|----------|
| 1 | `Availability` | -2.5% | 5 | **12.5** | Availability Issue |
| 2 | `DL RBLER` | +35% | 4 | **140.0** | DL Radio Failure |
| 3 | `DL Average CQI` | -18% | 3 | **54.0** | Radio Quality Issue |

**Main Cause:** `Availability` (highest severity-weighted score despite smaller percentage change)

**Rationale:** A 2.5% availability drop (severity 5) is more critical than a 35% RBLER increase (severity 4) because availability impacts all users and indicates a site-level problem.

### 10.3 Multi-Cause Detection

When multiple causes are detected (`multi_cause_flag = "Yes"`), the system reports:
- **Main cause:** Highest scored single issue
- **All causes:** Top 5 causes with recent/baseline values and change percentages
- **All categories:** Classification of each cause
- **All actions:** Recommended actions for each cause

---

## 11. Visualization & Reporting

### 11.1 Dashboard Features

**Degradation Dashboard:**
- Summary metrics (total KPIs, degraded cells)
- Bar chart: Degraded cells per KPI
- Horizontal bar chart: Root cause distribution
- Interactive Tkinter window

**Trend Dashboard:**
- Before/after degraded cell removal comparison
- Time-series line chart
- Fill-between highlighting degraded impact
- KPI selector dropdown

### 11.2 Word Report Structure

```
RF Optimization Analysis Report
+-- Analysis Summary
|   +-- Mode (Single/All KPIs)
|   +-- Baseline configuration
|   +-- Significance test status
|   +-- Degraded cell counts
+-- Degraded Cells Details (top 30)
|   +-- eNodeB Name, Cell Name
|   +-- Degradation ratio
|   +-- Root cause category
|   +-- Recommended action
|   +-- Statistical significance
+-- KPI Summary Table (All KPIs mode)
    +-- KPI name
    +-- Degraded cells count
    +-- Max/mean degradation
    +-- Status
```

### 11.3 CSV Export Structure

**Single KPI mode:**
- `{prefix}_degraded.csv` -- Main output
- `{prefix}_counter_quarantine.csv` -- Invalid values
- `{prefix}_incomplete_cells.csv` -- Excluded cells

**All KPIs mode:**
- `{prefix}_degraded.csv` -- Per-KPI output (13 files)
- `all_kpis_combined.csv` -- Unified degraded cells
- `summary_report.csv` -- KPI statistics
- `data_quality_quarantine.csv` -- All invalid values
- `data_quality_incomplete_cells.csv` -- All incomplete cells

---

## 12. Testing & Validation

### 12.1 Test Suite

| Test File | Purpose | Coverage |
|-----------|---------|----------|
| `test_data_quality.py` | Integration tests | Validation, imputation, end-to-end |
| `test_negative_filter.py` | Unit tests | Unit classification, negative filtering |

### 12.2 Running Tests

```bash
# Run all tests
python test_data_quality.py
python test_negative_filter.py

# Expected output (test_data_quality.py):
# [PASS] negative counter quarantined
# [PASS] sentinel quarantined
# [PASS] percentage>100 quarantined
# [PASS] bad values nulled in returned frame
# [PASS] missing baseline day imputed from 4-week median
# [PASS] imputed day counted
# [PASS] A and B degraded, C excluded
# [PASS] Cell-B shows imputed baseline day
# [PASS] invalid PRB recorded in quarantine_df
# [PASS] Cell-C recorded in incomplete_df
# [PASS] analyze_all_kpis returns 5 items
# RESULT: 11 passed, 0 failed

# Expected output (test_negative_filter.py):
# [PASS] All current targets keep >=0 filtering (no behavior change)
# [PASS] dBm target recognized as negative-allowed
# [PASS] dB target recognized as negative-allowed
# [PASS] Interference feature recognized
# [PASS] OLD logic destroyed all negative dBm rows
# [PASS] NEW logic preserved all negative dBm rows
# [PASS] Counter target still drops the impossible negative
# [PASS] main_function_for_selected_kpi imports and exposes analyze_selected_kpi
# RESULT: 8 passed, 0 failed
```

### 12.3 Test Scenarios

The test suite validates:
1. **Negative counter quarantining** -- Invalid negative values in non-negative metrics
2. **Sentinel detection** -- Vendor null markers (4294967295)
3. **Percentage bounds** -- Values outside [0, 100] for % metrics
4. **Baseline imputation** -- Same-weekday median filling
5. **End-to-end degradation** -- Complete pipeline with degraded/normal cells
6. **Incomplete handling** -- Cells with missing days properly excluded
7. **Unit classification** -- dBm/dB vs. counter/percentage distinction
8. **Backward compatibility** -- Existing KPIs unaffected by new features

---

## 13. Extending the System

### 13.1 Adding New Counter Types

To support a new vendor's counter naming convention:

```python
# In clean_excel_and_helpers.py
def normalize_column_name(col) -> str:
    col = str(col).lower()
    # Add vendor-specific normalization
    col = col.replace("vendor_prefix_", "")
    # ... existing logic
    return col
```

### 13.2 Adding New Visualization

```python
# In Visualization_Functions.py
def show_new_chart(parent_window, data, params):
    win = tk.Toplevel(parent_window)
    # chart implementation
    pass
```

### 13.3 Adding Export Format

```python
# Create new module: Generate_PDF_Report.py
def generate_pdf_report(output_df, summary_df, save_path):
    # Implementation using reportlab or fpdf2
    pass

# Register in initialization.py
from Generate_PDF_Report import generate_pdf_report
```

### 13.4 Batch/CLI Mode

For headless operation (no GUI):

```python
# batch_analysis.py
from main_function_for_selected_kpi import analyze_selected_kpi
from combined_degraded_kpi import analyze_all_kpis
import pandas as pd

df = pd.read_excel("network_data.xlsx")
output, metadata = analyze_selected_kpi(
    df=df,
    selected_kpi_name="DL Traffic",
    num_days=4,
    degradation_threshold=30.0,
    baseline_mode="last_week",
    enable_significance_test=True
)
output.to_csv("results.csv", index=False)
```

---

## 14. Troubleshooting

### 14.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Target KPI column not found" | Column name mismatch | Check Excel headers, use find_matching_column() logic |
| "No degraded cells found" | Threshold too strict / no real degradation | Lower threshold, disable significance test, check date range |
| "All cells excluded" | min_baseline_value too high | Adjust min_baseline_value in KPI config |
| "python-docx not installed" | Missing optional dependency | `pip install python-docx` or disable Word export |
| "Date parsing failed" | Non-standard date format | Ensure Excel dates are proper datetime cells |
| "Memory error" | Dataset too large | Process by cluster, increase RAM, or use chunked reading |
| "Zero baseline value" | Division by zero in degradation calc | Check data quality, baseline period selection |

### 14.2 Debug Information

The system provides debug metadata after each analysis:

```python
metadata["debug_info"] = {
    "cells_after_merge": 1523,      # Cells with both recent & baseline
    "max_degradation": 87.5,        # Worst degradation % found
    "mean_degradation": 23.4,       # Average degradation %
    "min_baseline_excluded": 45,    # Cells excluded by min baseline
    "incomplete_cells": 12,         # Cells with missing days
    "quarantined_values": 3,        # Invalid values nullified
}
```

### 14.3 Log Interpretation

```
[10%] Loading Excel sheet: Sheet1...           -> File I/O in progress
[35%] Analyzing KPI: DL Traffic...              -> Core analysis running
INFO: 45 cells excluded by min_baseline_value   -> Filter applied
DQ: 3 invalid value(s) quarantined in 'PRB'     -> Data quality action
[100%] Analysis completed.                      -> Success
```

---

## 15. License & Attribution

### 15.1 Project Information

- **Project Name:** Data-Driven & Automation-Based RF Optimization for Modern 4G/5G Mobile Networks
- **System Name:** LTE KPI Degradation Analyzer v2.0
- **Institution:** Information Technology Institute (ITI)
- **Year:** 2026
- **Team:** Musketeers_Team
- **Project Type:** Graduation Project

### 15.2 Acknowledgments

This project was developed as part of the ITI graduation requirements. The system leverages:
- **Pandas & NumPy** for data manipulation
- **SciPy** for statistical testing
- **Matplotlib** for visualization
- **python-docx** for report generation
- **Tkinter** for the graphical interface

### 15.3 Citation

If using this system in academic or professional work:

```bibtex
@software{lte_kpi_analyzer_2026,
  title = {LTE KPI Degradation Analyzer v2.0},
  author = {Musketeers_Team},
  institution = {Information Technology Institute (ITI)},
  year = {2026},
  note = {Graduation Project -- Data-Driven RF Optimization}
}
```

---

## Appendix A: Complete Column Categories

### A.1 TA Distribution (Coverage)
- `0-156 m`, `156-312 m`, `312-624 m`, `624-1092 m`
- `1-2 km`, `2-3.5 km`, `3.5-6.6 km`, `6.6-14 km`
- `TA Weighted Avg (meter)`

### A.2 CEU (Cell Edge User)
- `(HU)CEU Cell Downlink/Uplink Average Throughput`
- `(HU)CEU User Downlink/Uplink Average Throughput`
- `L.Traffic.User.BorderUE.Avg`

### A.3 Carrier Aggregation
- `L.CA.UE.Avg`, `L.CA.DLSCell.Act.Att`, `L.CA.DLSCell.Add.Att`
- `MAC CA Traffic Volume GB`, `MAC CA Traffic Ratio`
- `3CC DL PDCP CA Traffic Volume GB`, `DL PDCP FDDTDD CA Traffic Volume GB`

### A.4 MIMO/Rank
- `Reported rank 2 (%)`, `CQI_CW0`, `CQI_CW1`

### A.5 RRC Re-establishment
- `RRC Reestablish Setup Success Rate(%)`, `RRC Reestablish Failures(times)`
- `L.RRC.ReEstFail.NoReply`, `L.RRC.ReEstFail.Rej`, `L.RRC.ReEstFail.NoCntx`

### A.6 QCI-Specific
- `DL Traffic QCI-1/6/7/9`, `DL user Thrpt Mbps QCI 7`
- `E-RAB Drop Rate QCI 7`, `L.Traffic.ActiveUser.DL.QCI.7`

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **KPI** | Key Performance Indicator -- measurable network metric |
| **Baseline** | Reference period for comparison (historical "normal") |
| **Degradation** | Performance decline relative to baseline |
| **CEU** | Cell Edge User -- subscriber at coverage boundary |
| **CA** | Carrier Aggregation -- combining multiple carriers |
| **TA** | Timing Advance -- distance estimation from propagation delay |
| **CQI** | Channel Quality Indicator -- DL channel condition |
| **MCS** | Modulation and Coding Scheme -- spectral efficiency |
| **BLER** | Block Error Rate -- retransmission ratio |
| **PRB** | Physical Resource Block -- LTE resource unit |
| **RACH** | Random Access Channel -- initial UE access |
| **CSFB** | Circuit Switched Fallback -- voice fallback to 2G/3G |
| **VoLTE** | Voice over LTE -- packet-switched voice |
| **SRVCC** | Single Radio Voice Call Continuity -- VoLTE to 2G/3G handover |
| **Welch's t-test** | Statistical test for unequal variance means |

---

*Document Version: 2.0*  
*Last Updated: June 2026*  
*For technical support or feature requests, contact the development team.*