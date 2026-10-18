#!/usr/bin/env python3
"""
scripts/download_datasets.py — Unified Dataset Downloader & Fallback Provisioner
==================================================================================
Role:
    Automates the acquisition and verification of authoritative datasets required
    by the ContinuumBench serving experiments:
      1. Microsoft Azure Functions 2019 Dataset Distribution Archive (137 MB)
      2. ImageNet-1k Canonical Class Index (imagenet_class_index.json)
      3. Tiny ImageNet Validation Set & 182-Class Calibrated Subset Mapping

Fallback Strategy:
    Prioritizes existing local data in data/. If files are missing, checks local
    peer caches (~/edgecompute/data, ~/conformal-inference/data) before initiating
    network downloads from official public endpoints.

Execution Pattern:
    ./.venv/bin/python -m scripts.download_datasets [--all | --azure | --tiny | --verify_only]
"""

import os
import sys
import shutil
import argparse
import urllib.request
from pathlib import Path
from typing import Optional, List

# Authoritative URLs
AZURE_2019_TAR_URL = (
    "https://github.com/Azure/AzurePublicDataset/releases/download/"
    "dataset-functions-2019/azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz"
)
IMAGENET_CLASS_INDEX_URL = (
    "https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json"
)

# Root-anchored paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
AZURE_DIR = DATA_DIR / "azure_traces"
TINY_DIR = DATA_DIR / "tinyimagenet" / "val"
CONFIG_DIR = REPO_ROOT / "calibration" / "configs"

# Local fallback cache search paths
PEER_CACHE_DIRS = [
    Path.home() / "edgecompute" / "data",
    Path.home() / "conformal-inference" / "data",
]


def check_and_copy_fallback(filename: str, target_dir: Path) -> bool:
    """Checks peer workspace directories for existing copies of large datasets."""
    target_path = target_dir / filename
    if target_path.is_file() and target_path.stat().st_size > 100_000:
        return True

    for peer_dir in PEER_CACHE_DIRS:
        for sub in [peer_dir, peer_dir / "azure_traces", peer_dir / "tinyimagenet"]:
            candidate = sub / filename
            if candidate.is_file() and candidate.stat().st_size > 100_000:
                print(f"[FALLBACK] Found {filename} in peer cache: {candidate}")
                print(f"[FALLBACK] Copying to target: {target_path} ...")
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate, target_path)
                print(f"[FALLBACK] ✓ Copied {filename} ({target_path.stat().st_size / (1024*1024):.2f} MB).")
                return True
    return False


def setup_azure_trace(force: bool = False) -> Path:
    """Ensures Azure Functions 2019 archive and processed .npz are present."""
    AZURE_DIR.mkdir(parents=True, exist_ok=True)
    processed_npz = AZURE_DIR / "azure_functions_2019_processed.npz"
    raw_archive = AZURE_DIR / "azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz"

    # Check processed NPZ first
    if processed_npz.is_file() and not force:
        print(f"[AZURE TRACE] ✓ Processed trace present: {processed_npz} ({processed_npz.stat().st_size / (1024*1024):.2f} MB)")
    else:
        # Check fallback cache
        if not check_and_copy_fallback("azure_functions_2019_processed.npz", AZURE_DIR):
            print("[AZURE TRACE] Processed trace not found in peer cache. Checking raw archive...")

    # Check raw archive for full preprocessing provenance
    if raw_archive.is_file() and not force:
        print(f"[AZURE TRACE] ✓ Raw archive present: {raw_archive} ({raw_archive.stat().st_size / (1024*1024):.2f} MB)")
    else:
        if not check_and_copy_fallback(raw_archive.name, AZURE_DIR):
            print(f"[AZURE TRACE] Downloading raw archive from {AZURE_2019_TAR_URL}...")
            urllib.request.urlretrieve(AZURE_2019_TAR_URL, raw_archive)
            print(f"[AZURE TRACE] ✓ Downloaded {raw_archive.name} ({raw_archive.stat().st_size / (1024*1024):.2f} MB).")

    return processed_npz


def setup_tiny_imagenet(force: bool = False) -> Path:
    """Ensures Tiny ImageNet validation set and class mappings are present."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TINY_DIR.mkdir(parents=True, exist_ok=True)

    idx_path = CONFIG_DIR / "imagenet_class_index.json"
    mapping_path = CONFIG_DIR / "tiny_class_mapping.json"

    # 1. ImageNet-1k class index
    if not idx_path.is_file() or force:
        print(f"[TINY IMAGENET] Downloading ImageNet class index from {IMAGENET_CLASS_INDEX_URL}...")
        urllib.request.urlretrieve(IMAGENET_CLASS_INDEX_URL, idx_path)
        print(f"[TINY IMAGENET] ✓ Saved ImageNet index -> {idx_path}")
    else:
        print(f"[TINY IMAGENET] ✓ ImageNet class index verified: {idx_path}")

    # 2. Check 182-class mapping
    if not mapping_path.is_file():
        raise FileNotFoundError(f"Missing required class mapping at {mapping_path}")
    print(f"[TINY IMAGENET] ✓ 182-class subset mapping verified: {mapping_path}")

    # 3. Validation images count
    images = [f for f in os.listdir(TINY_DIR) if f.endswith(".jpg")]
    if len(images) >= 10000 and not force:
        print(f"[TINY IMAGENET] ✓ Validation images verified: {len(images):,} images found in {TINY_DIR}")
    else:
        print(f"[TINY IMAGENET] Current validation images: {len(images):,}. Checking peer caches...")
        for peer_dir in PEER_CACHE_DIRS:
            peer_val = peer_dir / "tinyimagenet" / "val"
            if peer_val.is_dir():
                peer_images = [f for f in os.listdir(peer_val) if f.endswith(".jpg")]
                if len(peer_images) >= 10000:
                    print(f"[FALLBACK] Found {len(peer_images):,} images in {peer_val}. Copying missing images...")
                    for img in peer_images:
                        src_file = peer_val / img
                        dst_file = TINY_DIR / img
                        if not dst_file.is_file():
                            shutil.copy2(src_file, dst_file)
                    print(f"[FALLBACK] ✓ Synchronized {len(os.listdir(TINY_DIR)):,} images into {TINY_DIR}")
                    break

    return TINY_DIR


def main():
    parser = argparse.ArgumentParser(description="ContinuumBench Dataset Downloader & Fallback Provisioner")
    parser.add_argument("--all", action="store_true", default=True, help="Verify and provision all datasets (default)")
    parser.add_argument("--azure", action="store_true", help="Provision only Azure Functions 2019 trace")
    parser.add_argument("--tiny", action="store_true", help="Provision only Tiny ImageNet validation split")
    parser.add_argument("--force", action="store_true", help="Force re-download / overwrite")
    parser.add_argument("--verify_only", action="store_true", help="Only verify dataset files without downloading")
    args = parser.parse_args()

    print("=" * 80)
    print("CONTINUUMBENCH DATASET DOWNLOADER & FALLBACK PROVISIONER")
    print("=" * 80)

    if args.verify_only:
        from scripts.verify_dataset_integrity import main as run_verify
        return run_verify()

    if args.azure or args.all:
        setup_azure_trace(force=args.force)

    if args.tiny or args.all:
        setup_tiny_imagenet(force=args.force)

    print("\n" + "=" * 80)
    print("DATASET PROVISIONING COMPLETE — RUNNING FINAL SANITY CHECK")
    print("=" * 80)
    from scripts.verify_dataset_integrity import main as run_verify
    return run_verify()


if __name__ == "__main__":
    sys.exit(main())
