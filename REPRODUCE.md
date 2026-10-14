# Extraction and Reproduction Guide
## Conformal-Gated Autoscaling for Heterogeneous Serving Cascades

This archive contains the complete, self-contained bundle for replicating the study, evaluating the champion controller, regenerating statistical tests, and reproducing all publication figures.

---

## 1. Archive Extraction

To extract the bundle into your target directory:

```bash
# If packaged as a zip file:
unzip conformal_autoscaler_bundle.zip -d edgecompute_bundle/
cd edgecompute_bundle/

# Or if packaged as a tarball:
tar -xzf conformal_autoscaler_bundle.tar.gz -C edgecompute_bundle/
cd edgecompute_bundle/
```

---

## 2. Environment Setup

All execution requires Python 3.10+ (Python 3.12 recommended). We enforce using a dedicated virtual environment:

```bash
# Create dedicated virtual environment
python3 -m venv .venv

# Activate virtual environment
source ./.venv/bin/activate

# Upgrade pip and install pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify standard package installation
./.venv/bin/python -c "import numpy, scipy, pydantic, onnxruntime; print('Environment initialized successfully!')"
```

---

## 3. Directory Layout in this Bundle

* `contracts/` — Pydantic typed schemas for Gate 1 and Gate 2 manifests.
* `configs/` — Workload scenario YAMLs (13 regimes) and OpenEvolve v7 config.
* `data/` — Authoritative datasets:
  * `data/azure_traces/azure_functions_2019_processed.npz` (24h Azure diurnal trace).
  * `data/tinyimagenet/val/` (TinyImageNet validation split).
* `models/` — Exported ONNX graphs (`efficientnet_b0_tiny.onnx`, `gate6_resnet152.onnx`).
* `gate1/` — Validity Gate 1 calibration scripts and verified outputs.
* `gate2/` — Validity Gate 2 hardware service rate profiling and Spearman correlation tests.
* `src/continuum_ext/` — Systems package: controllers, evolutionary harness, physical realism, workload generators.
* `clones/` — Outsourced execution frameworks (`ContinuumBench`, `eclypse`, `openevolve`).
* `scripts/` — Active reproduction, evaluation, and figure generation scripts.
* `output/` — Authoritative v7 outputs:
  * `output/champion_policy_v7_smooth.py` (canonical policy `c614055a`).
  * `output/step8_v7_multiseed_runs/multiseed_summary.csv` (1,300 run records).
  * `output/step8_v7_multiseed_runs/step8_v7_statistical_manifest.json` (authoritative hypothesis tests).
  * `output/eval_v7_champion_smooth/` (delay ladder and regime traces).
* `figures/` — Pre-generated publication figures (PNG and vector PDF).
* `paper/` — Pre-built publication PDF (`draft3_prebuilt.pdf`).
* `paper_references/` — BibTeX bibliography (`references.bib`) and literature taxonomies.
* `references/` — Reference research papers and benchmark methodology documentation.
* `docs/` — Authoritative specifications (`CERTIFIED_NUMBERS.md`, `FIGURE_SPECS.md`, `system_architecture.md`).
* `.agents/` and `skills/` — Agent skills and operational rules.
* `AGENTS.md` — Workspace governance and immutability rules.

---

## 4. End-to-End Study Reproduction Steps

### Step 1: Re-verify Gate 1 (Split-Conformal RAPS Calibration)
Verifies the non-conformity score quantile ($\hat{q} = 0.79914$ at $\alpha = 0.10$) and fast-path singleton exit safety:
```bash
./.venv/bin/python gate1/calibrate_export_onnx.py \
    --val_dir data/tinyimagenet/val \
    --output_config gate1/configs/calibration_config.json \
    --alpha 0.10
```

### Step 2: Re-verify Gate 2 (Hardware Profiling & Queue Grounding)
Verifies the Tesla T4 service rate ($\mu = 16.0\text{ RPS/worker}$) and queuing-aware Spearman correlation ($r_s > 0.40$):
```bash
./.venv/bin/python gate2/recompute_spearman.py
```

### Step 3: Reproduce Statistical Processing & Hypothesis Tests
Re-computes all paired Wilcoxon signed-rank tests, Cohen's $d$, and 95% confidence intervals from `multiseed_summary.csv`:
```bash
./.venv/bin/python scripts/process_step8_v7_statistics.py
```
Output files updated:
* `output/step8_v7_multiseed_runs/hypothesis_tests.json`
* `output/step8_v7_multiseed_runs/statistical_report.md`
* `docs/STEP8_V7_MULTISEED_STATISTICAL_VALIDATION_REPORT.md`

### Step 4: Regenerate Publication Figures
Regenerates Figures 1 through 9 in both 300 DPI PNG and publication vector PDF:
```bash
# Generate core benchmark plots (Fig 1 - Fig 7, Fig 8)
./.venv/bin/python scripts/generate_paper_figures_v7.py

# Generate testbed architecture diagram
./.venv/bin/python scripts/generate_testbed_figure.py
```
Check `figures/` to view updated plots.

### Step 5: (Optional) Re-run Full 1,300 Multi-Seed Benchmark from Scratch
To execute all 1,300 simulation runs across 5 controller paradigms, 13 regimes, and 20 random seeds (`1042`–`1061`):
```bash
./.venv/bin/python scripts/run_step8_multiseed_v7.py \
    --policy output/champion_policy_v7_smooth.py \
    --output_dir output/step8_v7_multiseed_runs \
    --seeds 20 \
    --boot_delay 15.0
```

---

## 5. Ground Truth Verification

After running Step 3, verify that metrics match [`docs/CERTIFIED_NUMBERS.md`](docs/CERTIFIED_NUMBERS.md):
* **Proposed Deadline Misses**: `0.00 ± 0.00` across all 260 runs (100% SLA compliance).
* **Proposed Cost**: `1,041.8 ± 50.4` worker-seconds (51.46% compute savings vs. Fixed Peak).
* **Proposed Flapping**: `18.2 ± 0.7` flaps/run (76.7% churn reduction vs. InferLine).
* **Wilcoxon p-values**:
  * vs. InferLine: $p = 5.74 \times 10^{-15}$ (cost), $2.15 \times 10^{-44}$ (flaps), $3.43 \times 10^{-36}$ (misses).
  * vs. HPA: $p = 3.22 \times 10^{-44}$ (cost).
  * vs. KEDA: $p = 4.80 \times 10^{-44}$ (misses).
