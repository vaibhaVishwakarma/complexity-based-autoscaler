"""
contracts/baselines.py — Formal Typed Contract for Canonical Baseline Benchmark Outputs
================================================================================
Role:
    Defines runtime type validation schemas and contract loaders for baseline benchmark
    outputs across the 13 canonical evaluation regimes. Downstream gates (OpenEvolve
    evaluators, multi-seed statistical analysis, and plotting scripts) use this schema
    to dynamically load baseline costs and performance surfaces without hardcoding.

AGENTS.md Compliance:
    Rule #2: Decoupled Linkage & Zero Hardcoding.
    Rule #3: Clean root module imports; no ad-hoc sys.path hacks.
    Rule #4: Self-documenting structure and inline comments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BaselineRunResult(BaseModel):
    """Execution outcome for a single (regime, controller) benchmark run."""
    regime: str = Field(..., description="Canonical regime name (e.g. suite1_flat, suite2_shock)")
    controller: str = Field(..., description="Human-readable controller name")
    key: str = Field(..., description="Identifier key used in continuum_bench CLI")
    status: str = Field(..., description="Run status ('SUCCESS', 'FAILED')")
    completed: int = Field(0, description="Count of successfully finished requests")
    pending: int = Field(0, description="Count of pending/unfinished requests at simulation drain")
    mean_workers: float = Field(..., ge=0.0, description="Time-weighted average active worker replicas")
    worker_seconds: float = Field(..., ge=0.0, description="Total provisioned worker-seconds")
    mean_latency: float = Field(..., ge=0.0, description="Mean end-to-end task latency in seconds")
    p95_latency: float = Field(..., ge=0.0, description="95th percentile task latency in seconds")
    p99_latency: float = Field(..., ge=0.0, description="99th percentile task latency in seconds")
    queue_wait_mean: float = Field(..., ge=0.0, description="Mean task queuing delay in seconds")
    scaling_deltas: float = Field(..., ge=0.0, description="Total absolute worker scaling adjustments")
    deadline_misses: int = Field(..., ge=0, description="Number of tasks exceeding SLA deadline (15s)")
    elapsed_s: float = Field(..., ge=0.0, description="Wall-clock simulation execution time in seconds")


class BaselineAggregateMetrics(BaseModel):
    """Authoritative aggregated baseline reference metrics across the 13 canonical suites."""
    fixed_capacity_worker_seconds: float = Field(
        ...,
        gt=0.0,
        description="Total worker-seconds provisioned by Fixed Peak across all 13 canonical regimes",
    )
    inferline_canonical_cost_ws: float = Field(
        ...,
        gt=0.0,
        description="Total worker-seconds provisioned by InferLine Exact across all 13 canonical regimes",
    )
    inferline_realism_cost_ws: Optional[float] = Field(
        None,
        description="Optional realism-triad worker-seconds for InferLine",
    )
    hpa_canonical_cost_ws: float = Field(
        ...,
        gt=0.0,
        description="Total worker-seconds provisioned by Kubernetes HPA across all 13 canonical regimes",
    )
    keda_canonical_cost_ws: float = Field(
        ...,
        gt=0.0,
        description="Total worker-seconds provisioned by KEDA across all 13 canonical regimes",
    )
    total_runs: int = Field(..., ge=1, description="Total benchmark runs attempted")
    successful_runs: int = Field(..., ge=1, description="Total runs that completed successfully")


class BaselineManifest(BaseModel):
    """Authoritative Manifest schema for output/suite_baselines_runs/manifest.json."""
    manifest_version: str = Field("1.0.0", description="Contract schema version")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    seed: int = Field(42, description="Simulation deterministic seed")
    controllers: List[str] = Field(..., description="List of evaluated baseline controller keys")
    regimes: List[str] = Field(..., description="List of evaluated 13 canonical regimes")
    aggregates: BaselineAggregateMetrics = Field(..., description="Aggregated reference costs")
    runs: List[BaselineRunResult] = Field(..., description="Per-run detailed telemetry")


def load_baselines_manifest(path: Optional[Path] = None) -> BaselineManifest:
    """Load and validate the authoritative baseline benchmark manifest."""
    manifest_path = path or (Path("output") / "suite_baselines_runs" / "manifest.json")
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Baselines manifest not found at {manifest_path}. "
            "Execute 'python -m scripts.run_suite_baselines' to generate it."
        )
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BaselineManifest.model_validate(data)
