#!/usr/bin/env python3
"""
export_step8_v3_results.py — Step 8 v3: Export & Archive Multi-Seed Readings for Easy Transfer

Role:
    Packages the complete Step 8 v3 multi-seed evaluation folder (output/step8_multiseed_runs_v3/)
    into a single compressed tarball (step8_v3_multiseed_results.tar.gz).
    Includes all raw summary.json simulation readings, tabular CSV logs, raw JSON arrays,
    and computed hypothesis tests, making it effortless to download from Codespace to local.

Gate Stage:    Step 8 v3 (Data Export & Packaging Gate)
Preceding:     scripts/run_step8_multiseed_v3.py
               scripts/process_step8_v3_statistics.py

Output:
    - step8_v3_multiseed_results.tar.gz
"""

import argparse
import os
import subprocess
import sys
import tarfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = WORKSPACE_ROOT / "output" / "step8_multiseed_runs_v3"
DEFAULT_ARCHIVE_PATH = WORKSPACE_ROOT / "step8_v3_multiseed_results.tar.gz"


def main():
    parser = argparse.ArgumentParser(description="Step 8 v3: Export multi-seed evaluation results to a compressed tarball")
    parser.add_argument("--source-dir", type=str, default=str(DEFAULT_SOURCE_DIR), help="Source directory containing step8 runs")
    parser.add_argument("--out-tar", type=str, default=str(DEFAULT_ARCHIVE_PATH), help="Target archive path")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    out_tar = Path(args.out_tar).resolve()

    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        sys.exit(1)

    csv_file = source_dir / "multiseed_summary.csv"
    if not csv_file.exists():
        print(f"WARNING: multiseed_summary.csv not found in {source_dir}. Run might be incomplete.")

    print("=" * 80)
    print("PACKAGING STEP 8 V3 MULTI-SEED RESULTS FOR DOWNLOAD")
    print(f"Source Directory: {source_dir}")
    print(f"Target Archive:   {out_tar}")
    print("=" * 80)

    # Count files to archive
    all_files = [f for f in source_dir.rglob("*") if f.is_file()]
    print(f"Found {len(all_files):,} files to package.")

    print("Compressing archive (tar.gz)...")
    with tarfile.open(out_tar, "w:gz") as tar:
        tar.add(source_dir, arcname="step8_multiseed_runs_v3")

    tar_size_mb = out_tar.stat().st_size / (1024 * 1024)
    print(f"Archive successfully created: {out_tar} ({tar_size_mb:.2f} MB)")
    print("=" * 80)
    print("HOW TO DOWNLOAD FROM CODESPACE:")
    print("1. From Codespace Terminal / Explorer:")
    print("   Right-click 'step8_v3_multiseed_results.tar.gz' -> Download")
    print("2. Or via GitHub CLI / SCP:")
    print(f"   gh codespace cp remote:{out_tar.name} ./")
    print("3. To extract locally in workspace root:")
    print("   tar -xzf step8_v3_multiseed_results.tar.gz -C output/")
    print("=" * 80)


if __name__ == "__main__":
    main()
