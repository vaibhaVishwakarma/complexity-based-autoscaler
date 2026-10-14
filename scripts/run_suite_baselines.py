"""
scripts/run_suite_baselines.py — Step 5 Comprehensive Baseline Benchmark Execution
================================================================================
Role:
    Executes the 5 canonical baseline autoscalers across all 13 benchmark regimes
    (Suites 1, 2, and 3) under the unified, telemetrically rectified simulation engine.
    Computes verified performance surfaces and serializes the authoritative
    typed BaselineManifest (output/suite_baselines_runs/manifest.json) for downstream
    OpenEvolve evaluators and multi-seed statistical validation.

Controllers Evaluated (5 total):
    1. fixed_capacity: Fixed Peak Provisioning (18 workers)
    2. hpa: Kubernetes Horizontal Pod Autoscaler (queue-ratio autoscaling)
    3. keda: KEDA Queue Autoscaler (queue-target autoscaling)
    4. inferline: InferLine Exact (ACM SoCC '20 Algs 3 & 4 sliding-window envelope)
    5. complexity_blind_predictive: Blind Predictive (EMA without conformal telemetry)

Regimes Evaluated (13 total):
    - Suite 1 (Quiescent & Synthetic Dynamics): flat, spike, burst, ramp, zero_begin, zero_terminal
    - Suite 2 (Complexity Shocks & Compound Stress): shock, recovery, compound_stress, compound_relief, decoupled_opposing, storm
    - Suite 3 (Production Macrobenchmark): azure (2-hour diurnal replay, rate_scale_factor=0.08)

Inputs:
    - configs/suites/*.yaml (Regime specifications)

Outputs:
    - output/suite_baselines_runs/<regime>/<controller>/ (Raw simulation run logs)
    - output/suite_baselines_runs/suite_baselines_summary.csv (Aggregated summary table)
    - output/suite_baselines_runs/manifest.json (Pydantic-validated authoritative manifest)

AGENTS.md Compliance:
    Rule #1 — Standardized script in scripts/run_suite_baselines.py.
    Rule #2 — Decoupled Linkage; outputs authoritative manifest with typed schema.
    Rule #3 — Strictly module-executable via ./.venv/bin/python -m scripts.run_suite_baselines.
    Rule #4 — Self-documenting structure and inline comments.
    Rule #5 — Grounded in existing libraries and continuum_bench engine.
"""

from __future__ import annotations

import datetime
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from contracts.baselines import (
    BaselineAggregateMetrics,
    BaselineManifest,
    BaselineRunResult,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_suite_baselines")

# Anchor root dynamically from script location (AGENTS.md Rule #3 zero path resolution hacks)
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
OUTPUT_DIR = WORKSPACE_ROOT / "output" / "suite_baselines_runs"
PYTHON_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "python"

CONTROLLERS = [
    ("fixed_capacity", "Fixed Capacity"),
    ("hpa", "Kubernetes HPA"),
    ("keda", "KEDA Queue"),
    ("inferline", "InferLine Exact"),
    ("complexity_blind_predictive", "Blind Predictive"),
]

REGIMES = [
    # Suite 1
    "suite1_flat",
    "suite1_spike",
    "suite1_burst",
    "suite1_ramp",
    "suite1_zero_begin",
    "suite1_zero_terminal",
    # Suite 2
    "suite2_shock",
    "suite2_recovery",
    "suite2_compound_stress",
    "suite2_compound_relief",
    "suite2_decoupled_opposing",
    "suite2_storm",
    # Suite 3
    "suite3_azure",
]


def run_single(regime: str, ctrl_key: str, ctrl_name: str, seed: int = 42) -> BaselineRunResult:
    """Execute a single simulation run and parse its summary.json output."""
    cfg_path = SUITES_DIR / f"{regime}.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing config: {cfg_path}")

    out_dir = OUTPUT_DIR / regime / ctrl_key
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(PYTHON_BIN),
        "-m", "continuum_bench.cli", "run",
        "--config", str(cfg_path),
        "--controller", ctrl_key,
        "--seed", str(seed),
        "--out", str(out_dir),
    ]

    start_t = time.time()
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
    elapsed = time.time() - start_t

    if res.returncode != 0:
        logger.error(f"FAILED: {regime} - {ctrl_key} in {elapsed:.1f}s\n{res.stderr}")
        return BaselineRunResult(
            regime=regime,
            controller=ctrl_name,
            key=ctrl_key,
            status="FAILED",
            completed=0,
            pending=0,
            mean_workers=0.0,
            worker_seconds=0.0,
            mean_latency=0.0,
            p95_latency=0.0,
            p99_latency=0.0,
            queue_wait_mean=0.0,
            scaling_deltas=0.0,
            deadline_misses=0,
            elapsed_s=round(elapsed, 2),
        )

    run_dirs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
    if not run_dirs:
        raise RuntimeError(f"No run directory generated in {out_dir}")

    summary_file = run_dirs[-1] / "summary.json"
    with open(summary_file, "r", encoding="utf-8") as f:
        summary = json.load(f)

    lat = summary.get("latency_s", {})
    cost = summary.get("cost", {})
    qos = summary.get("qos", {})
    rel = summary.get("reliability", {})
    stab = summary.get("stability", {})
    delay = summary.get("delay_breakdown_s", {})

    return BaselineRunResult(
        regime=regime,
        controller=ctrl_name,
        key=ctrl_key,
        status="SUCCESS",
        completed=int(rel.get("completed_tasks", 0)),
        pending=int(rel.get("pending_tasks", 0)),
        mean_workers=float(cost.get("mean_active_workers", 0.0)),
        worker_seconds=float(cost.get("total_provisioned_worker_seconds", 0.0)),
        mean_latency=float(lat.get("mean", 0.0)),
        p95_latency=float(lat.get("p95", 0.0)),
        p99_latency=float(lat.get("p99", 0.0)),
        queue_wait_mean=float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
        scaling_deltas=float(stab.get("scaling_delta_abs_total", 0.0)),
        deadline_misses=int(qos.get("deadline_miss_count", 0)),
        elapsed_s=round(elapsed, 2),
    )


def main() -> None:
    """Execute all 65 baseline runs and compile the authoritative manifest."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results: List[BaselineRunResult] = []

    total_runs = len(REGIMES) * len(CONTROLLERS)
    logger.info(
        f"Starting Step 5 Baseline Benchmark: {len(REGIMES)} regimes x {len(CONTROLLERS)} controllers = {total_runs} runs."
    )
    from concurrent.futures import ThreadPoolExecutor, as_completed

    tasks = []
    for regime in REGIMES:
        for ctrl_key, ctrl_name in CONTROLLERS:
            tasks.append((regime, ctrl_key, ctrl_name))

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(run_single, reg, c_key, c_name, 42): (reg, c_key, c_name)
            for reg, c_key, c_name in tasks
        }
        for future in as_completed(future_map):
            reg, c_key, c_name = future_map[future]
            try:
                result = future.result()
                all_results.append(result)
                logger.info(
                    f"[{len(all_results)}/{total_runs}] Completed {c_name} on {reg} -> {result.status} | "
                    f"Workers: {result.mean_workers:.2f} | Cost: {result.worker_seconds:.0f} ws | "
                    f"Misses: {result.deadline_misses} | Flap: {result.scaling_deltas:.0f} | Time: {result.elapsed_s:.1f}s"
                )
            except Exception as exc:
                logger.error(f"Execution error on {reg} - {c_name}: {exc}")


    # Convert results to DataFrame and save CSV summary
    records = [r.model_dump() for r in all_results]
    df = pd.DataFrame(records)
    csv_path = OUTPUT_DIR / "suite_baselines_summary.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved tabular summary to {csv_path}")

    # Compute aggregate baseline reference costs
    fixed_ws = sum(r.worker_seconds for r in all_results if r.key == "fixed_capacity" and r.status == "SUCCESS")
    inferline_ws = sum(r.worker_seconds for r in all_results if r.key == "inferline" and r.status == "SUCCESS")
    hpa_ws = sum(r.worker_seconds for r in all_results if r.key == "hpa" and r.status == "SUCCESS")
    keda_ws = sum(r.worker_seconds for r in all_results if r.key == "keda" and r.status == "SUCCESS")
    success_count = sum(1 for r in all_results if r.status == "SUCCESS")

    aggregates = BaselineAggregateMetrics(
        fixed_capacity_worker_seconds=fixed_ws,
        inferline_canonical_cost_ws=inferline_ws,
        hpa_canonical_cost_ws=hpa_ws,
        keda_canonical_cost_ws=keda_ws,
        total_runs=total_runs,
        successful_runs=success_count,
    )

    manifest = BaselineManifest(
        manifest_version="1.0.0",
        generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        seed=42,
        controllers=[c[0] for c in CONTROLLERS],
        regimes=REGIMES,
        aggregates=aggregates,
        runs=all_results,
    )

    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)

    logger.info(f"Successfully generated authoritative baseline manifest at {manifest_path}")
    logger.info(f"Baseline Aggregate Costs across 13 Regimes:")
    logger.info(f"  Fixed Capacity Peak: {fixed_ws:.1f} ws")
    logger.info(f"  InferLine Exact:    {inferline_ws:.1f} ws")
    logger.info(f"  Kubernetes HPA:     {hpa_ws:.1f} ws")
    logger.info(f"  KEDA Queue:         {keda_ws:.1f} ws")


if __name__ == "__main__":
    main()
