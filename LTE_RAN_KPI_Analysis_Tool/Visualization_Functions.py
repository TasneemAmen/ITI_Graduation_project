# ============================================================
# LTE KPI Degradation Analyzer - Visualization Functions
# ============================================================
# This file contains functions for dashboard and chart visualization.
# ============================================================

import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from KPI_Configuration import (
    DATE_COL,
    SITE_COL,
    CELL_COL,
    KPI_CONFIGS,
)
from clean_excel_and_helpers import find_matching_column


def show_dashboard(parent_window, output_df, summary_df, analysis_mode, selected_kpi):
    """
    Show the degradation dashboard window.
    
    Args:
        parent_window: Parent Tkinter window
        output_df: Output DataFrame with degraded cells
        summary_df: Summary DataFrame (for all KPIs mode)
        analysis_mode: "single" or "all"
        selected_kpi: Currently selected KPI name
    """
    if output_df is None and summary_df is None:
        return
    
    dash = tk.Toplevel(parent_window)
    dash.title("LTE KPI Degradation Dashboard")
    dash.geometry("1200x760")
    
    main_frame = ttk.Frame(dash, padding=10)
    main_frame.pack(fill="both", expand=True)
    
    ttk.Label(main_frame, text="LTE KPI Degradation Dashboard", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))
    
    metrics_frame = ttk.LabelFrame(main_frame, text="Summary Metrics", padding=10)
    metrics_frame.pack(fill="x", pady=(0, 10))
    
    charts_frame = ttk.Frame(main_frame)
    charts_frame.pack(fill="both", expand=True)
    
    left_chart = ttk.LabelFrame(charts_frame, text="Degraded Cells per KPI", padding=10)
    left_chart.pack(side="left", fill="both", expand=True, padx=(0, 5))
    
    right_chart = ttk.LabelFrame(charts_frame, text="Root Cause Distribution", padding=10)
    right_chart.pack(side="right", fill="both", expand=True, padx=(5, 0))
    
    # Metrics
    if analysis_mode == "all" and summary_df is not None:
        total_kpis = summary_df.shape[0]
        total_degraded = int(summary_df["degraded_cells_count"].sum()) if "degraded_cells_count" in summary_df.columns else 0
        metrics = [("Mode", "All KPIs"), ("KPIs", total_kpis), ("Total Degraded", total_degraded)]
    else:
        total_degraded = output_df.shape[0] if output_df is not None else 0
        metrics = [("Mode", "Single KPI"), ("KPI", selected_kpi), ("Degraded", total_degraded)]
    
    for i, (name, val) in enumerate(metrics):
        box = ttk.LabelFrame(metrics_frame, text=name, padding=5)
        box.grid(row=0, column=i, sticky="nsew", padx=5)
        ttk.Label(box, text=str(val), font=("Arial", 11, "bold")).pack()
        metrics_frame.columnconfigure(i, weight=1)
    
    # Charts
    fig1 = Figure(figsize=(5, 4), dpi=100)
    ax1 = fig1.add_subplot(111)
    
    if analysis_mode == "all" and summary_df is not None and "degraded_cells_count" in summary_df.columns:
        plot_df = summary_df.sort_values("degraded_cells_count", ascending=False).head(12)
        ax1.bar(plot_df["kpi_name"], plot_df["degraded_cells_count"])
        ax1.set_title("Degraded Cells per KPI")
        ax1.tick_params(axis="x", rotation=70)
    else:
        ax1.text(0.5, 0.5, "No data", ha="center")
    
    fig1.tight_layout()
    canvas1 = FigureCanvasTkAgg(fig1, master=left_chart)
    canvas1.draw()
    canvas1.get_tk_widget().pack(fill="both", expand=True)
    
    fig2 = Figure(figsize=(5, 4), dpi=100)
    ax2 = fig2.add_subplot(111)
    
    if output_df is not None and not output_df.empty and "main_root_cause_category" in output_df.columns:
        causes = output_df["main_root_cause_category"].value_counts().head(10).sort_values()
        ax2.barh(causes.index, causes.values)
        ax2.set_title("Root Causes")
    else:
        ax2.text(0.5, 0.5, "No data", ha="center")
    
    fig2.tight_layout()
    canvas2 = FigureCanvasTkAgg(fig2, master=right_chart)
    canvas2.draw()
    canvas2.get_tk_widget().pack(fill="both", expand=True)


def show_trend_dashboard(parent_window, original_df, output_df, degraded_cell_ids, selected_kpi, log_callback=None):
    """
    Show the trend analysis dashboard window.
    
    Args:
        parent_window: Parent Tkinter window
        original_df: Original input DataFrame
        output_df: Output DataFrame with degraded cells
        degraded_cell_ids: Set of degraded cell IDs
        selected_kpi: Currently selected KPI name
        log_callback: Optional logging callback
    """
    if original_df is None:
        if log_callback:
            log_callback("No data loaded")
        return
    
    if output_df is None or output_df.empty:
        if log_callback:
            log_callback("No degraded cells found")
        return
    
    trend_win = tk.Toplevel(parent_window)
    trend_win.title("KPI Trend - Before vs After Degradation Removal")
    trend_win.geometry("1300x800")
    
    main_frame = ttk.Frame(trend_win, padding=10)
    main_frame.pack(fill="both", expand=True)
    
    ttk.Label(main_frame, text="KPI Trend Analysis - Before vs After Degraded Cell Removal",
              font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))
    
    # Controls
    controls = ttk.Frame(main_frame)
    controls.pack(fill="x", pady=(0, 10))
    
    ttk.Label(controls, text="Select KPI:").pack(side="left", padx=5)
    
    config = KPI_CONFIGS.get(selected_kpi, {})
    target_kpi = config.get("target_kpi", "")
    kpi_col = find_matching_column(original_df, target_kpi)
    
    numeric_cols = original_df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in [SITE_COL, CELL_COL]]
    
    trend_kpi = tk.StringVar(value=kpi_col if kpi_col else (numeric_cols[0] if numeric_cols else ""))
    ttk.Combobox(controls, textvariable=trend_kpi, values=numeric_cols[:30], state="readonly", width=50).pack(side="left", padx=5)
    
    chart_frame = ttk.LabelFrame(main_frame, text="Trend Chart", padding=10)
    chart_frame.pack(fill="both", expand=True, pady=5)
    
    def draw_chart():
        for w in chart_frame.winfo_children():
            w.destroy()
        
        col = trend_kpi.get()
        if not col or col not in original_df.columns:
            ttk.Label(chart_frame, text="Invalid KPI column").pack()
            return
        
        df = original_df.copy()
        
        if DATE_COL not in df.columns:
            ttk.Label(chart_frame, text="Date column not found").pack()
            return
        
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors='coerce')
        df = df.dropna(subset=[DATE_COL])
        
        # Before: all cells
        daily_before = df.groupby(DATE_COL)[col].mean().reset_index()
        daily_before.columns = ['Date', 'Average']
        
        # After: remove degraded cells
        if degraded_cell_ids:
            mask = df.set_index([SITE_COL, CELL_COL]).index.isin(degraded_cell_ids)
            df_clean = df[~mask]
            daily_after = df_clean.groupby(DATE_COL)[col].mean().reset_index() if len(df_clean) > 0 else daily_before.copy()
            daily_after.columns = ['Date', 'Average']
        else:
            daily_after = daily_before.copy()
        
        if daily_before.empty:
            ttk.Label(chart_frame, text="No data to plot").pack()
            return
        
        fig = Figure(figsize=(12, 5), dpi=100)
        ax = fig.add_subplot(111)
        
        dates = daily_before['Date'].tolist()
        x = range(len(dates))
        labels = [d.strftime('%m/%d') if hasattr(d, 'strftime') else str(d)[:10] for d in dates]
        
        ax.plot(x, daily_before['Average'].values, 'b-o', linewidth=2, markersize=6, label='Before (All Cells)')
        ax.plot(x, daily_after['Average'].values, 'g-s', linewidth=2, markersize=6, label='After (Clean Cells)')
        
        if degraded_cell_ids:
            diff = daily_before['Average'].values - daily_after['Average'].values
            ax.fill_between(x, daily_before['Average'].values, daily_after['Average'].values,
                           where=diff != 0, alpha=0.3, color='red', label='Degraded Impact')
        
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        ax.set_xlabel('Date')
        ax.set_ylabel(col[:40])
        ax.set_title(f'{col[:40]} - Daily Trend')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    ttk.Button(controls, text="Update Chart", command=draw_chart).pack(side="left", padx=10)
    
    # Legend
    legend_frame = ttk.Frame(main_frame)
    legend_frame.pack(fill="x", pady=5)
    ttk.Label(legend_frame, text="■", foreground='blue', font=('Arial', 12)).pack(side="left", padx=2)
    ttk.Label(legend_frame, text="Before Removal (All Cells)").pack(side="left", padx=(0, 20))
    ttk.Label(legend_frame, text="■", foreground='green', font=('Arial', 12)).pack(side="left", padx=2)
    ttk.Label(legend_frame, text="After Removal (Clean Cells)").pack(side="left", padx=(0, 20))
    ttk.Label(legend_frame, text="■", foreground='red', font=('Arial', 12)).pack(side="left", padx=2)
    ttk.Label(legend_frame, text="Degraded Impact").pack(side="left")
    
    draw_chart()
