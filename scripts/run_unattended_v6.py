#!/usr/bin/env python3
"""
scripts/run_unattended_v6.py — Step 8.6: Unattended Evolution Supervisor (v6 Realism-Aware)
==========================================================================================

Role:
    Fault-tolerant, self-healing supervisor for OpenEvolve v6 Realism-Aware policy search.
    Designed for long-horizon headless GitHub Codespaces execution. Automatically handles
    process interruptions, rotates API keys via rotate_api_key.py, and resumes from checkpoints.

Usage:
    nohup ./.venv/bin/python scripts/run_unattended_v6.py --reset --iterations 150 > evaluation_run_v6.log 2>&1 &

AGENTS.md Compliance:
    Rule #1 — Dedicated v6 supervisor.
    Rule #2 — Config loaded dynamically; zero hardcoding.
    Rule #3 — Uses workspace virtual environment (./.venv/bin/python).
    Rule #4 — Self-documenting structure.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SUPERVISOR v6] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("unattended_supervisor_v6")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PYTHON_BIN = WORKSPACE_ROOT / ".venv" / "bin" / "python"
EVOLUTION_SCRIPT = WORKSPACE_ROOT / "scripts" / "run_evolution_v6.py"
ROTATOR_SCRIPT = WORKSPACE_ROOT / "scripts" / "rotate_api_key.py"
CHECKPOINTS_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v6" / "checkpoints"
BEST_POLICY_FILE = WORKSPACE_ROOT / "output" / "evolved_policy_v6.py"
EVOLUTION_RUNS_DIR = WORKSPACE_ROOT / "output" / "evolution_runs_v6"

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
    """Monitors and restarts OpenEvolve v6 until target_iterations is achieved."""
    logger.info("=" * 70)
    logger.info(" STARTING UNATTENDED EVOLUTION SUPERVISOR (v6 Realism-Aware)")
    logger.info(f" Target iterations: {target_iterations}")
    logger.info(f" Python binary:     {PYTHON_BIN}")
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

        cmd = [str(PYTHON_BIN), "-u", str(EVOLUTION_SCRIPT), "--iterations", str(target_iterations)]
        if current_ckpt > 0:
            cmd.append("--resume")

        logger.info(f"Launching OpenEvolve v6: {' '.join(cmd)}")
        start_time = time.time()

        try:
            proc = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
            duration = time.time() - start_time

            if proc.returncode == 0:
                new_ckpt = get_latest_checkpoint_iteration()
                logger.info(f"OpenEvolve v6 completed cleanly (Iteration {new_ckpt}).")
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

        except KeyboardInterrupt:
            logger.info("Supervisor interrupted by user. Exiting cleanly.")
            break
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"Supervisor unexpected error: {e}")
            time.sleep(10)


def main():
    parser = argparse.ArgumentParser(description="Fault-tolerant supervisor for OpenEvolve v6.")
    parser.add_argument("--iterations", type=int, default=150, help="Target total evolution iterations.")
    parser.add_argument("--reset", action="store_true", help="Reset previous runs in evolution_runs_v6.")
    args = parser.parse_args()

    if args.reset:
        if EVOLUTION_RUNS_DIR.exists():
            archive_dir = WORKSPACE_ROOT / "output" / f"evolution_runs_v6_archive_{time.strftime('%Y%m%d_%H%M%S')}"
            logger.warning(f"Archiving existing run directory to: {archive_dir}")
            shutil.move(str(EVOLUTION_RUNS_DIR), str(archive_dir))
        EVOLUTION_RUNS_DIR.mkdir(parents=True, exist_ok=True)

    run_supervisor(target_iterations=args.iterations)


if __name__ == "__main__":
    main()
