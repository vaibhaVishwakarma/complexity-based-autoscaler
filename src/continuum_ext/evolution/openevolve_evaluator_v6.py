"""
openevolve_evaluator_v6.py — Step 8.6: Realism-Aware Evolution v6 Evaluator Engine
==================================================================================

Role:
    Master cascade evaluation engine for OpenEvolve v6 evolutionary synthesis.
    Integrates the proven v3 Cost-Supreme canonical foundation (13 benchmark regimes)
    with the physically grounded Step 8.5 Realism Triad across operational container
    startup delays (T_init in [2.0s, 5.0s, 15.0s, 50.0s, 150.0s, 300.0s]).

Cascade Stages:
    Stage 1: Pure Validity Gate (~0.05s) — AST safety, While-loop guard, and 5 boundary unit tests.
    Stage 2: Multi-Stress Micro-Tranche Gate (~3.0s) — Fast 3-slice filter (flat, shock 1s, shock 5s).
    Stage 3: Full Dual-Tier Parallelized Benchmark (~35s):
             - Tier 1: 13 Canonical regimes (T_init = 1.0s, 121,134 requests)
             - Tier 2: 10 Physically Grounded Realism regimes (Azure diurnal, burst spikes, semantic shocks)
             - Evaluates Composite Fitness J_v6 with active gradient and signature deduplication.
             - Ephemeral disk cleanup: immediately prunes raw simulation logs to preserve disk space.

Lineage:
    Built upon openevolve_evaluator_v3.py (authoritative baseline) and
    openevolve_evaluator_v5.py, correcting the v5 physical duration trap.

AGENTS.md Compliance:
    Rule #1 — Dedicated v6 versioned evaluator file.
    Rule #2 — Decoupled linkage; loads metrics dynamically; zero hardcoding.
    Rule #3 — Strictly uses workspace virtual environment (./.venv/bin/python).
    Rule #4 — Self-documenting structure and inline comments.
    Rule #5 — Tool grounding; uses verified libraries; zero oracle leakage.
"""

from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import importlib.util
import json
import logging
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    from openevolve.evaluator import EvaluationResult
except ImportError:
    @dataclass
    class EvaluationResult:
        metrics: Dict[str, float]
        artifacts: Dict[str, Any]


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("openevolve_evaluator_v6")

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v6"
CHAMPION_V3_PATH = WORKSPACE_ROOT / "output" / "evolved_policy_v3.py"

# Baseline reference constants grounded in Gate calibration and Step 8.5
FIXED_CAPACITY_WORKER_SECONDS: float = 27_900.0
INFERLINE_CANONICAL_COST_WS: float = 14_261.0
INFERLINE_REALISM_COST_WS: float = 11_350.0  # InferLine cost across the 10 realism regimes

# ── Canonical 13 Evaluation Regimes (Baseline T_init = 1.0s from v3) ─────────
ALL_CANONICAL_REGIMES = [
    "suite1_flat", "suite1_spike", "suite1_burst", "suite1_ramp",
    "suite1_zero_begin", "suite1_zero_terminal",
    "suite2_shock", "suite2_recovery", "suite2_compound_stress",
    "suite2_compound_relief", "suite2_decoupled_opposing", "suite2_storm",
    "suite3_azure",
]

# ── Physically Grounded Realism Triad (Step 8.5 Empirical Tipping Points) ────
# Spans achievable operational spectrum where autoscaling is physically operable
REALISM_BENCHMARK_TRIAD = [
    # 1. Diurnal Production (Azure 14-day): Multi-minute container boot resilience
    ("suite3_azure", 15.0),
    ("suite3_azure", 50.0),
    ("suite3_azure", 150.0),
    ("suite3_azure", 300.0),
    # 2. Acute Ingress Spikes: Burst absorption up to the 50s tipping point
    ("suite1_spike", 5.0),
    ("suite1_spike", 15.0),
    ("suite1_spike", 50.0),
    # 3. Opposing Semantic Shocks: Triage drift preemption up to 15s SLA deadline tipping point
    ("suite2_shock", 2.0),
    ("suite2_shock", 5.0),
    ("suite2_shock", 15.0),
]

# ── Stage 2 Fast Micro-Tranche Regimes ───────────────────────────────────────
STAGE2_MICRO_TRANCHE = [
    ("suite1_flat", 1.0),
    ("suite2_shock", 1.0),
    ("suite2_shock", 5.0),
]


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _log_performance_check(stage: str, program_path: str, result: EvaluationResult, details: dict = None) -> EvaluationResult:
    """Logs evaluation details and saves checks to evaluator_checks.jsonl."""
    log_dir = EVOLUTION_OUTPUT_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    check_file = log_dir / "evaluator_checks.jsonl"
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stage": stage,
        "program_path": program_path,
        "metrics": result.metrics,
        "details": details or {},
    }
    try:
        with open(check_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning(f"Could not append to evaluator_checks.jsonl: {e}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1: PURE VALIDITY & PURITY GATE (~0.05s)
# ─────────────────────────────────────────────────────────────────────────────

FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "urllib", "requests", "http",
    "shutil", "glob", "pickle", "importlib", "builtins", "eval", "exec",
    "threading", "multiprocessing", "concurrent", "asyncio", "ctypes",
}


def evaluate_stage1(program_path: str) -> EvaluationResult:
    """Stage 1: Purity, syntax, while-loop guard, and boundary unit test gate."""
    p_path = Path(program_path)
    if not p_path.exists():
        return EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
            artifacts={"error": "File does not exist"},
        )

    try:
        with open(p_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(p_path))
    except SyntaxError as e:
        return EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
            artifacts={"error": f"SyntaxError: {e}"},
        )

    # 1. AST Purity and Loop Audit
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                    return EvaluationResult(
                        metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                        artifacts={"error": f"Forbidden import: {alias.name}"},
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
                return EvaluationResult(
                    metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                    artifacts={"error": f"Forbidden from-import: {node.module}"},
                )
        elif isinstance(node, ast.While):
            return EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": "Forbidden While loop detected: autoscaler laws must be closed-form algebraic expressions."},
            )

    # 2. Dynamic Import Contract Validation
    try:
        mod_name = f"candidate_v6_{p_path.stem}_{int(time.time()*1000)%100000}"
        spec = importlib.util.spec_from_file_location(mod_name, str(p_path))
        if spec is None or spec.loader is None:
            return EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": "Cannot load module spec"},
            )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)

        if not hasattr(mod, "compute_target_workers"):
            return EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": "Missing compute_target_workers function"},
            )
        if not hasattr(mod, "TelemetricState"):
            return EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": "Missing TelemetricState contract dataclass"},
            )

        TelemetricStateCls = mod.TelemetricState

        # 3. Five Boundary State Unit Tests
        test_states = [
            # Quiescent baseline
            TelemetricStateCls(
                p_fast=1.0, p_fast_velocity=0.0, mean_set_size=1.0,
                ingress_rps=0.0, ingress_acceleration=0.0, offered_cloud_rps=0.0,
                cloud_queue_depth=0, cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
                active_workers=1, booting_workers=0, time_since_last_scale_s=10.0,
            ),
            # Saturating acute shock
            TelemetricStateCls(
                p_fast=0.10, p_fast_velocity=-0.40, mean_set_size=3.5,
                ingress_rps=200.0, ingress_acceleration=20.0, offered_cloud_rps=180.0,
                cloud_queue_depth=40, cloud_queue_velocity=15.0, oldest_task_age_s=6.0,
                active_workers=2, booting_workers=0, time_since_last_scale_s=0.5,
            ),
            # In-flight booting credit test
            TelemetricStateCls(
                p_fast=0.50, p_fast_velocity=0.0, mean_set_size=1.1,
                ingress_rps=64.0, ingress_acceleration=0.0, offered_cloud_rps=32.0,
                cloud_queue_depth=2, cloud_queue_velocity=-1.0, oldest_task_age_s=0.2,
                active_workers=2, booting_workers=4, time_since_last_scale_s=1.2,
            ),
            # Rapid negative velocity drain
            TelemetricStateCls(
                p_fast=0.90, p_fast_velocity=0.25, mean_set_size=1.0,
                ingress_rps=20.0, ingress_acceleration=-10.0, offered_cloud_rps=2.0,
                cloud_queue_depth=0, cloud_queue_velocity=-6.0, oldest_task_age_s=0.0,
                active_workers=8, booting_workers=0, time_since_last_scale_s=4.0,
            ),
            # Uncertainty surge with task aging
            TelemetricStateCls(
                p_fast=0.25, p_fast_velocity=-0.15, mean_set_size=4.5,
                ingress_rps=100.0, ingress_acceleration=8.0, offered_cloud_rps=75.0,
                cloud_queue_depth=16, cloud_queue_velocity=4.0, oldest_task_age_s=3.5,
                active_workers=4, booting_workers=2, time_since_last_scale_s=1.0,
            ),
        ]

        for s in test_states:
            k = mod.compute_target_workers(s)
            if not isinstance(k, (int, float)) or math.isnan(k) or k < 1 or k > 18:
                return EvaluationResult(
                    metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                    artifacts={"error": f"Invalid output k={k} (must be int in [1, 18])"},
                )

    except Exception as e:
        return EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
            artifacts={"error": f"Execution exception: {e}\n{traceback.format_exc()}"},
        )

    return EvaluationResult(
        metrics={"stage1_passed": 1.0, "combined_score": 1.0, "cost_savings": 0.0, "realism_resilience": 0.0},
        artifacts={"status": "Stage 1 Purity & Boundary Gate Passed"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION EXECUTION HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _run_single_simulation(
    regime: str,
    program_path: str,
    startup_delay_s: float = 1.0,
    seed: int = 42,
    run_dir_tag: str = "",
) -> Optional[dict]:
    """Runs a single ContinuumBench simulation with overridden startup delay and k_min >= 1."""
    cfg_path = SUITES_DIR / f"{regime}.yaml"
    if not cfg_path.exists():
        logger.error(f"Config not found: {cfg_path}")
        return None

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Configure startup delay and enforce enterprise baseline k_min >= 1
    if "scaling" in cfg and "pools" in cfg["scaling"] and "CloudRefine" in cfg["scaling"]["pools"]:
        cfg["scaling"]["pools"]["CloudRefine"]["startup_delay_s"] = float(startup_delay_s)
        cfg["scaling"]["pools"]["CloudRefine"]["min_workers"] = 1

    if "autoscaling" in cfg:
        for c_key in cfg["autoscaling"]:
            if isinstance(cfg["autoscaling"][c_key], dict):
                cfg["autoscaling"][c_key]["min_replicas"] = 1

    stem = Path(program_path).stem
    out_dir = EVOLUTION_OUTPUT_DIR / stem / f"{regime}_d{int(startup_delay_s*10):04d}_{run_dir_tag}"
    out_dir.mkdir(parents=True, exist_ok=True)

    temp_cfg = out_dir / "config_run.yaml"
    with open(temp_cfg, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    env = {
        **os.environ,
        "EVOLUTION_CANDIDATE_PATH": str(program_path),
        "PYTHONPATH": f"{WORKSPACE_ROOT}/src:{os.environ.get('PYTHONPATH', '')}",
    }

    cmd = [
        str(VENV_PYTHON),
        "-m", "continuum_bench.cli", "run",
        "--config", str(temp_cfg),
        "--controller", "evolved_conformal",
        "--seed", str(seed),
        "--out", str(out_dir),
    ]

    t0 = time.time()
    try:
        res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, timeout=180, env=env)
        elapsed = time.time() - t0
        if res.returncode != 0:
            logger.warning(f"Run failed for {regime} (delay={startup_delay_s}s):\n{res.stderr[:300]}")
            return None

        subdirs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
        if not subdirs:
            return None

        summary_file = subdirs[-1] / "summary.json"
        if not summary_file.exists():
            return None

        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)

        lat = summary.get("latency_s", {})
        cost = summary.get("cost", {})
        qos = summary.get("qos", {})
        stab = summary.get("stability", {})
        delay = summary.get("delay_breakdown_s", {})

        result_data = {
            "regime": regime,
            "startup_delay_s": float(startup_delay_s),
            "completed": int(qos.get("slo_eligible_count", 0)),
            "generated": int(qos.get("slo_eligible_count", 0)),
            "deadline_misses": int(qos.get("deadline_miss_count", 0)),
            "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
            "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
            "p99_latency_s": float(lat.get("p99", 15.0)),
            "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
            "elapsed_s": elapsed,
        }

        # Ephemeral disk pruning: remove raw simulation run directory to prevent disk exhaustion
        try:
            shutil.rmtree(out_dir, ignore_errors=True)
        except Exception:
            pass

        return result_data

    except Exception as e:
        logger.error(f"Simulation exception on {regime}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2: MULTI-STRESS MICRO-TRANCHE GATE (~3.0s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage2(program_path: str) -> EvaluationResult:
    """Stage 2: Micro-Tranche filter assessing basic flat, baseline shock, and moderate delay."""
    results = []
    for regime, delay in STAGE2_MICRO_TRANCHE:
        res = _run_single_simulation(regime, program_path, startup_delay_s=delay, seed=42, run_dir_tag="stg2")
        if res is not None:
            results.append(res)

    if len(results) < len(STAGE2_MICRO_TRANCHE):
        return _log_performance_check("stage2", program_path, EvaluationResult(
            metrics={
                "stage2_passed": 0.0,
                "combined_score": -500.0,
                "cost_savings": 0.0,
                "realism_resilience": 0.0,
            },
            artifacts={"error": f"Failed Stage 2 simulations ({len(results)}/{len(STAGE2_MICRO_TRANCHE)})"},
        ))

    total_misses = sum(r["deadline_misses"] for r in results)
    total_cost = sum(r["worker_seconds"] for r in results)
    max_p99 = max(r["p99_latency_s"] for r in results)

    # Rejection criteria: must not exceed 5 misses on the fast triad, and max P99 <= 15s
    passed = (total_misses <= 5) and (max_p99 <= 15.0)

    stage2_baseline_ws = 4338.0
    stage2_cost_savings = (1.0 - total_cost / stage2_baseline_ws) * 100.0 if stage2_baseline_ws > 0 else 0.0

    summary = (
        f"Stage 2 Micro-Tranche (flat 1s, shock 1s, shock 5s):\n"
        f"  Total Misses: {total_misses}\n"
        f"  Max P99: {max_p99:.2f}s\n"
        f"  Total Cost: {total_cost:.1f}ws (Savings: {stage2_cost_savings:.2f}%)\n"
        f"  Passed: {passed}"
    )

    return _log_performance_check("stage2", program_path, EvaluationResult(
        metrics={
            "stage2_passed": 1.0 if passed else 0.0,
            "combined_score": 1.0 if passed else -200.0,
            "cost_savings": float(stage2_cost_savings),
            "stage2_misses": float(total_misses),
            "stage2_cost": float(total_cost),
            "realism_resilience": 0.0,
        },
        artifacts={"stage2_summary": summary},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: AUTHORITATIVE DUAL-TIER BENCHMARK & FITNESS J_v6 (~35s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage3(program_path: str) -> EvaluationResult:
    """Stage 3: Full Dual-Tier Benchmark computing definitive J_v6 fitness (parallelized)."""
    canonical_tasks = [(regime, 1.0, "canon") for regime in ALL_CANONICAL_REGIMES]
    realism_tasks = [(regime, delay, f"realism_{int(delay)}") for regime, delay in REALISM_BENCHMARK_TRIAD]
    all_tasks = canonical_tasks + realism_tasks

    results_map: Dict[Tuple[str, float, str], dict] = {}
    max_workers = min(4, os.cpu_count() or 2)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(_run_single_simulation, regime, program_path, delay, 42, tag): (regime, delay, tag)
            for regime, delay, tag in all_tasks
        }
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                res = future.result()
                if res is None:
                    return _log_performance_check("stage3", program_path, EvaluationResult(
                        metrics={"combined_score": -1000.0, "cost_savings": -100.0, "realism_resilience": 0.0},
                        artifacts={"error": f"Simulation failed on {task[0]} (delay={task[1]}s)"},
                    ))
                results_map[task] = res
            except Exception as exc:
                return _log_performance_check("stage3", program_path, EvaluationResult(
                    metrics={"combined_score": -1000.0, "cost_savings": -100.0, "realism_resilience": 0.0},
                    artifacts={"error": f"Simulation exception on {task[0]}: {exc}"},
                ))

    canonical_results = [results_map[t] for t in canonical_tasks]
    realism_results = [results_map[t] for t in realism_tasks]

    canon_misses = sum(r["deadline_misses"] for r in canonical_results)
    canon_cost = sum(r["worker_seconds"] for r in canonical_results)
    canon_deltas = sum(r["scaling_deltas"] for r in canonical_results)
    canon_max_p99 = max(r["p99_latency_s"] for r in canonical_results)

    realism_misses = sum(r["deadline_misses"] for r in realism_results)
    realism_cost = sum(r["worker_seconds"] for r in realism_results)
    realism_max_p99 = max((r["p99_latency_s"] for r in realism_results), default=0.0)

    # ── Component 1: J_v3_core (Tier 1 Canonical Criteria from v3) ───────────
    cost_savings = (1.0 - canon_cost / FIXED_CAPACITY_WORKER_SECONDS) * 100.0

    # Miss penalty: 2.0 per miss up to 10, harsh 20.0 per miss above 10
    canon_miss_penalty = (
        2.0 * min(canon_misses, 10.0) +
        20.0 * max(0.0, canon_misses - 10.0)
    )

    # Tail latency penalty: SLA baseline set to 6.0s on canonical suites
    p99_penalty = 10.0 * max(0.0, canon_max_p99 - 6.0)

    # Actuation churn penalty
    churn_penalty = 0.01 * canon_deltas

    j_v3_core = cost_savings - canon_miss_penalty - p99_penalty - churn_penalty

    # ── Component 2: J_realism (Tier 2 Realism Optimization Term) ────────────
    # Active linear gradient: -1.0 per realism miss, -5.0 per second of SLA breach (D=15s)
    realism_miss_penalty = 1.0 * realism_misses
    realism_p99_penalty = 5.0 * max(0.0, realism_max_p99 - 15.0)

    j_realism = -realism_miss_penalty - realism_p99_penalty

    # ── Component 3: Baseline Dominance Bonuses ──────────────────────────────
    bonus_canon_inferline = 0.0
    if canon_misses == 0 and canon_cost < INFERLINE_CANONICAL_COST_WS:
        bonus_canon_inferline = 10.0

    bonus_realism_inferline = 0.0
    # InferLine suffers ~31-45 misses on realism triad; award +10 if beating InferLine
    if realism_misses < 35.0 and realism_cost < INFERLINE_REALISM_COST_WS:
        bonus_realism_inferline = 10.0

    fitness_j = j_v3_core + j_realism + bonus_canon_inferline + bonus_realism_inferline

    # ── Hard Rejection for Non-Scaling Policies ──────────────────────────────
    if canon_cost >= FIXED_CAPACITY_WORKER_SECONDS or cost_savings <= 0.0:
        logger.warning(f"Candidate {program_path} failed to scale dynamically (cost={canon_cost:.1f} ws). Rejecting.")
        fitness_j = -1000.0
        cost_savings = -100.0

    # ── Signature Deduplication (Progressive 3-Strike Anti-Stagnation Gating) ──
    history_file = EVOLUTION_OUTPUT_DIR / "fitness_signature_history.json"
    is_seed = ("seed_policy" in Path(program_path).stem or "champion" in Path(program_path).stem)
    sig_key = f"{canon_cost:.1f}_{canon_misses}_{realism_misses}_{canon_deltas:.0f}"

    seen_signatures = {}
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                seen_signatures = json.load(f)
        except Exception:
            seen_signatures = {}

    strike_artifacts: Dict[str, Any] = {}
    if not is_seed and sig_key in seen_signatures:
        entry = seen_signatures[sig_key]
        if isinstance(entry, dict):
            count = int(entry.get("count", 1)) + 1
            first_seen = str(entry.get("program", "unknown"))
        else:
            count = 2
            first_seen = str(entry)

        seen_signatures[sig_key] = {
            "count": count,
            "program": first_seen,
            "last": Path(program_path).stem,
            "last_seen_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        if count == 2:
            # Strike 1: First duplicate occurrence - Soft diversity penalty
            logger.info(f"Duplicate signature strike 1 ({sig_key}) matching {first_seen}. Soft diversity penalty (-1.0).")
            fitness_j -= 1.0
            strike_artifacts["diagnostic_feedback"] = (
                f"DIVERSITY NOTICE (Strike 1): Output signature matched existing policy {first_seen}. "
                "Minor diversity penalty (-1.0) applied. Policy remains viable in archive as a parent."
            )
        elif count == 3:
            # Strike 2: Second duplicate occurrence - Stagnation warning & moderate penalty
            logger.warning(f"Duplicate signature strike 2 ({sig_key}) matching {first_seen}. Moderate penalty (-25.0).")
            fitness_j -= 25.0
            strike_artifacts["diagnostic_feedback"] = (
                "CRITICAL FEEDBACK (Strike 2): Continuous decimal parameter modifications were absorbed by "
                "integer capacity clamping k = int(clamp(...)), producing identical integer cluster actuation. "
                "Stop micro-tuning decimal constants. You MUST introduce structural, non-linear logic (e.g. conditional "
                "booting credits conditioned on dQ/dt or oldest_task_age_s, or early fast-path velocity triggers) to achieve progress."
            )
        else:
            # Strike 3+: Repeated duplicate - Local branch pruning
            logger.warning(f"Duplicate signature strike {count} ({sig_key}) matching {first_seen}. Branch pruning (-500.0).")
            fitness_j = -500.0
            strike_artifacts["diagnostic_feedback"] = (
                f"STAGNATION PRUNING (Strike {count}): Branch exhausted with identical integer output signature {count} times. "
                "Candidate pruned from parent selection so evolution focuses on novel structural branches."
            )
    elif not is_seed:
        seen_signatures[sig_key] = {
            "count": 1,
            "program": Path(program_path).stem,
            "last": Path(program_path).stem,
            "last_seen_time": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    if not is_seed:
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(seen_signatures, f, indent=2)
        except Exception:
            pass

    summary_text = (
        f"=== EVALUATOR v6 DUAL-TIER BENCHMARK SUMMARY ===\n"
        f"TIER 1 CANONICAL (T_init = 1.0s across 13 suites):\n"
        f"  Cost: {canon_cost:.1f} ws (Savings: {cost_savings:.2f}% vs Fixed)\n"
        f"  Misses: {canon_misses} / 121,134 requests\n"
        f"  Max P99 Latency: {canon_max_p99:.2f}s\n"
        f"  Actuation Churn: {canon_deltas:.0f} deltas\n"
        f"  InferLine Canonical Bonus: +{bonus_canon_inferline:.1f}\n"
        f"TIER 2 REALISM TRIAD (T_init in 2s..300s across 10 suites):\n"
        f"  Realism Misses: {realism_misses}\n"
        f"  Realism Cost: {realism_cost:.1f} ws\n"
        f"  Realism Max P99: {realism_max_p99:.2f}s\n"
        f"  InferLine Realism Bonus: +{bonus_realism_inferline:.1f}\n"
        f"OVERALL FITNESS J_v6: {fitness_j:.4f}\n"
    )

    metrics = {
        "combined_score": float(fitness_j),
        "cost_savings": float(cost_savings),
        "canonical_misses": float(canon_misses),
        "realism_misses": float(realism_misses),
        "churn_stability": float(max(0.0, 500.0 - canon_deltas)),
        "realism_resilience": float(max(0.0, 100.0 - realism_misses)),
        "tail_safety": float(max(0.0, 15.0 - canon_max_p99)),
        "worker_seconds": float(canon_cost),
        "scaling_deltas": float(canon_deltas),
        "deadline_misses": float(canon_misses),
        "max_p99_latency_s": float(canon_max_p99),
        "fitness_j_v6": float(fitness_j),
    }

    # Final cleanup of candidate directory if present
    try:
        candidate_sim_dir = EVOLUTION_OUTPUT_DIR / Path(program_path).stem
        if candidate_sim_dir.exists():
            shutil.rmtree(candidate_sim_dir, ignore_errors=True)
    except Exception:
        pass

    all_artifacts = {"summary": summary_text, **strike_artifacts}
    return _log_performance_check("stage3", program_path, EvaluationResult(
        metrics=metrics,
        artifacts=all_artifacts,
    ))


def evaluate(program_path: str) -> EvaluationResult:
    """Fallback single-entry point."""
    return evaluate_stage3(program_path)
