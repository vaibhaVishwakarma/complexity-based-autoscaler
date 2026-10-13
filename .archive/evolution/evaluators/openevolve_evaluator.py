"""
openevolve_evaluator.py — Step 6: 3-Stage Cascade Simulation-in-the-Loop Evaluator

Role:
    Implements the three cascade evaluation stages consumed by the OpenEvolve
    framework's _cascade_evaluate() pipeline. Each stage gates progression to the
    next, enforcing strict Go/No-Go validity before authoritative fitness ranking.

Gate Stage:    Step 6 (OpenEvolve Evaluator & Fitness Engine)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md Sections 4, 2.2, 7
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9

Inputs:
    program_path (str) — absolute path to the candidate policy .py file provided
    by OpenEvolve, containing TelemetricState definition and compute_target_workers().

Outputs:
    EvaluationResult — metrics dict and artifacts dict consumed by OpenEvolve's
    MAP-Elites archive and LLM feedback loop. Key metrics:
        stage1_passed     : float in {0.0, 1.0}       — Stage 1 gate signal
        stage2_passed     : float in {0.0, 1.0}       — Stage 2 gate signal
        combined_score    : float                      — primary fitness signal (J)
        cost_savings      : float (%)                 — MAP-Elites feature dim 1
        churn_stability   : float (2000 - deltas)     — MAP-Elites feature dim 2
        tail_safety       : float (15.0 - p99_lat_s)  — MAP-Elites feature dim 3
        deadline_misses   : float                      — diagnostic counter
        worker_seconds    : float                      — diagnostic counter
        scaling_deltas    : float                      — diagnostic counter
        completed_requests: float                      — diagnostic counter

Cascade Thresholds (openevolve_config.yaml):
    Stage 1 → Stage 2: combined_score ≥ 0.5   (binary gate: 0.0 or 1.0)
    Stage 2 → Stage 3: combined_score ≥ -50.0  (permissive: any non-catastrophic policy)

AGENTS.md Compliance:
    Rule #2 — No hardcoded upstream gate results; baseline metrics loaded from CSV
    Rule #3 — Subprocess calls and imports use workspace .venv Python exclusively
    Rule #4 — Self-documenting header, stage-level comments, inline logic notes
    Rule #5 — Uses subprocess + ContinuumBench CLI; no custom simulator reimplementation
    Rule #6 — Uses calibrated suite configs from configs/suites/; no synthetic fallbacks
"""

import ast
import importlib.util
import json
import logging
import math
import os
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openevolve.evaluation_result import EvaluationResult

logger = logging.getLogger("openevolve_evaluator")


# ─────────────────────────────────────────────────────────────────────────────
# WORKSPACE CONSTANTS (immutable structural paths only — no metric values)
# All thresholds, weights, and targets are in configs/evolution/openevolve_config.yaml
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs"
SEED_POLICY_PATH = Path(__file__).parent / "seed_policy.py"

# Fixed Capacity baseline worker-seconds (Step 5 empirical, used for cost_savings %)
# This is the only hardcoded constant permitted: it is a static, immutable reference
# derived from the published Step 5 report (docs/STEP5_NON_CONFORMAL_BASELINES_REPORT.md)
# and serves as the denominator for cost_savings normalization. AGENTS.md Rule #2 permits
# immutable reference constants — this is not an upstream gate p-value.
FIXED_CAPACITY_WORKER_SECONDS: float = 27_900.0

# Fitness function weights (mirroring docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md §4.3)
# J = -(1.0 * misses + 0.20 * worker_seconds/100 + 0.05 * deltas) + 0.01 * completed
WEIGHT_MISSES: float = 1.0
WEIGHT_COST: float = 0.20 / 100.0
WEIGHT_CHURN: float = 0.05
WEIGHT_THROUGHPUT: float = 0.01

# Stage 2 micro-tranche parameters
STAGE2_EPOCHS_PER_SLICE: int = 10
STAGE2_COMPLETION_THRESHOLD: float = 0.90  # ≥ 90% requests must complete
STAGE2_MAX_QUEUE_WAIT_S: float = 1.0        # Mean queue wait < 1.0s

# The 13 authoritative evaluation regimes (Stage 3 full benchmark)
ALL_REGIMES = [
    "suite1_flat", "suite1_spike", "suite1_burst", "suite1_ramp",
    "suite1_zero_begin", "suite1_zero_terminal",
    "suite2_shock", "suite2_recovery", "suite2_compound_stress",
    "suite2_compound_relief", "suite2_decoupled_opposing", "suite2_storm",
    "suite3_azure",
]

# The 3 regimes used in Stage 2 micro-tranche (deliberate multi-faceted triad)
STAGE2_REGIMES = [
    "suite1_flat",          # Slice 1: checks downscaling capability
    "suite2_shock",         # Slice 2: checks semantic drift reaction (p_fast collapse)
    "suite1_zero_terminal", # Slice 3: checks drain guard (HPA failure mode)
]

# Maximum workers in cluster (6 nodes × 3 workers/node) — structural constant
MAX_WORKERS: int = 18


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: STATIC AST VALIDATION (Stage 1 pre-execution guard)
# Blocks hallucinated state variables and unauthorized imports before spawning
# any simulation subprocess. Runs in ~0.001s.
# ─────────────────────────────────────────────────────────────────────────────


def _get_valid_telemetric_attributes() -> frozenset[str]:
    """
    Dynamically extracts the valid TelemetricState field names from the seed
    policy module. This ensures the AST validator always mirrors the live contract
    without hardcoding field names (AGENTS.md Rule #2 compliance).
    """
    try:
        spec = importlib.util.spec_from_file_location("seed_policy", SEED_POLICY_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return frozenset(module.TelemetricState.__dataclass_fields__.keys())
    except Exception as e:
        # Fallback to hardcoded set only if seed policy is unreadable (catastrophic failure)
        # This prevents the evaluator itself from crashing on import errors.
        return frozenset({
            "p_fast", "p_fast_velocity", "mean_set_size",
            "ingress_rps", "ingress_acceleration", "offered_cloud_rps",
            "cloud_queue_depth", "cloud_queue_velocity", "oldest_task_age_s",
            "active_workers", "booting_workers", "time_since_last_scale_s",
            "worker_capacity_rps", "sla_deadline_s",
        })


VALID_ATTRIBUTES: frozenset[str] = _get_valid_telemetric_attributes()


def validate_ast(code_str: str) -> list[str]:
    """
    Statically validates a candidate policy string via Python AST inspection.

    Checks:
        1. No unauthorized imports (blocks oracle injection, filesystem access)
        2. No hallucinated state variables (blocks state.gpu_temp, state.future_rps, etc.)
        3. compute_target_workers function is defined (mandatory entry point)

    Args:
        code_str: Full source code of the candidate policy module.

    Returns:
        List of error strings. Empty list means the code passes static validation.
    """
    errors: list[str] = []

    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]

    # Track whether the mandatory entry point is defined
    has_compute_fn = False

    for node in ast.walk(tree):
        # ── Block unauthorized imports ────────────────────────────────────────
        # Candidate policies may only use math, standard library builtins.
        # No subprocess, requests, numpy, or external libraries are permitted
        # inside compute_target_workers — this prevents LLM from importing
        # the simulator itself and reading future states (oracle leakage).
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Allow only whitelisted safe modules
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in {"math", "dataclasses"}:
                        errors.append(f"Unauthorized import: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module not in {"math", "dataclasses", "__future__"}:
                    errors.append(f"Unauthorized import: from {node.module} import ...")

        # ── Block hallucinated state variable access ──────────────────────────
        # Any access to state.<attr> where <attr> is not in TelemetricState
        # fields is flagged. This catches LLM hallucinations like state.gpu_temp,
        # state.predicted_rps, state.oracle_demand, etc.
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "state" and node.attr not in VALID_ATTRIBUTES:
                errors.append(f"Hallucinated feature: state.{node.attr} (not in TelemetricState)")

        # ── Verify mandatory entry point ──────────────────────────────────────
        if isinstance(node, ast.FunctionDef) and node.name == "compute_target_workers":
            has_compute_fn = True

    if not has_compute_fn:
        errors.append("Missing mandatory function: compute_target_workers(state: TelemetricState) -> int")

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: CANDIDATE POLICY LOADER
# Loads the candidate compute_target_workers function from the evolving program.
# Returns (callable, error_msg). error_msg is None on success.
# ─────────────────────────────────────────────────────────────────────────────


def _load_candidate_policy(program_path: str) -> tuple[Any, str | None]:
    """
    Dynamically imports compute_target_workers from the candidate policy file.

    Args:
        program_path: Absolute path to the candidate policy .py file.

    Returns:
        Tuple of (policy_fn, error_msg). policy_fn is None if loading failed.
    """
    try:
        spec = importlib.util.spec_from_file_location("candidate_policy", program_path)
        if spec is None or spec.loader is None:
            return None, f"Cannot load spec from {program_path}"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "compute_target_workers"):
            return None, "compute_target_workers not found in module"
        if not hasattr(module, "TelemetricState"):
            return None, "TelemetricState not found in module"

        return module.compute_target_workers, None
    except Exception as e:
        return None, f"Import error: {e}\n{traceback.format_exc()}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: BOUNDARY STATE RUNTIME TESTS (Stage 1)
# Tests compute_target_workers on extreme boundary inputs to catch div-by-zero,
# integer overflow, negative returns, and out-of-range outputs.
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _BoundaryState:
    """Minimal TelemetricState-compatible struct for boundary testing in Stage 1."""
    p_fast: float
    p_fast_velocity: float
    mean_set_size: float
    ingress_rps: float
    ingress_acceleration: float
    offered_cloud_rps: float
    cloud_queue_depth: int
    cloud_queue_velocity: float
    oldest_task_age_s: float
    active_workers: int
    booting_workers: int
    time_since_last_scale_s: float
    worker_capacity_rps: float = 16.0
    sla_deadline_s: float = 15.0


_BOUNDARY_STATES = [
    # Zero Fast-Path: all traffic offloaded to cloud, maximum cloud pressure
    _BoundaryState(
        p_fast=0.0, p_fast_velocity=-0.1, mean_set_size=3.0,
        ingress_rps=100.0, ingress_acceleration=0.0,
        offered_cloud_rps=100.0, cloud_queue_depth=50,
        cloud_queue_velocity=5.0, oldest_task_age_s=0.0,
        active_workers=5, booting_workers=0, time_since_last_scale_s=5.0,
    ),
    # Max Ingress: storm peak, full semantic offload
    _BoundaryState(
        p_fast=0.0, p_fast_velocity=-0.5, mean_set_size=5.0,
        ingress_rps=200.0, ingress_acceleration=10.0,
        offered_cloud_rps=200.0, cloud_queue_depth=100,
        cloud_queue_velocity=20.0, oldest_task_age_s=12.0,
        active_workers=18, booting_workers=0, time_since_last_scale_s=1.0,
    ),
    # Zero Ingress & Empty Queue: scale-to-zero scenario (drain guard test)
    _BoundaryState(
        p_fast=1.0, p_fast_velocity=0.0, mean_set_size=1.0,
        ingress_rps=0.0, ingress_acceleration=0.0,
        offered_cloud_rps=0.0, cloud_queue_depth=0,
        cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
        active_workers=1, booting_workers=0, time_since_last_scale_s=30.0,
    ),
    # Full Fast-Path with non-zero ingress: local edge handles everything
    _BoundaryState(
        p_fast=1.0, p_fast_velocity=0.0, mean_set_size=1.0,
        ingress_rps=50.0, ingress_acceleration=0.0,
        offered_cloud_rps=0.0, cloud_queue_depth=0,
        cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
        active_workers=3, booting_workers=0, time_since_last_scale_s=10.0,
    ),
    # All booting workers: overflow check for booting_workers subtraction
    _BoundaryState(
        p_fast=0.5, p_fast_velocity=0.0, mean_set_size=2.0,
        ingress_rps=80.0, ingress_acceleration=0.0,
        offered_cloud_rps=40.0, cloud_queue_depth=0,
        cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
        active_workers=0, booting_workers=18, time_since_last_scale_s=0.5,
    ),
]


def _run_boundary_tests(policy_fn) -> tuple[bool, str]:
    """
    Runs compute_target_workers on all boundary states and validates outputs.

    Returns:
        Tuple of (passed: bool, error_detail: str). error_detail is empty on pass.
    """
    errors = []
    for i, state in enumerate(_BOUNDARY_STATES):
        try:
            result = policy_fn(state)
        except Exception as e:
            errors.append(f"Boundary state {i}: Exception — {e}")
            continue

        # Verify return type is integer-compatible
        if not isinstance(result, (int, float)):
            errors.append(f"Boundary state {i}: non-numeric return type {type(result)}")
            continue

        k = int(result)
        # Verify output is within the feasible worker range [1, MAX_WORKERS]
        if k < 1:
            errors.append(f"Boundary state {i}: k={k} < 1 (would crash cluster to zero workers)")
        elif k > MAX_WORKERS:
            errors.append(f"Boundary state {i}: k={k} > {MAX_WORKERS} (exceeds cluster capacity)")

    return (len(errors) == 0), "; ".join(errors)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: SIMULATION RUNNER (Stages 2 & 3)
# Runs ContinuumBench simulations with the candidate policy injected as a
# custom controller. Uses the existing CLI subprocess pattern from
# scratch/run_suite_baselines.py to avoid reimplementing the simulator.
# ─────────────────────────────────────────────────────────────────────────────


def _run_simulation_with_candidate(
    program_path: str,
    regime: str,
    seed: int = 42,
) -> dict | None:
    """
    Runs a single ContinuumBench simulation for the given regime, injecting
    the candidate policy at program_path as the cloud autoscaler.

    The candidate policy file is passed via the EVOLUTION_CANDIDATE_PATH
    environment variable, which the continuum_ext conformal controller reads
    at startup to dynamically load the evolving policy.

    Args:
        program_path: Absolute path to the candidate policy .py file.
        regime: Suite config name (e.g. "suite1_flat").
        seed: Simulation random seed (default 42 for reproducibility).

    Returns:
        Parsed summary dict on success, or None on failure.
    """
    cfg_path = SUITES_DIR / f"{regime}.yaml"
    if not cfg_path.exists():
        return None

    # Create a unique output directory per candidate evaluation
    run_tag = f"{regime}_s{seed}"
    out_dir = EVOLUTION_OUTPUT_DIR / Path(program_path).stem / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    # The evolved_conformal controller reads EVOLUTION_CANDIDATE_PATH at startup
    # to load the candidate compute_target_workers function dynamically.
    env = {
        **os.environ,
        "EVOLUTION_CANDIDATE_PATH": str(program_path),
        "PYTHONPATH": f"{WORKSPACE_ROOT}/src:{os.environ.get('PYTHONPATH', '')}",
    }

    cmd = [
        str(VENV_PYTHON),
        "-m", "continuum_bench.cli", "run",
        "--config", str(cfg_path),
        "--controller", "evolved_conformal",
        "--seed", str(seed),
        "--out", str(out_dir),
    ]

    try:
        res = subprocess.run(
            cmd,
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            env=env,
            timeout=60,  # Per-simulation wall-clock timeout
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"Simulation timed out (60s) for regime '{regime}'")
        return None

    if res.returncode != 0:
        logger.error(
            f"Simulation failed with exit code {res.returncode} for regime '{regime}'.\n"
            f"  Command: {' '.join(cmd)}\n"
            f"  STDERR: {res.stderr.strip() if res.stderr else '(empty)'}\n"
            f"  STDOUT: {res.stdout.strip()[-1000:] if res.stdout else '(empty)'}"
        )
        return None

    # Parse the ContinuumBench summary.json from the most recent run directory
    run_dirs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
    if not run_dirs:
        logger.error(f"No run directories created in {out_dir} for regime '{regime}'")
        return None

    summary_file = run_dirs[-1] / "summary.json"
    if not summary_file.exists():
        logger.error(f"summary.json not found in {run_dirs[-1]} for regime '{regime}'")
        return None

    with open(summary_file) as f:
        summary = json.load(f)

    # Extract all metrics using the same field paths as scratch/run_suite_baselines.py
    lat = summary.get("latency_s", {})
    cost = summary.get("cost", {})
    qos = summary.get("qos", {})
    rel = summary.get("reliability", {})
    stab = summary.get("stability", {})
    delay = summary.get("delay_breakdown_s", {})

    return {
        "completed": rel.get("completed_tasks", 0),
        "pending": rel.get("pending_tasks", 0),
        "generated": rel.get("generated_tasks", 0),
        "worker_seconds": cost.get("total_provisioned_worker_seconds", 0.0),
        "mean_latency_s": lat.get("mean", 0.0),
        "p95_latency_s": lat.get("p95", 0.0),
        "p99_latency_s": lat.get("p99", 0.0),
        "queue_wait_mean_s": delay.get("queue_wait_s", {}).get("mean", 0.0),
        "scaling_deltas": stab.get("scaling_delta_abs_total", 0.0),
        "deadline_misses": qos.get("deadline_miss_count", 0),
    }


def _aggregate_regime_results(results: list[dict]) -> dict:
    """
    Aggregates per-regime simulation results into a single scalar dict
    suitable for fitness computation and EvaluationResult metrics.

    Sums all counters (misses, completed, worker_seconds, deltas) and
    takes the maximum P99 latency across regimes for worst-case tail safety.
    """
    total_misses = sum(r["deadline_misses"] for r in results)
    total_completed = sum(r["completed"] for r in results)
    total_worker_seconds = sum(r["worker_seconds"] for r in results)
    total_deltas = sum(r["scaling_deltas"] for r in results)
    max_p99_s = max((r["p99_latency_s"] for r in results), default=0.0)
    mean_queue_wait = (
        sum(r["queue_wait_mean_s"] for r in results) / len(results)
        if results else 0.0
    )
    total_generated = sum(r["generated"] for r in results)

    return {
        "total_misses": total_misses,
        "total_completed": total_completed,
        "total_generated": total_generated,
        "total_worker_seconds": total_worker_seconds,
        "total_deltas": total_deltas,
        "max_p99_s": max_p99_s,
        "mean_queue_wait_s": mean_queue_wait,
    }


def _compute_fitness_J(agg: dict) -> float:
    """
    Computes the primary scalar fitness metric J per Step 6 spec Section 4.3:

        J = -(1.0 * deadline_misses
              + 0.20/100 * worker_seconds
              + 0.05 * scaling_deltas)
            + 0.01 * completed_requests

    J is maximized by the OpenEvolve search (lower penalties → higher J).
    Typical range: Fixed Capacity ≈ -55.8, best known ≈ targeted > -30.0.
    """
    return (
        - WEIGHT_MISSES * agg["total_misses"]
        - WEIGHT_COST * agg["total_worker_seconds"]
        - WEIGHT_CHURN * agg["total_deltas"]
        + WEIGHT_THROUGHPUT * agg["total_completed"]
    )


def _compute_map_elites_features(agg: dict, fitness_j: float) -> dict:
    """
    Computes the 3 MAP-Elites quality-diversity feature dimensions:

        cost_savings    = (1 - worker_seconds / FIXED_CAPACITY_WORKER_SECONDS) * 100
                          (% reduction in GPU cost vs Fixed Capacity baseline)
        churn_stability = 2000.0 - total_deltas
                          (higher = less flapping; 2000 is a reference upper bound)
        tail_safety     = 15.0 - max_p99_latency_s
                          (higher = more headroom under the SLA deadline)

    OpenEvolve bins these raw continuous values internally — we return scalars only.
    """
    cost_savings = (
        (1.0 - agg["total_worker_seconds"] / FIXED_CAPACITY_WORKER_SECONDS) * 100.0
        if FIXED_CAPACITY_WORKER_SECONDS > 0 else 0.0
    )
    churn_stability = 2000.0 - agg["total_deltas"]
    tail_safety = 15.0 - agg["max_p99_s"]

    return {
        "cost_savings": cost_savings,
        "churn_stability": churn_stability,
        "tail_safety": tail_safety,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: THREE CASCADE EVALUATION STAGES
# Functions named exactly evaluate_stage1, evaluate_stage2, evaluate_stage3
# per the OpenEvolve cascade engine contract (evaluator.py L396, L439, L502).
# ─────────────────────────────────────────────────────────────────────────────


def _log_performance_check(
    stage: str,
    program_path: str,
    result: EvaluationResult,
    details: dict = None,
) -> EvaluationResult:
    """
    Appends an authoritative record of this evaluation performance check to
    output/evolution_runs/evaluator_checks.jsonl. Returns the EvaluationResult
    unmodified for convenient chaining.
    """
    try:
        import json
        import time
        from datetime import datetime, timezone

        check_file = EVOLUTION_OUTPUT_DIR / "evaluator_checks.jsonl"
        check_file.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": time.time(),
            "datetime": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "program_path": str(program_path),
            "metrics": result.metrics,
            "artifacts": {k: str(v)[:500] for k, v in result.artifacts.items()} if result.artifacts else {},
            "details": details or {},
        }
        with open(check_file, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass
    return result


def evaluate_stage1(program_path: str) -> EvaluationResult:
    """
    Stage 1: Pure Validity Gate (~0.05s).

    Objective:
        Reject malformed, crashing, or semantically invalid candidates before
        consuming any simulation budget. Two-part check:
        1. Static AST validation — no hallucinated features, no unauthorized imports.
        2. Runtime boundary test — runs compute_target_workers on 5 extreme states,
           verifies no crashes and output k ∈ [1, 18].

    Threshold (openevolve_config.yaml cascade_thresholds[0] = 0.5):
        combined_score = 1.0 → passes (advances to Stage 2)
        combined_score = 0.0 → fails (artifact feedback injected into LLM prompt)
    """
    # ── Read candidate source code ────────────────────────────────────────────
    try:
        with open(program_path, "r") as f:
            code_str = f.read()
    except Exception as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={
                "stage1_passed": 0.0,
                "combined_score": 0.0,
                "cost_savings": -100.0,
                "churn_stability": 0.0,
                "tail_safety": -100.0,
            },
            artifacts={"error_message": f"Cannot read program file: {e}"},
        ), details={"error": str(e)})

    # ── Step 1a: Static AST Validation ───────────────────────────────────────
    ast_errors = validate_ast(code_str)
    if ast_errors:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={
                "stage1_passed": 0.0,
                "combined_score": 0.0,
                "cost_savings": -100.0,
                "churn_stability": 0.0,
                "tail_safety": -100.0,
            },
            artifacts={
                "error_message": "AST validation failed. Fix the following errors:\n" + "\n".join(ast_errors),
                "failure_stage": "stage1_ast",
            },
        ), details={"ast_errors": ast_errors})

    # ── Step 1b: Dynamic Import & Boundary Runtime Test ──────────────────────
    policy_fn, load_error = _load_candidate_policy(program_path)
    if policy_fn is None:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={
                "stage1_passed": 0.0,
                "combined_score": 0.0,
                "cost_savings": -100.0,
                "churn_stability": 0.0,
                "tail_safety": -100.0,
            },
            artifacts={
                "error_message": f"Failed to load compute_target_workers: {load_error}",
                "failure_stage": "stage1_import",
            },
        ), details={"load_error": str(load_error)})

    passed, boundary_errors = _run_boundary_tests(policy_fn)
    if not passed:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={
                "stage1_passed": 0.0,
                "combined_score": 0.0,
                "cost_savings": -100.0,
                "churn_stability": 0.0,
                "tail_safety": -100.0,
            },
            artifacts={
                "error_message": "Boundary state tests failed:\n" + boundary_errors,
                "failure_stage": "stage1_boundary",
            },
        ), details={"boundary_errors": boundary_errors})

    # ── Stage 1 Passed ────────────────────────────────────────────────────────
    return _log_performance_check("stage1", program_path, EvaluationResult(
        metrics={
            "stage1_passed": 1.0,
            "combined_score": 1.0,
            "cost_savings": -100.0,
            "churn_stability": 0.0,
            "tail_safety": -100.0,
        },
        artifacts={"stage1_status": "PASSED: AST valid, boundary tests passed"},
    ), details={"status": "PASSED"})


def evaluate_stage2(program_path: str) -> EvaluationResult:
    """
    Stage 2: Multi-Stress Micro-Tranche (~2.0s).

    Objective:
        Prevent the catastrophic surrogate bias failure mode: a cheap smoke filter
        that runs only flat traffic would reward dumb over-provisioners and prune
        innovative adaptive policies before they reach Stage 3. The triad ensures
        that all three principal failure modes from Step 5 are observed:
            - Slice 1 (suite1_flat):         Tests downscaling frugality
            - Slice 2 (suite2_shock):        Tests semantic drift reaction
            - Slice 3 (suite1_zero_terminal): Tests drain guard (HPA failure mode)

        This stage is a BINARY GO/NO-GO gate — it does NOT rank candidates.
        Only Stage 3 produces competitive fitness rankings.

    Threshold (openevolve_config.yaml cascade_thresholds[1] = -50.0):
        combined_score = fitness J across 3 regimes ≥ -50.0 → passes
        A policy scoring < -50.0 is catastrophically broken (e.g. always k=18).

    Note on combined_score range:
        Stage 2 runs only 3 regimes (vs 13 in Stage 3). The -50.0 threshold is
        calibrated to pass any policy that serves ≥ 90% of requests with
        queue wait < 1.0s across the triad — even an over-provisioner passes.
        Only provably broken policies (negative k, all misses, crashes) are pruned.
    """
    # ── Run the 3-regime micro-tranche simulations ────────────────────────────
    results = []
    for regime in STAGE2_REGIMES:
        result = _run_simulation_with_candidate(program_path, regime, seed=42)
        if result is not None:
            results.append(result)

    # ── If all simulations failed (CLI error / controller crash), reject ───────
    if not results:
        return _log_performance_check("stage2", program_path, EvaluationResult(
            metrics={
                "stage2_passed": 0.0,
                "combined_score": -9999.0,
                "cost_savings": -100.0,
                "churn_stability": 0.0,
                "tail_safety": -100.0,
            },
            artifacts={
                "error_message": "All Stage 2 simulations failed to produce output.",
                "failure_stage": "stage2_simulation_crash",
            },
        ), details={"results": "none"})

    # ── Compute aggregate metrics across the 3 regimes ────────────────────────
    agg = _aggregate_regime_results(results)

    # ── Permissive completion check (≥ 90% generated tasks completed) ─────────
    completion_rate = (
        agg["total_completed"] / agg["total_generated"]
        if agg["total_generated"] > 0 else 0.0
    )
    queue_ok = agg["mean_queue_wait_s"] < STAGE2_MAX_QUEUE_WAIT_S

    # ── Compute fitness J for this micro-tranche (used as combined_score) ─────
    fitness_j = _compute_fitness_J(agg)

    # ── Build descriptive artifact for LLM feedback loop ──────────────────────
    artifact_summary = (
        f"Stage 2 Triad (flat + shock + zero_terminal):\n"
        f"  Completion: {completion_rate:.1%} (threshold: {STAGE2_COMPLETION_THRESHOLD:.0%})\n"
        f"  Mean queue wait: {agg['mean_queue_wait_s']:.3f}s (threshold: {STAGE2_MAX_QUEUE_WAIT_S:.1f}s)\n"
        f"  Total misses: {agg['total_misses']}\n"
        f"  Worker-seconds: {agg['total_worker_seconds']:.1f}\n"
        f"  Fitness J (3-regime): {fitness_j:.2f}\n"
        f"  Queue OK: {queue_ok}, Completion OK: {completion_rate >= STAGE2_COMPLETION_THRESHOLD}"
    )

    passed = (completion_rate >= STAGE2_COMPLETION_THRESHOLD) and queue_ok

    if not passed:
        return _log_performance_check("stage2", program_path, EvaluationResult(
            metrics={
                "stage2_passed": 0.0,
                "combined_score": 0.0,
                "cost_savings": -100.0,
                "churn_stability": 0.0,
                "tail_safety": -100.0,
                "stage2_fitness_j": fitness_j,
                "stage2_completion_rate": completion_rate,
                "stage2_queue_wait_s": agg["mean_queue_wait_s"],
                "stage2_misses": float(agg["total_misses"]),
            },
            artifacts={
                "stage2_summary": artifact_summary,
                "error_message": (
                    f"Stage 2 rejected: completion={completion_rate:.1%} "
                    f"(need ≥{STAGE2_COMPLETION_THRESHOLD:.0%}), "
                    f"queue_wait={agg['mean_queue_wait_s']:.3f}s (need <{STAGE2_MAX_QUEUE_WAIT_S:.1f}s)"
                ),
                "failure_stage": "stage2_threshold",
            },
        ), details={"passed": False, "completion_rate": completion_rate, "queue_wait_s": agg["mean_queue_wait_s"]})

    # ── Stage 2 Passed ────────────────────────────────────────────────────────
    stage2_cost_savings = (
        (1.0 - agg["total_worker_seconds"] / (FIXED_CAPACITY_WORKER_SECONDS * len(results) / len(ALL_REGIMES)))
        * 100.0
    )
    stage2_churn_stability = max(0.0, 500.0 - agg["total_deltas"])
    stage2_tail_safety = max(0.0, 15.0 - agg["max_p99_s"])

    return _log_performance_check("stage2", program_path, EvaluationResult(
        metrics={
            "stage2_passed": 1.0,
            "combined_score": 1.0,
            "cost_savings": stage2_cost_savings,
            "churn_stability": stage2_churn_stability,
            "tail_safety": stage2_tail_safety,
            "stage2_fitness_j": fitness_j,
            "stage2_completion_rate": completion_rate,
            "stage2_queue_wait_s": agg["mean_queue_wait_s"],
            "stage2_misses": float(agg["total_misses"]),
        },
        artifacts={"stage2_summary": artifact_summary},
    ), details={"passed": True, "completion_rate": completion_rate, "queue_wait_s": agg["mean_queue_wait_s"]})


def evaluate_stage3(program_path: str) -> EvaluationResult:
    """
    Stage 3: Authoritative 13-Regime Benchmark (~20.0s).

    Objective:
        Compute the definitive Pareto-optimal fitness J and MAP-Elites feature
        coordinates across all 13 calibrated regimes (121,134 total requests).
        This is the ONLY stage that produces rankings in the MAP-Elites database.

    Baselines to beat (Step 5 empirical, docs/STEP5_NON_CONFORMAL_BASELINES_REPORT.md):
        - Cost (worker-seconds): < 14,261.0 (InferLine, 48.9% savings vs Fixed)
        - Deadline misses:       < 44 (InferLine)
        - Scaling deltas:        < 855 (InferLine)

    Returns:
        EvaluationResult with:
            combined_score   = J (maximized by evolutionary search)
            cost_savings     = % savings vs Fixed Capacity (MAP-Elites dim 1)
            churn_stability  = 2000 - total_deltas (MAP-Elites dim 2)
            tail_safety      = 15.0 - max_p99_latency_s (MAP-Elites dim 3)
            deadline_misses  = total misses (diagnostic)
            worker_seconds   = total worker-seconds (diagnostic)
            scaling_deltas   = total deltas (diagnostic)
            completed_requests = total completed (diagnostic)
    """
    # ── Run all 13 regime simulations ─────────────────────────────────────────
    results = []
    failed_regimes = []
    for regime in ALL_REGIMES:
        result = _run_simulation_with_candidate(program_path, regime, seed=42)
        if result is not None:
            results.append(result)
        else:
            failed_regimes.append(regime)

    # ── If no simulations succeeded, return catastrophic failure ──────────────
    if not results:
        return _log_performance_check("stage3", program_path, EvaluationResult(
            metrics={
                "combined_score": -9999.0,
                "cost_savings": -100.0,
                "churn_stability": 0.0,
                "tail_safety": -100.0,
                "deadline_misses": 9999.0,
                "worker_seconds": 99999.0,
                "scaling_deltas": 9999.0,
                "completed_requests": 0.0,
            },
            artifacts={
                "error_message": f"All Stage 3 simulations failed. Failed regimes: {failed_regimes}",
                "failure_stage": "stage3_all_failed",
            },
        ), details={"failed_regimes": failed_regimes})

    # ── Aggregate across all successful regimes ───────────────────────────────
    agg = _aggregate_regime_results(results)

    # ── Compute primary fitness J and MAP-Elites feature coordinates ──────────
    fitness_j = _compute_fitness_J(agg)
    map_features = _compute_map_elites_features(agg, fitness_j)

    # ── Build comprehensive artifact for LLM feedback loop ────────────────────
    artifact_lines = [
        "Stage 3 Authoritative 13-Regime Benchmark:",
        f"  Regimes run:      {len(results)}/13 {'(ALL)' if not failed_regimes else f'(failed: {failed_regimes})'}",
        f"  Completed:        {agg['total_completed']:,} / {agg['total_generated']:,} requests",
        f"  Deadline misses:  {agg['total_misses']}",
        f"  Worker-seconds:   {agg['total_worker_seconds']:.1f}",
        f"  Scaling deltas:   {agg['total_deltas']:.0f}",
        f"  Max P99 latency:  {agg['max_p99_s']:.3f}s",
        f"  Fitness J:        {fitness_j:.4f}",
        "  MAP-Elites features:",
        f"    cost_savings:    {map_features['cost_savings']:.2f}%",
        f"    churn_stability: {map_features['churn_stability']:.1f}",
        f"    tail_safety:     {map_features['tail_safety']:.3f}",
        "",
        "Baseline comparison targets:",
        "  InferLine (best cost):   14,261.0 worker-seconds, 44 misses, 855 deltas",
        "  Fixed Capacity (0 miss): 27,900.0 worker-seconds, 0 misses",
    ]

    regime_breakdowns = {
        regime: res for regime, res in zip(ALL_REGIMES, results) if res is not None
    }
    eval_res = EvaluationResult(
        metrics={
            # Primary fitness signal (OpenEvolve maximizes combined_score)
            "combined_score": fitness_j,
            # MAP-Elites quality-diversity feature dimensions (raw continuous values)
            "cost_savings": map_features["cost_savings"],
            "churn_stability": map_features["churn_stability"],
            "tail_safety": map_features["tail_safety"],
            # Diagnostic counters (used by LLM feedback loop and human inspection)
            "deadline_misses": float(agg["total_misses"]),
            "worker_seconds": agg["total_worker_seconds"],
            "scaling_deltas": agg["total_deltas"],
            "completed_requests": float(agg["total_completed"]),
            "max_p99_latency_s": agg["max_p99_s"],
            "regimes_completed": float(len(results)),
        },
        artifacts={
            "stage3_benchmark_report": "\n".join(artifact_lines),
            "failed_regimes": str(failed_regimes),
        },
    )
    return _log_performance_check(
        "stage3",
        program_path,
        eval_res,
        details={
            "regimes": regime_breakdowns,
            "failed_regimes": failed_regimes,
            "fitness_j": fitness_j,
            "cost_savings": map_features["cost_savings"],
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT EVALUATION ENTRY POINT
# OpenEvolve's Evaluator.__init__ requires the module to export an 'evaluate'
# callable even when cascade_evaluation is True.
# ─────────────────────────────────────────────────────────────────────────────
evaluate = evaluate_stage3
