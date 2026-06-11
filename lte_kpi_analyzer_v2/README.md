 # LTE KPI Degradation Analyzer

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Module Documentation](#module-documentation)
  - [KPI_Configuration.py](#kpi_configurationpy---configuration-module)
  - [initialization.py](#initializationpy---initialization-module)
  - [clean_excel_and_helpers.py](#clean_excel_and_helperspy---data-cleaning-utilities)
  - [cause_detect_functions.py](#cause_detect_functionspy---root-cause-detection)
  - [main_function_for_selected_kpi.py](#main_function_for_selected_kpipy---main-analysis-engine)
  - [combined_degraded_kpi.py](#combined_degraded_kpipy---multi-kpi-analysis)
  - [Visualization_Functions.py](#visualization_functionspy---dashboard--charts)
  - [Generate_Word_Report.py](#generate_word_reportpy---word-document-generation)
  - [Save_Results.py](#save_resultspy---export-functions)
  - [Loading_file_inputs_outputs.py](#loading_file_inputs_outputspy---file-handling)
- [Supported KPIs](#supported-kpis)
- [Configuration Guide](#configuration-guide)
- [Adding New KPIs](#adding-new-kpis)
- [Statistical Methodology](#statistical-methodology)
- [Troubleshooting](#troubleshooting)
- [Dependencies](#dependencies)
- [Credits](#credits)

---

## Overview

**LTE KPI Degradation Analyzer** is a professional-grade tool designed for telecommunications engineers and network analysts to detect, analyze, and report KPI (Key Performance Indicator) degradations in LTE (Long-Term Evolution) cellular networks. The application provides an intuitive graphical interface for loading network performance data, identifying degraded cells, determining root causes, and generating comprehensive reports.

This project uses a **flat modular structure** where each Python file has a clear, single responsibility. This design makes it easy to locate and modify specific functionality without navigating through complex package hierarchies.

### Key Capabilities

- **Automated Degradation Detection**: Identifies cells experiencing significant performance degradation based on configurable thresholds
- **Root Cause Analysis**: Analyzes multiple related counters and metrics to determine probable causes of degradation
- **Statistical Validation**: Uses Welch's t-test to ensure statistical significance of detected degradations
- **Flexible Baseline Comparison**: Supports multiple baseline modes including last week, 4-week rolling average, and custom date ranges
- **Multi-KPI Analysis**: Analyze up to 12 different KPIs individually or all at once
- **Professional Reporting**: Generate Microsoft Word reports with detailed analysis results
- **Interactive Dashboard**: Visualize degradation patterns and root cause distributions through charts

---

## Features

### Core Analysis Features

| Feature | Description |
|---------|-------------|
| **Configurable Thresholds** | Set custom degradation thresholds per KPI (default: 20-30%) |
| **Multiple Baseline Modes** | Compare against last 7 days, 4-week rolling average, or custom date range |
| **Statistical Significance Testing** | Welch's t-test with configurable p-value threshold (default: 0.05) |
| **Severity Weighting** | Prioritize root causes based on severity levels (1-5) |
| **Minimum Baseline Filtering** | Exclude low-traffic or low-load cells from analysis |
| **Vectorized Processing** | Optimized pandas operations for handling large datasets |

### User Interface Features

- **Excel File Support**: Load data from `.xlsx` and `.xls` files with multi-sheet support
- **Sheet Selection**: Choose specific data sheets from multi-sheet Excel workbooks
- **Real-time Progress Tracking**: Visual progress bar and status updates during analysis
- **Results Grid**: Sortable, filterable treeview for browsing analysis results
- **Dashboard Visualization**: Bar charts showing degraded cells and root cause distribution
- **Trend Analysis**: Visualize KPI trends over time for specific cells
- **CSV Export**: Export analysis results to CSV format for further processing

### Reporting Features

- **Microsoft Word Report Generation**: Create professional reports with tables and charts
- **Summary Statistics**: Include overall degradation counts and severity breakdowns
- **Detailed Cell Reports**: Per-cell analysis with degradation percentages and root causes
- **Automatic Date Stamping**: Reports include analysis date and parameters used

---

## System Requirements

### Operating System
- Windows 10/11 (recommended)
- macOS 10.14+
- Linux (Ubuntu 20.04+, CentOS 8+, etc.)

### Python Version
- Python 3.8 or higher (Python 3.9+ recommended)

### Hardware Requirements
- **RAM**: Minimum 4GB (8GB+ recommended for large datasets)
- **Storage**: 500MB free disk space
- **Display**: Minimum 1280x720 resolution

---

## Installation

### Step 1: Clone or Download the Project

```bash
# Option A: Clone from repository (if applicable)
git clone <repository-url>
cd lte-kpi-analyzer

# Option B: Download and extract the project folder
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python -c "import pandas, numpy, scipy, matplotlib; print('All dependencies installed successfully!')"
```

---

## Quick Start

### Running the Application

```bash
# Run the main entry point
python initialization.py
```

### Basic Usage Workflow

1. **Load Data**: Click "Browse" to select an Excel file containing network KPI data
2. **Select Sheet**: Choose the appropriate sheet from multi-sheet Excel files
3. **Configure Analysis**:
   - Select the KPI to analyze
   - Set comparison days (typically 3-7 days)
   - Set degradation threshold percentage
   - Choose baseline mode
4. **Run Analysis**: Click "Analyze Selected KPI" or "Analyze All KPIs"
5. **Review Results**: Browse results in the treeview, dashboard, or trend charts
6. **Export**: Generate Word reports or export to CSV

---

## Project Structure

The project uses a **flat modular structure** for maximum simplicity and ease of editing. Each file has a clear, single responsibility:

```
project/
│
├── KPI_Configuration.py              # All KPI definitions, thresholds, and constants
├── initialization.py                 # GUI initialization and main entry point
├── clean_excel_and_helpers.py        # Data cleaning and helper utility functions
├── cause_detect_functions.py         # Root cause detection algorithms
├── main_function_for_selected_kpi.py # Core analysis engine for single KPI
├── combined_degraded_kpi.py          # Multi-KPI analysis orchestration
├── Visualization_Functions.py        # Dashboard and chart visualization
├── Generate_Word_Report.py           # Word document report generation
├── Save_Results.py                   # CSV and file export functions
├── Loading_file_inputs_outputs.py    # File I/O and data loading
│
└── requirements.txt                  # Python dependencies
```

### File Summary

| File | Purpose | Key Functions/Classes |
|------|---------|----------------------|
| `KPI_Configuration.py` | Central configuration | KPI_CONFIGS, column constants, baseline modes |
| `initialization.py` | App entry point | LTEKPIAnalyzerApp class, GUI setup |
| `clean_excel_and_helpers.py` | Data utilities | clean_excel_columns(), find_matching_column() |
| `cause_detect_functions.py` | Root cause analysis | find_degradation_causes_vectorized() |
| `main_function_for_selected_kpi.py` | Analysis engine | analyze_selected_kpi_enhanced() |
| `combined_degraded_kpi.py` | Multi-KPI logic | analyze_all_kpis() |
| `Visualization_Functions.py` | Charts & plots | show_dashboard(), show_trend_analysis() |
| `Generate_Word_Report.py` | Word reports | generate_word_report() |
| `Save_Results.py` | Export functions | export_to_csv(), save_results() |
| `Loading_file_inputs_outputs.py` | File handling | load_excel_file(), load_sheet_names() |

### Why Flat Structure?

The flat structure offers several advantages for this project:

| Advantage | Description |
|-----------|-------------|
| **Easy Navigation** | No need to navigate through nested directories |
| **Clear Ownership** | Each file has a single, obvious responsibility |
| **Simple Imports** | Direct imports without complex package paths |
| **Quick Editing** | Find the right file instantly by name |
| **Beginner Friendly** | No complex package structure to understand |

---

## Module Documentation

### KPI_Configuration.py - Configuration Module

**Purpose**: Centralized configuration for all KPI definitions, thresholds, and column mappings.

**Key Components**:

```python
# Global Column Names
DATE_COL = "Date"                    # Date column name in Excel
SITE_COL = "eNodeB Name"             # Site/Base station name
CELL_COL = "Cell Name"               # Cell identifier
LOCAL_CELL_COL = "LocalCell Id"      # Local cell ID

# Baseline Modes
BASELINE_MODE_LAST_WEEK = "last_week"           # Compare to previous 7 days
BASELINE_MODE_4WEEK_AVG = "4week_rolling_avg"   # Compare to 4-week average
BASELINE_MODE_CUSTOM = "custom_range"           # User-defined date range
```

**KPI Configuration Structure**:

Each KPI in `KPI_CONFIGS` dictionary contains:

| Field | Type | Description |
|-------|------|-------------|
| `target_kpi` | string | Exact column name in Excel |
| `bad_direction` | string | "low" (decrease is bad) or "high" (increase is bad) |
| `default_threshold` | float | Default degradation threshold (%) |
| `category` | string | KPI category for grouping |
| `output_prefix` | string | Prefix for output columns |
| `min_baseline_value` | float | Minimum baseline value to include cell |
| `related_rules` | list | List of related counter rules for root cause analysis |

**When to Edit**:
- Adding new KPIs to analyze
- Modifying degradation thresholds
- Changing column name mappings
- Adding new root cause detection rules

---

### initialization.py - Initialization Module

**Purpose**: GUI initialization and main application entry point.

**Key Components**:

```python
class LTEKPIAnalyzerApp:
    """Main GUI Application for LTE KPI Degradation Analyzer."""
    
    def __init__(self, root):
        """Initialize application with default settings."""
        
    def build_ui(self):
        """Build the user interface components."""
        
    def run(self):
        """Start the application main loop."""
```

**Features Initialized**:
- Main window with title and geometry
- File selection controls
- Analysis settings panel
- Results treeview
- Progress bar and status display
- Action buttons

**When to Edit**:
- Modifying main window properties
- Changing UI layout
- Adding new UI components
- Modifying default values

---

### clean_excel_and_helpers.py - Data Cleaning Utilities

**Purpose**: Helper functions for data cleaning, normalization, and processing.

**Key Functions**:

```python
def clean_excel_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean Excel column names by removing extra whitespace and special characters.
    Returns DataFrame with cleaned column names.
    """

def normalize_column_name(name: str) -> str:
    """
    Normalize column name for matching.
    Converts to lowercase, removes special characters, standardizes whitespace.
    """

def find_matching_column(df: pd.DataFrame, target: str) -> str:
    """
    Find matching column in DataFrame using fuzzy matching.
    Returns the actual column name or None if not found.
    """

def clean_numeric_series(series: pd.Series) -> pd.Series:
    """
    Convert text values to numeric, handling commas and special characters.
    Returns cleaned numeric series.
    """

def calculate_degradation(current: float, baseline: float, 
                          bad_direction: str) -> float:
    """
    Calculate degradation percentage based on bad direction.
    Positive values indicate degradation.
    """
```

**When to Edit**:
- Modifying data cleaning logic
- Adding new column matching patterns
- Handling new data formats
- Adding custom data transformations

---

### cause_detect_functions.py - Root Cause Detection

**Purpose**: Algorithms for detecting root causes of KPI degradation.

**Key Functions**:

```python
def find_degradation_causes_vectorized(df: pd.DataFrame, cell_data: dict,
                                       rules: list) -> pd.DataFrame:
    """
    Vectorized root cause detection for improved performance.
    Analyzes multiple cells simultaneously using pandas operations.
    
    Args:
        df: Full DataFrame with all data
        cell_data: Dictionary with cell identifiers and periods
        rules: List of detection rules from KPI_CONFIGS
        
    Returns:
        DataFrame with detected causes, severity scores, and recommendations
    """

def find_degradation_causes_row(row: pd.Series, rules: list) -> list:
    """
    Row-by-row cause detection (fallback for complex cases).
    
    Args:
        row: Single row of cell data
        rules: List of detection rules
        
    Returns:
        List of detected causes with details
    """
```

**Detection Logic**:
1. For each degraded cell, analyze all related counters
2. Compare counter values between baseline and comparison periods
3. Check if change exceeds threshold in bad direction
4. Assign severity score based on rule configuration
5. Generate recommended actions

**When to Edit**:
- Modifying cause detection algorithms
- Adding new detection patterns
- Optimizing performance
- Changing severity calculation logic

---

### main_function_for_selected_kpi.py - Main Analysis Engine

**Purpose**: Core analysis engine for single KPI degradation detection.

**Key Functions**:

```python
def perform_ttest(baseline_values: np.array, comparison_values: np.array,
                  alpha: float = 0.05) -> dict:
    """
    Perform Welch's t-test for statistical significance.
    
    Returns:
        dict: {
            'is_significant': bool,
            'p_value': float,
            't_statistic': float,
            'baseline_mean': float,
            'comparison_mean': float
        }
    """

def get_periods_enhanced(df: pd.DataFrame, num_days: int,
                         baseline_mode: str) -> tuple:
    """
    Determine baseline and comparison periods based on mode.
    
    Returns:
        tuple: (baseline_start, baseline_end, comparison_start, comparison_end)
    """

def analyze_selected_kpi_enhanced(df: pd.DataFrame, kpi_config: dict,
                                  num_days: int, threshold: float,
                                  baseline_mode: str,
                                  require_complete_days: bool = True,
                                  enable_significance_test: bool = True) -> pd.DataFrame:
    """
    Main analysis function that orchestrates the entire analysis process.
    
    Steps:
    1. Identify baseline and comparison periods
    2. Calculate per-cell statistics
    3. Detect degraded cells based on threshold
    4. Perform statistical significance testing
    5. Analyze root causes
    6. Generate output DataFrame
    
    Returns:
        DataFrame with analysis results including degradation percentages,
        root causes, severity scores, and statistical test results.
    """
```

**When to Edit**:
- Modifying analysis algorithms
- Adding new statistical tests
- Changing period calculation logic
- Optimizing performance for large datasets

---

### combined_degraded_kpi.py - Multi-KPI Analysis

**Purpose**: Orchestration logic for analyzing multiple KPIs simultaneously.

**Key Functions**:

```python
def analyze_all_kpis(df: pd.DataFrame, kpi_configs: dict,
                     num_days: int, threshold: float,
                     baseline_mode: str) -> dict:
    """
    Analyze all configured KPIs and combine results.
    
    Args:
        df: Full DataFrame with all KPI data
        kpi_configs: Dictionary of all KPI configurations
        num_days: Number of comparison days
        threshold: Degradation threshold percentage
        baseline_mode: Baseline comparison mode
        
    Returns:
        dict: {
            'results': Dict[str, DataFrame],  # Per-KPI results
            'summary': DataFrame,             # Combined summary
            'degraded_cells': set             # All degraded cell IDs
        }
    """

def combine_results(all_results: dict) -> pd.DataFrame:
    """
    Combine results from multiple KPI analyses into summary.
    
    Returns:
        DataFrame with combined degradation information across all KPIs
    """
```

**When to Edit**:
- Modifying multi-KPI analysis workflow
- Changing result combination logic
- Adding summary statistics
- Modifying progress reporting

---

### Visualization_Functions.py - Dashboard & Charts

**Purpose**: Visualization functions for dashboard, trends, and charts.

**Key Functions**:

```python
def show_dashboard(root: tk.Tk, results_df: pd.DataFrame,
                   degraded_cells: set) -> None:
    """
    Display dashboard with degradation charts.
    
    Charts included:
    - Top degraded cells by KPI
    - Root cause distribution
    - Severity breakdown
    """

def show_trend_analysis(root: tk.Tk, df: pd.DataFrame,
                        cell_id: str, kpi_config: dict) -> None:
    """
    Show KPI trend chart for a specific cell over time.
    
    Displays:
    - Baseline period values
    - Comparison period values
    - Degradation threshold line
    """

def create_degradation_chart(results_df: pd.DataFrame) -> Figure:
    """
    Create bar chart of degraded cells.
    
    Returns:
        matplotlib Figure object
    """

def create_cause_distribution_chart(results_df: pd.DataFrame) -> Figure:
    """
    Create pie/bar chart of root cause distribution.
    
    Returns:
        matplotlib Figure object
    """
```

**When to Edit**:
- Adding new chart types
- Modifying chart styling
- Adding interactive elements
- Changing color schemes

---

### Generate_Word_Report.py - Word Document Generation

**Purpose**: Generate professional Microsoft Word reports from analysis results.

**Key Functions**:

```python
def generate_word_report(results_df: pd.DataFrame, 
                         summary_df: pd.DataFrame,
                         kpi_name: str,
                         analysis_params: dict) -> str:
    """
    Generate Word document with analysis report.
    
    Report sections:
    1. Title and date
    2. Analysis parameters summary
    3. Degradation overview
    4. Detailed cell-by-cell results
    5. Root cause summary
    6. Recommendations
    
    Returns:
        str: Path to generated Word file
    """

def add_results_table(doc: Document, df: pd.DataFrame) -> None:
    """
    Add formatted results table to Word document.
    """

def add_summary_section(doc: Document, summary: dict) -> None:
    """
    Add executive summary section to report.
    """
```

**When to Edit**:
- Modifying report layout
- Adding new sections
- Changing formatting
- Adding charts to reports

---

### Save_Results.py - Export Functions

**Purpose**: Export analysis results to various file formats.

**Key Functions**:

```python
def export_to_csv(results_df: pd.DataFrame, 
                   output_path: str = None) -> str:
    """
    Export results to CSV file.
    
    Args:
        results_df: DataFrame with analysis results
        output_path: Optional custom output path
        
    Returns:
        str: Path to saved CSV file
    """

def save_all_results(all_results: dict, 
                     output_dir: str = None) -> list:
    """
    Save all analysis results to separate files.
    
    Args:
        all_results: Dictionary with results from all KPIs
        output_dir: Optional custom output directory
        
    Returns:
        list: Paths to all saved files
    """
```

**When to Edit**:
- Adding new export formats
- Modifying file naming conventions
- Adding custom formatting options
- Modifying default save locations

---

### Loading_file_inputs_outputs.py - File Handling

**Purpose**: File I/O operations and data loading functions.

**Key Functions**:

```python
def load_excel_file(file_path: str) -> pd.DataFrame:
    """
    Load Excel file and return DataFrame.
    
    Supports: .xlsx, .xls formats
    Handles: Multiple sheets, merged cells, special characters
    """

def load_sheet_names(file_path: str) -> list:
    """
    Get list of sheet names from Excel file.
    
    Returns:
        list: Sheet names in the workbook
    """

def validate_data_format(df: pd.DataFrame, 
                         required_columns: list) -> tuple:
    """
    Validate that DataFrame has required columns.
    
    Returns:
        tuple: (is_valid: bool, missing_columns: list)
    """

def save_to_excel(df: pd.DataFrame, output_path: str) -> str:
    """
    Save DataFrame to Excel file with formatting.
    
    Returns:
        str: Path to saved file
    """
```

**When to Edit**:
- Adding support for new file formats
- Modifying data validation logic
- Adding preprocessing steps
- Handling new Excel features

---

## Supported KPIs

The analyzer supports the following Key Performance Indicators:

| KPI | Target Column | Default Threshold | Category |
|-----|---------------|-------------------|----------|
| **DL Traffic** | (HU) DL Traffic Volume (GBytes) | 30% | Traffic |
| **UL Traffic** | (HU) UL Traffic Volume (GBytes) | 30% | Traffic |
| **DL Throughput** | (HU) DL MAC RLC Throughput (Mbps) | 20% | Throughput |
| **UL Throughput** | (HU) UL MAC RLC Throughput (Mbps) | 20% | Throughput |
| **DL User Throughput** | (HU) DL User Throughput (Mbps) | 20% | Throughput |
| **UL User Throughput** | (HU) UL User Throughput (Mbps) | 20% | Throughput |
| **RRC SR** | (HU) RRC Connection Setup SR (%) | 20% | Signaling |
| **ERAB SR** | (HU) E-RAB Setup SR (%) | 20% | Signaling |
| **CSSR** | (HU) CSSR (%) | 20% | Signaling |
| **CSFB SR** | (HU) CSFB Success Rate (%) | 20% | Signaling |
| **Retention Rate** | (HU) Retention Rate (%) | 20% | Retention |
| **Mobility** | (HU) Mobility SR (%) | 20% | Mobility |

### KPI Categories

1. **Traffic KPIs**: Measure data volume carried by the network
2. **Throughput KPIs**: Measure data transmission speeds
3. **Signaling KPIs**: Measure connection establishment success rates
4. **Retention KPIs**: Measure ability to maintain connections
5. **Mobility KPIs**: Measure handover success rates

---

## Configuration Guide

### Modifying Degradation Thresholds

Edit `KPI_Configuration.py` to change default thresholds:

```python
"DL Traffic": {
    "target_kpi": "(HU) DL Traffic Volume (GBytes)",
    "bad_direction": "low",
    "default_threshold": 30.0,  # Change this value
    ...
}
```

### Setting Minimum Baseline Values

Filter out low-traffic cells that may show misleading degradations:

```python
"DL Traffic": {
    ...
    "min_baseline_value": 1.0,  # Exclude cells with < 1 GB baseline traffic
    ...
}
```

### Understanding Related Rules

Each KPI has related rules for root cause analysis:

```python
"related_rules": [
    {
        "feature": "(HU) DL PRB Utilization (%)",  # Counter to analyze
        "bad_direction": "high",                    # Direction indicating problem
        "threshold": 20,                            # Percentage threshold
        "severity": 3,                              # Severity level (1-5)
        "category": "Capacity",                     # Cause category
        "reason": "High PRB utilization causing congestion",
        "recommended_action": "Consider cell split or carrier aggregation"
    },
    ...
]
```

### Severity Levels

| Level | Description | Example Causes |
|-------|-------------|----------------|
| 5 | Critical | Hardware failures, complete outages |
| 4 | High | Major capacity issues, severe interference |
| 3 | Medium | Moderate capacity, minor interference |
| 2 | Low | Parameter misconfigurations, minor issues |
| 1 | Informational | Normal variations, transient issues |

---

## Adding New KPIs

To add a new KPI to the analyzer:

### Step 1: Add Configuration

Edit `KPI_Configuration.py` and add a new entry to `KPI_CONFIGS`:

```python
"New KPI Name": {
    # Required fields
    "target_kpi": "Exact Column Name in Excel",
    "bad_direction": "low",  # or "high"
    "default_threshold": 20.0,
    "category": "Category Name",
    "output_prefix": "new_kpi",
    
    # Optional but recommended
    "min_baseline_value": 0.0,
    
    # Root cause detection rules
    "related_rules": [
        {
            "feature": "Related Counter Column",
            "bad_direction": "high",
            "threshold": 20,
            "severity": 3,
            "category": "Cause Category",
            "reason": "Explanation of cause",
            "recommended_action": "Recommended action"
        },
        # Add more rules as needed
    ],
},
```

### Step 2: Verify Column Names

Ensure the Excel file contains:
1. The target KPI column (exact name match)
2. All related counter columns
3. Standard identifier columns (Date, eNodeB Name, Cell Name)

### Step 3: Test the Configuration

1. Run `initialization.py`
2. Select the new KPI from the dropdown
3. Run analysis and verify results

---

## Statistical Methodology

### Degradation Detection

The analyzer compares cell performance between two periods:

1. **Baseline Period**: Reference period for normal performance
2. **Comparison Period**: Period to analyze for degradation

**Degradation Calculation**:

For KPIs where lower is bad (e.g., Traffic, Success Rates):
```
Degradation % = ((Baseline - Comparison) / Baseline) × 100
```

For KPIs where higher is bad (e.g., Failure Rates):
```
Degradation % = ((Comparison - Baseline) / Baseline) × 100
```

### Statistical Significance Testing

The analyzer uses **Welch's t-test** to validate that detected degradations are statistically significant and not due to random variation.

**Test Parameters**:
- **Null Hypothesis (H0)**: No significant difference between baseline and comparison
- **Alternative Hypothesis (H1)**: Significant degradation exists
- **Alpha Level**: 0.05 (5% significance level, configurable)

**Test Conditions**:
- Requires minimum 3 data points in each period
- Uses Welch's t-test (does not assume equal variances)
- Two-tailed test for degradation detection

**Results Interpretation**:
- `p_value < 0.05`: Degradation is statistically significant
- `p_value >= 0.05`: Degradation may be due to normal variation

### Baseline Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Last Week** | Previous 7 days before comparison period | Short-term anomaly detection |
| **4-Week Rolling Average** | Average of same weekdays over 4 weeks | Accounts for weekly patterns |
| **Custom Range** | User-specified start and end dates | Known good performance period |

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Column Not Found Error

**Problem**: "Column 'XXX' not found in data"

**Solutions**:
- Verify column names in Excel match `KPI_Configuration.py` exactly
- Check for extra spaces or special characters
- Use `find_matching_column()` in `clean_excel_and_helpers.py` for fuzzy matching

#### 2. No Degraded Cells Found

**Problem**: Analysis completes but finds no degraded cells

**Solutions**:
- Lower the degradation threshold
- Check if baseline mode is appropriate
- Verify data covers the expected time period
- Ensure comparison days parameter is correct

#### 3. Excel File Loading Errors

**Problem**: "Error reading Excel file"

**Solutions**:
- Ensure file is `.xlsx` or `.xls` format
- Close the file in Excel before loading
- Check if file is corrupted
- Install openpyxl: `pip install openpyxl`

#### 4. Memory Issues with Large Files

**Problem**: Application crashes or freezes with large datasets

**Solutions**:
- Process fewer KPIs at once
- Filter data by date range before analysis
- Increase system memory
- Use 64-bit Python

#### 5. GUI Not Displaying Correctly

**Problem**: UI elements not visible or overlapping

**Solutions**:
- Ensure minimum window size (1150x750)
- Check display scaling settings
- Update tkinter: `pip install --upgrade tk`

---

## Dependencies

### Required Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | >= 1.20.0 | Numerical operations |
| `pandas` | >= 1.3.0 | Data manipulation and analysis |
| `scipy` | >= 1.7.0 | Statistical tests (Welch's t-test) |
| `matplotlib` | >= 3.4.0 | Visualization and charts |
| `openpyxl` | >= 3.0.0 | Excel file reading (.xlsx) |
| `xlrd` | >= 2.0.0 | Excel file reading (.xls) |

### Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `python-docx` | >= 0.8.11 | Word document generation |

### Installing Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install specific package
pip install pandas>=1.3.0
```

---

## Credits

### Development Team

**Musketeers_Team**  
Information Technology Institute (ITI)  
Graduation Project 2026

### Project Information

- **Version**: 2.0 (Flat Modular Structure)
- **Architecture**: 10 independent Python modules
- **Original File**: Preserved at `/home/z/my-project/upload/3-LTE_KPI_Degradation_Analyzer_Enhanced.py`

### Acknowledgments

- Huawei Technologies for KPI naming conventions and counter definitions
- ITI faculty and supervisors for guidance and support
- Open source community for the excellent Python libraries used in this project

---

## Support

For questions, issues, or contributions:
- Review this documentation thoroughly
- Check the troubleshooting section for common issues
- Contact the development team for additional support

---

*Last Updated: June 2026*