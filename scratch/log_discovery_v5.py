"""
log_discovery_v5.py — Step 8.6: Real-Time Algorithm Discovery, Token & Churn Tracker (v5 Realism-Aware)

Role:
    Parses OpenEvolve v5 logs (evolution_trace.jsonl, evaluator_checks.jsonl, llm_calls.jsonl,
    and openevolve_db) to track:
    1. Cumulative and per-iteration LLM token usage (prompt, completion, total).
    2. Code edit churn (lines added, deleted, net modified vs. seed/parent).
    3. Primary metrics under dual-tier composite fitness J_v5 (canonical 13-regime floor
       preservation + extreme physical realism delayed shock mitigation up to 300s).
    4. Auto-identifies policies scoring < 30.0 or ranking lower than 30 for disk cleanup.

Outputs:
    1. output/evolution_runs_v5/llm_calls_log.csv            — all LLM calls & token metrics
    2. output/evolution_runs_v5/algorithm_performance_log.csv — all discovered algorithms & v5 metrics
    3. output/evolution_runs_v5/token_churn_summary.json     — cumulative token & churn telemetry
    4. docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V5.md          — real-time markdown dashboard

AGENTS.md Compliance:
    Rule #1 — Dedicated v5 discovery tracker; previous versions untouched.
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
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
EVOLUTION_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v5"
LLM_CALLS_FILE = EVOLUTION_DIR / "llm_calls.jsonl"
TRACE_FILE = EVOLUTION_DIR / "evolution_trace.jsonl"
CHECKS_FILE = EVOLUTION_DIR / "evaluator_checks.jsonl"
DB_PROGRAMS_DIR = EVOLUTION_DIR / "openevolve_db" / "programs"
SEED_POLICY_FILE = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "seed_policy_v5.py"

CSV_CALLS_OUTPUT = EVOLUTION_DIR / "llm_calls_log.csv"
CSV_ALGO_OUTPUT = EVOLUTION_DIR / "algorithm_performance_log.csv"
SUMMARY_JSON_OUTPUT = EVOLUTION_DIR / "token_churn_summary.json"
MD_OUTPUT = WORKSPACE_ROOT / "docs" / "EVOLVED_ALGORITHMS_DISCOVERY_LOG_V5.md"

BASELINES = {
    "fixed_capacity": {"worker_seconds": 27900.0, "misses": 0, "deltas": 205, "p99": 5.0, "fitness_v5": 0.0},
    "inferline": {"worker_seconds": 14261.0, "misses": 44, "deltas": 855, "p99": 6.0, "fitness_v5": -4356.0},
    "v3_champion": {"worker_seconds": 13001.0, "misses": 0, "deltas": 218, "p99": 5.92, "fitness_v5": 14.84, "shock_misses": 2379},
}

ISLAND_NAMES = {
    0: "Unified Realism Conformal Frontier",
    1: "Island 1: Continuous Complexity Dynamics Radical",
    2: "Island 2: Adaptive Queue Damping Radical",
}


def load_seed_code() -> str:
    """Loads the base seed policy v5 code for line diff computations."""
    if SEED_POLICY_FILE.exists():
        with open(SEED_POLICY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Loads a JSON Lines file into a list of dictionaries."""
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


def compute_code_churn(code_a: str, code_b: str) -> Tuple[int, int, int]:
    """
    Computes (lines_added, lines_deleted, net_churn) between two code strings.
    """
    lines_a = code_a.splitlines(keepends=True)
    lines_b = code_b.splitlines(keepends=True)
    diff = list(difflib.unified_diff(lines_a, lines_b))
    
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    deleted = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    return added, deleted, added + deleted


def sync_llm_calls_log(call_records: List[Dict[str, Any]], trace_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts token metrics from llm_calls.jsonl or evolution_trace.jsonl and writes llm_calls_log.csv.
    Returns cumulative token usage summary.
    """
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
        "model",
        "changes_summary",
        "error",
    ]

    total_prompt = 0
    total_completion = 0
    total_tokens = 0
    calls_count = 0

    # If call_records is empty, extract token records directly from trace_records
    records_to_write = []
    if call_records:
        for idx, r in enumerate(call_records, 1):
            tok = r.get("token_usage") or {}
            island_idx = r.get("island_id", 0) or 0
            p_tok = int(tok.get("prompt_tokens", 0) or 0)
            c_tok = int(tok.get("completion_tokens", 0) or 0)
            t_tok = int(tok.get("total_tokens", p_tok + c_tok) or 0)
            total_prompt += p_tok
            total_completion += c_tok
            total_tokens += t_tok
            calls_count += 1

            records_to_write.append({
                "call_index": idx,
                "iteration": r.get("iteration", 0),
                "datetime": r.get("datetime") or "",
                "island_id": island_idx,
                "island_name": ISLAND_NAMES.get(island_idx, f"Island {island_idx}"),
                "parent_id": r.get("parent_id") or "",
                "child_id": r.get("child_id") or "",
                "status": r.get("status") or "SUCCESS",
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": t_tok,
                "duration_s": r.get("duration_s", 0.0),
                "model": tok.get("model", "gemini-flash"),
                "changes_summary": (r.get("changes_summary") or "").replace("\n", " "),
                "error": (r.get("error") or "").replace("\n", " "),
            })
    else:
        # Fallback to trace_records
        for idx, r in enumerate(trace_records, 1):
            tok = r.get("token_usage") or r.get("metadata", {}).get("token_usage") or {}
            island_idx = r.get("island_id", 0) or 0
            p_tok = int(tok.get("prompt_tokens", 0) or 0)
            c_tok = int(tok.get("completion_tokens", 0) or 0)
            t_tok = int(tok.get("total_tokens", p_tok + c_tok) or 0)
            total_prompt += p_tok
            total_completion += c_tok
            total_tokens += t_tok
            calls_count += 1

            records_to_write.append({
                "call_index": idx,
                "iteration": r.get("iteration", 0),
                "datetime": r.get("datetime") or "",
                "island_id": island_idx,
                "island_name": ISLAND_NAMES.get(island_idx, f"Island {island_idx}"),
                "parent_id": r.get("parent_id") or "",
                "child_id": r.get("child_id") or "",
                "status": "SUCCESS" if "child_metrics" in r else "EVAL_FAILED",
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": t_tok,
                "duration_s": r.get("metadata", {}).get("iteration_time", 0.0),
                "model": tok.get("model", "gemini-flash"),
                "changes_summary": (r.get("child_changes_description") or r.get("metadata", {}).get("changes") or "")[:200].replace("\n", " "),
                "error": "",
            })

    with open(CSV_CALLS_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records_to_write)

    return {
        "calls_count": calls_count,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "total_tokens": total_tokens,
    }


def sync_algorithm_performance_log(trace_records: List[Dict[str, Any]], seed_code: str) -> Dict[str, Any]:
    """
    Parses trace_records, computes diff churn vs. seed, logs algorithm metrics,
    and returns cumulative churn summary.
    """
    CSV_ALGO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "iteration",
        "child_id",
        "parent_id",
        "island_id",
        "island_name",
        "combined_score_v5",
        "cost_savings_%",
        "canonical_misses",
        "realism_misses",
        "realism_resilience",
        "worker_seconds",
        "scaling_deltas",
        "max_p99_latency_s",
        "lines_added",
        "lines_deleted",
        "net_line_churn",
        "prune_status",
        "changes_description",
    ]

    total_added = 0
    total_deleted = 0
    rows = []

    for r in trace_records:
        m = r.get("child_metrics", {})
        island_idx = r.get("island_id", 0) or 0
        wsec = float(m.get("worker_seconds", 0.0))
        score_v5 = float(m.get("combined_score", float("-inf")))

        child_code = r.get("child_code") or ""
        if child_code and seed_code:
            added, deleted, churn = compute_code_churn(seed_code, child_code)
        else:
            added, deleted, churn = 0, 0, 0

        total_added += added
        total_deleted += deleted

        prune_status = "PRUNED (<30.0)" if score_v5 < 30.0 else "ACTIVE (>=30.0)"

        resp = r.get("llm_response") or ""
        rationale = resp.split("<<<<<<< SEARCH")[0].strip() if "<<<<<<< SEARCH" in resp else (r.get("child_changes_description") or "")
        if not rationale:
            meta_changes = r.get("metadata", {}).get("changes") or ""
            rationale = meta_changes[:200]

        rows.append({
            "iteration": r.get("iteration", 0),
            "child_id": r.get("child_id", ""),
            "parent_id": r.get("parent_id", ""),
            "island_id": island_idx,
            "island_name": ISLAND_NAMES.get(island_idx, f"Island {island_idx}"),
            "combined_score_v5": round(score_v5, 4),
            "cost_savings_%": round(float(m.get("cost_savings", 0.0)), 2),
            "canonical_misses": int(m.get("canonical_misses", m.get("deadline_misses", 0))),
            "realism_misses": int(m.get("realism_misses", 0)),
            "realism_resilience": round(float(m.get("realism_resilience", 0.0)), 1),
            "worker_seconds": round(wsec, 1),
            "scaling_deltas": int(m.get("scaling_deltas", 0)),
            "max_p99_latency_s": round(float(m.get("max_p99_latency_s", 0.0)), 3),
            "lines_added": added,
            "lines_deleted": deleted,
            "net_line_churn": churn,
            "prune_status": prune_status,
            "changes_description": (rationale or "").replace("\n", " "),
        })

    with open(CSV_ALGO_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "total_lines_added": total_added,
        "total_lines_deleted": total_deleted,
        "total_line_churn": total_added + total_deleted,
    }


def sync_markdown_dashboard(
    trace_records: List[Dict[str, Any]],
    token_summary: Dict[str, Any],
    churn_summary: Dict[str, Any],
) -> None:
    """Generates the rich real-time markdown dashboard docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V5.md."""
    valid_programs = [
        r for r in trace_records
        if "child_metrics" in r and "combined_score" in r["child_metrics"]
    ]
    valid_programs.sort(key=lambda r: float(r["child_metrics"].get("combined_score", -9999.0)), reverse=True)

    # Estimate API cost (Gemini 2.5 Flash Lite pricing: $0.075 / 1M prompt, $0.30 / 1M completion)
    prompt_cost = (token_summary.get("total_prompt_tokens", 0) / 1_000_000) * 0.075
    completion_cost = (token_summary.get("total_completion_tokens", 0) / 1_000_000) * 0.30
    total_cost_usd = prompt_cost + completion_cost

    lines = [
        "# OpenEvolve v5 Realism-Aware Evolutionary Search: Discovery Log & Leaderboard",
        "",
        f"*Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*",
        "",
        "## 1. Resource Consumption & Operational Telemetry",
        "",
        "| Metric | Total Value | Note |",
        "| :--- | :--- | :--- |",
        f"| **Total LLM Calls** | `{token_summary.get('calls_count', 0):,}` | Mutation & crossover prompts |",
        f"| **Prompt Tokens** | `{token_summary.get('total_prompt_tokens', 0):,}` | Input context and instructions |",
        f"| **Completion Tokens** | `{token_summary.get('total_completion_tokens', 0):,}` | Generated search/replace diffs |",
        f"| **Total Tokens Consumed** | **`{token_summary.get('total_tokens', 0):,}`** | Combined LLM token footprint |",
        f"| **Estimated API Cost** | **`${total_cost_usd:.4f}` USD** | Cost-effective synthesis |",
        f"| **Lines Added / Deleted** | `+{churn_summary.get('total_lines_added', 0):,}` / `-{churn_summary.get('total_lines_deleted', 0):,}` | Cumulative diff churn |",
        f"| **Net Code Churn** | `{churn_summary.get('total_line_churn', 0):,}` lines | Across all evaluated variants |",
        "",
        "---",
        "",
        "## 2. Objective Formulation: Dual-Tier Fitness $J_{\\text{v5}}$",
        "",
        "The **v5 Evolutionary Search** bridges the physical realism gap while preserving the canonical floor:",
        "$$J_{\\text{v5}} = J_{\\text{canon}} + J_{\\text{realism\\_shocks}} + \\text{InferLineBonus}$$",
        "$$\\text{where } J_{\\text{canon}} = \\text{CostSavings\\%} - 100 \\cdot M_{\\text{canon}} - 10 \\cdot \\max(0, P99_{\\text{canon}} - 6.0) - 0.01 \\cdot \\Delta_{\\text{canon}}$$",
        "$$J_{\\text{realism\\_shocks}} = +0.20 \\cdot \\max(0, 7031 - M_{\\text{shock}}) \\quad (T_{\\text{init}} \\in [15\\text{s}, 50\\text{s}, 150\\text{s}, 250\\text{s}, 300\\text{s}])$$",
        "",
        "### Authoritative Benchmarks Comparison",
        "| Controller / Candidate | Canonical Cost | Cost Savings | Canonical Misses | Realism Shock Misses ($T_{\\text{init}} \\le 300\\text{s}$) | Fitness $J_{\\text{v5}}$ | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        "| **Fixed Capacity Baseline** | 27,900.0 ws | 0.0% | 0 | 0 (Static Peak) | 0.00 | Static Floor |",
        "| **InferLine Baseline** | 14,261.0 ws | 48.9% | 44 | 0 (Over-provisioned) | -4,356.0 | Degraded Floor |",
        "| **v3 Champion (`bbd9b1c2`)** | 13,001.0 ws | **53.4%** | **0** | **2,379** (Delayed shock trap) | **+14.84** | Seed Baseline |",
    ]

    if valid_programs:
        best = valid_programs[0]
        bm = best["child_metrics"]
        best_id = best.get("child_id", "N/A")[:8]
        best_fit = float(bm.get("combined_score", 0.0))
        best_cs = float(bm.get("cost_savings", 0.0))
        best_canon_m = int(bm.get("canonical_misses", bm.get("deadline_misses", 0)))
        best_shock_m = int(bm.get("realism_misses", 0))
        best_wsec = float(bm.get("worker_seconds", 0.0))

        lines.append(
            f"| **Current v5 Champion (`{best_id}`)** | **{best_wsec:.1f} ws** | **{best_cs:.2f}%** | "
            f"**{best_canon_m}** | **{best_shock_m}** | **{best_fit:+.2f}** | 🏆 **Frontier Champion** |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Discovered Policies Leaderboard (Top 30 Ranked by Fitness $J_{\\text{v5}}$)",
        "",
        "| Rank | Child ID | Island | Fitness $J_{\\text{v5}}$ | Cost Savings | Canon Miss | Shock Miss | Shock Resilience | P99 Tail | Deltas | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    # Show top 30 policies
    for rank, p in enumerate(valid_programs[:30], 1):
        m = p["child_metrics"]
        cid = p.get("child_id", "N/A")[:8]
        island_idx = p.get("island_id", 0)
        fit = float(m.get("combined_score", -9999.0))
        cs = float(m.get("cost_savings", 0.0))
        c_miss = int(m.get("canonical_misses", m.get("deadline_misses", 0)))
        s_miss = int(m.get("realism_misses", 0))
        resil = float(m.get("realism_resilience", max(0.0, 3000.0 - s_miss)))
        p99 = float(m.get("max_p99_latency_s", 0.0))
        deltas = int(m.get("scaling_deltas", 0))

        if fit < 30.0:
            status = "Pruned (<30.0)"
        elif s_miss < 500:
            status = "★ Realism Master"
        elif s_miss < 2379:
            status = "✓ Beats v3 Realism"
        else:
            status = "Pareto Candidate"

        lines.append(
            f"| {rank} | `{cid}` | Island {island_idx} | **{fit:+.2f}** | {cs:.2f}% | {c_miss} | {s_miss} | {resil:.0f} | {p99:.2f}s | {deltas} | {status} |"
        )

    lines.append("")
    MD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def sync_logs():
    """Master entrypoint: aggregates records, updates CSVs, summary JSON, and markdown dashboard."""
    seed_code = load_seed_code()
    call_records = load_jsonl(LLM_CALLS_FILE)
    trace_records = load_jsonl(TRACE_FILE)

    token_summary = sync_llm_calls_log(call_records, trace_records)
    churn_summary = sync_algorithm_performance_log(trace_records, seed_code)
    sync_markdown_dashboard(trace_records, token_summary, churn_summary)

    # Save summary JSON for external scripts
    summary_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "token_usage": token_summary,
        "code_churn": churn_summary,
        "total_evaluated": len(trace_records),
    }
    with open(SUMMARY_JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)


if __name__ == "__main__":
    sync_logs()
    print("V5 Discovery logs, token metrics, and churn tracking synchronized successfully.")
