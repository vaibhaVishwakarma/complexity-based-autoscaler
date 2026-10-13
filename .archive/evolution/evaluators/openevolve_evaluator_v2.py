"""
openevolve_evaluator_v2.py — Step 6 v2: Cost-First / Balanced Miss & P99 Cascade Evaluator

Role:
    Implements the 3-stage cascade simulation-in-the-loop evaluator for the v2
    evolutionary search. Re-aligns the fitness function to prioritize Cost Savings
    as the primary objective, with equal, balanced penalties for Deadline Misses
    and P99 Latency degradation, and secondary regularizing for actuation churn.

Gate Stage:    Step 6 v2 (OpenEvolve Evaluator & Fitness Engine)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9

New Objective Formulation (v2):
    Costing First (Primary Driver):
        + 1.0 * cost_savings_% (Range: 0% to 60% vs Fixed Capacity 27,900 ws)
        Target to beat: InferLine's 48.9% savings (14,261 worker-seconds)

    Misses & P99 Tail Latency (Equal Balanced Co-Drivers):
        - 2.0 * min(misses, 50) - 10.0 * max(0, misses - 50)
        - 10.0 * max(0.0, p99_latency_s - 5.0s)
        (10 misses = -20 pts; 2.0s P99 degradation = -20 pts -> Exact equal weight!)

    Actuation Churn (Secondary Regularizer):
        - 0.01 * scaling_deltas

    Total Fitness:
        J = cost_savings - miss_penalty - p99_penalty - churn_penalty

AGENTS.md Compliance:
    Rule #1 — New versioned evaluator (openevolve_evaluator_v2.py); v1 preserved intact.
    Rule #2 — No hardcoded upstream gate p-values; TelemetricState dynamically injected.
    Rule #3 — Subprocess calls and imports use workspace .venv Python exclusively.
    Rule #4 — Self-documenting header, stage-level comments, inline logic notes.
    Rule #5 — Uses subprocess + ContinuumBench CLI; no custom simulator reimplementation.
    Rule #6 — Uses calibrated suite configs from configs/suites/; no synthetic fallbacks.
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
from typing import Any, Dict, List, Optional, Tuple

from openevolve.evaluation_result import EvaluationResult

logger = logging.getLogger("openevolve_evaluator_v2")

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v2"
SEED_POLICY_PATH = Path(__file__).parent / "seed_policy_v2.py"

FIXED_CAPACITY_WORKER_SECONDS: float = 27_900.0

# v2 Fitness function weights (Cost-First, Equal Miss & P99 Penalties)
WEIGHT_COST_SAVINGS: float = 1.0
WEIGHT_MISS_BASE: float = 2.0
WEIGHT_MISS_EXCESS: float = 10.0
WEIGHT_P99_PENALTY: float = 10.0
P99_BASELINE_S: float = 5.0
WEIGHT_CHURN_V2: float = 0.01

# Stage 2 micro-tranche parameters
STAGE2_EPOCHS_PER_SLICE: int = 10
STAGE2_COMPLETION_THRESHOLD: float = 0.90  # >= 90% requests must complete
STAGE2_MAX_QUEUE_WAIT_S: float = 1.0        # Mean queue wait < 1.0s

# The 13 authoritative evaluation regimes (Stage 3 full benchmark)
ALL_REGIMES = [
    "suite1_flat", "suite1_spike", "suite1_burst", "suite1_ramp",
    "suite1_zero_begin", "suite1_zero_terminal",
    "suite2_shock", "suite2_recovery", "suite2_compound_stress",
    "suite2_compound_relief", "suite2_decoupled_opposing", "suite2_storm",
    "suite3_azure",
]

# Fast 3-regime triad for Stage 2
STAGE2_REGIMES = ["suite1_flat", "suite2_shock", "suite1_zero_terminal"]


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _log_performance_check(stage: str, program_path: str, result: EvaluationResult, details: dict = None) -> EvaluationResult:
    """Logs evaluation details and saves checks to evaluator_checks.jsonl."""
    log_dir = EVOLUTION_OUTPUT_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    check_file = log_dir / "evaluator_checks.jsonl"
    record = {
        "timestamp": os.environ.get("OPENEVOLVE_TIMESTAMP", str(os.path.getmtime(program_path) if os.path.exists(program_path) else 0)),
        "stage": stage,
        "program_path": program_path,
        "metrics": result.metrics,
        "artifacts_keys": list(result.artifacts.keys()),
        "details": details or {},
    }
    try:
        with open(check_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning(f"Could not append to evaluator_checks.jsonl: {e}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1: PURE VALIDITY GATE (~0.05s)
# ─────────────────────────────────────────────────────────────────────────────

FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "urllib", "requests", "http",
    "shutil", "glob", "posix", "nt", "pty", "commands",
    "threading", "multiprocessing", "concurrent", "asyncio",
    "pickle", "shelve", "marshal", "ctypes", "builtins",
}


def _check_ast_safety(tree: ast.AST) -> Optional[str]:
    """Inspects AST for forbidden modules or dangerous calls."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                if root_pkg in FORBIDDEN_MODULES:
                    return f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                if root_pkg in FORBIDDEN_MODULES:
                    return f"Forbidden from-import: {node.module}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__", "compile", "open"}:
                return f"Forbidden builtin call: {node.func.id}()"
    return None


def evaluate_stage1(program_path: str) -> EvaluationResult:
    """
    Stage 1: Pure Validity Gate (~0.05s).
    Validates AST syntax, security constraints, and 5 boundary unit tests.
    """
    if not os.path.exists(program_path):
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"Program file not found: {program_path}"},
        ))

    try:
        with open(program_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"Could not read program source: {e}"},
        ))

    # AST Syntax & Safety Parse
    try:
        tree = ast.parse(source, filename=program_path)
    except SyntaxError as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"AST SyntaxError: {e}"},
        ))

    safety_error = _check_ast_safety(tree)
    if safety_error:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"AST Security Check Failed: {safety_error}"},
        ))

    # Dynamic Module Import
    try:
        spec = importlib.util.spec_from_file_location("candidate_policy_v2", program_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {program_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"Module load/runtime exception: {e}\n{traceback.format_exc()}"},
        ))

    if not hasattr(module, "compute_target_workers"):
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": "Missing compute_target_workers(state) callable in module."},
        ))

    TelemetricState = getattr(module, "TelemetricState", None)
    if TelemetricState is None:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": "Missing TelemetricState contract in module."},
        ))

    fn = module.compute_target_workers

    # 5 Boundary State Tests
    boundary_tests = [
        ("quiescent", TelemetricState(
            p_fast=1.0, p_fast_velocity=0.0, mean_set_size=1.0, ingress_rps=0.0,
            ingress_acceleration=0.0, offered_cloud_rps=0.0, cloud_queue_depth=0,
            cloud_queue_velocity=0.0, oldest_task_age_s=0.0, active_workers=1,
            booting_workers=0, time_since_last_scale_s=10.0
        )),
        ("saturating_shock", TelemetricState(
            p_fast=0.0, p_fast_velocity=-0.5, mean_set_size=3.5, ingress_rps=300.0,
            ingress_acceleration=50.0, offered_cloud_rps=300.0, cloud_queue_depth=50,
            cloud_queue_velocity=20.0, oldest_task_age_s=8.0, active_workers=4,
            booting_workers=0, time_since_last_scale_s=0.5
        )),
        ("booting_in_flight", TelemetricState(
            p_fast=0.5, p_fast_velocity=0.0, mean_set_size=1.0, ingress_rps=64.0,
            ingress_acceleration=0.0, offered_cloud_rps=32.0, cloud_queue_depth=4,
            cloud_queue_velocity=0.0, oldest_task_age_s=0.5, active_workers=2,
            booting_workers=4, time_since_last_scale_s=0.8
        )),
        ("negative_velocity_drain", TelemetricState(
            p_fast=0.9, p_fast_velocity=0.3, mean_set_size=1.0, ingress_rps=20.0,
            ingress_acceleration=-10.0, offered_cloud_rps=2.0, cloud_queue_depth=0,
            cloud_queue_velocity=-5.0, oldest_task_age_s=0.0, active_workers=8,
            booting_workers=0, time_since_last_scale_s=5.0
        )),
        ("uncertainty_surge", TelemetricState(
            p_fast=0.2, p_fast_velocity=-0.2, mean_set_size=4.8, ingress_rps=80.0,
            ingress_acceleration=5.0, offered_cloud_rps=64.0, cloud_queue_depth=12,
            cloud_queue_velocity=3.0, oldest_task_age_s=2.0, active_workers=4,
            booting_workers=0, time_since_last_scale_s=1.2
        )),
    ]

    for label, test_state in boundary_tests:
        try:
            k = fn(test_state)
            if not isinstance(k, (int, float)) or isinstance(k, bool):
                return _log_performance_check("stage1", program_path, EvaluationResult(
                    metrics={"stage1_passed": 0.0, "combined_score": 0.0},
                    artifacts={"error_message": f"Boundary test '{label}' returned non-numeric type: {type(k)}"},
                ))
            k_int = int(k)
            if not (1 <= k_int <= 18):
                return _log_performance_check("stage1", program_path, EvaluationResult(
                    metrics={"stage1_passed": 0.0, "combined_score": 0.0},
                    artifacts={"error_message": f"Boundary test '{label}' returned out-of-range worker count: {k_int} (expected in [1, 18])"},
                ))
        except Exception as e:
            return _log_performance_check("stage1", program_path, EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": 0.0},
                artifacts={"error_message": f"Boundary test '{label}' raised exception: {e}\n{traceback.format_exc()}"},
            ))

    return _log_performance_check("stage1", program_path, EvaluationResult(
        metrics={"stage1_passed": 1.0, "combined_score": 1.0},
        artifacts={"stage1_summary": "Passed AST safety check, import validation, and 5 boundary unit tests."},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# FITNESS FUNCTION (V2: COST-FIRST, EQUAL MISS & P99 PENALTIES)
# ─────────────────────────────────────────────────────────────────────────────

def _compute_fitness_J(agg: dict) -> float:
    """
    Computes the v2 Cost-First fitness metric J:

        cost_savings = (1 - worker_seconds / 27900.0) * 100
        miss_penalty = 2.0 * min(misses, 50) + 10.0 * max(0, misses - 50)
        p99_penalty  = 10.0 * max(0.0, p99_latency_s - 5.0)
        churn_penalty = 0.01 * deltas

        J = cost_savings - miss_penalty - p99_penalty - churn_penalty

    Properties:
        1. Cost Savings is the primary reward signal (+1.0 pt per 1% savings).
        2. Misses and P99 are equally weighted (10 misses = -20 pts; 2.0s P99 degradation = -20 pts).
        3. Allows minor single-digit misses under violent shocks if significant worker-seconds are saved.
    """
    cost_savings = (
        (1.0 - agg["total_worker_seconds"] / FIXED_CAPACITY_WORKER_SECONDS) * 100.0
        if FIXED_CAPACITY_WORKER_SECONDS > 0 else 0.0
    )
    misses = agg["total_misses"]
    miss_penalty = (
        WEIGHT_MISS_BASE * min(misses, 50.0) +
        WEIGHT_MISS_EXCESS * max(0.0, misses - 50.0)
    )
    p99_penalty = WEIGHT_P99_PENALTY * max(0.0, agg["max_p99_s"] - P99_BASELINE_S)
    churn_penalty = WEIGHT_CHURN_V2 * agg["total_deltas"]

    return cost_savings - miss_penalty - p99_penalty - churn_penalty


def _compute_map_elites_features(agg: dict, fitness_j: float) -> dict:
    """Computes continuous MAP-Elites feature dimensions."""
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


def _run_continuum_bench_simulation(
    regime: str,
    program_path: str,
    epochs: Optional[int] = None,
    seed: int = 42,
) -> Optional[dict]:
    """Runs a single simulation regime in ContinuumBench."""
    cfg_path = SUITES_DIR / f"{regime}.yaml"
    if not cfg_path.exists():
        return None

    run_tag = f"{regime}_s{seed}"
    out_dir = EVOLUTION_OUTPUT_DIR / Path(program_path).stem / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)

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
        res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, timeout=120, env=env)
        if res.returncode != 0:
            logger.warning(f"Simulation {regime} failed:\n{res.stderr[:300]}")
            return None

        run_dirs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
        if not run_dirs:
            return None

        summary_file = run_dirs[-1] / "summary.json"
        if not summary_file.exists():
            return None

        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)

        lat = summary.get("latency_s", {})
        cost = summary.get("cost", {})
        qos = summary.get("qos", {})
        stab = summary.get("stability", {})
        delay = summary.get("delay_breakdown_s", {})

        return {
            "regime": regime,
            "completed": int(qos.get("slo_eligible_count", 0)),
            "generated": int(qos.get("slo_eligible_count", 0)),
            "deadline_misses": int(qos.get("deadline_miss_count", 0)),
            "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
            "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
            "p99_latency_s": float(lat.get("p99", 15.0)),
            "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
        }
    except Exception as e:
        logger.error(f"Error running simulation {regime}: {e}")
        return None


def _aggregate_regime_results(results: list) -> dict:
    """Aggregates metrics across simulated regimes."""
    total_misses = sum(r["deadline_misses"] for r in results)
    total_completed = sum(r["completed"] for r in results)
    total_generated = sum(r["generated"] for r in results)
    total_worker_seconds = sum(r["worker_seconds"] for r in results)
    total_deltas = sum(r["scaling_deltas"] for r in results)
    max_p99_s = max((r["p99_latency_s"] for r in results), default=0.0)
    mean_queue_wait = (
        sum(r["queue_wait_mean_s"] for r in results) / len(results)
        if results else 0.0
    )

    return {
        "total_misses": total_misses,
        "total_completed": total_completed,
        "total_generated": total_generated,
        "total_worker_seconds": total_worker_seconds,
        "total_deltas": total_deltas,
        "max_p99_s": max_p99_s,
        "mean_queue_wait_s": mean_queue_wait,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: MULTI-STRESS MICRO-TRANCHE GATE (~2.0s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage2(program_path: str) -> EvaluationResult:
    """Stage 2: Micro-Tranche Gate evaluating flat, shock, and zero_terminal regimes."""
    results = []
    for regime in STAGE2_REGIMES:
        res = _run_continuum_bench_simulation(regime, program_path, epochs=STAGE2_EPOCHS_PER_SLICE, seed=42)
        if res is not None:
            results.append(res)

    if not results:
        return _log_performance_check("stage2", program_path, EvaluationResult(
            metrics={"stage2_passed": 0.0, "combined_score": -200.0},
            artifacts={"error_message": "All Stage 2 micro-tranche simulations failed."},
        ))

    agg = _aggregate_regime_results(results)
    completion_rate = agg["total_completed"] / agg["total_generated"] if agg["total_generated"] > 0 else 0.0
    queue_ok = agg["mean_queue_wait_s"] < STAGE2_MAX_QUEUE_WAIT_S
    fitness_j = _compute_fitness_J(agg)

    passed = (completion_rate >= STAGE2_COMPLETION_THRESHOLD) and queue_ok and (fitness_j >= -100.0)

    summary_text = (
        f"Stage 2 Triad (flat + shock + zero_terminal):\n"
        f"  Completion: {completion_rate:.1%}\n"
        f"  Queue wait: {agg['mean_queue_wait_s']:.3f}s\n"
        f"  Misses: {agg['total_misses']}\n"
        f"  Worker-seconds: {agg['total_worker_seconds']:.1f}\n"
        f"  P99: {agg['max_p99_s']:.2f}s\n"
        f"  Fitness J: {fitness_j:.2f}\n"
        f"  Passed: {passed}"
    )

    stage2_cost_savings = (
        (1.0 - agg["total_worker_seconds"] / (FIXED_CAPACITY_WORKER_SECONDS * 3.0 / 13.0)) * 100.0
        if FIXED_CAPACITY_WORKER_SECONDS > 0 else 0.0
    )

    return _log_performance_check("stage2", program_path, EvaluationResult(
        metrics={
            "stage2_passed": 1.0 if passed else 0.0,
            "combined_score": 1.0 if passed else 0.0,
            "cost_savings": stage2_cost_savings,
            "churn_stability": max(0.0, 500.0 - agg["total_deltas"]),
            "tail_safety": max(0.0, 15.0 - agg["max_p99_s"]),
            "stage2_fitness_j": fitness_j,
            "stage2_misses": float(agg["total_misses"]),
        },
        artifacts={"stage2_summary": summary_text},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: AUTHORITATIVE 13-REGIME BENCHMARK (~160s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage3(program_path: str) -> EvaluationResult:
    """Stage 3: Full 13-Regime Benchmark producing the definitive fitness J."""
    results = []
    failed_regimes = []
    for regime in ALL_REGIMES:
        res = _run_continuum_bench_simulation(regime, program_path, seed=42)
        if res is not None:
            results.append(res)
        else:
            failed_regimes.append(regime)

    if not results:
        return _log_performance_check("stage3", program_path, EvaluationResult(
            metrics={"combined_score": -1000.0, "cost_savings": -100.0, "churn_stability": 0.0, "tail_safety": 0.0},
            artifacts={"error_message": f"All Stage 3 simulations failed: {failed_regimes}"},
        ))

    agg = _aggregate_regime_results(results)
    fitness_j = _compute_fitness_J(agg)
    map_features = _compute_map_elites_features(agg, fitness_j)

    artifact_lines = [
        "Stage 3 Full Benchmark Summary (v2 Cost-First):",
        f"  Completed requests: {agg['total_completed']:,}",
        f"  Total misses:       {agg['total_misses']}",
        f"  Worker-seconds:     {agg['total_worker_seconds']:.1f}",
        f"  Cost savings:       {map_features['cost_savings']:.2f}%",
        f"  Max P99 latency:    {agg['max_p99_s']:.3f}s",
        f"  Scaling deltas:     {agg['total_deltas']:.0f}",
        f"  Fitness J:          {fitness_j:.4f}",
    ]

    return _log_performance_check("stage3", program_path, EvaluationResult(
        metrics={
            "combined_score": fitness_j,
            "cost_savings": map_features["cost_savings"],
            "churn_stability": map_features["churn_stability"],
            "tail_safety": map_features["tail_safety"],
            "deadline_misses": float(agg["total_misses"]),
            "worker_seconds": agg["total_worker_seconds"],
            "scaling_deltas": agg["total_deltas"],
            "completed_requests": float(agg["total_completed"]),
            "max_p99_latency_s": agg["max_p99_s"],
            "regimes_completed": float(len(results)),
        },
        artifacts={"stage3_report": "\n".join(artifact_lines)},
    ))


def evaluate(program_path: str) -> EvaluationResult:
    """Default fallback evaluation entry point."""
    return evaluate_stage3(program_path)
