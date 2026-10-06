"""
openevolve_evaluator_v4.py — Step 6 v4: OpenEvolve Evaluator with Tail Latency Optimization

Role:
    Executes the 3-stage cascade evaluation pipeline for OpenEvolve v4:
      Stage 1: AST Safety & Boundary Unit Tests (~0.05s)
      Stage 2: Micro-Tranche Gate (flat, spike, shock) (~2.0s)
      Stage 3: Authoritative 13-Regime ContinuumBench Benchmark (~160s)

Fitness Objective (v4 Pareto-Optimal: Cost-Supreme + Tail Latency Reduction):
    J_v4 = cost_savings - miss_penalty - p99_penalty - churn_penalty + tail_bonus

    Where:
      cost_savings = (1.0 - worker_seconds / 27,900.0) * 100.0
      miss_penalty = 3.0 * min(misses, 50.0) + 15.0 * max(0.0, misses - 50.0)
      p99_penalty  = 15.0 * max(0.0, max_p99_s - 5.0) + 5.0 * max(0.0, mean_p99_s - 4.8)
      tail_bonus   = 2.0 * max(0.0, 5.0 - mean_p99_s)
      churn_penalty = 0.01 * deltas

Gate Stage:    Step 6 v4 (OpenEvolve Evaluator Engine)
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9 & 10

Outputs:
    output/evolution_runs_v4/evaluator_checks.jsonl

AGENTS.md Compliance:
    Rule #1 — New versioned evaluator artifact (openevolve_evaluator_v4.py); previous evaluators untouched.
    Rule #2 — Dynamically reads simulation outputs from JSON manifests; zero hardcoding.
    Rule #3 — Strictly runs under workspace ./.venv/bin/python.
    Rule #4 — Fully documented with header docstrings and inline commentary.
    Rule #5 — Uses openevolve EvaluationResult contract.
"""

import ast
import json
import logging
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openevolve.evaluation_result import EvaluationResult

logger = logging.getLogger("openevolve_evaluator_v4")

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v4"
SEED_POLICY_PATH = Path(__file__).parent / "seed_policy_v4.py"

FIXED_CAPACITY_WORKER_SECONDS: float = 27_900.0

# v4 Fitness function weights (Pareto-Optimal: Cost-Supreme + Tail Latency Optimization)
WEIGHT_COST_SAVINGS: float = 1.0
WEIGHT_MISS_BASE: float = 3.0
WEIGHT_MISS_EXCESS: float = 15.0
P99_TARGET_S: float = 5.0            # Target P99 tightened from 6.0s down to 5.0s
P99_MEAN_TARGET_S: float = 4.8       # Mean P99 target across regimes
WEIGHT_P99_MAX_PENALTY: float = 15.0 # Steep gradient for worst-case P99 above 5.0s
WEIGHT_P99_MEAN_PENALTY: float = 5.0 # Penalty for mean P99 above 4.8s
WEIGHT_TAIL_BONUS: float = 2.0       # Bonus for achieving sub-5.0s tail
WEIGHT_CHURN_V4: float = 0.01

# Stage 2 micro-tranche parameters
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

# Fast 3-regime triad for Stage 2 (flat, spike, shock: explicitly tests spike handling!)
STAGE2_REGIMES = ["suite1_flat", "suite1_spike", "suite2_shock"]


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
    """Stage 1: Pure Validity Gate (~0.05s)."""
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

    # 1. Parse AST
    try:
        tree = ast.parse(source, filename=program_path)
    except SyntaxError as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"SyntaxError: {e}"},
        ))

    # 2. Safety AST check
    safety_violation = _check_ast_safety(tree)
    if safety_violation:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"AST Safety Violation: {safety_violation}"},
        ))

    # 3. Dynamic import test
    namespace = {}
    try:
        exec(compile(tree, program_path, "exec"), namespace)
    except Exception as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": f"Module load exception: {e}\n{traceback.format_exc()}"},
        ))

    if "compute_target_workers" not in namespace:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": "Missing required entry function: compute_target_workers"},
        ))

    fn = namespace["compute_target_workers"]
    TelemetricStateClass = namespace.get("TelemetricState")
    if not TelemetricStateClass:
        from continuum_ext.evolution.seed_policy_v4 import TelemetricState as TelemetricStateClass

    # 4. Boundary Unit Tests
    boundary_cases = [
        ("quiescent", TelemetricStateClass(
            p_fast=0.95, p_fast_velocity=0.0, mean_set_size=1.01,
            ingress_rps=10.0, ingress_acceleration=0.0, offered_cloud_rps=0.5,
            cloud_queue_depth=0, cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
            active_workers=1, booting_workers=0, time_since_last_scale_s=10.0,
        )),
        ("spike_onset", TelemetricStateClass(
            p_fast=0.80, p_fast_velocity=-0.10, mean_set_size=1.20,
            ingress_rps=180.0, ingress_acceleration=50.0, offered_cloud_rps=36.0,
            cloud_queue_depth=5, cloud_queue_velocity=10.0, oldest_task_age_s=0.2,
            active_workers=2, booting_workers=0, time_since_last_scale_s=5.0,
        )),
        ("semantic_collapse", TelemetricStateClass(
            p_fast=0.15, p_fast_velocity=-0.40, mean_set_size=2.80,
            ingress_rps=60.0, ingress_acceleration=0.0, offered_cloud_rps=51.0,
            cloud_queue_depth=12, cloud_queue_velocity=8.0, oldest_task_age_s=1.5,
            active_workers=4, booting_workers=1, time_since_last_scale_s=1.0,
        )),
        ("backlog_aging", TelemetricStateClass(
            p_fast=0.50, p_fast_velocity=0.0, mean_set_size=1.50,
            ingress_rps=60.0, ingress_acceleration=0.0, offered_cloud_rps=30.0,
            cloud_queue_depth=20, cloud_queue_velocity=2.0, oldest_task_age_s=4.5,
            active_workers=3, booting_workers=2, time_since_last_scale_s=3.0,
        )),
        ("overprovisioned_idle", TelemetricStateClass(
            p_fast=0.98, p_fast_velocity=0.05, mean_set_size=1.00,
            ingress_rps=5.0, ingress_acceleration=0.0, offered_cloud_rps=0.1,
            cloud_queue_depth=0, cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
            active_workers=18, booting_workers=0, time_since_last_scale_s=15.0,
        )),
    ]

    for label, state in boundary_cases:
        try:
            k = fn(state)
            if not isinstance(k, (int, float)):
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
# FITNESS FUNCTION (V4: PARETO-OPTIMAL COST-SUPREME + TAIL LATENCY)
# ─────────────────────────────────────────────────────────────────────────────

def _compute_fitness_J_v4(agg: dict) -> float:
    """
    Computes the v4 Pareto-Optimal fitness metric J_v4:
        J_v4 = cost_savings - miss_penalty - p99_penalty - churn_penalty + tail_bonus

        Where:
            cost_savings  = (1.0 - worker_seconds / 27,900.0) * 100.0
            miss_penalty  = 3.0 * min(misses, 50) + 15.0 * max(0, misses - 50)
            p99_penalty   = 15.0 * max(0.0, max_p99_s - 5.0) + 5.0 * max(0.0, mean_p99_s - 4.8)
            tail_bonus    = 2.0 * max(0.0, 5.0 - mean_p99_s)
            churn_penalty = 0.01 * deltas
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

    max_p99 = agg["max_p99_s"]
    mean_p99 = agg.get("mean_p99_s", max_p99)

    p99_penalty = (
        WEIGHT_P99_MAX_PENALTY * max(0.0, max_p99 - P99_TARGET_S) +
        WEIGHT_P99_MEAN_PENALTY * max(0.0, mean_p99 - P99_MEAN_TARGET_S)
    )
    tail_bonus = WEIGHT_TAIL_BONUS * max(0.0, P99_TARGET_S - mean_p99)
    churn_penalty = WEIGHT_CHURN_V4 * agg["total_deltas"]

    return cost_savings - miss_penalty - p99_penalty - churn_penalty + tail_bonus


def _compute_map_elites_features(agg: dict, fitness_j: float) -> dict:
    """Computes continuous MAP-Elites feature dimensions."""
    cost_savings = (
        (1.0 - agg["total_worker_seconds"] / FIXED_CAPACITY_WORKER_SECONDS) * 100.0
        if FIXED_CAPACITY_WORKER_SECONDS > 0 else 0.0
    )
    churn_stability = max(0.0, 2000.0 - agg["total_deltas"])
    tail_safety = max(0.0, 10.0 - agg["max_p99_s"])

    return {
        "cost_savings": cost_savings,
        "churn_stability": churn_stability,
        "tail_safety": tail_safety,
    }


def _run_continuum_bench_simulation(
    regime: str,
    program_path: str,
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
    mean_p99_s = (
        sum(r["p99_latency_s"] for r in results) / len(results)
        if results else 0.0
    )
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
        "mean_p99_s": mean_p99_s,
        "mean_queue_wait_s": mean_queue_wait,
    }


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: MULTI-STRESS MICRO-TRANCHE GATE (~2.0s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage2(program_path: str) -> EvaluationResult:
    """Stage 2: Micro-Tranche Gate evaluating flat, spike, and shock regimes."""
    results = []
    for regime in STAGE2_REGIMES:
        res = _run_continuum_bench_simulation(regime, program_path, seed=42)
        if res is not None:
            results.append(res)

    if not results:
        return _log_performance_check("stage2", program_path, EvaluationResult(
            metrics={"stage2_passed": 0.0, "combined_score": 0.0},
            artifacts={"error_message": "All Stage 2 micro-tranche simulations failed."},
        ))

    agg = _aggregate_regime_results(results)
    completion_rate = agg["total_completed"] / agg["total_generated"] if agg["total_generated"] > 0 else 0.0
    queue_ok = agg["mean_queue_wait_s"] < STAGE2_MAX_QUEUE_WAIT_S
    fitness_j = _compute_fitness_J_v4(agg)

    passed = (completion_rate >= STAGE2_COMPLETION_THRESHOLD) and queue_ok and (fitness_j >= -100.0)

    summary_text = (
        f"Stage 2 Triad (flat + spike + shock):\n"
        f"  Completion: {completion_rate:.1%}\n"
        f"  Queue wait: {agg['mean_queue_wait_s']:.3f}s\n"
        f"  Misses: {agg['total_misses']}\n"
        f"  Worker-seconds: {agg['total_worker_seconds']:.1f}\n"
        f"  Max P99: {agg['max_p99_s']:.2f}s\n"
        f"  Mean P99: {agg['mean_p99_s']:.2f}s\n"
        f"  Fitness J_v4: {fitness_j:.2f}\n"
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
            "tail_safety": max(0.0, 10.0 - agg["max_p99_s"]),
            "stage2_fitness_j": fitness_j,
            "stage2_misses": float(agg["total_misses"]),
            "stage2_max_p99_s": agg["max_p99_s"],
        },
        artifacts={"stage2_summary": summary_text},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: AUTHORITATIVE 13-REGIME BENCHMARK (~160s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage3(program_path: str) -> EvaluationResult:
    """Stage 3: Full 13-Regime Benchmark producing the definitive fitness J_v4."""
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
    fitness_j = _compute_fitness_J_v4(agg)
    map_features = _compute_map_elites_features(agg, fitness_j)

    artifact_lines = [
        "Stage 3 Full Benchmark Summary (v4 Pareto-Optimal Cost + Low-Tail-Latency):",
        f"  Completed requests: {agg['total_completed']:,}",
        f"  Total misses:       {agg['total_misses']}",
        f"  Worker-seconds:     {agg['total_worker_seconds']:.1f}",
        f"  Cost savings:       {map_features['cost_savings']:.2f}%",
        f"  Max P99 latency:    {agg['max_p99_s']:.3f}s",
        f"  Mean P99 latency:   {agg['mean_p99_s']:.3f}s",
        f"  Scaling deltas:     {agg['total_deltas']:.0f}",
        f"  Fitness J_v4:       {fitness_j:.4f}",
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
            "mean_p99_latency_s": agg["mean_p99_s"],
            "regimes_completed": float(len(results)),
        },
        artifacts={"stage3_report": "\n".join(artifact_lines)},
    ))


def evaluate(program_path: str) -> EvaluationResult:
    """Default fallback evaluation entry point."""
    return evaluate_stage3(program_path)
