# ============================================================
# LTE KPI Degradation Analyzer - Combined Degraded KPI Analysis
# ============================================================
# This file contains functions for analyzing all KPIs combined
# and removing degraded cells from the dataset for clean dashboard views.
#
# The per-KPI degradation is computed in main_function_for_selected_kpi.py
# using the MEDIAN of per-day degradations (robust to spike days) and
# SAME-WEEKDAY historical baseline fallback (per-weekday medians, not pooled).
# ============================================================

import pandas as pd

from KPI_Configuration import KPI_CONFIGS, CELL_ID_COLS, SITE_COL, CELL_COL, DATE_COL
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


# ============================================================
# REMOVE DEGRADED CELLS FROM DATASET
# ============================================================

def remove_degraded_cells(
    df,
    degraded_df,
    remove_mode="all_periods",
    kpi_filter=None,
    cell_id_cols=None,
    log_callback=None
):
    """
    Remove degraded cells from the dataset for clean dashboard visualization.
    
    Args:
        df: Original DataFrame with all cell data
        degraded_df: DataFrame with degraded cells (from analyze_all_kpis or analyze_selected_kpi)
        remove_mode: How to remove degraded cells:
            - "all_periods": Remove all data for degraded cells (all dates)
            - "recent_only": Remove only recent period data for degraded cells
            - "degraded_period_only": Remove only dates where degradation was detected
        kpi_filter: List of KPI names to filter by (None = all KPIs)
        cell_id_cols: Columns that identify a cell (default: CELL_ID_COLS)
        log_callback: Optional callback for logging
        
    Returns:
        Tuple of (clean_df, removed_cells_count, removal_summary)
        - clean_df: DataFrame with degraded cells removed
        - removed_cells_count: Number of cell records removed
        - removal_summary: Dict with removal statistics
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    if cell_id_cols is None:
        cell_id_cols = CELL_ID_COLS
    
    df = df.copy()
    
    # Handle empty degraded_df
    if degraded_df is None or degraded_df.empty:
        log_msg("No degraded cells to remove")
        return df, 0, {"removed_cells": 0, "removed_records": 0}
    
    # Filter by KPI if specified
    if kpi_filter:
        if isinstance(kpi_filter, str):
            kpi_filter = [kpi_filter]
        degraded_df = degraded_df[degraded_df["selected_kpi_name"].isin(kpi_filter)]
        if degraded_df.empty:
            log_msg(f"No degraded cells found for KPIs: {kpi_filter}")
            return df, 0, {"removed_cells": 0, "removed_records": 0, "kpi_filter": kpi_filter}
    
    # Get unique degraded cells
    degraded_cells = degraded_df[cell_id_cols].drop_duplicates()
    n_degraded_cells = len(degraded_cells)
    
    log_msg(f"Removing {n_degraded_cells} degraded cells from dataset (mode: {remove_mode})")
    
    original_count = len(df)
    
    if remove_mode == "all_periods":
        # Remove all data for degraded cells (all dates)
        # Create a merge key to identify cells to remove
        df["_tmp_key"] = df[cell_id_cols].apply(lambda x: tuple(x), axis=1)
        degraded_cells["_tmp_key"] = degraded_cells[cell_id_cols].apply(lambda x: tuple(x), axis=1)
        
        keys_to_remove = set(degraded_cells["_tmp_key"].tolist())
        clean_df = df[~df["_tmp_key"].isin(keys_to_remove)].drop(columns=["_tmp_key"])
        
        # Clean up
        degraded_cells = degraded_cells.drop(columns=["_tmp_key"], errors="ignore")
        
    elif remove_mode == "recent_only":
        # Remove only recent period data for degraded cells
        # Need to identify recent period from degraded_df
        if "recent_period" in degraded_df.columns:
            recent_period = degraded_df["recent_period"].iloc[0]
            # Parse the period string (format: "YYYY-MM-DD to YYYY-MM-DD")
            try:
                parts = recent_period.split(" to ")
                recent_start = pd.to_datetime(parts[0])
                recent_end = pd.to_datetime(parts[1])
                
                # Add date column parsing
                df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
                
                # Create merge key
                df["_tmp_key"] = df[cell_id_cols].apply(lambda x: tuple(x), axis=1)
                degraded_cells["_tmp_key"] = degraded_cells[cell_id_cols].apply(lambda x: tuple(x), axis=1)
                
                keys_to_remove = set(degraded_cells["_tmp_key"].tolist())
                
                # Remove only recent period data for degraded cells
                is_recent = (df[DATE_COL] >= recent_start) & (df[DATE_COL] <= recent_end)
                is_degraded_cell = df["_tmp_key"].isin(keys_to_remove)
                
                clean_df = df[~(is_recent & is_degraded_cell)].drop(columns=["_tmp_key"])
                
            except Exception as e:
                log_msg(f"Warning: Could not parse recent period, falling back to all_periods mode: {e}")
                # Fallback to all_periods
                df["_tmp_key"] = df[cell_id_cols].apply(lambda x: tuple(x), axis=1)
                degraded_cells["_tmp_key"] = degraded_cells[cell_id_cols].apply(lambda x: tuple(x), axis=1)
                keys_to_remove = set(degraded_cells["_tmp_key"].tolist())
                clean_df = df[~df["_tmp_key"].isin(keys_to_remove)].drop(columns=["_tmp_key"])
        else:
            log_msg("Warning: recent_period not found in degraded_df, using all_periods mode")
            df["_tmp_key"] = df[cell_id_cols].apply(lambda x: tuple(x), axis=1)
            degraded_cells["_tmp_key"] = degraded_cells[cell_id_cols].apply(lambda x: tuple(x), axis=1)
            keys_to_remove = set(degraded_cells["_tmp_key"].tolist())
            clean_df = df[~df["_tmp_key"].isin(keys_to_remove)].drop(columns=["_tmp_key"])
            
    else:
        # Default to all_periods
        df["_tmp_key"] = df[cell_id_cols].apply(lambda x: tuple(x), axis=1)
        degraded_cells["_tmp_key"] = degraded_cells[cell_id_cols].apply(lambda x: tuple(x), axis=1)
        keys_to_remove = set(degraded_cells["_tmp_key"].tolist())
        clean_df = df[~df["_tmp_key"].isin(keys_to_remove)].drop(columns=["_tmp_key"])
    
    removed_count = original_count - len(clean_df)
    
    removal_summary = {
        "removed_cells": n_degraded_cells,
        "removed_records": removed_count,
        "remove_mode": remove_mode,
        "original_records": original_count,
        "remaining_records": len(clean_df),
        "kpi_filter": kpi_filter if kpi_filter else "all_kpis"
    }
    
    log_msg(f"Removed {removed_count} records ({n_degraded_cells} cells)")
    
    return clean_df, removed_count, removal_summary


def remove_degraded_cells_by_kpi(
    df,
    degraded_outputs_dict,
    kpi_names=None,
    remove_mode="all_periods",
    cell_id_cols=None,
    log_callback=None
):
    """
    Remove degraded cells from dataset based on specific KPIs.
    
    This is a convenience function that takes the outputs_dict from analyze_all_kpis
    and removes cells degraded in specified KPIs.
    
    Args:
        df: Original DataFrame with all cell data
        degraded_outputs_dict: Dictionary of KPI name -> degraded cells DataFrame
        kpi_names: List of KPI names to consider (None = all KPIs)
        remove_mode: How to remove degraded cells (see remove_degraded_cells)
        cell_id_cols: Columns that identify a cell
        log_callback: Optional callback for logging
        
    Returns:
        Tuple of (clean_df, total_removed, removal_summary_dict)
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    if cell_id_cols is None:
        cell_id_cols = CELL_ID_COLS
    
    if kpi_names is None:
        kpi_names = list(degraded_outputs_dict.keys())
    
    # Combine degraded cells from specified KPIs
    degraded_frames = []
    for kpi_name in kpi_names:
        if kpi_name in degraded_outputs_dict:
            deg_df = degraded_outputs_dict[kpi_name]
            if deg_df is not None and not deg_df.empty:
                degraded_frames.append(deg_df)
    
    if not degraded_frames:
        log_msg("No degraded cells found for specified KPIs")
        return df.copy(), 0, {"total_removed": 0, "by_kpi": {}}
    
    combined_degraded = pd.concat(degraded_frames, ignore_index=True)
    
    # Get unique degraded cells across all KPIs
    unique_degraded_cells = combined_degraded[cell_id_cols].drop_duplicates()
    
    # Remove using the main function
    clean_df, removed_count, removal_summary = remove_degraded_cells(
        df=df,
        degraded_df=combined_degraded,
        remove_mode=remove_mode,
        kpi_filter=None,  # Already filtered
        cell_id_cols=cell_id_cols,
        log_callback=log_callback
    )
    
    # Add per-KPI breakdown
    kpi_breakdown = {}
    for kpi_name in kpi_names:
        if kpi_name in degraded_outputs_dict:
            deg_df = degraded_outputs_dict[kpi_name]
            if deg_df is not None and not deg_df.empty:
                kpi_breakdown[kpi_name] = len(deg_df[cell_id_cols].drop_duplicates())
    
    removal_summary["by_kpi"] = kpi_breakdown
    
    return clean_df, removed_count, removal_summary


def get_clean_data_for_dashboard(
    df,
    num_days,
    kpi_names=None,
    baseline_mode="last_week",
    remove_mode="all_periods",
    enable_significance_test=True,
    log_callback=None
):
    """
    Complete workflow: Analyze all KPIs, identify degraded cells, and return clean data.
    
    This is a convenience function that combines analyze_all_kpis and remove_degraded_cells
    for easy dashboard integration.
    
    Args:
        df: Original DataFrame with all cell data
        num_days: Number of days for recent period
        kpi_names: List of KPI names to analyze (None = all KPIs)
        baseline_mode: Baseline calculation mode
        remove_mode: How to remove degraded cells
        enable_significance_test: Whether to perform t-test
        log_callback: Optional callback for logging
        
    Returns:
        Dict with:
        - clean_df: DataFrame with degraded cells removed
        - degraded_cells_df: All degraded cells found
        - summary_df: Summary of KPI analysis
        - removal_summary: Summary of removal operation
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    log_msg("Starting clean data generation for dashboard...")
    
    # Analyze all KPIs
    combined_degraded, outputs_dict, summary_df, quarantine_df, incomplete_df = analyze_all_kpis(
        df=df,
        num_days=num_days,
        baseline_mode=baseline_mode,
        enable_significance_test=enable_significance_test,
        log_callback=log_msg
    )
    
    # Filter KPIs if specified
    if kpi_names:
        combined_degraded = combined_degraded[combined_degraded["selected_kpi_name"].isin(kpi_names)]
    
    # Remove degraded cells
    clean_df, removed_count, removal_summary = remove_degraded_cells(
        df=df,
        degraded_df=combined_degraded,
        remove_mode=remove_mode,
        log_callback=log_msg
    )
    
    log_msg(f"Clean data ready: {len(clean_df)} records remaining")
    
    return {
        "clean_df": clean_df,
        "degraded_cells_df": combined_degraded,
        "summary_df": summary_df,
        "quarantine_df": quarantine_df,
        "incomplete_df": incomplete_df,
        "removal_summary": removal_summary,
        "outputs_by_kpi": outputs_dict,
    }


def get_clean_sheet_without_degraded_cells(
    df,
    num_days,
    baseline_mode="last_week",
    enable_significance_test=True,
    log_callback=None
):
    """
    Get the original input sheet with ALL degraded cells removed (for all 13 KPIs).
    
    This function:
    1. Analyzes all 13 KPIs to find degraded cells
    2. Collects ALL unique degraded cells across all KPIs
    3. Returns the original sheet structure with ONLY normal (non-degraded) cells
    
    The output has the SAME structure as the input - just with degraded cells filtered out.
    Use this for dashboard visualizations where you want to show trends without degraded cells.
    
    Args:
        df: Original DataFrame with all cell data (full sheet structure)
        num_days: Number of days for recent period
        baseline_mode: Baseline calculation mode ("last_week" or "4week_rolling_avg")
        enable_significance_test: Whether to perform t-test
        log_callback: Optional callback for logging
        
    Returns:
        Dict with:
        - clean_sheet: DataFrame with SAME structure as input, but degraded cells removed
        - degraded_cells_list: DataFrame listing all unique degraded cells removed
        - summary: Summary statistics
        - analysis_results: Full analysis results (degraded cells per KPI, etc.)
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    log_msg("=" * 50)
    log_msg("Analyzing all 13 KPIs to identify degraded cells...")
    log_msg("=" * 50)
    
    # Step 1: Analyze all KPIs
    combined_degraded, outputs_dict, summary_df, quarantine_df, incomplete_df = analyze_all_kpis(
        df=df,
        num_days=num_days,
        baseline_mode=baseline_mode,
        enable_significance_test=enable_significance_test,
        log_callback=log_msg
    )
    
    # Step 2: Get unique degraded cells across ALL KPIs
    if combined_degraded.empty:
        log_msg("No degraded cells found - returning original sheet")
        return {
            "clean_sheet": df.copy(),
            "degraded_cells_list": pd.DataFrame(columns=CELL_ID_COLS),
            "summary": {
                "total_cells": len(df[CELL_ID_COLS].drop_duplicates()),
                "degraded_cells": 0,
                "remaining_cells": len(df[CELL_ID_COLS].drop_duplicates()),
                "original_records": len(df),
                "remaining_records": len(df),
            },
            "analysis_results": {
                "degraded_per_kpi": {},
                "summary_df": summary_df,
                "outputs_by_kpi": outputs_dict,
            }
        }
    
    # Get unique degraded cells (a cell is degraded if it's degraded in ANY KPI)
    degraded_cells_list = combined_degraded[CELL_ID_COLS].drop_duplicates()
    n_degraded = len(degraded_cells_list)
    
    log_msg(f"Found {n_degraded} unique degraded cells across all KPIs")
    
    # Step 3: Create clean sheet by removing ALL degraded cells
    # Use tuple keys for matching
    df_copy = df.copy()
    df_copy["_tmp_key"] = df_copy[CELL_ID_COLS].apply(lambda x: tuple(x), axis=1)
    degraded_cells_list["_tmp_key"] = degraded_cells_list[CELL_ID_COLS].apply(lambda x: tuple(x), axis=1)
    
    keys_to_remove = set(degraded_cells_list["_tmp_key"].tolist())
    
    # Filter out degraded cells
    clean_sheet = df_copy[~df_copy["_tmp_key"].isin(keys_to_remove)].drop(columns=["_tmp_key"])
    
    # Clean up
    degraded_cells_list = degraded_cells_list.drop(columns=["_tmp_key"], errors="ignore")
    
    # Step 4: Calculate summary statistics
    original_cells = len(df[CELL_ID_COLS].drop_duplicates())
    remaining_cells = len(clean_sheet[CELL_ID_COLS].drop_duplicates())
    original_records = len(df)
    remaining_records = len(clean_sheet)
    
    # Degraded cells per KPI
    degraded_per_kpi = {}
    for kpi_name, kpi_df in outputs_dict.items():
        if kpi_df is not None and not kpi_df.empty:
            degraded_per_kpi[kpi_name] = len(kpi_df[CELL_ID_COLS].drop_duplicates())
        else:
            degraded_per_kpi[kpi_name] = 0
    
    log_msg("-" * 50)
    log_msg(f"Clean sheet generated:")
    log_msg(f"  Original: {original_cells} cells, {original_records} records")
    log_msg(f"  Removed:  {n_degraded} degraded cells, {original_records - remaining_records} records")
    log_msg(f"  Remaining: {remaining_cells} cells, {remaining_records} records")
    log_msg("-" * 50)
    
    return {
        "clean_sheet": clean_sheet,
        "degraded_cells_list": degraded_cells_list,
        "summary": {
            "total_cells": original_cells,
            "degraded_cells": n_degraded,
            "remaining_cells": remaining_cells,
            "original_records": original_records,
            "remaining_records": remaining_records,
            "removed_records": original_records - remaining_records,
        },
        "analysis_results": {
            "degraded_per_kpi": degraded_per_kpi,
            "summary_df": summary_df,
            "outputs_by_kpi": outputs_dict,
            "combined_degraded": combined_degraded,
        }
    }


def export_clean_sheet_to_excel(
    df,
    num_days,
    output_path,
    baseline_mode="last_week",
    enable_significance_test=True,
    include_summary=True,
    log_callback=None
):
    """
    Analyze all KPIs, remove degraded cells, and export clean sheet to Excel.
    
    This is a convenience function that:
    1. Gets clean sheet without degraded cells
    2. Exports to Excel with optional summary sheets
    
    Args:
        df: Original DataFrame with all cell data
        num_days: Number of days for recent period
        output_path: Path to save the Excel file
        baseline_mode: Baseline calculation mode
        enable_significance_test: Whether to perform t-test
        include_summary: Include summary sheets in Excel
        log_callback: Optional callback for logging
        
    Returns:
        Dict with file path and summary information
    """
    def log_msg(msg):
        if log_callback:
            log_callback(msg)
    
    # Get clean sheet
    result = get_clean_sheet_without_degraded_cells(
        df=df,
        num_days=num_days,
        baseline_mode=baseline_mode,
        enable_significance_test=enable_significance_test,
        log_callback=log_msg
    )
    
    clean_sheet = result["clean_sheet"]
    summary = result["summary"]
    
    # Export to Excel
    if include_summary:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Clean data sheet
            clean_sheet.to_excel(writer, sheet_name='Clean_Data', index=False)
            
            # Degraded cells list
            result["degraded_cells_list"].to_excel(writer, sheet_name='Degraded_Cells', index=False)
            
            # Summary sheet
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Degraded per KPI
            degraded_per_kpi = result["analysis_results"]["degraded_per_kpi"]
            kpi_summary = pd.DataFrame([
                {"KPI": kpi, "Degraded_Cells": count}
                for kpi, count in degraded_per_kpi.items()
            ])
            kpi_summary.to_excel(writer, sheet_name='Degraded_Per_KPI', index=False)
    else:
        clean_sheet.to_excel(output_path, index=False)
    
    log_msg(f"Clean sheet exported to: {output_path}")
    
    return {
        "output_path": output_path,
        "summary": summary,
        "records_exported": len(clean_sheet),
    }
