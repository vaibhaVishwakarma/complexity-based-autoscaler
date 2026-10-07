"""
scripts/run_realism_gap_stress_suite.py — Unified Realism & Scale-Gap Stress Suite Runner
========================================================================================
Role:
    Executes Step 8.5 Physical Realism and Scale-Gap Stress experiments across the smooth,
    non-impulsive container startup delay ladder:
        T_boot in [0.5s, 1.0s, 5.0s, 15.0s, 50.0s, 100.0s, 150.0s, 200.0s, 250.0s, 300.0s]
    Evaluates Evolved Conformal v3, InferLine, HPA, KEDA, and Plan B Adaptive Conformal
    under a strictly unified enterprise baseline (k_min >= 1).

Governance:
    AGENTS.md Rule #1 — Dedicated versioned evaluation script.
    AGENTS.md Rule #2 — Zero hardcoding; outputs saved to typed JSON manifest & CSV.
    AGENTS.md Rule #3 — Dedicated workspace venv at ./.venv/bin/python.
    AGENTS.md Rule #4 — Self-documenting structure with clear headers and inline comments.
    AGENTS.md Rule #7 — Script accepts explicit CLI arguments, provides smoke mode for testing.

Outputs:
    - output/realism_stress_results/manifest.json
    - output/realism_stress_results/summary.csv
    - Epoch logs for all executed runs under output/realism_stress_results/runs/
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("realism_stress_runner")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
CANDIDATE_PATH = WORKSPACE_ROOT / "output" / "evolved_policy_v3.py"
OUT_BASE = WORKSPACE_ROOT / "output" / "realism_stress_results"

SMOOTH_DELAY_LADDER = [0.5, 1.0, 5.0, 15.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0]
DEFAULT_CONTROLLERS = [
    "evolved_conformal",
    "inferline",
    "hpa",
    "keda",
]
DEFAULT_STRESS_TRIAD = [
    "suite1_spike",
    "suite2_shock",
    "suite3_azure",
]


def run_single_simulation(
    regime: str,
    controller: str,
    startup_delay_s: float,
    seed: int,
    out_dir: Path,
    macro_trace: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Execute a single ContinuumBench run with overridden startup_delay_s and enforced k_min >= 1.
    """
    if macro_trace:
        cfg_file_name = "macro_azure_deep_trace.yaml"
    else:
        cfg_file_name = f"{regime}.yaml"

    cfg_path = WORKSPACE_ROOT / "configs" / "suites" / cfg_file_name
    if not cfg_path.exists():
        logger.error(f"Config not found: {cfg_path}")
        return None

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Enforce startup delay on CloudRefine pool
    if "scaling" in cfg and "pools" in cfg["scaling"] and "CloudRefine" in cfg["scaling"]["pools"]:
        cfg["scaling"]["pools"]["CloudRefine"]["startup_delay_s"] = float(startup_delay_s)
        # Enforce unified enterprise baseline k_min >= 1
        cfg["scaling"]["pools"]["CloudRefine"]["min_workers"] = 1

    # Enforce min_replicas >= 1 across all autoscaling blocks
    if "autoscaling" in cfg:
        for c_key in cfg["autoscaling"]:
            if isinstance(cfg["autoscaling"][c_key], dict):
                cfg["autoscaling"][c_key]["min_replicas"] = 1

    run_temp_cfg = out_dir / f"config_delay_{startup_delay_s:.1f}s.yaml"
    with open(run_temp_cfg, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    # Check for existing completed run (idempotent resume)
    subdirs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
    if subdirs:
        summary_file = subdirs[-1] / "summary.json"
        if summary_file.exists():
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    summary = json.load(f)
                qos = summary.get("qos", {})
                if qos.get("slo_eligible_count", 0) > 0:
                    lat = summary.get("latency_s", {})
                    cost = summary.get("cost", {})
                    stab = summary.get("stability", {})
                    delay = summary.get("delay_breakdown_s", {})
                    return {
                        "regime": regime,
                        "controller": controller,
                        "startup_delay_s": float(startup_delay_s),
                        "seed": seed,
                        "completed": int(qos.get("slo_eligible_count", 0)),
                        "deadline_misses": int(qos.get("deadline_miss_count", 0)),
                        "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
                        "mean_active_workers": float(cost.get("mean_active_workers", 0.0)),
                        "p99_latency_s": float(lat.get("p99", 0.0)),
                        "p95_latency_s": float(lat.get("p95", 0.0)),
                        "mean_latency_s": float(lat.get("mean", 0.0)),
                        "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
                        "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
                        "startup_delay_total_s": float(stab.get("startup_delay_s_total", 0.0)),
                        "execution_time_s": 0.0,
                    }
            except Exception:
                pass

    env = {
        **os.environ,
        "EVOLUTION_CANDIDATE_PATH": str(CANDIDATE_PATH),
        "PYTHONPATH": f"{WORKSPACE_ROOT}/src:{os.environ.get('PYTHONPATH', '')}",
    }

    cmd = [
        str(VENV_PYTHON),
        "-m", "continuum_bench.cli", "run",
        "--config", str(run_temp_cfg),
        "--controller", controller,
        "--seed", str(seed),
        "--out", str(out_dir),
    ]

    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, env=env)
    elapsed = time.time() - t0

    if res.returncode != 0:
        logger.error(f"Run failed for {controller} on {regime} (delay={startup_delay_s}s):\n{res.stderr[:400]}")
        return None

    # Find the created run directory
    subdirs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
    if not subdirs:
        logger.error("No run directory created.")
        return None

    summary_file = subdirs[-1] / "summary.json"
    if not summary_file.exists():
        logger.error(f"Summary file missing: {summary_file}")
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
        "controller": controller,
        "startup_delay_s": float(startup_delay_s),
        "seed": seed,
        "completed": int(qos.get("slo_eligible_count", 0)),
        "deadline_misses": int(qos.get("deadline_miss_count", 0)),
        "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
        "mean_active_workers": float(cost.get("mean_active_workers", 0.0)),
        "p99_latency_s": float(lat.get("p99", 0.0)),
        "p95_latency_s": float(lat.get("p95", 0.0)),
        "mean_latency_s": float(lat.get("mean", 0.0)),
        "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
        "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
        "startup_delay_total_s": float(stab.get("startup_delay_s_total", 0.0)),
        "execution_time_s": float(elapsed),
    }


def main():
    parser = argparse.ArgumentParser(description="Run Step 8.5 Physical Realism & Scale-Gap Stress Suite")
    parser.add_argument("--smoke", action="store_true", help="Fast smoke test on 3 delays on suite1_spike with seed 42")
    parser.add_argument("--delays", type=float, nargs="+", default=None, help="Explicit list of startup delays (s)")
    parser.add_argument("--controllers", type=str, nargs="+", default=None, help="Controllers to evaluate")
    parser.add_argument("--regimes", type=str, nargs="+", default=None, help="Regimes to evaluate")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42], help="Random seeds (default: 42)")
    parser.add_argument("--macro", action="store_true", help="Run 1,800s macro Azure trace benchmark")
    parser.add_argument("--out", type=str, default=str(OUT_BASE), help="Output directory")
    args = parser.parse_args()

    out_base = Path(args.out)
    out_base.mkdir(parents=True, exist_ok=True)
    runs_dir = out_base / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        delays = [0.5, 5.0, 50.0]
        controllers = ["evolved_conformal", "inferline", "hpa", "keda"]
        regimes = ["suite1_spike"]
        seeds = [42]
        logger.info("Executing SMOKE TEST mode (fast check)")
    else:
        delays = args.delays if args.delays is not None else SMOOTH_DELAY_LADDER
        controllers = args.controllers if args.controllers is not None else DEFAULT_CONTROLLERS
        regimes = args.regimes if args.regimes is not None else DEFAULT_STRESS_TRIAD
        seeds = args.seeds

    logger.info("=" * 80)
    logger.info("STARTING STEP 8.5 REALISM & SCALE-GAP STRESS SUITE")
    logger.info(f"Controllers: {controllers}")
    logger.info(f"Startup Delays: {delays}")
    logger.info(f"Regimes: {regimes}")
    logger.info(f"Seeds: {seeds}")
    logger.info(f"Unified Baseline: k_min >= 1 enforced")
    logger.info("=" * 80)

    results: List[Dict[str, Any]] = []
    total_runs = len(regimes) * len(controllers) * len(delays) * len(seeds)
    run_idx = 0

    for regime in regimes:
        for controller in controllers:
            for delay in delays:
                for seed in seeds:
                    run_idx += 1
                    logger.info(
                        f"[{run_idx:03d}/{total_runs:03d}] "
                        f"{controller} | {regime} | delay={delay:5.1f}s | seed={seed}"
                    )
                    run_out = runs_dir / f"{regime}_{controller}_d{int(delay*10):04d}_s{seed}"
                    run_out.mkdir(parents=True, exist_ok=True)

                    res = run_single_simulation(
                        regime=regime,
                        controller=controller,
                        startup_delay_s=delay,
                        seed=seed,
                        out_dir=run_out,
                        macro_trace=args.macro,
                    )
                    if res:
                        results.append(res)
                        logger.info(
                            f"  -> Misses: {res['deadline_misses']} | "
                            f"P99: {res['p99_latency_s']:.2f}s | "
                            f"Cost: {res['worker_seconds']:.1f}ws | "
                            f"Flaps: {res['scaling_deltas']:.0f}"
                        )

    # Save summary artifacts
    if results:
        df = pd.DataFrame(results)
        csv_path = out_base / "summary.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved summary CSV to: {csv_path}")

        manifest = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_runs": len(results),
            "delays": delays,
            "controllers": controllers,
            "regimes": regimes,
            "seeds": seeds,
            "results": results,
        }
        manifest_path = out_base / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Saved manifest to: {manifest_path}")

        print("\n" + "=" * 80)
        print("REALISM STRESS SUITE RESULTS SUMMARY")
        print("=" * 80)
        summary_table = df.groupby(["regime", "controller", "startup_delay_s"])[
            ["deadline_misses", "p99_latency_s", "worker_seconds", "scaling_deltas"]
        ].mean().reset_index()
        print(summary_table.to_string(index=False))


if __name__ == "__main__":
    main()
