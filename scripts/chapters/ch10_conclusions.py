#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch12_limitations.py: Chapter 12 Builder for BCE497J Project Report

Drafts Chapter 12: Limitations and Threats to Validity in a concise, rigorous format:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, no em-dashes).
- Concise coverage of exchangeability bounds, systems constraints, and empirical validity threats.
- Zero inverted question marks, fully compliant OMML equations.
"""

from __future__ import annotations

import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls

from scripts.omml_builder import add_formatted_math_text, add_omml_equation


def build_chapter_10(doc: docx.Document):
    """Constructs a concise, rigorous academic appraisal for Chapter 10."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 10  LIMITATIONS, CONCLUSIONS, AND FUTURE RESEARCH TRAJECTORIES", level=1)

    # -------------------------------------------------------------------------
    # 10.1 THEORETICAL ASSUMPTIONS AND EXCHANGEABILITY BOUNDS
    # -------------------------------------------------------------------------
    doc.add_heading("10.1 THEORETICAL ASSUMPTIONS AND EXCHANGEABILITY BOUNDS", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "A rigorous scientific evaluation requires a candid appraisal of underlying theoretical assumptions. "
        "The edge triage mechanism in Conformal-Gated Dual-Horizon Autoscaling (CGDA) relies on Split Conformal Prediction, "
        "specifically Regularized Adaptive Prediction Sets (RAPS; Angelopoulos et al., 2021 [10]). The theoretical foundation "
        "of conformal prediction is exchangeability: calibration and test data are assumed to be identically distributed, or at least "
        "invariant under permutation. Under this exchangeability condition, conformal prediction provides a rigorous, "
        "distribution-free marginal coverage guarantee for any chosen miscoverage rate alpha in (0, 1):"
    )

    # OMML Equation 10.1: Marginal coverage guarantee
    ns_m = nsdecls("m")
    omml_eq12_1 = (
        f'<m:oMathPara {ns_m}>'
        '<m:oMath>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>P</m:t></m:r>'
        '<m:d>'
        '<m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr>'
        '<m:e>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Y</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>n</m:t></m:r><m:r><m:t>+1</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> ∈ </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>X</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>n</m:t></m:r><m:r><m:t>+1</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:e>'
        '</m:d>'
        '<m:r><m:t> ≥ 1 - </m:t></m:r>'
        '<m:r><m:t>α</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq12_1, eq_number="10.1")

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "In our system, calibrating RAPS on held-out Tiny ImageNet-C data with alpha = 0.10 yielded a non-conformity threshold "
        "q_hat = 0.79914, achieving 96.63% empirical validation coverage. In operational environments, however, exchangeability "
        "is subject to drift under sudden illumination changes, optical sensor corruptions, or unexpected domain shifts. When test inputs "
        "deviate sharply from the calibration distribution, marginal coverage guarantees can experience transient violations. "
        "Crucially, in the CGDA architecture, distribution drift acts favorably for systems stability: domain corruptions broaden prediction "
        "sets (|C(x)| >= 2), causing the edge gateway to shed ambiguous queries to the cloud and pre-warming GPU workers via the fast lookahead loop. "
        "Nonetheless, persistent non-stationarity necessitates periodic re-calibration or online adaptive conformal bounds (Gibbs & Candes, 2021 [13])."
    )

    # -------------------------------------------------------------------------
    # 10.2 SYSTEMS AND ACTUATION CONSTRAINTS
    # -------------------------------------------------------------------------
    doc.add_heading("10.2 SYSTEMS AND ACTUATION CONSTRAINTS", level=2)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "The control performance of CGDA is fundamentally bounded by the physical dynamics of the cloud substrate. "
        "First, container startup latency establishes a hard lower bound on reactive response times. When the cold-start delay T_boot exceeds "
        "the SLA deadline D_SLA (15.0 s), no autoscaler operating without clairvoyant workload knowledge can prevent deadline violations. "
        "As established in Chapter 9, once T_boot > D_SLA, newly spawned containers cannot become operational before queuing delays miss the deadline. "
        "Second, the controller operates at a discrete actuation period of Delta t = 5.0 s. Traffic bursts with duration shorter than Delta t cannot "
        "be preempted during their initial arrival, relying entirely on existing standby capacity and edge buffering. "
        "Third, the asymmetric scale-down cooldown parameter tau_down = 15.0 s enforces stability at the expense of temporary over-provisioning: "
        "when demand suddenly subsides, excess workers are held active across three control epochs before being decommissioned."
    )

    # -------------------------------------------------------------------------
    # 10.3 THREATS TO EMPIRICAL VALIDITY
    # -------------------------------------------------------------------------
    doc.add_heading("10.3 THREATS TO EMPIRICAL VALIDITY", level=2)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "To ensure objective scientific interpretation, we identify three potential threats to experimental validity. "
        "Internal validity is protected by executing all evaluations under fixed random seeds across matched synthetic and empirical Azure Functions "
        "workload traces, ensuring identical arrival patterns across compared autoscalers. A potential internal threat arises from network variance: "
        "wide-area latency was emulated using stochastic RTT distributions (15-35 ms) rather than live transcontinental links. "
        "Construct validity is maintained by evaluating standardized systems metrics: tail SLA miss percentage (p99 latency > 15.0 s), cumulative "
        "worker-seconds, actuator switching churn, and maximum queue backlog. "
        "External validity concerns the generalizability of findings beyond the specific experimental configuration. While empirical measurements "
        "were obtained on an AWS c7i serverless edge host (150 mCPU container quota) and NVIDIA Tesla T4 cloud GPUs running Triton Inference Server, "
        "the underlying two-loop control principles apply broadly to multi-tier cascading systems, including Vision-Language Models (VLMs) "
        "and cascading Large Language Models (LLMs) deployed across edge-cloud continuum topologies."
    )

    # =========================================================================
    # 10.4 TO 10.7: CONCLUSIONS AND FUTURE RESEARCH
    # =========================================================================
    doc.add_heading("10.4 SUMMARY OF SCIENTIFIC CONTRIBUTIONS", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "This capstone project addressed the fundamental vulnerability of split-inference edge-cloud systems under semantic complexity shocks. "
        "Standard serverless autoscalers monitor trailing queue backlogs or CPU utilization, implicitly assuming that compute demand scales "
        "proportionally with raw request arrival rates. In split-computing cascades, input corruption or domain shift decouples arrival volume "
        "from physical compute requirements, triggering sudden offload surges that saturate cloud GPU queues while raw ingress rates remain constant. "
        "To resolve this complexity blindness, this thesis designed, implemented, and validated Conformal-Gated Dual-Horizon Autoscaling (CGDA). "
        "The primary technical contributions are summarized across four core pillars:"
    )

    p_c1 = doc.add_paragraph()
    p_c1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p_c1,
        "1. Conformal Edge Telemetry and Gating: We formulated an edge-tier statistical triage mechanism using Split Conformal Prediction "
        "(RAPS; Angelopoulos et al., 2021 [10]). Calibrating non-conformity scores on held-out data (q_hat = 0.79914 at alpha = 0.10), the edge gateway "
        "evaluates prediction set cardinality |C(x)| for each query. Unambiguous samples (|C(x)| = 1) exit locally within a 150 mCPU Linux cgroups "
        "container quota on an AWS c7i compute host in 10.7 ms. Ambiguous samples (|C(x)| >= 2) generate zero-lag feed-forward offload rate "
        "derivative telemetry (Delta_offload), alerting cloud schedulers to impending compute surges seconds before requests arrive at cloud queues."
    )

    p_c2 = doc.add_paragraph()
    p_c2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p_c2,
        "2. Evolutionary AST Policy Synthesis: We formulated a domain-specific grammar for dual-horizon elastic control and deployed OpenEvolve [30] "
        "to explore the policy space. Through multi-objective Pareto optimization balancing SLA compliance, compute expenditure, and actuation churn, "
        "the evolutionary search synthesized an interpretable Abstract Syntax Tree policy. The policy incorporates dynamic booting credit modulation, "
        "queue-pressure acceleration, and container boot-lock protection registers, avoiding opaque black-box deep reinforcement learning controllers."
    )

    p_c3 = doc.add_paragraph()
    p_c3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p_c3,
        "3. Decoupled Two-Loop Continuum Orchestration: We engineered a runtime controller that decouples fast inner-loop preemption from slow "
        "outer-loop capacity stabilization. The fast loop responds proactively to edge confidence velocity drops (theta_shock = 0.15) to reserve GPU "
        "capacity ahead of request arrival. The slow outer loop regulates scale-down actions through an asymmetric cooldown hysteresis (tau_down = 15.0 s, "
        "spanning 3 control epochs Delta t = 5.0 s), eliminating destructive worker oscillation."
    )

    p_c4 = doc.add_paragraph()
    p_c4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p_c4,
        "4. Empirical Validation and Tipping Point Boundary: Across 260 matched evaluation runs (1,300 total controller executions) spanning "
        "13 workload regimes derived from the Azure Functions 2019 dataset downsampled by 0.08x, CGDA confirmed 100% SLA compliance (zero misses), "
        "substantial cost savings, and high actuation stability. Through a 9-point startup delay ladder (T_boot in [0.5, 300] s), we established "
        "the physical boundary T* approx D_SLA = 15.0 s, proving that zero SLA violations are attainable whenever container startup latency "
        "remains within the SLA deadline budget."
    )

    # -------------------------------------------------------------------------
    # 10.5 KEY EMPIRICAL TAKEAWAYS
    # -------------------------------------------------------------------------
    doc.add_heading("10.5 KEY EMPIRICAL TAKEAWAYS", level=2)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "The empirical findings documented across Chapters 8 and 9 demonstrate five major takeaways regarding serverless autoscaling in split-inference systems: "
        "(1) Complete SLA Compliance: across 260 matched runs under nominal boot delay (T_boot = 15.0 s) and deadline (D_SLA = 15.0 s), CGDA achieved "
        "exactly 0.00 SLA misses, whereas InferLine incurred 114 misses, KEDA incurred 342 misses, and HPA incurred 821 misses. "
        "(2) Cost Efficiency: CGDA reduced cumulative cloud compute expenditure by 67.38% relative to Static Peak Provisioning (700.0 vs. 2,146.2 worker-seconds; "
        "paired Wilcoxon p = 2.07 x 10^-44), achieving a 61.6% cost reduction against HPA and 33.3% against KEDA during peak demand periods. "
        "(3) Tail Latency Suppression: CGDA lowered P99 tail latency by 35.0% compared to predictive traffic-envelope autoscaling (11.45 s vs. 16.82 s; "
        "paired Wilcoxon p = 5.46 x 10^-43) while accepting a modest 12.8% preemption premium to prevent queue buildup during cold starts. "
        "(4) Actuation Stability: dynamic booting-credit accounting with asymmetric cooldown (tau_down = 15.0 s) suppressed controller flapping by 89.2% "
        "relative to KEDA (16 vs. 148 deltas; paired Wilcoxon p = 4.31 x 10^-31). "
        "(5) Delay Tipping Point: for T_boot <= D_SLA = 15.0 s, proactive lookahead eliminates misses; for T_boot > D_SLA, proactive scaling functions as "
        "backlog mitigation, reducing misses by 83.3% at T_boot = 20.0 s relative to predictive baselines."
    )

    # -------------------------------------------------------------------------
    # 10.6 GENERALIZATION HORIZONS: CASCADING VLMS AND FOUNDATION MODEL ROUTERS
    # -------------------------------------------------------------------------
    doc.add_heading("10.6 GENERALIZATION HORIZONS: CASCADING VLMS AND FOUNDATION MODEL ROUTERS", level=2)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "Importantly, while this thesis empirically evaluated split computer vision (distilled EfficientNet-B0 to ResNet-152), the underlying "
        "conformal-gated dual-horizon control architecture serves as an empirical proof of concept for general cascading intelligence across "
        "modern foundation models, including Vision-Language Models (VLMs) and cascading Large Language Models (LLMs; Valkanas et al., 2025 [14]; "
        "Fu et al., 2024 [3]; Turkoglu et al., 2026 [13]; Romero et al., 2021 [2])."
    )

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "In generative foundation model deployments, serving costs and latency scale steeply with model parameter size. Deploying 70B+ parameter frontier "
        "LLMs directly on edge devices is physically infeasible due to memory and thermal constraints. Cascaded architectures resolve this bottleneck "
        "by deploying small language models (SLMs, 1B to 8B parameters) at the edge or local gateway to process routine prompts. When input queries "
        "involve multi-step mathematical reasoning or ambiguous semantics, the edge model escalates the query to cloud GPU clusters. Conformal prediction "
        "provides a rigorous statistical framework for semantic triage: edge routers construct conformal prediction sets over token logits or sequence "
        "perplexity (as explored in C3PO; Valkanas et al., 2025 [14], and CADS; Turkoglu et al., 2026 [13]). A sudden surge in user query difficulty produces "
        "a semantic complexity shock: edge confidence collapses, and offload volume spikes while raw ingress rates remain flat. Because foundation model "
        "containers exhibit severe cold-start latencies (100 s to 300 s; Fu et al., 2024 [3]), reactive cloud autoscalers inevitably induce massive queue backlogs. "
        "By ingesting feed-forward conformal derivatives from edge SLMs, cloud foundation model clusters can preemptively scale GPU workers, extending "
        "the core principles validated in this thesis across the generative AI ecosystem."
    )

    # OMML Equation 10.2: Optimization objective
    ns_m = nsdecls("m")
    omml_eq13_1 = (
        f'<m:oMathPara {ns_m}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>min</m:t></m:r></m:e>'
        '<m:sub>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:sub>'
        '</m:sSub>'
        '<m:r><m:t>&#160;</m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>∑</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r><m:r><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>T</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> ⋅ Δ</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>&#160;&#160;&#160;s.t.&#160;&#160;&#160;</m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>∑</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r><m:r><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>N</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>&#x1D540;</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>L</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> &gt; </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>D</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>SLA</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>)</m:t></m:r>'
        '<m:r><m:t> = 0</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq13_1, eq_number="10.2")

    # -------------------------------------------------------------------------
    # 10.7 CLOSING REMARKS AND ARTIFACT REPOSITORY
    # -------------------------------------------------------------------------
    doc.add_heading("10.7 CLOSING REMARKS AND ARTIFACT REPOSITORY", level=2)

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "By grounding elastic autoscaling in distribution-free conformal uncertainty rather than lagging hardware metrics, "
        "CGDA demonstrates that semantic complexity derivatives provide the decisive telemetric signal required to eliminate SLA misses "
        "under acute distribution shift. To support independent replication and further research, the complete experimental harness, "
        "synthesized champion AST policy, and benchmark traces are open-sourced at: "
        "https://github.com/vaibhaVishwakarma/complexity-based-autoscaler."
    )
