### **Q1 Journal-Grade Forensic Scrutiny Report: Validity Gate 1**

**To:** Cloud Systems Engineering Team  
**From:** Lead Systems & Statistical Auditor  
**Subject:** Forensic Audit of Fast-Path Safety & Online Calibration (Gate 1) — Defending Scientific Integrity for Q1 Peer Review  

---

### **Executive Summary**

Existing literature on split-conformal prediction and adaptive cascades—such as *RAPS* (ICLR 2021) \\(\\), *ACI* (NeurIPS 2021) \\(\\), and *CADS* (IEEE ICIP 2026) \\(\\)—demands absolute transparency in statistical guarantees and physical validation. The objective of **Validity Gate 1** is to establish that our lightweight fast-path model (`EfficientNet-B0`), calibrated via temperature scaling and conformal prediction, maintains a selective error rate (\\(\text{Err}_{\text{selective}}\\)) **\\(\le 10\%\\)** under baseline traffic and recovers coverage via **Adaptive Conformal Inference (ACI)** under non-stationary drift \\(\\).

However, this forensic audit reveals **four severe scientific discrepancies, mathematical misrepresentations, and validation mismatches** in the current Gate 1 specification (`gate1-README.md` and associated reports) \\(\\). Left uncorrected, these issues represent critical vulnerabilities that peer reviewers will identify as statistical masking tricks. 

Below is the line-by-line forensic report and the actionable refactoring matrix required to secure a pass.

---

### **Part 1: Detailed Forensic Audit of Implementation Flaws & "Tricks"**

```
                       SUMMARY OF DETECTED GATE 1 VULNERABILITIES
  
  [1. Score Misrepresentation] ──► Claims "RAPS" but implements unregularized, randomized "APS"
  [2. Temperature Sharpening]  ──► Uses T = 0.70 to artificially pad singleton offloads (FP_frac)
  [3. Composite Metric Trick]  ──► Claims to eliminate "Weighted Selective Error" but relies on it in metrics.md
  [4. ACI vs. Table Conflict]  ──► Claims 90% coverage recovery but image-C table reports 45%-50% coverage
  [5. Dataset Scope Illusion]  ──► Implies full ImageNet-C validation on a pruned K=182 class subset
```

---

#### **1. The Conformal Score Misrepresentation (APS Masked as RAPS)**
In Section 3 (Step 3: Conformal Calibration), the README claims to implement **Regularized Adaptive Prediction Sets (RAPS)** \\(\\). It provides the following mathematical formulation for the non-conformity score:
\\[s_i(x_i, y_i) = \sum_{j=1}^{\text{rank}(y_i)} \hat{\pi}_{(j)}(x_i) - u_i \cdot \hat{\pi}_{(\text{rank}(y_i))}(x_i) \quad \text{where } u_i \sim \text{Uniform}(0, 1)\\]

*   **The Flaw:** This is **not the RAPS score**. This is the mathematical definition of **randomized APS** (Adaptive Prediction Sets) \\(\\). In the RAPS paper (Angelopoulos et al., ICLR 2021) \\(\\), the true RAPS non-conformity score includes a vital cumulative regularization penalty to suppress noisy tail probabilities \\(\\):
    \\[S(x, y) = \sum_{y': \hat{\pi}_x(y') \ge \hat{\pi}_x(y)} \hat{\pi}_x(y') + \lambda \cdot (o_x(y) - k_{\text{reg}})^+ - u \cdot \hat{\pi}_x(y)\\]
    Without the regularization penalty (\\(\lambda = 0\\)), RAPS collapses directly back to APS \\(\\).
*   **The Consequence:** APS is highly sensitive to noisy, uncalibrated tail probabilities far down the classification sorted index \\(\\). By omitting the regularizer, the constructed prediction sets will suffer from a heavy tail under uncertainty \\(\\). This directly degrades our gateway performance because large set sizes mean fewer singletons (collapsing our fast-path offload fraction, \\(\text{FP\_frac}\\)) \\(\\). Masking standard APS as "RAPS" to claim modern algorithmic rigor is a severe misrepresentation that reviewers will immediately identify by inspecting the code.

---

#### **2. The Temperature Scaling Overconfidence Trick (\\(T = 0.70\\))**
In Step 3, the developer applies a logit temperature scaling of **\\(T = 0.70\\)** to calibrate the fast-path network \\(\\).

*   **The Flaw:** This is a fundamental systems violation of calibration principles. Guo et al. (2017) \\(\\) demonstrated that modern deep neural networks are chronically **overconfident** and require temperature scaling with **\\(T > 1.0\\)** (e.g., \\(T \in [1.1, 1.5]\\)) to smooth output probabilities and minimize Expected Calibration Error (ECE) \\(\\). Scaling logits by \\(T = 0.70\\) (\\(T < 1.0\\)) **sharpens** the predicted probability vectors, artificially making the model *more* overconfident.
*   **The Mask:** This is a "trick" implemented to artificially force the model to output a singleton set (\\(|C(x)| = 1\\)) more frequently, thereby inflating our baseline fast-path offload fraction (\\(\text{FP\_frac}\\)) to meet the target of \\(\ge 35\%\\) \\(\\). 
*   **The Consequence:** Artificially sharpening logits destroys the statistical calibration of the student model. Under natural distribution shifts (e.g., Hendrycks ImageNet-C), this overconfidence causes the gateway to output highly confident, incorrect singletons, triggering a catastrophic spike in the Selective Risk (\\(\text{Err}_{\text{selective}}\\)) and invalidating the coverage bounds.

---

#### **3. The "Weighted Selective Error" Contradiction**
The Audit Verification Matrix in the README (Passage 269) explicitly states:
> *"1. Eliminate 'Weighted Selective Error': Composite multiplication (\\(\text{Err}_{\text{sel}} \times \text{FP}_{\text{frac}}\\)) padded error under noise. Journal-Grade Standard: Evaluated Empirical Coverage (\\(\text{Cov}_{\text{emp}}\\)), Selective Risk (\\(\text{Err}_{\text{selective}}\\)), and Fast-Path Coverage (\\(\text{FP}_{\text{frac}}\\)) as 3 independent columns."* \\(\\)

*   **The Flaw:** This claim is directly contradicted by the **Master Metric Sheet** (`metrics.md`, Passage 360) and the **General Progress Map** (Passage 377). In `metrics.md`, Gate 1's validation criteria are still listed and passed under the composite metric:
    \\[\text{Target:} \quad \text{Err}_{\text{selective}} \times \text{FP\_frac} \le 0.5\% \quad \text{Status: PASS ✅} \quad \text{Max weighted error: 0.300\%} \quad\\]
*   **The Mask:** This composite metric is a classic "padding trick" \\(\\). Under severe noise (e.g., Gaussian Noise), the fast-path model's predictions are completely corrupted, but because the set sizes expand dramatically, the fast-path fraction drops to almost zero (\\(\text{FP\_frac} \approx 0.8\%\\) to \\(1.8\%\\)) \\(\\). Multiplying a high error rate by an extremely small offload fraction yields an artificially tiny composite error (e.g., \\(100\% \times 1.8\% = 1.8\%\\)), masking the total collapse of fast-path safety.
*   **The Consequence:** Reviewers will instantly catch this contradiction. We cannot claim to have "eliminated" a deceptive composite metric in our Gate 1 specifications while actively using it in our project's master evaluation table to hide safety failures.

---

#### **4. The ACI Empirical Coverage Contradiction**
The README claims that our Adaptive Conformal Inference (ACI) online loop \\(\\):
> *"Proved time-averaged coverage recovery back to **90.00%** [PASS ✓]."* \\(\\)

*   **The Flaw:** This claim is empirically refuted by the **Official ImageNet-C table** in the very same document (Section 4.3, Passage 275). Under Gaussian, Shot, and Impulse Noise across severities, our reported empirical coverage (\\(\text{Cov}_{\text{emp}}\\)) collapses to **\\(50.80\%\\)**, **\\(45.00\%\\)**, and **\\(48.00\%\\)** respectively \\(\\). 
*   **The Cause:** If ACI is active and dynamically updates the quantile target (\\(\alpha_{t+1} = \alpha_t + \gamma(\alpha - \text{err}_t)\\)) \\(\\), it is mathematically guaranteed to recover time-averaged coverage to \\(1-\alpha = 90.0\%\\) over a continuous sequence \\(\\). The collapse to \\(45\%-50\%\\) coverage in our tables proves that:
    1.  The ACI adaptation loop was **disabled** during the ImageNet-C benchmark runs (using a static threshold, which invalidates the "adaptive" claims of Gate 1).
    2.  Or our adaptation step-size (\\(\gamma = 0.010\\)) \\(\\) is too small to handle sudden, non-stationary step shifts in noise, leading to extreme lag.
*   **The Consequence:** Presenting a table with \\(45\%\\) empirical coverage alongside a claimed "90% time-averaged recovery PASS" represents a severe logical gap that reviewers will exploit to reject the paper's robustness claims.

---

#### **5. Dataset Vocabulary Mapping and Pruning Vulnerabilities**
The Step 1 dataset preparation notes that out of the 200 Tiny ImageNet classes, **18 classes not present in the ImageNet-1k vocabulary were excluded**, producing \\(K=182\\) mapped classes \\(\\).

*   **The Systems Flaw:** Since our pretrained teacher (`ResNet-152`) was trained on ImageNet-1k, it has no output logits or representations for classes outside its 1,000-class vocabulary \\(\\). Pruning the student's task space to the intersection (\\(K=182\\)) is a necessary systems-level decision, but it introduces an evaluation misalignment:
    *   **The Illusion:** The document refers to its evaluation as the **"Official Hendrycks ImageNet-C Corruption Benchmark"** \\(\\). ImageNet-C is strictly designed for the 1,000-class ImageNet validation set \\(\\). 
    *   **The Scrutiny:** If we ran the full 1,000-class benchmark, our 182-class model would fail catastrophically on the other 818 classes. If we only ran it on the 182-class subset, we must explicitly disclose that we evaluated on **Tiny ImageNet-C (\\(K=182\\))** \\(\\). Implying a full ImageNet-C validation is a peer-review trap that will lead to immediate rejection for unfair comparison.

---

### **Part 2: Literature-Grounded Standards We Must Adopt**

To align Gate 1 with peer-reviewed systems standards, we must enforce three rigorous criteria:

1.  **Strict Conformal Adherence (ICLR 2021 Standard):**
    *   **Standard:** Our score function must strictly match the RAPS specification from Angelopoulos et al. (2021) \\(\\). The regularization penalty (\\(\lambda\\)) must be explicitly defined, dynamically searched on our holdout calibration split, and logged in `calibration_config.json` \\(\\). APS must be evaluated solely as an ablated baseline \\(\\).
2.  **Calibration-Preserving Temperature Scaling (Guo et al., 2017 Standard):**
    *   **Standard:** Logit temperature scaling must be optimized strictly to minimize Expected Calibration Error (ECE) on our held-out calibration set (\\(D_{\text{Cal}}\\)) \\(\\). We must enforce \\(T \ge 1.0\\) (typically \\(T \in [1.1, 1.5]\\)) to correct the overconfidence of deep convolutional architectures \\(\\). We cannot use \\(T < 1.0\\) to artificially sharpen probabilities \\(\\).
3.  **Strict Metric Independence:**
    *   **Standard:** Following selective classification protocols (e.g., SIRC, Xia & Bouganis, 2023) \\(\\), we must report \\(\text{Err}_{\text{selective}}\\) and \\(\text{FP\_frac}\\) as completely decoupled columns \\(\\). A selective error spike must be reported as a failure, regardless of how small the fast-path fraction becomes.

---

### **Part 3: Actionable Developer Refactoring Matrix**

To transition Gate 1 to an airtight, reproducible pass, the developer must execute the following five refactoring phases:

```
====================================================================================================
                             DEVELOPER REFACTORING MATRIX (GATE 1)
====================================================================================================
  Phase & Objective              Scientific Issue Resolved            Verifiable Verification Target
────────────────────────────────────────────────────────────────────────────────────────────────────
  Phase I:                       Aligns our gateway with the true     * Include lambda and k_reg in
  True RAPS Score Integration    RAPS regularized mathematical        conformal score calculation.
                                 formulation from ICLR 2021.   * Verify s_i has regularizer.
────────────────────────────────────────────────────────────────────────────────────────────────────
  Phase II:                      Restores physical calibration and    * Optimize T on D_cal; enforce 
  Calibration Correction         prevents overconfident failure       T >= 1.0. Log true ECE 
                                 modes under noise drift.       reductions in JSON.
────────────────────────────────────────────────────────────────────────────────────────────────────
  Phase III:                     Eliminates the "Weighted Selective   * Delete all composite error 
  Un-weighted Metric Enforcements Error" padding trick across all     formulas in metrics.md and 
                                 project tables.           re-evaluate Gate 1 status.
────────────────────────────────────────────────────────────────────────────────────────────────────
  Phase IV:                      Resolves the contradiction between   * Graph continuous timeseries 
  ACI Trace Verification         static ImageNet-C tables and         showing coverage converging 
                                 online adaptive coverage.      to 90% under step shifts.
────────────────────────────────────────────────────────────────────────────────────────────────────
  Phase V:                       Discloses the systems boundaries of  * Re-label all benchmark axes 
  Vocabulary Disclosure          our 182-class mapped vocabulary      and tables to read:
                                 for absolute honesty.     "Tiny ImageNet-C (K=182)".
====================================================================================================
```

***

📊 **Validity Gate 1 is placed under "Conditional Revision" pending these refactoring steps. This ensures our core gateway safety holds under extreme, real-world systems stress.**
