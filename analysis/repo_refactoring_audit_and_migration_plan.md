# Repository Refactoring Audit, Script Relevance & Migration Plan

## 1. Overview & Objectives

This audit provides a comprehensive roadmap for refactoring the research repository to meet journal-grade software engineering standards. The refactoring addresses three foundational problems:
1. **Ad-hoc Path Resolution Hacks**: Widespread usage of `sys.path.insert(0, ...)` and relative parent traversal (`Path(__file__).resolve().parent...`) to resolve imports.
2. **Ambiguous Legacy Naming**: The pipeline stages `gate1` and `gate2` reflect early verification checkpoints rather than descriptive scientific domains (Statistical Conformal Calibration and Empirical Hardware Latency Profiling).
3. **Dead Code & Evolutionary Debris**: Accumulation of superseded intermediate scripts (e.g. 11 intermediate evolutionary seeds and evaluators, duplicated distillation scripts, and broken phantom modules).

All changes are governed by the **Methodology Invariance Guardrail**: zero changes to core mathematical logic, seeds (`SEED = 42`), conformal quantile calculations, or simulation state equations.

---

## 2. Universal Governance Rules (Mandatory & Permanent)

1. **Root Module Execution**:
   - Every script must be executed strictly from the workspace root directory.
   - Invocation must strictly use the module flag `-m`:
     ```bash
     ./.venv/bin/python -m <module_path>
     # Example:
     ./.venv/bin/python -m scripts.generate_testbed_figures
     ```
   - Running scripts via `cd <subdir> && python <file>.py` or `python path/to/file.py` is forbidden.

2. **Absolute Clean Module Imports (Zero Path Hacks)**:
   - `sys.path.append()`, `sys.path.insert()`, and manual path resolution for imports are strictly prohibited.
   - All workspace imports must be anchored at the repository root (e.g., `from src.continuum_ext...`, `from contracts...`).

3. **Workspace Virtual Environment Discipline**:
   - All tests, evaluations, figure renderings, and sanity checks must execute using `./.venv/bin/python`.

---

## 3. Stage 1: Script Audit & Relevance Categorization

### Category A: Active & Essential Scripts (Retain & Refactor)

These scripts constitute the active scientific workflow, benchmark testbed, and publication pipeline:

| Script Path | Primary Role | Status & Action |
| :--- | :--- | :--- |
| `scripts/run_step8_multiseed_v7.py` | Master experimental driver (1,300 benchmark runs across 20 seeds x 13 regimes) | **Active / Core**. Remove `sys.path` hacks in subprocess call. |
| `scripts/process_step8_v7_statistics.py` | Hypothesis testing engine (Wilcoxon, t-tests, Cohen's d, CIs) | **Active / Core**. Clean module imports. |
| `scripts/generate_paper_figures_v7.py` | Generates Publication Figures 1–9 (PNG & vector PDF) | **Active / Core**. Clean module imports. |
| `scripts/generate_testbed_figure.py` | Testbed architecture schematic generator | **Active / Core**. Rename to plural `generate_testbed_figures.py`. |
| `scripts/run_evolution_v7.py` | Master launcher for OpenEvolve policy search | **Active / Core**. Remove `sys.path.insert` loop. |
| `scripts/evaluate_v7_raw_results.py` | Realism stress ladder evaluator for candidate policies | **Active / Core**. Clean module imports. |
| `gate1/download_datasets.py` | Dataset integrity verification (TinyImageNet & Azure traces) | **Active / Core**. Relocate to semantic directory. |
| `gate1/recalibrate_onnx.py` | ONNX runtime coverage and probability sanity test | **Active / Core**. Relocate to semantic directory. |
| `gate1/evaluate_aci_online.py` | Online ACI non-stationary OOD stream benchmark | **Active / Core**. Remove `sys.path.insert(0, ROOT_DIR)`. |
| `gate1/evaluate_imagenet_c.py` | Tiny ImageNet-C corruption benchmark across 5 severities | **Active / Core**. Remove `sys.path.insert(0, ROOT_DIR)`. |
| `gate1/calibrate_export_onnx.py` | RAPS split-conformal quantile calibration & ONNX exporter | **Active / Core** (Training/Export environment). |
| `gate1/train_distill_new.py` | Multi-GPU 4-phase calibrated fast-path distillation | **Active / Core** (Canonical model training recipe). |
| `gate2/profile_triton_service.py` | Empirical Triton latency surface benchmarking & Spearman | **Active / Core**. Fix phantom import `core.cross_gate_registry`. |
| `gate2/generate_figures.py` | Generates hardware latency surface figure | **Active / Core**. Fix phantom import `core.cross_gate_registry`. |
| `src/continuum_ext/controllers/conformal_controllers.py` | Core autoscalers (Proposed Conformal, InferLine, HPA, KEDA) | **Active / Core**. |
| `src/continuum_ext/controllers/inferline_exact.py` | Mechanistic InferLine envelope scaler implementation | **Active / Core**. |
| `src/continuum_ext/controllers/inferline_planner.py` | InferLine stage capacity optimization planner | **Active / Core**. |
| `src/continuum_ext/controllers/extensions_local.py` | Simulation runtime controller registration hook | **Active / Core**. |
| `src/continuum_ext/evolution/champion_policy_v7_smooth.py` | Authoritative production Champion policy (`c614055a`) | **Active / Core**. |
| `src/continuum_ext/evolution/openevolve_evaluator_v7.py` | Realism-aware dual-tier parallel fitness evaluator | **Active / Core**. |
| `src/continuum_ext/evolution/seed_policy_v7.py` | Canonical seed policy for v7 evolutionary search | **Active / Core**. |
| `src/continuum_ext/realism/dynamic_batching_model.py` | Triton batch formation delay model | **Active / Core**. |
| `src/continuum_ext/realism/network_batch_link.py` | WAN packet queuing and transit delay link | **Active / Core**. |
| `src/continuum_ext/workload/conformal_workloads.py` | 13-regime decoupled complexity workload generators | **Active / Core**. |

---

### Category B: Candidates for Deletion / Archival (Approval Requested)

These files represent superseded evolutionary milestones, dead or redundant scripts, and phantom imports:

| File Path | Description & Role | Recommendation | Rationale |
| :--- | :--- | :--- | :--- |
| `gate1/train_distill.py` | Older single-GPU distillation script | **Delete** | Superseded by `gate1/train_distill_new.py`. Uses legacy $T=0.70$ sharpening explicitly corrected in Scrutiny Fix #2. |
| `gate2/recompute_spearman.py` | Offline Spearman recomputer | **Delete** | Duplicates logic already in `profile_triton_service.py`. Contains fatal unresolved import `from core.cross_gate_registry import load_registry`. Output already saved in `gate2_spearman_result.json`. |
| `src/continuum_ext/evolution/seed_policy.py` | v1 Seed policy | **Delete** | Superseded evolutionary ancestor; v7 champion is active. |
| `src/continuum_ext/evolution/seed_policy_v2.py` | v2 Seed policy | **Delete** | Superseded evolutionary ancestor. |
| `src/continuum_ext/evolution/seed_policy_v3.py` | v3 Seed policy | **Delete** | Superseded evolutionary ancestor. |
| `src/continuum_ext/evolution/seed_policy_v5.py` | v5 Seed policy | **Delete** | Superseded evolutionary ancestor. |
| `src/continuum_ext/evolution/seed_policy_v6.py` | v6 Seed policy | **Delete** | Superseded evolutionary ancestor. |
| `src/continuum_ext/evolution/openevolve_evaluator.py` | v1 Evaluator | **Delete** | Superseded; lacks physical realism ladder. |
| `src/continuum_ext/evolution/openevolve_evaluator_v2.py` | v2 Evaluator | **Delete** | Superseded. |
| `src/continuum_ext/evolution/openevolve_evaluator_v3.py` | v3 Evaluator | **Delete** | Superseded. |
| `src/continuum_ext/evolution/openevolve_evaluator_v5.py` | v5 Evaluator | **Delete** | Superseded; contains duration trap fixed in v6/v7. |
| `src/continuum_ext/evolution/openevolve_evaluator_v6.py` | v6 Evaluator | **Delete** | Superseded by canonical v7 evaluator. |
| `src/continuum_ext/evolution/population_policy.py` | Unused helper policy template | **Delete** | Orphaned; never referenced by OpenEvolve runners or benchmarks. |

---

### Category C: Unit Tests to Reposition

| File Path | Description | Recommendation |
| :--- | :--- | :--- |
| `src/continuum_ext/controllers/validate_inferline.py` | Analytical unit test for InferLine exact logic | Relocate to `tests/test_inferline_exact.py`. Remove `sys.path` hacks. |
| `src/continuum_ext/controllers/validate_inferline_planner.py` | Analytical unit test for InferLine algorithms 1 & 2 | Relocate to `tests/test_inferline_planner.py`. Remove `sys.path` hacks. |

---

## 4. Stage 2: Naming Rectification Architecture

### The Problem with `gate1` and `gate2`
The terms `gate1` and `gate2` originated as internal engineering checkpoints. In an academic publication or open-source scientific repository:
1. `gate1` represents **Conformal Calibration & Edge Model Evaluation** (distillation, RAPS calibration, ACI stream tracking, ImageNet-C corruption benchmarks).
2. `gate2` represents **Empirical Hardware Latency Profiling** (Triton dynamic batch profiling on Tesla T4/Intel CPU and M/M/1 queuing-aware Spearman correlation).

### Proposed Semantic Directory & Contract Mapping

```
Existing Legacy Name          --> Proposed Semantic Name
-------------------------------------------------------------------------------
gate1/                        --> calibration/ (or conformal_calibration/)
gate1/configs/                --> configs/calibration/
gate1/output/                 --> output/calibration/
gate1/train_distill_new.py    --> calibration/train_distillation.py
gate1/calibrate_export_onnx.py--> calibration/calibrate_export_onnx.py
gate1/evaluate_aci_online.py  --> calibration/evaluate_aci_online.py
gate1/evaluate_imagenet_c.py  --> calibration/evaluate_imagenet_c.py
gate1/recalibrate_onnx.py     --> calibration/verify_onnx_calibration.py
gate1/download_datasets.py    --> calibration/verify_datasets.py

gate2/                        --> profiling/ (or hardware_profiling/)
gate2/output-gpu-t4/          --> output/profiling/gpu-t4/
gate2/output-cpu-c7i/         --> output/profiling/cpu-c7i/
gate2/profile_triton_service.py-> profiling/profile_hardware_latency.py
gate2/generate_figures.py     --> profiling/generate_profiling_figures.py

contracts/gate1.py            --> contracts/calibration.py
contracts/gate2.py            --> contracts/profiling.py

scripts/generate_testbed_figure.py -> scripts/generate_testbed_figures.py
```

---

## 5. Stage 3: Path Resolution & Clean Import Execution Plan

### Step-by-Step Execution:
1. **Remove `sys.path` Hacks Across All Files**:
   - In `evaluate_aci_online.py` and `evaluate_imagenet_c.py`: remove `sys.path.insert(0, str(ROOT_DIR))`.
   - In `scripts/run_evolution_v7.py`: remove `sys.path.insert` iterations for `SRC_PATH`, `CONTINUUM_SRC`, etc.
   - In `scripts/run_step8_multiseed_v7.py`: remove `sys.path.insert` injected into subprocess strings.
2. **Resolve Missing `core.cross_gate_registry`**:
   - In profiling scripts (`profile_triton_service.py` and `generate_figures.py`), replace nonexistent `core.cross_gate_registry` with authoritative contracts from `contracts.profiling` and `contracts.calibration`.
3. **Formalize Root Execution Verification**:
   - Execute all verification commands via:
     ```bash
     ./.venv/bin/python -m pytest tests/
     ./.venv/bin/python -m calibration.verify_onnx_calibration
     ./.venv/bin/python -m scripts.generate_testbed_figures
     ./.venv/bin/python -m scripts.generate_paper_figures_v7
     ```
