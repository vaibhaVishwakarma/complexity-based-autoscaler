# Pipeline Governance & Engineering Rules

These rules govern all pipeline gates, evaluation modules, scripts, and agent activities in this workspace.

---

## Rule 1: Version Immutability & Modification Guardrail
- **Baseline Freezing**: The current version of any evaluation or gate script is an immutable baseline.
- **Permitted Edits**: You MUST NOT modify an existing version unless a syntax error, import error, or fatal runtime crash completely prevents execution.
- **New Features & Improvements**: Any algorithmic improvements, parameter adjustments, performance optimizations, or architectural cleanups MUST be authored in a new versioned file (e.g. `evaluate_aci_online_v2.py` or versioned submodule).
- This ensures reproducible historical comparisons without regression drift.

---

## Rule 2: Decoupled Linkage & Zero Hardcoding (The Gate Contract Mechanism)
- **No Hardcoded Upstream Data**: Data and results from previous gates must NEVER be hardcoded into downstream scripts.
- **Artifact Manifests as Interfaces**: Every gate writes its final verified metrics and thresholds to an authoritative output manifest (e.g., `gate1/output/gate1_manifest.json` or `gate1/configs/calibration_config.json`).
- **Downstream Linking Pattern**:
  1. Downstream gate configs specify the path to upstream gate manifests:
     ```yaml
     upstream_contracts:
       gate1_manifest: "gate1/configs/calibration_config.json"
     ```
  2. Downstream gates load and validate upstream outputs at runtime using **typed Pydantic schemas** (`Gate1Contract`, `Gate2Contract`).
  3. If an upstream artifact is missing or indicates failure, the downstream gate **fails fast** before consuming compute.
- **External Configuration**: Every operational variable (thresholds, $\alpha$ levels, batch sizes, test tolerances, paths) must live in an external configuration file (YAML/JSON), not in Python code.
- **Code Constants**: ONLY truly fixed, invariant constants (e.g., standard random seed `SEED = 42`, standard normalization tensors) may exist in the scripts.

---

## Rule 3: Dedicated Workspace Virtual Environment
- All Python scripts, tests, evaluations, and package inspections MUST strictly run using the repository's dedicated virtual environment located at `./.venv` (`/home/vaibo/edgecompute/.venv/bin/python`, `./.venv/bin/pytest`, etc.).
- Never invoke system Python directly or rely on global Python packages.

---

## Rule 4: Purpose-Driven Structure & Documentation
- **Script Header Mandate**: Every script must begin with a clear header docstring declaring:
  1. Script Role & Gate Identity.
  2. Inputs & Expected Types.
  3. Outputs & Destination Artifacts.
- **Block Purpose & Logic**: Every logical block of lines performing a discrete operation (e.g. data loader setup, score computation, ACI quantile update, error calculation) must have an explicit comment explaining its specific purpose and mathematical/business logic.

---

## Rule 5: Tool Grounding & Anti-Reinvention Hierarchy
You must follow a strict three-tier implementation hierarchy:
1. **Tier 1 (Mandatory First Step) — Verified Existing Tools**:
   - Always probe the environment first (`./.venv/bin/python -c "import <tool>"`) before authoring any logic.
   - Use standard industry tools and libraries (e.g., `scipy.stats`, `statsmodels`, `openevolve`, `pydantic`, `onnxruntime`, `torchvision`).
   - NEVER hallucinate libraries or mock nonexistent APIs (e.g., inventing dummy classes or fake modules).
2. **Tier 2 — Adaptation**:
   - If an existing library has minor interface mismatches with edge/cloud constraints, write a minimal adapter or subclass around the verified library.
3. **Tier 3 (Absolute Last Resort) — Bespoke Implementation**:
   - Author custom implementations ONLY if verified tools do not exist or are fundamentally incompatible.
   - When doing so, you must explicitly document why existing tools could not be used.

---

## Rule 6: Primary Dataset as Single Source of Truth (SSOT)
- Datasets must reside in the dedicated `data/` directory.
- Preprocessed artifacts (e.g., `data/azure_traces/azure_functions_2019_processed.npz` and `data/tinyimagenet/val`) are authoritative immutable source assets.
- Downstream gates must read from the verified primary dataset or typed upstream output artifacts; no gate may fabricate mock dataset records or synthetic fallbacks unless synthetic testing is explicitly commanded.
