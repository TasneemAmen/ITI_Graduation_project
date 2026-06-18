# ============================================================
# LTE KPI Degradation Analyzer - Save Results
# ============================================================
# This file contains functions for saving results to CSV and Excel files.
# ============================================================

import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

from KPI_Configuration import KPI_CONFIGS


def save_csv_results(
    output_df,
    all_outputs,
    summary_df,
    analysis_mode,
    selected_kpi,
    save_path_or_dir,
    log_callback=None,
    quarantine_df=None,
    incomplete_df=None,
    anomalies_df=None,
    clean_cells_df=None,
):
    """
    Save analysis results to CSV files.
    
    Args:
        output_df: Output DataFrame with degraded cells
        all_outputs: Dictionary of KPI name -> DataFrame (for all KPIs mode)
        summary_df: Summary DataFrame
        analysis_mode: "single" or "all"
        selected_kpi: Currently selected KPI name
        save_path_or_dir: File path (single mode) or directory path (all mode)
        log_callback: Optional logging callback
        clean_cells_df: Original data without degraded cells
        
    Returns:
        True if successful, False otherwise
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    if output_df is None and summary_df is None:
        log_msg("ERROR: No output to save")
        return False
    
    if analysis_mode == "all":
        
        # Save to directory
        save_dir = save_path_or_dir
        if not save_dir:
            return False
        
        saved = 0
        for kpi_name, kpi_df in all_outputs.items():
            if kpi_df is not None and not kpi_df.empty:
                prefix = KPI_CONFIGS[kpi_name]["output_prefix"]
                path = os.path.join(save_dir, f"{prefix}_degraded.csv")
                kpi_df.to_csv(path, index=False, encoding="utf-8-sig")
                saved += 1
        
        if output_df is not None and not output_df.empty:
            output_df.to_csv(os.path.join(save_dir, "all_kpis_combined.csv"), index=False, encoding="utf-8-sig")
            saved += 1
        
        if summary_df is not None and not summary_df.empty:
            summary_df.to_csv(os.path.join(save_dir, "summary_report.csv"), index=False, encoding="utf-8-sig")
            saved += 1

        if anomalies_df is not None and not anomalies_df.empty:
            anomalies_df.to_csv(
                os.path.join(save_dir, "anomalies_all.csv"),
                index=False,
                encoding="utf-8-sig"
            )
            saved += 1

            zero_df = anomalies_df[anomalies_df["Anomaly_Type"] == "Zero"]
            if not zero_df.empty:
                zero_df.to_csv(
                    os.path.join(save_dir, "anomalies_zero.csv"),
                    index=False,
                    encoding="utf-8-sig"
                )
                saved += 1

            spike_df = anomalies_df[anomalies_df["Anomaly_Type"] == "Spike"]
            if not spike_df.empty:
                spike_df.to_csv(
                    os.path.join(save_dir, "anomalies_spike.csv"),
                    index=False,
                    encoding="utf-8-sig"
                )
                saved += 1

            summary_rows = [{
                "Total_Anomalies": len(anomalies_df),
                "Zero_Anomalies": int((anomalies_df["Anomaly_Type"] == "Zero").sum()),
                "Spike_Anomalies": int((anomalies_df["Anomaly_Type"] == "Spike").sum()),
                "Critical": int((anomalies_df["Severity"] == "Critical").sum()),
                "High": int((anomalies_df["Severity"] == "High").sum()),
                "Medium": int((anomalies_df["Severity"] == "Medium").sum()),
                "Low": int((anomalies_df["Severity"] == "Low").sum())
            }]

            pd.DataFrame(summary_rows).to_csv(
                os.path.join(save_dir, "anomalies_summary.csv"),
                index=False,
                encoding="utf-8-sig"
            )
            saved += 1

        if clean_cells_df is not None and not clean_cells_df.empty:
            clean_cells_df.to_csv(os.path.join(save_dir, "clean_cells_original_data.csv"), index=False, encoding="utf-8-sig")
            saved += 1
            log_msg(f"Clean cells: {clean_cells_df.shape[0]} normal cell records (original data without degraded)")

        if quarantine_df is not None and not quarantine_df.empty:
            quarantine_df.to_csv(os.path.join(save_dir, "data_quality_quarantine.csv"), index=False, encoding="utf-8-sig")
            saved += 1
            log_msg(f"Quarantine: {quarantine_df.shape[0]} invalid counter value(s) flagged")
        if incomplete_df is not None and not incomplete_df.empty:
            incomplete_df.to_csv(os.path.join(save_dir, "data_quality_incomplete_cells.csv"), index=False, encoding="utf-8-sig")
            saved += 1
            log_msg(f"Incomplete: {incomplete_df.shape[0]} cell-row(s) with missing/insufficient data")
        
        log_msg(f"Saved {saved} files to: {save_dir}")
        return True
    
    # Single KPI mode
    if output_df is None or output_df.empty:
        log_msg("ERROR: No degraded cells to save")
        return False
    
    prefix = KPI_CONFIGS[selected_kpi]["output_prefix"]
    
    output_df.to_csv(save_path_or_dir, index=False, encoding="utf-8-sig")
    log_msg(f"CSV saved: {save_path_or_dir}")

    out_dir = os.path.dirname(os.path.abspath(save_path_or_dir))
    if quarantine_df is not None and not quarantine_df.empty:
        qp = os.path.join(out_dir, f"{prefix}_counter_quarantine.csv")
        quarantine_df.to_csv(qp, index=False, encoding="utf-8-sig")
        log_msg(f"Quarantine CSV saved: {qp} ({quarantine_df.shape[0]} rows)")
    if incomplete_df is not None and not incomplete_df.empty:
        ip = os.path.join(out_dir, f"{prefix}_incomplete_cells.csv")
        incomplete_df.to_csv(ip, index=False, encoding="utf-8-sig")
        log_msg(f"Incomplete-cells CSV saved: {ip} ({incomplete_df.shape[0]} rows)")
    return True


def save_excel_results(
    output_df,
    summary_df,
    analysis_mode,
    selected_kpi,
    excel_file_path,
    log_callback=None,
    anomalies_df=None,
    quarantine_df=None,
    incomplete_df=None,
    clean_cells_df=None,
):
    """
    Save analysis results to an Excel workbook with multiple sheets.
    
    Sheets created:
    1. Combined Degraded - All degraded cells (all KPIs combined)
    2. Clean Cells - Original data without degraded cells
    3. Anomalies - All detected anomalies
    4. Summary Report - Technical professional summary
    5. Data Quality - Quarantine and incomplete data flags
    
    Args:
        output_df: Output DataFrame with degraded cells
        summary_df: Summary DataFrame
        analysis_mode: "single" or "all"
        selected_kpi: Currently selected KPI name
        excel_file_path: Path to save the Excel file
        log_callback: Optional logging callback
        anomalies_df: Anomalies DataFrame
        quarantine_df: Quarantine DataFrame
        incomplete_df: Incomplete cells DataFrame
        clean_cells_df: Original data without degraded cells
        
    Returns:
        True if successful, False otherwise
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    if output_df is None and summary_df is None:
        log_msg("ERROR: No output to save")
        return False
    
    try:
        with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
            # Sheet 1: Combined Degraded Cells
            if output_df is not None and not output_df.empty:
                output_df.to_excel(writer, sheet_name='Combined Degraded', index=False)
                log_msg(f"Sheet 'Combined Degraded': {output_df.shape[0]} records")
            
            # Sheet 2: Clean Cells (Original data without degraded)
            if clean_cells_df is not None and not clean_cells_df.empty:
                clean_cells_df.to_excel(writer, sheet_name='Clean Cells', index=False)
                log_msg(f"Sheet 'Clean Cells': {clean_cells_df.shape[0]} normal cell records")
            
            # Sheet 3: Anomalies
            if anomalies_df is not None and not anomalies_df.empty:
                anomalies_df.to_excel(writer, sheet_name='Anomalies', index=False)
                log_msg(f"Sheet 'Anomalies': {anomalies_df.shape[0]} anomaly records")
            
            # Sheet 4: Summary Report (Technical Professional)
            if summary_df is not None and not summary_df.empty:
                summary_df.to_excel(writer, sheet_name='Summary Report', index=False)
                log_msg(f"Sheet 'Summary Report': {summary_df.shape[0]} KPI summaries")
            
            # Sheet 5: Data Quality
            dq_data = []
            if quarantine_df is not None and not quarantine_df.empty:
                dq_data.append({
                    'Category': 'Quarantine',
                    'Description': 'Invalid counter values flagged',
                    'Count': quarantine_df.shape[0]
                })
            if incomplete_df is not None and not incomplete_df.empty:
                dq_data.append({
                    'Category': 'Incomplete Cells',
                    'Description': 'Rows with missing/insufficient data',
                    'Count': incomplete_df.shape[0]
                })
            
            if dq_data:
                dq_df = pd.DataFrame(dq_data)
                dq_df.to_excel(writer, sheet_name='Data Quality', index=False)
                log_msg(f"Sheet 'Data Quality': {len(dq_data)} data quality issues")
        
        log_msg(f"Excel report saved: {excel_file_path}")
        return True
        
    except Exception as e:
        log_msg(f"ERROR saving Excel: {str(e)}")
        return False
