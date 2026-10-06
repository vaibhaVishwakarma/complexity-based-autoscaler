#!/usr/bin/env python3
"""
run_step8_multiseed_v3.py — Step 8 v3: Multi-Seed Statistical Validation Simulation Runner

Role:
    Executes multi-seed evaluation of the Step 7 v3 Champion Evolved Conformal Policy
    (output/evolved_policy_v3.py) against all 4 baseline controllers (InferLine, Fixed,
    Kubernetes HPA, KEDA Queue) across N independent stochastic seeds.
    Logs all detailed QoS, cost, tail latency, queue dynamics, and actuation stability
    metrics into a single centralized directory (output/step8_multiseed_runs_v3/).

Gate Stage:    Step 8 v3 (Multi-Seed Statistical Validation Gate)
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 12
Preceding:     docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V3.md
               docs/HEAD_TO_HEAD_INFERLINE_VS_V3_COMPARISON.md

Controllers Evaluated:
    1. evolved_conformal       (Champion Policy bbd9b1c2: output/evolved_policy_v3.py)
    2. inferline               (ACM SoCC '20 Multi-Scale Envelope Tuner)
    3. fixed_capacity          (Static Peak Oracle: k=18)
    4. hpa                     (Kubernetes CPU Utilization Threshold: U=0.70)
    5. keda                    (Kubernetes Event-driven Autoscaling: Q=5)

Default Stochastic Seeds (N=10):
    [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]
    (Seed 42: Training/Calibration; Seeds 101-909: 9 Held-Out Unseen Evaluation Seeds)

Leakage Prevention & Isolation Guarantees:
    1. Zero Temporal Lookahead: Controllers observe only past/current telemetric signals.
    2. Strict Process Isolation: Each simulation runs in a separate Python subprocess.
    3. Paired Determinism: All controllers receive bit-for-bit identical requests for a given (regime, seed).
    4. Resume Capability: Skips re-running completed simulations if summary.json already exists.

Outputs:
    - output/step8_multiseed_runs_v3/raw_runs/<controller>/<regime>/seed_<seed>/summary.json
    - output/step8_multiseed_runs_v3/multiseed_summary.csv
    - output/step8_multiseed_runs_v3/multiseed_raw_readings.json

AGENTS.md Compliance:
    Rule #1 — Dedicated versioned script (run_step8_multiseed_v3.py).
    Rule #2 — Dynamically links output/evolved_policy_v3.py via EVOLUTION_CANDIDATE_PATH.
    Rule #3 — Runs strictly with workspace ./.venv/bin/python.
    Rule #4 — Self-documenting with header docstring and inline commentary.
    Rule #5 — Uses standard numpy, pandas, and json libraries.
    Rule #6 — Ground truth evaluation on calibrated 13 regimes without synthetic fallbacks.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# WORKSPACE & DIRECTORY SETUP
# ─────────────────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "step8_multiseed_runs_v3"
DEFAULT_CHAMPION_PATH = WORKSPACE_ROOT / "output" / "evolved_policy_v3.py"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Step8v3Runner")

# Authoritative 13 ContinuumBench Workload Regimes
ALL_REGIMES = [
    "suite1_flat",
    "suite1_spike",
    "suite1_burst",
    "suite1_ramp",
    "suite1_zero_begin",
    "suite1_zero_terminal",
    "suite2_shock",
    "suite2_recovery",
    "suite2_compound_stress",
    "suite2_compound_relief",
    "suite2_decoupled_opposing",
    "suite2_storm",
    "suite3_azure",
]

# Benchmark Controllers
CONTROLLERS = [
    ("evolved_conformal", "Evolved Conformal v3 (Champion bbd9b1c2)"),
    ("inferline", "InferLine Tuner (ACM SoCC '20)"),
    ("fixed_capacity", "Fixed Capacity Peak (k=18)"),
    ("hpa", "Kubernetes HPA (Util=0.70)"),
    ("keda", "KEDA Queue (Backlog=5)"),
]

DEFAULT_SEEDS = [42, 101, 202, 303, 404, 505, 606, 707, 808, 909]


# ─────────────────────────────────────────────────────────────────────────────
# PRE-FLIGHT AUDIT
# ─────────────────────────────────────────────────────────────────────────────

def run_preflight_audit(champion_path: Path) -> bool:
    """Certifies that environment, candidate policy, and configs are valid."""
    logger.info("=================================================================")
    logger.info("        STEP 8 V3 PRE-FLIGHT VALIDATION & INTEGRITY AUDIT        ")
    logger.info("=================================================================")

    if not VENV_PYTHON.exists():
        logger.error(f"[AUDIT FAIL] Workspace .venv Python not found: {VENV_PYTHON}")
        return False
    logger.info(f"[PASS] Python interpreter: {VENV_PYTHON}")

    if not champion_path.exists():
        logger.error(f"[AUDIT FAIL] Champion policy not found: {champion_path}")
        return False

    # Check importability of the champion policy
    try:
        check_code = (
            f"import sys; sys.path.insert(0, '{WORKSPACE_ROOT}'); "
            f"import output.{champion_path.stem} as ep; "
            f"print('Policy imported cleanly')"
        )
        res = subprocess.run([str(VENV_PYTHON), "-c", check_code], capture_output=True, text=True, cwd=str(WORKSPACE_ROOT))
        if res.returncode != 0:
            logger.error(f"[AUDIT FAIL] Policy import error:\n{res.stderr}")
            return False
        logger.info(f"[PASS] Policy {champion_path.name} imports cleanly.")
    except Exception as e:
        logger.error(f"[AUDIT FAIL] Policy verification exception: {e}")
        return False

    for regime in ALL_REGIMES:
        cfg = SUITES_DIR / f"{regime}.yaml"
        if not cfg.exists():
            logger.error(f"[AUDIT FAIL] Missing suite config: {cfg}")
            return False
    logger.info(f"[PASS] All {len(ALL_REGIMES)} suite configurations verified.")

    logger.info("-----------------------------------------------------------------")
    logger.info("AUDIT COMPLETE: ALL PRE-FLIGHT CHECKS PASSED.")
    logger.info("=================================================================\n")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION EXECUTION WORKER
# ─────────────────────────────────────────────────────────────────────────────

def execute_single_simulation(
    regime: str,
    ctrl_key: str,
    ctrl_name: str,
    seed: int,
    out_root: Path,
    champion_path: Path,
    force_rerun: bool = False,
) -> Dict[str, Any]:
    """
    Executes a single simulation in an isolated subprocess.
    Writes summary.json into out_root/raw_runs/<ctrl_key>/<regime>/seed_<seed>/
    """
    cfg_path = SUITES_DIR / f"{regime}.yaml"
    raw_dir = out_root / "raw_runs" / ctrl_key / regime / f"seed_{seed}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Resume check: Return cached data if already completed
    run_dirs = sorted([d for d in raw_dir.iterdir() if d.is_dir()]) if not force_rerun else []
    if run_dirs:
        summary_file = run_dirs[-1] / "summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                qos = data.get("qos", {})
                cost = data.get("cost", {})
                stab = data.get("stability", {})
                lat = data.get("latency_s", {})
                delay = data.get("delay_breakdown_s", {})

                if qos.get("slo_eligible_count", 0) > 0:
                    return {
                        "controller": ctrl_name,
                        "controller_key": ctrl_key,
                        "regime": regime,
                        "seed": seed,
                        "status": "CACHED",
                        "elapsed_s": 0.0,
                        "completed_requests": int(qos.get("slo_eligible_count", 0)),
                        "deadline_misses": int(qos.get("deadline_miss_count", 0)),
                        "deadline_miss_rate": float(qos.get("deadline_miss_rate", 0.0)),
                        "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
                        "mean_workers": float(cost.get("mean_active_workers", 0.0)),
                        "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
                        "mean_latency_s": float(lat.get("mean", 0.0)),
                        "p50_latency_s": float(lat.get("p50", 0.0)),
                        "p90_latency_s": float(lat.get("p90", 0.0)),
                        "p95_latency_s": float(lat.get("p95", 0.0)),
                        "p99_latency_s": float(lat.get("p99", 0.0)),
                        "max_latency_s": float(lat.get("max", lat.get("p99", 0.0))),
                        "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
                        "summary_path": str(summary_file),
                    }
            except Exception:
                pass

    env = {
        **os.environ,
        "PYTHONPATH": f"{WORKSPACE_ROOT}/src:{os.environ.get('PYTHONPATH', '')}",
        "EVOLUTION_CANDIDATE_PATH": str(champion_path),
    }

    cmd = [
        str(VENV_PYTHON),
        "-m", "continuum_bench.cli", "run",
        "--config", str(cfg_path),
        "--controller", ctrl_key,
        "--seed", str(seed),
        "--out", str(raw_dir),
    ]

    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), env=env, capture_output=True, text=True)
    elapsed = time.time() - t0

    if res.returncode != 0:
        logger.warning(f"Run failed: {ctrl_key} | {regime} | Seed {seed} in {elapsed:.1f}s\nError: {res.stderr[:200]}")
        return {
            "controller": ctrl_name,
            "controller_key": ctrl_key,
            "regime": regime,
            "seed": seed,
            "status": "FAILED",
            "elapsed_s": elapsed,
            "error": res.stderr[:500],
        }

    run_dirs = sorted([d for d in raw_dir.iterdir() if d.is_dir()])
    if not run_dirs:
        return {
            "controller": ctrl_name,
            "controller_key": ctrl_key,
            "regime": regime,
            "seed": seed,
            "status": "NO_RUN_DIR",
            "elapsed_s": elapsed,
        }

    summary_file = run_dirs[-1] / "summary.json"
    if not summary_file.exists():
        return {
            "controller": ctrl_name,
            "controller_key": ctrl_key,
            "regime": regime,
            "seed": seed,
            "status": "MISSING_SUMMARY",
            "elapsed_s": elapsed,
        }

    try:
        with open(summary_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        qos = data.get("qos", {})
        cost = data.get("cost", {})
        stab = data.get("stability", {})
        lat = data.get("latency_s", {})
        delay = data.get("delay_breakdown_s", {})

        return {
            "controller": ctrl_name,
            "controller_key": ctrl_key,
            "regime": regime,
            "seed": seed,
            "status": "SUCCESS",
            "elapsed_s": elapsed,
            "completed_requests": int(qos.get("slo_eligible_count", 0)),
            "deadline_misses": int(qos.get("deadline_miss_count", 0)),
            "deadline_miss_rate": float(qos.get("deadline_miss_rate", 0.0)),
            "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
            "mean_workers": float(cost.get("mean_active_workers", 0.0)),
            "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
            "mean_latency_s": float(lat.get("mean", 0.0)),
            "p50_latency_s": float(lat.get("p50", 0.0)),
            "p90_latency_s": float(lat.get("p90", 0.0)),
            "p95_latency_s": float(lat.get("p95", 0.0)),
            "p99_latency_s": float(lat.get("p99", 0.0)),
            "max_latency_s": float(lat.get("max", lat.get("p99", 0.0))),
            "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
            "summary_path": str(summary_file),
        }
    except Exception as e:
        return {
            "controller": ctrl_name,
            "controller_key": ctrl_key,
            "regime": regime,
            "seed": seed,
            "status": "PARSE_ERROR",
            "elapsed_s": elapsed,
            "error": str(e),
        }


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCHER & ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────

def parse_seed_list(seed_inputs: List[Any]) -> List[int]:
    out = []
    for item in seed_inputs:
        s = str(item).strip()
        if "-" in s and not s.startswith("-"):
            parts = s.split("-", 1)
            out.extend(range(int(parts[0]), int(parts[1]) + 1))
        elif ".." in s:
            parts = s.split("..", 1)
            out.extend(range(int(parts[0]), int(parts[1]) + 1))
        else:
            out.append(int(s))
    return sorted(list(set(out)))


def main():
    parser = argparse.ArgumentParser(description="Step 8 v3: Multi-Seed Statistical Validation Runner")
    parser.add_argument("--seeds", nargs="+", default=[str(s) for s in DEFAULT_SEEDS], help="List of seeds or range e.g. 1042-1061")
    parser.add_argument("--regimes", nargs="+", default=ALL_REGIMES, help="List of regimes to evaluate")
    parser.add_argument("--controllers", nargs="+", default=[k for k, _ in CONTROLLERS], help="Controllers to benchmark")
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4), help="Parallel subprocess workers")
    parser.add_argument("--candidate", type=str, default=str(DEFAULT_CHAMPION_PATH), help="Path to evolved policy v3")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory for all runs")
    parser.add_argument("--force", action="store_true", help="Force re-run even if cached")
    parser.add_argument("--smoke", action="store_true", help="Execute 1 iteration smoke test (1 regime, 1 seed, 2 controllers)")

    args = parser.parse_args()
    champion_path = Path(args.candidate).resolve()
    out_root = Path(args.output_dir).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    if not run_preflight_audit(champion_path):
        sys.exit(1)

    if args.smoke:
        seeds = [42]
        regimes = ["suite1_flat"]
        controllers = [
            ("evolved_conformal", "Evolved Conformal v3 (Champion bbd9b1c2)"),
            ("inferline", "InferLine Tuner (ACM SoCC '20)"),
        ]
        logger.info("[SMOKE TEST MODE ENABLED] Running 1 regime (suite1_flat), 1 seed (42), 2 controllers.")
    else:
        seeds = parse_seed_list(args.seeds)
        regimes = args.regimes
        controllers = [(k, n) for k, n in CONTROLLERS if k in args.controllers]

    tasks = []
    for regime in regimes:
        for seed in seeds:
            for ctrl_key, ctrl_name in controllers:
                tasks.append((regime, ctrl_key, ctrl_name, seed))

    total_runs = len(tasks)
    logger.info(f"Target Runs: {total_runs} (Regimes={len(regimes)}, Seeds={len(seeds)}, Controllers={len(controllers)})")
    logger.info(f"Parallel Workers: {args.workers}")
    logger.info(f"Output Directory: {out_root}")

    results = []
    t_start = time.time()
    completed_count = 0

    if args.workers > 1 and len(tasks) > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            future_to_task = {
                executor.submit(
                    execute_single_simulation,
                    reg, key, name, s, out_root, champion_path, args.force
                ): (reg, key, s)
                for reg, key, name, s in tasks
            }

            for future in as_completed(future_to_task):
                task_meta = future_to_task[future]
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    logger.error(f"Task {task_meta} raised exception: {e}")
                completed_count += 1
                if completed_count % max(1, total_runs // 10) == 0 or completed_count == total_runs:
                    logger.info(f"Progress: [{completed_count:4d}/{total_runs:4d}] runs completed ({completed_count/total_runs*100:.1f}%)")
    else:
        for reg, key, name, s in tasks:
            res = execute_single_simulation(reg, key, name, s, out_root, champion_path, args.force)
            results.append(res)
            completed_count += 1
            logger.info(f"Progress: [{completed_count:4d}/{total_runs:4d}] {key} | {reg} | seed={s} -> {res.get('status')} ({res.get('worker_seconds', 0):.1f} ws, {res.get('deadline_misses', 0)} miss)")

    total_duration = time.time() - t_start
    logger.info(f"All {len(results)} simulations completed in {total_duration:.1f}s.")

    # Save to consolidated CSV and JSON inside out_root
    df = pd.DataFrame(results)
    csv_path = out_root / "multiseed_summary.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Consolidated CSV saved to: {csv_path}")

    json_path = out_root / "multiseed_raw_readings.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Consolidated JSON saved to: {json_path}")

    # Print quick console overview
    print("\n" + "=" * 80)
    print("STEP 8 V3 MULTI-SEED RUN COMPLETED")
    print("=" * 80)
    if "status" in df.columns:
        print(f"Status breakdown:\n{df['status'].value_counts().to_string()}\n")
    if "completed_requests" in df.columns:
        print("Aggregate Metrics Summary by Controller:")
        agg = df.groupby("controller_key").agg({
            "completed_requests": "sum",
            "deadline_misses": "sum",
            "worker_seconds": ["mean", "sum"],
            "p99_latency_s": "max",
            "scaling_deltas": "mean",
        })
        print(agg.to_string())
    print("=" * 80)
    print(f"Next Step: Run processing script: ./.venv/bin/python scripts/process_step8_v3_statistics.py --input-dir {out_root}")


if __name__ == "__main__":
    main()
