# LTE KPI Degradation Analyzer

## Overview

**LTE KPI Degradation Analyzer** is a desktop GUI tool developed for the ITI Graduation Project 2026.

The tool helps RF optimization and telecom data analytics engineers analyze LTE network KPI degradation using a data-driven and rule-based approach.

It allows the user to upload an LTE KPI Excel file, select one KPI or analyze all supported KPIs, compare recent performance against the same period from the previous week, detect degraded cells, identify possible root causes using related counters, recommend optimization actions, visualize results in a dashboard, and export the results as CSV files.

---

## Project Idea

In traditional RF optimization, engineers manually check KPI reports, compare degraded cells, analyze related counters, and recommend actions. This process can be slow and repetitive.

This project automates the first layer of KPI degradation analysis by providing:

- Degraded cell detection
- Root-cause analysis using related counters
- Action recommendation
- Dashboard visualization
- CSV reporting
- GUI-based workflow
- Support for `.exe` deployment

The project is designed for LTE network optimization and can later be extended to 5G NR KPIs.

---

## Main Features

### Desktop GUI

The tool uses a Tkinter-based desktop interface. It does not require Streamlit or a web browser.

Main GUI features:

- Browse and upload Excel KPI file
- Select KPI from dropdown list
- Select number of comparison days
- Set degradation threshold
- Enable or disable complete-days filtering
- Run selected KPI analysis
- Analyze all KPIs at once
- Save degraded-cell CSV output
- Show dashboard
- Track execution using progress bar and percentage indicator

---

## KPI Degradation Detection

The tool compares:

```text
Recent period = last N days in the dataset
Baseline period = same N days from the previous week
```

Example:

```text
If recent period = 2026-05-16 to 2026-05-18
Then baseline period = 2026-05-09 to 2026-05-11
```

This is useful because mobile network traffic and KPI behavior usually follow weekly patterns.

---

## Supported KPIs

The tool currently supports:

- DL Traffic
- UL Traffic
- DL Throughput
- UL Throughput
- RRC Setup SR
- ERAB Setup SR
- Drop Rate
- HO Success Rate
- Availability
- RACH Success Rate
- VoLTE KPIs
- CSFB KPI

---

## Root-Cause Analysis

For each degraded cell, the tool checks related counters and KPIs to identify possible causes.

Example for DL Traffic:

- DL throughput
- User throughput
- DL PRB utilization
- CQI
- DL IBLER
- DL RBLER
- PDSCH MCS
- Availability
- Active users
- CA traffic ratio
- QCI-9 traffic
- CCE allocation failure

The tool returns:

- Main cause
- Recent cause value
- Baseline cause value
- Cause change percentage
- Root-cause category
- Recommended action
- All detected causes
- Multi-cause flag

---

## Recommendation Engine

The tool provides rule-based optimization recommendations according to the detected root cause.

| Root Cause | Recommended Action |
|---|---|
| DL congestion | Check PRB utilization, load balancing, CA, bandwidth, and capacity expansion |
| Poor radio quality | Check CQI, interference, PCI, antenna tilt, azimuth, and coverage |
| Availability issue | Check alarms, S1 issue, power issue, transmission, and site outage |
| HO failure | Check neighbors, A3 offset, CIO, TTT, PCI, and target coverage |
| CSFB issue | Check 2G/3G neighbors, redirection, target RAT coverage, and CSFB configuration |
| VoLTE issue | Check VoLTE traffic, QCI-1/QCI-7, SRVCC, IMS service, and bearer drops |

---

## Analyze All KPIs

The tool includes an **Analyze All KPIs** feature.

When used, it analyzes all supported KPIs using each KPI default threshold and the number of days selected in the GUI.

Outputs may include:

- One CSV file per KPI
- Combined degraded-cell output
- Summary report

---

## Dashboard

The dashboard provides visual insight into the analysis results.

Dashboard features include:

- Summary KPIs
- Top degraded cells
- Degraded cells per KPI
- Root-cause distribution
- Bar values displayed above or beside bars

---

## Degradation Ratio Formula

For KPIs where lower values are bad, such as traffic, throughput, success rates, and availability:

```text
Degradation % = ((Baseline - Recent) / Baseline) * 100
```

For KPIs where higher values are bad, such as drop rate or failure counters:

```text
Degradation % = ((Recent - Baseline) / Baseline) * 100
```

Positive degradation percentage means the KPI became worse.

---

## Threshold Logic

Thresholds are configurable and stored inside the code under `KPI_CONFIGS`.

The current thresholds are initial engineering thresholds, not fixed telecom-standard values.

| KPI Type | Suggested Sensitivity |
|---|---|
| Traffic KPIs | Higher threshold because traffic naturally changes |
| Throughput KPIs | Medium threshold because throughput is sensitive |
| Success Rate KPIs | Lower threshold because small drops can be serious |
| Drop Rate KPIs | Medium threshold because increase means degradation |
| Availability | Very low threshold because availability is critical |

Example:

```python
"DL Traffic": {
    "default_threshold": 30.0
}
```

This means a cell is degraded if DL Traffic decreased by 30% or more compared with the same days last week.

---

## Output CSV Columns

The generated CSV output includes columns such as:

- eNodeB Name
- Cell Name
- LocalCell Id
- Selected KPI name
- Target KPI column
- KPI category
- KPI bad direction
- Selected threshold
- Recent period
- Baseline period
- Recent average KPI
- Baseline average KPI
- Recent total KPI
- Baseline total KPI
- Recent days count
- Baseline days count
- KPI degradation ratio %
- KPI status
- Main cause counter or KPI
- Main cause recent value
- Main cause baseline value
- Main cause change %
- Main root-cause category
- Main degradation reason
- Main recommended action
- Number of detected causes
- Multi-cause flag
- All detected causes
- All cause categories
- All recommended actions

---

## Recommended Project Structure

```text
LTE-KPI-Degradation-Analyzer/
│
├── LTE_KPI_Degradation_Analyzer.py
├── requirements.txt
├── README.md
├── sample_data/
│   └── sample_kpis.xlsx
├── outputs/
│   └── sample_output.csv
├── screenshots/
│   ├── gui_home.png
│   ├── dashboard.png
│   └── output_csv.png
└── docs/
    └── project_report.pdf
```

---

## Requirements

Install the required packages using:

```bash
py -m pip install -r requirements.txt
```

`requirements.txt`:

```text
pandas
numpy
openpyxl
pyinstaller
matplotlib
```

---

## How to Run the Tool

### 1. Place files in one folder

Example:

```text
HUAWEI DATA/
├── LTE_KPI_Degradation_Analyzer.py
├── requirements.txt
└── New Cairo KPIs.xlsx
```

### 2. Install requirements

```bash
py -m pip install -r requirements.txt
```

### 3. Run the GUI

```bash
py LTE_KPI_Degradation_Analyzer.py
```

---

## How to Use the GUI

1. Click **Browse**
2. Select the LTE KPI Excel file
3. Select a KPI from the dropdown list
4. Choose the number of comparison days
5. Set threshold percentage
6. Select whether to require complete days in both periods
7. Click **Run Analysis**
8. Review the result table and log
9. Click **Save CSV** to export the result
10. Click **Show Dashboard** to view dashboard charts

---

## Analyze All KPIs

To analyze all KPIs:

1. Upload the Excel file
2. Choose the comparison days
3. Select complete-days option if needed
4. Click **Analyze All KPIs**

The tool will analyze all configured KPIs using each KPI default threshold.

---

## Debugging Tips

If no degraded cells appear:

1. Reduce the threshold
2. Uncheck complete-days filtering
3. Check recent and baseline dates in the log
4. Check maximum degradation value in the log
5. Check if the selected KPI column exists in the Excel file
6. Check if related counters are found
7. Validate that the Excel file contains data for both recent and baseline periods

Recommended testing values:

| KPI | Test Threshold |
|---|---:|
| DL Traffic | 5-10% |
| UL Traffic | 5-10% |
| DL Throughput | 5-10% |
| UL Throughput | 5-10% |
| RRC Setup SR | 1-3% |
| ERAB Setup SR | 1-3% |
| HO Success Rate | 1-3% |
| RACH Success Rate | 1-3% |
| Availability | 0.5-1% |
| CSFB KPI | 1-5% |

---

## Limitations

This project uses rule-based degradation detection and root-cause analysis.

Current limitations:

- It depends on column names in the Excel file.
- It uses relative comparison with the same period last week.
- It does not yet use machine learning anomaly detection in the GUI version.
- Recommendations are rule-based and need RF engineer validation.
- It does not directly modify network parameters.
- It does not connect to OSS or live network systems.

---

## Future Work

Possible future enhancements:

- Add machine learning anomaly detection models
- Add automatic thresholding
- Add PDF report generation
- Add parameter audit module
- Add OSS integration
- Add multi-vendor support
- Add 5G NR KPI support
- Add time-series visualization
- Add cell-level historical trend analysis
- Add automatic action-priority scoring
- Add configuration file instead of hardcoded KPI rules

---

## Graduation Project Value

This project demonstrates how telecom network optimization can be enhanced using data analytics and automation.

It provides a practical workflow for RF engineers:

```text
KPI monitoring -> degraded cell detection -> root-cause analysis -> recommendation -> reporting
```

This supports faster troubleshooting, better decision-making, and a more data-driven optimization process.

---

## Team

Developed by:

```text
Mahmoud Ashraf
Ibrahim samy
Mohab Tarek
Khaled Mogahed
Tasneem Amein
ITI Graduation Project 2026
Telco Cloud Track
```

---

## Disclaimer

This tool is designed for educational and graduation-project purposes. The recommended actions should be reviewed by RF optimization engineers before applying any changes to a live network.
