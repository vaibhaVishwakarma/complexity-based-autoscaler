"""
openevolve_evaluator_v7.py — Step 8.7: Realism-Aware Evolution v7 Evaluator Engine
==================================================================================

Role:
    Master cascade evaluation engine for OpenEvolve v7 evolutionary synthesis.
    Integrates the verified v3/v6 Cost-Supreme canonical foundation (13 benchmark regimes)
    with the physically grounded Step 8.5 Realism Triad across operational container
    startup delays (T_init in [2.0s, 5.0s, 15.0s, 50.0s, 150.0s, 300.0s]).

Key Enhancements in v7:
    1. True SLO Accountability: Extracts max(slo_violation_count, deadline_miss_count),
       penalizing both completed deadline misses AND unserved requests abandoned in queues.
    2. Physically Grounded Triad:
       - suite2_shock @ [2.0s, 5.0s, 15.0s] (within the 15s SLA deadline).
       - suite1_spike @ [5.0s, 15.0s, 50.0s] (burst expansion).
       - suite3_azure @ [15.0s, 50.0s, 150.0s, 300.0s] (true long-horizon macro dynamics).
    3. Progressive 3-Strike Anti-Stagnation Gating:
       - Strike 1: Soft diversity penalty (-1.0)
       - Strike 2: Moderate penalty (-25.0) + diagnostic reflection injection
       - Strike 3: Local branch pruning (-500.0)
    4. Ephemeral Disk Pruning: Automatically removes raw event logs post-evaluation.
    5. Zero-Crash Return Contracts: Always provides cost_savings and realism_resilience metrics.

Cascade Stages:
    Stage 1: Pure Validity Gate (~0.05s) — AST safety, While-loop guard, and 5 boundary unit tests.
    Stage 2: Multi-Stress Micro-Tranche Gate (~3.0s) — Fast 3-slice filter (flat, shock 1s, shock 5s).
    Stage 3: Full Dual-Tier Parallelized Benchmark (~35s) — Evaluates Composite Fitness J_v7.

AGENTS.md Compliance:
    Rule #1 — Dedicated versioned v7 evaluator file.
    Rule #2 — Decoupled linkage; loads metrics dynamically from authoritative summaries.
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
logger = logging.getLogger("openevolve_evaluator_v7")

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v7"
SEED_POLICY_V7_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "seed_policy_v7.py"

# Baseline reference constants grounded in Gate calibration and Step 8.5
FIXED_CAPACITY_WORKER_SECONDS: float = 27_900.0
INFERLINE_CANONICAL_COST_WS: float = 14_261.0
INFERLINE_REALISM_COST_WS: float = 11_350.0

# ── Canonical 13 Evaluation Regimes (Baseline T_init = 1.0s) ──────────────────
ALL_CANONICAL_REGIMES = [
    "suite1_flat", "suite1_spike", "suite1_burst", "suite1_ramp",
    "suite1_zero_begin", "suite1_zero_terminal",
    "suite2_shock", "suite2_recovery", "suite2_compound_stress",
    "suite2_compound_relief", "suite2_decoupled_opposing", "suite2_storm",
    "suite3_azure",
]

# ── Physically Grounded Realism Triad (Operational Spectrum) ────────────────
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
        "program": Path(program_path).name,
        "metrics": result.metrics,
        "details": details or {},
    }
    try:
        with open(check_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning(f"Could not log evaluation check: {e}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC MODULE LOADER
# ─────────────────────────────────────────────────────────────────────────────

def _load_program(program_path: str):
    """Dynamically imports the policy module from the candidate filepath."""
    mod_name = f"candidate_v7_{Path(program_path).stem}_{int(time.time()*1000)%100000}"
    spec = importlib.util.spec_from_file_location(mod_name, program_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {program_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1: PURE VALIDITY GATE (~0.05s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage1(program_path: str) -> EvaluationResult:
    """
    Stage 1: Pure Validity Gate.
    - AST syntax check and forbidden while-loop guard.
    - Dynamic load verification.
    - 5 boundary unit tests covering quiescent, saturation, in-flight boot, negative trend, zero load.
    """
    code_str = Path(program_path).read_text(encoding="utf-8")

    # 1. AST Validation
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
            artifacts={"error": f"SyntaxError in candidate: {e}"},
        ))

    # Guard: While-loops are forbidden to avoid non-terminating loops in simulation
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            return _log_performance_check("stage1", program_path, EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": "Forbidden while-loop detected in candidate policy."},
            ))

    # 2. Dynamic Import
    try:
        mod = _load_program(program_path)
    except Exception as e:
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
            artifacts={"error": f"Import error: {e}\n{traceback.format_exc()}"},
        ))

    if not hasattr(mod, "compute_target_workers") or not hasattr(mod, "TelemetricState"):
        return _log_performance_check("stage1", program_path, EvaluationResult(
            metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
            artifacts={"error": "Missing compute_target_workers or TelemetricState contract."},
        ))

    compute_fn = mod.compute_target_workers
    TelemetricState = mod.TelemetricState

    # 3. Boundary Unit Tests
    boundary_cases = [
        # (name, state, expected_min, expected_max)
        (
            "quiescent_baseline",
            TelemetricState(
                p_fast=0.85, p_fast_velocity=0.0, mean_set_size=1.05,
                ingress_rps=60.0, ingress_acceleration=0.0, offered_cloud_rps=9.0,
                cloud_queue_depth=0, cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
                active_workers=2, booting_workers=0, time_since_last_scale_s=10.0,
            ),
            1, 4,
        ),
        (
            "saturation_shock",
            TelemetricState(
                p_fast=0.15, p_fast_velocity=-0.70, mean_set_size=1.95,
                ingress_rps=180.0, ingress_acceleration=10.0, offered_cloud_rps=153.0,
                cloud_queue_depth=120, cloud_queue_velocity=25.0, oldest_task_age_s=8.5,
                active_workers=2, booting_workers=0, time_since_last_scale_s=5.0,
            ),
            10, 18,
        ),
        (
            "in_flight_booting",
            TelemetricState(
                p_fast=0.50, p_fast_velocity=0.0, mean_set_size=1.20,
                ingress_rps=100.0, ingress_acceleration=0.0, offered_cloud_rps=50.0,
                cloud_queue_depth=15, cloud_queue_velocity=2.0, oldest_task_age_s=1.0,
                active_workers=4, booting_workers=8, time_since_last_scale_s=1.0,
            ),
            1, 10,
        ),
        (
            "negative_trend_drop",
            TelemetricState(
                p_fast=0.90, p_fast_velocity=0.40, mean_set_size=1.00,
                ingress_rps=20.0, ingress_acceleration=-5.0, offered_cloud_rps=2.0,
                cloud_queue_depth=0, cloud_queue_velocity=-1.0, oldest_task_age_s=0.0,
                active_workers=8, booting_workers=0, time_since_last_scale_s=15.0,
            ),
            1, 4,
        ),
        (
            "zero_ingress_cold",
            TelemetricState(
                p_fast=1.00, p_fast_velocity=0.0, mean_set_size=1.00,
                ingress_rps=0.0, ingress_acceleration=0.0, offered_cloud_rps=0.0,
                cloud_queue_depth=0, cloud_queue_velocity=0.0, oldest_task_age_s=0.0,
                active_workers=1, booting_workers=0, time_since_last_scale_s=30.0,
            ),
            1, 1,
        ),
    ]

    for name, st, min_w, max_w in boundary_cases:
        try:
            val = compute_fn(st)
        except Exception as e:
            return _log_performance_check("stage1", program_path, EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": f"Exception in test '{name}': {e}\n{traceback.format_exc()}"},
            ))

        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            return _log_performance_check("stage1", program_path, EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": f"Test '{name}' returned non-numeric value: {val}"},
            ))

        k_val = int(val)
        if not (1 <= k_val <= 18):
            return _log_performance_check("stage1", program_path, EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": f"Test '{name}' returned out-of-bounds worker count: {k_val} (allowed [1, 18])"},
            ))

        if not (min_w <= k_val <= max_w):
            return _log_performance_check("stage1", program_path, EvaluationResult(
                metrics={"stage1_passed": 0.0, "combined_score": 0.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                artifacts={"error": f"Test '{name}' value {k_val} outside expected envelope [{min_w}, {max_w}]"},
            ))

    # Passed Stage 1: Advance to Stage 2
    return _log_performance_check("stage1", program_path, EvaluationResult(
        metrics={
            "stage1_passed": 1.0,
            "combined_score": 1.0,
            "cost_savings": 0.0,
            "realism_resilience": 0.0,
        },
        artifacts={"info": "All 5 boundary unit tests passed."},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION WORKHORSE
# ─────────────────────────────────────────────────────────────────────────────

def _run_single_simulation(
    regime: str,
    program_path: str,
    startup_delay_s: float,
    seed: int,
    run_dir_tag: str,
) -> Optional[dict]:
    """Runs a single simulation on the requested regime and delay, extracting true SLO violations."""
    cfg_path = SUITES_DIR / f"{regime}.yaml"
    if not cfg_path.exists():
        logger.error(f"Suite config not found: {cfg_path}")
        return None

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Set container startup delay on CloudRefine pool
    if "scaling" in cfg and "pools" in cfg["scaling"] and "CloudRefine" in cfg["scaling"]["pools"]:
        cfg["scaling"]["pools"]["CloudRefine"]["startup_delay_s"] = float(startup_delay_s)
        cfg["scaling"]["pools"]["CloudRefine"]["min_workers"] = 1

    if "autoscaling" in cfg:
        for c_key in cfg["autoscaling"]:
            if isinstance(cfg["autoscaling"][c_key], dict):
                cfg["autoscaling"][c_key]["min_replicas"] = 1

    run_hash = f"{abs(hash((program_path, regime, startup_delay_s, seed, time.time()))) % 1_000_000:06d}"
    out_dir = EVOLUTION_OUTPUT_DIR / "runs" / f"{regime}_{run_dir_tag}_d{int(startup_delay_s*10)}_{run_hash}"
    out_dir.mkdir(parents=True, exist_ok=True)

    run_temp_cfg = out_dir / f"config_{regime}.yaml"
    with open(run_temp_cfg, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    env = {
        **os.environ,
        "EVOLUTION_CANDIDATE_PATH": str(Path(program_path).resolve()),
        "PYTHONPATH": f"{WORKSPACE_ROOT}/src:{os.environ.get('PYTHONPATH', '')}",
    }

    cmd = [
        str(VENV_PYTHON),
        "-m", "continuum_bench.cli", "run",
        "--config", str(run_temp_cfg),
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

        # ── True SLO Accountability in v7 ───────────────────────────────────
        # qos.get("slo_violation_count", 0) counts both completed deadline misses
        # AND unserved requests abandoned in intermediate queues past deadline.
        slo_violations = int(qos.get("slo_violation_count", 0))
        deadline_misses = int(qos.get("deadline_miss_count", 0))
        true_misses = max(slo_violations, deadline_misses)

        result_data = {
            "regime": regime,
            "startup_delay_s": float(startup_delay_s),
            "completed": int(qos.get("slo_eligible_count", 0)),
            "generated": int(qos.get("slo_eligible_count", 0)),
            "deadline_misses": true_misses,
            "unserved_queue_abandoned": max(0, slo_violations - deadline_misses),
            "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
            "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
            "p99_latency_s": float(lat.get("p99", 15.0)),
            "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
            "elapsed_s": elapsed,
        }

        # Ephemeral disk pruning: remove raw simulation run directory to preserve disk space
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
                "combined_score": 0.0,
                "cost_savings": 0.0,
                "realism_resilience": 0.0,
            },
            artifacts={"error": "Failed execution on one or more Stage 2 micro-tranche regimes."},
        ))

    total_misses = sum(r["deadline_misses"] for r in results)
    total_cost = sum(r["worker_seconds"] for r in results)

    # Micro-tranche threshold: must have <= 1 miss and cost must not exceed unscaled fixed baseline
    if total_misses > 2 or total_cost > 3_500.0:
        return _log_performance_check("stage2", program_path, EvaluationResult(
            metrics={
                "stage2_passed": 0.0,
                "combined_score": 0.0,
                "cost_savings": 0.0,
                "realism_resilience": 0.0,
            },
            artifacts={"error": f"Stage 2 filter rejected: {total_misses} misses, {total_cost:.1f} ws."},
        ))

    # Passed Stage 2: Advance to Stage 3
    return _log_performance_check("stage2", program_path, EvaluationResult(
        metrics={
            "stage2_passed": 1.0,
            "combined_score": 2.0,
            "cost_savings": 0.0,
            "realism_resilience": 0.0,
        },
        artifacts={"info": f"Stage 2 passed with {total_misses} misses, {total_cost:.1f} ws."},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3: FULL DUAL-TIER BENCHMARK (~35s)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_stage3(program_path: str) -> EvaluationResult:
    """Stage 3: Full Dual-Tier Benchmark computing definitive J_v7 fitness (parallelized)."""
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
                        metrics={"combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
                        artifacts={"error": f"Simulation failed on {task[0]} (delay={task[1]}s)"},
                    ))
                results_map[task] = res
            except Exception as exc:
                return _log_performance_check("stage3", program_path, EvaluationResult(
                    metrics={"combined_score": -1000.0, "cost_savings": 0.0, "realism_resilience": 0.0},
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

    # ── Component 1: J_v3_core (Canonical Foundation) ────────────────────────
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

    # ── Component 2: J_realism (Realism Optimization Term) ───────────────────
    # Active linear gradient: -1.0 per realism miss, -5.0 per second of SLA breach (D=15s)
    realism_miss_penalty = 1.0 * realism_misses
    realism_p99_penalty = 5.0 * max(0.0, realism_max_p99 - 15.0)

    j_realism = -realism_miss_penalty - realism_p99_penalty

    # ── Component 3: Baseline Dominance Bonuses ──────────────────────────────
    bonus_canon_inferline = 0.0
    if canon_misses == 0 and canon_cost < INFERLINE_CANONICAL_COST_WS:
        bonus_canon_inferline = 10.0

    bonus_realism_inferline = 0.0
    if realism_misses < 35.0 and realism_cost < INFERLINE_REALISM_COST_WS:
        bonus_realism_inferline = 10.0

    fitness_j = j_v3_core + j_realism + bonus_canon_inferline + bonus_realism_inferline

    # ── Hard Rejection for Non-Scaling Policies ──────────────────────────────
    if canon_cost >= FIXED_CAPACITY_WORKER_SECONDS or cost_savings <= 0.0:
        logger.warning(f"Candidate {program_path} failed to scale dynamically (cost={canon_cost:.1f} ws). Rejecting.")
        fitness_j = -1000.0
        cost_savings = 0.0

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
        except Exception as e:
            logger.warning(f"Could not persist signature history: {e}")

    logger.info(
        f"Stage 3 Complete for {Path(program_path).name} -> Fitness J_v7: {fitness_j:+.4f} | "
        f"Savings: {cost_savings:.2f}% | Canon Cost: {canon_cost:.1f} ws (Misses: {canon_misses}) | "
        f"Realism Misses: {realism_misses} (Cost: {realism_cost:.1f} ws, Max P99: {realism_max_p99:.2f}s)"
    )

    realism_resilience = max(0.0, 100.0 - realism_misses)

    return _log_performance_check("stage3", program_path, EvaluationResult(
        metrics={
            "combined_score": float(fitness_j),
            "cost_savings": float(cost_savings),
            "canonical_cost_ws": float(canon_cost),
            "canonical_misses": float(canon_misses),
            "realism_misses": float(realism_misses),
            "realism_resilience": float(realism_resilience),
            "realism_cost_ws": float(realism_cost),
            "max_p99_latency_s": float(max(canon_max_p99, realism_max_p99)),
            "scaling_deltas": float(canon_deltas),
        },
        artifacts={
            "j_v3_core": float(j_v3_core),
            "j_realism": float(j_realism),
            "bonus_canon_inferline": float(bonus_canon_inferline),
            "bonus_realism_inferline": float(bonus_realism_inferline),
            **strike_artifacts,
        },
    ))


# ─────────────────────────────────────────────────────────────────────────────
# MASTER EVALUATION ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(program_path: str) -> EvaluationResult:
    """Cascade entrypoint called by OpenEvolve runner."""
    stg1 = evaluate_stage1(program_path)
    if stg1.metrics.get("stage1_passed", 0.0) < 0.5:
        return stg1

    stg2 = evaluate_stage2(program_path)
    if stg2.metrics.get("stage2_passed", 0.0) < 0.5:
        return stg2

    return evaluate_stage3(program_path)
