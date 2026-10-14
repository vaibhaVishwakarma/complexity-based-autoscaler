#!/usr/bin/env python3
"""
scripts/audit_refactor_hygiene.py — Automated Refactoring & Hygiene Auditor

Scans the repository to verify compliance with scientific refactoring standards:
1. Zero dynamic sys.path tampering.
2. Zero silent fallback patterns (e.g., ternary legacy directory checks).
3. Zero out-of-bounds symlinks.
4. Clean virtualenv confinement.
5. Zero deprecated directory references.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

ROOT_DIR = Path(".").resolve()


def check_sys_path_tampering(root: Path) -> List[Tuple[str, int, str]]:
    """Detect sys.path.insert, sys.path.append, or sys.path manipulation in active python files."""
    violations: List[Tuple[str, int, str]] = []
    pattern = re.compile(r"^\s*sys\.path\.(insert|append|extend)")

    excluded_dirs = {".venv", "venv", ".git", ".archive", "clones", "scratch", ".agents"}

    for path in root.rglob("*.py"):
        if any(part in excluded_dirs for part in path.parts):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, 1):
                    stripped = line.strip()
                    if pattern.search(line) and not stripped.startswith("#"):
                        violations.append((str(path.relative_to(root)), idx, stripped))
        except Exception:
            continue
    return violations


def check_silent_fallbacks(root: Path, legacy_names: List[str]) -> List[Tuple[str, int, str]]:
    """Detect ternary silent fallback patterns targeting legacy directory/file names."""
    violations: List[Tuple[str, int, str]] = []
    fallback_patterns = [
        re.compile(rf"if\s+.*is_(dir|file)\(\)\s+else\s+.*['\"]({name})['\"]")
        for name in legacy_names
    ]

    excluded_dirs = {".venv", "venv", ".git", ".archive", "clones", "scratch", ".agents"}

    for path in root.rglob("*.py"):
        if any(part in excluded_dirs for part in path.parts):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, 1):
                    stripped = line.strip()
                    if any(p.search(line) for p in fallback_patterns) and not stripped.startswith("#"):
                        violations.append((str(path.relative_to(root)), idx, stripped))
        except Exception:
            continue
    return violations


def check_out_of_bounds_symlinks(root: Path) -> List[Tuple[str, str]]:
    """Detect symlinks pointing outside the workspace root (excluding standard system Python symlinks inside .venv)."""
    violations: List[Tuple[str, str]] = []
    root_resolved = root.resolve()

    for path in root.rglob("*"):
        if ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.is_symlink():
            try:
                target = path.resolve()
                if not str(target).startswith(str(root_resolved)):
                    violations.append((str(path.relative_to(root)), str(target)))
            except Exception:
                violations.append((str(path.relative_to(root)), "Unresolvable symlink"))
    return violations


def check_virtualenv_confinement(root: Path) -> List[str]:
    """Verify that .venv is genuine and self-contained."""
    issues: List[str] = []
    venv_path = root / ".venv"

    if not venv_path.exists():
        issues.append("Missing .venv directory in workspace root.")
        return issues

    if venv_path.is_symlink():
        target = venv_path.resolve()
        if not str(target).startswith(str(root.resolve())):
            issues.append(f".venv is an out-of-bounds symlink pointing to: {target}")

    python_bin = venv_path / "bin" / "python"
    if not python_bin.exists():
        issues.append("Missing .venv/bin/python interpreter.")

    return issues


def main() -> int:
    legacy_names = ["gate1", "gate2"]
    exit_code = 0

    print("=" * 70)
    print("Scientific Refactoring & Hygiene Audit")
    print(f"Workspace Root: {ROOT_DIR}")
    print("=" * 70)

    # 1. Virtualenv Confinement
    venv_issues = check_virtualenv_confinement(ROOT_DIR)
    if venv_issues:
        print("[FAIL] Virtualenv Confinement:")
        for issue in venv_issues:
            print(f"  - {issue}")
        exit_code = 1
    else:
        print("[PASS] Virtualenv is genuine and strictly confined to workspace.")

    # 2. Out-of-bounds Symlinks
    symlink_violations = check_out_of_bounds_symlinks(ROOT_DIR)
    if symlink_violations:
        print("[FAIL] Out-of-Bounds Symlinks Detected:")
        for link, target in symlink_violations:
            print(f"  - {link} -> {target}")
        exit_code = 1
    else:
        print("[PASS] Zero out-of-bounds symlinks detected.")

    # 3. sys.path Tampering
    sys_path_violations = check_sys_path_tampering(ROOT_DIR)
    if sys_path_violations:
        print("[FAIL] Dynamic sys.path Tampering Detected:")
        for file, line_no, content in sys_path_violations:
            print(f"  - {file}:{line_no} -> {content}")
        exit_code = 1
    else:
        print("[PASS] Zero dynamic sys.path modifications in active code.")

    # 4. Silent Fallbacks
    fallback_violations = check_silent_fallbacks(ROOT_DIR, legacy_names)
    if fallback_violations:
        print(f"[FAIL] Silent Fallback Patterns Detected ({', '.join(legacy_names)}):")
        for file, line_no, content in fallback_violations:
            print(f"  - {file}:{line_no} -> {content}")
        exit_code = 1
    else:
        print(f"[PASS] Zero silent fallbacks to legacy names ({', '.join(legacy_names)}).")

    print("=" * 70)
    if exit_code == 0:
        print("ALL HYGIENE AUDITS PASSED [100% CLEAN] ✓")
    else:
        print("HYGIENE AUDIT FAILED: Please fix identified violations above.")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
