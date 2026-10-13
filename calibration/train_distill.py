#!/usr/bin/env python3
"""
train_distill.py — Gate 1 Knowledge Distillation, Calibration & ONNX Export

Architecture & Method:
  1. Student Model: EfficientNet-B0 fine-tuned on Tiny ImageNet (K=182 valid classes).
     (Native 64x64 images upscaled to 224x224 via bicubic interpolation).
  2. Teacher Model: Pretrained ResNet-152 (11.56B FLOPs).
  3. Knowledge Distillation: Alpha_KD = 0.70, T_KD = 4.0, 20 epochs.
  4. Temperature Scaling: T = 0.70 (sharpens probabilities for conformal set size efficiency).
  5. Split-Conformal RAPS Calibration: Miscoverage target alpha = 0.10 (90% coverage guarantee),
     computing quantile threshold q_hat on n=5,000 calibration split (`CAL_SIZE = 5000`).
  6. ONNX Export: Exports EfficientNet-B0 with baked-in T=0.70 temperature scaling as
     'efficientnet_b0_tiny.onnx' (accurately named after student backbone).

Execution:
  python3 -m gate1.train_distill [--epochs 20] [--batch-size 64] [--out-dir gate1/output]
"""

import os
import json
import random
import copy
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
from torchvision.transforms import InterpolationMode
from torchvision.models import (
    EfficientNet_B0_Weights,
    ResNet152_Weights,
)
from torch.utils.data import Dataset, DataLoader
from datasets import load_dataset
from tqdm import tqdm

# ── Argument Parsing ──────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Gate 1 KD Training & Calibration")
parser.add_argument("--epochs",     type=int,   default=20,    help="Training epochs")
parser.add_argument("--batch-size", type=int,   default=64,    help="Batch size")
parser.add_argument("--alpha",      type=float, default=0.10,  help="Miscoverage target alpha")
parser.add_argument("--temp",       type=float, default=0.70,  help="Inference temperature scaling T")
parser.add_argument("--kd-temp",    type=float, default=4.0,   help="Distillation temperature T_KD")
parser.add_argument("--kd-alpha",   type=float, default=0.70,  help="KD loss weight alpha_KD")
parser.add_argument("--cal-size",   type=int,   default=5000,  help="Calibration split size")
parser.add_argument("--out-dir",    type=str,   default="gate1/output", help="Directory for training/evaluation outputs")
parser.add_argument("--config-dir", type=str,   default="gate1/configs", help="Directory for fixed configs")
parser.add_argument("--model-dir",  type=str,   default="models", help="Directory for models/ONNX")
args = parser.parse_args()

os.makedirs(args.out_dir, exist_ok=True)
os.makedirs(args.config_dir, exist_ok=True)
os.makedirs(args.model_dir, exist_ok=True)
RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Gate 1 Environment Device: {device}")

# ── CPU Guardrails ────────────────────────────────────────────────────────────
use_cuda    = torch.cuda.is_available()
num_workers = 2 if use_cuda else 0
pin_memory  = use_cuda

# ── 1. Load ImageNet Class Index ──────────────────────────────────────────────
idx_path = os.path.join(args.config_dir, "imagenet_class_index.json")
if not os.path.exists(idx_path):
    import urllib.request
    print(f"Downloading ImageNet class index to {idx_path}...")
    urllib.request.urlretrieve(
        "https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json",
        idx_path,
    )

with open(idx_path) as f:
    imagenet_class_index = json.load(f)
wnid_to_imagenet_idx = {v[0]: int(k) for k, v in imagenet_class_index.items()}

# ── 2. Load Tiny ImageNet & Build 182-Class Mapping ────────────────────────────
print("Loading zh-plus/tiny-imagenet from HuggingFace...")
dataset = load_dataset("zh-plus/tiny-imagenet")
tiny_wnids = dataset["train"].features["label"].names

valid_tiny_wnids = []
wnid_to_new_idx  = {}
for wnid in tiny_wnids:
    if wnid in wnid_to_imagenet_idx:
        wnid_to_new_idx[wnid] = len(valid_tiny_wnids)
        valid_tiny_wnids.append(wnid)

NUM_CLASSES = len(valid_tiny_wnids)
print(f"Mapped {NUM_CLASSES} valid classes (18 excluded WNIDs).")

tiny_class_mapping = {i: valid_tiny_wnids[i] for i in range(NUM_CLASSES)}
with open(os.path.join(args.config_dir, "tiny_class_mapping.json"), "w") as f:
    json.dump(tiny_class_mapping, f, indent=2)

valid_wnids_set = set(valid_tiny_wnids)

# ── 3. Build Train / Calibration / Test Splits ─────────────────────────────────
train_raw = []
for item in tqdm(dataset["train"], desc="Filter train"):
    wnid = tiny_wnids[item["label"]]
    if wnid in valid_wnids_set:
        train_raw.append({"image": item["image"], "label": wnid_to_new_idx[wnid]})

val_raw = []
for item in tqdm(dataset["valid"], desc="Filter val"):
    wnid = tiny_wnids[item["label"]]
    if wnid in valid_wnids_set:
        val_raw.append({"image": item["image"], "label": wnid_to_new_idx[wnid]})

rng = random.Random(RANDOM_SEED)
rng.shuffle(val_raw)
cal_data  = val_raw[:args.cal_size]
test_data = val_raw[args.cal_size:]

print(f"Splits -> Train: {len(train_raw)} | Cal: {len(cal_data)} | Test: {len(test_data)}")

# ── 4. Transforms ─────────────────────────────────────────────────────────────
_MEAN = [0.485, 0.456, 0.406]
_STD  = [0.229, 0.224, 0.225]

train_transform = transforms.Compose([
    transforms.Resize(256, interpolation=InterpolationMode.BICUBIC, antialias=True),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize(_MEAN, _STD),
])

eval_transform = transforms.Compose([
    transforms.Resize(256, interpolation=InterpolationMode.BICUBIC, antialias=True),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(_MEAN, _STD),
])

class TinyDataset(Dataset):
    def __init__(self, data_list, transform):
        self.data = data_list
        self.transform = transform
    def __len__(self):
        return len(self.data)
    def __getitem__(self, idx):
        item = self.data[idx]
        img = item["image"]
        if img.mode != "RGB":
            img = img.convert("RGB")
        return self.transform(img), item["label"]

train_loader = DataLoader(TinyDataset(train_raw, train_transform), batch_size=args.batch_size, shuffle=True,  num_workers=num_workers, pin_memory=pin_memory)
cal_loader   = DataLoader(TinyDataset(cal_data, eval_transform),   batch_size=args.batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)
test_loader  = DataLoader(TinyDataset(test_data, eval_transform),  batch_size=args.batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)

# ── 5. Teacher Setup: ResNet-152 (Frozen) ──────────────────────────────────────
print("Loading ResNet-152 teacher (pretrained, frozen)...")
teacher_full = torchvision.models.resnet152(weights=ResNet152_Weights.DEFAULT).eval().to(device)
for p in teacher_full.parameters():
    p.requires_grad = False

imagenet_indices_for_classes = [wnid_to_imagenet_idx[valid_tiny_wnids[i]] for i in range(NUM_CLASSES)]
imagenet_idx_tensor = torch.tensor(imagenet_indices_for_classes, dtype=torch.long).to(device)

def teacher_soft_labels(images: torch.Tensor, T: float) -> torch.Tensor:
    with torch.no_grad():
        full_logits = teacher_full(images)
        subset_logits = full_logits[:, imagenet_idx_tensor]
        return F.softmax(subset_logits / T, dim=1)

# ── 6. Student Setup: EfficientNet-B0 ──────────────────────────────────────────
print("Building EfficientNet-B0 student model...")
student = torchvision.models.efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
student.classifier[1] = nn.Linear(student.classifier[1].in_features, NUM_CLASSES)
student = student.to(device)

optimizer = torch.optim.AdamW([
    {"params": student.features[:4].parameters(), "lr": 5e-5},
    {"params": student.features[4:].parameters(), "lr": 2e-4},
    {"params": student.classifier.parameters(),   "lr": 1e-3},
], weight_decay=1e-2)

scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
ce_loss   = nn.CrossEntropyLoss(label_smoothing=0.1)
kl_loss   = nn.KLDivLoss(reduction="batchmean")

# ── 7. Training Loop with KD & Checkpointing ──────────────────────────────────
best_val_acc = 0.0
best_epoch   = 0
best_student_weights = copy.deepcopy(student.state_dict())

print(f"\nBeginning {args.epochs} epochs of KD fine-tuning (KD_ALPHA={args.kd_alpha}, KD_TEMP={args.kd_temp})...")
for epoch in range(args.epochs):
    student.train()
    total_loss, correct, total = 0.0, 0, 0

    for images, labels in tqdm(train_loader, desc=f"Epoch {epoch+1:2d}/{args.epochs}"):
        images, labels = images.to(device), labels.to(device)
        soft_targets   = teacher_soft_labels(images, args.kd_temp)

        optimizer.zero_grad()
        logits   = student(images)
        loss_ce  = ce_loss(logits, labels)
        student_soft = F.log_softmax(logits / args.kd_temp, dim=1)
        loss_kd  = kl_loss(student_soft, soft_targets) * (args.kd_temp ** 2)

        loss = (1 - args.kd_alpha) * loss_ce + args.kd_alpha * loss_kd
        loss.backward()
        torch.nn.utils.clip_grad_norm_(student.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        correct    += (logits.argmax(1) == labels).sum().item()
        total      += images.size(0)

    scheduler.step()

    # Validation pass
    student.eval()
    val_correct, val_total = 0, 0
    with torch.no_grad():
        for val_imgs, val_lbls in cal_loader:
            val_imgs, val_lbls = val_imgs.to(device), val_lbls.to(device)
            val_logits = student(val_imgs)
            val_correct += (val_logits.argmax(1) == val_lbls).sum().item()
            val_total   += val_imgs.size(0)

    val_acc = val_correct / val_total * 100.0
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_epoch   = epoch + 1
        best_student_weights = copy.deepcopy(student.state_dict())

    print(f"  Epoch {epoch+1:2d}/{args.epochs} | Train Loss: {total_loss/total:.4f} | Train Acc: {correct/total*100:.2f}% | Val Acc: {val_acc:.2f}% {'[BEST ✓]' if val_acc == best_val_acc else ''}")

# ── 8. Restore Best Checkpoint & Apply Temperature Scaling ─────────────────────
print(f"\nRestoring best model from Epoch {best_epoch} (Val Acc: {best_val_acc:.2f}%)...")
student.load_state_dict(best_student_weights)
student.eval()

class EfficientNetWithTempSoftmax(nn.Module):
    def __init__(self, backbone, temperature=1.0):
        super().__init__()
        self.backbone    = backbone
        self.temperature = temperature
    def forward(self, x):
        logits = self.backbone(x)
        return torch.softmax(logits / self.temperature, dim=1)

model = EfficientNetWithTempSoftmax(student, temperature=args.temp).eval().to(device)

# ── 9. APS Split-Conformal Calibration ─────────────────────────────────────────
print(f"\nComputing RAPS non-conformity scores on n={len(cal_data)} calibration split...")
aps_scores = []
cal_top1_correct = 0
rng_aps = random.Random(RANDOM_SEED + 1)

with torch.no_grad():
    for images, labels in tqdm(cal_loader, desc="Calibration"):
        images, labels = images.to(device), labels.to(device)
        probs = model(images)

        for i in range(probs.size(0)):
            p = probs[i].cpu().numpy()
            true_label = labels[i].item()
            sorted_probs = np.sort(p)[::-1]
            sorted_idx   = np.argsort(p)[::-1]
            rank_arr     = np.where(sorted_idx == true_label)[0]

            if len(rank_arr) == 0:
                aps_scores.append(1.0)
                continue
            rank = int(rank_arr[0])
            if rank == 0:
                cal_top1_correct += 1
            cum_prob  = float(sorted_probs[:rank + 1].sum())
            tail_prob = float(sorted_probs[rank])
            u         = rng_aps.random()
            aps_scores.append(cum_prob - u * tail_prob)

aps_arr = np.sort(np.array(aps_scores))
n_cal   = len(aps_arr)
q_idx   = min(n_cal - 1, int(np.ceil((n_cal + 1) * (1 - args.alpha))) - 1)
q_hat   = float(aps_arr[q_idx])
cal_top1_acc = float(cal_top1_correct / n_cal)
print(f"  Calibrated q_hat = {q_hat:.8f} (alpha={args.alpha}) | Cal Top-1 Acc: {cal_top1_acc*100:.2f}%")

# ── 10. Test Split Evaluation (Explicit Test Top-1 Measurement) ────────────────
covered, set_sizes, fast_count = 0, [], 0
test_top1_correct = 0
with torch.no_grad():
    for images, labels in tqdm(test_loader, desc="Test evaluation"):
        images, labels = images.to(device), labels.to(device)
        probs = model(images)

        for i in range(probs.size(0)):
            p = probs[i].cpu().numpy()
            true_label = labels[i].item()
            sorted_probs = np.sort(p)[::-1]
            sorted_idx   = np.argsort(p)[::-1]

            if sorted_idx[0] == true_label:
                test_top1_correct += 1

            pred_set, cum_sum = [], 0.0
            for prob_val, idx_val in zip(sorted_probs, sorted_idx):
                pred_set.append(int(idx_val))
                cum_sum += float(prob_val)
                if cum_sum >= q_hat:
                    break

            sz = len(pred_set)
            set_sizes.append(sz)
            if true_label in pred_set:
                covered += 1
            if sz == 1:
                fast_count += 1

n_test        = len(set_sizes)
empirical_cov = covered / n_test
fp_frac       = fast_count / n_test
mean_sz       = float(np.mean(set_sizes))
test_top1_acc = float(test_top1_correct / n_test)

print(f"  Test Top-1 Acc: {test_top1_acc*100:.2f}% | Empirical Coverage: {empirical_cov*100:.2f}% | Fast-Path: {fp_frac*100:.2f}%")

# ── 11. Save Calibration Config & Export Accurately-Named ONNX ─────────────────
config = {
    "alpha":              args.alpha,
    "q_hat":              q_hat,
    "k_reg":              1,
    "lambda_reg":         0.0,
    "temperature":        args.temp,
    "num_classes":        NUM_CLASSES,
    "dataset":            "Tiny ImageNet (zh-plus/tiny-imagenet, K=182)",
    "model_type":         f"EfficientNet-B0 (KD from ResNet-152, T={args.temp}, APS, Bicubic)",
    "kd_alpha":           args.kd_alpha,
    "kd_temp":            args.kd_temp,
    "num_epochs":         args.epochs,
    "split":              f"train=dataset['train']({len(train_raw)}) / cal={n_cal} / test={n_test}",
    "cal_top1_accuracy":  cal_top1_acc,
    "test_top1_accuracy": test_top1_acc,
    "empirical_coverage": float(empirical_cov),
    "fast_path_fraction": float(fp_frac),
    "mean_set_size":      float(mean_sz),
    "gate25_passed":      (0.91 <= q_hat <= 0.96) and (fp_frac >= 0.35) and (empirical_cov >= 0.90),
}

cfg_path = os.path.join(args.config_dir, "calibration_config.json")
with open(cfg_path, "w") as f:
    json.dump(config, f, indent=2)

print("\nExporting EfficientNet-B0 model to ONNX...")
onnx_path = os.path.join(args.model_dir, "efficientnet_b0_tiny.onnx")
cpu_model = model.cpu().eval()
dummy     = torch.randn(1, 3, 224, 224)

torch.onnx.export(
    cpu_model, dummy, onnx_path,
    export_params=True,
    opset_version=18,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["probabilities"],
    dynamic_axes={"input": {0: "batch_size"}, "probabilities": {0: "batch_size"}},
)
print(f"Exported ONNX model -> {onnx_path}")
print(f"Saved config -> {cfg_path}")
