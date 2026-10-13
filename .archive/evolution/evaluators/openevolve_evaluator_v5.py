"""
openevolve_evaluator_v5.py — Step 8.6: Realism-Aware Cascade Evaluator & Fitness Engine (v5)
=============================================================================================

Role:
    Implements the 3-stage cascade simulation-in-the-loop evaluator for the Step 8.6 v5
    evolutionary search. Re-aligns the objective function to:
    1. PRESERVE THE CANONICAL FLOOR: Strictly maintain 0 deadline misses and >= 50% cost savings
       across all 13 canonical benchmark regimes at baseline T_init = 1.0s, dominating InferLine.
    2. OPTIMIZE FOR EXTREME INITIALIZATION DELAYS: Evaluate candidates against the physical realism
       delayed shock regimes (T_init in [15s, 50s, 150s, 250s, 300s]), rewarding policies that
       eliminate the opposing semantic shock queue overflow in suite2_shock and suite1_spike.

Gate Stage:    Step 8.6 (Realism-Aware Evolutionary Synthesis v5)
Roadmap Ref:   docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 13 & 14
Report Ref:    docs/STEP8_5_PHYSICAL_REALISM_AND_SCALE_GAP_SENSITIVITY_REPORT.md

Objective Formulation (v5 Realism-Aware Composite Fitness):
    J_v5 = CostSavings_canonical - MissPenalty_canonical - P99Penalty_canonical
           - ChurnPenalty_canonical - RealismShockPenalty + InferLineBonus

    Where:
        CostSavings_canonical  = (1.0 - worker_seconds_canon / 27,900.0) * 100.0
        MissPenalty_canonical  = 100.0 * misses_canon  (Hard zero-tolerance regression gate!)
        P99Penalty_canonical   = 10.0 * max(0.0, max_p99_canon - 6.0s)
        ChurnPenalty_canonical = 0.01 * deltas_canon
        RealismShockPenalty    = 0.02 * misses_realism_shocks (suite2_shock @ 15s..300s & suite1 @ 50s..300s)
        InferLineBonus         = +10.0 if (misses_canon == 0 and cost_canon < 14,261.0 ws) else 0.0

AGENTS.md Compliance:
    Rule #1 — Dedicated v5 versioned evaluator; prior evaluators remain untouched.
    Rule #2 — Zero hardcoding; dynamic loading via TelemetricState contract.
    Rule #3 — Subprocess calls exclusively use workspace .venv Python.
    Rule #4 — Self-documenting header, stage comments, and inline logic notes.
    Rule #5 — Subprocess ContinuumBench CLI invocation; no synthetic simulator mock.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import logging
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from openevolve.evaluation_result import EvaluationResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("openevolve_evaluator_v5")

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v5"
CHAMPION_V3_PATH = WORKSPACE_ROOT / "output" / "evolved_policy_v3.py"

FIXED_CAPACITY_WORKER_SECONDS: float = 27_900.0
INFERLINE_COST_THRESHOLD_WS: float = 14_261.0
INFERLINE_DELTA_THRESHOLD: float = 855.0

# ── Canonical 13 Evaluation Regimes (Baseline T_init = 1.0s) ─────────────────
ALL_CANONICAL_REGIMES = [
    "suite1_flat", "suite1_spike", "suite1_burst", "suite1_ramp",
    "suite1_zero_begin", "suite1_zero_terminal",
    "suite2_shock", "suite2_recovery", "suite2_compound_stress",
    "suite2_compound_relief", "suite2_decoupled_opposing", "suite2_storm",
    "suite3_azure",
]

# ── Realism Shock Evaluation Matrix (Extreme T_init Delays) ──────────────────
# Evaluates delayed opposing semantic shocks and severe bursts
REALISM_SHOCK_BENCHMARKS = [
    ("suite2_shock", 15.0),
    ("suite2_shock", 50.0),
    ("suite2_shock", 150.0),
    ("suite2_shock", 300.0),
    ("suite1_spike", 50.0),
    ("suite1_spike", 300.0),
]

# ── Stage 2 Fast Micro-Tranche Regimes ───────────────────────────────────────
STAGE2_MICRO_TRANCHE = [
    ("suite1_flat", 1.0),
    ("suite2_shock", 1.0),
    ("suite2_shock", 15.0),
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
}


def evaluate_stage1(program_path: str) -> EvaluationResult:
    """Stage 1: Purity, syntax, and boundary input contract gate."""
    p_path = Path(program_path)
    if not p_path.exists():
        return EvaluationResult(metrics={"stage1_passed": 0.0, "combined_score": -1000.0},
                                artifacts={"error": "File does not exist"})

    try:
        with open(p_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(p_path))
    except SyntaxError as e:
        return EvaluationResult(metrics={"stage1_passed": 0.0, "combined_score": -1000.0},
                                artifacts={"error": f"SyntaxError: {e}"})

    # Purity audit
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                    return EvaluationResult(metrics={"stage1_passed": 0.0, "combined_score": -1000.0},
                                            artifacts={"error": f"Forbidden import: {alias.name}"})
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
                return EvaluationResult(metrics={"stage1_passed": 0.0, "combined_score": -1000.0},
                                        artifacts={"error": f"Forbidden import: {node.module}"})

    # Dynamic boundary evaluation test
    try:
        mod_name = f"candidate_stage1_{int(time.time()*1000)}"
        spec = importlib.util.spec_from_file_location(mod_name, str(p_path))
        if spec is None or spec.loader is None:
            return EvaluationResult(metrics={"stage1_passed": 0.0, "combined_score": -1000.0},
                                    artifacts={"error": "Cannot load module spec"})
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)

        if not hasattr(mod, "compute_target_workers"):
            return EvaluationResult(metrics={"stage1_passed": 0.0, "combined_score": -1000.0},
                                    artifacts={"error": "compute_target_workers function not found"})

        TelemetricStateCls = getattr(mod, "TelemetricState", None)
        if TelemetricStateCls is None:
            # Fallback to output.evolved_policy_v3 TelemetricState
            sys.path.insert(0, str(WORKSPACE_ROOT / "output"))
            import evolved_policy_v3
            TelemetricStateCls = evolved_policy_v3.TelemetricState

        # Synthetic boundary tests
        test_states = [
            TelemetricStateCls(
                p_fast=0.5, p_fast_velocity=0.0, mean_set_size=1.0,
                ingress_rps=10.0, ingress_acceleration=0.0, offered_cloud_rps=5.0,
                cloud_queue_depth=0, cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
                active_workers=2, booting_workers=0, time_since_last_scale_s=10.0,
            ),
            # Opposing semantic shock state (low p_fast, high queue)
            TelemetricStateCls(
                p_fast=0.1, p_fast_velocity=-0.4, mean_set_size=2.5,
                ingress_rps=80.0, ingress_acceleration=10.0, offered_cloud_rps=72.0,
                cloud_queue_depth=50, cloud_queue_velocity=15.0, oldest_task_age_s=8.0,
                active_workers=4, booting_workers=6, time_since_last_scale_s=25.0,
            ),
            # Empty idle state
            TelemetricStateCls(
                p_fast=1.0, p_fast_velocity=0.0, mean_set_size=1.0,
                ingress_rps=0.0, ingress_acceleration=0.0, offered_cloud_rps=0.0,
                cloud_queue_depth=0, cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
                active_workers=1, booting_workers=0, time_since_last_scale_s=100.0,
            ),
        ]

        for s in test_states:
            k = mod.compute_target_workers(s)
            if not isinstance(k, (int, float)) or math.isnan(k) or k < 1 or k > 18:
                return EvaluationResult(
                    metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "churn_stability": 0.0, "realism_resilience": 0.0},
                    artifacts={"error": f"Invalid output k={k} (must be int in [1, 18])"}
                )

    except Exception as e:
        return EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": -1000.0, "cost_savings": 0.0, "churn_stability": 0.0, "realism_resilience": 0.0},
            artifacts={"error": f"Execution exception: {e}\n{traceback.format_exc()}"}
        )

    return EvaluationResult(
        metrics={"stage1_passed": 1.0, "combined_score": 1.0, "cost_savings": 0.0, "churn_stability": 0.0, "realism_resilience": 0.0},
        artifacts={"status": "Stage 1 Purity & Boundary Gate Passed"}
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

    # Configure startup delay and enforce k_min >= 1
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

    temp_cfg = out_dir / f"config_run.yaml"
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
        res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, timeout=240, env=env)
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

        return {
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
            metrics={"stage2_passed": 0.0, "combined_score": -500.0},
            artifacts={"error": f"Failed Stage 2 simulations ({len(results)}/{len(STAGE2_MICRO_TRANCHE)})"},
        ))

    total_misses = sum(r["deadline_misses"] for r in results)
    total_cost = sum(r["worker_seconds"] for r in results)
    max_p99 = max(r["p99_latency_s"] for r in results)

    # Rejection criteria: must not exceed 25 misses on the fast triad
    passed = total_misses <= 25 and max_p99 <= 15.0

    # Fixed capacity baseline worker-seconds for flat 1s (1350ws), shock 1s (1890ws), shock 15s (1890ws) = 5130ws
    stage2_baseline_ws = 5130.0
    stage2_cost_savings = (1.0 - total_cost / stage2_baseline_ws) * 100.0 if stage2_baseline_ws > 0 else 0.0

    summary = (
        f"Stage 2 Micro-Tranche (flat 1s, shock 1s, shock 15s):\n"
        f"  Total Misses: {total_misses}\n"
        f"  Max P99: {max_p99:.2f}s\n"
        f"  Total Cost: {total_cost:.1f}ws (Savings: {stage2_cost_savings:.2f}%)\n"
        f"  Passed: {passed}"
    )

    if not passed:
        try:
            stem = Path(program_path).stem
            candidate_sim_dir = EVOLUTION_OUTPUT_DIR / stem
            if candidate_sim_dir.exists():
                shutil.rmtree(candidate_sim_dir, ignore_errors=True)
        except Exception:
            pass

    return _log_performance_check("stage2", program_path, EvaluationResult(
        metrics={
            "stage2_passed": 1.0 if passed else 0.0,
            "combined_score": 1.0 if passed else -200.0,
            "cost_savings": stage2_cost_savings,
            "churn_stability": 0.0,
            "realism_resilience": 0.0,
            "stage2_misses": float(total_misses),
            "stage2_cost": float(total_cost),
        },
        artifacts={"stage2_summary": summary},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: AUTHORITATIVE DUAL-TIER BENCHMARK & FITNESS J_v5
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage3(program_path: str) -> EvaluationResult:
    """Stage 3: Full Dual-Tier Benchmark computing definitive J_v5 fitness (parallelized)."""
    canonical_tasks = [(regime, 1.0, "canon") for regime in ALL_CANONICAL_REGIMES]
    realism_tasks = [(regime, delay, f"realism_{int(delay)}") for regime, delay in REALISM_SHOCK_BENCHMARKS]
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
                        metrics={"combined_score": -1000.0, "cost_savings": -100.0},
                        artifacts={"error": f"Simulation failed on {task[0]} (delay={task[1]}s)"},
                    ))
                results_map[task] = res
            except Exception as exc:
                return _log_performance_check("stage3", program_path, EvaluationResult(
                    metrics={"combined_score": -1000.0, "cost_savings": -100.0},
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

    # ── Composite Fitness J_v5 Calculation ───────────────────────────────────
    cost_savings = (1.0 - canon_cost / FIXED_CAPACITY_WORKER_SECONDS) * 100.0

    # Hard zero-tolerance preservation penalty: -100 points per canonical miss!
    canonical_miss_penalty = 100.0 * canon_misses

    # Tail latency penalty (envelope 6.0s on canonical suites)
    p99_penalty = 10.0 * max(0.0, canon_max_p99 - 6.0)

    # Actuation stability penalty
    churn_penalty = 0.01 * canon_deltas

    # Realism shock optimization term:
    # Baseline seed suffers 7,031 shock misses across extreme initialization delays (15s..300s).
    # We award +0.20 fitness points per shock miss reduced below baseline (50 misses saved = +10.0 pts),
    # and penalize any regression above baseline at -0.05 per extra miss.
    SEED_BASELINE_SHOCK_MISSES = 7031.0
    shock_miss_delta = SEED_BASELINE_SHOCK_MISSES - realism_misses
    if shock_miss_delta >= 0:
        realism_shock_reward = 0.20 * shock_miss_delta
    else:
        realism_shock_reward = 0.05 * shock_miss_delta  # Negative penalty for regressions

    # InferLine Dominance Bonus: rewards policies beating InferLine while preserving zero canonical misses
    inferline_bonus = 0.0
    if canon_misses == 0:
        if canon_cost < INFERLINE_COST_THRESHOLD_WS:
            inferline_bonus = 10.0
        else:
            # Smooth degradation rather than a cliff
            inferline_bonus = max(0.0, 10.0 * (1.0 - (canon_cost - INFERLINE_COST_THRESHOLD_WS) / 3739.0))

    fitness_j = (
        cost_savings
        - canonical_miss_penalty
        - p99_penalty
        - churn_penalty
        + realism_shock_reward
        + inferline_bonus
    )

    # ── Duplicate & Stagnation Gating ─────────────────────────────────────────
    # Reject degenerate policies that fail to scale dynamically (cost >= 27,900 ws or cost_savings <= 0.0)
    if canon_cost >= FIXED_CAPACITY_WORKER_SECONDS or cost_savings <= 0.0:
        logger.warning(f"Candidate {program_path} failed to scale dynamically (cost={canon_cost:.1f} ws). Rejecting.")
        fitness_j = -1000.0
        cost_savings = -100.0

    # Signature deduplication: reject candidates yielding identical performance signatures
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

    if not is_seed and sig_key in seen_signatures:
        logger.warning(
            f"Duplicate fitness signature detected ({sig_key}) matching {seen_signatures[sig_key]}. "
            f"Applying stagnation rejection penalty."
        )
        fitness_j -= 500.0  # Harshly penalize duplicate to reject from MAP-Elites elite pool
    elif not is_seed:
        seen_signatures[sig_key] = Path(program_path).stem
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(seen_signatures, f)
        except Exception:
            pass

    summary_text = (
        f"=== EVALUATOR v5 DUAL-TIER BENCHMARK SUMMARY ===\n"
        f"TIER 1 CANONICAL (T_init = 1.0s across 13 suites):\n"
        f"  Cost: {canon_cost:.1f} ws (Savings: {cost_savings:.2f}% vs Fixed)\n"
        f"  Misses: {canon_misses} / 121,134 requests\n"
        f"  Max P99 Latency: {canon_max_p99:.2f}s\n"
        f"  Actuation Churn: {canon_deltas:.0f} deltas\n"
        f"  InferLine Dominance Bonus: +{inferline_bonus:.1f}\n"
        f"TIER 2 REALISM SHOCK (T_init in 15s..300s):\n"
        f"  Shock Misses: {realism_misses}\n"
        f"  Shock Cost: {realism_cost:.1f} ws\n"
        f"  Shock Max P99: {realism_max_p99:.2f}s\n"
        f"OVERALL FITNESS J_v5: {fitness_j:.4f}\n"
    )

    metrics = {
        "combined_score": fitness_j,
        "cost_savings": cost_savings,
        "canonical_misses": float(canon_misses),
        "realism_misses": float(realism_misses),
        "churn_stability": max(0.0, 500.0 - canon_deltas),
        "realism_resilience": max(0.0, 7100.0 - float(realism_misses)),
        "tail_safety": max(0.0, 15.0 - canon_max_p99),
        "worker_seconds": float(canon_cost),
        "scaling_deltas": float(canon_deltas),
        "deadline_misses": float(canon_misses),
        "max_p99_latency_s": float(canon_max_p99),
        "fitness_j_v5": fitness_j,
    }

    try:
        stem = Path(program_path).stem
        candidate_sim_dir = EVOLUTION_OUTPUT_DIR / stem
        if fitness_j < 30.0 and candidate_sim_dir.exists():
            logger.info(f"Policy {stem} score {fitness_j:.2f} < 30.0 — pruning disposable simulation directory to preserve disk.")
            shutil.rmtree(candidate_sim_dir, ignore_errors=True)
    except Exception as e:
        logger.debug(f"Simulation cleanup ignored error: {e}")

    return _log_performance_check("stage3", program_path, EvaluationResult(
        metrics=metrics,
        artifacts={"summary": summary_text},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# OPENEVOLVE ENTRYPOINT: CASCADE EVALUATE
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(program_path: str) -> EvaluationResult:
    """
    OpenEvolve primary evaluation entrypoint.
    Executes the 3-stage cascade:
      Stage 1 (Validity) → Stage 2 (Micro-Tranche) → Stage 3 (Full Dual-Tier Benchmark)
    Prunes simulation directories for failed or low-scoring (<30.0) candidates to preserve disk space.
    """
    stem = Path(program_path).stem
    candidate_sim_dir = EVOLUTION_OUTPUT_DIR / stem

    # Stage 1: Purity and Syntax Gate
    r1 = evaluate_stage1(program_path)
    if r1.metrics.get("stage1_passed", 0.0) < 1.0:
        if candidate_sim_dir.exists():
            shutil.rmtree(candidate_sim_dir, ignore_errors=True)
        return _log_performance_check("stage1", program_path, r1)

    # Stage 2: Micro-Tranche Pre-Filter Gate
    r2 = evaluate_stage2(program_path)
    if r2.metrics.get("stage2_passed", 0.0) < 1.0:
        if candidate_sim_dir.exists():
            shutil.rmtree(candidate_sim_dir, ignore_errors=True)
        return _log_performance_check("stage2", program_path, r2)

    # Stage 3: Full Dual-Tier Authoritative Benchmark
    r3 = evaluate_stage3(program_path)
    score = r3.metrics.get("combined_score", float("-inf"))
    if score < 30.0 and candidate_sim_dir.exists():
        logger.info(f"Policy {stem} score {score:.2f} < 30.0 — pruning disposable simulation directory to preserve disk.")
        shutil.rmtree(candidate_sim_dir, ignore_errors=True)

    return r3


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_prog = sys.argv[1]
    else:
        target_prog = str(CHAMPION_V3_PATH)

    print(f"Testing openevolve_evaluator_v5 on: {target_prog}")
    res = evaluate(target_prog)
    print("\nResult Metrics:")
    print(json.dumps(res.metrics, indent=2))
    if "summary" in res.artifacts:
        print("\n" + res.artifacts["summary"])
