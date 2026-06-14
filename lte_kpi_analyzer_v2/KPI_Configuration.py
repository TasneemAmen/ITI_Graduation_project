# ============================================================
# LTE KPI Degradation Analyzer - KPI Configuration
# ============================================================
# This file contains all KPI definitions, thresholds, and rules.
# Edit this file to add new KPIs or modify existing thresholds.
# ============================================================

import re


# ============================================================
# GLOBAL COLUMN NAMES
# ============================================================

DATE_COL = "Date"
SITE_COL = "eNodeB Name"
CELL_COL = "Cell Name"
LOCAL_CELL_COL = "LocalCell Id"

CELL_ID_COLS = [
    SITE_COL,
    CELL_COL,
    LOCAL_CELL_COL,
]

# Baseline window modes
BASELINE_MODE_LAST_WEEK = "last_week"
BASELINE_MODE_4WEEK_AVG = "4week_rolling_avg"
BASELINE_MODE_CUSTOM = "custom_range"

# ============================================================
# NEGATIVE VALUE POLICY (unit-aware)
# ============================================================
# Negatives are valid only for signal/power metrics (dBm/dB: RSRP, RSRQ,
# SINR, interference). For counters/volumes/%/throughput a negative is a
# data glitch and should be filtered. Decision is by column name, so it is
# correct whether a column is a target or a related feature.

_NEG_KEYWORDS = ("interference", "rsrp", "rsrq", "sinr", "rssi")
_NEG_UNITS = ("dbm", "db")
_LAST_PAREN_RE = re.compile(r"\(([^()]+)\)[^()]*$")

# Exact-name overrides for cases the heuristic gets wrong. column -> bool.
NEGATIVE_VALUE_OVERRIDES = {
    # "Some Signed Counter": True,
}


def allows_negative(column_name: str) -> bool:
    """True if negative values are physically valid for this column."""
    if not isinstance(column_name, str):
        return False
    if column_name in NEGATIVE_VALUE_OVERRIDES:
        return NEGATIVE_VALUE_OVERRIDES[column_name]
    low = column_name.lower()
    if any(k in low for k in _NEG_KEYWORDS):
        return True
    m = _LAST_PAREN_RE.search(column_name)
    if m and m.group(1).strip().lower() in _NEG_UNITS:
        return True
    return False


# ============================================================
# KPI CONFIGURATION
# ============================================================
# Each KPI has:
# - target_kpi: The main KPI column name to analyze
# - bad_direction: "low" or "high" - direction indicating degradation
# - default_threshold: Default degradation threshold percentage
# - category: KPI category (Traffic, Integrity, Accessibility, etc.)
# - output_prefix: Prefix for output file names
# - min_baseline_value: Minimum baseline value filter
# - related_rules: List of related counters for root cause detection
# ============================================================

KPI_CONFIGS = {
    "DL Traffic": {
        "target_kpi": "(HU) DL Traffic Volume (GBytes)",
        "bad_direction": "low",
        "default_threshold": 30.0,
        "category": "Traffic",
        "output_prefix": "dl_traffic",
        "min_baseline_value": 1.0,
        "related_rules": [
            {"feature": "(HU) Cell DL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "DL Throughput Degradation", "reason": "Cell DL throughput decreased.", "recommended_action": "Check DL scheduler, bandwidth, CA activation, load balancing, and congestion."},
            {"feature": "(HU) User DL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "User Throughput Degradation", "reason": "User DL throughput decreased.", "recommended_action": "Check radio quality, PRB load, scheduler behavior, and user distribution."},
            {"feature": "(HU) DL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "Capacity / Congestion", "reason": "DL PRB utilization increased.", "recommended_action": "Check load balancing, CA usage, bandwidth, traffic distribution, and capacity expansion."},
            {"feature": "DL Average CQI", "bad_direction": "low", "threshold": 15, "severity": 3, "category": "Radio Quality Issue", "reason": "DL CQI decreased.", "recommended_action": "Check interference, PCI conflict/confusion, antenna tilt, azimuth, and coverage."},
            {"feature": "(HU) DL IBLER(%)", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "DL Radio Quality Issue", "reason": "DL IBLER increased.", "recommended_action": "Check interference, CQI, MCS, antenna tilt, and DL power."},
            {"feature": "DL RBLER", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "DL Radio Failure", "reason": "DL RBLER increased.", "recommended_action": "Check DL interference, poor coverage, CQI, MCS, and radio conditions."},
            {"feature": "(HU) PDSCH MCS", "bad_direction": "low", "threshold": 15, "severity": 2, "category": "Poor Modulation Efficiency", "reason": "PDSCH MCS decreased.", "recommended_action": "Check CQI, SINR, interference, antenna direction, and coverage."},
            {"feature": "Availability", "bad_direction": "low", "threshold": 1, "severity": 5, "category": "Availability Issue", "reason": "Cell availability decreased.", "recommended_action": "Check alarms, S1 issue, manual outage, system outage, and site availability."},
            {"feature": "(HU) Cell Unavail Time (s)", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "Cell Unavailability", "reason": "Cell unavailable time increased.", "recommended_action": "Check site outage, power issue, transmission issue, S1 failure, and alarms."},
            {"feature": "L.Traffic.ActiveUser.Dl.Avg", "bad_direction": "low", "threshold": 20, "severity": 1, "category": "Traffic Demand Drop", "reason": "DL active users decreased.", "recommended_action": "Validate if traffic drop is normal demand behavior before RF optimization."},
            {"feature": "MAC CA Traffic Ratio", "bad_direction": "low", "threshold": 20, "severity": 2, "category": "Carrier Aggregation Issue", "reason": "CA traffic ratio decreased.", "recommended_action": "Check CA activation, SCell availability, CA bands, and CA parameters."},
            {"feature": "DL Traffic QCI-9", "bad_direction": "low", "threshold": 20, "severity": 2, "category": "Default Bearer Traffic Drop", "reason": "QCI-9 DL traffic decreased.", "recommended_action": "Check packet data service, APN/data service, user demand, and internet traffic trend."},
            {"feature": "DL_CCE_AllocFail (%)", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "Control Channel Congestion", "reason": "DL CCE allocation failure increased.", "recommended_action": "Check PDCCH/CCE utilization, control channel capacity, and scheduler configuration."},
        ],
    },

    "UL Traffic": {
        "target_kpi": "(HU) UL Traffic Volume (GBytes)",
        "bad_direction": "low",
        "default_threshold": 30.0,
        "category": "Traffic",
        "output_prefix": "ul_traffic",
        "min_baseline_value": 0.1,
        "related_rules": [
            {"feature": "(HU) Cell UL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "UL Throughput Degradation", "reason": "Cell UL throughput decreased.", "recommended_action": "Check UL scheduler, UL PRB utilization, uplink interference, and power control."},
            {"feature": "(HU) User UL Average Throughput (Mbps)", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "UL User Throughput Degradation", "reason": "User UL throughput decreased.", "recommended_action": "Check UL radio quality, UL interference, PUSCH MCS, and UL PRB load."},
            {"feature": "(HU)UL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "UL Capacity / Congestion", "reason": "UL PRB utilization increased.", "recommended_action": "Check UL capacity, UL scheduling, uplink load, and traffic distribution."},
            {"feature": "(HU) Avg UL Interference(dBm)", "bad_direction": "high", "threshold": 10, "severity": 4, "category": "UL Interference Issue", "reason": "Average UL interference increased.", "recommended_action": "Check external interference, PIM, neighboring cells, and uplink noise rise."},
            {"feature": "L.UpPTS.Interference.Avg(dBm)", "bad_direction": "high", "threshold": 10, "severity": 3, "category": "UL Interference Issue", "reason": "UpPTS interference increased.", "recommended_action": "Check uplink interference source and TDD interference conditions."},
            {"feature": "(HU) UL IBLER(%)", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "UL Radio Quality Issue", "reason": "UL IBLER increased.", "recommended_action": "Check UL interference, PUSCH MCS, UE power, and coverage."},
            {"feature": "UL RBLER", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "UL Radio Failure", "reason": "UL RBLER increased.", "recommended_action": "Check UL interference, coverage, UE power, and uplink radio conditions."},
            {"feature": "(HU) PUSCH MCS", "bad_direction": "low", "threshold": 15, "severity": 2, "category": "UL Modulation Efficiency Issue", "reason": "PUSCH MCS decreased.", "recommended_action": "Check UL SINR, interference, UE power control, and uplink coverage."},
            {"feature": "L.Traffic.ActiveUser.UL.Avg", "bad_direction": "low", "threshold": 20, "severity": 1, "category": "UL Traffic Demand Drop", "reason": "UL active users decreased.", "recommended_action": "Validate traffic trend before applying RF action."},
        ],
    },

    "DL Throughput": {
        "target_kpi": "(HU) User DL Average Throughput (Mbps)",
        "bad_direction": "low",
        "default_threshold": 20.0,
        "category": "Integrity",
        "output_prefix": "dl_throughput",
        "min_baseline_value": 5.0,
        "related_rules": [
            {"feature": "(HU) DL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "DL Congestion", "reason": "DL PRB utilization increased while DL throughput decreased.", "recommended_action": "Check congestion, load balancing, CA, bandwidth, scheduler, and capacity expansion."},
            {"feature": "DL Average CQI", "bad_direction": "low", "threshold": 15, "severity": 4, "category": "Poor Radio Quality", "reason": "CQI decreased while DL throughput degraded.", "recommended_action": "Check interference, PCI, antenna tilt, azimuth, and coverage."},
            {"feature": "(HU) DL IBLER(%)", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "High DL Retransmission", "reason": "DL IBLER increased while DL throughput degraded.", "recommended_action": "Check BLER, CQI, MCS, DL power, and interference."},
            {"feature": "DL RBLER", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "DL Radio Block Errors", "reason": "DL RBLER increased while DL throughput degraded.", "recommended_action": "Check interference, radio quality, and coverage."},
            {"feature": "(HU) PDSCH MCS", "bad_direction": "low", "threshold": 15, "severity": 3, "category": "Low DL Modulation", "reason": "PDSCH MCS decreased while DL throughput degraded.", "recommended_action": "Check CQI, SINR, interference, and coverage."},
            {"feature": "MAC CA Traffic Ratio", "bad_direction": "low", "threshold": 20, "severity": 2, "category": "Low CA Usage", "reason": "CA traffic ratio decreased while DL throughput degraded.", "recommended_action": "Check CA activation, SCell availability, and CA configuration."},
            {"feature": "L.Traffic.ActiveUser.Dl.Avg", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "High User Load", "reason": "DL active users increased while DL throughput decreased.", "recommended_action": "Check load, scheduling, congestion, and user distribution."},
        ],
    },

    "UL Throughput": {
        "target_kpi": "(HU) User UL Average Throughput (Mbps)",
        "bad_direction": "low",
        "default_threshold": 20.0,
        "category": "Integrity",
        "output_prefix": "ul_throughput",
        "min_baseline_value": 2.0,
        "related_rules": [
            {"feature": "(HU)UL PRB Utilization(%)", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "UL Congestion", "reason": "UL PRB utilization increased while UL throughput degraded.", "recommended_action": "Check UL load, UL scheduler, and uplink capacity."},
            {"feature": "(HU) Avg UL Interference(dBm)", "bad_direction": "high", "threshold": 10, "severity": 4, "category": "UL Interference Issue", "reason": "UL interference increased while UL throughput degraded.", "recommended_action": "Check external interference, PIM, and uplink noise rise."},
            {"feature": "(HU) UL IBLER(%)", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "High UL Retransmission", "reason": "UL IBLER increased while UL throughput degraded.", "recommended_action": "Check UL BLER, interference, PUSCH MCS, and UE power."},
            {"feature": "UL RBLER", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "UL Radio Block Errors", "reason": "UL RBLER increased while UL throughput degraded.", "recommended_action": "Check UL coverage, interference, and UE power limitation."},
            {"feature": "(HU) PUSCH MCS", "bad_direction": "low", "threshold": 15, "severity": 3, "category": "Low UL Modulation", "reason": "PUSCH MCS decreased while UL throughput degraded.", "recommended_action": "Check uplink SINR, interference, and power control."},
            {"feature": "L.Traffic.ActiveUser.UL.Avg", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "High UL User Load", "reason": "UL active users increased while UL throughput decreased.", "recommended_action": "Check uplink scheduling, congestion, and load distribution."},
        ],
    },

    "RRC Setup SR": {
        "target_kpi": "(TE) RRC Setup SR%",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Accessibility",
        "output_prefix": "rrc_setup_sr",
        "min_baseline_value": 90.0,
        "related_rules": [
            {"feature": "L.RRC.ConnReq.Att", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "High RRC Attempts", "reason": "RRC attempts increased.", "recommended_action": "Check RACH load, access parameters, admission control, and overload."},
            {"feature": "RRC Setup Failure Time", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "RRC Failure Increase", "reason": "RRC setup failures increased.", "recommended_action": "Check RACH failures, no reply, rejection, admission control, and radio quality."},
            {"feature": "L.RRC.SetupFail.NoReply", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "RRC No Reply", "reason": "RRC no-reply failures increased.", "recommended_action": "Check coverage, interference, RACH configuration, and UE access conditions."},
            {"feature": "L.RRC.SetupFail.Rej", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "RRC Rejection", "reason": "RRC rejection failures increased.", "recommended_action": "Check admission control, overload, forbidden access, and MME overload."},
            {"feature": "L.RRC.SetupFail.Rej.MMEOverload", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "MME Overload", "reason": "RRC rejection due to MME overload increased.", "recommended_action": "Check MME/S1 signaling, core side load, and S1 interface."},
            {"feature": "L.RRC.SetupFail.ResFail", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "Radio Resource Failure", "reason": "RRC setup failures due to resource failure increased.", "recommended_action": "Check radio resources, PRB load, admission control, and congestion."},
            {"feature": "RACH Contention-Based Failures", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "RACH Failure", "reason": "RACH contention failures increased.", "recommended_action": "Check PRACH configuration, root sequence planning, preamble load, and coverage."},
        ],
    },

    "ERAB Setup SR": {
        "target_kpi": "ERAB Setup Success Rate",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Accessibility",
        "output_prefix": "erab_setup_sr",
        "min_baseline_value": 95.0,
        "related_rules": [
            {"feature": "L.E-RAB.AttEst", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "High ERAB Attempts", "reason": "E-RAB setup attempts increased.", "recommended_action": "Check access load, service attempts, and admission control."},
            {"feature": "ERAB Setup Failure Times", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "ERAB Failure Increase", "reason": "E-RAB setup failures increased.", "recommended_action": "Check ERAB failure reason counters, MME, TNL, RNL, and radio resources."},
            {"feature": "L.E-RAB.FailEst.NoRadioRes", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "No Radio Resource", "reason": "E-RAB failures due to no radio resources increased.", "recommended_action": "Check PRB load, admission control, congestion, and capacity."},
            {"feature": "L.E-RAB.FailEst.NoReply", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "No Reply Failure", "reason": "E-RAB no-reply failures increased.", "recommended_action": "Check radio quality, signaling, and UE response issues."},
            {"feature": "L.E-RAB.FailEst.MME", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "MME Related Failure", "reason": "E-RAB setup failures related to MME increased.", "recommended_action": "Check MME/core side, S1 signaling, and core load."},
            {"feature": "L.E-RAB.FailEst.TNL", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "Transport Network Failure", "reason": "E-RAB setup failures related to TNL increased.", "recommended_action": "Check transmission, backhaul, S1-U/S1-C, and transport path."},
        ],
    },

    "Drop Rate": {
        "target_kpi": "E-RAB Drop Rate (E-NodeB + MME) %",
        "bad_direction": "high",
        "default_threshold": 20.0,
        "category": "Retainability",
        "output_prefix": "drop_rate",
        "min_baseline_value": 0.0,
        "related_rules": [
            {"feature": "L.E-RAB.AbnormRel", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "Abnormal Release Increase", "reason": "E-RAB abnormal releases increased.", "recommended_action": "Check drop reason counters, radio quality, HO failures, and TNL/MME causes."},
            {"feature": "L.E-RAB.AbnormRel.Radio", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "Radio Drop Issue", "reason": "Radio abnormal releases increased.", "recommended_action": "Check coverage, interference, CQI, BLER, and antenna settings."},
            {"feature": "L.E-RAB.AbnormRel.Radio.ULSyncFail", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "UL Sync Failure", "reason": "Drops due to UL synchronization failure increased.", "recommended_action": "Check uplink coverage, UL interference, UE power, and timing advance."},
            {"feature": "L.E-RAB.AbnormRel.Radio.UuNoReply", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "Uu No Reply", "reason": "Drops due to Uu no-reply increased.", "recommended_action": "Check coverage holes, interference, and radio link quality."},
            {"feature": "L.E-RAB.AbnormRel.TNL", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "Transport Drop Issue", "reason": "Transport-related abnormal releases increased.", "recommended_action": "Check backhaul, transmission alarms, packet loss, and transport congestion."},
            {"feature": "L.E-RAB.AbnormRel.MME", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "MME Drop Issue", "reason": "MME-related abnormal releases increased.", "recommended_action": "Check core network, MME, S1 signaling, and S1 reset counters."},
            {"feature": "L.E-RAB.AbnormRel.HOFailure", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "HO Related Drop", "reason": "Abnormal releases related to HO failure increased.", "recommended_action": "Check neighbors, missing neighbors, A3 offset, CIO, TTT, and PCI issues."},
            {"feature": "RRC Connection Drop Rate%", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "RRC Drop Issue", "reason": "RRC connection drop rate increased.", "recommended_action": "Check radio quality, coverage, interference, re-establishment, and mobility."},
        ],
    },

    "HO Success Rate": {
        "target_kpi": "HO SR% Overall",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Mobility",
        "output_prefix": "ho_success_rate",
        "min_baseline_value": 90.0,
        "related_rules": [
            {"feature": "Intra_Freq HO Prepare Failed Times", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "Intra-Frequency HO Preparation Failure", "reason": "Intra-frequency HO preparation failures increased.", "recommended_action": "Check neighbor relations, target cell availability, admission control, and HO prep failure reasons."},
            {"feature": "Intra_Freq HO Execution Failed Times", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "Intra-Frequency HO Execution Failure", "reason": "Intra-frequency HO execution failures increased.", "recommended_action": "Check radio quality, A3 offset, TTT, CIO, PCI, and target cell coverage."},
            {"feature": "Inter_Freq HO Prepare Failed Times", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "Inter-Frequency HO Preparation Failure", "reason": "Inter-frequency HO preparation failures increased.", "recommended_action": "Check inter-frequency neighbors, measurement configuration, frequency priority, and target availability."},
            {"feature": "Inter_Freq HO Execution Failed Times", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "Inter-Frequency HO Execution Failure", "reason": "Inter-frequency HO execution failures increased.", "recommended_action": "Check A3/A5 thresholds, TTT, CIO, target cell coverage, and PCI conflicts."},
            {"feature": "S1 HO Execution Failed Times", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "S1 HO Failure", "reason": "S1 HO execution failures increased.", "recommended_action": "Check S1 handover path, MME, transport, and target eNodeB response."},
            {"feature": "X2 Intra-Freq Failure", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "X2 Intra-Frequency HO Failure", "reason": "X2 intra-frequency HO failures increased.", "recommended_action": "Check X2 links, neighbor relation, target cell, and mobility parameters."},
            {"feature": "X2 Inter-Freq Failure", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "X2 Inter-Frequency HO Failure", "reason": "X2 inter-frequency HO failures increased.", "recommended_action": "Check X2 links, inter-frequency neighbors, and target frequency settings."},
            {"feature": "L.HHO.PingPongHo", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "Ping-Pong HO Issue", "reason": "Ping-pong handovers increased.", "recommended_action": "Tune hysteresis, TTT, CIO, A3 offset, and neighbor priorities."},
        ],
    },

    "Availability": {
        "target_kpi": "Availability",
        "bad_direction": "low",
        "default_threshold": 1.0,
        "category": "Availability",
        "output_prefix": "availability",
        "min_baseline_value": 99.0,
        "related_rules": [
            {"feature": "(HU) Cell Unavail Time (s)", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "Cell Unavailable Time Increase", "reason": "Cell unavailable time increased.", "recommended_action": "Check outage, alarms, power, transmission, and site status."},
            {"feature": "L.Cell.Unavail.Dur.Sys(s)", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "System Unavailability", "reason": "System unavailability duration increased.", "recommended_action": "Check system faults, board alarms, transmission, and eNodeB health."},
            {"feature": "L.Cell.Unavail.Dur.Manual(s)", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "Manual Unavailability", "reason": "Manual unavailability duration increased.", "recommended_action": "Check manual lock, planned work, maintenance activity, and cell administrative state."},
            {"feature": "L.Cell.Unavail.Dur.Sys.S1Fail(s)", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "S1 Failure Unavailability", "reason": "S1 failure unavailability duration increased.", "recommended_action": "Check S1 link, MME connection, transmission, and core network alarms."},
        ],
    },

    "RACH Success Rate": {
        "target_kpi": "(HU) RACH Success Rate(%)",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "Accessibility",
        "output_prefix": "rach_success_rate",
        "min_baseline_value": 95.0,
        "related_rules": [
            {"feature": "RACH Setup Failed Number", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "RACH Setup Failures", "reason": "RACH setup failures increased.", "recommended_action": "Check PRACH parameters, root sequence planning, coverage, interference, and access load."},
            {"feature": "RACH Contention-Based Failures", "bad_direction": "high", "threshold": 20, "severity": 3, "category": "Contention-Based RACH Failure", "reason": "Contention-based RACH failures increased.", "recommended_action": "Check preamble congestion, PRACH configuration, root sequence, and access load."},
            {"feature": "RACH_att", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "High RACH Attempts", "reason": "RACH attempts increased.", "recommended_action": "Check access load, coverage, PRACH capacity, and random access configuration."},
            {"feature": "RACH Contention-Based SR", "bad_direction": "low", "threshold": 5, "severity": 3, "category": "Contention-Based RACH SR Drop", "reason": "Contention-based RACH success rate decreased.", "recommended_action": "Check PRACH configuration, root sequence planning, and access congestion."},
            {"feature": "RACH Non-Contention-Based SR", "bad_direction": "low", "threshold": 5, "severity": 3, "category": "Non-Contention RACH SR Drop", "reason": "Non-contention RACH success rate decreased.", "recommended_action": "Check HO-related RACH, target cell access, and PRACH settings."},
        ],
    },

    "CSFB KPI": {
        "target_kpi": "CSFB SR%",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "CSFB / Voice Accessibility",
        "output_prefix": "csfb_kpi",
        "min_baseline_value": 90.0,
        "related_rules": [
            {"feature": "CSFB Failure Times", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "CSFB Failure Increase", "reason": "CSFB failure times increased.", "recommended_action": "Check CSFB failure reasons, MME/S1 signaling, RRC redirection, and target 2G/3G availability."},
            {"feature": "L.CSFB.PrepAtt", "bad_direction": "high", "threshold": 20, "severity": 2, "category": "High CSFB Preparation Attempts", "reason": "CSFB preparation attempts increased, which may increase CSFB load.", "recommended_action": "Check CSFB traffic demand, MME load, S1 signaling, and whether the increase is normal voice demand."},
            {"feature": "L.RRCRedirection.E2W.CSFB", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "E2W CSFB Redirection Drop", "reason": "LTE-to-3G CSFB redirection count decreased compared with baseline.", "recommended_action": "Check UTRAN neighbor configuration, 3G target coverage, UTRAN frequency priority, and CSFB redirection settings."},
            {"feature": "L.RRCRedirection.E2G.CSFB", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "E2G CSFB Redirection Drop", "reason": "LTE-to-2G CSFB redirection count decreased compared with baseline.", "recommended_action": "Check GERAN neighbor configuration, 2G target coverage, GERAN frequency priority, LAI/TAI mapping, and CSFB redirection settings."},
            {"feature": "(TE) RRC Setup SR%", "bad_direction": "low", "threshold": 5, "severity": 4, "category": "LTE RRC Access Issue", "reason": "RRC setup success rate decreased, which can affect CSFB before fallback starts.", "recommended_action": "Check LTE RRC accessibility, RACH, RRC setup failures, admission control, and radio quality."},
            {"feature": "ERAB Setup Success Rate", "bad_direction": "low", "threshold": 5, "severity": 3, "category": "E-RAB Setup Issue", "reason": "E-RAB setup success rate decreased, indicating possible access or core signaling issue affecting services.", "recommended_action": "Check E-RAB setup failures, MME/TNL/RNL causes, admission control, radio resources, and S1 signaling."},
        ],
    },

    "VoLTE KPIs": {
        "target_kpi": "BA_Voice E2E VQI",
        "bad_direction": "low",
        "default_threshold": 5.0,
        "category": "VoLTE",
        "output_prefix": "volte_kpis",
        "min_baseline_value": 3.5,
        "related_rules": [
            {"feature": "VoLTE Traffic (Erl)(Erl)", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "VoLTE Traffic Drop", "reason": "VoLTE traffic decreased.", "recommended_action": "Check VoLTE user demand, IMS service, VoLTE coverage, and QCI-1 traffic."},
            {"feature": "L.Traffic.User.VoIP.Avg", "bad_direction": "low", "threshold": 20, "severity": 2, "category": "VoIP User Drop", "reason": "Average VoIP users decreased.", "recommended_action": "Check VoLTE traffic demand, service availability, and IMS registration behavior."},
            {"feature": "DL Traffic QCI-1", "bad_direction": "low", "threshold": 20, "severity": 3, "category": "QCI-1 DL Traffic Drop", "reason": "QCI-1 DL traffic decreased.", "recommended_action": "Check VoLTE bearer traffic, IMS service, and VoLTE user behavior."},
            {"feature": "E-RAB Drop(ENB+MME)_Tot", "bad_direction": "high", "threshold": 20, "severity": 5, "category": "VoLTE Retainability Risk", "reason": "Total E-RAB drops increased.", "recommended_action": "Check VoLTE drops, radio quality, TNL/MME causes, and mobility."},
            {"feature": "E-RAB Drop Rate QCI 7", "bad_direction": "high", "threshold": 20, "severity": 4, "category": "QCI-7 Drop Issue", "reason": "QCI-7 drop rate increased.", "recommended_action": "Check VoLTE-related bearer retainability and radio quality."},
            {"feature": "BA_Overall SRVCC HO Execution Success Rate (%)", "bad_direction": "low", "threshold": 5, "severity": 4, "category": "SRVCC Execution Degradation", "reason": "SRVCC HO execution success rate decreased.", "recommended_action": "Check SRVCC neighbors, 2G/3G target cells, IMS/SRVCC configuration, and mobility parameters."},
            {"feature": "BA_Overall SRVCC HO Preparation Success Rate (%)", "bad_direction": "low", "threshold": 5, "severity": 3, "category": "SRVCC Preparation Degradation", "reason": "SRVCC HO preparation success rate decreased.", "recommended_action": "Check SRVCC preparation, target availability, MSC/MME coordination, and neighbor definitions."},
        ],
    },
}
