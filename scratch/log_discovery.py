"""
log_discovery.py — Step 7: Real-Time Algorithm Discovery & Performance Tracker

Role:
    Parses OpenEvolve logs (llm_calls.jsonl, evolution_trace.jsonl, evaluator_checks.jsonl,
    and openevolve_db) to produce comprehensive, structured performance logs for all
    LLM calls and every discovered algorithm.

Outputs:
    1. output/evolution_runs/llm_calls_log.csv            — all LLM calls & token metrics
    2. output/evolution_runs/algorithm_performance_log.csv — all discovered algorithms & fitness
    3. docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG.md          — rich human-readable dashboard & diffs

AGENTS.md Compliance:
    Rule #2 — Dynamically reads metrics from authoritative evaluation traces.
    Rule #3 — Uses workspace virtual environment ./.venv
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
EVOLUTION_DIR = WORKSPACE_ROOT / "output" / "evolution_runs"
LLM_CALLS_FILE = EVOLUTION_DIR / "llm_calls.jsonl"
TRACE_FILE = EVOLUTION_DIR / "evolution_trace.jsonl"
CHECKS_FILE = EVOLUTION_DIR / "evaluator_checks.jsonl"
DB_PROGRAMS_DIR = EVOLUTION_DIR / "openevolve_db" / "programs"

CSV_CALLS_OUTPUT = EVOLUTION_DIR / "llm_calls_log.csv"
CSV_ALGO_OUTPUT = EVOLUTION_DIR / "algorithm_performance_log.csv"
MD_OUTPUT = WORKSPACE_ROOT / "docs" / "EVOLVED_ALGORITHMS_DISCOVERY_LOG.md"

# Baseline targets for comparative evaluation (from Step 5 empirical report)
BASELINES = {
    "fixed_capacity": {"worker_seconds": 27900.0, "misses": 0, "deltas": 205, "p99": 5.0},
    "inferline": {"worker_seconds": 14261.0, "misses": 44, "deltas": 855, "p99": 6.0},
    "kubernetes_hpa": {"worker_seconds": 23940.0, "misses": 72, "deltas": 606, "p99": 13.0},
    "keda": {"worker_seconds": 19850.0, "misses": 128, "deltas": 1710, "p99": 9.5},
    "seed_baseline": {"worker_seconds": 16675.0, "misses": 824, "deltas": 4628, "p99": 7.0},
}

ISLAND_NAMES = {
    0: "Island 0: Core Conformal Branch",
    1: "Island 1: Continuous Complexity Dynamic Radical",
    2: "Island 2: InferLine-Conformal Hybrid Radical",
}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Loads a JSONL file into a list of dictionaries."""
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
    """Writes all LLM calls to output/evolution_runs/llm_calls_log.csv."""
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

    print(f"Updated LLM Calls CSV log: {CSV_CALLS_OUTPUT} ({len(call_records)} entries)")


def sync_algorithm_performance_log(trace_records: List[Dict[str, Any]]) -> None:
    """Writes all discovered algorithms to output/evolution_runs/algorithm_performance_log.csv."""
    if not trace_records:
        return

    CSV_ALGO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "iteration",
        "child_id",
        "parent_id",
        "island_id",
        "island_name",
        "combined_score",
        "cost_savings_%",
        "deadline_misses",
        "worker_seconds",
        "scaling_deltas",
        "max_p99_latency_s",
        "completed_requests",
        "stage1_passed",
        "stage2_passed",
        "regimes_completed",
        "beats_inferline_misses",
        "beats_inferline_cost",
        "beats_inferline_churn",
        "dominates_inferline",
        "changes_description",
    ]

    with open(CSV_ALGO_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in trace_records:
            m = r.get("child_metrics", {})
            island_idx = r.get("island_id", 0) or 0
            misses = int(m.get("deadline_misses", 0))
            wsec = float(m.get("worker_seconds", 0.0))
            deltas = int(m.get("scaling_deltas", 0))

            beats_misses = misses < BASELINES["inferline"]["misses"]
            beats_cost = wsec < BASELINES["inferline"]["worker_seconds"]
            beats_churn = deltas < BASELINES["inferline"]["deltas"]
            dominates = beats_misses and beats_cost and beats_churn

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
                "combined_score": round(float(m.get("combined_score", float("-inf"))), 4),
                "cost_savings_%": round(float(m.get("cost_savings", 0.0)), 2),
                "deadline_misses": misses,
                "worker_seconds": round(wsec, 1),
                "scaling_deltas": deltas,
                "max_p99_latency_s": round(float(m.get("max_p99_latency_s", 0.0)), 2),
                "completed_requests": int(m.get("completed_requests", 0)),
                "stage1_passed": int(m.get("stage1_passed", 0)),
                "stage2_passed": int(m.get("stage2_passed", 0)),
                "regimes_completed": int(m.get("regimes_completed", 0)),
                "beats_inferline_misses": "YES" if beats_misses else "NO",
                "beats_inferline_cost": "YES" if beats_cost else "NO",
                "beats_inferline_churn": "YES" if beats_churn else "NO",
                "dominates_inferline": "YES" if dominates else "NO",
                "changes_description": rationale.replace("\n", " "),
            })

    print(f"Updated Algorithm Performance CSV: {CSV_ALGO_OUTPUT} ({len(trace_records)} entries)")


def sync_markdown_discovery_log(
    trace_records: List[Dict[str, Any]],
    call_records: List[Dict[str, Any]],
    check_records: List[Dict[str, Any]],
) -> None:
    """Generates the human-readable Markdown dashboard."""
    # Find best program
    best_record = None
    best_score = float("-inf")
    for r in trace_records:
        score = float(r.get("child_metrics", {}).get("combined_score", float("-inf")))
        if score > best_score:
            best_score = score
            best_record = r

    # Compute call token aggregates
    total_calls = len(call_records)
    succ_calls = sum(1 for c in call_records if c.get("status") == "SUCCESS")
    err_calls = sum(1 for c in call_records if c.get("status") != "SUCCESS")
    tot_prompt_tok = sum(c.get("token_usage", {}).get("prompt_tokens", 0) or 0 for c in call_records)
    tot_comp_tok = sum(c.get("token_usage", {}).get("completion_tokens", 0) or 0 for c in call_records)
    tot_tok = sum(c.get("token_usage", {}).get("total_tokens", 0) or 0 for c in call_records)

    md = [
        "# OpenEvolve Evolutionary Conformal Autoscaler Discovery Log",
        "",
        "> **Notice**: This document tracks the simulation-in-the-loop synthesis of",
        "> adaptive conformal scaling policies across 13 diverse workload regimes",
        "> on ContinuumBench (121,134 requests). Real-time telemetry is recorded on",
        "> every LLM synthesis call and multi-stage cascade evaluation.",
        "",
        "## 1. Executive Status & Best Policy to Date",
        "",
    ]

    if best_record:
        bm = best_record.get("child_metrics", {})
        b_island = best_record.get("island_id", 0)
        b_misses = int(bm.get("deadline_misses", 0))
        b_wsec = float(bm.get("worker_seconds", 0.0))
        b_savings = float(bm.get("cost_savings", 0.0))
        b_deltas = int(bm.get("scaling_deltas", 0))
        b_p99 = float(bm.get("max_p99_latency_s", 0.0))

        md.extend([
            f"- **Best Program ID**: `{best_record.get('child_id', '')}` (Iteration {best_record.get('iteration', 0)})",
            f"- **Branch Origin**: **{ISLAND_NAMES.get(b_island, f'Island {b_island}')}**",
            f"- **Primary Fitness $J$**: **{best_score:.4f}**",
            f"- **Deadline Misses**: **{b_misses}** (InferLine: 44, Fixed: 0)",
            f"- **Worker-Seconds**: **{b_wsec:,.1f}** (**{b_savings:.2f}% savings** vs Fixed Capacity; InferLine: 14,261.0 / 48.9%)",
            f"- **Churn Deltas**: **{b_deltas}** (InferLine: 855, KEDA: 1,710)",
            f"- **Tail Safety (P99)**: **{b_p99:.2f}s** (InferLine: 6.0s, SLA Deadline: 10.0s)",
            "",
        ])
    else:
        md.append("- *No evaluated programs recorded yet.* Initial seed baseline or pre-flight run active.\n")

    md.extend([
        "### Benchmark Baseline Comparison Matrix",
        "",
        "| Controller / Policy | Type | Worker-Seconds | Cost Savings vs Fixed | Deadline Misses | Churn Deltas | Max P99 Latency |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|",
        f"| **Fixed Capacity** | Static Peak | {BASELINES['fixed_capacity']['worker_seconds']:,.1f} | 0.0% | {BASELINES['fixed_capacity']['misses']} | {BASELINES['fixed_capacity']['deltas']} | {BASELINES['fixed_capacity']['p99']:.1f}s |",
        f"| **InferLine Tuner** | Reactive Envelope | {BASELINES['inferline']['worker_seconds']:,.1f} | 48.9% | {BASELINES['inferline']['misses']} | {BASELINES['inferline']['deltas']} | {BASELINES['inferline']['p99']:.1f}s |",
        f"| **Kubernetes HPA** | Reactive Util | {BASELINES['kubernetes_hpa']['worker_seconds']:,.1f} | 14.2% | {BASELINES['kubernetes_hpa']['misses']} | {BASELINES['kubernetes_hpa']['deltas']} | {BASELINES['kubernetes_hpa']['p99']:.1f}s |",
        f"| **KEDA** | Reactive Concurrency | {BASELINES['keda']['worker_seconds']:,.1f} | 28.9% | {BASELINES['keda']['misses']} | {BASELINES['keda']['deltas']} | {BASELINES['keda']['p99']:.1f}s |",
        f"| **Conformal Seed Baseline** | Conformal ACI | {BASELINES['seed_baseline']['worker_seconds']:,.1f} | 40.2% | {BASELINES['seed_baseline']['misses']} | {BASELINES['seed_baseline']['deltas']} | {BASELINES['seed_baseline']['p99']:.1f}s |",
    ])

    if best_record:
        bm = best_record.get("child_metrics", {})
        md.append(
            f"| **⭐ Best Evolved Policy** | **Conformal Evolved** | **{float(bm.get('worker_seconds', 0.0)):,.1f}** | "
            f"**{float(bm.get('cost_savings', 0.0)):.2f}%** | **{int(bm.get('deadline_misses', 0))}** | "
            f"**{int(bm.get('scaling_deltas', 0))}** | **{float(bm.get('max_p99_latency_s', 0.0)):.2f}s** |"
        )

    md.extend([
        "",
        "---",
        "",
        "## 2. LLM Call & Synthesis Telemetry",
        "",
        f"- **Total LLM Calls**: {total_calls} (Successful: {succ_calls} | Rejected/Error: {err_calls})",
        f"- **Total Token Budget Consumed**: {tot_tok:,} tokens ({tot_prompt_tok:,} prompt + {tot_comp_tok:,} completion/thinking)",
        f"- **Model**: `gemini-2.5-flash` via Google AI Studio (`temperature: 0.7`, `max_tokens: 8192`)",
        "",
        "---",
        "",
        "## 3. Discovered Algorithms Summary Table",
        "",
        "| Iter | Program ID | Branch Origin | Fitness $J$ | Misses | Worker-Sec | Savings | Deltas | Max P99 | Regimes | Status vs InferLine |",
        "|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|",
    ])

    for r in trace_records:
        m = r.get("child_metrics", {})
        island_idx = r.get("island_id", 0) or 0
        tag = f"Island {island_idx}"
        score = float(m.get("combined_score", float("-inf")))
        misses = int(m.get("deadline_misses", 0))
        wsec = float(m.get("worker_seconds", 0.0))
        savings = float(m.get("cost_savings", 0.0))
        deltas = int(m.get("scaling_deltas", 0))
        p99 = float(m.get("max_p99_latency_s", 0.0))
        regimes = f"{int(m.get('regimes_completed', 0))}/13"

        beats_misses = misses < BASELINES["inferline"]["misses"]
        beats_cost = wsec < BASELINES["inferline"]["worker_seconds"]
        beats_churn = deltas < BASELINES["inferline"]["deltas"]

        if beats_misses and beats_cost and beats_churn:
            status_str = "🏆 Strictly Dominates"
        elif beats_misses and beats_cost:
            status_str = "✅ Beats Cost & Misses"
        elif beats_misses:
            status_str = "✅ Beats Misses"
        elif beats_cost:
            status_str = "⚡ Beats Cost"
        else:
            status_str = "Evaluated"

        md.append(
            f"| {r.get('iteration', 0)} | `{r.get('child_id', '')[:8]}` | {tag} | "
            f"**{score:.2f}** | {misses} | {wsec:,.1f} | {savings:.1f}% | {deltas} | {p99:.2f}s | {regimes} | {status_str} |"
        )

    md.extend([
        "",
        "---",
        "",
        "## 4. Chronological Iteration Breakdown & Code Innovations",
        "",
    ])

    for r in trace_records:
        m = r.get("child_metrics", {})
        island_idx = r.get("island_id", 0) or 0

        p_lines = (r.get("parent_code") or "").splitlines(keepends=True)
        c_lines = (r.get("child_code") or "").splitlines(keepends=True)
        if p_lines and c_lines:
            diff = "".join(difflib.unified_diff(p_lines, c_lines, fromfile="parent_policy.py", tofile="evolved_policy.py", n=3))
        else:
            diff = r.get("code_diff") or r.get("metadata", {}).get("changes") or "(Initial seed baseline)"

        resp = r.get("llm_response") or ""
        desc = resp.split("<<<<<<< SEARCH")[0].strip() if "<<<<<<< SEARCH" in resp else (r.get("child_changes_description") or "Initial seed policy")
        if not desc:
            desc = r.get("metadata", {}).get("changes") or "Initial seed policy"

        score = float(m.get("combined_score", float("-inf")))
        misses = int(m.get("deadline_misses", 0))
        wsec = float(m.get("worker_seconds", 0.0))
        savings = float(m.get("cost_savings", 0.0))
        deltas = int(m.get("scaling_deltas", 0))
        p99 = float(m.get("max_p99_latency_s", 0.0))

        # Find matching call record for token details
        c_match = next((c for c in call_records if c.get("child_id") == r.get("child_id")), None)
        token_info = ""
        if c_match:
            tok = c_match.get("token_usage", {})
            token_info = (
                f"- **LLM Call Telemetry**: {tok.get('prompt_tokens', 0)} prompt tokens, "
                f"{tok.get('completion_tokens', 0)} completion tokens (total: {tok.get('total_tokens', 0)}) | "
                f"Latency: {c_match.get('duration_s', 0.0)}s\n"
            )

        md.extend([
            f"### Iteration {r.get('iteration', 0)}: Program `{r.get('child_id', '')}`",
            f"- **Branch Origin**: **{ISLAND_NAMES.get(island_idx, f'Island {island_idx}')}**",
            f"- **Parent Program**: `{r.get('parent_id', 'None')}`",
            token_info.rstrip(),
            f"- **Composite Fitness $J$**: **{score:.4f}**",
            f"- **13-Regime Benchmark Performance**: {misses} misses, {wsec:,.1f} worker-s ({savings:.2f}% savings), {deltas} deltas, Max P99: {p99:.2f}s",
            f"- **Innovation Rationale**: {desc}",
            "",
            "#### Code Mutation Applied:",
            "```diff",
            diff.strip(),
            "```",
            "",
        ])

    # Failed calls log section
    if err_calls > 0:
        md.extend([
            "---",
            "",
            "## 5. Failed LLM Calls & Feedback Diagnostics",
            "",
            "The following LLM calls encountered syntax, formatting, or boundary rejections and were handled by OpenEvolve's feedback loop:",
            "",
            "| Iter | Island | Duration | Error Diagnostic |",
            "|:---:|:---:|:---:|:---|",
        ])
        for c in call_records:
            if c.get("status") != "SUCCESS":
                err_text = (c.get("error") or "Unknown error").replace("|", "\\|")[:120]
                md.append(
                    f"| {c.get('iteration', 0)} | Island {c.get('island_id', 0)} | "
                    f"{c.get('duration_s', 0.0)}s | `{err_text}` |"
                )

    MD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"Updated Discovery Markdown log: {MD_OUTPUT}")


def sync_logs():
    """Authoritative synchronizer invoked after each iteration and at run completion."""
    call_records = load_jsonl(LLM_CALLS_FILE)
    trace_records = load_jsonl(TRACE_FILE)
    check_records = load_jsonl(CHECKS_FILE)

    if call_records:
        sync_llm_calls_log(call_records)

    if trace_records:
        sync_algorithm_performance_log(trace_records)

    sync_markdown_discovery_log(trace_records, call_records, check_records)


if __name__ == "__main__":
    sync_logs()
