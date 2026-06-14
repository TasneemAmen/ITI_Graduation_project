# ============================================================
# LTE KPI Degradation Analyzer - Combined Degraded KPI Analysis
# ============================================================
# This file contains functions for analyzing all KPIs combined.
# ============================================================

import pandas as pd

from KPI_Configuration import KPI_CONFIGS
from main_function_for_selected_kpi import analyze_selected_kpi


def analyze_all_kpis(
    df,
    num_days,
    require_complete_days=True,
    baseline_mode="last_week",
    enable_significance_test=True,
    log_callback=None
):
    """
    Analyze all KPIs defined in KPI_CONFIGS.
    
    Args:
        df: Input DataFrame with KPI data
        num_days: Number of days for recent period
        require_complete_days: Whether to require complete data
        baseline_mode: Baseline calculation mode
        enable_significance_test: Whether to perform t-test
        log_callback: Optional callback for logging
        
    Returns:
        Tuple of (combined_df, outputs_dict, summary_df, quarantine_df, incomplete_df)
        - combined_df: Combined DataFrame with all degraded cells
        - outputs_dict: Dictionary of KPI name -> DataFrame
        - summary_df: Summary DataFrame with KPI statistics
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    outputs = {}
    summary_records = []
    quarantine_frames = []
    incomplete_frames = []
    all_kpi_names = list(KPI_CONFIGS.keys())
    total_kpis = len(all_kpi_names)
    
    for idx, kpi_name in enumerate(all_kpi_names, 1):
        config = KPI_CONFIGS[kpi_name]
        threshold = float(config["default_threshold"])
        
        if log_callback:
            log_msg(f"Analyzing {idx}/{total_kpis}: {kpi_name}")
        
        try:
            output_df, metadata = analyze_selected_kpi(
                df=df,
                selected_kpi_name=kpi_name,
                num_days=num_days,
                degradation_threshold=threshold,
                require_complete_days=require_complete_days,
                baseline_mode=baseline_mode,
                enable_significance_test=enable_significance_test,
                log_callback=log_callback,
            )
            outputs[kpi_name] = output_df

            q = metadata.get("quarantine_df")
            if q is not None and not q.empty:
                quarantine_frames.append(q)
            inc = metadata.get("incomplete_df")
            if inc is not None and not inc.empty:
                incomplete_frames.append(inc)

            debug = metadata.get("debug_info", {})
            degraded_count = output_df.shape[0]
            
            summary_records.append({
                "kpi_name": kpi_name,
                "target_kpi_column": config["target_kpi"],
                "kpi_category": config["category"],
                "threshold_%": threshold,
                "degraded_cells_count": degraded_count,
                "max_degradation_%": debug.get("max_degradation"),
                "mean_degradation_%": debug.get("mean_degradation"),
                "status": "Completed",
                "error": ""
            })
            log_msg(f"{kpi_name}: {degraded_count} degraded cells")
            
        except Exception as e:
            outputs[kpi_name] = pd.DataFrame()
            summary_records.append({
                "kpi_name": kpi_name,
                "target_kpi_column": config.get("target_kpi", ""),
                "kpi_category": config.get("category", ""),
                "threshold_%": threshold,
                "degraded_cells_count": 0,
                "max_degradation_%": None,
                "mean_degradation_%": None,
                "status": "Failed",
                "error": str(e)
            })
            log_msg(f"{kpi_name}: ERROR - {e}")
    
    # Combine results
    non_empty = [df for df in outputs.values() if df is not None and not df.empty]
    combined = pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame()
    summary_df = pd.DataFrame(summary_records)
    quarantine_df = pd.concat(quarantine_frames, ignore_index=True) if quarantine_frames else pd.DataFrame()
    incomplete_df = pd.concat(incomplete_frames, ignore_index=True) if incomplete_frames else pd.DataFrame()

    return combined, outputs, summary_df, quarantine_df, incomplete_df
