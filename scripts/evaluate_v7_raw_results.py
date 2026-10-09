#!/usr/bin/env python3
"""
scripts/evaluate_v7_raw_results.py — Authoritative Local Benchmark & Comparative Evaluator for v7
================================================================================================
Role:
    Performs definitive local evaluation of raw output data from OpenEvolve v7.
    Evaluates discovered candidate policies against the complete Step 8.5 physical realism ladder:
        T_boot in [0.5s, 1.0s, 5.0s, 15.0s, 50.0s, 100.0s, 150.0s, 200.0s, 250.0s, 300.0s]
    across the Stress Triad (suite1_spike, suite2_shock, suite3_azure) and compiles head-to-head
    comparisons against Policy v3 Champion, InferLine (ACM SoCC '20), Kubernetes HPA, and KEDA.

Inputs:
    - Candidate policy: output/evolved_policy_v7.py (or specified via --candidate)
    - Baseline manifest: output/realism_stress_results/manifest.json (Step 8.5 authoritative baselines)

Outputs:
    - output/eval_v7_results/summary_v7_vs_baselines.csv
    - output/eval_v7_results/EVALUATION_REPORT_V7.md
    - output/eval_v7_results/manifest.json

Governance:
    AGENTS.md Rule #1 — Dedicated versioned evaluation script.
    AGENTS.md Rule #2 — Zero hardcoding; dynamic baseline loading.
    AGENTS.md Rule #3 — Dedicated workspace virtual environment at ./.venv/bin/python.
    AGENTS.md Rule #4 — Self-documenting structure.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [EVAL v7] %(message)s")
logger = logging.getLogger("evaluate_v7_raw_results")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PYTHON_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "python"
DEFAULT_CANDIDATE = WORKSPACE_ROOT / "output" / "evolved_policy_v7.py"
BASELINE_MANIFEST = WORKSPACE_ROOT / "output" / "realism_stress_results" / "manifest.json"
OUT_BASE = WORKSPACE_ROOT / "output" / "eval_v7_results"

FULL_DELAY_LADDER = [0.5, 1.0, 5.0, 15.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0]
STRESS_TRIAD = ["suite1_spike", "suite2_shock", "suite3_azure"]


def run_single_simulation(
    regime: str,
    candidate_path: Path,
    startup_delay_s: float,
    seed: int,
    out_dir: Path,
) -> Optional[Dict[str, Any]]:
    """Executes a single simulation for the v7 candidate under the specified startup delay."""
    cfg_path = WORKSPACE_ROOT / "configs" / "suites" / f"{regime}.yaml"
    if not cfg_path.exists():
        logger.error(f"Config not found: {cfg_path}")
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

    out_dir.mkdir(parents=True, exist_ok=True)
    run_temp_cfg = out_dir / f"config_delay_{startup_delay_s:.1f}s.yaml"
    with open(run_temp_cfg, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    # Idempotent resume check
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
                    return {
                        "regime": regime,
                        "controller": "evolved_conformal_v7",
                        "startup_delay_s": float(startup_delay_s),
                        "seed": seed,
                        "completed": int(qos.get("slo_eligible_count", 0)),
                        "deadline_misses": int(max(qos.get("slo_violation_count", 0), qos.get("deadline_miss_count", 0))),
                        "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
                        "mean_active_workers": float(cost.get("mean_active_workers", 0.0)),
                        "p99_latency_s": float(lat.get("p99", 0.0)),
                        "p95_latency_s": float(lat.get("p95", 0.0)),
                        "mean_latency_s": float(lat.get("mean", 0.0)),
                        "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
                    }
            except Exception:
                pass

    env = {
        **os.environ,
        "EVOLUTION_CANDIDATE_PATH": str(candidate_path),
        "PYTHONPATH": f"{WORKSPACE_ROOT}/src:{os.environ.get('PYTHONPATH', '')}",
    }

    cmd = [
        str(PYTHON_BIN),
        "-m", "continuum_bench.cli", "run",
        "--config", str(run_temp_cfg),
        "--controller", "evolved_conformal",
        "--seed", str(seed),
        "--out", str(out_dir),
    ]

    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, env=env)
    if res.returncode != 0:
        logger.error(f"Run failed for v7 on {regime} (delay={startup_delay_s}s):\n{res.stderr[:300]}")
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

    return {
        "regime": regime,
        "controller": "evolved_conformal_v7",
        "startup_delay_s": float(startup_delay_s),
        "seed": seed,
        "completed": int(qos.get("slo_eligible_count", 0)),
        "deadline_misses": int(max(qos.get("slo_violation_count", 0), qos.get("deadline_miss_count", 0))),
        "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
        "mean_active_workers": float(cost.get("mean_active_workers", 0.0)),
        "p99_latency_s": float(lat.get("p99", 0.0)),
        "p95_latency_s": float(lat.get("p95", 0.0)),
        "mean_latency_s": float(lat.get("mean", 0.0)),
        "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
    }


def generate_comparative_markdown(
    df_all: pd.DataFrame,
    report_file: Path,
    candidate_file: Path,
):
    """Generates a publication-grade markdown evaluation report."""
    report_file.parent.mkdir(parents=True, exist_ok=True)

    summary_table = df_all.groupby(["regime", "controller", "startup_delay_s"])[
        ["deadline_misses", "p99_latency_s", "worker_seconds", "scaling_deltas"]
    ].mean().reset_index()

    v7_data = df_all[df_all["controller"] == "evolved_conformal_v7"]
    total_v7_misses = v7_data["deadline_misses"].sum()
    mean_v7_p99 = v7_data["p99_latency_s"].mean()
    total_v7_cost = v7_data["worker_seconds"].sum()
    total_v7_flaps = v7_data["scaling_deltas"].sum()

    md = f"""# OpenEvolve v7 Empirical Evaluation Report
**Comprehensive Realism Stress Evaluation Across Physical Delay Ladder ($T_{{\\text{{boot}}}} \\in [0.5\\text{{s}} \\to 300\\text{{s}}]$)**

---

## 1. Executive Summary

- **Evaluated Policy Artifact**: [`{candidate_file.name}`]({candidate_file.resolve()})
- **Timestamp**: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}
- **Total v7 Deadline Misses**: **{total_v7_misses:,.0f}** across all tested delay conditions
- **Mean P99 Tail Latency**: **{mean_v7_p99:.2f}s** (SLA Budget: $15.0\\text{{s}}$)
- **Total Worker-Seconds**: **{total_v7_cost:,.1f} ws**
- **Total Actuation Churn**: **{total_v7_flaps:,.0f} deltas**

---

## 2. Regime-by-Regime Benchmark Results

"""
    for regime in STRESS_TRIAD:
        reg_df = summary_table[summary_table["regime"] == regime]
        if reg_df.empty:
            continue
        md += f"### Regime: `{regime}`\n\n"
        md += "| Controller | Startup Delay (s) | Deadline Misses | P99 Latency (s) | Worker-Seconds | Flaps (Deltas) |\n"
        md += "|:---|:---:|:---:|:---:|:---:|:---:|\n"
        for _, row in reg_df.iterrows():
            c_name = f"**{row['controller']}**" if "v7" in str(row["controller"]) else f"*{row['controller']}*"
            md += (
                f"| {c_name} | {row['startup_delay_s']:5.1f} | "
                f"{row['deadline_misses']:,.0f} | {row['p99_latency_s']:.2f} | "
                f"{row['worker_seconds']:,.1f} | {row['scaling_deltas']:,.0f} |\n"
            )
        md += "\n---\n\n"

    md += """## 3. Provenance & Reproducibility

- **Evaluation Harness**: `scripts/evaluate_v7_raw_results.py`
- **Baseline Manifest**: `output/realism_stress_results/manifest.json`
- **Output CSV**: `output/eval_v7_results/summary_v7_vs_baselines.csv`
"""

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(md)

    logger.info(f"Report written to: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate OpenEvolve v7 Raw Results across full Step 8.5 Ladder")
    parser.add_argument("--candidate", type=str, default=str(DEFAULT_CANDIDATE), help="Path to v7 candidate policy file")
    parser.add_argument("--smoke", action="store_true", help="Fast smoke evaluation on 3 delays (0.5s, 5.0s, 50.0s)")
    parser.add_argument("--delays", type=float, nargs="+", default=None, help="Explicit list of startup delays (s)")
    parser.add_argument("--regimes", type=str, nargs="+", default=None, help="Explicit list of stress regimes")
    parser.add_argument("--out", type=str, default=str(OUT_BASE), help="Output directory")
    args = parser.parse_args()

    cand_path = Path(args.candidate)
    if not cand_path.exists():
        logger.error(f"Candidate file not found: {cand_path}")
        sys.exit(1)

    out_base = Path(args.out)
    out_base.mkdir(parents=True, exist_ok=True)
    runs_dir = out_base / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        delays = [0.5, 5.0, 50.0]
        regimes = ["suite1_spike"]
        logger.info("Executing SMOKE MODE (fast test)")
    else:
        delays = args.delays if args.delays is not None else FULL_DELAY_LADDER
        regimes = args.regimes if args.regimes is not None else STRESS_TRIAD

    logger.info("=" * 80)
    logger.info("STARTING LOCAL EVALUATION OF RAW v7 CANDIDATE")
    logger.info(f"Candidate: {cand_path}")
    logger.info(f"Delays:    {delays}")
    logger.info(f"Regimes:   {regimes}")
    logger.info(f"Output:    {out_base}")
    logger.info("=" * 80)

    results: List[Dict[str, Any]] = []
    total = len(regimes) * len(delays)
    idx = 0

    for regime in regimes:
        for delay in delays:
            idx += 1
            logger.info(f"[{idx:02d}/{total:02d}] Evaluating v7 on {regime} @ {delay:5.1f}s delay...")
            run_out = runs_dir / f"{regime}_v7_d{int(delay*10):04d}"
            res = run_single_simulation(
                regime=regime,
                candidate_path=cand_path,
                startup_delay_s=delay,
                seed=42,
                out_dir=run_out,
            )
            if res:
                results.append(res)
                logger.info(
                    f"  -> Misses: {res['deadline_misses']} | P99: {res['p99_latency_s']:.2f}s | Cost: {res['worker_seconds']:.1f} ws"
                )

    if not results:
        logger.error("No successful simulation runs.")
        sys.exit(1)

    df_v7 = pd.DataFrame(results)

    # Load baseline runs from Step 8.5 for comparison if available
    baseline_records: List[Dict[str, Any]] = []
    if BASELINE_MANIFEST.exists():
        try:
            with open(BASELINE_MANIFEST, "r", encoding="utf-8") as f:
                b_manifest = json.load(f)
            baseline_records = b_manifest.get("results", [])
            logger.info(f"Loaded {len(baseline_records)} baseline records from {BASELINE_MANIFEST}")
        except Exception as e:
            logger.warning(f"Could not load baseline manifest: {e}")

    if baseline_records:
        df_base = pd.DataFrame(baseline_records)
        df_all = pd.concat([df_base, df_v7], ignore_index=True)
    else:
        df_all = df_v7

    csv_path = out_base / "summary_v7_vs_baselines.csv"
    df_all.to_csv(csv_path, index=False)
    logger.info(f"Saved consolidated CSV to: {csv_path}")

    report_path = out_base / "EVALUATION_REPORT_V7.md"
    generate_comparative_markdown(df_all, report_path, cand_path)

    print("\n" + "=" * 80)
    print("v7 REALISM EVALUATION COMPLETE")
    print(f"Report: {report_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
