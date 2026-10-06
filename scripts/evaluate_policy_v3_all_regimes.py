"""
evaluate_policy_v3_all_regimes.py — Regime-by-Regime Verification of Evolved Policy v3

Role:
    Executes the Step 7 v3 Champion policy (output/evolved_policy_v3.py) across all 13
    authoritative ContinuumBench regimes with seed=42, extracting per-regime QoS, cost,
    latency, and stability telemetry, and cross-comparing against Fixed Capacity and InferLine.

AGENTS.md Compliance:
    Rule #1 — Self-contained, dedicated evaluation script.
    Rule #2 — Reads baseline data dynamically from output/suite_baselines_runs/suite_baselines_summary.csv.
    Rule #3 — Runs exclusively in ./.venv/bin/python.
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_v3_regimes")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv" / "bin" / "python"
CANDIDATE_PATH = WORKSPACE_ROOT / "output" / "evolved_policy_v3.py"
OUT_BASE = WORKSPACE_ROOT / "output" / "eval_v3_regimes"
BASELINES_CSV = WORKSPACE_ROOT / "output" / "suite_baselines_runs" / "suite_baselines_summary.csv"

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

REGIME_DESCRIPTIONS = {
    "suite1_flat": "Steady baseline Poisson traffic (60 RPS)",
    "suite1_spike": "Sudden 3x traffic spike (60 -> 180 RPS)",
    "suite1_burst": "Aggressive short-pulse burst (180 RPS, 5s duration)",
    "suite1_ramp": "Continuous gradual load ramp (20 -> 180 RPS)",
    "suite1_zero_begin": "Cold-start ramp from zero ingress (0 -> 100 RPS)",
    "suite1_zero_terminal": "Abrupt traffic drop to zero (120 -> 0 RPS)",
    "suite2_shock": "Sudden semantic triage collapse (p_fast drops 0.90 -> 0.15)",
    "suite2_recovery": "Semantic triage recovery under heavy load",
    "suite2_compound_stress": "Simultaneous traffic spike + triage drop (worst-case stress)",
    "suite2_compound_relief": "Simultaneous traffic drop + triage recovery",
    "suite2_decoupled_opposing": "Decoupled opposing signals (ingress drops but cloud RPS surges)",
    "suite2_storm": "Continuous oscillating triage shifts (dynamic edge uncertainty)",
    "suite3_azure": "Real-world Azure Functions 2019 production invocation trace",
}


def load_baselines():
    if not BASELINES_CSV.exists():
        logger.warning(f"Baselines CSV not found at {BASELINES_CSV}")
        return {}, {}
    df = pd.read_csv(BASELINES_CSV)
    fixed = df[df["key"] == "fixed_capacity"].set_index("regime").to_dict(orient="index")
    inferline = df[df["key"] == "inferline"].set_index("regime").to_dict(orient="index")
    return fixed, inferline


def run_regime(regime: str):
    cfg_path = WORKSPACE_ROOT / "configs" / "suites" / f"{regime}.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")

    out_dir = OUT_BASE / regime
    out_dir.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "EVOLUTION_CANDIDATE_PATH": str(CANDIDATE_PATH),
        "PYTHONPATH": f"{WORKSPACE_ROOT}/src:{os.environ.get('PYTHONPATH', '')}",
    }

    cmd = [
        str(VENV_PYTHON),
        "-m", "continuum_bench.cli", "run",
        "--config", str(cfg_path),
        "--controller", "evolved_conformal",
        "--seed", "42",
        "--out", str(out_dir),
    ]

    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, env=env)
    elapsed = time.time() - t0

    if res.returncode != 0:
        logger.error(f"Regime {regime} failed:\n{res.stderr}")
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
        "description": REGIME_DESCRIPTIONS.get(regime, ""),
        "completed": int(qos.get("slo_eligible_count", 0)),
        "deadline_misses": int(qos.get("deadline_miss_count", 0)),
        "worker_seconds": float(cost.get("total_provisioned_worker_seconds", 0.0)),
        "mean_workers": float(cost.get("mean_active_workers", 0.0)),
        "mean_latency_s": float(lat.get("mean", 0.0)),
        "p95_latency_s": float(lat.get("p95", 0.0)),
        "p99_latency_s": float(lat.get("p99", 0.0)),
        "queue_wait_mean_s": float(delay.get("queue_wait_s", {}).get("mean", 0.0)),
        "scaling_deltas": float(stab.get("scaling_delta_abs_total", 0.0)),
        "elapsed_s": elapsed,
    }


def main():
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    fixed_base, inferline_base = load_baselines()

    results = []
    print("=" * 80)
    print("STARTING REGIME-BY-REGIME EVALUATION OF EVOLVED POLICY V3")
    print(f"Candidate: {CANDIDATE_PATH}")
    print(f"Total Regimes: {len(ALL_REGIMES)}")
    print("=" * 80)

    for i, regime in enumerate(ALL_REGIMES, 1):
        print(f"[{i:02d}/{len(ALL_REGIMES):02d}] Evaluating {regime}...")
        r = run_regime(regime)
        if r is None:
            print(f"  -> FAILED: {regime}")
            continue

        # Baseline comparisons
        f_cost = fixed_base.get(regime, {}).get("worker_seconds", 2146.0)
        f_miss = fixed_base.get(regime, {}).get("deadline_misses", 0)

        inf_cost = inferline_base.get(regime, {}).get("worker_seconds", 1097.0)
        inf_miss = inferline_base.get(regime, {}).get("deadline_misses", 0)
        inf_p99 = inferline_base.get(regime, {}).get("p99_latency", 6.0)
        inf_deltas = inferline_base.get(regime, {}).get("scaling_deltas", 65.0)

        savings_vs_fixed = ((f_cost - r["worker_seconds"]) / f_cost) * 100.0 if f_cost > 0 else 0.0
        savings_vs_inferline = ((inf_cost - r["worker_seconds"]) / inf_cost) * 100.0 if inf_cost > 0 else 0.0

        r["fixed_worker_seconds"] = f_cost
        r["savings_vs_fixed_%"] = savings_vs_fixed
        r["inferline_worker_seconds"] = inf_cost
        r["inferline_misses"] = inf_miss
        r["inferline_p99_s"] = inf_p99
        r["inferline_deltas"] = inf_deltas
        r["savings_vs_inferline_%"] = savings_vs_inferline
        r["ws_saved_vs_inferline"] = inf_cost - r["worker_seconds"]

        results.append(r)
        print(
            f"  -> Completed: {r['completed']:,} reqs | Misses: {r['deadline_misses']} | "
            f"Cost: {r['worker_seconds']:.1f} ws (Save: {savings_vs_fixed:.1f}% vs Fixed, {savings_vs_inferline:+.1f}% vs InferLine) | "
            f"P99: {r['p99_latency_s']:.2f}s | Deltas: {r['scaling_deltas']:.0f}"
        )

    # Save to CSV and JSON
    df = pd.DataFrame(results)
    csv_path = OUT_BASE / "regime_wise_report_v3.csv"
    df.to_csv(csv_path, index=False)
    json_path = OUT_BASE / "regime_wise_report_v3.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("REGIME-BY-REGIME EVALUATION COMPLETE")
    print(f"Results saved to:")
    print(f"  - {csv_path}")
    print(f"  - {json_path}")
    print("=" * 80)

    # Compute overall summary
    tot_reqs = sum(r["completed"] for r in results)
    tot_miss = sum(r["deadline_misses"] for r in results)
    tot_ws = sum(r["worker_seconds"] for r in results)
    tot_fixed_ws = sum(r["fixed_worker_seconds"] for r in results)
    tot_inf_ws = sum(r["inferline_worker_seconds"] for r in results)
    tot_inf_miss = sum(r["inferline_misses"] for r in results)
    tot_deltas = sum(r["scaling_deltas"] for r in results)
    tot_inf_deltas = sum(r["inferline_deltas"] for r in results)
    max_p99 = max(r["p99_latency_s"] for r in results)

    overall_savings_fixed = ((tot_fixed_ws - tot_ws) / tot_fixed_ws) * 100.0
    overall_savings_inf = ((tot_inf_ws - tot_ws) / tot_inf_ws) * 100.0

    print("\nOVERALL BENCHMARK TOTALS:")
    print(f"  Total Requests:       {tot_reqs:,}")
    print(f"  Total Misses:         {tot_miss} (InferLine had {tot_inf_miss})")
    print(f"  Total Worker-Seconds: {tot_ws:.1f} ws (Fixed: {tot_fixed_ws:.1f} ws, InferLine: {tot_inf_ws:.1f} ws)")
    print(f"  Cost Savings vs Fixed: {overall_savings_fixed:.2f}%")
    print(f"  Cost Savings vs InferLine: {overall_savings_inf:.2f}% (Saved {tot_inf_ws - tot_ws:.1f} ws)")
    print(f"  Max P99 Latency:      {max_p99:.2f}s")
    print(f"  Total Scaling Deltas: {tot_deltas:.0f} (InferLine had {tot_inf_deltas:.0f})")


if __name__ == "__main__":
    main()
