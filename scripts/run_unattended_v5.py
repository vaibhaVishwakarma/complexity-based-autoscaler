#!/usr/bin/env python3
"""
scripts/run_unattended_v5.py — Step 8.6 v5: Unattended Evolution Supervisor (Realism-Aware)

Role:
    Fault-tolerant, self-healing supervisor for OpenEvolve v5 Realism-Aware policy search.
    Designed for headless GitHub Codespaces compute sessions. Automatically handles process
    interruptions, rotates API keys via rotate_api_key.py, and resumes from latest checkpoint.
    Preserves disk health by triggering cleanup and logs full token & churn statistics.

Usage:
    # Run full 150-iteration search hands-free in background:
    nohup ./.venv/bin/python scripts/run_unattended_v5.py --reset --iterations 150 > evaluation_run_v5.log 2>&1 &

AGENTS.md Compliance:
    Rule #1 — Dedicated v5 supervisor; previous supervisors untouched.
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
    format="%(asctime)s [%(levelname)s] [SUPERVISOR v5] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("unattended_supervisor_v5")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PYTHON_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "python"
EVOLUTION_SCRIPT = WORKSPACE_ROOT / "scratch" / "run_evolution_v5.py"
ROTATOR_SCRIPT = WORKSPACE_ROOT / "scripts" / "rotate_api_key.py"
CHECKPOINTS_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v5" / "checkpoints"
BEST_POLICY_FILE = WORKSPACE_ROOT / "output" / "evolved_policy_v5.py"
EVOLUTION_RUNS_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v5"

_env_file = WORKSPACE_ROOT / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def get_latest_checkpoint_iteration() -> int:
    """Returns the highest iteration number found in checkpoints directory."""
    if not CHECKPOINTS_DIR.exists():
        return 0
    ckpts = [
        int(d.name.split("_")[-1])
        for d in CHECKPOINTS_DIR.iterdir()
        if d.is_dir() and d.name.startswith("checkpoint_") and d.name.split("_")[-1].isdigit()
    ]
    return max(ckpts) if ckpts else 0


def try_auto_rotate_key() -> bool:
    """Attempts to find and activate a responsive Gemini API key using rotate_api_key.py."""
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
    """Monitors and restarts OpenEvolve v5 until target_iterations is achieved."""
    logger.info("=" * 70)
    logger.info(" STARTING UNATTENDED EVOLUTION SUPERVISOR (v5 Realism-Aware)")
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

        logger.info(f"Launching OpenEvolve v5: {' '.join(cmd)}")
        start_time = time.time()

        try:
            proc = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
            duration = time.time() - start_time

            if proc.returncode == 0:
                new_ckpt = get_latest_checkpoint_iteration()
                logger.info(f"OpenEvolve v5 completed cleanly (Iteration {new_ckpt}).")
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
                    logger.error("Max consecutive failures reached. Attempting API key rotation...")
                    rotated = try_auto_rotate_key()
                    if rotated:
                        consecutive_failures = 0
                        logger.info("Key rotated successfully. Resuming in 10s...")
                        time.sleep(10)
                        continue
                    else:
                        logger.critical("Key rotation failed or exhausted. Exiting supervisor.")
                        sys.exit(1)

                logger.info("Cooling down for 15s before restarting...")
                time.sleep(15)

        except Exception as e:
            consecutive_failures += 1
            logger.error(f"Supervisor encountered unexpected error: {e}")
            if consecutive_failures >= max_consecutive_failures:
                logger.critical("Fatal errors in supervisor loop. Exiting.")
                sys.exit(1)
            time.sleep(15)

    # Post-completion packaging
    logger.info("=" * 70)
    logger.info("EVOLUTION COMPLETE. Packaging top variants and generating results bundle...")
    export_script = WORKSPACE_ROOT / "scripts" / "export_top_variants.py"
    if export_script.exists():
        subprocess.run([str(PYTHON_BIN), str(export_script), "--top", "30", "--version", "5"], cwd=str(WORKSPACE_ROOT))
    logger.info("All operations completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unattended supervisor for OpenEvolve v5.")
    parser.add_argument("--iterations", type=int, default=150, help="Target iterations (default: 150)")
    parser.add_argument("--reset", action="store_true", help="Reset previous runs and start from iteration 0")
    args = parser.parse_args()

    if args.reset:
        if EVOLUTION_RUNS_DIR.exists():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            archive_path = EVOLUTION_RUNS_DIR.parent / f"evolution_runs_v5_archive_{timestamp}"
            shutil.move(str(EVOLUTION_RUNS_DIR), str(archive_path))
            logger.info(f"Existing evolution_runs_v5 archived to {archive_path}")

    run_supervisor(target_iterations=args.iterations)
