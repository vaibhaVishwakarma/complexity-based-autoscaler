#!/usr/bin/env python3
"""
scripts/rotate_api_key.py

Role:
    Manages and rotates Gemini API keys from a backup pool (.env.backup) into
    the active environment configuration (.env). Designed for long-running
    experiments on Codespaces or headless compute where API keys may hit
    rate limits, token quotas, or expiration.

Usage:
    # Rotate to next key in sequence:
    ./.venv/bin/python scripts/rotate_api_key.py

    # View current key status (masked) without changing:
    ./.venv/bin/python scripts/rotate_api_key.py --status

    # Test if currently active key is healthy (200 OK):
    ./.venv/bin/python scripts/rotate_api_key.py --test

    # Rotate to next key AND verify health:
    ./.venv/bin/python scripts/rotate_api_key.py --test-after-rotate

    # Automatically scan pool and select the first working, non-exhausted key:
    ./.venv/bin/python scripts/rotate_api_key.py --auto-find-working

    # Select a specific key by 1-based index:
    ./.venv/bin/python scripts/rotate_api_key.py --index 2

AGENTS.md Compliance:
    Rule #2: Zero hardcoded keys or values; loaded dynamically from .env/.env.backup.
    Rule #3: Runs in workspace virtual environment (./.venv).
    Rule #4: Self-documenting docstrings and inline comments.
    Rule #5: Uses standard library only (pathlib, urllib, json, argparse).
"""

import argparse
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("key_rotator")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = WORKSPACE_ROOT / ".env"
DEFAULT_BACKUP_FILE = WORKSPACE_ROOT / ".env.backup"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


def mask_key(key: Optional[str]) -> str:
    """Returns a masked version of the key for safe logging (e.g. 'AIzaSy...4aBc')."""
    if not key:
        return "<EMPTY>"
    key = key.strip()
    if len(key) <= 10:
        return "***"
    return f"{key[:6]}...{key[-4:]}"


def load_backup_keys(backup_file: Path) -> List[str]:
    """
    Parses backup keys from .env.backup.
    Supports flexible formats:
      - Raw keys on each line: AIzaSy...
      - Variable assignment: GEMINI_API_KEY=AIzaSy...
      - Numbered assignments: GEMINI_API_KEY_1=AIzaSy...
      - Strips quotes, whitespace, and ignores lines starting with #.
    """
    if not backup_file.exists():
        return []

    keys = []
    with open(backup_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Strip possible prefix like GEMINI_API_KEY_1= or export GEMINI_API_KEY=
            if line.startswith("export "):
                line = line[len("export "):].strip()
            if "=" in line:
                _, val = line.split("=", 1)
                val = val.strip().strip("'\"")
            else:
                val = line.strip("'\"")

            if val and val not in keys:
                keys.append(val)

    return keys


def get_active_key(env_file: Path) -> Optional[str]:
    """Reads the active GEMINI_API_KEY from .env."""
    if not env_file.exists():
        return None

    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].strip()
            if line.startswith("GEMINI_API_KEY="):
                _, val = line.split("=", 1)
                return val.strip().strip("'\"")

    return None


def write_active_key(env_file: Path, new_key: str) -> None:
    """
    Safely writes or updates GEMINI_API_KEY in .env, preserving
    any other environment variables and comments.
    """
    lines = []
    found = False

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("GEMINI_API_KEY=") or stripped.startswith("export GEMINI_API_KEY="):
                    lines.append(f"GEMINI_API_KEY={new_key}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        lines.append(f"GEMINI_API_KEY={new_key}\n")

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(lines)


def test_api_key(api_key: str, model: str = DEFAULT_MODEL, timeout_s: float = 8.0) -> Tuple[bool, str]:
    """
    Pings Google AI Studio's OpenAI-compatible endpoint with a minimal 1-token query.
    Returns (is_healthy, status_message).
    """
    if not api_key:
        return False, "Key is empty"

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_ENDPOINT,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            if resp.status == 200:
                return True, "HTTP 200 OK (Key active & responsive)"
            return False, f"Unexpected HTTP status {resp.status}"

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
            err_data = json.loads(body)
            err_msg = err_data.get("error", {}).get("message", body[:150])
        except Exception:
            err_msg = body[:150] or str(e)

        if e.code == 429:
            return False, f"HTTP 429 Quota/Rate Limit Exceeded: {err_msg}"
        elif e.code in (400, 401, 403):
            return False, f"HTTP {e.code} Auth/Permission Error: {err_msg}"
        else:
            return False, f"HTTP {e.code} Error: {err_msg}"

    except urllib.error.URLError as e:
        return False, f"Network Connection Error: {e.reason}"
    except Exception as e:
        return False, f"Request Failed: {e}"


def rotate_to_next(
    backup_file: Path = DEFAULT_BACKUP_FILE,
    env_file: Path = DEFAULT_ENV_FILE,
    target_index: Optional[int] = None,
) -> Tuple[int, int, str]:
    """
    Rotates GEMINI_API_KEY in env_file to the next key from backup_file.
    Returns (1-based index selected, total keys, masked new key).
    """
    keys = load_backup_keys(backup_file)
    if not keys:
        raise ValueError(
            f"No backup keys found in {backup_file}. "
            f"Please populate {backup_file} with your API keys (one per line)."
        )

    current_key = get_active_key(env_file)
    total = len(keys)

    if target_index is not None:
        idx = (target_index - 1) % total
    else:
        # Find index of current key in backup list
        try:
            cur_idx = keys.index(current_key) if current_key else -1
            idx = (cur_idx + 1) % total
        except ValueError:
            # If current key isn't in backup list, choose the first one
            idx = 0

    new_key = keys[idx]
    write_active_key(env_file, new_key)
    return idx + 1, total, mask_key(new_key)


def find_first_working_key(
    backup_file: Path = DEFAULT_BACKUP_FILE,
    env_file: Path = DEFAULT_ENV_FILE,
) -> Tuple[int, int, str]:
    """
    Sequentially tests keys in backup_file starting from the active key,
    and sets the first responsive, non-exhausted key into env_file.
    """
    keys = load_backup_keys(backup_file)
    if not keys:
        raise ValueError(f"No backup keys found in {backup_file}.")

    current_key = get_active_key(env_file)
    total = len(keys)

    try:
        cur_idx = keys.index(current_key) if current_key else -1
    except ValueError:
        cur_idx = -1

    # Start searching from cur_idx + 1
    start_offset = (cur_idx + 1) % total
    for i in range(total):
        idx = (start_offset + i) % total
        candidate_key = keys[idx]
        masked = mask_key(candidate_key)
        logger.info(f"Testing Key #{idx + 1}/{total} [{masked}]...")
        ok, msg = test_api_key(candidate_key)
        if ok:
            logger.info(f"-> Key #{idx + 1} passed: {msg}")
            write_active_key(env_file, candidate_key)
            return idx + 1, total, masked
        else:
            logger.warning(f"-> Key #{idx + 1} failed: {msg}")

    raise RuntimeError("All backup API keys in pool failed verification or are quota-exhausted.")


def print_status(backup_file: Path, env_file: Path):
    """Prints current status without modifying anything."""
    keys = load_backup_keys(backup_file)
    current_key = get_active_key(env_file)

    print("\n" + "=" * 60)
    print(" GEMINI API KEY STATUS")
    print("=" * 60)
    print(f"Env File:    {env_file}")
    print(f"Backup File: {backup_file}")
    print(f"Pool Size:   {len(keys)} backup key(s) detected")

    if not current_key:
        print("Active Key:  <NONE SET>")
    else:
        try:
            idx = keys.index(current_key) + 1
            print(f"Active Key:  Key #{idx} of {len(keys)} [{mask_key(current_key)}]")
        except ValueError:
            print(f"Active Key:  [{mask_key(current_key)}] (Note: not in .env.backup)")

    if keys:
        print("\nAvailable Keys in Backup Pool:")
        for i, k in enumerate(keys, 1):
            marker = " -> [ACTIVE]" if k == current_key else "             "
            print(f"  #{i:02d}: {mask_key(k)}{marker}")
    print("=" * 60 + "\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rotate Gemini API keys from .env.backup into .env for unattended runs."
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Display current active key and backup pool status without making changes.",
    )
    parser.add_argument(
        "--next", action="store_true",
        help="Rotate to next key in sequence (default behavior if no flags passed).",
    )
    parser.add_argument(
        "--index", type=int, default=None,
        help="Switch to a specific key index (1-based, e.g. --index 3).",
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Test currently active key with a lightweight 1-token API request.",
    )
    parser.add_argument(
        "--test-after-rotate", action="store_true",
        help="Rotate to next key and verify that it is responsive.",
    )
    parser.add_argument(
        "--auto-find-working", action="store_true",
        help="Scan keys in pool and activate the first one that passes API health check.",
    )
    parser.add_argument(
        "--backup-file", type=Path, default=DEFAULT_BACKUP_FILE,
        help=f"Path to backup keys file (default: {DEFAULT_BACKUP_FILE}).",
    )
    parser.add_argument(
        "--env-file", type=Path, default=DEFAULT_ENV_FILE,
        help=f"Path to active .env file (default: {DEFAULT_ENV_FILE}).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Mode 1: Status only
    if args.status:
        print_status(args.backup_file, args.env_file)
        return

    # Mode 2: Test active key only
    if args.test:
        current_key = get_active_key(args.env_file)
        if not current_key:
            logger.error("No active key found in .env to test.")
            sys.exit(1)
        logger.info(f"Testing active key [{mask_key(current_key)}]...")
        ok, msg = test_api_key(current_key)
        if ok:
            logger.info(f"[SUCCESS] {msg}")
            sys.exit(0)
        else:
            logger.error(f"[FAILED] {msg}")
            sys.exit(1)

    # Mode 3: Automatically find working key
    if args.auto_find_working:
        try:
            idx, total, masked = find_first_working_key(args.backup_file, args.env_file)
            logger.info(f"[SUCCESS] Activated healthy Key #{idx}/{total} [{masked}] in {args.env_file.name}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"[FAILED] {e}")
            sys.exit(1)

    # Mode 4: Rotate (default or explicit)
    try:
        current_key = get_active_key(args.env_file)
        prev_masked = mask_key(current_key)
        idx, total, masked = rotate_to_next(
            args.backup_file, args.env_file, target_index=args.index
        )
        logger.info(
            f"[ROTATED] Replaced {args.env_file.name}:\n"
            f"  Previous: [{prev_masked}]\n"
            f"  Active  : Key #{idx} of {total} [{masked}]"
        )

        if args.test_after_rotate:
            logger.info(f"Verifying new active Key #{idx}...")
            active_now = get_active_key(args.env_file)
            ok, msg = test_api_key(active_now)
            if ok:
                logger.info(f"[HEALTHY] {msg}")
            else:
                logger.warning(f"[WARNING] New key may be invalid or exhausted: {msg}")

    except Exception as e:
        logger.error(f"[ERROR] Rotation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
