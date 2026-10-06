"""
run_evolution_v4.py — Step 7 v4: OpenEvolve Evolutionary Search Launcher (Pareto-Optimal Cost + Low-Tail-Latency)

Role:
    Orchestrates the v4 OpenEvolve multi-island evolutionary search that synthesizes
    the Pareto-Optimal Conformal Autoscaler policy. Initialized from the v3 Champion
    (Program bbd9b1c2, 57.44% savings, 0 misses, 6.00s max P99), directing mutations to
    aggressively squash P99 tail latency down to <= 5.00s while preserving > 55% cost savings
    and zero deadline misses.

Key Enhancements in v4:
    - Auto-Key-Rotation: Automatically tests active Gemini key on startup and seamlessly rotates
      to backup pool (.env.backup) when token/quota exhaustion (HTTP 429) is encountered.
    - Tail Latency Gradient: P99 threshold lowered from 6.0s to 5.0s with steep penalty for tail spikes.
    - Seeded from v3 Champion (bbd9b1c2) ensuring no regression in baseline efficiency.

Gate Stage:    Step 7 v4 (Evolutionary Policy Search - Pareto-Optimal)
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9 & 10

Inputs:
    configs/evolution/openevolve_config_v4.yaml     — master v4 config
    src/continuum_ext/evolution/seed_policy_v4.py   — v3 Champion seed
    src/continuum_ext/evolution/openevolve_evaluator_v4.py — v4 cascade evaluator
    src/continuum_ext/evolution/population_policy.py — directed migration hook

Outputs:
    output/evolved_policy_v4.py                     — best discovered v4 policy
    output/evolution_runs_v4/openevolve_db/         — full MAP-Elites database
    output/evolution_runs_v4/evolution_trace.jsonl  — per-iteration metrics trace
    docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md     — real-time markdown dashboard

AGENTS.md Compliance:
    Rule #1 — Version immutability: runs v4 search without altering v1/v2/v3 artifacts.
    Rule #2 — Config loaded dynamically from YAML; zero hardcoded parameters.
    Rule #3 — Runs exclusively via ./.venv/bin/python.
    Rule #4 — Self-documenting header with role, inputs, outputs.
    Rule #5 — Uses openevolve.OpenEvolve directly.

Usage:
    ./.venv/bin/python scratch/run_evolution_v4.py [--iterations N] [--resume] [--reset] [--dry-run]
"""

import argparse
import asyncio
import logging
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATH BOOTSTRAP
# ─────────────────────────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = WORKSPACE_ROOT / "src"
CONTINUUM_SRC = WORKSPACE_ROOT / "clones" / "ContinuumBench" / "src"
SCRATCH_PATH = WORKSPACE_ROOT / "scratch"
SCRIPTS_PATH = WORKSPACE_ROOT / "scripts"

for p in [str(SRC_PATH), str(CONTINUUM_SRC), str(SCRATCH_PATH), str(SCRIPTS_PATH), str(WORKSPACE_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Bootstrap .env variables
_env_file = WORKSPACE_ROOT / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import openevolve
from openevolve import OpenEvolve
from openevolve.config import Config
from continuum_ext.evolution.population_policy import custom_population_strategy

try:
    from scripts.rotate_api_key import (
        DEFAULT_BACKUP_FILE,
        DEFAULT_ENV_FILE,
        get_active_key,
        mask_key,
        test_api_key,
        find_first_working_key,
    )
    ROTATOR_AVAILABLE = True
except Exception:
    ROTATOR_AVAILABLE = False

CONFIG_PATH = WORKSPACE_ROOT / "configs" / "evolution" / "openevolve_config_v4.yaml"
SEED_POLICY_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "seed_policy_v4.py"
EVALUATOR_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "openevolve_evaluator_v4.py"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v4"
BEST_POLICY_OUTPUT = WORKSPACE_ROOT / "output" / "evolved_policy_v4.py"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_evolution_v4")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch OpenEvolve v4 Pareto-Optimal evolutionary policy search."
    )
    parser.add_argument(
        "--iterations", type=int, default=None,
        help="Override max_iterations from config (default: use config value)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from existing checkpoint in output/evolution_runs_v4/openevolve_db/",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Safely archive existing database and checkpoints to start from iteration 0.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run 2 iterations only to validate the full pipeline end-to-end.",
    )
    return parser.parse_args()


def ensure_healthy_api_key():
    """Validates the active Gemini API key, auto-rotating from backup pool if exhausted."""
    active_key = os.environ.get("GEMINI_API_KEY")
    if not active_key and _env_file.exists():
        if ROTATOR_AVAILABLE:
            active_key = get_active_key(DEFAULT_ENV_FILE)
            if active_key:
                os.environ["GEMINI_API_KEY"] = active_key

    if not active_key:
        logger.warning("No active GEMINI_API_KEY detected in environment or .env.")

    if ROTATOR_AVAILABLE and DEFAULT_BACKUP_FILE.exists():
        logger.info(f"Checking health of active key: [{mask_key(active_key)}]")
        healthy, status_msg = test_api_key(active_key) if active_key else (False, "No key")
        if healthy:
            logger.info(f"Active key verified healthy: {status_msg}")
        else:
            logger.warning(f"Active key unhealthy ({status_msg}). Auto-scanning backup pool...")
            try:
                idx, total, masked = find_first_working_key(DEFAULT_BACKUP_FILE, DEFAULT_ENV_FILE)
                new_key = get_active_key(DEFAULT_ENV_FILE)
                if new_key:
                    os.environ["GEMINI_API_KEY"] = new_key
                    logger.info(f"Auto-selected working key #{idx}/{total} [{masked}]")
            except Exception as e:
                logger.error(f"Auto-key-rotation failed: {e}")


def validate_prerequisites():
    errors = []

    if not CONFIG_PATH.exists():
        errors.append(f"Missing config: {CONFIG_PATH}")
    if not SEED_POLICY_PATH.exists():
        errors.append(f"Missing seed policy: {SEED_POLICY_PATH}")
    if not EVALUATOR_PATH.exists():
        errors.append(f"Missing evaluator: {EVALUATOR_PATH}")

    try:
        import openevolve
        logger.info(f"OpenEvolve version: {openevolve.__version__}")
    except ImportError:
        errors.append("OpenEvolve not installed in .venv.")

    suites_dir = WORKSPACE_ROOT / "configs" / "suites"
    required_suites = [
        "suite1_flat", "suite1_spike", "suite1_burst", "suite1_ramp",
        "suite1_zero_begin", "suite1_zero_terminal",
        "suite2_shock", "suite2_recovery", "suite2_compound_stress",
        "suite2_compound_relief", "suite2_decoupled_opposing", "suite2_storm",
        "suite3_azure",
    ]
    for suite in required_suites:
        cfg = suites_dir / f"{suite}.yaml"
        if not cfg.exists():
            errors.append(f"Missing suite config: {cfg}")

    ensure_healthy_api_key()

    if not os.environ.get("GEMINI_API_KEY"):
        errors.append(
            "GEMINI_API_KEY is not set in environment or .env. "
            "Please configure .env or .env.backup before running evolution."
        )

    if errors:
        logger.error("Prerequisites validation FAILED:")
        for e in errors:
            logger.error(f"  x {e}")
        sys.exit(1)

    logger.info("Prerequisites validated successfully.")


def export_best_policy(evolve_instance: OpenEvolve):
    try:
        best = evolve_instance.database.get_best_program()
        if not best:
            logger.warning("No programs in database — cannot export best policy.")
            return

        fitness = best.metrics.get("combined_score", float("-inf"))
        cost_val = best.metrics.get("cost_savings", "N/A")
        cost_str = f"{cost_val:.2f}%" if isinstance(cost_val, (int, float)) else str(cost_val)
        p99_val = best.metrics.get("max_p99_latency_s", "N/A")
        p99_str = f"{p99_val:.2f}s" if isinstance(p99_val, (int, float)) else str(p99_val)

        provenance = f'''"""
evolved_policy_v4.py — Step 7 v4 Output: Discovered Pareto-Optimal Conformal Autoscaler Policy

Role:
    Global Champion policy discovered by OpenEvolve v4 evolutionary search
    optimizing Pareto-Optimal objective (Cost-Supreme with P99 tail optimization <= 5.0s).

Provenance:
    Program ID:           {best.id}
    Discovered In:        Iteration {best.iteration} (Island {best.island})
    Parent ID:            {best.parent_id}
    Search configuration: configs/evolution/openevolve_config_v4.yaml
    Seed program:         src/continuum_ext/evolution/seed_policy_v4.py (from bbd9b1c2)
    Evaluator:            src/continuum_ext/evolution/openevolve_evaluator_v4.py
    MAP-Elites archive:   output/evolution_runs_v4/openevolve_db/

Performance (Authoritative 13-Regime ContinuumBench Benchmark):
    Fitness J_v4 (combined_score): {fitness:.4f}
    Cost savings vs Fixed:         {cost_str}
    Max P99 Tail Latency:          {p99_str}
    Deadline misses:               {best.metrics.get("deadline_misses", "N/A")}
    Worker-seconds:                {best.metrics.get("worker_seconds", "N/A")}
    Scaling deltas:                {best.metrics.get("scaling_deltas", "N/A")}

AGENTS.md Compliance:
    Rule #1 — Saved as new versioned artifact (evolved_policy_v4.py).
    Rule #2 — Decoupled Linkage & Zero Hardcoding.
    Rule #3 — Runs exclusively under ./.venv/bin/python.
    Rule #4 — Self-documenting with full header docstring and inline logic.
"""

'''
        evolved_source = provenance + best.code
        BEST_POLICY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(BEST_POLICY_OUTPUT, "w") as f:
            f.write(evolved_source)

        logger.info(f"Best policy exported to {BEST_POLICY_OUTPUT}")
        logger.info(f"  Fitness J_v4:    {fitness:.4f}")
        logger.info(f"  Cost savings:    {cost_str}")
        logger.info(f"  Max P99 Tail:    {p99_str}")
        logger.info(f"  Deadline misses: {best.metrics.get('deadline_misses', 'N/A')}")
        logger.info(f"  Worker-seconds:  {best.metrics.get('worker_seconds', 'N/A')}")

    except Exception as e:
        logger.error(f"Failed to export best policy: {e}")


def main():
    args = parse_args()

    logger.info("=" * 70)
    logger.info("STEP 7 v4: OpenEvolve Pareto-Optimal (Cost + Tail Latency) Search")
    logger.info(f"  Config:    {CONFIG_PATH}")
    logger.info(f"  Seed:      {SEED_POLICY_PATH}")
    logger.info(f"  Evaluator: {EVALUATOR_PATH}")
    logger.info(f"  Output:    {EVOLUTION_OUTPUT_DIR}")
    logger.info("=" * 70)

    validate_prerequisites()

    config = Config.from_yaml(CONFIG_PATH)

    if args.iterations is not None:
        config.max_iterations = args.iterations
        logger.info(f"Overriding max_iterations -> {config.max_iterations}")

    if args.dry_run:
        config.max_iterations = 2
        config.checkpoint_interval = 1
        logger.info("DRY RUN mode: 2 iterations only")

    if args.reset:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_dir = EVOLUTION_OUTPUT_DIR / f"archive_reset_{timestamp}"
        items_to_archive = [
            EVOLUTION_OUTPUT_DIR / "checkpoints",
            EVOLUTION_OUTPUT_DIR / "openevolve_db",
            EVOLUTION_OUTPUT_DIR / "evolution_trace.jsonl",
            EVOLUTION_OUTPUT_DIR / "evaluator_checks.jsonl",
            EVOLUTION_OUTPUT_DIR / "algorithm_performance_log.csv",
            EVOLUTION_OUTPUT_DIR / "llm_calls.jsonl",
            EVOLUTION_OUTPUT_DIR / "llm_calls_log.csv",
        ]
        if any(item.exists() for item in items_to_archive):
            archive_dir.mkdir(parents=True, exist_ok=True)
            for item in items_to_archive:
                if item.exists():
                    shutil.move(str(item), str(archive_dir / item.name))
            logger.info(f"Evolution state reset. Previous run archived to {archive_dir}")

    EVOLUTION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Instantiating OpenEvolve v4 with asymmetric island topology...")
    evolve = OpenEvolve(
        initial_program_path=str(SEED_POLICY_PATH),
        evaluation_file=str(EVALUATOR_PATH),
        config=config,
        output_dir=str(EVOLUTION_OUTPUT_DIR),
        population_strategy=custom_population_strategy,
    )

    orig_save_checkpoint = evolve._save_checkpoint

    def _sync_logs_callback(iteration: int):
        orig_save_checkpoint(iteration)
        try:
            from log_discovery_v4 import sync_logs
            t = sync_logs()
            logger.info(
                f"📊 [Telemetry Iter {iteration}]: Tokens: {t['total_tokens']:,} "
                f"(Prompt: {t['total_prompt_tokens']:,}, Comp: {t['total_completion_tokens']:,}) | "
                f"Code Churn: +{t['total_lines_added']}/-{t['total_lines_deleted']} lines ({t['total_edit_hunks']} edit hunks)"
            )
        except Exception as err:
            logger.warning(f"Could not sync discovery logs at iteration {iteration}: {err}")

    evolve._save_checkpoint = _sync_logs_callback

    logger.info("Launching evolutionary search...")
    logger.info(f"Target iterations: {config.max_iterations}")

    try:
        checkpoint_path = None
        if args.resume:
            checkpoints_dir = EVOLUTION_OUTPUT_DIR / "checkpoints"
            if checkpoints_dir.exists():
                ckpts = sorted(
                    [d for d in checkpoints_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint_")],
                    key=lambda p: int(p.name.split("_")[-1]) if p.name.split("_")[-1].isdigit() else -1,
                )
                if ckpts:
                    checkpoint_path = str(ckpts[-1])
                    logger.info(f"Resuming evolution from latest checkpoint: {checkpoint_path}")
                else:
                    logger.warning(f"No checkpoints found in {checkpoints_dir}. Starting fresh.")

        asyncio.run(evolve.run(iterations=config.max_iterations, checkpoint_path=checkpoint_path))

    except KeyboardInterrupt:
        logger.info("Evolution interrupted by user (Ctrl+C). Saving best policy...")
    except Exception as e:
        logger.error(f"Evolution failed with exception: {e}")
        raise
    finally:
        logger.info("Exporting best discovered policy...")
        export_best_policy(evolve)

        try:
            from log_discovery_v4 import sync_logs
            t = sync_logs()
            logger.info("=" * 70)
            logger.info("CUMULATIVE EVOLUTION TELEMETRY SUMMARY:")
            logger.info(f"  Total LLM Calls:       {t['total_llm_calls']:,}")
            logger.info(f"  Total Prompt Tokens:   {t['total_prompt_tokens']:,}")
            logger.info(f"  Total Comp Tokens:     {t['total_completion_tokens']:,}")
            logger.info(f"  Total Tokens Consumed: {t['total_tokens']:,}")
            logger.info(f"  Code Lines Added:      +{t['total_lines_added']:,}")
            logger.info(f"  Code Lines Deleted:    -{t['total_lines_deleted']:,}")
            logger.info(f"  Net Line Delta:        {t['total_net_lines']:+,}")
            logger.info(f"  Total Edit Hunks:      {t['total_edit_hunks']:,}")
            logger.info("=" * 70)
        except Exception as e:
            logger.warning(f"Could not update discovery logs: {e}")

    logger.info("=" * 70)
    logger.info("STEP 7 v4 RUN COMPLETED")
    logger.info(f"Best policy:    {BEST_POLICY_OUTPUT}")
    logger.info(f"Discovery Log:  docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md")
    logger.info(f"Database:       {config.database.db_path}")
    logger.info(f"Trace:          {config.evolution_trace.output_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
