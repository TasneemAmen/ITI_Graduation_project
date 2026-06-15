# ============================================================
# LTE KPI Degradation Analyzer - Save Results
# ============================================================
# This file contains functions for saving results to CSV files.
# ============================================================

import os
import pandas as pd

from KPI_Configuration import KPI_CONFIGS


def save_csv_results(output_df, all_outputs, summary_df, analysis_mode, selected_kpi, 
                      save_path_or_dir, log_callback=None,
                      quarantine_df=None, incomplete_df=None):
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
