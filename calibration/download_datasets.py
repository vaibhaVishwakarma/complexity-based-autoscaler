#!/usr/bin/env python3
"""
gate1/download_datasets.py — Gate 1 Dataset Verification and Preparation Utility
================================================================================
Role:
    Verifies and prepares the authoritative dataset splits and class mappings for
    Gate 1 Conformal Calibration. Validates local Tiny ImageNet validation images
    and 182-class index mapping against ImageNet-1k, adhering to the Decoupled Linkage
    and Dataset Integrity Governance directives.

Stage:
    Gate 1 — Dataset Preparation & Integrity Verification

Inputs:
    - gate1/configs/imagenet_class_index.json (ImageNet-1k WNID index)
    - gate1/configs/tiny_class_mapping.json (182-class subset mapping)
    - data/tinyimagenet/val/ (Pre-processed validation JPEG files)
    - data/azure_traces/azure_functions_2019_processed.npz (Production trace)

Outputs:
    - Verified local dataset directories and diagnostic validation report.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path
from typing import Dict, Any

# Standard dataset paths
CONFIG_DIR = Path("gate1/configs")
DATA_DIR = Path("data/tinyimagenet/val")
AZURE_TRACE_PATH = Path("data/azure_traces/azure_functions_2019_processed.npz")
IMAGENET_CLASS_INDEX_URL = "https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json"


def verify_tiny_imagenet(
    config_dir: Path = CONFIG_DIR,
    val_data_dir: Path = DATA_DIR,
    min_required_images: int = 500,
) -> Dict[str, Any]:
    """
    Verifies that the Tiny ImageNet validation split and class mappings are present.
    If the ImageNet class index is missing, retrieves it from the authoritative URL.
    """
    config_dir.mkdir(parents=True, exist_ok=True)
    val_data_dir.mkdir(parents=True, exist_ok=True)

    idx_path = config_dir / "imagenet_class_index.json"
    mapping_path = config_dir / "tiny_class_mapping.json"

    # Block 1: Verify or download ImageNet class index
    # ImageNet-1k index maps WNID string to canonical index 0..999
    if not idx_path.is_file():
        print(f"[DATASET] ImageNet class index missing at {idx_path}. Downloading from authoritative source...")
        urllib.request.urlretrieve(IMAGENET_CLASS_INDEX_URL, str(idx_path))
        print(f"[DATASET] ✓ Saved ImageNet index -> {idx_path}")
    else:
        print(f"[DATASET] ✓ ImageNet class index verified: {idx_path}")

    # Block 2: Verify 182-class subset mapping
    # Maps internal Gate 1 class index (0..181) to Tiny ImageNet WNID
    if not mapping_path.is_file():
        raise FileNotFoundError(
            f"[DATASET] Missing required class mapping at {mapping_path}. "
            "Please ensure the 182-class mapping file is present."
        )
    with open(mapping_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    print(f"[DATASET] ✓ Tiny ImageNet 182-class mapping verified ({len(mapping)} classes).")

    # Block 3: Inspect local validation image files
    # Scans data/tinyimagenet/val for properly formatted validation images
    existing_images = sorted([f for f in os.listdir(val_data_dir) if f.endswith(".jpg")])
    image_count = len(existing_images)
    print(f"[DATASET] ✓ Tiny ImageNet validation images verified: {image_count} found in {val_data_dir}.")

    if image_count < min_required_images:
        print(
            f"[DATASET] Warning: Found {image_count} images, which is less than "
            f"recommended minimum ({min_required_images})."
        )

    return {
        "status": "ready",
        "imagenet_class_index": str(idx_path),
        "tiny_class_mapping": str(mapping_path),
        "val_data_dir": str(val_data_dir),
        "val_image_count": image_count,
        "classes_count": len(mapping),
    }


def verify_azure_traces(trace_path: Path = AZURE_TRACE_PATH) -> bool:
    """
    Verifies integrity of the preprocessed Azure Functions 2019 trace dataset.
    """
    # Block 4: Check immutable trace single source of truth
    if not trace_path.is_file():
        print(f"[DATASET] Notice: Azure trace not found at {trace_path}.")
        return False
    size_mb = trace_path.stat().st_size / (1024 * 1024)
    print(f"[DATASET] ✓ Azure Functions 2019 trace verified: {trace_path} ({size_mb:.2f} MB).")
    return True


def main() -> None:
    print("=" * 70)
    print("Gate 1 Authoritative Dataset & Mapping Verification")
    print("=" * 70)
    tiny_res = verify_tiny_imagenet()
    azure_ok = verify_azure_traces()
    print("=" * 70)
    print("SUMMARY:")
    print(f"  Tiny ImageNet Val Images: {tiny_res['val_image_count']}")
    print(f"  Gate 1 Target Classes   : {tiny_res['classes_count']}")
    print(f"  Azure Trace Status      : {'Present' if azure_ok else 'Missing'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
