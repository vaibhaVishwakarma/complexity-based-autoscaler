#!/usr/bin/env python3
"""
scripts/run_unattended_v2.py — Step 7 v2: Unattended Evolution Supervisor

Role:
    Fault-tolerant, self-healing supervisor for OpenEvolve v2 Cost-First policy search.
    Designed for long-running Codespace or remote headless compute sessions.
    Automatically handles process interruptions, API key exhaustion, and
    network drops by rotating keys and resuming from the latest checkpoint.

Usage:
    # Run full 200-iteration search hands-free:
    ./.venv/bin/python scripts/run_unattended_v2.py --iterations 200

    # Run in background (survives SSH/browser disconnection):
    nohup ./.venv/bin/python scripts/run_unattended_v2.py --reset --iterations 200 > evaluation_run_v2.log 2>&1 &

AGENTS.md Compliance:
    Rule #1 — Dedicated v2 supervisor; original run_unattended.py untouched.
    Rule #2 — Zero hardcoded parameters; paths and config loaded dynamically.
    Rule #3 — Uses workspace virtual environment (./.venv).
    Rule #4 — Self-documenting docstrings and inline comments.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SUPERVISOR v2] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("unattended_supervisor_v2")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PYTHON_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "python"
EVOLUTION_SCRIPT = WORKSPACE_ROOT / "scratch" / "run_evolution_v2.py"
ROTATOR_SCRIPT = WORKSPACE_ROOT / "scripts" / "rotate_api_key.py"
CHECKPOINTS_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v2" / "checkpoints"
BEST_POLICY_FILE = WORKSPACE_ROOT / "output" / "evolved_policy_v2.py"
EVOLUTION_RUNS_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v2"


def get_latest_checkpoint_iteration() -> int:
    """Returns the highest iteration number found in checkpoints directory, or 0."""
    if not CHECKPOINTS_DIR.exists():
        return 0
    ckpts = [
        int(d.name.split("_")[-1])
        for d in CHECKPOINTS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("checkpoint_") and d.name.split("_")[-1].isdigit()
    ]
    return max(ckpts) if ckpts else 0


def try_auto_rotate_key() -> bool:
    """Runs rotate_api_key.py --auto-find-working if present."""
    if not ROTATOR_SCRIPT.exists():
        return False
    try:
        res = subprocess.run(
            [str(PYTHON_BIN), str(ROTATOR_SCRIPT), "--auto-find-working"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if res.returncode == 0:
            logger.info("Successfully identified and activated a responsive API key.")
            return True
        else:
            logger.warning(f"Key auto-find returned non-zero: {res.stderr.strip() or res.stdout.strip()}")
            return False
    except Exception as e:
        logger.warning(f"Failed to run key rotator: {e}")
        return False


def run_supervisor(target_iterations: int, max_consecutive_failures: int = 5):
    """
    Supervises the evolution process until target_iterations is achieved.
    Automatically restarts with --resume if interrupted.
    """
    logger.info("=" * 70)
    logger.info(" STARTING UNATTENDED EVOLUTION SUPERVISOR (v2 Cost-First)")
    logger.info(f" Target iterations: {target_iterations}")
    logger.info(f" Python executable: {PYTHON_BIN}")
    logger.info(f" Checkpoints dir:   {CHECKPOINTS_DIR}")
    logger.info("=" * 70)

    consecutive_failures = 0

    while True:
        current_ckpt = get_latest_checkpoint_iteration()
        logger.info(f"Current progress: Checkpoint {current_ckpt} / {target_iterations}")

        if current_ckpt >= target_iterations:
            logger.info(f"[SUCCESS] Target of {target_iterations} iterations reached!")
            if BEST_POLICY_FILE.exists():
                logger.info(f"Authoritative evolved policy exported at: {BEST_POLICY_FILE}")
            break

        cmd = [str(PYTHON_BIN), str(EVOLUTION_SCRIPT), "--iterations", str(target_iterations)]
        if current_ckpt > 0:
            cmd.append("--resume")

        logger.info(f"Launching OpenEvolve v2: {' '.join(cmd)}")
        start_time = time.time()

        try:
            proc = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
            duration = time.time() - start_time

            if proc.returncode == 0:
                new_ckpt = get_latest_checkpoint_iteration()
                logger.info(f"OpenEvolve v2 completed cleanly (Iteration {new_ckpt}).")
                if new_ckpt >= target_iterations:
                    break
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                logger.warning(
                    f"OpenEvolve exited with code {proc.returncode} after {duration:.1f}s. "
                    f"Failure count: {consecutive_failures}/{max_consecutive_failures}"
                )

                if consecutive_failures >= max_consecutive_failures:
                    logger.error(
                        f"Aborting: Exceeded {max_consecutive_failures} consecutive failures. "
                        "Please inspect logs/error traces."
                    )
                    sys.exit(1)

                logger.info("Checking API key pool for active credentials...")
                try_auto_rotate_key()

                logger.info("Waiting 10 seconds before resuming from latest checkpoint...")
                time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Supervisor interrupted by user (Ctrl+C). Exiting cleanly.")
            break
        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                logger.error("Max failures reached. Exiting.")
                sys.exit(1)
            time.sleep(10)


def reset_evolution_state() -> None:
    """Safely archives previous v2 evolution artifacts."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_dir = EVOLUTION_RUNS_DIR / f"archive_reset_{timestamp}"

    items_to_archive = [
        EVOLUTION_RUNS_DIR / "checkpoints",
        EVOLUTION_RUNS_DIR / "openevolve_db",
        EVOLUTION_RUNS_DIR / "evolution_trace.jsonl",
        EVOLUTION_RUNS_DIR / "evaluator_checks.jsonl",
        EVOLUTION_RUNS_DIR / "algorithm_performance_log.csv",
        EVOLUTION_RUNS_DIR / "llm_calls.jsonl",
        EVOLUTION_RUNS_DIR / "llm_calls_log.csv",
    ]

    has_items = any(item.exists() for item in items_to_archive)
    if has_items:
        archive_dir.mkdir(parents=True, exist_ok=True)
        for item in items_to_archive:
            if item.exists():
                dest = archive_dir / item.name
                logger.info(f"[RESET] Archiving {item.name} → {dest}")
                shutil.move(str(item), str(dest))

    if EVOLUTION_RUNS_DIR.exists():
        for d in EVOLUTION_RUNS_DIR.glob("tmp*"):
            if d.is_dir():
                shutil.rmtree(str(d), ignore_errors=True)

    logger.info(f"[RESET] ✓ V2 Evolution state reset. Starting fresh from iteration 0.")


def main():
    parser = argparse.ArgumentParser(
        description="Unattended supervisor for OpenEvolve v2 policy search on Codespaces."
    )
    parser.add_argument(
        "--iterations", type=int, default=200,
        help="Target number of iterations to complete (default: 200).",
    )
    parser.add_argument(
        "--max-failures", type=int, default=5,
        help="Maximum consecutive crashes before aborting (default: 5).",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Reset evolution state to start fresh from iteration 0.",
    )
    args = parser.parse_args()

    if args.reset:
        reset_evolution_state()

    run_supervisor(args.iterations, args.max_failures)


if __name__ == "__main__":
    main()
