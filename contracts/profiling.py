"""
contracts/gate2.py — Formal Typed Contract for Validity Gate 2 (Model Profiling)
================================================================================
Role:
    Defines runtime type validation schemas and contract loaders for Gate 2 service
    profiling manifests and queuing-aware Spearman correlation outputs.
    Downstream consumers (Gate 3, Gate 4 autoscaler, ContinuumBench simulator)
    use this schema to dynamically ingest empirical hardware latency surfaces and
    worker throughput capacities without hardcoding.

Inputs:
    - gate2/output-gpu-t4/triton_service_profiles.json
    - gate2/output-gpu-t4/gate2_spearman_result.json

Outputs:
    - Validated Pydantic models:
        * Gate2BatchProfileEntry
        * Gate2HardwareProfile
        * Gate2SpearmanQueueResult
        * Gate2SpearmanReport
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Gate2BatchProfileEntry(BaseModel):
    """Profile metrics for a single batch size on profiled hardware."""
    batch_size: int = Field(..., ge=1, description="Evaluated batch size b")
    p50_ms: float = Field(..., gt=0.0, description="Median execution latency (ms)")
    p95_ms: float = Field(..., gt=0.0, description="95th percentile execution latency (ms)")
    p99_ms: float = Field(..., gt=0.0, description="99th percentile execution latency (ms)")
    mean_ms: float = Field(..., gt=0.0, description="Mean execution latency (ms)")
    std_ms: float = Field(..., ge=0.0, description="Standard deviation (ms)")
    n_runs: int = Field(..., ge=1, description="Number of timed evaluation runs")
    batch_formation_wait_ms_mean: float = Field(..., ge=0.0, description="Erlang batch formation wait mean (ms)")
    batch_formation_wait_ms_p95: float = Field(..., ge=0.0, description="Erlang batch formation wait p95 (ms)")
    jitter_cv: float = Field(0.05, ge=0.0, description="Hardware execution jitter CV (5%)")
    jitter_sigma_ms: float = Field(..., ge=0.0, description="Jitter standard deviation (ms)")
    e2e_p50_ms: float = Field(..., gt=0.0, description="End-to-end P50 latency including batch wait (ms)")


class Gate2HardwareProfile(BaseModel):
    """
    Authoritative Hardware Latency Surface Profile.
    Matches schema of gate2/output-gpu-t4/triton_service_profiles.json.
    """
    description: str = Field(..., min_length=1)
    hardware: str = Field(..., min_length=1)
    warmup_runs: int = Field(..., ge=1)
    timed_runs: int = Field(..., ge=1)
    batch_sizes: List[int] = Field(..., min_length=1)
    synthetic_tensors: bool = Field(True)
    preprocessing_note: Optional[str] = None
    gpu_profiles_raw: List[Gate2BatchProfileEntry] = Field(..., min_length=1)

    def get_batch_profile(self, batch_size: int) -> Gate2BatchProfileEntry:
        """Retrieve profile entry for specific batch size."""
        for entry in self.gpu_profiles_raw:
            if entry.batch_size == batch_size:
                return entry
        raise KeyError(f"Batch size {batch_size} not found in profile for {self.hardware}")

    def compute_service_capacity_rps(self, batch_size: int = 8, batch_timeout_s: float = 0.040) -> float:
        """
        Derive closed-form worker throughput capacity mu_cloud (RPS/node)
        mu = B / (T_profile(B) + tau_timeout)
        """
        entry = self.get_batch_profile(batch_size)
        t_exec_s = entry.p50_ms / 1000.0
        total_cycle_s = t_exec_s + batch_timeout_s
        return float(batch_size / total_cycle_s)


class Gate2SpearmanQueueResult(BaseModel):
    """Queuing-aware correlation metrics at specific utilization level rho."""
    queue_utilization_rho: float = Field(..., ge=0.0, le=1.0)
    mean_Wq_ms: float = Field(..., ge=0.0)
    r_s: float = Field(..., ge=-1.0, le=1.0, description="Spearman rank correlation coefficient")
    p_value: float = Field(..., ge=0.0, le=1.0)
    t_statistic: float
    n_samples: int = Field(..., ge=1)
    gate_pass: bool = Field(...)
    fast_slow_overlap_frac: float = Field(..., ge=0.0, le=1.0)
    fast_path_mean_ms: float = Field(..., gt=0.0)
    slow_path_mean_ms: float = Field(..., gt=0.0)


class Gate2SpearmanReport(BaseModel):
    """
    Authoritative Gate 2 Workload-Complexity Correlation Report.
    Matches schema of gate2/output-gpu-t4/gate2_spearman_result.json.
    """
    hardware: str = Field(..., min_length=1)
    n_requests: int = Field(..., ge=1)
    fast_path_frac: float = Field(..., ge=0.0, le=1.0)
    bin_fracs: Dict[str, float]
    batch_dist: Dict[str, float]
    jitter_cv: float = Field(..., ge=0.0)
    arrival_rate_rps: float = Field(..., gt=0.0)
    results_by_queue_utilization: Dict[str, Gate2SpearmanQueueResult]
    gate_pass_all_rho: bool
    gate_pass_rho_0_7: bool
    constant_flop_disclosure: str
    scrutiny_fixes: Dict[str, str] = Field(default_factory=dict)


def load_gate2_profiles(
    path: str | Path = "gate2/output-gpu-t4/triton_service_profiles.json"
) -> Gate2HardwareProfile:
    """Load and type-validate Gate 2 service latency profiles."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Gate 2 profile manifest not found at: {file_path.resolve()}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Gate2HardwareProfile.model_validate(data)


def load_gate2_spearman(
    path: str | Path = "gate2/output-gpu-t4/gate2_spearman_result.json"
) -> Gate2SpearmanReport:
    """Load and type-validate Gate 2 Spearman correlation report."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Gate 2 Spearman result not found at: {file_path.resolve()}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return Gate2SpearmanReport.model_validate(data)
