"""
run_suite_baselines.py — Step 5 Comprehensive Evaluation:
Runs the 5 non-conformal autoscalers across all 13 calibrated suite regimes.

Controllers:
1. fixed_capacity
2. hpa
3. keda
4. inferline
5. complexity_blind_predictive

Suites:
- Suite 1: flat, spike, burst, ramp, zero_begin, zero_terminal
- Suite 2: shock, recovery, compound_stress, compound_relief, decoupled_opposing, storm
- Suite 3: azure
"""

import json
import subprocess
import sys
import time
from pathlib import Path
import pandas as pd

WORKSPACE_ROOT = Path("/home/vaibo/edgecompute")
SUITES_DIR = WORKSPACE_ROOT / "configs" / "suites"
OUTPUT_DIR = WORKSPACE_ROOT / "output" / "suite_baselines_runs"
PYTHON_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "python"

CONTROLLERS = [
    ("fixed_capacity", "Fixed Capacity"),
    ("hpa", "Kubernetes HPA"),
    ("keda", "KEDA Queue"),
    ("inferline", "InferLine Tuner"),
    ("complexity_blind_predictive", "Blind Predictive"),
]

REGIMES = [
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

def run_single(regime: str, ctrl_key: str, ctrl_name: str) -> dict:
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
        "--seed", "42",
        "--out", str(out_dir),
    ]
    
    start_t = time.time()
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
    elapsed = time.time() - start_t
    
    if res.returncode != 0:
        print(f"FAILED: {regime} - {ctrl_key} in {elapsed:.1f}s\n{res.stderr}")
        return {
            "regime": regime,
            "controller": ctrl_name,
            "key": ctrl_key,
            "status": "FAILED",
            "error": res.stderr,
        }
        
    run_dirs = sorted([d for d in out_dir.iterdir() if d.is_dir()])
    if not run_dirs:
        return {"regime": regime, "controller": ctrl_name, "key": ctrl_key, "status": "NO_RUN_DIR"}
        
    summary_file = run_dirs[-1] / "summary.json"
    with open(summary_file) as f:
        summary = json.load(f)
        
    lat = summary.get("latency_s", {})
    cost = summary.get("cost", {})
    qos = summary.get("qos", {})
    rel = summary.get("reliability", {})
    stab = summary.get("stability", {})
    delay = summary.get("delay_breakdown_s", {})
    per_pri = qos.get("per_priority", {})
    
    return {
        "regime": regime,
        "controller": ctrl_name,
        "key": ctrl_key,
        "status": "SUCCESS",
        "completed": rel.get("completed_tasks", 0),
        "pending": rel.get("pending_tasks", 0),
        "fast_path": f"{per_pri.get('high', {}).get('completed', 0)}/{per_pri.get('high', {}).get('generated', 0)}",
        "slow_path": f"{per_pri.get('low', {}).get('completed', 0)}/{per_pri.get('low', {}).get('generated', 0)}",
        "mean_workers": cost.get("mean_active_workers", 0.0),
        "worker_seconds": cost.get("total_provisioned_worker_seconds", 0.0),
        "mean_latency": lat.get("mean", 0.0),
        "p95_latency": lat.get("p95", 0.0),
        "p99_latency": lat.get("p99", 0.0),
        "queue_wait_mean": delay.get("queue_wait_s", {}).get("mean", 0.0),
        "scaling_deltas": stab.get("scaling_delta_abs_total", 0.0),
        "deadline_misses": qos.get("deadline_miss_count", 0),
        "elapsed_s": round(elapsed, 2),
    }

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []
    
    total_runs = len(REGIMES) * len(CONTROLLERS)
    print(f"Starting Step 5 Comprehensive Evaluation: {len(REGIMES)} regimes x {len(CONTROLLERS)} controllers = {total_runs} runs.")
    
    count = 0
    for regime in REGIMES:
        print(f"\n=======================================================")
        print(f"Regime: {regime}")
        print(f"=======================================================")
        for ctrl_key, ctrl_name in CONTROLLERS:
            count += 1
            print(f"[{count}/{total_runs}] Running {ctrl_name} on {regime}...", end="", flush=True)
            res = run_single(regime, ctrl_key, ctrl_name)
            print(f" Done ({res.get('elapsed_s', 0)}s) | Workers: {res.get('mean_workers', 0):.2f}, Cost: {res.get('worker_seconds', 0):.0f}, Misses: {res.get('deadline_misses', 0)}, Flap: {res.get('scaling_deltas', 0):.0f}")
            all_results.append(res)
            
    df = pd.DataFrame(all_results)
    csv_path = OUTPUT_DIR / "suite_baselines_summary.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n\n=======================================================")
    print(f"COMPREHENSIVE STEP 5 EVALUATION COMPLETE")
    print(f"Saved full results to {csv_path}")
    print(f"=======================================================")

if __name__ == "__main__":
    main()
