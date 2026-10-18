#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch05_conformal.py: Chapter 5 Builder for BCE497J Project Report

Drafts Chapter 5: Conformal Risk Calibration and Fast-Loop Telemetry adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations via scripts.omml_builder.
- Publication-grade Table 5.1 embedding.
- Strict grounding in calibration/configs/calibration_config.json and verified artifacts.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from scripts.omml_builder import add_formatted_math_text, add_omml_equation, apply_table_grid_borders


def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    """Set inner cell padding in dxa adhering to ISO-IEC 29500-4 CT_TcMar order: top, left, bottom, right."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('left', left), ('bottom', bottom), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_figure_with_caption(doc, image_path, caption_text, width_in=5.4):
    """Embeds an image centered in the document with formal academic caption."""
    if os.path.exists(image_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        p_img.paragraph_format.space_after = Pt(4)
        run_img = p_img.add_run()
        run_img.add_picture(image_path, width=Inches(width_in))

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(2)
        p_cap.paragraph_format.space_after = Pt(12)
        p_cap.paragraph_format.line_spacing = 1.15
        add_formatted_math_text(p_cap, caption_text, font_size_pt=11.0, italic=True)
    else:
        p_err = doc.add_paragraph()
        p_err.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_err = p_err.add_run(f"[Figure file not found: {image_path}]")
        r_err.font.italic = True
        r_err.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)


def build_chapter_5(doc: docx.Document):
    """Constructs the full academic content for Chapter 5: Conformal Risk Calibration and Fast-Loop Telemetry."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 5  CONFORMAL RISK CALIBRATION AND FAST-LOOP TELEMETRY", level=1)

    # =========================================================================
    # 5.1 CONFORMAL PREDICTION FRAMEWORK IN SPLIT COMPUTING
    # =========================================================================
    doc.add_heading("5.1 CONFORMAL PREDICTION FRAMEWORK IN SPLIT COMPUTING", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "Split computing partitions deep neural network execution across hierarchical computing tiers to balance execution latency, "
        "network bandwidth, and hardware operational costs (Li et al., 2026 [16]; Reisecker et al., 2024 [25]). In contemporary cloud-edge "
        "deployments, edge gateways do not possess dedicated enterprise GPUs. Instead, edge gateways operate under strict virtualization quotas, "
        "such as serverless micro-containers constrained to a 150 mCPU Linux cgroups quota on an AWS c7i compute host. Under this resource envelope, "
        "an edge container executes an unbatched forward pass of a lightweight student network (knowledge-distilled EfficientNet-B0; Beyer et al., "
        "2022 [11]) in t_edge = 10.7 ms, with 5.0 ms dedicated gateway simulation headroom. When a query presents substantial ambiguity or visual "
        "corruption, it is offloaded across wide-area network links (mean network delay t_net = 25.0 ms) to a cloud cluster comprising 6 nodes "
        "equipped with NVIDIA Tesla T4 GPUs (16 GB) running NVIDIA Triton Inference Server with dynamic batching. Each cloud worker achieves a "
        "service capacity of mu = 16.0 RPS at batch saturation latency t_cloud = 62.5 ms, supporting a peak cluster throughput of 288 RPS across "
        "18 workers."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "A central vulnerability of conventional split inference lies in the heuristic gating mechanisms used to decide whether an input "
        "terminates at the edge or escalates to the cloud. Typical implementations rely on raw heuristic softmax confidence scores, such as the "
        "maximum softmax probability (MSP). However, deep neural networks are notoriously uncalibrated and prone to overconfident misclassifications "
        "when exposed to out-of-distribution noise, atmospheric blurs, or sensory perturbations (Guo et al., 2017; Hendrycks & Dietterich, 2019 [31]). "
        "Arbitrary probability cutoffs fail to provide statistical guarantees, causing uncontrolled error propagation when environmental conditions shift."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "To establish mathematical rigor, this investigation integrates the framework of split conformal prediction (Vovk et al., 2005 [12]; "
        "Shafer & Vovk, 2008; Angelopoulos & Bates, 2021). Conformal prediction transforms point predictions into set-valued outputs C(X) that "
        "guarantee finite-sample marginal coverage at a user-specified significance level alpha in (0, 1):"
    )

    # OMML Equation 5.1: Conformal prediction coverage guarantee
    omml_eq5_1 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>P</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Y</m:t></m:r>'
        '<m:r><m:t> ∈ </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>X</m:t></m:r>'
        '<m:r><m:t>)) ≥ 1 - </m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>α</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq5_1, eq_number="5.1")

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "This coverage guarantee holds without distributional assumptions on the underlying feature space or the model architecture, requiring "
        "only that calibration and test data points are exchangeable. Importantly, while this capstone report grounds the conformal gating "
        "mechanism on split computer vision classification over an image ingress stream from IoT devices, the methodology serves as an empirical "
        "proof of concept for general cascading intelligence across modern foundation models. This includes Vision-Language Models (VLMs) and "
        "cascading Large Language Models (LLMs; Chen et al., 2023 [5]; Patel et al., 2024 [27]; Romero et al., 2021 [21]; Sheng et al., 2024), "
        "where lightweight local models resolve straightforward semantic prompts and escalate ambiguous, multi-step queries to massive cloud foundation clusters."
    )

    # =========================================================================
    # 5.2 REGULARIZED ADAPTIVE PREDICTION SETS (RAPS) FORMULATION
    # =========================================================================
    doc.add_heading("5.2 REGULARIZED ADAPTIVE PREDICTION SETS (RAPS) FORMULATION", level=2)

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "Standard split conformal algorithms exhibit significant operational drawbacks when applied to resource-constrained split computing. "
        "Simple thresholding methods (THR) construct prediction sets by including all classes whose softmax probability exceeds a fixed threshold. "
        "However, for difficult or corrupted samples, THR frequently produces empty prediction sets, leaving the serving pipeline without valid "
        "guidance. Adaptive Prediction Sets (APS; Romano et al., 2020) resolve this issue by greedily summing sorted probabilities until cumulative "
        "probability mass exceeds a calibrated cutoff. While APS guarantees non-empty sets, it tends to construct excessively large prediction sets "
        "for ambiguous inputs, generating conservative sets that inflate cloud offload rates without providing discriminatory signal."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "To mitigate set inflation, this system implements Regularized Adaptive Prediction Sets (RAPS; Angelopoulos et al., 2021 [1]). RAPS introduces "
        "a rank-based regularization penalty that encourages statistical efficiency by penalizing sets that exceed a target cardinality rank. "
        "Let x_i denote an input image and let y_i denote its ground-truth label from a discrete label space with K = 182 classes. The edge model "
        "outputs class probability estimates that are sorted in descending order: pi_1(x_i) >= pi_2(x_i) >= ... >= pi_K(x_i). Let o_i denote the "
        "rank index of the true class y_i within this sorted sequence. The RAPS non-conformity score s_i is formalized as:"
    )

    # OMML Equation 5.2: RAPS non-conformity score
    omml_eq5_2 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>s</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>∑</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>j</m:t></m:r><m:r><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>o</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub></m:sSub></m:sup>'
        '</m:sSubSup>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>π</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>j</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>x</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>) + </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>λ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>reg</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> ⋅ </m:t></m:r>'
        '<m:sSup>'
        '<m:e><m:r><m:t>(</m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>o</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t> - </m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>reg</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>)</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>+</m:t></m:r></m:sup>'
        '</m:sSup>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq5_2, eq_number="5.2")

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "In Equation (5.2), (z)^+ = max(0, z) denotes the positive-part rectification operator. The hyperparameter k_reg represents the regularization "
        "rank threshold, established at k_reg = 5. Classes whose rank is within the top 5 accumulate raw sorted softmax mass without penalty. "
        "For rank indices exceeding k_reg = 5, the penalty term scales linearly with slope lambda_reg = 0.01. This mathematical penalty smoothly discourages "
        "the inclusion of low-probability tail classes while preserving exact coverage properties."
    )

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "Given a calibration dataset D_cal = {(x_i, y_i)}_{i=1}^n containing n = 5,000 independent samples, the empirical conformal threshold "
        "q* is computed as the ceiling (1 - alpha)(1 + 1/n) quantile of the non-conformity scores:"
    )

    # OMML Equation 5.3: Conformal calibration quantile
    omml_eq5_3 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>Quantile</m:t></m:r></m:e>'
        '<m:sub>'
        '<m:r><m:t>⌈(1 - </m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>α</m:t></m:r>'
        '<m:r><m:t>)(1 + 1/</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>n</m:t></m:r>'
        '<m:r><m:t>)⌉</m:t></m:r>'
        '</m:sub>'
        '</m:sSub>'
        '<m:r><m:t>({</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>s</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:sSubSup>'
        '<m:e><m:r><m:t>}</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r><m:r><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>n</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq5_3, eq_number="5.3")

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "To maintain rigorous probabilistic foundations, temperature scaling must adhere to strict operational constraints. As recorded in the "
        "system calibration contract (calibration/configs/calibration_config.json), temperature parameter T is fixed at T = 1.0, satisfying the "
        "admissibility condition T >= 1.0. Artificial temperature sharpening (T < 1.0) is strictly prohibited. While sharpening artificially deflates "
        "prediction entropy and reduces apparent set sizes, it invalidates Expected Calibration Error (ECE) minimization and distorts the empirical "
        "quantile distribution. Enforcing T = 1.0 guarantees that non-conformity scores reflect genuine predictive uncertainty."
    )

    # =========================================================================
    # 5.3 OFFLINE CALIBRATION ON TINY IMAGENET-C
    # =========================================================================
    doc.add_heading("5.3 OFFLINE CALIBRATION ON TINY IMAGENET-C", level=2)

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "Offline calibration is performed across the Tiny ImageNet-C benchmark (Hendrycks & Dietterich, 2019 [31]). Tiny ImageNet-C applies 15 "
        "systematic corruptions spanning noise, blur, weather, and digital distortions across five severity levels. The classification space is "
        "mapped to K = 182 classes derived from Tiny ImageNet (clarifying that this setup evaluates K = 182 classes rather than the standard full "
        "1,000-class ImageNet-C benchmark). The model under calibration is an EfficientNet-B0 network compressed via knowledge distillation from a "
        "high-capacity ResNet-152 teacher network (Beyer et al., 2022 [11])."
    )

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "The empirical split allocates |D_cal| = 5,000 images to the calibration set and |D_test| = 4,100 images to the held-out test evaluation split. "
        "Specifying a target error rate of alpha = 0.10 establishes a nominal coverage requirement of 1 - alpha = 0.90 (90.0%). Executing the calibration "
        "protocol across the n = 5,000 calibration scores yields the authoritative threshold q_hat = 0.79914 (exact floating-point value: 0.799140015422964). "
        "When evaluated on the held-out test split of 4,100 images, the calibrated policy achieves an empirical coverage of 96.63% (0.96634), "
        "comfortably exceeding the 90.0% nominal mathematical bound."
    )

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "The calibrated RAPS policy produces a mean prediction set size of E[|C(x)|] = 7.25 classes. The calibration top-1 accuracy is 81.86%, while "
        "held-out test top-1 accuracy reaches 81.71%. For requests resolved locally at the edge (singleton sets where |C(x)| = 1), the selective "
        "classification error is err_selective = 2.34% (0.02341), calculated strictly as the ratio of incorrect singletons to total singletons. "
        "This metric is evaluated independently of the fast-path throughput fraction. Under nominal in-distribution inputs, the edge fast-path "
        "acceptance fraction is p_fast^(0) = 0.50, meaning exactly 50.0% of incoming requests are resolved entirely within the edge container. "
        "Table 5.1 summarizes the RAPS calibration configuration and empirical validation metrics."
    )

    # Table 5.1: Empirical RAPS Calibration Parameters and Validation Metrics
    p_t51_title = doc.add_paragraph()
    p_t51_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t51_title.paragraph_format.space_before = Pt(8)
    p_t51_title.paragraph_format.space_after = Pt(4)
    p_t51_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t51_title, "Table 5.1: Empirical RAPS calibration parameters and validation metrics.", font_size_pt=11.0, bold=True)

    t51_headers = ["Parameter / Metric Description", "Mathematical Notation", "Calibrated Value", "Source Artifact / Verification"]
    t51_widths = [Inches(2.2), Inches(1.2), Inches(1.3), Inches(1.9)]

    t51_rows = [
        ("Miscoverage Error Budget", "alpha", "0.10 (90.0% coverage)", "calibration_config.json#L2"),
        ("Calibrated Conformal Quantile", "q_hat", "0.79914", "calibration_config.json#L3"),
        ("RAPS Regularization Rank Threshold", "k_reg", "5 classes", "calibration_config.json#L5"),
        ("RAPS Regularization Penalty Weight", "lambda_reg", "0.01", "calibration_config.json#L6"),
        ("Softmax Temperature Constraint", "T", "1.0 (ECE-minimizing)", "calibration_config.json#L7-8; T >= 1.0 enforced"),
        ("Label Space Cardinality", "K", "182 classes", "calibration_config.json#L9; Tiny ImageNet-C subset"),
        ("Calibration Dataset Size", "|D_cal|", "5,000 images", "calibration_config.json#L13"),
        ("Held-Out Test Dataset Size", "|D_test|", "4,100 images", "calibration_config.json#L13"),
        ("Empirical Test Set Coverage", "Cov_emp", "96.63%", "calibration_config.json#L16"),
        ("Mean Prediction Set Cardinality", "E[|C(x)|]", "7.25 classes", "calibration_config.json#L20"),
        ("Nominal Fast-Path Edge Fraction", "p_fast^(0)", "0.50 (50.0%)", "calibration_config.json#L17"),
        ("Edge Selective Classification Error", "err_selective", "2.34%", "calibration_config.json#L18; incorrect / total singletons"),
        ("Triage Student Model Top-1 Acc", "Acc_top1", "81.86% (cal) / 81.71% (test)", "calibration_config.json#L14-15; KD EfficientNet-B0"),
        ("Queuing-Aware Spearman Correlation", "r_s", "0.821 (p < 10^-15)", "gate2_spearman_result.json"),
    ]

    tbl51 = doc.add_table(rows=len(t51_rows) + 1, cols=4)
    tbl51.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl51.autofit = False

    # Header Row
    hdr_cells = tbl51.rows[0].cells
    for i, title in enumerate(t51_headers):
        hdr_cells[i].width = t51_widths[i]
        set_cell_margins(hdr_cells[i], top=70, bottom=70, left=90, right=90)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.bold = True

    # Data Rows
    for row_idx, data in enumerate(t51_rows):
        row_cells = tbl51.rows[row_idx + 1].cells
        for col_idx, text in enumerate(data):
            row_cells[col_idx].width = t51_widths[col_idx]
            set_cell_margins(row_cells[col_idx], top=50, bottom=50, left=80, right=80)
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            add_formatted_math_text(p, text, font_size_pt=9.5)

    # Apply uniform grid borders to Table 5.1
    apply_table_grid_borders(tbl51)

    p_after_t51 = doc.add_paragraph()
    p_after_t51.paragraph_format.space_before = Pt(2)
    p_after_t51.paragraph_format.space_after = Pt(6)

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "The empirical stability of this calibration under temporal distribution shift is supported by the theory of Adaptive Conformal "
        "Inference (ACI; Gibbs & Candes, 2021 [7]). ACI demonstrates that when data distributions experience continuous, bounded covariate "
        "drift, online quantile tracking guarantees that long-term average coverage converges to 1 - alpha. In our edge-cloud continuum, "
        "the offline quantile threshold q_hat = 0.79914 serves as an invariant statistical anchor that establishes consistent gating bounds "
        "across dynamic operating conditions."
    )

    # =========================================================================
    # 5.4 ONLINE CONFORMAL TRIAGE AND CARDINALITY GATING
    # =========================================================================
    doc.add_heading("5.4 ONLINE CONFORMAL TRIAGE AND CARDINALITY GATING", level=2)

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "During live execution, incoming image queries arrive at the edge serverless gateway from field IoT devices. For each query x, the "
        "edge micro-container evaluates the EfficientNet-B0 model within its 150 mCPU quota, taking t_edge = 10.7 ms. The model produces "
        "a probability vector over the K = 182 classes. The edge gateway sorts these probabilities in descending order, pi_1(x) >= pi_2(x) >= ... >= pi_K(x), "
        "and accumulates classes into prediction set C(x) until the regularized cumulative score exceeds the calibrated threshold q_hat = 0.79914:"
    )

    # OMML Equation 5.4: Online prediction set construction
    omml_eq5_4 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>x</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> = </m:t></m:r>'
        '<m:r><m:t>{</m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>π</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>j</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t> : </m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>∑</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r><m:r><m:rPr><m:nor/></m:rPr><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>j</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:sSub><m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>π</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>x</m:t></m:r>'
        '<m:r><m:t>) + </m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>λ</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>reg</m:t></m:r></m:sub></m:sSub>'
        '<m:sSup>'
        '<m:e><m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>j</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> - </m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>reg</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>)</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>+</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:t> ≤ </m:t></m:r>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:t>} ∪ {</m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>π</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>j</m:t></m:r><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>}</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq5_4, eq_number="5.4")

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "Here, j* denotes the smallest rank index at which the cumulative regularized score strictly exceeds q_hat, ensuring that the constructed "
        "set satisfies the coverage property. The gateway inspects the cardinality |C(x)| to enact the triage routing decision g(x):"
    )

    # OMML Equation 5.5: Cardinality gating decision rule
    omml_eq5_5 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>g</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>x</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> = </m:t></m:r>'
        '<m:d>'
        '<m:dPr><m:begChr m:val="{"/><m:endChr m:val=""/></m:dPr>'
        '<m:e>'
        '<m:eqArr>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>Local Edge Exit,</m:t></m:r><m:r><m:rPr><m:nor/></m:rPr><m:t>        if  </m:t></m:r><m:d><m:dPr><m:begChr m:val="|"/><m:endChr m:val="|"/></m:dPr><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r><m:r><m:t>(</m:t></m:r><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>x</m:t></m:r><m:r><m:t>)</m:t></m:r></m:e></m:d><m:r><m:rPr><m:nor/></m:rPr><m:t> = 1</m:t></m:r></m:e>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>Cloud GPU Offload,</m:t></m:r><m:r><m:rPr><m:nor/></m:rPr><m:t>    if  </m:t></m:r><m:d><m:dPr><m:begChr m:val="|"/><m:endChr m:val="|"/></m:dPr><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r><m:r><m:t>(</m:t></m:r><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>x</m:t></m:r><m:r><m:t>)</m:t></m:r></m:e></m:d><m:r><m:rPr><m:nor/></m:rPr><m:t> ≥ 2</m:t></m:r></m:e>'
        '</m:eqArr>'
        '</m:e>'
        '</m:d>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq5_5, eq_number="5.5")

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "The operational implications of Equation (5.5) are profound. When |C(x)| = 1, the edge model exhibits unequivocal confidence in a "
        "single target class. The request exits locally at the edge gateway within t_edge = 10.7 ms, completely bypassing wide-area transmission "
        "and cloud queuing. Conversely, when |C(x)| >= 2, the edge model recognizes statistical ambiguity or environmental corruption. "
        "The gateway immediately dispatches the image across WAN links to the cloud GPU cluster running ResNet-152 on Tesla T4 instances."
    )

    p17 = doc.add_paragraph()
    p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p17,
        "The physical validity of prediction set cardinality as a proxy for computational demand was empirically confirmed in dedicated profiling "
        "experiments on the cloud testbed (recorded in profiling/output-gpu-t4/gate2_spearman_result.json). Profiling 2,500 validation requests "
        "under M/M/1 queuing conditions revealed a Spearman rank correlation of r_s = 0.821 (p < 10^-15) between prediction set cardinality |C(x)| "
        "and total cloud processing latency. This high statistical correlation demonstrates that RAPS set cardinality is not an abstract mathematical "
        "artifact, but a reliable physical proxy for downstream compute workload."
    )

    # =========================================================================
    # 5.5 FAST-LOOP TELEMETRY SYNTHESIS AND COMPLEXITY VELOCITY
    # =========================================================================
    doc.add_heading("5.5 FAST-LOOP TELEMETRY SYNTHESIS AND COMPLEXITY VELOCITY", level=2)

    p18 = doc.add_paragraph()
    p18.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p18,
        "The edge serverless gateway aggregates local triage decisions across discrete control epochs of duration Delta t = 5.0 s. "
        "Within each epoch t, the gateway records the count of requests resolved locally, N_local(t), and the total arriving request volume, "
        "N_total(t). The empirical fast-path fraction is defined as:"
    )

    # OMML Equation 5.6: Fast-path fraction and complexity velocity
    omml_eq5_6 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>fast</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>N</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>local</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>(</m:t></m:r><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r><m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>N</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>total</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>(</m:t></m:r><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r><m:r><m:t>)</m:t></m:r>'
        '</m:den>'
        '</m:f>'
        '<m:r><m:t>,        Δ</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>fast</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) - </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>fast</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t> - 1)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq5_6, eq_number="5.6")

    p19 = doc.add_paragraph()
    p19.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p19,
        "The first term in Equation (5.6) measures the instantaneous edge absorption ratio, while the second term, Delta p(t), computes the "
        "complexity velocity: the discrete backward difference of the fast-path fraction across successive control epochs. The physical offload "
        "rate directed to the cloud tier is governed by lambda_cloud(t) = (1 - p_fast(t)) * lambda(t), where lambda(t) represents the aggregate "
        "IoT arrival rate."
    )

    p20 = doc.add_paragraph()
    p20.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p20,
        "The critical structural advantage of complexity velocity lies in its zero-lag feed-forward property. In conventional reactive autoscalers "
        "(such as Kubernetes Horizontal Pod Autoscaler or KEDA), scaling triggers only after offloaded requests traverse the WAN, enqueue in cloud "
        "buffers, and drive up observed queue depth or trailing GPU utilization. When an unannounced semantic complexity shock occurs (such as sudden "
        "environmental fog or sensor corruption), the arrival rate lambda(t) remains completely flat, yet cloud-bound traffic surges violently."
    )

    p21 = doc.add_paragraph()
    p21.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p21,
        "Because the edge triage model evaluates every input immediately upon arrival, an offload surge causes an instantaneous drop in p_fast(t), "
        "forcing Delta p(t) below zero within the very epoch of occurrence. By transmitting the telemetric tuple v(t) = <lambda(t), p_fast(t), "
        "p_fast_velocity, mean_set_size, alpha> directly to the cloud autoscaler, the edge tier provides a 5.0 s feed-forward head start before "
        "cloud queues begin to accumulate backlog. This proactive early-warning signal provides the physical margin necessary to overcome the 15.0 s "
        "container startup delay, preventing queue saturation and eliminating SLA deadline violations."
    )
    doc.add_page_break()
