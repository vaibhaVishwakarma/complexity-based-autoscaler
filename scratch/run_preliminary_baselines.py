"""
run_preliminary_baselines.py — Execute preliminary multi-node baseline evaluation.

Runs the 5 non-conformal autoscaler policies on the multi-node split-inference continuum:
1. fixed_capacity
2. hpa
3. keda
4. inferline
5. complexity_blind_predictive

Extracts and tabulates:
- QoS / SLO violation rate (deadline = 15s)
- P50, P95, P99 end-to-end latency
- Cost (total provisioned worker-seconds, mean active workers)
- Queue dynamics (queue wait time, peak/mean buffer)
- Stability / Churn (scale-up count, scale-down count, flapping events)
- Routing (fast-path vs slow-path completion counts)
- Epoch-by-epoch trajectory logs
"""

import json
import subprocess
import sys
from pathlib import Path
import pandas as pd

WORKSPACE_ROOT = Path("/home/vaibo/edgecompute")
CONFIG_PATH = WORKSPACE_ROOT / "configs" / "preliminary_multinode_split_inference.yaml"
OUTPUT_DIR = WORKSPACE_ROOT / "output" / "preliminary_runs"
PYTHON_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "python"

CONTROLLERS = [
    ("fixed_capacity", "Fixed Capacity (Peak Oracle)"),
    ("hpa", "Kubernetes HPA"),
    ("keda", "KEDA Queue Trigger"),
    ("inferline", "InferLine Envelope Tuner"),
    ("complexity_blind_predictive", "Complexity-Blind Predictive"),
]

def run_controller(controller_key: str, display_name: str) -> dict:
    ctrl_out = OUTPUT_DIR / controller_key
    ctrl_out.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        str(PYTHON_BIN),
        "-m", "continuum_bench.cli", "run",
        "--config", str(CONFIG_PATH),
        "--controller", controller_key,
        "--seed", "42",
        "--out", str(ctrl_out),
    ]
    
    print(f"\n=======================================================")
    print(f"Running controller: {display_name} ({controller_key})")
    print(f"=======================================================")
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED: {controller_key}\n{res.stderr}")
        raise RuntimeError(f"Controller {controller_key} failed:\n{res.stderr}")
    
    # Locate output directory
    run_dirs = sorted([d for d in ctrl_out.iterdir() if d.is_dir()])
    if not run_dirs:
        raise FileNotFoundError(f"No run directory created under {ctrl_out}")
    latest_run = run_dirs[-1]
    
    summary_file = latest_run / "summary.json"
    with open(summary_file) as f:
        summary = json.load(f)
        
    epochs_file = latest_run / "epochs.csv"
    epochs_df = pd.read_csv(epochs_file) if epochs_file.exists() else None
    
    return {
        "key": controller_key,
        "name": display_name,
        "run_dir": str(latest_run),
        "summary": summary,
        "epochs_df": epochs_df,
    }

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    
    for key, name in CONTROLLERS:
        res = run_controller(key, name)
        results.append(res)
        
    # Compile comparison table
    rows = []
    for r in results:
        s = r["summary"]
        lat = s.get("latency_s", {})
        cost = s.get("cost", {})
        qos = s.get("qos", {})
        rel = s.get("reliability", {})
        stab = s.get("stability", {})
        delay = s.get("delay_breakdown_s", {})
        
        # Fast vs slow path
        per_pri = qos.get("per_priority", {})
        fast_completed = per_pri.get("high", {}).get("completed", 0)
        slow_completed = per_pri.get("low", {}).get("completed", 0)
        fast_gen = per_pri.get("high", {}).get("generated", 0)
        slow_gen = per_pri.get("low", {}).get("generated", 0)
        
        row = {
            "Controller": r["name"],
            "Key": r["key"],
            "Completed Tasks": rel.get("completed_tasks", 0),
            "Pending Tasks": rel.get("pending_tasks", 0),
            "Fast Path (Edge)": f"{fast_completed}/{fast_gen}",
            "Slow Path (Cloud)": f"{slow_completed}/{slow_gen}",
            "Mean Active Workers": cost.get("mean_active_workers", 0.0),
            "Worker-Seconds (Cost)": cost.get("total_provisioned_worker_seconds", 0.0),
            "Mean Latency (s)": lat.get("mean", 0.0),
            "P50 Latency (s)": lat.get("p50", 0.0),
            "P95 Latency (s)": lat.get("p95", 0.0),
            "P99 Latency (s)": lat.get("p99", 0.0),
            "Queue Wait Mean (s)": delay.get("queue_wait_s", {}).get("mean", 0.0),
            "Queue Wait P95 (s)": delay.get("queue_wait_s", {}).get("p95", 0.0),
            "Total Scaling Delta (abs)": stab.get("scaling_delta_abs_total", 0.0),
            "Deadline Miss Count": qos.get("deadline_miss_count", 0),
        }
        rows.append(row)
        
    df = pd.DataFrame(rows)
    print("\n\n=======================================================")
    print("PRELIMINARY BASELINE EVALUATION SUMMARY")
    print("=======================================================")
    print(df.to_string(index=False))
    
    # Save comparison CSV and JSON
    df.to_csv(OUTPUT_DIR / "preliminary_baselines_comparison.csv", index=False)
    with open(OUTPUT_DIR / "preliminary_baselines_results.json", "w") as f:
        json.dump([{"key": r["key"], "name": r["name"], "run_dir": r["run_dir"], "summary": r["summary"]} for r in results], f, indent=2)
    print(f"\nSaved comparison artifacts to {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
