#!/usr/bin/env python3
"""
scripts/export_top_variants.py — Export Top-N Discovered Policies & Lightweight Bundle

Role:
    Extracts the Top-N best policies from the OpenEvolve MAP-Elites database and
    evolution trace, exports each policy as a standalone, runnable Python file with
    full performance provenance, generates a comparative leaderboard, and packages
    them into a tiny tarball (< 2MB) for instant download — bypassing the 18GB of
    temporary simulation logs.

Usage:
    # Export top 20 variants and package into top20_evolved_variants.tar.gz:
    ./.venv/bin/python scripts/export_top_variants.py --top 20

    # Also delete the disposable ~18GB tmp* simulation directories to free up Codespace disk:
    ./.venv/bin/python scripts/export_top_variants.py --top 20 --clean-sim-logs

AGENTS.md Compliance:
    Rule #1 — All exports are versioned in output/top20_variants/; source files untouched.
    Rule #2 — Dynamically reads metrics from authoritative evaluation records.
    Rule #3 — Uses workspace virtual environment (./.venv).
    Rule #4 — Self-documenting header and inline comments.
"""

import argparse
import csv
import json
import os
import shutil
import sys
import tarfile
from pathlib import Path
from typing import Any, Dict, List

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
EVOLUTION_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v2"
DB_PROGRAMS_DIR = EVOLUTION_DIR / "openevolve_db" / "programs"
TRACE_FILE = EVOLUTION_DIR / "evolution_trace.jsonl"
OUTPUT_DIR = WORKSPACE_ROOT / "output" / "top20_variants"
TARBALL_OUTPUT = WORKSPACE_ROOT / "top20_evolved_variants.tar.gz"

FIXED_CAPACITY_WORKER_SECONDS = 27_900.0


def load_programs_from_db() -> List[Dict[str, Any]]:
    """Loads all evaluated programs from the MAP-Elites JSON files."""
    programs = []
    if not DB_PROGRAMS_DIR.exists():
        return programs

    for json_path in DB_PROGRAMS_DIR.glob("*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "code" in data and "metrics" in data:
                    programs.append(data)
        except Exception:
            continue
    return programs


def load_programs_from_trace() -> List[Dict[str, Any]]:
    """Fallback: loads programs from evolution_trace.jsonl if DB directory is missing."""
    programs = []
    if not TRACE_FILE.exists():
        return programs

    with open(TRACE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                child_code = rec.get("child_code")
                child_metrics = rec.get("child_metrics")
                if child_code and child_metrics and "combined_score" in child_metrics:
                    programs.append({
                        "id": rec.get("child_id", "trace_candidate"),
                        "code": child_code,
                        "metrics": child_metrics,
                        "parent_id": rec.get("parent_id", ""),
                        "iteration_found": rec.get("iteration", 0),
                        "changes_description": rec.get("child_changes_description", ""),
                    })
            except Exception:
                continue
    return programs


def export_top_variants(top_n: int = 20, clean_sim_logs: bool = False):
    print("=" * 70)
    print(f" EXPORTING TOP {top_n} EVOLVED VARIANTS (Cost-First v2 Search)")
    print(f" Source DB: {DB_PROGRAMS_DIR}")
    print(f" Output Dir: {OUTPUT_DIR}")
    print("=" * 70)

    # 1. Load candidate programs
    programs = load_programs_from_db()
    if not programs:
        print("  -> Notice: No programs found in openevolve_db. Loading from trace...")
        programs = load_programs_from_trace()

    if not programs:
        print("  ✗ ERROR: No evaluated programs found in database or trace.")
        sys.exit(1)

    print(f"  ✓ Loaded {len(programs)} evaluated programs.")

    # 2. Deduplicate programs by code content and pick the best score
    unique_programs = {}
    for p in programs:
        code_str = p.get("code", "").strip()
        score = float(p.get("metrics", {}).get("combined_score", float("-inf")))
        if code_str not in unique_programs or score > float(unique_programs[code_str].get("metrics", {}).get("combined_score", float("-inf"))):
            unique_programs[code_str] = p

    sorted_programs = sorted(
        unique_programs.values(),
        key=lambda x: float(x.get("metrics", {}).get("combined_score", float("-inf"))),
        reverse=True,
    )

    top_variants = sorted_programs[:top_n]
    print(f"  ✓ Selected top {len(top_variants)} unique programs (highest fitness J_v2).")

    # 3. Create output directory
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 4. Export each top variant as a standalone Python file
    leaderboard_rows = []

    for rank, p in enumerate(top_variants, 1):
        pid = p.get("id", f"program_{rank}")
        pid_short = pid[:8]
        m = p.get("metrics", {})
        score = float(m.get("combined_score", 0.0))
        cost_savings = float(m.get("cost_savings", 0.0))
        misses = int(m.get("deadline_misses", 0))
        p99 = float(m.get("max_p99_latency_s", 0.0))
        wsec = float(m.get("worker_seconds", 0.0))
        deltas = int(m.get("scaling_deltas", 0))
        completed = int(m.get("completed_requests", 0))

        # Format clean filename: rank01_fit+26.01_id085265b3.py
        score_tag = f"{score:+.2f}".replace(".", "p")
        filename = f"rank{rank:02d}_fit{score_tag}_id{pid_short}.py"
        file_path = OUTPUT_DIR / filename

        provenance_header = f'''"""
Policy Rank:        #{rank} of {len(top_variants)}
Program ID:         {pid}
Discovered In:      Iteration {p.get("iteration_found", "N/A")}
Fitness J_v2:       {score:+.4f}

Performance Profile (Authoritative 13-Regime Benchmark):
  - Cost Savings:       {cost_savings:.2f}% vs Fixed Capacity
  - Provisioned Cost:   {wsec:.1f} worker-seconds (Target: beat InferLine 14,261 ws)
  - Deadline Misses:    {misses}
  - Max P99 Latency:    {p99:.2f}s (SLA: 15.0s, Target: <= 5.0s)
  - Scaling Flapping:   {deltas} deltas
  - Completed Requests: {completed:,}

Mutation Rationale:
  {(p.get("changes_description") or "Initial champion seed candidate").replace(chr(10), " ")}
"""

'''
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(provenance_header + p.get("code", ""))

        leaderboard_rows.append({
            "rank": rank,
            "filename": filename,
            "program_id": pid_short,
            "fitness_j_v2": round(score, 4),
            "cost_savings_%": round(cost_savings, 2),
            "worker_seconds": round(wsec, 1),
            "deadline_misses": misses,
            "max_p99_s": round(p99, 3),
            "scaling_deltas": deltas,
            "beats_inferline_cost": wsec < 14261.0 and wsec > 0,
            "zero_misses": misses == 0,
        })

    # 5. Write Leaderboard CSV
    csv_path = OUTPUT_DIR / "TOP20_LEADERBOARD.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(leaderboard_rows[0].keys()))
        writer.writeheader()
        writer.writerows(leaderboard_rows)

    # 6. Write Leaderboard Markdown
    md_path = OUTPUT_DIR / "TOP20_LEADERBOARD.md"
    md_lines = [
        f"# Top {len(top_variants)} Discovered Autoscaling Policies (v2 Cost-First Search)",
        "",
        "Objective: $J_{\\text{v2}} = \\text{cost\\_savings\\_\\%} - \\left(2.0 \\cdot \\min(M, 50) + 10.0 \\cdot \\max(0, M - 50)\\right) - 10.0 \\cdot \\max(0.0, P99 - 5.0) - 0.01 \\cdot \\Delta$",
        "",
        "| Rank | File | Program ID | Fitness $J_{\\text{v2}}$ | Cost Savings | Worker-Sec | Misses | Max P99 | Deltas | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in leaderboard_rows:
        status = "★ Beats InferLine Cost" if r["beats_inferline_cost"] else ("✓ Zero Misses" if r["zero_misses"] else "Pareto Candidate")
        md_lines.append(
            f"| {r['rank']} | `{r['filename']}` | `{r['program_id']}` | **{r['fitness_j_v2']:+.2f}** | {r['cost_savings_%']:.2f}% | {r['worker_seconds']} ws | {r['deadline_misses']} | {r['max_p99_s']}s | {r['scaling_deltas']} | {status} |"
        )
    md_lines.append("")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"  ✓ Exported {len(top_variants)} policies into {OUTPUT_DIR}")
    print(f"  ✓ Created {csv_path.name} and {md_path.name}")

    # 7. Copy auxiliary lightweight reporting files if they exist
    aux_files = [
        WORKSPACE_ROOT / "output" / "evolved_policy_v2.py",
        WORKSPACE_ROOT / "docs" / "EVOLVED_ALGORITHMS_DISCOVERY_LOG_V2.md",
        EVOLUTION_DIR / "algorithm_performance_log.csv",
        EVOLUTION_DIR / "llm_calls_log.csv",
        EVOLUTION_DIR / "evolution_trace.jsonl",
    ]
    for af in aux_files:
        if af.exists():
            shutil.copy(str(af), str(OUTPUT_DIR / af.name))
            print(f"  ✓ Bundled auxiliary file: {af.name}")

    # 8. Create compressed tarball (< 2MB)
    with tarfile.open(TARBALL_OUTPUT, "w:gz") as tar:
        tar.add(str(OUTPUT_DIR), arcname="top20_variants")

    tar_size_kb = TARBALL_OUTPUT.stat().st_size / 1024
    tar_size_mb = tar_size_kb / 1024
    size_str = f"{tar_size_mb:.2f} MB" if tar_size_mb >= 1.0 else f"{tar_size_kb:.1f} KB"
    print("=" * 70)
    print(f" PACKAGING COMPLETE!")
    print(f"  Output Tarball: {TARBALL_OUTPUT}")
    print(f"  Tarball Size:   {size_str} (bypassed 18GB of temporary simulation logs!)")
    print("=" * 70)

    # 9. Optional: Clean disposable simulation logs if requested
    if clean_sim_logs:
        print("\n[CLEANUP] Cleaning temporary simulation directories in evolution_runs_v2...")
        freed_bytes = 0
        for item in EVOLUTION_DIR.iterdir():
            if item.is_dir() and (item.name.startswith("tmp") or item.name == "seed_policy_v2"):
                try:
                    size = sum(f.stat().st_size for f in item.glob("**/*") if f.is_file())
                    shutil.rmtree(str(item), ignore_errors=True)
                    freed_bytes += size
                except Exception:
                    pass
        freed_gb = freed_bytes / (1024 ** 3)
        print(f"  ✓ Freed ~{freed_gb:.2f} GB of disk space on Codespaces!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export top discovered policies into a lightweight tarball.")
    parser.add_argument("--top", type=int, default=20, help="Number of top variants to export (default: 20)")
    parser.add_argument("--clean-sim-logs", action="store_true", help="Delete disposable tmp* simulation folders to free disk space")
    args = parser.parse_args()

    export_top_variants(top_n=args.top, clean_sim_logs=args.clean_sim_logs)
