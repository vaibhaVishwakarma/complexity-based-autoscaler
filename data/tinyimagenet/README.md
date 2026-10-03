# Tiny ImageNet Validation Dataset & Conformal Calibration Split

> **Source:** Stanford Tiny ImageNet (`zh-plus/tiny-imagenet`)  
> **Class Mapping:** [`gate1/configs/tiny_class_mapping.json`](file:///home/vaibo/conformal-inference/gate1/configs/tiny_class_mapping.json)  
> **Class Index Reference:** [`gate1/configs/imagenet_class_index.json`](file:///home/vaibo/conformal-inference/gate1/configs/imagenet_class_index.json)

---

## Directory Contents

| Directory / File | Contents | Size / Count | Description |
| :--- | :--- | :---: | :--- |
| **`val/`** | JPEG Image Files | 10,000 images (~40 MB) | Standardized RGB validation images ($64 \times 64$ pixels) evaluated during Gate 1 distillation and RAPS calibration. |

---

## 1. File Naming Convention & Schema

Every image file inside `data/tinyimagenet/val/` follows the exact format:
```
val_<global_index>_label_<class_idx>.jpg
```
- **`global_index`** (`integer`, $0$ to $9999$): Zero-padded index identifying the validation sample.
- **`class_idx`** (`integer`, $0$ to $181$): Integer label corresponding to the filtered 182-class ontology.

### Example Entries:
- `val_00000_label_0.jpg`: Validation image #0 belonging to class index 0 (`n01443537` / goldfish).
- `val_00050_label_1.jpg`: Validation image #50 belonging to class index 1 (`n01629819` / European fire salamander).

---

## 2. 182-Class Mapping Rationale

Standard Tiny ImageNet contains 200 classes (500 train images, 50 val images per class). However, the teacher model (ResNet-50) is pretrained on ImageNet-1k (1,000 classes). 

To ensure exact mathematical alignment between the teacher and student models:
1. All 200 WordNet IDs (WNIDs) from Tiny ImageNet were mapped against the 1,000 classes of ImageNet-1k.
2. 18 classes in Tiny ImageNet do not appear in the standard ImageNet-1k 1,000-class index or have conflicting semantic scopes.
3. The remaining **182 intersecting classes** were indexed contiguously from $0$ to $181$ in [`gate1/configs/tiny_class_mapping.json`](file:///home/vaibo/conformal-inference/gate1/configs/tiny_class_mapping.json).
4. Validation images were re-indexed to retain only verified samples matching these 182 classes.

---

## 3. Use Cases Across Experimental Gates

### Gate 1: Knowledge Distillation & Model Shrinkage
- **Objective:** Compress ResNet-50 ($25.6\text{M parameters}$, $97.7\text{ MB}$, compute-heavy slow-path) down to EfficientNet-B0 ($5.3\text{M parameters}$, $21.4\text{ MB}$, sub-millisecond CPU fast-path).
- **Distillation Loss:** Combined cross-entropy and Kullback-Leibler divergence on softened logits ($T=2.0$):
  $$\mathcal{L}_{\text{KD}} = \alpha_{\text{KD}} T^2 D_{\text{KL}}(\sigma(z_s / T) \parallel \sigma(z_t / T)) + (1 - \alpha_{\text{KD}}) \mathcal{L}_{\text{CE}}(y, \sigma(z_s))$$

### Gate 1: True RAPS Conformal Prediction Calibration
- **Objective:** Guarantee statistical coverage without heuristics.
- **Nonconformity Score:** Uses Regularized Adaptive Prediction Sets (RAPS) with penalty parameters $k_{\text{reg}}=5, \lambda_{\text{reg}}=0.01$:
  $$E_i = \sum_{j=1}^{k_i} \hat{\pi}_{(j)}(X_i) + \lambda_{\text{reg}} \max(0, k_i - k_{\text{reg}}) + U_i \cdot \hat{\pi}_{(k_i)}(X_i)$$
- **Calibrated Outcome:** At nominal error $\alpha = 0.10$, RAPS calibration yields $\hat{q} = 0.79914$ on this validation split, achieving:
  - **Empirical Coverage:** $96.63\% \ge 90.0\%$ (statistically conservative).
  - **Fast-Path Singleton Ratio:** $f_{\text{fast}} = 50.0\%$ (exactly half of in-distribution inputs have $|\mathcal{C}(x)| = 1$).
  - **Average Set Size:** $\mathbb{E}[|\mathcal{C}(x)|] = 7.25$ classes.

---

## 4. Constraints & Data Integrity

- **Image Dimensions:** Strictly $64 \times 64$ pixels with 3 RGB color channels.
- **Pixel Value Range:** $[0, 255]$ uint8 on disk, normalized during inference via ImageNet standard mean $[0.485, 0.456, 0.406]$ and standard deviation $[0.229, 0.224, 0.225]$.
- **Label Bounds:** $y \in \{0, 1, \dots, 181\}$.
