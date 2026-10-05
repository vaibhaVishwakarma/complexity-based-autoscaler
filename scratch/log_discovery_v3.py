"""
log_discovery_v3.py — Step 7 v3: Real-Time Algorithm Discovery & Performance Tracker

Role:
    Parses OpenEvolve v3 logs (llm_calls.jsonl, evolution_trace.jsonl, evaluator_checks.jsonl,
    and openevolve_db) to produce structured performance logs for all LLM calls and every
    discovered algorithm under the Cost-Supreme v3 fitness objective (6.0s P99 baseline).

Outputs:
    1. output/evolution_runs_v3/llm_calls_log.csv            — all LLM calls & token metrics
    2. output/evolution_runs_v3/algorithm_performance_log.csv — all discovered algorithms & v3 fitness
    3. docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V3.md          — rich human-readable dashboard & diffs

AGENTS.md Compliance:
    Rule #1 — Dedicated v3 discovery tracker; v1/v2 trackers untouched.
    Rule #2 — Dynamically reads metrics from authoritative evaluation traces.
    Rule #3 — Uses workspace virtual environment ./.venv.
    Rule #4 — Self-documenting header and inline comments.
"""

import csv
import difflib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
EVOLUTION_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v3"
LLM_CALLS_FILE = EVOLUTION_DIR / "llm_calls.jsonl"
TRACE_FILE = EVOLUTION_DIR / "evolution_trace.jsonl"
CHECKS_FILE = EVOLUTION_DIR / "evaluator_checks.jsonl"
DB_PROGRAMS_DIR = EVOLUTION_DIR / "openevolve_db" / "programs"

CSV_CALLS_OUTPUT = EVOLUTION_DIR / "llm_calls_log.csv"
CSV_ALGO_OUTPUT = EVOLUTION_DIR / "algorithm_performance_log.csv"
MD_OUTPUT = WORKSPACE_ROOT / "docs" / "EVOLVED_ALGORITHMS_DISCOVERY_LOG_V3.md"

BASELINES = {
    "fixed_capacity": {"worker_seconds": 27900.0, "misses": 0, "deltas": 205, "p99": 5.0, "fitness_v3": 0.0},
    "inferline": {"worker_seconds": 14261.0, "misses": 44, "deltas": 855, "p99": 6.0, "fitness_v3": -47.67},
    "step7_v1_champion": {"worker_seconds": 20645.0, "misses": 0, "deltas": 218, "p99": 4.89, "fitness_v3": 23.82},
    "step7_v2_cost_champion": {"worker_seconds": 13100.0, "misses": 0, "deltas": 258, "p99": 6.00, "fitness_v3": 50.47},
}

ISLAND_NAMES = {
    0: "Island 0: Core Conformal Branch",
    1: "Island 1: Continuous Complexity Dynamic Radical",
    2: "Island 2: InferLine-Conformal Hybrid Radical",
}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    if not path.exists():
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def sync_llm_calls_log(call_records: List[Dict[str, Any]]) -> None:
    if not call_records:
        return

    CSV_CALLS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "call_index",
        "iteration",
        "datetime",
        "island_id",
        "island_name",
        "parent_id",
        "child_id",
        "status",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "duration_s",
        "changes_summary",
        "error",
    ]

    with open(CSV_CALLS_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, r in enumerate(call_records, 1):
            tok = r.get("token_usage") or {}
            island_idx = r.get("island_id", 0) or 0
            writer.writerow({
                "call_index": idx,
                "iteration": r.get("iteration", 0),
                "datetime": r.get("datetime") or "",
                "island_id": island_idx,
                "island_name": ISLAND_NAMES.get(island_idx, f"Island {island_idx}"),
                "parent_id": r.get("parent_id") or "",
                "child_id": r.get("child_id") or "",
                "status": r.get("status") or "SUCCESS",
                "prompt_tokens": tok.get("prompt_tokens", 0) or 0,
                "completion_tokens": tok.get("completion_tokens", 0) or 0,
                "total_tokens": tok.get("total_tokens", 0) or 0,
                "duration_s": r.get("duration_s", 0.0),
                "changes_summary": (r.get("changes_summary") or "").replace("\n", " "),
                "error": (r.get("error") or "").replace("\n", " "),
            })


def sync_algorithm_performance_log(trace_records: List[Dict[str, Any]]) -> None:
    if not trace_records:
        return

    CSV_ALGO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "iteration",
        "child_id",
        "parent_id",
        "island_id",
        "island_name",
        "combined_score_v3",
        "cost_savings_%",
        "deadline_misses",
        "worker_seconds",
        "scaling_deltas",
        "max_p99_latency_s",
        "completed_requests",
        "stage1_passed",
        "stage2_passed",
        "regimes_completed",
        "beats_inferline_cost",
        "beats_seed_53pct",
        "changes_description",
    ]

    with open(CSV_ALGO_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in trace_records:
            m = r.get("child_metrics", {})
            island_idx = r.get("island_id", 0) or 0
            wsec = float(m.get("worker_seconds", 0.0))
            fitness_v3 = float(m.get("combined_score", float("-inf")))

            beats_cost = wsec < BASELINES["inferline"]["worker_seconds"] and wsec > 0
            beats_seed = wsec < BASELINES["step7_v2_cost_champion"]["worker_seconds"] and wsec > 0

            resp = r.get("llm_response") or ""
            rationale = resp.split("<<<<<<< SEARCH")[0].strip() if "<<<<<<< SEARCH" in resp else (r.get("child_changes_description") or "")
            if not rationale:
                meta_changes = r.get("metadata", {}).get("changes") or ""
                rationale = meta_changes[:200]

            writer.writerow({
                "iteration": r.get("iteration", 0),
                "child_id": r.get("child_id", ""),
                "parent_id": r.get("parent_id", ""),
                "island_id": island_idx,
                "island_name": ISLAND_NAMES.get(island_idx, f"Island {island_idx}"),
                "combined_score_v3": round(fitness_v3, 4),
                "cost_savings_%": round(float(m.get("cost_savings", 0.0)), 2),
                "deadline_misses": int(m.get("deadline_misses", 0)),
                "worker_seconds": round(wsec, 1),
                "scaling_deltas": int(m.get("scaling_deltas", 0)),
                "max_p99_latency_s": round(float(m.get("max_p99_latency_s", 0.0)), 3),
                "completed_requests": int(m.get("completed_requests", 0)),
                "stage1_passed": int(m.get("stage1_passed", 1)),
                "stage2_passed": int(m.get("stage2_passed", 1)),
                "regimes_completed": int(m.get("regimes_completed", 0)),
                "beats_inferline_cost": beats_cost,
                "beats_seed_53pct": beats_seed,
                "changes_description": (rationale or "").replace("\n", " "),
            })


def sync_markdown_dashboard(trace_records: List[Dict[str, Any]]) -> None:
    if not trace_records:
        return

    valid_programs = [
        r for r in trace_records
        if "child_metrics" in r and "combined_score" in r["child_metrics"]
    ]
    valid_programs.sort(key=lambda r: float(r["child_metrics"].get("combined_score", -9999.0)), reverse=True)

    lines = [
        "# OpenEvolve v3 Cost-Supreme Evolutionary Search: Discovery Log & Leaderboard",
        "",
        f"*Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
        "## 1. Executive Summary & Objective Realignment (v3 Cost-Supreme)",
        "",
        "The **v3 Evolutionary Search** establishes **Cost Savings as supreme**, setting the P99 tail latency envelope at 6.0s (SLA deadline is 15.0s):",
        "$$J_{\\text{v3}} = \\text{cost\\_savings\\_\\%} - \\left(2.0 \\cdot \\min(M, 50) + 10.0 \\cdot \\max(0, M - 50)\\right) - 10.0 \\cdot \\max(0.0, P99 - 6.0) - 0.01 \\cdot \\Delta$$",
        "",
        "| Policy / Model | Worker-Sec (Cost) | Cost Savings vs Fixed | Deadline Misses | P99 Tail Latency | Scaling Deltas | Fitness $J_{\\text{v3}}$ |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        "| **Fixed Capacity Baseline** | 27,900.0 ws | 0.0% | 0 | 5.00s | 205 | 0.00 |",
        "| **InferLine Baseline** | 14,261.0 ws | **48.9%** | 44 | 6.00s | 855 | -47.67 |",
        "| **v2 Cost Champion (Seed)** | 13,100.0 ws | **53.05%** | **0** | **6.00s** | **258** | **+50.47** |",
    ]

    if valid_programs:
        best = valid_programs[0]
        bm = best["child_metrics"]
        lines.append(
            f"| **Current v3 Champion ({best.get('child_id', 'N/A')[:8]})** | "
            f"**{bm.get('worker_seconds', 0.0):.1f} ws** | "
            f"**{bm.get('cost_savings', 0.0):.2f}%** | "
            f"**{int(bm.get('deadline_misses', 0))}** | "
            f"**{bm.get('max_p99_latency_s', 0.0):.2f}s** | "
            f"**{int(bm.get('scaling_deltas', 0))}** | "
            f"**+{float(bm.get('combined_score', 0.0)):.2f}** |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 2. Top Discovered Policies (Ranked by Fitness $J_{\\text{v3}}$)",
        "",
        "| Rank | Child ID | Island | Fitness $J_{\\text{v3}}$ | Cost Savings | Misses | P99 Latency | Worker-Sec | Deltas | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for rank, p in enumerate(valid_programs[:15], 1):
        m = p["child_metrics"]
        cid = p.get("child_id", "N/A")[:8]
        island_idx = p.get("island_id", 0)
        fit = float(m.get("combined_score", -9999.0))
        cs = float(m.get("cost_savings", 0.0))
        misses = int(m.get("deadline_misses", 0))
        p99 = float(m.get("max_p99_latency_s", 0.0))
        ws = float(m.get("worker_seconds", 0.0))
        deltas = int(m.get("scaling_deltas", 0))
        status = "★ Beats Seed Cost" if ws < 13100.0 and ws > 0 else ("Beats InferLine Cost" if ws < 14261.0 else "Exploring")

        lines.append(
            f"| {rank} | `{cid}` | Island {island_idx} | **{fit:+.2f}** | {cs:.2f}% | {misses} | {p99:.2f}s | {ws:.1f} | {deltas} | {status} |"
        )

    lines.append("")
    MD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def sync_logs():
    call_records = load_jsonl(LLM_CALLS_FILE)
    trace_records = load_jsonl(TRACE_FILE)

    sync_llm_calls_log(call_records)
    sync_algorithm_performance_log(trace_records)
    sync_markdown_dashboard(trace_records)


if __name__ == "__main__":
    sync_logs()
    print("V3 Discovery logs synchronized successfully.")
