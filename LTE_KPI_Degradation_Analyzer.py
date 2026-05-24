# ============================================================
# LTE KPI Degradation Analyzer - Desktop GUI Version
# ============================================================

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd


# ============================================================
# 1. GLOBAL COLUMN NAMES
# ============================================================
# Edit only if your Excel column names change.
# ============================================================

DATE_COL = "Date"
SITE_COL = "eNodeB Name"
CELL_COL = "Cell Name"
LOCAL_CELL_COL = "LocalCell Id"
# We will NOT use Cluster in grouping because it has missing/None values.
# Using Cluster can remove valid cells or break matching between periods.

CELL_ID_COLS = [
    SITE_COL,
    CELL_COL,
    LOCAL_CELL_COL,
]


# ============================================================
# 2. KPI CONFIGURATION
# ============================================================
# This is the main section you will edit later.
# Each KPI has:
# - target_kpi: exact column name in Excel
# - bad_direction: low/high
# - default_threshold: default degradation threshold
# - output_prefix: CSV file prefix
# - related_rules: counters used to explain degradation
# ============================================================

KPI_CONFIGS = {
    "DL Traffic": {
        "target_kpi": "(HU) DL Traffic Volume (GBytes)",
        "bad_direction": "low",
        "default_threshold": 30.0,
        "category": "Traffic",
        "output_prefix": "dl_traffic",
        "related_rules": [
            {"feature": "(HU) Cell DL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "category": "DL Throughput Degradation", "reason": "Cell DL throughput decreased.", "recommended_action": "Check DL scheduler, bandwidth, CA activation, load balancing, and congestion."},
            {"feature": "(HU) User DL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "category": "User Throughput Degradation", "reason": "User DL throughput decreased.", "recommended_action": "Check radio quality, PRB load, scheduler behavior, and user distribution."},
            {"feature": "(HU) DL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "category": "Capacity / Congestion", "reason": "DL PRB utilization increased.", "recommended_action": "Check load balancing, CA usage, bandwidth, traffic distribution, and capacity expansion."},
            {"feature": "DL Average CQI", "bad_direction": "low", "threshold": 15, "category": "Radio Quality Issue", "reason": "DL CQI decreased.", "recommended_action": "Check interference, PCI conflict/confusion, antenna tilt, azimuth, and coverage."},
            {"feature": "(HU) DL IBLER(%)", "bad_direction": "high", "threshold": 20, "category": "DL Radio Quality Issue", "reason": "DL IBLER increased.", "recommended_action": "Check interference, CQI, MCS, antenna tilt, and DL power."},
            {"feature": "DL RBLER", "bad_direction": "high", "threshold": 20, "category": "DL Radio Failure", "reason": "DL RBLER increased.", "recommended_action": "Check DL interference, poor coverage, CQI, MCS, and radio conditions."},
            {"feature": "(HU) PDSCH MCS", "bad_direction": "low", "threshold": 15, "category": "Poor Modulation Efficiency", "reason": "PDSCH MCS decreased.", "recommended_action": "Check CQI, SINR, interference, antenna direction, and coverage."},
            {"feature": "Availability", "bad_direction": "low", "threshold": 1, "category": "Availability Issue", "reason": "Cell availability decreased.", "recommended_action": "Check alarms, S1 issue, manual outage, system outage, and site availability."},
            {"feature": "(HU) Cell Unavail Time (s)", "bad_direction": "high", "threshold": 20, "category": "Cell Unavailability", "reason": "Cell unavailable time increased.", "recommended_action": "Check site outage, power issue, transmission issue, S1 failure, and alarms."},
            {"feature": "L.Traffic.ActiveUser.Dl.Avg", "bad_direction": "low", "threshold": 20, "category": "Traffic Demand Drop", "reason": "DL active users decreased.", "recommended_action": "Validate if traffic drop is normal demand behavior before RF optimization."},
            {"feature": "MAC CA Traffic Ratio", "bad_direction": "low", "threshold": 20, "category": "Carrier Aggregation Issue", "reason": "CA traffic ratio decreased.", "recommended_action": "Check CA activation, SCell availability, CA bands, and CA parameters."},
            {"feature": "DL Traffic QCI-9", "bad_direction": "low", "threshold": 20, "category": "Default Bearer Traffic Drop", "reason": "QCI-9 DL traffic decreased.", "recommended_action": "Check packet data service, APN/data service, user demand, and internet traffic trend."},
            {"feature": "DL_CCE_AllocFail (%)", "bad_direction": "high", "threshold": 20, "category": "Control Channel Congestion", "reason": "DL CCE allocation failure increased.", "recommended_action": "Check PDCCH/CCE utilization, control channel capacity, and scheduler configuration."},
        ],
    },

    "UL Traffic": {
        "target_kpi": "(HU) UL Traffic Volume (GBytes)",
        "bad_direction": "low",
        "default_threshold": 30.0,
        "category": "Traffic",
        "output_prefix": "ul_traffic",
        "related_rules": [
            {"feature": "(HU) Cell UL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "category": "UL Throughput Degradation", "reason": "Cell UL throughput decreased.", "recommended_action": "Check UL scheduler, UL PRB utilization, uplink interference, and power control."},
            {"feature": "(HU) User UL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "category": "UL User Throughput Degradation", "reason": "User UL throughput decreased.", "recommended_action": "Check UL radio quality, UL interference, PUSCH MCS, and UL PRB load."},
            {"feature": "(HU)UL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "category": "UL Capacity / Congestion", "reason": "UL PRB utilization increased.", "recommended_action": "Check UL capacity, UL scheduling, uplink load, and traffic distribution."},
            {"feature": "(HU) Avg UL Interference(dBm)", "bad_direction": "high", "threshold": 10, "category": "UL Interference Issue", "reason": "Average UL interference increased.", "recommended_action": "Check external interference, PIM, neighboring cells, and uplink noise rise."},
            {"feature": "L.UpPTS.Interference.Avg(dBm)", "bad_direction": "high", "threshold": 10, "category": "UL Interference Issue", "reason": "UpPTS interference increased.", "recommended_action": "Check uplink interference source and TDD interference conditions."},
            {"feature": "(HU) UL IBLER(%)", "bad_direction": "high", "threshold": 20, "category": "UL Radio Quality Issue", "reason": "UL IBLER increased.", "recommended_action": "Check UL interference, PUSCH MCS, UE power, and coverage."},
            {"feature": "UL RBLER", "bad_direction": "high", "threshold": 20, "category": "UL Radio Failure", "reason": "UL RBLER increased.", "recommended_action": "Check UL interference, coverage, UE power, and uplink radio conditions."},
            {"feature": "(HU) PUSCH MCS", "bad_direction": "low", "threshold": 15, "category": "UL Modulation Efficiency Issue", "reason": "PUSCH MCS decreased.", "recommended_action": "Check UL SINR, interference, UE power control, and uplink coverage."},
            {"feature": "L.Traffic.ActiveUser.UL.Avg", "bad_direction": "low", "threshold": 20, "category": "UL Traffic Demand Drop", "reason": "UL active users decreased.", "recommended_action": "Validate traffic trend before applying RF action."},
        ],
    },

    "DL Throughput": {
        "target_kpi": "(HU) User DL Average Throughput (Mbps)",
        "bad_direction": "low",
        "default_threshold": 20.0,
        "category": "Integrity",
        "output_prefix": "dl_throughput",
        "related_rules": [
            {"feature": "(HU) DL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "category": "DL Congestion", "reason": "DL PRB utilization increased while DL throughput decreased.", "recommended_action": "Check congestion, load balancing, CA, bandwidth, scheduler, and capacity expansion."},
            {"feature": "DL Average CQI", "bad_direction": "low", "threshold": 15, "category": "Poor Radio Quality", "reason": "CQI decreased while DL throughput degraded.", "recommended_action": "Check interference, PCI, antenna tilt, azimuth, and coverage."},
            {"feature": "(HU) DL IBLER(%)", "bad_direction": "high", "threshold": 20, "category": "High DL Retransmission", "reason": "DL IBLER increased while DL throughput degraded.", "recommended_action": "Check BLER, CQI, MCS, DL power, and interference."},
            {"feature": "DL RBLER", "bad_direction": "high", "threshold": 20, "category": "DL Radio Block Errors", "reason": "DL RBLER increased while DL throughput degraded.", "recommended_action": "Check interference, radio quality, and coverage."},
            {"feature": "(HU) PDSCH MCS", "bad_direction": "low", "threshold": 15, "category": "Low DL Modulation", "reason": "PDSCH MCS decreased while DL throughput degraded.", "recommended_action": "Check CQI, SINR, interference, and coverage."},
            {"feature": "MAC CA Traffic Ratio", "bad_direction": "low", "threshold": 20, "category": "Low CA Usage", "reason": "CA traffic ratio decreased while DL throughput degraded.", "recommended_action": "Check CA activation, SCell availability, and CA configuration."},
            {"feature": "L.Traffic.ActiveUser.Dl.Avg", "bad_direction": "high", "threshold": 20, "category": "High User Load", "reason": "DL active users increased while DL throughput decreased.", "recommended_action": "Check load, scheduling, congestion, and user distribution."},
        ],
    },

    "UL Throughput": {
        "target_kpi": "(HU) User UL Average Throughput (Mbps)",
        "bad_direction": "low",
        "default_threshold": 20.0,
        "category": "Integrity",
        "output_prefix": "ul_throughput",
        "related_rules": [
            {"feature": "(HU)UL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "category": "UL Congestion", "reason": "UL PRB utilization increased while UL throughput degraded.", "recommended_action": "Check UL load, UL scheduler, and uplink capacity."},
            {"feature": "(HU) Avg UL Interference(dBm)", "bad_direction": "high", "threshold": 10, "category": "UL Interference Issue", "reason": "UL interference increased while UL throughput degraded.", "recommended_action": "Check external interference, PIM, and uplink noise rise."},
            {"feature": "(HU) UL IBLER(%)", "bad_direction": "high", "threshold": 20, "category": "High UL Retransmission", "reason": "UL IBLER increased while UL throughput degraded.", "recommended_action": "Check UL BLER, interference, PUSCH MCS, and UE power."},
            {"feature": "UL RBLER", "bad_direction": "high", "threshold": 20, "category": "UL Radio Block Errors", "reason": "UL RBLER increased while UL throughput degraded.", "recommended_action": "Check UL coverage, interference, and UE power limitation."},
            {"feature": "(HU) PUSCH MCS", "bad_direction": "low", "threshold": 15, "category": "Low UL Modulation", "reason": "PUSCH MCS decreased while UL throughput degraded.", "recommended_action": "Check uplink SINR, interference, and power control."},
            {"feature": "L.Traffic.ActiveUser.UL.Avg", "bad_direction": "high", "threshold": 20, "category": "High UL User Load", "reason": "UL active users increased while UL throughput decreased.", "recommended_action": "Check uplink scheduling, congestion, and load distribution."},
        ],
    },

    "RRC Setup SR": {
        "target_kpi": "(TE) RRC Setup SR%",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Accessibility",
        "output_prefix": "rrc_setup_sr",
        "related_rules": [
            {"feature": "L.RRC.ConnReq.Att", "bad_direction": "high", "threshold": 20, "category": "High RRC Attempts", "reason": "RRC attempts increased.", "recommended_action": "Check RACH load, access parameters, admission control, and overload."},
            {"feature": "RRC Setup Failure Time", "bad_direction": "high", "threshold": 20, "category": "RRC Failure Increase", "reason": "RRC setup failures increased.", "recommended_action": "Check RACH failures, no reply, rejection, admission control, and radio quality."},
            {"feature": "L.RRC.SetupFail.NoReply", "bad_direction": "high", "threshold": 20, "category": "RRC No Reply", "reason": "RRC no-reply failures increased.", "recommended_action": "Check coverage, interference, RACH configuration, and UE access conditions."},
            {"feature": "L.RRC.SetupFail.Rej", "bad_direction": "high", "threshold": 20, "category": "RRC Rejection", "reason": "RRC rejection failures increased.", "recommended_action": "Check admission control, overload, forbidden access, and MME overload."},
            {"feature": "L.RRC.SetupFail.Rej.MMEOverload", "bad_direction": "high", "threshold": 20, "category": "MME Overload", "reason": "RRC rejection due to MME overload increased.", "recommended_action": "Check MME/S1 signaling, core side load, and S1 interface."},
            {"feature": "L.RRC.SetupFail.ResFail", "bad_direction": "high", "threshold": 20, "category": "Radio Resource Failure", "reason": "RRC setup failures due to resource failure increased.", "recommended_action": "Check radio resources, PRB load, admission control, and congestion."},
            {"feature": "RACH Contention-Based Failures", "bad_direction": "high", "threshold": 20, "category": "RACH Failure", "reason": "RACH contention failures increased.", "recommended_action": "Check PRACH configuration, root sequence planning, preamble load, and coverage."},
        ],
    },

    "ERAB Setup SR": {
        "target_kpi": "ERAB Setup Success Rate",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Accessibility",
        "output_prefix": "erab_setup_sr",
        "related_rules": [
            {"feature": "L.E-RAB.AttEst", "bad_direction": "high", "threshold": 20, "category": "High ERAB Attempts", "reason": "E-RAB setup attempts increased.", "recommended_action": "Check access load, service attempts, and admission control."},
            {"feature": "ERAB Setup Failure Times", "bad_direction": "high", "threshold": 20, "category": "ERAB Failure Increase", "reason": "E-RAB setup failures increased.", "recommended_action": "Check ERAB failure reason counters, MME, TNL, RNL, and radio resources."},
            {"feature": "L.E-RAB.FailEst.NoRadioRes", "bad_direction": "high", "threshold": 20, "category": "No Radio Resource", "reason": "E-RAB failures due to no radio resources increased.", "recommended_action": "Check PRB load, admission control, congestion, and capacity."},
            {"feature": "L.E-RAB.FailEst.NoReply", "bad_direction": "high", "threshold": 20, "category": "No Reply Failure", "reason": "E-RAB no-reply failures increased.", "recommended_action": "Check radio quality, signaling, and UE response issues."},
            {"feature": "L.E-RAB.FailEst.MME", "bad_direction": "high", "threshold": 20, "category": "MME Related Failure", "reason": "E-RAB setup failures related to MME increased.", "recommended_action": "Check MME/core side, S1 signaling, and core load."},
            {"feature": "L.E-RAB.FailEst.TNL", "bad_direction": "high", "threshold": 20, "category": "Transport Network Failure", "reason": "E-RAB setup failures related to TNL increased.", "recommended_action": "Check transmission, backhaul, S1-U/S1-C, and transport path."},
        ],
    },

    "Drop Rate": {
        "target_kpi": "E-RAB Drop Rate (E-NodeB + MME) %",
        "bad_direction": "high",
        "default_threshold": 20.0,
        "category": "Retainability",
        "output_prefix": "drop_rate",
        "related_rules": [
            {"feature": "L.E-RAB.AbnormRel", "bad_direction": "high", "threshold": 20, "category": "Abnormal Release Increase", "reason": "E-RAB abnormal releases increased.", "recommended_action": "Check drop reason counters, radio quality, HO failures, and TNL/MME causes."},
            {"feature": "L.E-RAB.AbnormRel.Radio", "bad_direction": "high", "threshold": 20, "category": "Radio Drop Issue", "reason": "Radio abnormal releases increased.", "recommended_action": "Check coverage, interference, CQI, BLER, and antenna settings."},
            {"feature": "L.E-RAB.AbnormRel.Radio.ULSyncFail", "bad_direction": "high", "threshold": 20, "category": "UL Sync Failure", "reason": "Drops due to UL synchronization failure increased.", "recommended_action": "Check uplink coverage, UL interference, UE power, and timing advance."},
            {"feature": "L.E-RAB.AbnormRel.Radio.UuNoReply", "bad_direction": "high", "threshold": 20, "category": "Uu No Reply", "reason": "Drops due to Uu no-reply increased.", "recommended_action": "Check coverage holes, interference, and radio link quality."},
            {"feature": "L.E-RAB.AbnormRel.TNL", "bad_direction": "high", "threshold": 20, "category": "Transport Drop Issue", "reason": "Transport-related abnormal releases increased.", "recommended_action": "Check backhaul, transmission alarms, packet loss, and transport congestion."},
            {"feature": "L.E-RAB.AbnormRel.MME", "bad_direction": "high", "threshold": 20, "category": "MME Drop Issue", "reason": "MME-related abnormal releases increased.", "recommended_action": "Check core network, MME, S1 signaling, and S1 reset counters."},
            {"feature": "L.E-RAB.AbnormRel.HOFailure", "bad_direction": "high", "threshold": 20, "category": "HO Related Drop", "reason": "Abnormal releases related to HO failure increased.", "recommended_action": "Check neighbors, missing neighbors, A3 offset, CIO, TTT, and PCI issues."},
            {"feature": "RRC Connection Drop Rate%", "bad_direction": "high", "threshold": 20, "category": "RRC Drop Issue", "reason": "RRC connection drop rate increased.", "recommended_action": "Check radio quality, coverage, interference, re-establishment, and mobility."},
        ],
    },

    "HO Success Rate": {
        "target_kpi": "HO SR% Overall",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Mobility",
        "output_prefix": "ho_success_rate",
        "related_rules": [
            {"feature": "Intra_Freq HO Prepare Failed Times", "bad_direction": "high", "threshold": 20, "category": "Intra-Frequency HO Preparation Failure", "reason": "Intra-frequency HO preparation failures increased.", "recommended_action": "Check neighbor relations, target cell availability, admission control, and HO prep failure reasons."},
            {"feature": "Intra_Freq HO Execution Failed Times", "bad_direction": "high", "threshold": 20, "category": "Intra-Frequency HO Execution Failure", "reason": "Intra-frequency HO execution failures increased.", "recommended_action": "Check radio quality, A3 offset, TTT, CIO, PCI, and target cell coverage."},
            {"feature": "Inter_Freq HO Prepare Failed Times", "bad_direction": "high", "threshold": 20, "category": "Inter-Frequency HO Preparation Failure", "reason": "Inter-frequency HO preparation failures increased.", "recommended_action": "Check inter-frequency neighbors, measurement configuration, frequency priority, and target availability."},
            {"feature": "Inter_Freq HO Execution Failed Times", "bad_direction": "high", "threshold": 20, "category": "Inter-Frequency HO Execution Failure", "reason": "Inter-frequency HO execution failures increased.", "recommended_action": "Check A3/A5 thresholds, TTT, CIO, target cell coverage, and PCI conflicts."},
            {"feature": "S1 HO Execution Failed Times", "bad_direction": "high", "threshold": 20, "category": "S1 HO Failure", "reason": "S1 HO execution failures increased.", "recommended_action": "Check S1 handover path, MME, transport, and target eNodeB response."},
            {"feature": "X2 Intra-Freq Failure", "bad_direction": "high", "threshold": 20, "category": "X2 Intra-Frequency HO Failure", "reason": "X2 intra-frequency HO failures increased.", "recommended_action": "Check X2 links, neighbor relation, target cell, and mobility parameters."},
            {"feature": "X2 Inter-Freq Failure", "bad_direction": "high", "threshold": 20, "category": "X2 Inter-Frequency HO Failure", "reason": "X2 inter-frequency HO failures increased.", "recommended_action": "Check X2 links, inter-frequency neighbors, and target frequency settings."},
            {"feature": "L.HHO.PingPongHo", "bad_direction": "high", "threshold": 20, "category": "Ping-Pong HO Issue", "reason": "Ping-pong handovers increased.", "recommended_action": "Tune hysteresis, TTT, CIO, A3 offset, and neighbor priorities."},
        ],
    },

    "Availability": {
        "target_kpi": "Availability",
        "bad_direction": "low",
        "default_threshold": 1.0,
        "category": "Availability",
        "output_prefix": "availability",
        "related_rules": [
            {"feature": "(HU) Cell Unavail Time (s)", "bad_direction": "high", "threshold": 20, "category": "Cell Unavailable Time Increase", "reason": "Cell unavailable time increased.", "recommended_action": "Check outage, alarms, power, transmission, and site status."},
            {"feature": "L.Cell.Unavail.Dur.Sys(s)", "bad_direction": "high", "threshold": 20, "category": "System Unavailability", "reason": "System unavailability duration increased.", "recommended_action": "Check system faults, board alarms, transmission, and eNodeB health."},
            {"feature": "L.Cell.Unavail.Dur.Manual(s)", "bad_direction": "high", "threshold": 20, "category": "Manual Unavailability", "reason": "Manual unavailability duration increased.", "recommended_action": "Check manual lock, planned work, maintenance activity, and cell administrative state."},
            {"feature": "L.Cell.Unavail.Dur.Sys.S1Fail(s)", "bad_direction": "high", "threshold": 20, "category": "S1 Failure Unavailability", "reason": "S1 failure unavailability duration increased.", "recommended_action": "Check S1 link, MME connection, transmission, and core network alarms."},
        ],
    },

    "RACH Success Rate": {
        "target_kpi": "(HU) RACH Success Rate(%)",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Accessibility",
        "output_prefix": "rach_success_rate",
        "related_rules": [
            {"feature": "RACH Setup Failed Number", "bad_direction": "high", "threshold": 20, "category": "RACH Setup Failures", "reason": "RACH setup failures increased.", "recommended_action": "Check PRACH parameters, root sequence planning, coverage, interference, and access load."},
            {"feature": "RACH Contention-Based Failures", "bad_direction": "high", "threshold": 20, "category": "Contention-Based RACH Failure", "reason": "Contention-based RACH failures increased.", "recommended_action": "Check preamble congestion, PRACH configuration, root sequence, and access load."},
            {"feature": "RACH_att", "bad_direction": "high", "threshold": 20, "category": "High RACH Attempts", "reason": "RACH attempts increased.", "recommended_action": "Check access load, coverage, PRACH capacity, and random access configuration."},
            {"feature": "RACH Contention-Based SR", "bad_direction": "low", "threshold": 5, "category": "Contention-Based RACH SR Drop", "reason": "Contention-based RACH success rate decreased.", "recommended_action": "Check PRACH configuration, root sequence planning, and access congestion."},
            {"feature": "RACH Non-Contention-Based SR", "bad_direction": "low", "threshold": 5, "category": "Non-Contention RACH SR Drop", "reason": "Non-contention RACH success rate decreased.", "recommended_action": "Check HO-related RACH, target cell access, and PRACH settings."},
        ],
    },

    "CSFB KPI": {
        "target_kpi": "CSFB SR%",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "CSFB / Voice Accessibility",
        "output_prefix": "csfb_kpi",
        "related_rules": [
            {"feature": "CSFB Failure Times", "bad_direction": "high", "threshold": 20, "category": "CSFB Failure Increase", "reason": "CSFB failure times increased.", "recommended_action": "Check CSFB failure reasons, MME/S1 signaling, RRC redirection, and target 2G/3G availability."},
            {"feature": "L.CSFB.PrepAtt", "bad_direction": "high", "threshold": 20, "category": "High CSFB Preparation Attempts", "reason": "CSFB preparation attempts increased, which may increase CSFB load.", "recommended_action": "Check CSFB traffic demand, MME load, S1 signaling, and whether the increase is normal voice demand."},
            {"feature": "L.RRCRedirection.E2W.CSFB", "bad_direction": "low", "threshold": 20, "category": "E2W CSFB Redirection Drop", "reason": "LTE-to-3G CSFB redirection count decreased compared with baseline.", "recommended_action": "Check UTRAN neighbor configuration, 3G target coverage, UTRAN frequency priority, and CSFB redirection settings."},
            {"feature": "L.RRCRedirection.E2G.CSFB", "bad_direction": "low", "threshold": 20, "category": "E2G CSFB Redirection Drop", "reason": "LTE-to-2G CSFB redirection count decreased compared with baseline.", "recommended_action": "Check GERAN neighbor configuration, 2G target coverage, GERAN frequency priority, LAI/TAI mapping, and CSFB redirection settings."},
            {"feature": "L.RRCRedirection.E2W", "bad_direction": "low", "threshold": 20, "category": "E2W Redirection Issue", "reason": "LTE-to-3G RRC redirection decreased, which may affect CSFB to 3G.", "recommended_action": "Check 3G redirection configuration, UTRAN neighbor/frequency settings, and target 3G coverage."},
            {"feature": "L.RRCRedirection.E2W.Coverage", "bad_direction": "low", "threshold": 20, "category": "E2W Coverage-Based Redirection Issue", "reason": "Coverage-based LTE-to-3G redirection decreased.", "recommended_action": "Check 3G coverage layer, inter-RAT coverage thresholds, UTRAN neighbor definitions, and coverage-based redirection parameters."},
            {"feature": "L.FlashCSFB.E2W", "bad_direction": "low", "threshold": 20, "category": "Flash CSFB E2W Issue", "reason": "Flash CSFB to 3G decreased.", "recommended_action": "Check Flash CSFB feature activation, E2W CSFB configuration, UTRAN target frequency, and UE support."},
            {"feature": "Flash CSFB Ratio", "bad_direction": "low", "threshold": 20, "category": "Flash CSFB Ratio Drop", "reason": "Flash CSFB ratio decreased.", "recommended_action": "Check Flash CSFB switch/feature configuration, CSFB method priority, UE capability, and target 3G readiness."},
            {"feature": "(TE) RRC Setup SR%", "bad_direction": "low", "threshold": 5, "category": "LTE RRC Access Issue", "reason": "RRC setup success rate decreased, which can affect CSFB before fallback starts.", "recommended_action": "Check LTE RRC accessibility, RACH, RRC setup failures, admission control, and radio quality."},
            {"feature": "RRC Setup Failure Time", "bad_direction": "high", "threshold": 20, "category": "RRC Failure Increase", "reason": "RRC setup failures increased, which can impact CSFB accessibility.", "recommended_action": "Check RRC failure reasons, no reply, rejection, resource failure, and access congestion."},
            {"feature": "RRC Setup(Service) Attempt  Times", "bad_direction": "high", "threshold": 20, "category": "High RRC Service Attempts", "reason": "RRC service attempts increased, which may increase signaling load before CSFB.", "recommended_action": "Check service access load, RRC service setup, signaling congestion, and admission control."},
            {"feature": "RRC Setup Success (Service) Rate(%)", "bad_direction": "low", "threshold": 5, "category": "RRC Service Setup Issue", "reason": "RRC service setup success rate decreased, which may affect CSFB service access.", "recommended_action": "Check RRC service setup failures, radio quality, admission control, and MME/S1 signaling."},
            {"feature": "S1 Sig Setup SR%", "bad_direction": "low", "threshold": 5, "category": "S1 Signaling Issue", "reason": "S1 signaling setup success rate decreased, which may affect CSFB preparation with MME.", "recommended_action": "Check S1 link, MME load, S1 signaling failures, transmission, and core alarms."},
            {"feature": "S1 Sig setup Failure Times", "bad_direction": "high", "threshold": 20, "category": "S1 Signaling Failure Increase", "reason": "S1 signaling setup failures increased.", "recommended_action": "Check S1 signaling failure reasons, MME overload, SCTP/S1 link stability, and transmission issues."},
            {"feature": "ERAB Setup Success Rate", "bad_direction": "low", "threshold": 5, "category": "E-RAB Setup Issue", "reason": "E-RAB setup success rate decreased, indicating possible access or core signaling issue affecting services.", "recommended_action": "Check E-RAB setup failures, MME/TNL/RNL causes, admission control, radio resources, and S1 signaling."},
            {"feature": "ERAB Setup Failure Times", "bad_direction": "high", "threshold": 20, "category": "E-RAB Failure Increase", "reason": "E-RAB setup failures increased, which may indicate access/core-side degradation.", "recommended_action": "Check E-RAB failure reasons, MME, TNL, RNL, no radio resources, and no reply counters."},
        ],
    },

    "VoLTE KPIs": {
        "target_kpi": "BA_Voice E2E VQI",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "VoLTE",
        "output_prefix": "volte_kpis",
        "related_rules": [
            {"feature": "VoLTE Traffic (Erl)(Erl)", "bad_direction": "low", "threshold": 20, "category": "VoLTE Traffic Drop", "reason": "VoLTE traffic decreased.", "recommended_action": "Check VoLTE user demand, IMS service, VoLTE coverage, and QCI-1 traffic."},
            {"feature": "L.Traffic.User.VoIP.Avg", "bad_direction": "low", "threshold": 20, "category": "VoIP User Drop", "reason": "Average VoIP users decreased.", "recommended_action": "Check VoLTE traffic demand, service availability, and IMS registration behavior."},
            {"feature": "DL Traffic QCI-1", "bad_direction": "low", "threshold": 20, "category": "QCI-1 DL Traffic Drop", "reason": "QCI-1 DL traffic decreased.", "recommended_action": "Check VoLTE bearer traffic, IMS service, and VoLTE user behavior."},
            {"feature": "E-RAB Drop(ENB+MME)_Tot", "bad_direction": "high", "threshold": 20, "category": "VoLTE Retainability Risk", "reason": "Total E-RAB drops increased.", "recommended_action": "Check VoLTE drops, radio quality, TNL/MME causes, and mobility."},
            {"feature": "E-RAB Drop Rate QCI 7", "bad_direction": "high", "threshold": 20, "category": "QCI-7 Drop Issue", "reason": "QCI-7 drop rate increased.", "recommended_action": "Check VoLTE-related bearer retainability and radio quality."},
            {"feature": "BA_Overall SRVCC HO Execution Success Rate (%)", "bad_direction": "low", "threshold": 5, "category": "SRVCC Execution Degradation", "reason": "SRVCC HO execution success rate decreased.", "recommended_action": "Check SRVCC neighbors, 2G/3G target cells, IMS/SRVCC configuration, and mobility parameters."},
            {"feature": "BA_Overall SRVCC HO Preparation Success Rate (%)", "bad_direction": "low", "threshold": 5, "category": "SRVCC Preparation Degradation", "reason": "SRVCC HO preparation success rate decreased.", "recommended_action": "Check SRVCC preparation, target availability, MSC/MME coordination, and neighbor definitions."},
            {"feature": "AJ_E2G SRVCC HO Execution Failure", "bad_direction": "high", "threshold": 20, "category": "E2G SRVCC Execution Failure", "reason": "E2G SRVCC HO execution failures increased.", "recommended_action": "Check 2G target cells, SRVCC configuration, and mobility thresholds."},
            {"feature": "AJ_E2W SRVCC HO Execution Failure", "bad_direction": "high", "threshold": 20, "category": "E2W SRVCC Execution Failure", "reason": "E2W SRVCC HO execution failures increased.", "recommended_action": "Check 3G target cells, SRVCC configuration, and mobility thresholds."},
        ],
    },
}


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def clean_excel_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Clean Excel column names from spaces and hidden line breaks."""
    df = df.copy()

    cleaned_columns = []
    for col in df.columns:
        col = str(col)
        col = col.replace(chr(10), " ")   # remove hidden new line 

        col = col.replace(chr(13), " ")   # remove carriage return 

        col = col.strip()
        cleaned_columns.append(col)

    df.columns = cleaned_columns
    return df


def normalize_column_name(col) -> str:
    """Normalize column names for smart matching."""
    col = str(col).lower()
    col = col.replace(" ", "")
    col = col.replace("_", "")
    col = col.replace("-", "")
    col = col.replace(chr(10), "")
    col = col.replace(chr(13), "")
    col = col.strip()
    return col


def find_matching_column(df: pd.DataFrame, wanted_col: str):
    """Find real Excel column even if spaces/newlines are different."""
    if wanted_col in df.columns:
        return wanted_col

    for col in df.columns:
        if str(col).strip() == str(wanted_col).strip():
            return col

    wanted_norm = normalize_column_name(wanted_col)
    for col in df.columns:
        if normalize_column_name(col) == wanted_norm:
            return col

    return None


def clean_numeric_series(series: pd.Series) -> pd.Series:
    """Convert mixed numeric/text column to numeric."""
    return pd.to_numeric(
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace({"": np.nan, "nan": np.nan, "None": np.nan}),
        errors="coerce",
    )


def calculate_degradation(recent_value, baseline_value, bad_direction):
    """Return degradation percentage. Positive means worse."""
    if pd.isna(recent_value) or pd.isna(baseline_value):
        return np.nan
    if baseline_value == 0:
        return np.nan
    if bad_direction == "low":
        return ((baseline_value - recent_value) / baseline_value) * 100
    if bad_direction == "high":
        return ((recent_value - baseline_value) / baseline_value) * 100
    return np.nan


def get_periods(df, date_col, num_days):
    """Get last N days and same N days last week."""
    last_date = df[date_col].max()
    recent_start = last_date - pd.Timedelta(days=num_days - 1)
    recent_end = last_date
    baseline_start = recent_start - pd.Timedelta(days=7)
    baseline_end = recent_end - pd.Timedelta(days=7)
    return last_date, recent_start, recent_end, baseline_start, baseline_end


def find_degradation_causes(row, rules):
    """Find one or more related causes for one degraded cell."""
    detected_causes = []

    for rule in rules:
        feature = rule["feature"]
        recent_col = f"recent_{feature}"
        baseline_col = f"baseline_{feature}"

        if recent_col not in row.index or baseline_col not in row.index:
            continue

        recent_value = row[recent_col]
        baseline_value = row[baseline_col]

        change_pct = calculate_degradation(
            recent_value,
            baseline_value,
            rule["bad_direction"],
        )

        if pd.isna(change_pct):
            continue

        if change_pct >= rule["threshold"]:
            detected_causes.append({
                "feature": feature,
                "recent_value": recent_value,
                "baseline_value": baseline_value,
                "change_pct": change_pct,
                "category": rule["category"],
                "reason": rule["reason"],
                "recommended_action": rule["recommended_action"],
            })

    if not detected_causes:
        return pd.Series({
            "main_cause_counter_or_kpi": "No strong related counter detected",
            "main_cause_recent_value": np.nan,
            "main_cause_baseline_value": np.nan,
            "main_cause_change_%": np.nan,
            "main_root_cause_category": "Unknown",
            "main_degradation_reason": "Main KPI degraded, but no related counter passed its threshold.",
            "main_recommended_action": "Check raw counters, alarms, availability, recent changes, and nearby cells manually.",
            "number_of_detected_causes": 0,
            "multi_cause_flag": "No",
            "all_detected_causes": "None",
            "all_cause_categories": "Unknown",
            "all_recommended_actions": "Manual investigation needed",
        })

    detected_causes = sorted(detected_causes, key=lambda x: x["change_pct"], reverse=True)
    main_cause = detected_causes[0]

    all_causes_text = " | ".join([
        f"{c['feature']}: recent={c['recent_value']:.2f}, baseline={c['baseline_value']:.2f}, change={c['change_pct']:.2f}%"
        for c in detected_causes
    ])

    all_categories_text = " | ".join([c["category"] for c in detected_causes])
    all_actions_text = " | ".join([c["recommended_action"] for c in detected_causes])

    return pd.Series({
        "main_cause_counter_or_kpi": main_cause["feature"],
        "main_cause_recent_value": main_cause["recent_value"],
        "main_cause_baseline_value": main_cause["baseline_value"],
        "main_cause_change_%": main_cause["change_pct"],
        "main_root_cause_category": main_cause["category"],
        "main_degradation_reason": main_cause["reason"],
        "main_recommended_action": main_cause["recommended_action"],
        "number_of_detected_causes": len(detected_causes),
        "multi_cause_flag": "Yes" if len(detected_causes) > 1 else "No",
        "all_detected_causes": all_causes_text,
        "all_cause_categories": all_categories_text,
        "all_recommended_actions": all_actions_text,
    })


# ============================================================
# 4. MAIN ANALYSIS ENGINE
# ============================================================

def analyze_selected_kpi(df, selected_kpi_name, num_days, degradation_threshold, require_complete_days=True):
    """Analyze selected KPI and return degraded cells with causes."""
    config = KPI_CONFIGS[selected_kpi_name]

    # Clean Excel column names first
    df = clean_excel_columns(df)

    # Smart target KPI matching
    original_target_kpi = config["target_kpi"]
    target_kpi = find_matching_column(df, original_target_kpi)

    if target_kpi is None:
        raise ValueError(f"Target KPI column not found in Excel: {original_target_kpi}")

    bad_direction = config["bad_direction"]
    related_rules = config["related_rules"]

    needed_cols = CELL_ID_COLS + [DATE_COL, target_kpi]
    missing_cols = [col for col in needed_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df_kpi = df[needed_cols].copy()
    df_kpi[DATE_COL] = pd.to_datetime(df_kpi[DATE_COL], errors="coerce").dt.normalize()
    df_kpi[target_kpi] = clean_numeric_series(df_kpi[target_kpi])
    df_kpi = df_kpi.dropna(subset=[DATE_COL, target_kpi])
    df_kpi = df_kpi[df_kpi[target_kpi] >= 0].copy()

    last_date, recent_start, recent_end, baseline_start, baseline_end = get_periods(df_kpi, DATE_COL, num_days)

    recent_df = df_kpi[(df_kpi[DATE_COL] >= recent_start) & (df_kpi[DATE_COL] <= recent_end)].copy()
    baseline_df = df_kpi[(df_kpi[DATE_COL] >= baseline_start) & (df_kpi[DATE_COL] <= baseline_end)].copy()

    recent_agg = recent_df.groupby(CELL_ID_COLS).agg(
        recent_avg_kpi=(target_kpi, "mean"),
        recent_total_kpi=(target_kpi, "sum"),
        recent_days_count=(DATE_COL, "nunique"),
    ).reset_index()

    baseline_agg = baseline_df.groupby(CELL_ID_COLS).agg(
        baseline_avg_kpi=(target_kpi, "mean"),
        baseline_total_kpi=(target_kpi, "sum"),
        baseline_days_count=(DATE_COL, "nunique"),
    ).reset_index()

    comparison = recent_agg.merge(baseline_agg, on=CELL_ID_COLS, how="inner")

    if require_complete_days:
        comparison = comparison[
            (comparison["recent_days_count"] == num_days) &
            (comparison["baseline_days_count"] == num_days)
        ].copy()

    comparison = comparison[comparison["baseline_avg_kpi"] != 0].copy()

    comparison["kpi_degradation_ratio_%"] = comparison.apply(
        lambda row: calculate_degradation(row["recent_avg_kpi"], row["baseline_avg_kpi"], bad_direction),
        axis=1,
    )

    comparison["kpi_status"] = np.where(
        comparison["kpi_degradation_ratio_%"] >= degradation_threshold,
        "Degraded",
        "Normal",
    )

    comparison["selected_kpi_name"] = selected_kpi_name
    comparison["target_kpi_column"] = target_kpi
    comparison["kpi_category"] = config["category"]
    comparison["kpi_bad_direction"] = bad_direction
    comparison["selected_threshold_%"] = degradation_threshold
    comparison["recent_period"] = f"{recent_start.date()} to {recent_end.date()}"
    comparison["baseline_period"] = f"{baseline_start.date()} to {baseline_end.date()}"

    degraded_cells = comparison[comparison["kpi_status"] == "Degraded"].copy()
    degraded_cells = degraded_cells.sort_values("kpi_degradation_ratio_%", ascending=False)

    debug_info = {
        "cells_after_merge": comparison.shape[0],
        "recent_days_distribution": comparison["recent_days_count"].value_counts().sort_index().to_dict(),
        "baseline_days_distribution": comparison["baseline_days_count"].value_counts().sort_index().to_dict(),
        "max_degradation": comparison["kpi_degradation_ratio_%"].max() if not comparison.empty else None,
        "min_degradation": comparison["kpi_degradation_ratio_%"].min() if not comparison.empty else None,
        "mean_degradation": comparison["kpi_degradation_ratio_%"].mean() if not comparison.empty else None,
    }

    metadata = {
        "last_date": last_date,
        "recent_start": recent_start,
        "recent_end": recent_end,
        "baseline_start": baseline_start,
        "baseline_end": baseline_end,
        "available_related_features": [],
        "missing_related_features": [],
        "debug_info": debug_info,
    }

    if degraded_cells.empty:
        return degraded_cells, metadata

    # Smart related counter matching
    available_related_rules = []
    missing_related_features = []

    for rule in related_rules:
        matched_col = find_matching_column(df, rule["feature"])
        if matched_col is not None:
            new_rule = rule.copy()
            new_rule["feature"] = matched_col
            available_related_rules.append(new_rule)
        else:
            missing_related_features.append(rule["feature"])

    available_related_features = [rule["feature"] for rule in available_related_rules]
    metadata["available_related_features"] = available_related_features
    metadata["missing_related_features"] = missing_related_features

    if available_related_features:
        reason_cols = CELL_ID_COLS + [DATE_COL] + available_related_features
        df_reason = df[reason_cols].copy()
        df_reason[DATE_COL] = pd.to_datetime(df_reason[DATE_COL], errors="coerce").dt.normalize()

        for col in available_related_features:
            df_reason[col] = clean_numeric_series(df_reason[col])

        recent_reason_df = df_reason[(df_reason[DATE_COL] >= recent_start) & (df_reason[DATE_COL] <= recent_end)].copy()
        baseline_reason_df = df_reason[(df_reason[DATE_COL] >= baseline_start) & (df_reason[DATE_COL] <= baseline_end)].copy()

        recent_reason_agg = recent_reason_df.groupby(CELL_ID_COLS)[available_related_features].mean().reset_index()
        baseline_reason_agg = baseline_reason_df.groupby(CELL_ID_COLS)[available_related_features].mean().reset_index()

        recent_reason_agg = recent_reason_agg.rename(columns={col: f"recent_{col}" for col in available_related_features})
        baseline_reason_agg = baseline_reason_agg.rename(columns={col: f"baseline_{col}" for col in available_related_features})

        degraded_with_causes = degraded_cells.merge(recent_reason_agg, on=CELL_ID_COLS, how="left")
        degraded_with_causes = degraded_with_causes.merge(baseline_reason_agg, on=CELL_ID_COLS, how="left")

        cause_results = degraded_with_causes.apply(
            lambda row: find_degradation_causes(row, available_related_rules),
            axis=1,
        )
        degraded_with_causes = pd.concat([degraded_with_causes, cause_results], axis=1)
    else:
        degraded_with_causes = degraded_cells.copy()
        degraded_with_causes["main_cause_counter_or_kpi"] = "No related counters available in sheet"
        degraded_with_causes["main_cause_recent_value"] = np.nan
        degraded_with_causes["main_cause_baseline_value"] = np.nan
        degraded_with_causes["main_cause_change_%"] = np.nan
        degraded_with_causes["main_root_cause_category"] = "Unknown"
        degraded_with_causes["main_degradation_reason"] = "No related counters from the config were found in the uploaded sheet."
        degraded_with_causes["main_recommended_action"] = "Check KPI manually or update KPI_CONFIGS with available counters."
        degraded_with_causes["number_of_detected_causes"] = 0
        degraded_with_causes["multi_cause_flag"] = "No"
        degraded_with_causes["all_detected_causes"] = "None"
        degraded_with_causes["all_cause_categories"] = "Unknown"
        degraded_with_causes["all_recommended_actions"] = "Manual investigation needed"

    final_cols = CELL_ID_COLS + [
        "selected_kpi_name",
        "target_kpi_column",
        "kpi_category",
        "kpi_bad_direction",
        "selected_threshold_%",
        "recent_period",
        "baseline_period",
        "recent_avg_kpi",
        "baseline_avg_kpi",
        "recent_total_kpi",
        "baseline_total_kpi",
        "recent_days_count",
        "baseline_days_count",
        "kpi_degradation_ratio_%",
        "kpi_status",
        "main_cause_counter_or_kpi",
        "main_cause_recent_value",
        "main_cause_baseline_value",
        "main_cause_change_%",
        "main_root_cause_category",
        "main_degradation_reason",
        "main_recommended_action",
        "number_of_detected_causes",
        "multi_cause_flag",
        "all_detected_causes",
        "all_cause_categories",
        "all_recommended_actions",
    ]

    return degraded_with_causes[final_cols].copy(), metadata


# ============================================================
# 5. DESKTOP GUI APPLICATION
# ============================================================

class LTEKPIAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LTE KPI Degradation Analyzer - Developed by Musketeers_Team for (ITI Graduation Project 2026)")
        self.root.geometry("1250x760")
        self.root.minsize(1050, 700)

        self.file_path = tk.StringVar()
        self.selected_kpi = tk.StringVar(value="DL Traffic")
        self.num_days = tk.IntVar(value=4)
        self.threshold = tk.DoubleVar(value=KPI_CONFIGS["DL Traffic"]["default_threshold"])
        self.require_complete_days = tk.BooleanVar(value=True)
        self.output_df = None

        # Stores outputs when running Analyze All KPIs
        self.all_outputs = {}
        self.summary_df = None
        self.analysis_mode = "single"

        # Running/progress state
        self.is_running = False
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_percent_var = tk.StringVar(value="0%")
        self.status_var = tk.StringVar(value="Ready")

        self.build_ui()

    def build_ui(self):
        # Main frames
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill="x")

        settings_frame = ttk.LabelFrame(self.root, text="Analysis Settings", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        result_frame = ttk.LabelFrame(self.root, text="Results Preview", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="x", padx=10, pady=5)

        # File selection
        ttk.Label(top_frame, text="Excel File:").pack(side="left")
        ttk.Entry(top_frame, textvariable=self.file_path, width=90).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Browse", command=self.browse_file).pack(side="left", padx=5)

        # KPI selection
        ttk.Label(settings_frame, text="KPI:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.kpi_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.selected_kpi,
            values=list(KPI_CONFIGS.keys()),
            state="readonly",
            width=28,
        )
        self.kpi_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.kpi_combo.bind("<<ComboboxSelected>>", self.on_kpi_change)

        # Number of days
        ttk.Label(settings_frame, text="Comparison Days:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Spinbox(settings_frame, from_=1, to=14, textvariable=self.num_days, width=8).grid(
            row=0, column=3, sticky="w", padx=5, pady=5
        )

        # Threshold
        ttk.Label(settings_frame, text="Threshold (%):").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        ttk.Entry(settings_frame, textvariable=self.threshold, width=10).grid(
            row=0, column=5, sticky="w", padx=5, pady=5
        )

        # Run and save buttons
        self.run_button = ttk.Button(settings_frame, text="Run Selected KPI", command=self.run_analysis_thread)
        self.run_button.grid(row=0, column=6, padx=10, pady=5)

        self.run_all_button = ttk.Button(settings_frame, text="Analyze All KPIs", command=self.run_all_analysis_thread)
        self.run_all_button.grid(row=0, column=7, padx=10, pady=5)

        self.save_button = ttk.Button(settings_frame, text="Save CSV", command=self.save_csv)
        self.save_button.grid(row=1, column=6, padx=10, pady=5)

        self.dashboard_button = ttk.Button(settings_frame, text="Show Dashboard", command=self.show_dashboard)
        self.dashboard_button.grid(row=1, column=7, padx=10, pady=5)

        # Complete days checkbox
        ttk.Checkbutton(
            settings_frame,
            text="Require complete days in recent and baseline periods",
            variable=self.require_complete_days,
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        # Info label
        self.info_label = ttk.Label(settings_frame, text="")
        self.info_label.grid(row=1, column=3, columnspan=3, sticky="w", padx=5, pady=5)
        self.update_info_label()

        # Progress bar + percentage + status
        ttk.Label(settings_frame, text="Progress:").grid(row=2, column=0, sticky="w", padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(
            settings_frame,
            variable=self.progress_var,
            maximum=100,
            length=430,
            mode="determinate",
        )
        self.progress_bar.grid(row=2, column=1, columnspan=3, sticky="we", padx=5, pady=5)

        self.progress_percent_label = ttk.Label(
            settings_frame,
            textvariable=self.progress_percent_var,
            width=7,
        )
        self.progress_percent_label.grid(row=2, column=4, sticky="w", padx=5, pady=5)

        self.status_label = ttk.Label(settings_frame, textvariable=self.status_var)
        self.status_label.grid(row=2, column=5, columnspan=2, sticky="w", padx=5, pady=5)

        # Results treeview
        self.tree = ttk.Treeview(result_frame, show="headings")
        tree_y = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        tree_x = ttk.Scrollbar(result_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_y.set, xscrollcommand=tree_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_y.grid(row=0, column=1, sticky="ns")
        tree_x.grid(row=1, column=0, sticky="ew")

        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)

        # Log box
        self.log_text = tk.Text(log_frame, height=7)
        self.log_text.pack(fill="x")

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select KPI Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")],
        )
        if path:
            self.file_path.set(path)
            self.log(f"Selected file: {path}")

    def on_kpi_change(self, event=None):
        config = KPI_CONFIGS[self.selected_kpi.get()]
        self.threshold.set(config["default_threshold"])
        self.update_info_label()

    def update_info_label(self):
        config = KPI_CONFIGS[self.selected_kpi.get()]
        self.info_label.config(
            text=f"Target: {config['target_kpi']} | Bad direction: {config['bad_direction']}"
        )

    def log(self, msg):
        self.log_text.insert("end", str(msg) + "\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def update_progress(self, value, status):
        """Update progress bar, percentage label, status label, and log."""
        value = max(0, min(100, float(value)))
        self.progress_var.set(value)
        self.progress_percent_var.set(f"{int(value)}%")
        self.status_var.set(status)
        self.log(f"[{int(value)}%] {status}")
        self.root.update_idletasks()

    def set_running_state(self, running):
        """Disable Run/Save buttons while analysis is running."""
        self.is_running = running
        if running:
            self.run_button.config(state="disabled")
            self.run_all_button.config(state="disabled")
            self.save_button.config(state="disabled")
            self.dashboard_button.config(state="disabled")
        else:
            self.run_button.config(state="normal")
            self.run_all_button.config(state="normal")
            self.save_button.config(state="normal")
            self.dashboard_button.config(state="normal")

    def run_analysis_thread(self):
        if self.is_running:
            messagebox.showinfo("Running", "Analysis is already running. Please wait.")
            return

        self.progress_var.set(0)
        self.progress_percent_var.set("0%")
        self.status_var.set("Starting...")

        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()

    def run_all_analysis_thread(self):
        if self.is_running:
            messagebox.showinfo("Running", "Analysis is already running. Please wait.")
            return

        self.progress_var.set(0)
        self.progress_percent_var.set("0%")
        self.status_var.set("Starting Analyze All KPIs...")

        thread = threading.Thread(target=self.run_all_analysis, daemon=True)
        thread.start()

    def sanitize_filename(self, name):
        """Create a safe file name from KPI name."""
        safe_name = str(name)
        for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '(', ')', '%']:
            safe_name = safe_name.replace(ch, '')
        safe_name = safe_name.replace(' ', '_').replace('__', '_')
        return safe_name.lower()

    def run_analysis(self):
        try:
            self.set_running_state(True)
            self.update_progress(2, "Checking selected file...")

            path = self.file_path.get().strip()

            if not path:
                messagebox.showwarning("Missing file", "Please select an Excel file first.")
                self.update_progress(0, "Ready")
                return

            if not os.path.exists(path):
                messagebox.showerror("File error", "The selected file does not exist.")
                self.update_progress(0, "Ready")
                return

            self.update_progress(10, "Loading Excel file...")
            df = pd.read_excel(path)

            self.update_progress(20, "Cleaning Excel column names...")
            df = clean_excel_columns(df)

            self.log(f"Loaded file. Rows: {df.shape[0]}, Columns: {df.shape[1]}")

            selected_kpi = self.selected_kpi.get()
            num_days = int(self.num_days.get())
            threshold = float(self.threshold.get())
            complete_days = bool(self.require_complete_days.get())

            self.update_progress(35, f"Preparing analysis for KPI: {selected_kpi}")
            self.log(f"Comparison days: {num_days}, Threshold: {threshold}%")

            self.update_progress(45, "Running KPI degradation comparison and root-cause analysis...")

            output_df, metadata = analyze_selected_kpi(
                df=df,
                selected_kpi_name=selected_kpi,
                num_days=num_days,
                degradation_threshold=threshold,
                require_complete_days=complete_days,
            )

            self.output_df = output_df
            self.all_outputs = {}
            self.summary_df = None
            self.analysis_mode = "single"

            self.update_progress(75, "Analysis engine completed. Preparing logs...")

            self.log(f"Recent period: {metadata['recent_start'].date()} to {metadata['recent_end'].date()}")
            self.log(f"Baseline period: {metadata['baseline_start'].date()} to {metadata['baseline_end'].date()}")
            self.log(f"Available related counters: {len(metadata.get('available_related_features', []))}")
            self.log(f"Missing related counters: {len(metadata.get('missing_related_features', []))}")

            debug_info = metadata.get("debug_info", {})
            self.log(f"Cells after recent/baseline merge: {debug_info.get('cells_after_merge')}")
            self.log(f"Recent days distribution: {debug_info.get('recent_days_distribution')}")
            self.log(f"Baseline days distribution: {debug_info.get('baseline_days_distribution')}")
            self.log(f"Max degradation: {debug_info.get('max_degradation')}")
            self.log(f"Mean degradation: {debug_info.get('mean_degradation')}")

            self.log(f"Degraded cells found: {output_df.shape[0]}")

            self.update_progress(90, "Updating results table...")
            self.update_table(output_df)

            self.update_progress(100, "Analysis completed successfully.")

            if output_df.empty:
                messagebox.showinfo("Done", "Analysis completed. No degraded cells found.")
            else:
                messagebox.showinfo("Done", f"Analysis completed. Degraded cells: {output_df.shape[0]}")

        except Exception as e:
            self.update_progress(0, "Error happened during analysis.")
            self.log(f"ERROR: {e}")
            messagebox.showerror("Error", str(e))

        finally:
            self.set_running_state(False)

    def run_all_analysis(self):
        """Analyze all configured KPIs using their default thresholds."""
        try:
            self.set_running_state(True)
            self.update_progress(2, "Checking selected file...")

            path = self.file_path.get().strip()

            if not path:
                messagebox.showwarning("Missing file", "Please select an Excel file first.")
                self.update_progress(0, "Ready")
                return

            if not os.path.exists(path):
                messagebox.showerror("File error", "The selected file does not exist.")
                self.update_progress(0, "Ready")
                return

            self.update_progress(10, "Loading Excel file...")
            df = pd.read_excel(path)

            self.update_progress(15, "Cleaning Excel column names...")
            df = clean_excel_columns(df)

            self.log(f"Loaded file. Rows: {df.shape[0]}, Columns: {df.shape[1]}")

            num_days = int(self.num_days.get())
            complete_days = bool(self.require_complete_days.get())

            self.log(f"Analyze All KPIs started. Comparison days: {num_days}")
            self.log(f"Complete-days filter: {complete_days}")

            outputs = {}
            summary_records = []
            all_kpi_names = list(KPI_CONFIGS.keys())
            total_kpis = len(all_kpi_names)

            for index, kpi_name in enumerate(all_kpi_names, start=1):
                config = KPI_CONFIGS[kpi_name]
                threshold = float(config["default_threshold"])

                # Progress range from 20% to 85% during KPI loop
                progress_value = 20 + ((index - 1) / max(total_kpis, 1)) * 65
                self.update_progress(
                    progress_value,
                    f"Analyzing {index}/{total_kpis}: {kpi_name}"
                )

                try:
                    output_df, metadata = analyze_selected_kpi(
                        df=df,
                        selected_kpi_name=kpi_name,
                        num_days=num_days,
                        degradation_threshold=threshold,
                        require_complete_days=complete_days,
                    )

                    outputs[kpi_name] = output_df

                    debug_info = metadata.get("debug_info", {})
                    degraded_count = int(output_df.shape[0])
                    max_degradation = debug_info.get("max_degradation")
                    mean_degradation = debug_info.get("mean_degradation")

                    if not output_df.empty and "main_root_cause_category" in output_df.columns:
                        most_common_cause = output_df["main_root_cause_category"].mode().iloc[0]
                    else:
                        most_common_cause = "No degraded cells"

                    summary_records.append({
                        "kpi_name": kpi_name,
                        "target_kpi_column": config["target_kpi"],
                        "kpi_category": config["category"],
                        "bad_direction": config["bad_direction"],
                        "threshold_%": threshold,
                        "recent_period": f"{metadata['recent_start'].date()} to {metadata['recent_end'].date()}",
                        "baseline_period": f"{metadata['baseline_start'].date()} to {metadata['baseline_end'].date()}",
                        "available_related_counters": len(metadata.get("available_related_features", [])),
                        "missing_related_counters": len(metadata.get("missing_related_features", [])),
                        "cells_after_merge": debug_info.get("cells_after_merge"),
                        "max_degradation_%": max_degradation,
                        "mean_degradation_%": mean_degradation,
                        "degraded_cells_count": degraded_count,
                        "most_common_cause": most_common_cause,
                        "status": "Completed",
                        "error": ""
                    })

                    self.log(f"{kpi_name}: degraded cells = {degraded_count}")

                except Exception as kpi_error:
                    outputs[kpi_name] = pd.DataFrame()
                    summary_records.append({
                        "kpi_name": kpi_name,
                        "target_kpi_column": config.get("target_kpi", ""),
                        "kpi_category": config.get("category", ""),
                        "bad_direction": config.get("bad_direction", ""),
                        "threshold_%": threshold,
                        "recent_period": "",
                        "baseline_period": "",
                        "available_related_counters": 0,
                        "missing_related_counters": 0,
                        "cells_after_merge": 0,
                        "max_degradation_%": None,
                        "mean_degradation_%": None,
                        "degraded_cells_count": 0,
                        "most_common_cause": "Error",
                        "status": "Failed",
                        "error": str(kpi_error)
                    })
                    self.log(f"{kpi_name}: ERROR - {kpi_error}")

            self.update_progress(88, "Combining outputs...")

            non_empty_outputs = [df_out for df_out in outputs.values() if df_out is not None and not df_out.empty]
            if non_empty_outputs:
                combined_output = pd.concat(non_empty_outputs, ignore_index=True)
            else:
                combined_output = pd.DataFrame()

            summary_df = pd.DataFrame(summary_records)

            self.output_df = combined_output
            self.all_outputs = outputs
            self.summary_df = summary_df
            self.analysis_mode = "all"

            total_degraded = int(combined_output.shape[0])

            self.update_progress(92, "Updating results table with summary...")
            self.update_table(summary_df)

            self.log("Analyze All KPIs completed.")
            self.log(f"Total degraded cells across all KPIs: {total_degraded}")
            self.log("Click Save CSV to export all KPI CSV files, combined output, and summary report.")

            self.update_progress(100, "Analyze All KPIs completed successfully.")

            if total_degraded == 0:
                messagebox.showinfo(
                    "Done",
                    "Analyze All KPIs completed. No degraded cells found. Summary is shown in the table."
                )
            else:
                messagebox.showinfo(
                    "Done",
                    f"Analyze All KPIs completed. Total degraded rows: {total_degraded}. Click Save CSV to export files."
                )

        except Exception as e:
            self.update_progress(0, "Error happened during Analyze All KPIs.")
            self.log(f"ERROR: {e}")
            messagebox.showerror("Error", str(e))

        finally:
            self.set_running_state(False)

    def update_table(self, df):
        # Clear old table
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = []

        if df is None or df.empty:
            return

        # Show only first 200 rows for speed
        preview_df = df.head(200).copy()
        columns = list(preview_df.columns)
        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=160, anchor="w")

        for _, row in preview_df.iterrows():
            values = ["" if pd.isna(row[col]) else str(row[col]) for col in columns]
            self.tree.insert("", "end", values=values)


    # ============================================================
    # DASHBOARD FEATURE
    # ============================================================

    def show_dashboard(self):
        """Open a dashboard window with visual charts for the latest analysis result."""
        if self.output_df is None and self.summary_df is None:
            messagebox.showwarning("No output", "Please run the analysis first.")
            return

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except Exception:
            messagebox.showerror(
                "Missing package",
                "matplotlib is required for the dashboard.\n\nInstall it using:\npy -m pip install matplotlib"
            )
            return

        dashboard = tk.Toplevel(self.root)
        dashboard.title("LTE KPI Analyzer Dashboard")
        dashboard.geometry("1200x760")
        dashboard.minsize(1000, 650)

        main_frame = ttk.Frame(dashboard, padding=10)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(
            main_frame,
            text="LTE KPI Degradation Dashboard",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w", pady=(0, 10))

        metrics_frame = ttk.LabelFrame(main_frame, text="Summary Metrics", padding=10)
        metrics_frame.pack(fill="x", pady=(0, 10))

        charts_frame = ttk.Frame(main_frame)
        charts_frame.pack(fill="both", expand=True)

        left_chart_frame = ttk.LabelFrame(charts_frame, text="Chart 1", padding=10)
        left_chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_chart_frame = ttk.LabelFrame(charts_frame, text="Chart 2", padding=10)
        right_chart_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Prepare metrics
        if self.analysis_mode == "all" and self.summary_df is not None:
            summary_df = self.summary_df.copy()
            total_kpis = summary_df.shape[0]
            successful_kpis = int((summary_df["status"] == "Completed").sum()) if "status" in summary_df.columns else total_kpis
            total_degraded = int(summary_df["degraded_cells_count"].sum()) if "degraded_cells_count" in summary_df.columns else 0
            max_degradation = summary_df["max_degradation_%"].max() if "max_degradation_%" in summary_df.columns else np.nan

            metrics = [
                ("Mode", "Analyze All KPIs"),
                ("KPIs analyzed", total_kpis),
                ("Successful KPIs", successful_kpis),
                ("Total degraded rows", total_degraded),
                ("Max degradation %", "N/A" if pd.isna(max_degradation) else f"{max_degradation:.2f}%"),
            ]
        else:
            output_df = self.output_df.copy() if self.output_df is not None else pd.DataFrame()
            total_degraded = int(output_df.shape[0])
            selected_kpi = self.selected_kpi.get()
            max_degradation = output_df["kpi_degradation_ratio_%"].max() if not output_df.empty and "kpi_degradation_ratio_%" in output_df.columns else np.nan
            main_cause = output_df["main_root_cause_category"].mode().iloc[0] if not output_df.empty and "main_root_cause_category" in output_df.columns else "N/A"

            metrics = [
                ("Mode", "Selected KPI"),
                ("Selected KPI", selected_kpi),
                ("Degraded cells", total_degraded),
                ("Max degradation %", "N/A" if pd.isna(max_degradation) else f"{max_degradation:.2f}%"),
                ("Most common cause", main_cause),
            ]

        for col_index, (metric_name, metric_value) in enumerate(metrics):
            box = ttk.LabelFrame(metrics_frame, text=str(metric_name), padding=8)
            box.grid(row=0, column=col_index, sticky="nsew", padx=5, pady=5)
            ttk.Label(box, text=str(metric_value), font=("Arial", 11, "bold")).pack()
            metrics_frame.columnconfigure(col_index, weight=1)

        # Draw charts
        if self.analysis_mode == "all" and self.summary_df is not None:
            self._draw_all_kpis_dashboard(left_chart_frame, right_chart_frame, Figure, FigureCanvasTkAgg)
        else:
            self._draw_single_kpi_dashboard(left_chart_frame, right_chart_frame, Figure, FigureCanvasTkAgg)


    def _format_bar_value(self, value, suffix="", decimals=0):
        """Format bar labels in a clean readable way."""
        try:
            value = float(value)
        except Exception:
            return str(value)

        if decimals == 0:
            return f"{int(round(value))}{suffix}"

        return f"{value:.{decimals}f}{suffix}"

    def _add_vertical_bar_values(self, ax, bars, suffix="", decimals=0):
        """Write values above vertical bars."""
        if not bars:
            return

        max_height = max([bar.get_height() for bar in bars]) if bars else 0
        offset = max_height * 0.02 if max_height else 0.5

        for bar in bars:
            height = bar.get_height()
            label = self._format_bar_value(height, suffix=suffix, decimals=decimals)

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + offset,
                label,
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=0,
            )

        ax.margins(y=0.15)

    def _add_horizontal_bar_values(self, ax, bars, suffix="", decimals=0):
        """Write values at the end of horizontal bars."""
        if not bars:
            return

        max_width = max([bar.get_width() for bar in bars]) if bars else 0
        offset = max_width * 0.02 if max_width else 0.5

        for bar in bars:
            width = bar.get_width()
            label = self._format_bar_value(width, suffix=suffix, decimals=decimals)

            ax.text(
                width + offset,
                bar.get_y() + bar.get_height() / 2,
                label,
                ha="left",
                va="center",
                fontsize=8,
            )

        ax.margins(x=0.18)


    def _draw_all_kpis_dashboard(self, left_frame, right_frame, Figure, FigureCanvasTkAgg):
        """Dashboard charts for Analyze All KPIs mode."""
        summary_df = self.summary_df.copy()

        # Chart 1: degraded cells count per KPI
        fig1 = Figure(figsize=(6, 4), dpi=100)
        ax1 = fig1.add_subplot(111)

        if "degraded_cells_count" in summary_df.columns and not summary_df.empty:
            plot_df = summary_df.sort_values("degraded_cells_count", ascending=False)
            bars = ax1.bar(plot_df["kpi_name"], plot_df["degraded_cells_count"])
            self._add_vertical_bar_values(ax1, bars, decimals=0)
            ax1.set_title("Degraded Cells per KPI")
            ax1.set_ylabel("Degraded rows")
            ax1.tick_params(axis="x", rotation=75)
        else:
            ax1.text(0.5, 0.5, "No summary data", ha="center", va="center")
            ax1.set_axis_off()

        fig1.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=left_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True)

        # Chart 2: root cause distribution from combined output
        fig2 = Figure(figsize=(6, 4), dpi=100)
        ax2 = fig2.add_subplot(111)

        if self.output_df is not None and not self.output_df.empty and "main_root_cause_category" in self.output_df.columns:
            cause_counts = self.output_df["main_root_cause_category"].value_counts().head(10).sort_values()
            bars = ax2.barh(cause_counts.index, cause_counts.values)
            self._add_horizontal_bar_values(ax2, bars, decimals=0)
            ax2.set_title("Top Root Causes Across All KPIs")
            ax2.set_xlabel("Count")
        else:
            ax2.text(0.5, 0.5, "No degraded cells found", ha="center", va="center")
            ax2.set_axis_off()

        fig2.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=right_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True)

    def _draw_single_kpi_dashboard(self, left_frame, right_frame, Figure, FigureCanvasTkAgg):
        """Dashboard charts for selected KPI mode."""
        output_df = self.output_df.copy() if self.output_df is not None else pd.DataFrame()

        # Chart 1: top degraded cells
        fig1 = Figure(figsize=(6, 4), dpi=100)
        ax1 = fig1.add_subplot(111)

        if not output_df.empty and "kpi_degradation_ratio_%" in output_df.columns:
            label_col = CELL_COL if CELL_COL in output_df.columns else CELL_ID_COLS[0]
            plot_df = output_df.sort_values("kpi_degradation_ratio_%", ascending=False).head(10).copy()
            plot_df = plot_df.sort_values("kpi_degradation_ratio_%")
            bars = ax1.barh(plot_df[label_col].astype(str), plot_df["kpi_degradation_ratio_%"])
            self._add_horizontal_bar_values(ax1, bars, suffix="%", decimals=2)
            ax1.set_title("Top 10 Degraded Cells")
            ax1.set_xlabel("Degradation %")
        else:
            ax1.text(0.5, 0.5, "No degraded cells found", ha="center", va="center")
            ax1.set_axis_off()

        fig1.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=left_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True)

        # Chart 2: cause distribution
        fig2 = Figure(figsize=(6, 4), dpi=100)
        ax2 = fig2.add_subplot(111)

        if not output_df.empty and "main_root_cause_category" in output_df.columns:
            cause_counts = output_df["main_root_cause_category"].value_counts().head(10).sort_values()
            bars = ax2.barh(cause_counts.index, cause_counts.values)
            self._add_horizontal_bar_values(ax2, bars, decimals=0)
            ax2.set_title("Root Cause Distribution")
            ax2.set_xlabel("Count")
        else:
            ax2.text(0.5, 0.5, "No cause data", ha="center", va="center")
            ax2.set_axis_off()

        fig2.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=right_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True)

    def save_csv(self):
        if self.output_df is None and self.summary_df is None:
            messagebox.showwarning("No output", "Please run the analysis first.")
            return

        # Save all KPI outputs when Analyze All KPIs was used
        if self.analysis_mode == "all":
            save_dir = filedialog.askdirectory(title="Select folder to save all KPI CSV files")

            if not save_dir:
                return

            saved_files_count = 0

            # Save one CSV per KPI
            for kpi_name, kpi_df in self.all_outputs.items():
                if kpi_df is None or kpi_df.empty:
                    continue

                prefix = KPI_CONFIGS[kpi_name]["output_prefix"]
                file_name = f"{prefix}_degraded_cells_with_causes.csv"
                save_path = os.path.join(save_dir, file_name)
                kpi_df.to_csv(save_path, index=False, encoding="utf-8-sig")
                saved_files_count += 1

            # Save combined degraded cells output
            if self.output_df is not None and not self.output_df.empty:
                combined_path = os.path.join(save_dir, "all_kpis_combined_degraded_cells.csv")
                self.output_df.to_csv(combined_path, index=False, encoding="utf-8-sig")
                saved_files_count += 1

            # Save summary report even if no degraded cells exist
            if self.summary_df is not None and not self.summary_df.empty:
                summary_path = os.path.join(save_dir, "all_kpis_summary_report.csv")
                self.summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")
                saved_files_count += 1

            self.log(f"All KPI outputs saved in: {save_dir}")
            messagebox.showinfo(
                "Saved",
                f"Saved {saved_files_count} CSV file(s) successfully in:\n{save_dir}"
            )
            return

        # Save selected KPI output
        if self.output_df is None:
            messagebox.showwarning("No output", "Please run the analysis first.")
            return

        if self.output_df.empty:
            messagebox.showwarning("No data", "There are no degraded cells to save.")
            return

        selected_kpi = self.selected_kpi.get()
        prefix = KPI_CONFIGS[selected_kpi]["output_prefix"]
        default_name = f"{prefix}_degraded_cells_with_causes.csv"

        save_path = filedialog.asksaveasfilename(
            title="Save CSV Output",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv")],
        )

        if save_path:
            self.output_df.to_csv(save_path, index=False, encoding="utf-8-sig")
            self.log(f"CSV saved: {save_path}")
            messagebox.showinfo("Saved", f"CSV file saved successfully:\n{save_path}")


# ============================================================
# 6. RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = LTEKPIAnalyzerApp(root)
    root.mainloop()
