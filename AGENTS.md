# Workspace Agent Governance Rules

These rules are active across the entire workspace. All agents, planners, and coders must adhere to these directives unconditionally.

## 1. Version Immutability
- Never alter the current working version of any evaluation or gate script unless fixing an active compile, syntax, or runtime crash.
- All optimizations, extensions, and refactors MUST be committed as new versioned files (e.g. `_v2.py`).

## 2. Decoupled Linkage & Zero Hardcoding
- Never hardcode upstream gate results, p-values, or intermediate metrics in downstream gates.
- Upstream gate outputs must be linked and loaded dynamically via verified typed schemas (Pydantic / TypedDict) from authoritative output manifests (`output/gateX_manifest.json` or `configs/calibration_config.json`).
- Downstream gate configs must specify the path to upstream artifacts rather than baking in assumptions.
- All operational variables, thresholds, tolerances, and filepaths must be defined in external config files (YAML/JSON).
- Only static, immutable constants (e.g., standard seed `SEED = 42`) belong in code.

## 3. Dedicated Workspace Virtual Environment
- All Python commands, environment checks, evaluations, and tests MUST strictly use the workspace virtual environment located at `./.venv` (`/home/vaibo/edgecompute/.venv/bin/python`, `./.venv/bin/pytest`, etc.).
- Never invoke system Python directly or use unverified global environments.

## 4. Self-Documenting Structure
- Every script must feature a header docstring detailing its role, gate stage, inputs, and outputs.
- Every functional block of code must state its purpose and underlying logic in descriptive inline comments.

## 5. Tool Grounding (Anti-Reinvention & Anti-Hallucination)
- **Tool Hierarchy**:
  1. **Existing libraries first**: Inspect and use standard packages (`scipy`, `pydantic`, `onnxruntime`, `openevolve`). Check installation in `./.venv` via `./.venv/bin/python -c "import <pkg>"` before writing code.
  2. **Minimal adaptation second**: Adapt existing tools only when interface mismatch occurs.
  3. **Custom code as last resort**: Never write custom implementations without proof that existing tools are incompatible.
- **Never hallucinate or mock libraries**: Do not create dummy modules or fake APIs to simulate missing dependencies.

## 6. Dataset Integrity
- The primary dataset in `data/` is the authoritative single source of truth.
- Preprocessed traces (e.g., `data/azure_traces/azure_functions_2019_processed.npz`) and image splits (`data/tinyimagenet/val`) must be preserved as immutable source artifacts.
- No synthetic fallbacks or ad-hoc data fabrication unless synthetic testing is explicitly commanded.

## 7. Advisor-First & Confirmation Gating (Anti-Impulsive Action)
- Never make impulsive, unilateral execution decisions or launch background jobs without explicit user consent.
- The agent must act strictly as an advisor first: analyze options, outline trade-offs, and lay out intuitive hypotheses in structured lists for user review and confirmation before branching out, modifying code, launching runs, or making workspace changes.
- Always present proposed directions in a clear, numbered list and wait for confirmation before acting.
