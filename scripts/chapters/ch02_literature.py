#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch02_literature.py: Chapter 2 Builder for BCE497J Project Report

Drafts Chapter 2: Literature Review and Background in complete academic depth adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations.
- Comparative Taxonomy Table 2.1.
- Open-source upstream repository linkage.
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
    """Set inner cell padding in dxa adhering to ISO-IEC 29500-4 CT_TcMar order."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('left', left), ('bottom', bottom), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def build_chapter_2(doc: docx.Document):
    """Constructs the full academic content for Chapter 2: Literature Review and Background."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 2  LITERATURE REVIEW AND BACKGROUND", level=1)

    # -------------------------------------------------------------------------
    # 2.1 SERVERLESS EDGE COMPUTING AND ELASTIC AUTOSCALING PARADIGMS
    # -------------------------------------------------------------------------
    doc.add_heading("2.1 SERVERLESS EDGE COMPUTING AND ELASTIC AUTOSCALING PARADIGMS", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "Serverless computing has transitioned from an execution runtime for lightweight, stateless event handlers into a core "
        "paradigm for managing distributed machine learning serving pipelines (Copik et al., 2021 [5]; Jia & Witchel, 2021 [23]). "
        "In traditional Function-as-a-Service (FaaS) platforms, elasticity is achieved by dynamically provisioning container instances in "
        "response to incoming request load. Resource management within container orchestrators depends primarily on reactive autoscaling "
        "mechanisms. In production Kubernetes environments, the Horizontal Pod Autoscaler (HPA; Kubernetes Authors, 2024 [3]) periodically "
        "polls container metrics (such as average CPU utilization or memory consumption across active pods) and computes a target replica count "
        "proportional to the observed utilization error relative to a predetermined setpoint."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "Event-driven autoscaling engines, exemplified by Kubernetes Event-driven Autoscaling (KEDA; KEDA Core Team, 2024 [4]), extend "
        "reactive scheduling by scaling worker pools based on external message queue depths rather than container utilization. "
        "By monitoring the queue backlog directly at ingress message brokers, queue-based scalers detect sudden spikes before physical CPU "
        "cores saturate. However, both CPU-driven and queue-driven controllers operate under closed-loop error feedback. When a substantial "
        "workload surge occurs, the controller observes the error only after requests have begun queuing or after CPU utilization has exceeded "
        "the target threshold. Because physical cloud GPU worker containers exhibit initialization delays (T_boot = 15.0 s baseline in cloud "
        "environments; Fu et al., 2024 [6]), reactive controllers experience unavoidable phase lag. By the time newly provisioned GPU workers "
        "reach the operational state, queue backlogs have already accumulated beyond recovery, causing severe Service Level Agreement (SLA) "
        "deadline misses."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "To mitigate reactive phase lag, researchers have developed predictive autoscaling architectures that forecast future request arrival "
        "patterns. InferLine (Crankshaw et al., 2020 [1]) represents the state of the art in pipeline-aware inference provisioning. "
        "InferLine utilizes network calculus to construct upper-bounding traffic envelopes over sliding historical windows, calculating "
        "the minimum worker allocation required to guarantee tail-latency constraints across multi-stage machine learning pipelines. "
        "MagicScaler (Pan et al., 2023 [17]) couples Gaussian Process regression with model predictive control to anticipate demand shifts. "
        "Online learning frameworks such as SIMPPO (Qiu et al., 2022 [21]) and hierarchical reinforcement learning frameworks such as "
        "Fuzzy-HDRL (Chen & Jiang, 2026 [22]) seek optimal scaling trajectories through continuous interaction with cloud runtime metrics."
    )

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "Despite their sophistication, both reactive and predictive autoscalers share a fundamental architectural blind spot: they assume that "
        "computational demand scales proportionally with raw request volume lambda(t). In traditional web workloads, arrival rate serves as "
        "an effective proxy for execution burden. However, in modern split-computing continuum pipelines, raw request arrival volume and physical "
        "compute requirements become strongly decoupled. When input complexity changes abruptly while raw ingress volume remains constant, "
        "volume-centric predictive scalers fail to trigger proactive provisioning."
    )

    # -------------------------------------------------------------------------
    # 2.2 EPISTEMIC UNCERTAINTY AND OUT-OF-DISTRIBUTION DETECTION IN EDGE VISION
    # -------------------------------------------------------------------------
    doc.add_heading("2.2 EPISTEMIC UNCERTAINTY AND OUT-OF-DISTRIBUTION DETECTION IN EDGE VISION", level=2)

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "A central requirement in edge-cloud continuum computing is determining when a lightweight edge model possesses sufficient certainty "
        "to resolve a query locally versus when the query must be escalated to high-capacity cloud models. Modern deep neural networks "
        "frequently exhibit overconfidence in their softmax probability distributions, assigning high confidence scores to incorrect classes or "
        "unseen inputs (Guo et al., 2017). This miscalibration is exacerbated at the edge, where compute constraints necessitate compact, "
        "low-capacity architectures (such as EfficientNet-B0) operating under tight resource limits, including a 150 mCPU Linux cgroups container quota "
        "on host instances (yielding mean inference latency t_edge = 10.7 ms)."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "In physical deployments, IoT endpoints encounter corruptions and environmental perturbations that degrade input distribution "
        "homogeneity. The Tiny ImageNet-C benchmark (Hendrycks & Dietterich, 2019 [11]) establishes an empirical standard for evaluating neural "
        "network robustness across 15 distinct corruption types spanning noise (Gaussian, shot, impulse), blur (defocus, glass, motion, zoom), "
        "weather (snow, frost, fog), and digital alterations (contrast, elastic, pixelate, JPEG compression) evaluated across 5 discrete "
        "severity levels. As corruption severity increases, the epistemic uncertainty of the model widens substantially."
    )

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "To deploy accurate classification at the edge, practitioners apply knowledge distillation (Beyer et al., 2022 [12]), transferring "
        "representational knowledge from heavy teacher models (such as ResNet-152) into compact student networks (EfficientNet-B0). "
        "While distillation improves student accuracy on nominal in-distribution inputs, student capacity remains bounded. Under acute "
        "distribution shift, the student model loses discriminative capacity, producing high entropy across its softmax output vector. "
        "Standard heuristic thresholds on Maximum Softmax Probability (MSP) fail to provide formal reliability bounds, either prematurely "
        "offloading solvable inputs or retaining highly ambiguous queries that produce classification errors at the edge."
    )

    # -------------------------------------------------------------------------
    # 2.3 CONFORMAL PREDICTION: THEORY, CALIBRATION, AND COVERAGE GUARANTEES
    # -------------------------------------------------------------------------
    doc.add_heading("2.3 CONFORMAL PREDICTION: THEORY, CALIBRATION, AND COVERAGE GUARANTEES", level=2)

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "Conformal prediction (Vovk et al., 2005 [10]; Angelopoulos & Bates, 2021) provides a mathematically rigorous, distribution-free "
        "framework for quantifying model uncertainty. Rather than forcing a neural network to produce a single point prediction, conformal "
        "prediction constructs a prediction set C(x) subseteq Y guaranteed to contain the ground-truth label Y with a user-specified marginal "
        "coverage probability 1 - alpha:"
    )

    # OMML Equation 2.1: Conformal Coverage Guarantee
    omml_eq21 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>P</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Y</m:t></m:r>'
        '<m:r><m:t> ∈ </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>X</m:t></m:r>'
        '<m:r><m:t>)) ≥ 1 - </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>α</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq21, eq_number="2.1")

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "Under split-conformal prediction, calibration data D_cal = {(x_i, y_i)}_{i=1}^n is held out from model training. "
        "Because standard conformal prediction sets can become unnecessarily large under high-dimensional label spaces, we utilize "
        "Regularized Adaptive Prediction Sets (RAPS; Angelopoulos et al., 2021 [7]). RAPS penalizes large prediction sets by incorporating a "
        "regularization penalty that discourages sets with cardinality exceeding k_reg. For each calibration sample (x_i, y_i), sorted softmax "
        "probabilities pi_hat_j(x_i) are accumulated up to the rank o_i of the true class y_i, yielding the non-conformity score s_i:"
    )

    # OMML Equation 2.2: RAPS Non-Conformity Score
    omml_eq22 = (
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
        '<m:e><m:acc><m:accPr><m:chr m:val="^"/></m:accPr><m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>π</m:t></m:r></m:e></m:acc></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>j</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>x</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>) + </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>λ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>reg</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:sSup>'
        '<m:e><m:r><m:t>(</m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>o</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> - </m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>reg</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>)</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>+</m:t></m:r></m:sup>'
        '</m:sSup>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq22, eq_number="2.2")

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "Here, (z)^+ = max(0, z) denotes the positive rectification operator, k_reg = 5 establishes the set size regularization threshold, "
        "and lambda_reg = 0.01 controls the regularization penalty weight. The conformal calibration threshold q_hat is then calculated as the "
        "conservative (1 - alpha) empirical quantile across the calibration scores:"
    )

    # OMML Equation 2.3: Empirical Quantile Calibration
    omml_eq23 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> = </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>Quantile</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>1 - </m:t></m:r><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>α</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:t>{</m:t></m:r><m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>s</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub></m:sSub><m:r><m:t>}</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r><m:r><m:rPr><m:nor/></m:rPr><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>n</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq23, eq_number="2.3")

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "In our system, RAPS calibration was executed on |D_cal| = 5,000 images drawn from Tiny ImageNet-C using the knowledge-distilled "
        "EfficientNet-B0 model across K = 182 classes at error tolerance alpha = 0.10. This calibration yielded the empirical threshold "
        "q_hat = 0.79914. When evaluated across a held-out test split of 4,100 images, the calibrated model achieved an empirical coverage "
        "of 96.63%, strictly satisfying the nominal 90.0% coverage requirement. The resulting mean prediction set cardinality was |C| = 7.25, "
        "and the nominal calibration fast-path fraction was p_fast^(0) = 0.50, establishing that exactly half of the calibration requests "
        "were resolved as singletons (|C(x)| = 1)."
    )

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "A critical theoretical question concerns the validity of conformal coverage under non-stationary distributions, where exchangeability "
        "between calibration and runtime data is violated. Adaptive Conformal Inference (ACI; Gibbs & Candes, 2021 [13]) demonstrates that "
        "dynamically adjusting the nominal alpha parameter enables conformal predictors to track coverage targets under bounded covariate "
        "drift. Furthermore, Conformal Risk Control (CRC; Angelopoulos et al., 2024 [24]) generalizes conformal guarantees to arbitrary "
        "monotone loss functions, providing a theoretical foundation for extending prediction set bounds to system-level latency and resource constraints."
    )

    # -------------------------------------------------------------------------
    # 2.4 GATED CASCADING ARCHITECTURES: PROOF OF CONCEPT FOR VLMS AND CASCADING LLMS
    # -------------------------------------------------------------------------
    doc.add_heading("2.4 GATED CASCADING ARCHITECTURES: PROOF OF CONCEPT FOR VLMS AND CASCADING LLMS", level=2)

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "Cascading inference architectures route incoming queries through a hierarchy of models of increasing capacity to balance execution "
        "cost against output quality. Early systems such as INFaaS (Romero et al., 2021 [2]) automated model-variant selection across hardware "
        "targets, selecting architectures based on offline profiling. Recent work in computer vision has applied conformal prediction directly "
        "to cascade routing. In particular, CADS (Conformal Adaptive Decision System; Turkoglu et al., 2026 [8]) utilizes conformal prediction "
        "set cardinality to decide whether an image should be classified by a compact local model or escalated to a cloud teacher. "
        "However, CADS operates exclusively at the model-routing level, assuming an unconstrained, always-available cloud tier without modeling "
        "queue backlogs, worker provisioning delays, or elastic container autoscaling."
    )

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "Importantly, the architectural challenges addressed in this capstone report extend far beyond image classification. We explicitly "
        "frame our edge-cloud split vision testbed as an empirical proof of concept for general cascading intelligence across modern foundation "
        "models, including Vision-Language Models (VLMs) and cascading Large Language Models (LLMs). In modern generative pipelines, multi-model "
        "cascades pair small, low-latency edge language models (such as 1B to 3B parameter models) with massive cloud foundation models "
        "(such as 70B parameter LLMs or proprietary API endpoints). For example, C3PO (Valkanas et al., 2025 [9]) optimizes LLM reasoning cascades "
        "under probabilistic cost constraints, evaluating query difficulty before invoking high-parameter models. Similarly, ServerlessLLM "
        "(Fu et al., 2024 [6]) highlights that loading large foundation model checkpoints into GPU memory incurs startup penalties of 100 to "
        "300 s, creating extreme vulnerability to sudden surges in cloud escalation."
    )

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "In both split vision and generative language cascades, the underlying systems dynamics are mathematically isomorphic: a local triage "
        "layer filters straightforward queries, while ambiguous, high-complexity, or multi-modal reasoning tasks are escalated to an elastic cloud "
        "pool. When environmental corruptions or complex query shifts occur, edge resolution collapses, precipitating a sudden flood of "
        "expensive tasks toward the cloud. By demonstrating how statistical uncertainty sets can be repurposed into real-time infrastructure "
        "autoscaling telemetry, our work provides an operational blueprint applicable across vision, multi-modal, and generative language serving."
    )

    # -------------------------------------------------------------------------
    # 2.5 SUMMARY AND RESEARCH GAPS
    # -------------------------------------------------------------------------
    doc.add_heading("2.5 SUMMARY AND RESEARCH GAPS", level=2)

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "Table 2.1 provides a structured comparative taxonomy contrasting dominant autoscaling and inference serving paradigms against our "
        "proposed Conformal-Gated Dual-Horizon Autoscaling (CGDA) framework. The comparison evaluates seven critical dimensions: telemetry signal "
        "origin, core scaling mechanism, reactivity latency, semantic complexity awareness, container actuation churn suppression, "
        "and primary target workload domain."
    )

    # Table 2.1: Comparative Taxonomy
    p_t2_title = doc.add_paragraph()
    p_t2_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_title.paragraph_format.space_before = Pt(8)
    p_t2_title.paragraph_format.space_after = Pt(4)
    p_t2_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(
        p_t2_title,
        "Table 2.1: Comparative taxonomy of elastic autoscaling and inference serving frameworks.",
        font_size_pt=11.0,
        bold=True
    )

    t2_headers = [
        "Framework / System",
        "Telemetry Signal Origin",
        "Scaling Mechanism",
        "Reactivity Latency",
        "Semantic Awareness",
        "Churn Suppression",
        "Target Workload"
    ]
    t2_widths = [
        Inches(1.0),
        Inches(0.9),
        Inches(1.0),
        Inches(0.8),
        Inches(0.7),
        Inches(0.9),
        Inches(1.1)
    ]

    t2_rows = [
        (
            "Kubernetes HPA (Kubernetes Authors, 2024 [3])",
            "Cloud Pod CPU utilization",
            "Proportional error feedback: target utilization setpoint",
            "Lag-bound: requires CPU saturation (Delta t >= 15 s)",
            "None (blind to sample complexity)",
            "Trailing stabilization window (100 s)",
            "Stateless microservices & web applications"
        ),
        (
            "KEDA (KEDA Core Team, 2024 [4])",
            "Message broker queue depth",
            "Queue-length threshold: worker per N messages",
            "Lag-bound: requires queue backlog formation",
            "None (blind to sample complexity)",
            "Minimal (susceptible to rapid flapping)",
            "Event-driven message processing queues"
        ),
        (
            "InferLine (Crankshaw et al., 2020 [1])",
            "End-to-end arrival rate lambda(t)",
            "Network calculus traffic envelopes & pipeline sizing",
            "Predictive over window; blind to zero-volume shifts",
            "None (assumes static model service time)",
            "Upper-bound envelope damping",
            "Multi-stage pipeline inference serving"
        ),
        (
            "INFaaS (Romero et al., 2021 [2])",
            "Inference requests & profiling logs",
            "Dynamic model-variant and hardware selection",
            "Periodic offline profiling & variant switching",
            "Coarse (accuracy vs. latency Pareto trade-offs)",
            "Variant migration dampening",
            "Multi-model multi-tenant cloud serving"
        ),
        (
            "CADS (Turkoglu et al., 2026 [8])",
            "Prediction set size |C(x)| at local classifier",
            "Static threshold gating for model cascade routing",
            "Instantaneous per-sample decision",
            "High (conformal prediction set cardinality)",
            "Not applicable (unconstrained cloud assumed)",
            "Two-tier vision model cascade routing"
        ),
        (
            "CGDA (This Work)",
            "Cross-tier vector v(t) = <lambda(t), p_fast(t), dot_p_fast(t), q(t)>",
            "Synthesized AST dual-horizon: fast preemption & slow re-anchoring",
            "Zero-lag feed-forward: preemption triggered at edge collapse",
            "Rigorous (RAPS uncertainty sets + derivative tracking)",
            "Asymmetric cooldown (tau_down = 15 s) & boot-locking",
            "Edge-cloud split inference & cascading foundation models"
        )
    ]

    tbl_t2 = doc.add_table(rows=len(t2_rows) + 1, cols=7)
    tbl_t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t2.autofit = False
    apply_table_grid_borders(tbl_t2)

    for j, h in enumerate(t2_headers):
        c = tbl_t2.cell(0, j)
        c.width = t2_widths[j]
        set_cell_margins(c, top=40, bottom=40, left=35, right=35)
        p = c.paragraphs[0]
        p.paragraph_format.line_spacing = 1.1
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True

    for i, row_data in enumerate(t2_rows):
        row = tbl_t2.rows[i + 1]
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = t2_widths[j]
            set_cell_margins(c, top=30, bottom=30, left=30, right=30)
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_math_text(p, val, font_size_pt=8.5)

    p17 = doc.add_paragraph()
    p17.paragraph_format.space_before = Pt(8)
    p17.paragraph_format.space_after = Pt(6)
    p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p17,
        "The comparative analysis reveals two decisive research gaps in the existing literature: "
        "(1) Disconnect between statistical uncertainty quantification and physical autoscaling: Prior conformal prediction and model "
        "cascading literature (such as CADS) treats the cloud as an infinite, instantly responsive computational sink, ignoring physical worker "
        "provisioning latency, queue backlog dynamics, and finite hardware saturation. "
        "(2) Blindness of infrastructure autoscalers to semantic complexity: Existing commercial and academic autoscalers (HPA, KEDA, InferLine) "
        "rely strictly on trailing error metrics or arrival volume forecasting. When input distribution shifts occur without an accompanying change "
        "in raw arrival rate, these systems experience catastrophic queue saturation and SLA collapse. "
        "Resolving this dual gap requires bridging statistical conformal triage directly into closed-loop, dual-horizon infrastructure control, "
        "which constitutes the foundational contribution of this thesis."
    )

    doc.add_page_break()
