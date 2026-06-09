# LTE KPI Degradation Analyzer - Enhanced Version v2.0

## ITI Graduation Project 2026

**Developed by: Musketeers_Team**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Supported KPI Categories](#supported-kpi-categories)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Usage Guide](#usage-guide)
7. [Configuration](#configuration)
8. [Output Files](#output-files)
9. [Technical Architecture](#technical-architecture)
10. [Troubleshooting](#troubleshooting)
11. [License](#license)

---

## Project Overview

The **LTE KPI Degradation Analyzer** is a comprehensive tool designed for RF (Radio Frequency) Optimization engineers to automatically detect, analyze, and diagnose KPI (Key Performance Indicator) degradation in LTE/4G cellular networks. This tool compares recent KPI performance against baseline periods, identifies degraded cells, and provides root cause analysis with recommended actions.

### Purpose

- Automate the detection of KPI degradation across multiple network cells
- Provide intelligent root cause analysis based on related counter correlations
- Generate professional reports for network optimization teams
- Reduce manual analysis time and improve troubleshooting efficiency

### Key Capabilities

- **Multi-KPI Analysis**: Supports 12 different KPI categories covering traffic, throughput, accessibility, retainability, mobility, and availability
- **Configurable Baselines**: Multiple baseline comparison modes for flexible analysis
- **Statistical Validation**: Welch's t-test for statistical significance of degradation
- **Root Cause Detection**: Automated identification of contributing factors with severity-weighted ranking
- **Report Generation**: Professional Word document reports with tables and visualizations

---

## Features

### Version 2.0 Enhancements

| Feature | Description |
|---------|-------------|
| **Configurable Baseline Window** | Supports 7-day comparison, 4-week rolling average, and custom date ranges |
| **Minimum Baseline Value Filter** | Filters low-traffic/low-load cells to reduce false positives |
| **Severity Weighting** | Prioritizes root causes based on severity scores for better ranking |
| **Statistical Significance Test** | Welch's t-test validates degradation significance (p < 0.05) |
| **Enhanced Aggregation** | Mean, max, and percentile aggregation for failure counters |
| **Vectorized Processing** | Optimized performance using NumPy vectorized operations |
| **Multi-Sheet Excel Support** | Handles complex Excel files with multiple sheets |
| **Word Report Generation** | Professional reports with degradation tables and summaries |
| **Visualization Functions** | Built-in charts for trend analysis and cause distribution |

### Smart Column Matching

The analyzer includes intelligent column matching that handles:
- Spaces and hidden line breaks in Excel column names
- Case-insensitive matching
- Flexible column name variations

---

## Supported KPI Categories

The analyzer supports **12 KPI categories** with **86 related counters**:

| # | KPI Category | Target KPI | Category Type | Default Threshold |
|---|--------------|------------|---------------|-------------------|
| 1 | DL Traffic | (HU) DL Traffic Volume (GBytes) | Traffic | 30% |
| 2 | UL Traffic | (HU) UL Traffic Volume (GBytes) | Traffic | 30% |
| 3 | DL Throughput | (HU) User DL Average Throughput (Mbps) | Integrity | 20% |
| 4 | UL Throughput | (HU) User UL Average Throughput (Mbps) | Integrity | 20% |
| 5 | RRC Setup SR | (TE) RRC Setup SR% | Accessibility | 5% |
| 6 | ERAB Setup SR | ERAB Setup Success Rate | Accessibility | 5% |
| 7 | Drop Rate | E-RAB Drop Rate (E-NodeB + MME) % | Retainability | 20% |
| 8 | HO Success Rate | HO SR% Overall | Mobility | 5% |
| 9 | Availability | Availability | Availability | 1% |
| 10 | RACH Success Rate | (HU) RACH Success Rate(%) | Accessibility | 5% |
| 11 | CSFB KPI | CSFB SR% | CSFB / Voice Accessibility | 5% |
| 12 | VoLTE KPIs | BA_Voice E2E VQI | VoLTE | 5% |

### Related Counters per KPI

Each KPI category includes multiple related counters (5-13 counters each) for root cause analysis:

- **DL Traffic**: 13 related counters (CQI, IBLER, RBLER, MCS, PRB utilization, CA traffic, etc.)
- **UL Traffic**: 9 related counters (UL interference, PUSCH MCS, UL IBLER, etc.)
- **DL Throughput**: 7 related counters
- **UL Throughput**: 7 related counters
- **RRC Setup SR**: 7 related counters
- **ERAB Setup SR**: 6 related counters
- **Drop Rate**: 8 related counters
- **HO Success Rate**: 8 related counters
- **Availability**: 4 related counters
- **RACH Success Rate**: 5 related counters
- **CSFB KPI**: 6 related counters
- **VoLTE KPIs**: 7 related counters

---

## Requirements

### Python Version

- Python 3.9 or higher

### Required Libraries

```
numpy>=1.21.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
python-docx>=0.8.11
openpyxl>=3.0.0
```

### Required Columns in Input Data

The input Excel file must contain the following columns:

| Column Name | Description |
|-------------|-------------|
| Date | Date of the measurement (supports daily/hourly granularity) |
| eNodeB Name | Site/Base station identifier |
| Cell Name | Cell sector identifier |
| LocalCell Id | Local cell identifier |
| [KPI columns] | Various KPI measurements as defined in KPI_CONFIGS |

---

## Installation

### Step 1: Clone or Download

```bash
# Clone the repository
git clone <repository-url>

# Or download the notebook file directly
```

### Step 2: Install Dependencies

```bash
pip install numpy pandas scipy matplotlib python-docx openpyxl
```

### Step 3: Launch Jupyter Notebook

```bash
jupyter notebook 4-LTE_KPI_Degradation_Analyzer_Enhanced.ipynb
```

---

## Usage Guide

### Quick Start

```python
# 1. Import required libraries (Cell 2)
# 2. Define constants (Cell 3)
# 3. Load KPI configuration (Cell 4)

# 4. Load your data
df = pd.read_excel("your_kpi_data.xlsx", sheet_name=0)

# 5. Run analysis for all KPIs
combined_df, summary_df, all_outputs = analyze_all_kpis(
    df, 
    num_days=4, 
    baseline_mode=BASELINE_MODE_LAST_WEEK,
    enable_significance_test=True
)

# 6. Visualize results
plot_degraded_cells_per_kpi(summary_df)
plot_root_cause_distribution(combined_df)

# 7. Save results
save_results(combined_df, summary_df, all_outputs, output_dir="./output")

# 8. Generate Word report
generate_word_report(combined_df, summary_df, save_path="RF_Optimization_Report.docx")
```

### Single KPI Analysis

```python
# Analyze a specific KPI
output_df, metadata = analyze_selected_kpi_enhanced(
    df=df,
    selected_kpi_name="DL Traffic",
    num_days=4,
    degradation_threshold=30.0,
    require_complete_days=True,
    baseline_mode=BASELINE_MODE_LAST_WEEK,
    enable_significance_test=True
)

print(f"Degraded Cells Found: {len(output_df)}")
```

### Baseline Modes

| Mode | Constant | Description |
|------|----------|-------------|
| Last Week | `BASELINE_MODE_LAST_WEEK` | Compares against same N days from previous week |
| 4-Week Rolling | `BASELINE_MODE_4WEEK_AVG` | Uses 4-week rolling average as baseline |
| Custom Range | `BASELINE_MODE_CUSTOM` | User-defined baseline start and end dates |

```python
# Example: Custom baseline
output_df, metadata = analyze_selected_kpi_enhanced(
    df=df,
    selected_kpi_name="DL Throughput",
    num_days=4,
    degradation_threshold=20.0,
    baseline_mode=BASELINE_MODE_CUSTOM,
    custom_baseline_start="2026-01-01",
    custom_baseline_end="2026-01-07"
)
```

---

## Configuration

### KPI Configuration Structure

Each KPI in `KPI_CONFIGS` contains:

```python
{
    "target_kpi": "Column name of the main KPI to analyze",
    "bad_direction": "low" or "high" (direction of degradation)",
    "default_threshold": "Percentage threshold for degradation detection",
    "category": "KPI category (Traffic, Integrity, Accessibility, etc.)",
    "output_prefix": "Prefix for output file naming",
    "min_baseline_value": "Minimum baseline value filter (NEW in v2.0)",
    "related_rules": [
        {
            "feature": "Related counter column name",
            "bad_direction": "low" or "high",
            "threshold": "Change percentage threshold",
            "severity": "1-5 severity score (NEW in v2.0)",
            "category": "Root cause category",
            "reason": "Explanation of the cause",
            "recommended_action": "Suggested action to take"
        }
    ]
}
```

### Severity Levels

| Severity | Level | Description |
|----------|-------|-------------|
| 5 | Critical | Major issues requiring immediate attention (Availability, Drop issues) |
| 4 | High | Significant impact on user experience (Radio failures, Core issues) |
| 3 | Medium | Moderate impact (Throughput degradation, Congestion) |
| 2 | Low | Minor issues (Low utilization, Parameter tuning) |
| 1 | Informational | Monitoring/Validation needed (Traffic demand changes) |

### Modifying KPI Configuration

To add or modify KPI configurations, edit the `KPI_CONFIGS` dictionary in Cell 4:

```python
KPI_CONFIGS["New KPI"] = {
    "target_kpi": "Your KPI Column Name",
    "bad_direction": "low",
    "default_threshold": 10.0,
    "category": "Category Name",
    "output_prefix": "new_kpi",
    "min_baseline_value": 0.0,
    "related_rules": [
        {
            "feature": "Related Counter 1",
            "bad_direction": "high",
            "threshold": 20,
            "severity": 3,
            "category": "Category",
            "reason": "Reason text",
            "recommended_action": "Action text"
        }
    ]
}
```

---

## Output Files

### CSV Outputs

| File Name | Description |
|-----------|-------------|
| `dl_traffic_degraded.csv` | Degraded cells for DL Traffic KPI |
| `ul_traffic_degraded.csv` | Degraded cells for UL Traffic KPI |
| `dl_throughput_degraded.csv` | Degraded cells for DL Throughput KPI |
| `ul_throughput_degraded.csv` | Degraded cells for UL Throughput KPI |
| `rrc_setup_sr_degraded.csv` | Degraded cells for RRC Setup SR |
| `erab_setup_sr_degraded.csv` | Degraded cells for ERAB Setup SR |
| `drop_rate_degraded.csv` | Degraded cells for Drop Rate |
| `ho_success_rate_degraded.csv` | Degraded cells for HO Success Rate |
| `availability_degraded.csv` | Degraded cells for Availability |
| `rach_success_rate_degraded.csv` | Degraded cells for RACH Success Rate |
| `csfb_kpi_degraded.csv` | Degraded cells for CSFB KPI |
| `volte_kpis_degraded.csv` | Degraded cells for VoLTE KPIs |
| `all_kpis_combined.csv` | Combined results from all KPIs |
| `summary_report.csv` | Summary table of all KPI analysis |

### Word Report Output

| File Name | Description |
|-----------|-------------|
| `RF_Optimization_Report.docx` | Professional report with tables, summaries, and analysis results |

### Output Columns

Each degraded cells output contains:

| Column | Description |
|--------|-------------|
| eNodeB Name | Site identifier |
| Cell Name | Cell identifier |
| LocalCell Id | Local cell ID |
| selected_kpi_name | Analyzed KPI name |
| target_kpi_column | Actual column used |
| kpi_category | KPI category |
| recent_avg_kpi | Average KPI in recent period |
| baseline_avg_kpi | Average KPI in baseline period |
| kpi_degradation_ratio_% | Degradation percentage |
| kpi_status | "Degraded" or "Normal" |
| stat_significant | Boolean (t-test result) |
| p_value | Statistical p-value |
| main_cause_counter_or_kpi | Primary identified cause |
| main_root_cause_category | Category of root cause |
| main_degradation_reason | Explanation of degradation |
| main_recommended_action | Suggested action |
| number_of_detected_causes | Count of detected causes |
| multi_cause_flag | "Yes" if multiple causes detected |

---

## Technical Architecture

### Data Flow

```
Input Excel File
       ↓
[Load & Clean Data]
       ↓
[Smart Column Matching]
       ↓
[Period Definition]
       ↓
[Aggregation (Mean/Max/Sum)]
       ↓
[Degradation Calculation]
       ↓
[Statistical Significance Test]
       ↓
[Root Cause Detection]
       ↓
[Output Generation]
       ↓
CSV Files + Word Report
```

### Key Functions

| Function | Purpose |
|----------|---------|
| `clean_excel_columns()` | Clean column names from spaces/line breaks |
| `find_matching_column()` | Smart column name matching |
| `calculate_degradation()` | Calculate degradation percentage |
| `perform_ttest()` | Welch's t-test for statistical significance |
| `get_periods_enhanced()` | Determine analysis periods |
| `find_degradation_causes_vectorized()` | Optimized root cause detection |
| `analyze_selected_kpi_enhanced()` | Main single KPI analysis engine |
| `analyze_all_kpis()` | Batch analysis for all KPIs |
| `generate_word_report()` | Create Word document report |

### Performance Optimization

- **Vectorized Operations**: Uses NumPy arrays instead of row-by-row iteration
- **Efficient Aggregation**: GroupBy operations with multiple aggregation functions
- **Memory Management**: Drops unused columns during intermediate processing

---

## Troubleshooting

### Common Issues

#### 1. "Target KPI column not found"

**Cause**: Column name mismatch between config and Excel file

**Solution**: 
- Check for hidden spaces or line breaks in Excel column names
- The smart matching should handle most variations
- Verify exact column name in Excel using `df.columns.tolist()`

#### 2. "Missing required columns"

**Cause**: Required identification columns not present

**Solution**:
- Ensure columns exist: `Date`, `eNodeB Name`, `Cell Name`, `LocalCell Id`
- Modify `CELL_ID_COLS` constant if your column names differ

#### 3. "No degraded cells found"

**Possible Causes**:
- Threshold too high
- Baseline period has issues
- Data quality problems

**Solution**:
- Lower the degradation threshold
- Check baseline period data availability
- Enable debug logging with `log_callback=print`

#### 4. "python-docx not installed"

**Solution**:
```bash
pip install python-docx
```

#### 5. Low degradation detection with significance test

**Cause**: Statistical test filtering out non-significant changes

**Solution**:
- Disable significance test: `enable_significance_test=False`
- Or increase number of analysis days for more data points

---

## Example Use Case

### Scenario: Investigating DL Traffic Drop

A network engineer notices overall DL traffic decreased and wants to identify affected cells and root causes.

```python
# 1. Load daily KPI data
df = pd.read_excel("network_kpi_data.xlsx")

# 2. Analyze DL Traffic with 4-day window
output_df, metadata = analyze_selected_kpi_enhanced(
    df=df,
    selected_kpi_name="DL Traffic",
    num_days=4,
    degradation_threshold=30.0,
    baseline_mode=BASELINE_MODE_LAST_WEEK
)

# 3. Review results
print(f"Analysis Period: {metadata['recent_start']} to {metadata['recent_end']}")
print(f"Degraded Cells: {len(output_df)}")

# 4. Identify top root causes
if not output_df.empty:
    print(output_df['main_root_cause_category'].value_counts())
    
# 5. Generate report
generate_word_report(output_df, None, selected_kpi="DL Traffic", 
                     analysis_mode="single", save_path="DL_Traffic_Report.docx")
```

---

## Contributors

**Musketeers_Team** - ITI Graduation Project 2026

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | 2026 | Enhanced version with configurable baselines, significance testing, severity weighting, vectorized processing |
| v1.0 | 2025 | Initial release with basic KPI analysis |

---

## License

This project is developed as part of ITI Graduation Project 2026.

---

*For questions or support, please contact the Musketeers_Team.*
