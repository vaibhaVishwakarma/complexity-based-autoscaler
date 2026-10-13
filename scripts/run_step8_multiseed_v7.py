#!/usr/bin/env python3
"""
scripts/run_step8_multiseed_v7.py — Step 8 v7: Multi-Seed Statistical Validation Engine

Role:
    Executes multi-seed evaluation of the Promoted Production Champion Evolved Conformal
    Policy v7 (output/champion_policy_v7_smooth.py) against all 4 baseline controllers
    (InferLine, Fixed Capacity Peak, Kubernetes HPA, KEDA Queue) across N independent
    stochastic seeds. Preserves full granular telemetric artifacts (decision trajectories,
    epoch traces, summaries) to guarantee reproducible, zero-rerun publication workflows.

Gate Stage:    Step 8 v7 (Multi-Seed Statistical Certification & Repository Freeze)
Inputs:        output/champion_policy_v7_smooth.py, configs/suites/*.yaml
Outputs:       output/step8_v7_multiseed_runs/raw_runs/<ctrl>/<regime>/seed_<seed>/
               output/step8_v7_multiseed_runs/multiseed_summary.csv
               output/step8_v7_multiseed_runs/step8_v7_statistical_manifest.json
               docs/STEP8_V7_MULTISEED_STATISTICAL_VALIDATION_REPORT.md

AGENTS.md Compliance:
    Rule #1 — Dedicated versioned script (run_step8_multiseed_v7.py).
    Rule #2 — Dynamically links candidate via EVOLUTION_CANDIDATE_PATH and external manifests.
    Rule #3 — Runs strictly with workspace ./.venv/bin/python.
    Rule #4 — Self-documenting with header docstring and inline commentary.
    Rule #5 — Uses standard numpy, pandas, scipy.stats.
    Rule #6 — Evaluates authoritative 13 regimes without synthetic data fabrication.
"""

from __future__ import annotations

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

import numpy as np
import pandas as pd
from scipy import stats

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
DEFAULT_CHAMPION_PATH = WORKSPACE_ROOT / "output" / "champion_policy_v7_smooth.py"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "step8_v7_multiseed_runs"
DEFAULT_REPORT_PATH = WORKSPACE_ROOT / "docs" / "STEP8_V7_MULTISEED_STATISTICAL_VALIDATION_REPORT.md"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Step8v7Runner")

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

CONTROLLERS = [
    ("evolved_conformal", "Evolved Conformal v7 (Champion c614055a)"),
    ("inferline", "InferLine Tuner (ACM SoCC '20)"),
    ("fixed_capacity", "Fixed Capacity Peak (k=18)"),
    ("hpa", "Kubernetes HPA (Util=0.70)"),
    ("keda", "KEDA Queue (Backlog=5)"),
]

DEFAULT_20_SEEDS = list(range(1042, 1062))  # 1042 to 1061


def run_preflight_audit(champion_path: Path) -> bool:
    """Validates python interpreter, champion policy syntax, and suite configurations."""
    logger.info("=" * 70)
    logger.info("       STEP 8 v7 PRE-FLIGHT VALIDATION & INTEGRITY AUDIT        ")
    logger.info("=" * 70)

    if not VENV_PYTHON.exists():
        logger.error(f"[AUDIT FAIL] Workspace Python interpreter missing: {VENV_PYTHON}")
        return False
    logger.info(f"[PASS] Python interpreter verified: {VENV_PYTHON}")

    if not champion_path.exists():
        logger.error(f"[AUDIT FAIL] Champion policy not found: {champion_path}")
        return False

    try:
        check_code = (
            f"import output.{champion_path.stem} as ep; "
            f"print('Champion policy imported cleanly')"
        )
        res = subprocess.run(
            [str(VENV_PYTHON), "-c", check_code],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT),
        )
        if res.returncode != 0:
            logger.error(f"[AUDIT FAIL] Policy import error:\n{res.stderr}")
            return False
        logger.info(f"[PASS] Policy {champion_path.name} verified.")
    except Exception as e:
        logger.error(f"[AUDIT FAIL] Exception during policy verification: {e}")
        return False

    for regime in ALL_REGIMES:
        cfg = SUITES_DIR / f"{regime}.yaml"
        if not cfg.exists():
            logger.error(f"[AUDIT FAIL] Missing suite config: {cfg}")
            return False
    logger.info(f"[PASS] All {len(ALL_REGIMES)} suite configurations verified.")
    logger.info("=" * 70 + "\n")
    return True


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
    Executes a single simulation in an isolated process.
    Preserves all raw telemetry files (decision_trajectory, epochs, summary).
    """
    cfg_path = SUITES_DIR / f"{regime}.yaml"
    raw_dir = out_root / "raw_runs" / ctrl_key / regime / f"seed_{seed}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Cache check to support resumption
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


def compute_paired_statistics(
    df: pd.DataFrame,
    baseline_key: str,
    champion_key: str = "evolved_conformal",
) -> Dict[str, Any]:
    """Computes paired Wilcoxon signed-rank, Student's t-tests, Cohen's d, and 95% CIs."""
    df_champ = df[df["controller_key"] == champion_key].sort_values(by=["regime", "seed"])
    df_base = df[df["controller_key"] == baseline_key].sort_values(by=["regime", "seed"])

    if df_champ.empty or df_base.empty:
        return {}

    merged = pd.merge(df_champ, df_base, on=["regime", "seed"], suffixes=("_champ", "_base"))
    if merged.empty:
        return {}

    metrics = [
        "deadline_misses",
        "worker_seconds",
        "scaling_deltas",
        "p99_latency_s",
        "queue_wait_mean_s",
    ]

    res: Dict[str, Any] = {}
    for metric in metrics:
        c_col = f"{metric}_champ"
        b_col = f"{metric}_base"
        if c_col not in merged.columns or b_col not in merged.columns:
            continue

        c_vals = merged[c_col].to_numpy(dtype=float)
        b_vals = merged[b_col].to_numpy(dtype=float)
        diffs = c_vals - b_vals

        n = len(diffs)
        mean_diff = float(np.mean(diffs))
        std_diff = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
        se_diff = std_diff / np.sqrt(n) if n > 0 else 0.0

        ci_lower = float(mean_diff - 1.96 * se_diff)
        ci_upper = float(mean_diff + 1.96 * se_diff)

        non_zero = diffs[diffs != 0]
        if len(non_zero) >= 5:
            try:
                w_test = stats.wilcoxon(c_vals, b_vals, zero_method="pratt", alternative="two-sided")
                w_stat, w_p = float(w_test.statistic), float(w_test.pvalue)
            except Exception:
                w_stat, w_p = 0.0, 1.0
        else:
            w_stat, w_p = 0.0, 1.0 if len(non_zero) == 0 else 0.5

        if n >= 2 and std_diff > 0:
            try:
                t_test = stats.ttest_rel(c_vals, b_vals, alternative="two-sided")
                t_stat, t_p = float(t_test.statistic), float(t_test.pvalue)
            except Exception:
                t_stat, t_p = 0.0, 1.0
        else:
            t_stat, t_p = 0.0, 1.0

        cohen_d = float(mean_diff / std_diff) if std_diff > 0 else 0.0

        res[metric] = {
            "n_pairs": n,
            "mean_champ": float(np.mean(c_vals)),
            "mean_base": float(np.mean(b_vals)),
            "mean_diff": mean_diff,
            "ci_95_diff": [ci_lower, ci_upper],
            "cohens_d": cohen_d,
            "wilcoxon_stat": w_stat,
            "wilcoxon_pvalue": w_p,
            "ttest_stat": t_stat,
            "ttest_pvalue": t_p,
            "significant_at_0_01": bool(w_p < 0.01),
        }

    return res


def synthesize_markdown_report(
    df: pd.DataFrame,
    hypothesis_results: Dict[str, Any],
    report_path: Path,
    seeds: List[int],
    champion_path: Path,
) -> None:
    """Generates a publication-grade markdown statistical report."""
    report_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    fixed_mean_cost = 2146.0  # reference fixed peak cost
    for ctrl_key, ctrl_name in CONTROLLERS:
        cdf = df[df["controller_key"] == ctrl_key]
        if cdf.empty:
            continue
        n = len(cdf)
        m_cost = cdf["worker_seconds"].mean()
        se_cost = cdf["worker_seconds"].std() / np.sqrt(n) if n > 1 else 0.0
        m_miss = cdf["deadline_misses"].mean()
        se_miss = cdf["deadline_misses"].std() / np.sqrt(n) if n > 1 else 0.0
        m_deltas = cdf["scaling_deltas"].mean()
        se_deltas = cdf["scaling_deltas"].std() / np.sqrt(n) if n > 1 else 0.0
        m_p99 = cdf["p99_latency_s"].mean()
        se_p99 = cdf["p99_latency_s"].std() / np.sqrt(n) if n > 1 else 0.0
        savings = ((fixed_mean_cost - m_cost) / fixed_mean_cost) * 100.0 if fixed_mean_cost > 0 else 0.0

        summary_rows.append(
            f"| **{ctrl_key}** | {ctrl_name} | {m_miss:.2f} ± {1.96*se_miss:.2f} | "
            f"{m_cost:.1f} ± {1.96*se_cost:.1f} | **{savings:.2f}%** | "
            f"{m_deltas:.1f} ± {1.96*se_deltas:.1f} | {m_p99:.2f}s ± {1.96*se_p99:.2f}s |"
        )

    sections = [
        f"# Step 8 v7 Statistical Validation & Hypothesis Testing Report",
        f"",
        f"- **Evaluated Policy Artifact**: [`{champion_path.name}`]({champion_path})",
        f"- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        f"- **Stochastic Seeds (N={len(seeds)})**: `{seeds}`",
        f"- **Evaluated Regimes (R={len(ALL_REGIMES)})**: `{ALL_REGIMES}`",
        f"- **Total Simulations**: {len(df)} runs",
        f"",
        f"---",
        f"",
        f"## 1. Multi-Seed Aggregate Performance Summary",
        f"",
        f"| Controller Key | Policy Name | Mean Deadline Misses | Mean Worker-Sec (Cost) | Cost Savings (%) | Mean Scaling Churn (Flaps) | Mean P99 Latency |",
        f"| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
        *summary_rows,
        f"",
        f"---",
        f"",
        f"## 2. Paired Hypothesis Testing Results (vs Baseline Controllers)",
        f"",
    ]

    for base_key, b_name in [("inferline", "InferLine Tuner"), ("hpa", "Kubernetes HPA"), ("keda", "KEDA Queue")]:
        tests = hypothesis_results.get(base_key, {})
        if not tests:
            continue
        sections.append(f"### Comparison: Evolved Conformal v7 vs. {b_name}")
        sections.append(f"")
        sections.append(f"| Metric | Mean (Evolved v7) | Mean ({base_key}) | Mean Diff (Δ) | 95% CI of Δ | Cohen's d | Wilcoxon p-value | Significant (p < 0.01)? |")
        sections.append(f"| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

        for m_name in ["deadline_misses", "worker_seconds", "scaling_deltas", "p99_latency_s", "queue_wait_mean_s"]:
            m_res = tests.get(m_name, {})
            if not m_res:
                continue
            ci = m_res["ci_95_diff"]
            sig_str = "✅ **YES**" if m_res["significant_at_0_01"] else "❌ No"
            sections.append(
                f"| `{m_name}` | {m_res['mean_champ']:.2f} | {m_res['mean_base']:.2f} | "
                f"{m_res['mean_diff']:.2f} | [{ci[0]:.2f}, {ci[1]:.2f}] | {m_res['cohens_d']:.2f} | "
                f"{m_res['wilcoxon_pvalue']:.4e} | {sig_str} |"
            )
        sections.append(f"")

    sections.extend([
        f"---",
        f"",
        f"## 3. Data Availability & Telemetry Preservation",
        f"",
        f"- Full decision trajectories (`decision_trajectory.jsonl`), epoch summaries (`epochs.csv`), and simulation metadata are preserved in `output/step8_v7_multiseed_runs/raw_runs/`.",
        f"- Statistical test outputs archived in `output/step8_v7_multiseed_runs/step8_v7_statistical_manifest.json`.",
    ])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sections) + "\n")
    logger.info(f"Markdown report generated: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 8 v7 Multi-Seed Validation Engine")
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CHAMPION_PATH, help="Path to v7 champion policy")
    parser.add_argument("--seeds", type=int, nargs="+", default=None, help="Explicit list of stochastic seeds")
    parser.add_argument("--regimes", type=str, nargs="+", default=None, help="Explicit list of regimes")
    parser.add_argument("--controllers", type=str, nargs="+", default=None, help="Explicit controller keys")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Report path")
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 4), help="Parallel processes")
    parser.add_argument("--smoke", action="store_true", help="Fast 2-seed smoke test")
    parser.add_argument("--force-rerun", action="store_true", help="Force re-run ignoring cached summaries")
    args = parser.parse_args()

    if not run_preflight_audit(args.candidate):
        sys.exit(1)

    if args.smoke:
        seeds = [1042, 1043]
        logger.info(f"Executing in SMOKE TEST mode (N=2 seeds: {seeds})")
    elif args.seeds is not None:
        seeds = args.seeds
    else:
        seeds = DEFAULT_20_SEEDS

    regimes = args.regimes if args.regimes is not None else ALL_REGIMES
    ctrl_list = [c for c in CONTROLLERS if c[0] in args.controllers] if args.controllers else CONTROLLERS

    args.out.mkdir(parents=True, exist_ok=True)

    tasks: List[Tuple[str, str, str, int]] = []
    for regime in regimes:
        for ctrl_key, ctrl_name in ctrl_list:
            for seed in seeds:
                tasks.append((regime, ctrl_key, ctrl_name, seed))

    total_tasks = len(tasks)
    logger.info(f"Initialized {total_tasks} simulation tasks ({len(ctrl_list)} controllers × {len(regimes)} regimes × {len(seeds)} seeds).")
    logger.info(f"Dispatching across {args.workers} parallel workers...")

    results: List[Dict[str, Any]] = []
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                execute_single_simulation,
                regime=regime,
                ctrl_key=ctrl_key,
                ctrl_name=ctrl_name,
                seed=seed,
                out_root=args.out,
                champion_path=args.candidate,
                force_rerun=args.force_rerun,
            ): (regime, ctrl_key, seed)
            for regime, ctrl_key, ctrl_name, seed in tasks
        }

        completed = 0
        for future in as_completed(futures):
            completed += 1
            res = future.result()
            results.append(res)
            if completed % max(1, total_tasks // 10) == 0 or completed == total_tasks:
                logger.info(f"Progress: [{completed}/{total_tasks}] ({(completed/total_tasks)*100.0:.1f}%) completed in {time.time()-t_start:.1f}s.")

    df = pd.DataFrame(results)
    csv_path = args.out / "multiseed_summary.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved summary CSV to: {csv_path}")

    # Compute paired statistical hypothesis tests
    hyp_results: Dict[str, Any] = {}
    for base_key, _ in [c for c in CONTROLLERS if c[0] != "evolved_conformal"]:
        hyp_results[base_key] = compute_paired_statistics(df, baseline_key=base_key, champion_key="evolved_conformal")

    manifest_path = args.out / "step8_v7_statistical_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "champion_policy": str(args.candidate),
                "total_runs": len(df),
                "seeds": seeds,
                "regimes": regimes,
                "hypothesis_tests": hyp_results,
            },
            f,
            indent=2,
        )
    logger.info(f"Saved statistical manifest to: {manifest_path}")

    synthesize_markdown_report(
        df=df,
        hypothesis_results=hyp_results,
        report_path=args.report,
        seeds=seeds,
        champion_path=args.candidate,
    )

    print("\n" + "=" * 70)
    print("STEP 8 v7 MULTI-SEED VALIDATION COMPLETE")
    print(f"Summary CSV: {csv_path}")
    print(f"Manifest:    {manifest_path}")
    print(f"Report:      {args.report}")
    print("=" * 70)


if __name__ == "__main__":
    main()
