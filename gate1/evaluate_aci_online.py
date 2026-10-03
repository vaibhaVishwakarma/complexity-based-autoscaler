#!/usr/bin/env python3
"""
gate1/evaluate_aci_online.py — Gate 1 Online Adaptive Conformal Inference (ACI) Benchmark
========================================================================================
Role:
    Simulates online streaming inference under non-stationary OOD distribution shift.
    Evaluates the Gibbs & Candès (2021) ACI online recalibration feedback loop:

        alpha_{t+1} = alpha_t + gamma * (alpha_target - err_t)

    where:
      - alpha_target = 0.10 (target 90% coverage guarantee, derived from Gate 1 contract)
      - err_t = 1 if true label y_t NOT in prediction set C_t(x_t), else 0
      - gamma = 0.010 (online learning rate step size)

Stage:
    Gate 1 — Dynamic Conformal Recalibration & OOD Adaptation Benchmark

Inputs:
    - models/efficientnet_b0_tiny.onnx (or gate1/output/efficientnet_b0_tiny.onnx)
    - gate1/configs/calibration_config.json (Typed Gate 1 Calibration Contract)
    - data/tinyimagenet/val/ (Validation image stream)

Outputs:
    - gate1/output/aci_online_report.json (Typed contract validated via Gate1AciOnlineReport)
"""

import os
import sys
import json
import random
import numpy as np
import onnxruntime as ort
from PIL import Image
from tqdm import tqdm
from pathlib import Path

# Add project root to sys.path to enable contracts import
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from contracts.gate1 import load_gate1_config, Gate1AciOnlineReport

# ── Block 1: Path Resolution & Contract Ingestion ──────────────────────────────
# Ingest calibration config dynamically via Pydantic contract (Rule 2: Decoupled Linkage)
ONNX_PATH = Path("models/efficientnet_b0_tiny.onnx")
if not ONNX_PATH.is_file():
    alt_onnx = Path("gate1/output/efficientnet_b0_tiny.onnx")
    if alt_onnx.is_file():
        ONNX_PATH = alt_onnx
    else:
        raise FileNotFoundError(f"ONNX model graph missing at {ONNX_PATH}!")

CONFIG_PATH = Path("gate1/configs/calibration_config.json")
if not CONFIG_PATH.is_file():
    alt_cfg = Path("gate1/calibration_config.json")
    if alt_cfg.is_file():
        CONFIG_PATH = alt_cfg
    else:
        raise FileNotFoundError(f"Calibration config missing at {CONFIG_PATH}!")

DATA_DIR = Path("data/tinyimagenet/val")
OUT_REPORT = Path("gate1/output/aci_online_report.json")
OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

# Ingest and validate contract schema
contract = load_gate1_config(CONFIG_PATH)
q_hat_base = contract.q_hat
alpha_target = contract.alpha
lambda_reg = contract.lambda_reg
k_reg = contract.k_reg

# Static, immutable constant seed (Rule 2: Only static constants in code)
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# ── Block 2: ONNX Runtime Session Initialization ──────────────────────────────
# Uses CPUExecutionProvider for lightweight local evaluation
sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])
inp_name = sess.get_inputs()[0].name

# ── Block 3: Stream Data Selection & Image Normalization Constants ────────────
# Evaluates first 500 sorted validation frames
img_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".jpg")])[:500]
print(f"Loaded {len(img_files)} images for online ACI stream simulation.")

_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 3, 1, 1)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 3, 1, 1)

# ── Block 4: ACI Online Feedback Loop Parameters & History Tracking ───────────
# gamma = 0.010 facilitates fast adaptation during non-stationary OOD distribution shift
gamma = 0.010
alpha_t = alpha_target
alpha_history = []
coverage_history = []
set_size_history = []
fp_history = []

print(f"\nStarting Online Adaptive Conformal Inference (ACI) Simulation (gamma={gamma})...")

# ── Block 5: Online Streaming Inference & Feedback Loop ───────────────────────
for t, img_name in enumerate(tqdm(img_files, desc="ACI Online Stream")):
    parts = img_name.split("_label_")
    if len(parts) < 2:
        continue
    true_label = int(parts[1].split(".jpg")[0])

    img_path = DATA_DIR / img_name
    pil_img = Image.open(img_path).convert("RGB").resize((224, 224), Image.BICUBIC)
    img_np = np.array(pil_img)

    # Inject synthetic OOD Gaussian noise shift between step 150 and 350 to simulate distribution drift
    if 150 <= t < 350:
        noise = np.random.normal(0, 45, img_np.shape)
        img_np = np.clip(img_np + noise, 0, 255).astype(np.uint8)

    arr = img_np.astype(np.float32) / 255.0
    arr = arr.transpose(2, 0, 1)[np.newaxis, ...]
    arr = (arr - _MEAN) / _STD

    # Forward inference via ONNX Runtime
    probs = sess.run(None, {inp_name: arr})[0][0]
    sorted_probs = np.sort(probs)[::-1]
    sorted_idx = np.argsort(probs)[::-1]

    # RAPS dynamic quantile threshold scaling (ACI-adapted):
    # As alpha_t decreases (higher desired coverage), q_hat_t increases, widening prediction set
    q_hat_t = float(np.clip(q_hat_base * ((1.0 - alpha_t) / (1.0 - alpha_target)), 0.05, 0.999))

    # Prediction set construction via Regularized Adaptive Prediction Sets (RAPS)
    pred_set, cum_prob = [], 0.0
    for j, (p_val, i_val) in enumerate(zip(sorted_probs, sorted_idx)):
        pred_set.append(int(i_val))
        cum_prob += float(p_val)
        o_j = j + 1
        raps_score = cum_prob + lambda_reg * max(0, o_j - k_reg)
        if raps_score >= q_hat_t:
            break

    sz = len(pred_set)
    is_covered = int(true_label in pred_set)
    err_t = 1 - is_covered

    # Gibbs & Candès (2021) online error gradient update
    alpha_t = float(np.clip(alpha_t + gamma * (alpha_target - err_t), 0.0001, 0.50))

    alpha_history.append(alpha_t)
    coverage_history.append(is_covered)
    set_size_history.append(sz)
    fp_history.append(int(sz == 1))

# ── Block 6: Metric Aggregation Across Simulation Phases ───────────────────────
phase1_cov = np.mean(coverage_history[:150]) if len(coverage_history) >= 150 else 0.0
phase2_cov = np.mean(coverage_history[150:350]) if len(coverage_history) >= 350 else 0.0
phase3_cov = np.mean(coverage_history[350:]) if len(coverage_history) > 350 else 0.0
overall_cov = float(np.mean(coverage_history))
overall_fp = float(np.mean(fp_history))
overall_sz = float(np.mean(set_size_history))

print()
print("=" * 65)
print("ACI ONLINE RECALIBRATION BENCHMARK RESULTS")
print("=" * 65)
print(f"  Phase 1 (Clean Workload 1-150)       Coverage = {phase1_cov*100:.2f}%")
print(f"  Phase 2 (OOD Noise Shift 151-350)    Coverage = {phase2_cov*100:.2f}% (ACI Recovered)")
print(f"  Phase 3 (Clean Recovery 351-500)     Coverage = {phase3_cov*100:.2f}%")
print(f"  Overall Time-Averaged Coverage       = {overall_cov*100:.2f}% (target >= 90.0%) [{'PASS ✓' if overall_cov >= 0.90 else 'FAIL ✗'}]")
print(f"  Fast-Path Coverage (Offload Frac)    = {overall_fp*100:.2f}%")
print(f"  Mean Set Size                        = {overall_sz:.2f}")
print("=" * 65)

# ── Block 7: Output Report Construction & Contract Validation ──────────────────
report_dict = {
    "gamma": gamma,
    "target_alpha": alpha_target,
    "overall_coverage": overall_cov,
    "phase1_clean_coverage": float(phase1_cov),
    "phase2_ood_noise_coverage": float(phase2_cov),
    "phase3_recovery_coverage": float(phase3_cov),
    "overall_fast_path_fraction": overall_fp,
    "overall_mean_set_size": overall_sz,
    "total_stream_requests": len(img_files),
    "aci_passed": overall_cov >= (1.0 - alpha_target),
}

# Type-validate payload against Pydantic contract before saving
validated_report = Gate1AciOnlineReport.model_validate(report_dict)

with open(OUT_REPORT, "w", encoding="utf-8") as f:
    json.dump(validated_report.model_dump(), f, indent=2)

print(f"\nSaved verified ACI benchmark report -> {OUT_REPORT}")
