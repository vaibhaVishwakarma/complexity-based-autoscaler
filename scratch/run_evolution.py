"""
run_evolution.py — Step 7: OpenEvolve Evolutionary Policy Search Launcher

Role:
    Orchestrates the OpenEvolve multi-island evolutionary search that synthesizes
    the Pareto-optimal Conformal Autoscaler policy. Configures the asymmetric
    island topology, registers the custom population migration strategy, and
    launches the 200-iteration search with checkpointing and best-policy export.

Gate Stage:    Step 7 (Evolutionary Policy Search)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md Section 7
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Step 7

Inputs:
    configs/evolution/openevolve_config.yaml  — all parameters (LLM, cascade, MAP-Elites)
    src/continuum_ext/evolution/seed_policy.py — initial candidate program
    src/continuum_ext/evolution/openevolve_evaluator.py — cascade evaluator
    src/continuum_ext/evolution/population_policy.py — directed migration hook

Outputs:
    output/evolved_policy.py              — best discovered policy (saved on completion)
    output/evolution_runs/openevolve_db/  — full MAP-Elites database with checkpoints
    output/evolution_runs/evolution_trace.jsonl — per-iteration metrics trace

AGENTS.md Compliance:
    Rule #1 — Evolved best policy saved as output/evolved_policy.py (new versioned artifact)
    Rule #2 — Config loaded dynamically from YAML; no hardcoded parameters
    Rule #3 — Runs exclusively via ./.venv/bin/python (not system Python)
    Rule #4 — Self-documenting header with role, inputs, outputs
    Rule #5 — Uses openevolve.OpenEvolve directly; no custom training loop reimplementation

Usage:
    ./.venv/bin/python scratch/run_evolution.py [--iterations N] [--resume]
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATH BOOTSTRAP
# Add workspace src/ to PYTHONPATH so continuum_ext and ContinuumBench are
# importable. This must happen before any project imports.
# ─────────────────────────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = WORKSPACE_ROOT / "src"
CONTINUUM_SRC = WORKSPACE_ROOT / "clones" / "ContinuumBench" / "src"

# Auto-load .env file if present at workspace root
_env_file = WORKSPACE_ROOT / ".env"
if _env_file.exists():
    import os
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

SCRATCH_PATH = WORKSPACE_ROOT / "scratch"
for p in [str(SRC_PATH), str(CONTINUUM_SRC), str(SCRATCH_PATH), str(WORKSPACE_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS (after path bootstrap)
# ─────────────────────────────────────────────────────────────────────────────
import openevolve
from openevolve import OpenEvolve
from openevolve.config import Config

from continuum_ext.evolution.population_policy import custom_population_strategy

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
CONFIG_PATH = WORKSPACE_ROOT / "configs" / "evolution" / "openevolve_config.yaml"
SEED_POLICY_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "seed_policy.py"
EVALUATOR_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "openevolve_evaluator.py"
EVOLUTION_OUTPUT_DIR = WORKSPACE_ROOT / "output" / "evolution_runs"
BEST_POLICY_OUTPUT = WORKSPACE_ROOT / "output" / "evolved_policy.py"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_evolution")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch OpenEvolve evolutionary policy search for Conformal Autoscaler."
    )
    parser.add_argument(
        "--iterations", type=int, default=None,
        help="Override max_iterations from config (default: use config value)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from existing checkpoint in output/evolution_runs/openevolve_db/",
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
    """
    Validates that all required files and configurations exist before launching
    the expensive evolutionary search. Fails fast with clear diagnostics.
    """
    errors = []

    if not CONFIG_PATH.exists():
        errors.append(f"Missing config: {CONFIG_PATH}")
    if not SEED_POLICY_PATH.exists():
        errors.append(f"Missing seed policy: {SEED_POLICY_PATH}")
    if not EVALUATOR_PATH.exists():
        errors.append(f"Missing evaluator: {EVALUATOR_PATH}")

    # Verify OpenEvolve is installed in the workspace venv
    try:
        import openevolve
        logger.info(f"OpenEvolve version: {openevolve.__version__}")
    except ImportError:
        errors.append("OpenEvolve not installed in .venv. Run: .venv/bin/pip install -e clones/openevolve/")

    # Verify suite configs exist for Stage 3 evaluation
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

    # Verify ContinuumBench can load controller extensions and 2D workloads
    try:
        from continuum_bench.controllers.extensions import build_extension_controller
        from continuum_bench.workload import build_stream
    except Exception as e:
        errors.append(f"ContinuumBench extensions/workload integration failure: {e}")

    # Verify LLM API key is present in environment
    import os
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
    """
    Exports the best discovered policy to output/evolved_policy.py.
    Adds a provenance header documenting the evolutionary search metadata.
    """
    try:
        # Query the best program from the MAP-Elites archive
        best = evolve_instance.database.get_best_program()
        if not best:
            logger.warning("No programs in database — cannot export best policy.")
            return

        fitness = best.metrics.get("combined_score", float("-inf"))

        # Build provenance header documenting the discovered policy's origin
        provenance = f'''"""
evolved_policy.py — Step 7 Output: OpenEvolve-Discovered Conformal Autoscaler Policy

Role:
    Best policy discovered by the OpenEvolve evolutionary search across
    {evolve_instance.config.max_iterations} iterations of simulation-in-the-loop optimization.

Provenance:
    Search configuration: configs/evolution/openevolve_config.yaml
    Seed program:         src/continuum_ext/evolution/seed_policy.py
    Evaluator:            src/continuum_ext/evolution/openevolve_evaluator.py
    MAP-Elites archive:   output/evolution_runs/openevolve_db/

Performance (authoritative 13-regime benchmark):
    Fitness J (combined_score): {fitness:.4f}
    Cost savings:               {best.metrics.get("cost_savings", "N/A")}%
    Churn stability:            {best.metrics.get("churn_stability", "N/A")}
    Tail safety:                {best.metrics.get("tail_safety", "N/A")}
    Deadline misses:            {best.metrics.get("deadline_misses", "N/A")}
    Worker-seconds:             {best.metrics.get("worker_seconds", "N/A")}
    Scaling deltas:             {best.metrics.get("scaling_deltas", "N/A")}

AGENTS.md Compliance:
    Rule #1 — Saved as new versioned artifact (evolved_policy.py) per Rule #1.
              Seed policy (seed_policy.py) is NOT modified.
"""

'''
        # Prepend provenance header to the evolved policy source code
        evolved_source = provenance + best.code

        BEST_POLICY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(BEST_POLICY_OUTPUT, "w") as f:
            f.write(evolved_source)

        cost_val = best.metrics.get("cost_savings", "N/A")
        cost_str = f"{cost_val:.2f}%" if isinstance(cost_val, (int, float)) else str(cost_val)

        logger.info(f"Best policy exported to {BEST_POLICY_OUTPUT}")
        logger.info(f"  Fitness J: {fitness:.4f}")
        logger.info(f"  Cost savings: {cost_str}")
        logger.info(f"  Deadline misses: {best.metrics.get('deadline_misses', 'N/A')}")

    except Exception as e:
        logger.error(f"Failed to export best policy: {e}")


def main():
    args = parse_args()

    logger.info("=" * 70)
    logger.info("STEP 7: OpenEvolve Conformal Autoscaler Evolutionary Search")
    logger.info(f"  Config:    {CONFIG_PATH}")
    logger.info(f"  Seed:      {SEED_POLICY_PATH}")
    logger.info(f"  Evaluator: {EVALUATOR_PATH}")
    logger.info("=" * 70)

    # ── Validate all prerequisites before starting ────────────────────────────
    validate_prerequisites()

    # ── Load configuration from YAML (AGENTS.md Rule #2 — no hardcoding) ─────
    config = Config.from_yaml(CONFIG_PATH)

    # ── Apply CLI overrides ───────────────────────────────────────────────────
    if args.iterations is not None:
        config.max_iterations = args.iterations
        logger.info(f"Overriding max_iterations → {config.max_iterations}")

    if args.dry_run:
        config.max_iterations = 3
        config.checkpoint_interval = 1
        logger.info("DRY RUN mode: 3 iterations only")

    # ── Handle --reset request ─────────────────────────────────────────────────
    if args.reset:
        import shutil
        from datetime import datetime, timezone
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

    # ── Create output directories ──────────────────────────────────────────────
    EVOLUTION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Instantiate OpenEvolve with custom population migration strategy ───────
    # The custom_population_strategy enforces directed source→sink migration:
    #   Island 0 (Core Conformal) → Island 1 (Experimental Radical) ONLY.
    #   Island 1 never sends programs back to Island 0 (asymmetric gene flow).
    logger.info("Instantiating OpenEvolve with asymmetric island topology...")
    logger.info(f"  max_iterations: {config.max_iterations}")
    logger.info(f"  num_islands: {config.database.num_islands}")
    logger.info(f"  MAP-Elites dims: {config.database.feature_dimensions}")
    logger.info(f"  Cascade thresholds: {config.evaluator.cascade_thresholds}")
    logger.info(f"  Migration interval: {config.database.migration_interval}")

    evolve = OpenEvolve(
        initial_program_path=str(SEED_POLICY_PATH),
        evaluation_file=str(EVALUATOR_PATH),
        config=config,
        output_dir=str(EVOLUTION_OUTPUT_DIR),
        population_strategy=custom_population_strategy,
    )

    # ── Hook real-time discovery log sync into checkpoint callback ────────────
    # Automatically update CSV and Markdown discovery logs as each iteration finishes
    orig_save_checkpoint = evolve._save_checkpoint

    def _sync_logs_callback(iteration: int):
        orig_save_checkpoint(iteration)
        try:
            from log_discovery import sync_logs
            sync_logs()
        except Exception as err:
            logger.warning(f"Could not sync discovery logs at iteration {iteration}: {err}")

    evolve._save_checkpoint = _sync_logs_callback

    # ── Run the evolutionary search ───────────────────────────────────────────
    logger.info("Launching evolutionary search...")
    logger.info(f"Target iterations: {config.max_iterations}")

    try:
        import asyncio

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

        # Run evolution (asyncio entry point for OpenEvolve's async evaluation loop)
        asyncio.run(evolve.run(iterations=config.max_iterations, checkpoint_path=checkpoint_path))

    except KeyboardInterrupt:
        logger.info("Evolution interrupted by user (Ctrl+C). Saving best policy...")
    except Exception as e:
        logger.error(f"Evolution failed with exception: {e}")
        raise
    finally:
        # Always export the best policy found so far, even on interrupt/failure
        logger.info("Exporting best discovered policy...")
        export_best_policy(evolve)

        # Update CSV and Markdown discovery logs
        try:
            from log_discovery import sync_logs
            sync_logs()
        except Exception as e:
            logger.warning(f"Could not update discovery logs: {e}")

    logger.info("=" * 70)
    logger.info("STEP 7 ITERATION RUN FINISHED")
    logger.info(f"Best policy: {BEST_POLICY_OUTPUT}")
    logger.info(f"Discovery Log: docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG.md")
    logger.info(f"Performance CSV: output/evolution_runs/algorithm_performance_log.csv")
    logger.info(f"Database:    {config.database.db_path}")
    logger.info(f"Trace:       {config.evolution_trace.output_path}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
