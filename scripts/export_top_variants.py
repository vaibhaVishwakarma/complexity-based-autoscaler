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
FIXED_CAPACITY_WORKER_SECONDS = 27_900.0


def get_evolution_paths(version: str = "auto") -> tuple[Path, Path, Path, str]:
    if version == "auto":
        v5_dir = WORKSPACE_ROOT / "output" / "evolution_runs_v5"
        v3_dir = WORKSPACE_ROOT / "output" / "evolution_runs_v3"
        v2_dir = WORKSPACE_ROOT / "output" / "evolution_runs_v2"
        if (v5_dir / "openevolve_db").exists() or (v5_dir / "evolution_trace.jsonl").exists():
            chosen_dir = v5_dir
            ver_label = "v5 Realism-Aware"
        elif (v3_dir / "openevolve_db").exists() or (v3_dir / "evolution_trace.jsonl").exists():
            chosen_dir = v3_dir
            ver_label = "v3 Cost-Supreme"
        else:
            chosen_dir = v2_dir
            ver_label = "v2 Cost-First"
    elif version in ("5", "v5"):
        chosen_dir = WORKSPACE_ROOT / "output" / "evolution_runs_v5"
        ver_label = "v5 Realism-Aware"
    elif version in ("3", "v3"):
        chosen_dir = WORKSPACE_ROOT / "output" / "evolution_runs_v3"
        ver_label = "v3 Cost-Supreme"
    else:
        chosen_dir = WORKSPACE_ROOT / "output" / "evolution_runs_v2"
        ver_label = "v2 Cost-First"

    db_dir = chosen_dir / "openevolve_db" / "programs"
    trace_file = chosen_dir / "evolution_trace.jsonl"
    return chosen_dir, db_dir, trace_file, ver_label


def load_programs_from_db(db_programs_dir: Path) -> List[Dict[str, Any]]:
    """Loads all evaluated programs from the MAP-Elites JSON files."""
    programs = []
    if not db_programs_dir.exists():
        return programs

    for json_path in db_programs_dir.glob("*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "code" in data and "metrics" in data:
                    programs.append(data)
        except Exception:
            continue
    return programs


def load_programs_from_trace(trace_file: Path) -> List[Dict[str, Any]]:
    """Fallback: loads programs from evolution_trace.jsonl if DB directory is missing."""
    programs = []
    if not trace_file.exists():
        return programs

    with open(trace_file, "r", encoding="utf-8") as f:
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


def export_top_variants(top_n: int = 30, clean_sim_logs: bool = False, version: str = "auto"):
    evolution_dir, db_programs_dir, trace_file, ver_label = get_evolution_paths(version)
    output_dir = WORKSPACE_ROOT / "output" / f"top{top_n}_variants"
    tarball_output = WORKSPACE_ROOT / "evolution_v5_results_bundle.tar.gz"

    print("=" * 70)
    print(f" EXPORTING TOP {top_n} EVOLVED VARIANTS ({ver_label})")
    print(f" Source DB: {db_programs_dir}")
    print(f" Output Dir: {output_dir}")
    print("=" * 70)

    # 1. Load candidate programs
    programs = load_programs_from_db(db_programs_dir)
    if not programs:
        print("  -> Notice: No programs found in openevolve_db. Loading from trace...")
        programs = load_programs_from_trace(trace_file)

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
    print(f"  ✓ Selected top {len(top_variants)} unique programs (highest fitness).")

    # 3. Create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 4. Export each top variant as a standalone Python file
    leaderboard_rows = []

    for rank, p in enumerate(top_variants, 1):
        pid = p.get("id", f"program_{rank}")
        pid_short = pid[:8]
        m = p.get("metrics", {})
        score = float(m.get("combined_score", 0.0))
        cost_savings = float(m.get("cost_savings", 0.0))
        canon_misses = int(m.get("canonical_misses", m.get("deadline_misses", 0)))
        shock_misses = int(m.get("realism_misses", 0))
        resilience = float(m.get("realism_resilience", max(0.0, 3000.0 - shock_misses)))
        p99 = float(m.get("max_p99_latency_s", 0.0))
        wsec = float(m.get("worker_seconds", 0.0))
        deltas = int(m.get("scaling_deltas", 0))
        completed = int(m.get("completed_requests", 0))

        score_tag = f"{score:+.2f}".replace(".", "p")
        filename = f"rank{rank:02d}_fit{score_tag}_id{pid_short}.py"
        file_path = output_dir / filename

        provenance_header = f'''"""
Policy Rank:        #{rank} of {len(top_variants)}
Program ID:         {pid}
Discovered In:      Iteration {p.get("iteration_found", "N/A")}
Fitness (Score):    {score:+.4f}

Performance Profile:
  - Cost Savings:         {cost_savings:.2f}% vs Fixed Capacity Peak (27,900 ws)
  - Canonical Cost:       {wsec:.1f} worker-seconds (Target: beat InferLine 14,261 ws)
  - Canonical Misses:     {canon_misses} (Strict Floor: 0 misses)
  - Realism Shock Misses: {shock_misses} (Extreme T_init in [15s, 50s, 150s, 250s, 300s])
  - Realism Resilience:   {resilience:.1f}
  - Max P99 Latency:      {p99:.2f}s
  - Scaling Deltas:       {deltas} deltas

Mutation Rationale:
  {(p.get("changes_description") or "Initial seed candidate").replace(chr(10), " ")}
"""

'''
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(provenance_header + p.get("code", ""))

        leaderboard_rows.append({
            "rank": rank,
            "filename": filename,
            "program_id": pid_short,
            "fitness_score": round(score, 4),
            "cost_savings_%": round(cost_savings, 2),
            "worker_seconds": round(wsec, 1),
            "canon_misses": canon_misses,
            "shock_misses": shock_misses,
            "realism_resilience": round(resilience, 1),
            "max_p99_s": round(p99, 3),
            "scaling_deltas": deltas,
            "beats_inferline_cost": wsec < 14261.0 and wsec > 0,
            "zero_canon_misses": canon_misses == 0,
        })

    # 5. Write Leaderboard CSV
    csv_path = output_dir / f"TOP{top_n}_LEADERBOARD.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(leaderboard_rows[0].keys()))
        writer.writeheader()
        writer.writerows(leaderboard_rows)

    # 6. Write Leaderboard Markdown
    md_path = output_dir / f"TOP{top_n}_LEADERBOARD.md"
    md_lines = [
        f"# Top {len(top_variants)} Discovered Autoscaling Policies ({ver_label})",
        "",
        "Dual-Tier Objective: $J_{\\text{v5}} = \\text{CostSavings\\%} - 100 \\cdot M_{\\text{canon}} - 0.02 \\cdot M_{\\text{shock}} - \\text{ChurnPenalty}$",
        "",
        "| Rank | File | Program ID | Fitness $J$ | Cost Savings | Worker-Sec | Canon Miss | Shock Miss | Resilience | Deltas | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in leaderboard_rows:
        if r["shock_misses"] < 500 and r["zero_canon_misses"]:
            status = "★ Realism Master"
        elif r["beats_inferline_cost"] and r["zero_canon_misses"]:
            status = "✓ Beats InferLine Cost"
        elif r["zero_canon_misses"]:
            status = "✓ Zero Canon Misses"
        else:
            status = "Pareto Candidate"

        md_lines.append(
            f"| {r['rank']} | `{r['filename']}` | `{r['program_id']}` | **{r['fitness_score']:+.2f}** | "
            f"{r['cost_savings_%']:.2f}% | {r['worker_seconds']} ws | {r['canon_misses']} | "
            f"{r['shock_misses']} | {r['realism_resilience']} | {r['scaling_deltas']} | {status} |"
        )
    md_lines.append("")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"  ✓ Exported {len(top_variants)} policies into {output_dir}")
    print(f"  ✓ Created {csv_path.name} and {md_path.name}")

    # 7. Copy auxiliary lightweight reporting files if they exist
    aux_files = [
        WORKSPACE_ROOT / "output" / "evolved_policy_v5.py",
        WORKSPACE_ROOT / "output" / "evolved_policy_v3.py",
        WORKSPACE_ROOT / "output" / "evolved_policy_v2.py",
        WORKSPACE_ROOT / "docs" / "EVOLVED_ALGORITHMS_DISCOVERY_LOG_V5.md",
        WORKSPACE_ROOT / "docs" / "EVOLVED_ALGORITHMS_DISCOVERY_LOG_V3.md",
        evolution_dir / "algorithm_performance_log.csv",
        evolution_dir / "llm_calls_log.csv",
        evolution_dir / "token_churn_summary.json",
        evolution_dir / "evolution_trace.jsonl",
    ]
    for af in aux_files:
        if af.exists():
            shutil.copy(str(af), str(output_dir / af.name))
            print(f"  ✓ Bundled auxiliary file: {af.name}")

    # 8. Create compressed tarball (< 3MB)
    with tarfile.open(tarball_output, "w:gz") as tar:
        tar.add(str(output_dir), arcname=f"top{top_n}_variants")

    tar_size_kb = tarball_output.stat().st_size / 1024
    tar_size_mb = tar_size_kb / 1024
    size_str = f"{tar_size_mb:.2f} MB" if tar_size_mb >= 1.0 else f"{tar_size_kb:.1f} KB"
    print("=" * 70)
    print(f" PACKAGING COMPLETE!")
    print(f"  Output Tarball: {tarball_output}")
    print(f"  Tarball Size:   {size_str} (lightweight bundle for download!)")
    print("=" * 70)

    # 9. Optional: Clean disposable simulation logs if requested
    if clean_sim_logs and evolution_dir.exists():
        print(f"\n[CLEANUP] Cleaning temporary simulation directories in {evolution_dir.name}...")
        freed_bytes = 0
        for item in evolution_dir.iterdir():
            if item.is_dir() and (item.name.startswith("tmp") or item.name.startswith("seed_policy") or "suite" in item.name):
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
    parser.add_argument("--top", type=int, default=30, help="Number of top variants to export (default: 30)")
    parser.add_argument("--clean-sim-logs", action="store_true", help="Delete disposable simulation folders to free disk space")
    parser.add_argument("--version", type=str, default="auto", choices=["auto", "2", "v2", "3", "v3", "5", "v5"], help="Run version to export (default: auto)")
    args = parser.parse_args()

    export_top_variants(top_n=args.top, clean_sim_logs=args.clean_sim_logs, version=args.version)
