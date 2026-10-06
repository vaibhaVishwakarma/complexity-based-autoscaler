"""
log_discovery_v4.py — Step 7 v4: Real-Time Algorithm Discovery & Full Telemetry Tracker

Role:
    Parses OpenEvolve v4 execution artifacts (llm_calls.jsonl, evolution_trace.jsonl,
    evaluator_checks.jsonl, and openevolve_db) to track:
      1. Discovered policy performance (v4 Pareto-optimal fitness, cost, tail latency, misses).
      2. Cumulative & per-iteration LLM token consumption (prompt, completion, total, per-model).
      3. Cumulative & per-iteration code churn metrics (lines added, deleted, modified, edit hunks).

Outputs:
    1. output/evolution_runs_v4/llm_calls_log.csv            — all LLM calls, tokens, code diffs
    2. output/evolution_runs_v4/algorithm_performance_log.csv — all evaluated policies & metrics
    3. output/evolution_runs_v4/evolution_telemetry_summary.json — machine-readable telemetry aggregates
    4. docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md          — real-time markdown dashboard

AGENTS.md Compliance:
    Rule #1 — Dedicated v4 discovery tracker; v1/v2/v3 trackers untouched.
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
EVOLUTION_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v4"
LLM_CALLS_FILE = EVOLUTION_DIR / "llm_calls.jsonl"
TRACE_FILE = EVOLUTION_DIR / "evolution_trace.jsonl"
CHECKS_FILE = EVOLUTION_DIR / "evaluator_checks.jsonl"
DB_PROGRAMS_DIR = EVOLUTION_DIR / "openevolve_db" / "programs"

CSV_CALLS_OUTPUT = EVOLUTION_DIR / "llm_calls_log.csv"
CSV_ALGO_OUTPUT = EVOLUTION_DIR / "algorithm_performance_log.csv"
TELEMETRY_JSON_OUTPUT = EVOLUTION_DIR / "evolution_telemetry_summary.json"
MD_OUTPUT = WORKSPACE_ROOT / "docs" / "EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md"

BASELINES = {
    "fixed_capacity": {"worker_seconds": 27900.0, "misses": 0, "deltas": 205, "max_p99": 5.0, "mean_p99": 5.0, "fitness_v4": 0.0},
    "inferline": {"worker_seconds": 14261.0, "misses": 44, "deltas": 855, "max_p99": 7.0, "mean_p99": 5.8, "fitness_v4": -75.0},
    "v3_champion_bbd9b1c2": {"worker_seconds": 11874.0, "misses": 0, "deltas": 228, "max_p99": 6.0, "mean_p99": 5.2, "fitness_v4": 40.16},
}

ISLAND_NAMES = {
    0: "Island 0: Core Conformal Branch",
    1: "Island 1: Acceleration & Causal Dynamics Radical",
    2: "Island 2: Task-Age Urgency & Drain Hybrid",
}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    if not path.exists():
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    return records


def compute_code_diff_stats(parent_code: str, child_code: str) -> Dict[str, int]:
    """
    Computes exact line additions, deletions, modified lines, and edit hunks between parent and child code.
    """
    if not parent_code or not child_code:
        return {"lines_added": 0, "lines_deleted": 0, "lines_modified": 0, "edit_hunks": 0}

    parent_lines = parent_code.splitlines(keepends=True)
    child_lines = child_code.splitlines(keepends=True)

    diff = list(difflib.unified_diff(parent_lines, child_lines, n=0))
    lines_added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    lines_deleted = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
    edit_hunks = sum(1 for line in diff if line.startswith("@@"))

    return {
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "lines_modified": lines_added + lines_deleted,
        "edit_hunks": edit_hunks,
    }


def extract_tokens(r: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts prompt, completion, total tokens and model from record or metadata."""
    tok = r.get("token_usage") or r.get("metadata", {}).get("token_usage") or {}
    p_tok = int(tok.get("prompt_tokens", 0) or 0)
    c_tok = int(tok.get("completion_tokens", 0) or 0)
    t_tok = int(tok.get("total_tokens", 0) or (p_tok + c_tok))
    model = tok.get("model") or r.get("model") or "gemini-flash"
    return {
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "total_tokens": t_tok,
        "model": model,
    }


def aggregate_telemetry(
    llm_calls: List[Dict[str, Any]],
    trace_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Computes cumulative tokens and code edit statistics across the entire evolution run.
    """
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    model_breakdown: Dict[str, Dict[str, int]] = {}

    # Prefer detailed llm_calls if available, fallback to trace_records
    source_records = llm_calls if llm_calls else trace_records

    for r in source_records:
        tok = extract_tokens(r)
        total_prompt_tokens += tok["prompt_tokens"]
        total_completion_tokens += tok["completion_tokens"]
        total_tokens += tok["total_tokens"]

        m_name = tok["model"]
        if m_name not in model_breakdown:
            model_breakdown[m_name] = {
                "calls": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        model_breakdown[m_name]["calls"] += 1
        model_breakdown[m_name]["prompt_tokens"] += tok["prompt_tokens"]
        model_breakdown[m_name]["completion_tokens"] += tok["completion_tokens"]
        model_breakdown[m_name]["total_tokens"] += tok["total_tokens"]

    total_lines_added = 0
    total_lines_deleted = 0
    total_lines_modified = 0
    total_edit_hunks = 0
    total_mutation_events = 0

    per_iter_diffs: Dict[int, Dict[str, int]] = {}

    for t in trace_records:
        p_code = t.get("parent_code", "")
        c_code = t.get("child_code", "")
        diff_stats = compute_code_diff_stats(p_code, c_code)

        it = t.get("iteration", 0)
        per_iter_diffs[it] = diff_stats

        total_lines_added += diff_stats["lines_added"]
        total_lines_deleted += diff_stats["lines_deleted"]
        total_lines_modified += diff_stats["lines_modified"]
        total_edit_hunks += diff_stats["edit_hunks"]
        if diff_stats["lines_modified"] > 0:
            total_mutation_events += 1

    return {
        "total_llm_calls": len(source_records),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "model_breakdown": model_breakdown,
        "total_lines_added": total_lines_added,
        "total_lines_deleted": total_lines_deleted,
        "total_net_lines": total_lines_added - total_lines_deleted,
        "total_lines_modified": total_lines_modified,
        "total_edit_hunks": total_edit_hunks,
        "total_mutation_events": total_mutation_events,
        "per_iter_diffs": per_iter_diffs,
    }


def sync_llm_calls_csv(
    records: List[Dict[str, Any]],
    telemetry: Dict[str, Any],
) -> None:
    if not records:
        return
    CSV_CALLS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "call_index", "iteration", "datetime", "island_id", "island_name",
        "parent_id", "child_id", "status", "model",
        "prompt_tokens", "completion_tokens", "total_tokens",
        "lines_added", "lines_deleted", "edit_hunks",
        "duration_s", "changes_summary", "error",
    ]
    per_iter_diffs = telemetry.get("per_iter_diffs", {})

    with open(CSV_CALLS_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for idx, r in enumerate(records, 1):
            tok = extract_tokens(r)
            it = r.get("iteration", 0)
            diff = per_iter_diffs.get(it, {"lines_added": 0, "lines_deleted": 0, "edit_hunks": 0})
            island_idx = r.get("island_id", 0) or 0
            writer.writerow({
                "call_index": idx,
                "iteration": it,
                "datetime": r.get("datetime") or "",
                "island_id": island_idx,
                "island_name": ISLAND_NAMES.get(island_idx, f"Island {island_idx}"),
                "parent_id": r.get("parent_id") or "",
                "child_id": r.get("child_id") or "",
                "status": r.get("status") or "SUCCESS",
                "model": tok["model"],
                "prompt_tokens": tok["prompt_tokens"],
                "completion_tokens": tok["completion_tokens"],
                "total_tokens": tok["total_tokens"],
                "lines_added": diff["lines_added"],
                "lines_deleted": diff["lines_deleted"],
                "edit_hunks": diff["edit_hunks"],
                "duration_s": r.get("duration_s", 0.0),
                "changes_summary": (r.get("changes_summary") or "").replace("\n", " "),
                "error": (r.get("error") or "").replace("\n", " "),
            })


def sync_algorithms_csv(
    programs: List[Dict[str, Any]],
    telemetry: Dict[str, Any],
) -> None:
    if not programs:
        return
    CSV_ALGO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "program_id", "iteration", "island", "parent_id", "combined_score_v4",
        "cost_savings_%", "churn_stability", "tail_safety", "deadline_misses",
        "worker_seconds", "scaling_deltas", "max_p99_latency_s", "mean_p99_latency_s",
        "lines_added", "lines_deleted", "net_lines", "edit_hunks",
        "regimes_completed", "status",
    ]
    per_iter_diffs = telemetry.get("per_iter_diffs", {})

    with open(CSV_ALGO_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for p in programs:
            it = p.get("iteration", 0)
            diff = per_iter_diffs.get(it, {"lines_added": 0, "lines_deleted": 0, "edit_hunks": 0})
            writer.writerow({
                "program_id": p.get("program_id"),
                "iteration": it,
                "island": p.get("island"),
                "parent_id": p.get("parent_id"),
                "combined_score_v4": p.get("combined_score"),
                "cost_savings_%": p.get("cost_savings"),
                "churn_stability": p.get("churn_stability"),
                "tail_safety": p.get("tail_safety"),
                "deadline_misses": p.get("deadline_misses"),
                "worker_seconds": p.get("worker_seconds"),
                "scaling_deltas": p.get("scaling_deltas"),
                "max_p99_latency_s": p.get("max_p99_latency_s"),
                "mean_p99_latency_s": p.get("mean_p99_latency_s"),
                "lines_added": diff["lines_added"],
                "lines_deleted": diff["lines_deleted"],
                "net_lines": diff["lines_added"] - diff["lines_deleted"],
                "edit_hunks": diff["edit_hunks"],
                "regimes_completed": p.get("regimes_completed"),
                "status": p.get("status", "EVALUATED"),
            })


def generate_markdown_dashboard(
    programs: List[Dict[str, Any]],
    llm_calls: List[Dict[str, Any]],
    trace_records: List[Dict[str, Any]],
    telemetry: Dict[str, Any],
) -> None:
    MD_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    valid_programs = [p for p in programs if p.get("combined_score") is not None and p.get("combined_score") > -900]
    valid_programs.sort(key=lambda p: float(p.get("combined_score", -9999)), reverse=True)

    top5 = valid_programs[:5]
    total_evals = len(programs)
    best_prog = top5[0] if top5 else None

    lines = [
        "# OpenEvolve v4 Algorithm Discovery & Full Telemetry Log",
        "",
        rf"*Last Synchronized: `{now_str}`*",
        rf"- **Objective**: Maximize $J_{{v4}}$ (Retain $>55\%$ cost savings, 0 misses, and squash Max P99 from $6.0\text{{s}} \to \le 5.0\text{{s}}$)",
        f"- **Total Discovered Policies**: `{total_evals}`",
        f"- **Top Discovered Fitness ($J_{{v4}}$)**: `{best_prog['combined_score']:.4f}`" if best_prog else "- **Top Discovered Fitness**: `Pending initial run`",
        "",
        "---",
        "",
        "## 1. Global Resource & Code Churn Telemetry",
        "",
        "Comprehensive tracking of all LLM API token consumption and evolutionary code edit activities:",
        "",
        "| Telemetric Category | Metric | Cumulative Total |",
        "| :--- | :--- | :---: |",
        f"| **LLM Token Usage** | Prompt Tokens Consumed | `{telemetry['total_prompt_tokens']:,}` |",
        f"| | Completion Tokens Generated | `{telemetry['total_completion_tokens']:,}` |",
        f"| | **Total Tokens Consumed** | **`{telemetry['total_tokens']:,}`** |",
        f"| | Total LLM Synthesis Calls | `{telemetry['total_llm_calls']:,}` |",
        f"| **Code Mutation Churn** | Lines Added (`+`) | **`+{telemetry['total_lines_added']:,}`** |",
        f"| | Lines Deleted (`-`) | **`-{telemetry['total_lines_deleted']:,}`** |",
        f"| | Net Line Delta | `{telemetry['total_net_lines']:+,}` |",
        f"| | Total Modified Lines (`+` & `-`) | `{telemetry['total_lines_modified']:,}` |",
        f"| | Mutation Edit Hunks Applied | `{telemetry['total_edit_hunks']:,}` |",
        f"| | Successful Code Evolutions | `{telemetry['total_mutation_events']:,}` |",
        "",
    ]

    # Model Breakdown table
    if telemetry.get("model_breakdown"):
        lines.extend([
            "### LLM Model Consumption Breakdown",
            "",
            "| Model Name | API Calls | Prompt Tokens | Completion Tokens | Total Tokens |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ])
        for m_name, m_data in telemetry["model_breakdown"].items():
            lines.append(
                f"| `{m_name}` | {m_data['calls']:,} | {m_data['prompt_tokens']:,} | {m_data['completion_tokens']:,} | **{m_data['total_tokens']:,}** |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 2. Top Discovered Policies (Ranked by v4 Fitness $J_{v4}$)",
        "",
        "| Rank | Program ID | Island | Iteration | Fitness ($J_{v4}$) | Cost Savings (%) | Max P99 (s) | Mean P99 (s) | Deadline Misses | Worker-Sec | Flapping (Deltas) |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for idx, p in enumerate(top5, 1):
        pid = p.get("program_id", "N/A")[:8]
        island = p.get("island", 0)
        it = p.get("iteration", "N/A")
        fit = float(p.get("combined_score", 0.0))
        cost = float(p.get("cost_savings", 0.0))
        max_p99 = float(p.get("max_p99_latency_s", 0.0))
        mean_p99 = float(p.get("mean_p99_latency_s", max_p99))
        misses = int(p.get("deadline_misses", 0))
        ws = float(p.get("worker_seconds", 0.0))
        deltas = int(p.get("scaling_deltas", 0))

        lines.append(
            f"| **#{idx}** | `{pid}` | Island {island} | Iter {it} | **{fit:.4f}** | **{cost:.2f}%** | **{max_p99:.2f}s** | {mean_p99:.2f}s | {misses} | {ws:.1f} | {deltas} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Reference Baselines Comparison",
        "",
        "| Controller | Cost (ws) | Savings vs Fixed | SLA Misses | Max P99 | Flapping | Fitness ($J_{v4}$) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        f"| **Fixed Capacity Peak** | {BASELINES['fixed_capacity']['worker_seconds']:.1f} | 0.00% | 0 | 5.00s | 205 | {BASELINES['fixed_capacity']['fitness_v4']:.2f} |",
        f"| **InferLine (ACM SoCC '20)** | {BASELINES['inferline']['worker_seconds']:.1f} | 48.88% | 44 | 7.00s | 855 | {BASELINES['inferline']['fitness_v4']:.2f} |",
        f"| **v3 Champion (bbd9b1c2)** | {BASELINES['v3_champion_bbd9b1c2']['worker_seconds']:.1f} | 57.44% | **0** | 6.00s | **228** | **{BASELINES['v3_champion_bbd9b1c2']['fitness_v4']:.2f}** |",
        "",
    ])

    # Per-iteration trace breakdown
    if trace_records:
        lines.extend([
            "---",
            "",
            "## 4. Iteration-by-Iteration Mutation & Token Telemetry (Recent 15 Runs)",
            "",
            "| Iter | Child ID | Island | Model | Tokens (Prompt / Comp / Total) | Code Churn (+ / - / Net) | Fitness ($J_{v4}$) | Max P99 | Status |",
            "| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |",
        ])
        for t in reversed(trace_records[-15:]):
            it = t.get("iteration", 0)
            cid = t.get("child_id", "N/A")[:8]
            isl = t.get("island_id", 0)
            tok = extract_tokens(t)
            diff = compute_code_diff_stats(t.get("parent_code", ""), t.get("child_code", ""))
            cm = t.get("child_metrics", {})
            fit_val = cm.get("combined_score")
            fit_str = f"{fit_val:.2f}" if isinstance(fit_val, (int, float)) else "N/A"
            p99_val = cm.get("max_p99_latency_s")
            p99_str = f"{p99_val:.2f}s" if isinstance(p99_val, (int, float)) else "N/A"
            status = "Accepted" if fit_val is not None and fit_val > -500 else "Pruned"

            lines.append(
                f"| {it} | `{cid}` | Isl {isl} | `{tok['model']}` | {tok['prompt_tokens']} / {tok['completion_tokens']} / **{tok['total_tokens']}** | "
                f"+{diff['lines_added']} / -{diff['lines_deleted']} ({diff['lines_added'] - diff['lines_deleted']:+}) | "
                f"**{fit_str}** | {p99_str} | {status} |"
            )
        lines.append("")

    with open(MD_OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def sync_logs() -> Dict[str, Any]:
    """Main synchronization routine, returns aggregated telemetry."""
    programs = []
    if DB_PROGRAMS_DIR.exists():
        for p_file in sorted(DB_PROGRAMS_DIR.glob("*.json")):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                m = data.get("metrics", {})
                programs.append({
                    "program_id": data.get("id"),
                    "iteration": data.get("iteration"),
                    "island": data.get("island"),
                    "parent_id": data.get("parent_id"),
                    "combined_score": m.get("combined_score"),
                    "cost_savings": m.get("cost_savings"),
                    "churn_stability": m.get("churn_stability"),
                    "tail_safety": m.get("tail_safety"),
                    "deadline_misses": m.get("deadline_misses"),
                    "worker_seconds": m.get("worker_seconds"),
                    "scaling_deltas": m.get("scaling_deltas"),
                    "max_p99_latency_s": m.get("max_p99_latency_s"),
                    "mean_p99_latency_s": m.get("mean_p99_latency_s"),
                    "regimes_completed": m.get("regimes_completed"),
                    "code": data.get("code", ""),
                    "status": "EVALUATED",
                })
            except Exception:
                pass

    llm_calls = load_jsonl(LLM_CALLS_FILE)
    trace_records = load_jsonl(TRACE_FILE)

    telemetry = aggregate_telemetry(llm_calls, trace_records)

    TELEMETRY_JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=2)

    sync_llm_calls_csv(llm_calls, telemetry)
    sync_algorithms_csv(programs, telemetry)
    generate_markdown_dashboard(programs, llm_calls, trace_records, telemetry)

    return telemetry


if __name__ == "__main__":
    t = sync_logs()
    print("V4 Discovery logs and Telemetry synchronized:")
    print(f"  Total Tokens:  {t['total_tokens']:,} (Prompt: {t['total_prompt_tokens']:,}, Comp: {t['total_completion_tokens']:,})")
    print(f"  Code Churn:    +{t['total_lines_added']} / -{t['total_lines_deleted']} lines ({t['total_edit_hunks']} edit hunks)")
    print(f"  Dashboard:     {MD_OUTPUT}")
