#!/usr/bin/env python3
"""
gate2/generate_figures.py — Standalone Generator for Gate 2 Figure 2

Role:
    Regenerates Figure 2 for both hardware pathways (Tesla T4 GPU & AWS c7i-flex CPU)
    using the corrected scrutiny-fixed data (queuing-aware, jitter, W_batch).

Compliance:
    AGENTS.md Rule #2 — Zero hardcoding; contract ingestion.
    AGENTS.md Rule #3 — Workspace virtual environment; module execution (-m).
    AGENTS.md Rule #4 — Self-documenting structure.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from gate2.profile_triton_service import render_profiling_figure

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Gate2FigureGen")

GATE2_DIR = Path("gate2")
GPU_DIR = GATE2_DIR / "output-gpu-t4"
CPU_DIR = GATE2_DIR / "output-cpu-c7i"


def generate_for_pathway(dir_path: Path, label: str) -> None:
    profile_path = dir_path / "triton_service_profiles.json"
    spearman_path = dir_path / "gate2_spearman_result.json"
    out_fig = dir_path / "figure2_profiling_surface.png"

    if not profile_path.is_file() or not spearman_path.is_file():
        logger.warning("Manifests missing in %s, skipping.", dir_path)
        return

    with open(profile_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    with open(spearman_path, "r", encoding="utf-8") as f:
        spearman = json.load(f)

    render_profiling_figure(profiles.get("gpu_profiles_raw", []), spearman, out_fig)
    logger.info("Successfully generated %s figure -> %s", label, out_fig)


def main() -> None:
    generate_for_pathway(GPU_DIR, "Tesla T4 GPU")
    generate_for_pathway(CPU_DIR, "AWS c7i-flex CPU")


if __name__ == "__main__":
    main()
