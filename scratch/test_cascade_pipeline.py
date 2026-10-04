"""
test_cascade_pipeline.py — Verification of OpenEvolve Cascade Evaluation Engine

Role:
    Tests OpenEvolve's native Evaluator class against seed_policy.py to verify
    that Stage 1, Stage 2, and Stage 3 cascade correctly end-to-end under OpenEvolve.
"""

import asyncio
from pathlib import Path
from openevolve.config import Config
from openevolve.evaluator import Evaluator

WORKSPACE_ROOT = Path("/home/vaibo/edgecompute")
CONFIG_PATH = WORKSPACE_ROOT / "configs" / "evolution" / "openevolve_config.yaml"
SEED_PATH = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "seed_policy.py"
EVALUATOR_FILE = WORKSPACE_ROOT / "src" / "continuum_ext" / "evolution" / "openevolve_evaluator.py"

async def main():
    import os
    os.environ.setdefault("GEMINI_API_KEY", "dummy_key_for_offline_eval")
    print("Loading config from YAML...")
    config = Config.from_yaml(CONFIG_PATH)
    
    print(f"Creating Evaluator with evaluation_file={EVALUATOR_FILE}...")
    evaluator = Evaluator(
        config=config.evaluator,
        evaluation_file=str(EVALUATOR_FILE),
    )
    
    print(f"Reading seed code from {SEED_PATH}...")
    with open(SEED_PATH, "r") as f:
        seed_code = f.read()

    print(f"Running cascade evaluation via evaluator.evaluate_program...")
    metrics = await evaluator.evaluate_program(seed_code, program_id="seed_v1")
    
    print("Cascade evaluation completed!")
    print("Metrics returned:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    
    pending_artifacts = evaluator.get_pending_artifacts("seed_v1")
    if pending_artifacts:
        print("\nArtifacts returned:")
        for k in pending_artifacts.keys():
            print(f"  {k}: ({len(str(pending_artifacts[k]))} bytes)")
    
    assert "combined_score" in metrics, "combined_score missing from metrics!"
    assert metrics["stage1_passed"] == 1.0, "Stage 1 did not pass!"
    assert metrics["stage2_passed"] == 1.0, "Stage 2 did not pass!"
    assert "cost_savings" in metrics, "cost_savings missing from Stage 3 metrics!"
    print("\nALL CASCADE STAGES (1 -> 2 -> 3) VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
