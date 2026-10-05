"""
run_evolution_v3.py — Step 7 v3: OpenEvolve Cost-Supreme Evolutionary Policy Search Launcher

Role:
    Orchestrates the v3 OpenEvolve multi-island evolutionary search that synthesizes
    the Cost-Supreme Conformal Autoscaler policy. Initialized from the v2 Cost Champion
    (Program 4a7ccfe9, 53.05% savings, 0 misses), directing mutations to break the
    55-60% cost barrier while maintaining zero deadline misses and safe tail latency.

Gate Stage:    Step 7 v3 (Evolutionary Policy Search - Cost-Supreme)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md Section 7
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Step 7 & Section 9

Inputs:
    configs/evolution/openevolve_config_v3.yaml     — master v3 config
    src/continuum_ext/evolution/seed_policy_v3.py   — v2 Cost Champion seed
    src/continuum_ext/evolution/openevolve_evaluator_v3.py — v3 cascade evaluator
    src/continuum_ext/evolution/population_policy.py — directed migration hook

Outputs:
    output/evolved_policy_v3.py                     — best discovered v3 policy
    output/evolution_runs_v3/openevolve_db/         — full MAP-Elites database
    output/evolution_runs_v3/evolution_trace.jsonl  — per-iteration metrics trace
    docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V3.md     — real-time markdown dashboard

AGENTS.md Compliance:
    Rule #1 — Version immutability: runs v3 search without altering v1/v2 artifacts.
    Rule #2 — Config loaded dynamically from YAML; zero hardcoded parameters.
    Rule #3 — Runs exclusively via ./.venv/bin/python.
    Rule #4 — Self-documenting header with role, inputs, outputs.
    Rule #5 — Uses openevolve.OpenEvolve directly.

Usage:
    ./.venv/bin/python scratch/run_evolution_v3.py [--iterations N] [--resume] [--reset] [--dry-run]
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

_env_file = WORKSPACE_ROOT / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

for p in [str(SRC_PATH), str(CONTINUUM_SRC), str(SCRATCH_PATH), str(WORKSPACE_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
import openevolve
from openevolve import OpenEvolve
from openevolve.config import Config
from continuum_ext.evolution.population_policy import custom_population_strategy

CONFIG_PATH = WORKSPACE_ROOT / "configs" / "evolution" / "openevolve_config_v3.yaml"
SEED_POLICY_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "seed_policy_v3.py"
EVALUATOR_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "openevolve_evaluator_v3.py"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v3"
BEST_POLICY_OUTPUT = WORKSPACE_ROOT / "output" / "evolved_policy_v3.py"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_evolution_v3")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch OpenEvolve v3 Cost-Supreme evolutionary policy search."
    )
    parser.add_argument(
        "--iterations", type=int, default=None,
        help="Override max_iterations from config (default: use config value)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from existing checkpoint in output/evolution_runs_v3/openevolve_db/",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Safely archive existing database and checkpoints to start from iteration 0.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run 3 iterations only to validate the full pipeline end-to-end.",
    )
    return parser.parse_args()


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

    if not os.environ.get("GEMINI_API_KEY"):
        errors.append(
            "GEMINI_API_KEY is not set in environment. "
            "Please export your API key before running evolution: export GEMINI_API_KEY='...'"
        )

    if errors:
        logger.error("Prerequisites validation FAILED:")
        for e in errors:
            logger.error(f"  ✗ {e}")
        sys.exit(1)

    logger.info("Prerequisites validated ✓")


def export_best_policy(evolve_instance: OpenEvolve):
    try:
        best = evolve_instance.database.get_best_program()
        if not best:
            logger.warning("No programs in database — cannot export best policy.")
            return

        fitness = best.metrics.get("combined_score", float("-inf"))
        cost_val = best.metrics.get("cost_savings", "N/A")
        cost_str = f"{cost_val:.2f}%" if isinstance(cost_val, (int, float)) else str(cost_val)

        provenance = f'''"""
evolved_policy_v3.py — Step 7 v3 Output: Discovered Cost-Supreme Conformal Autoscaler Policy

Role:
    Best policy discovered by OpenEvolve v3 evolutionary search across
    {evolve_instance.config.max_iterations} iterations optimizing Cost-Supreme with 6.0s P99 baseline.

Provenance:
    Search configuration: configs/evolution/openevolve_config_v3.yaml
    Seed program:         src/continuum_ext/evolution/seed_policy_v3.py (from 4a7ccfe9)
    Evaluator:            src/continuum_ext/evolution/openevolve_evaluator_v3.py
    MAP-Elites archive:   output/evolution_runs_v3/openevolve_db/

Performance (authoritative 13-regime benchmark):
    Fitness J_v3 (combined_score): {fitness:.4f}
    Cost savings vs Fixed:         {cost_str}
    Churn stability:               {best.metrics.get("churn_stability", "N/A")}
    Tail safety:                   {best.metrics.get("tail_safety", "N/A")}
    Deadline misses:               {best.metrics.get("deadline_misses", "N/A")}
    Worker-seconds:                {best.metrics.get("worker_seconds", "N/A")}
    Scaling deltas:                {best.metrics.get("scaling_deltas", "N/A")}

AGENTS.md Compliance:
    Rule #1 — Saved as new versioned artifact (evolved_policy_v3.py).
"""

'''
        evolved_source = provenance + best.code
        BEST_POLICY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(BEST_POLICY_OUTPUT, "w") as f:
            f.write(evolved_source)

        logger.info(f"Best policy exported to {BEST_POLICY_OUTPUT}")
        logger.info(f"  Fitness J_v3:    {fitness:.4f}")
        logger.info(f"  Cost savings:    {cost_str}")
        logger.info(f"  Deadline misses: {best.metrics.get('deadline_misses', 'N/A')}")
        logger.info(f"  Worker-seconds:  {best.metrics.get('worker_seconds', 'N/A')}")

    except Exception as e:
        logger.error(f"Failed to export best policy: {e}")


def main():
    args = parse_args()

    logger.info("=" * 70)
    logger.info("STEP 7 v3: OpenEvolve Cost-Supreme Conformal Autoscaler Search")
    logger.info(f"  Config:    {CONFIG_PATH}")
    logger.info(f"  Seed:      {SEED_POLICY_PATH}")
    logger.info(f"  Evaluator: {EVALUATOR_PATH}")
    logger.info(f"  Output:    {EVOLUTION_OUTPUT_DIR}")
    logger.info("=" * 70)

    validate_prerequisites()

    config = Config.from_yaml(CONFIG_PATH)

    if args.iterations is not None:
        config.max_iterations = args.iterations
        logger.info(f"Overriding max_iterations → {config.max_iterations}")

    if args.dry_run:
        config.max_iterations = 3
        config.checkpoint_interval = 1
        logger.info("DRY RUN mode: 3 iterations only")

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

    logger.info("Instantiating OpenEvolve v3 with asymmetric island topology...")
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
            from log_discovery_v3 import sync_logs
            sync_logs()
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
            from log_discovery_v3 import sync_logs
            sync_logs()
        except Exception as e:
            logger.warning(f"Could not update discovery logs: {e}")

    logger.info("=" * 70)
    logger.info("STEP 7 v3 RUN COMPLETED")
    logger.info(f"Best policy:    {BEST_POLICY_OUTPUT}")
    logger.info(f"Discovery Log:  docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V3.md")
    logger.info(f"Database:       {config.database.db_path}")
    logger.info(f"Trace:          {config.evolution_trace.output_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
