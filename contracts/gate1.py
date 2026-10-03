"""
contracts/gate1.py — Formal Typed Contract for Validity Gate 1
================================================================================
Role:
    Defines runtime type validation schemas and contract loaders for Gate 1 outputs
    and calibration configurations. Downstream consumers (Gate 2, autoscalers, or
    evaluators) use this schema to ingest Gate 1 parameters without code coupling
    or hardcoding.

Inputs:
    - JSON manifests or dictionary payloads emitted by Gate 1 calibration.

Outputs:
    - Validated Pydantic models:
        * Gate1PassStatus
        * Gate1CalibrationConfig
        * Gate1VerificationResult
        * Gate1AciOnlineReport
        * Gate1SelectiveRiskEntry
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Gate1PassStatus(BaseModel):
    """Boolean pass flags for independent Gate 1 criteria."""
    empirical_coverage_pass: bool = Field(..., description="Coverage >= target (1 - alpha)")
    err_selective_pass: bool = Field(..., description="Selective fast-path error <= threshold")
    fp_frac_pass: bool = Field(..., description="Fast-path singleton rate >= threshold")
    overall: bool = Field(..., description="Composite overall pass status")


class Gate1CalibrationConfig(BaseModel):
    """
    Authoritative Gate 1 Conformal Calibration Contract.
    Matches the schema of gate1/configs/calibration_config.json.
    """
    alpha: float = Field(0.1, gt=0.0, lt=1.0, description="Miscoverage rate target (e.g. 0.1 for 90% coverage)")
    q_hat: float = Field(..., gt=0.0, le=1.0, description="Calibrated RAPS quantile cut-off")
    score_function: str = Field(..., min_length=1, description="Score function used (e.g. RAPS)")
    k_reg: int = Field(5, ge=0, description="RAPS regularization rank threshold")
    lambda_reg: float = Field(0.01, ge=0.0, description="RAPS regularization penalty weight")
    temperature: float = Field(1.0, ge=1.0, description="Softmax scaling temperature (must be >= 1.0)")
    temperature_constraint: Optional[str] = None
    num_classes: int = Field(182, ge=1, description="Number of target classes")
    dataset: str = Field(..., min_length=1, description="Dataset identifier")
    model_type: str = Field(..., min_length=1, description="Architecture description")
    num_epochs: int = Field(20, ge=1)
    split: str = Field(..., min_length=1)
    cal_top1_accuracy: float = Field(..., ge=0.0, le=1.0)
    test_top1_accuracy: float = Field(..., ge=0.0, le=1.0)
    empirical_coverage: float = Field(..., ge=0.0, le=1.0)
    fast_path_fraction: float = Field(..., ge=0.0, le=1.0)
    err_selective: float = Field(..., ge=0.0, le=1.0)
    err_selective_note: Optional[str] = None
    mean_set_size: float = Field(..., ge=1.0)
    gate1_passed: Gate1PassStatus
    scrutiny_fixes: Dict[str, str] = Field(default_factory=dict)

    @field_validator("temperature")
    @classmethod
    def validate_temperature_scaling(cls, v: float) -> float:
        """Enforces Guo et al. 2017: T < 1.0 is prohibited to prevent overconfidence."""
        if v < 1.0:
            raise ValueError(f"Temperature T={v} < 1.0 is prohibited (artificially inflates singletons).")
        return v


class Gate1VerificationResult(BaseModel):
    """
    Runtime verification output produced by recalibrate_onnx or evaluation passes.
    """
    images_evaluated: int = Field(..., ge=1)
    empirical_coverage: float = Field(..., ge=0.0, le=1.0)
    fast_path_coverage: float = Field(..., ge=0.0, le=1.0)
    selective_risk: float = Field(..., ge=0.0, le=1.0)
    mean_set_size: float = Field(..., ge=1.0)
    coverage_passed: bool
    fast_path_passed: bool
    selective_risk_passed: bool
    overall_passed: bool


class Gate1AciOnlineReport(BaseModel):
    """
    Online Adaptive Conformal Inference (ACI) stream benchmark report.
    Matches schema of gate1/output/aci_online_report.json.
    """
    gamma: float = Field(..., gt=0.0, description="ACI online step size learning rate")
    target_alpha: float = Field(..., gt=0.0, lt=1.0, description="Target miscoverage rate")
    overall_coverage: float = Field(..., ge=0.0, le=1.0, description="Overall streaming empirical coverage")
    phase1_clean_coverage: float = Field(..., ge=0.0, le=1.0, description="Clean phase coverage")
    phase2_ood_noise_coverage: float = Field(..., ge=0.0, le=1.0, description="OOD noise phase coverage")
    phase3_recovery_coverage: float = Field(..., ge=0.0, le=1.0, description="Post-shift recovery coverage")
    overall_fast_path_fraction: float = Field(..., ge=0.0, le=1.0, description="Overall fast-path offload fraction")
    overall_mean_set_size: float = Field(..., ge=1.0, description="Mean prediction set size across stream")
    total_stream_requests: int = Field(..., ge=1, description="Total image requests processed in stream")
    aci_passed: bool = Field(..., description="Whether overall coverage >= (1 - target_alpha)")


class Gate1SelectiveRiskEntry(BaseModel):
    """
    Single corruption & severity evaluation entry for Tiny ImageNet-C.
    Matches individual item in gate1/output/selective_error_report.json.
    """
    benchmark: str = Field(..., min_length=1)
    corruption: str = Field(..., min_length=1)
    severity: int = Field(..., ge=1, le=5)
    empirical_coverage: float = Field(..., ge=0.0, le=1.0)
    fast_path_fraction: float = Field(..., ge=0.0, le=1.0)
    err_selective: Optional[float] = Field(None, ge=0.0, le=1.0)
    err_selective_str: Optional[str] = None
    mean_set_size: float = Field(..., ge=0.0)
    total_evaluated: int = Field(..., ge=1)
    aci_final_alpha: Optional[float] = None
    aci_mean_alpha: Optional[float] = None
    aci_coverage_target: Optional[float] = None


def load_gate1_config(path: str | Path = "gate1/configs/calibration_config.json") -> Gate1CalibrationConfig:
    """
    Load and type-validate Gate 1 configuration from disk.
    
    Raises:
        FileNotFoundError: If the specified config file does not exist.
        ValidationError: If the schema or value constraints fail.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Gate 1 configuration not found at: {file_path.resolve()}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate against Pydantic schema
    return Gate1CalibrationConfig.model_validate(data)


def load_gate1_aci_report(path: str | Path = "gate1/output/aci_online_report.json") -> Gate1AciOnlineReport:
    """
    Load and type-validate Gate 1 ACI online benchmark report.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Gate 1 ACI report not found at: {file_path.resolve()}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Gate1AciOnlineReport.model_validate(data)


def load_gate1_selective_risk_report(
    path: str | Path = "gate1/output/selective_error_report.json"
) -> List[Gate1SelectiveRiskEntry]:
    """
    Load and type-validate Gate 1 Selective Risk (ImageNet-C) report.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Gate 1 Selective Risk report not found at: {file_path.resolve()}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list of corruption entries in {file_path}, got {type(data).__name__}")

    return [Gate1SelectiveRiskEntry.model_validate(entry) for entry in data]
