"""
contracts — Universal Typed Contracts for Evaluation, Calibration, and Profiling
"""

from contracts.calibration import (
    Gate1CalibrationConfig,
    Gate1PassStatus,
    Gate1VerificationResult,
    Gate1AciOnlineReport,
    Gate1SelectiveRiskEntry,
    load_gate1_config,
    load_gate1_aci_report,
    load_gate1_selective_risk_report,
)
from contracts.profiling import (
    Gate2BatchProfileEntry,
    Gate2HardwareProfile,
    Gate2SpearmanQueueResult,
    Gate2SpearmanReport,
    load_gate2_profiles,
    load_gate2_spearman,
)

from contracts.baselines import (
    BaselineRunResult,
    BaselineAggregateMetrics,
    BaselineManifest,
    load_baselines_manifest,
)

# Canonical aliases
CalibrationConfig = Gate1CalibrationConfig
CalibrationPassStatus = Gate1PassStatus
HardwareProfile = Gate2HardwareProfile
SpearmanReport = Gate2SpearmanReport

load_calibration_config = load_gate1_config
load_hardware_profiles = load_gate2_profiles
load_spearman_report = load_gate2_spearman

__all__ = [
    "Gate1CalibrationConfig",
    "Gate1PassStatus",
    "Gate1VerificationResult",
    "Gate1AciOnlineReport",
    "Gate1SelectiveRiskEntry",
    "load_gate1_config",
    "load_gate1_aci_report",
    "load_gate1_selective_risk_report",
    "Gate2BatchProfileEntry",
    "Gate2HardwareProfile",
    "Gate2SpearmanQueueResult",
    "Gate2SpearmanReport",
    "load_gate2_profiles",
    "load_gate2_spearman",
    "BaselineRunResult",
    "BaselineAggregateMetrics",
    "BaselineManifest",
    "load_baselines_manifest",
    "CalibrationConfig",
    "CalibrationPassStatus",
    "HardwareProfile",
    "SpearmanReport",
    "load_calibration_config",
    "load_hardware_profiles",
    "load_spearman_report",
]

