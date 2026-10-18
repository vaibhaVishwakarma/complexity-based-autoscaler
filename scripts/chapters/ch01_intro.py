#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch01_intro.py: Chapter 1 Builder for BCE497J Project Report

Drafts Chapter 1: Introduction in complete academic depth adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations.
- Publication-grade Table 1.1 and Figure 1.1 embedding.
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


def build_chapter_1(doc: docx.Document):
    """Constructs the full academic content for Chapter 1: Introduction."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 1  INTRODUCTION", level=1)

    # -------------------------------------------------------------------------
    # 1.1 MOTIVATION AND THE EDGE-CLOUD CONTINUUM
    # -------------------------------------------------------------------------
    doc.add_heading("1.1 MOTIVATION AND THE EDGE-CLOUD CONTINUUM", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "Modern deep neural networks deliver high accuracy across complex perceptual tasks, yet their substantial compute "
        "footprints prevent direct execution within lightweight edge serverless environments. In commercial cloud-edge ecosystems, "
        "serverless platforms do not expose dedicated desktop GPUs or bare-metal embedded accelerators. Instead, edge gateways operate "
        "under fractional, virtualized container quotas (such as 150 mCPU Linux cgroups allocations on host instances) designed to absorb "
        "massive concurrent IoT request streams without incurring the heavy provisioning costs and thermal envelopes of dedicated edge hardware."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "Edge-cloud split computing resolves these resource constraints by partitioning inference across the continuum (Li et al., "
        "2026 [16]; Reisecker et al., 2024 [25]). Under this architecture, a lightweight student network (knowledge-distilled EfficientNet-B0) "
        "runs as a serverless triage function within a 150 mCPU container quota on an AWS c7i compute host. Requests carrying unambiguous "
        "inputs that the triage model resolves with high statistical confidence (|C(x)| = 1) exit locally within 10.7 ms, bypassing "
        "wide-area network transmission and cloud queuing entirely. Conversely, ambiguous or corrupted samples (|C(x)| >= 2) are offloaded "
        "to an elastic cloud GPU cluster hosting high-capacity teacher models (ResNet-152 running on NVIDIA Tesla T4 GPUs via NVIDIA Triton "
        "Inference Server). Importantly, while this study demonstrates this paradigm on split vision classification, the underlying "
        "conformal-gated control architecture serves as an empirical proof of concept for general cascading intelligence, including "
        "Vision-Language Models (VLMs) and cascading Large Language Models (LLMs; Chen et al., 2023 [5]; Patel et al., 2024 [27]), "
        "where semantic query complexity governs escalation to expensive cloud foundation models."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "To balance latency guarantees against operational infrastructure costs, cloud operators deploy elastic serverless autoscaling "
        "engines to scale GPU worker pools based on offload demand (Shahrad et al., 2020 [15]; Yu et al., 2025 [20]). When offload volume "
        "recedes, surplus GPU worker instances terminate to avoid idle billing. When offload volume surges, additional workers initialize to "
        "maintain service level agreements. Figure 1.1 illustrates the two-stage decoupled system architecture connecting high-density IoT ingress streams "
        "through edge serverless triage gateways to elastically provisioned cloud GPU instances."
    )

    # Embed Figure 1.1
    fig1_path = "figures/fig1_system_architecture.png"
    add_figure_with_caption(
        doc,
        fig1_path,
        "Figure 1.1: System architecture of Conformal-Gated Dual-Horizon Autoscaling (CGDA), illustrating the two-stage decoupled design between offline evolutionary AST policy synthesis and the online edge-cloud serving continuum.",
        width_in=5.4
    )

    # -------------------------------------------------------------------------
    # 1.2 THE SEMANTIC COMPLEXITY SHOCK PHENOMENON
    # -------------------------------------------------------------------------
    doc.add_heading("1.2 THE SEMANTIC COMPLEXITY SHOCK PHENOMENON", level=2)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "Standard serverless autoscaling systems assume that computational demand scales proportionally with raw request volume. "
        "In traditional web services, incoming load fluctuates smoothly, allowing reactive controllers to adjust worker capacity by "
        "monitoring trailing CPU utilization or request queue depths."
    )

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "In split inference architectures, raw request volume and physical computational demand become strongly decoupled. "
        "Consider an edge serverless triage gateway aggregating an incoming image ingress stream of 100 requests per second from "
        "distributed IoT endpoints. Under standard, in-distribution input conditions, the lightweight local model resolves 95% of queries "
        "locally, forwarding only 5 requests per second to the cloud GPU tier. When environmental conditions or domain shifts suddenly "
        "degrade input clarity (due to severe noise, blur, or atmospheric corruptions; Hendrycks & Dietterich, 2019 [31]), sample difficulty "
        "spikes without any change in the aggregate IoT ingress arrival rate. We define this event as a semantic complexity shock: an unannounced "
        "shift in input complexity that triggers an immediate collapse in edge confidence, driving cloud offload traffic from 5% to over "
        "80% within seconds."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "Existing autoscalers fail during semantic complexity shocks. Utilization-based schedulers (such as Kubernetes Horizontal Pod "
        "Autoscaler [7]) detect workload changes only after requests have already overloaded active GPUs. Queue-based controllers (such as "
        "KEDA [8]) react only after backlogs accumulate in the message broker. Offline predictive controllers (such as InferLine; Crankshaw "
        "et al., 2020 [6]) fail because raw image arrival counts at the ingress boundary remain constant. Because cloud GPU containers require substantial "
        "startup and model initialization delays (T_boot = 15.0 s), delayed scaling triggers lead to severe queue accumulation. Requests wait "
        "in queues well beyond the allowable latency deadline (D_SLA = 15.0 s), producing widespread deadline violations."
    )

    # -------------------------------------------------------------------------
    # 1.3 FORMAL PROBLEM STATEMENT AND SLA LATENCY BUDGET
    # -------------------------------------------------------------------------
    doc.add_heading("1.3 FORMAL PROBLEM STATEMENT AND SLA LATENCY BUDGET", level=2)

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "We consider a discrete-time continuous serving system indexed by time step t with actuation interval Delta t = 5.0 s. "
        "Each incoming request i arriving at time t_i experiences total end-to-end turnaround latency L_i composed of edge inference delay, "
        "wide-area network transmission delay, cloud queue waiting delay, and cloud GPU execution delay:"
    )

    # OMML Equation 1.1: Latency decomposition
    omml_eq1 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>L</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>edge</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> + </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>net</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> + </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) + </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>cloud</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> ≤ </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>D</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>SLA</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq1, eq_number="1.1")

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "Here, edge execution time t_edge is 10.7 ms under a 150 mCPU serverless container quota on AWS c7i (or 5.0 ms on dedicated edge "
        "gateway cores), network transmission delay t_net is 25.0 ms over an emulated wide-area network (15-35 ms stochastic RTT), "
        "and cloud inference processing latency t_cloud is 62.5 ms per request on NVIDIA Tesla T4 GPU workers at batch saturation (yielding "
        "authoritative worker service capacity mu = 16.0 RPS per worker). The Service Level Agreement deadline budget is established at "
        "D_SLA = 15.0 s. Because physical execution and transmission latencies consume less than 105 ms combined, the queue waiting delay "
        "W_q(t) dominates total turnaround time during congestion."
    )

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "Let W_t denote the active integer worker count provisioned at epoch t. When a scaling command requests an increase to W_{t+1} > W_t, "
        "newly requested container instances remain in initializing state for container startup duration T_boot = 15.0 s before becoming operational. "
        "The objective of the elastic control policy is to select worker trajectories {W_t} that minimize cumulative compute expenditure "
        "(worker-seconds) over horizon T while enforcing zero SLA deadline violations across all N processed requests:"
    )

    # OMML Equation 1.2: Cost optimization objective
    omml_eq2 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>min</m:t></m:r></m:e>'
        '<m:sub><m:r><m:t>{</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>}</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> </m:t></m:r>'
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
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>  s.t.  </m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>∑</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r><m:r><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>N</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>𝕀</m:t></m:r>'
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
        '<m:r><m:t>) = 0</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq2, eq_number="1.2")

    # -------------------------------------------------------------------------
    # 1.4 RESEARCH OBJECTIVES AND PERFORMANCE TARGETS
    # -------------------------------------------------------------------------
    doc.add_heading("1.4 RESEARCH OBJECTIVES AND PERFORMANCE TARGETS", level=2)

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "To resolve the vulnerability of split inference systems under semantic complexity shocks, this capstone project "
        "defines five verifiable research objectives with concrete empirical performance targets:"
    )

    targets = [
        (
            "Target 1 (Zero SLA Deadline Violations): ",
            "Guarantee complete elimination of deadline misses across all 13 evaluation regimes under baseline operational container boot delay "
            "(T_boot = 15.0 s), achieving exactly zero deadline misses where unmitigated reactive baselines fail."
        ),
        (
            "Target 2 (Cost Efficiency vs. Static Provisioning): ",
            "Reduce cumulative cloud compute expenditure (worker-seconds) by at least 50% relative to static peak provisioning, "
            "demonstrating that proactive elastic scaling avoids wasteful resource over-allocation."
        ),
        (
            "Target 3 (Actuation Stability and Churn Suppression): ",
            "Suppress high-frequency controller flapping by at least 80% relative to standard queue-length reactive scalers (KEDA), "
            "protecting physical cloud infrastructure against destructive worker churn."
        ),
        (
            "Target 4 (Interpretable Closed-Loop Policy Synthesis): ",
            "Synthesize an elastic control policy expressed as an explicit, human-readable Abstract Syntax Tree (AST), "
            "avoiding opaque black-box deep reinforcement learning policies that resist verification."
        ),
        (
            "Target 5 (Empirical Characterization of Startup Tipping Point): ",
            "Formally characterize controller sensitivity across a container startup delay ladder (T_boot in [0.5, 300] s), "
            "identifying the theoretical and physical tipping point boundary (T* approx D_SLA = 15.0 s) beyond which proactive scaling transitions into unavoidable queue saturation."
        )
    ]

    for label, desc in targets:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.left_indent = Inches(0.25)
        p_t.paragraph_format.space_before = Pt(2)
        p_t.paragraph_format.space_after = Pt(4)
        p_t.paragraph_format.line_spacing = 1.5
        p_t.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl = p_t.add_run(label)
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(12)
        r_lbl.font.bold = True

        add_formatted_math_text(p_t, desc, font_size_pt=12.0)

    # -------------------------------------------------------------------------
    # 1.5 SUMMARY OF KEY TECHNICAL CONTRIBUTIONS
    # -------------------------------------------------------------------------
    doc.add_heading("1.5 SUMMARY OF KEY TECHNICAL CONTRIBUTIONS", level=2)

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "This thesis introduces Conformal-Gated Dual-Horizon Autoscaling (CGDA), an elastic control framework that bridges statistical "
        "uncertainty quantification with serverless resource management. The technical contributions are summarized as follows:"
    )

    contributions = [
        (
            "1. Edge-Tier Conformal Telemetry Generator: ",
            "We formulate an edge triage mechanism using Regularized Adaptive Prediction Sets (RAPS; Angelopoulos et al., 2021 [1]). "
            "By calibrating non-conformity thresholds on held-out data (q_hat = 0.79914 at alpha = 0.10), the edge node generates zero-lag "
            "feed-forward telemetry tracking empirical offload rate derivatives Delta_offload. This signal alerts the cloud controller to impending surges "
            "several seconds before offloaded requests reach cloud queues, providing a generalizable proof of concept across split vision, VLMs, "
            "and cascading LLM systems."
        ),
        (
            "2. Evolutionary AST Policy Synthesis via OpenEvolve: ",
            "We formulate a domain-specific grammar for dual-horizon elastic control and deploy OpenEvolve [26] to search the policy space. "
            "The multi-objective fitness function optimizes SLA compliance, compute costs, and actuation stability. The search synthesized "
            "an interpretable AST policy incorporating container boot-lock registers and asymmetric hysteresis."
        ),
        (
            "3. Decoupled Two-Loop Continuum Orchestration: ",
            "We design a two-loop runtime controller decoupling fast preemption from slow queue re-anchoring. The fast inner loop engages "
            "proactive capacity reservation under acute offload surges, while the slow outer loop enforces asymmetric scale-down cooldown "
            "(tau_down = 15.0 s, corresponding to three control epochs Delta t = 5.0 s) to eliminate container flapping."
        ),
        (
            "4. Multi-Seed Empirical Validation Across ContinuumBench: ",
            "We evaluate CGDA across 260 matched evaluation runs (1,300 total controller executions) spanning 13 workload regimes derived "
            "from the Azure Functions 2019 trace (Shahrad et al., 2020 [15]; Li et al., 2026 [16]). CGDA achieves 100% SLA compliance (zero misses), "
            "cuts compute costs by 67.38% vs. static peak (diff = -1,446.2 worker-seconds; Wilcoxon p = 2.07 x 10^-44), and suppresses churn by 89.2% relative to KEDA."
        ),
        (
            "5. Open-Source Research Artifacts and Code Availability: ",
            "To support rigorous verification and community extension, the complete experimental testbed, synthesized Abstract Syntax Tree "
            "policy implementations, multi-seed statistical logs, and evaluation figures are publicly available at "
            "https://github.com/vaibhaVishwakarma/complexity-based-autoscaler. All benchmarks and statistical tests run directly within the repository virtual environment."
        )
    ]

    for label, desc in contributions:
        p_c = doc.add_paragraph()
        p_c.paragraph_format.left_indent = Inches(0.25)
        p_c.paragraph_format.space_before = Pt(2)
        p_c.paragraph_format.space_after = Pt(4)
        p_c.paragraph_format.line_spacing = 1.5
        p_c.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl = p_c.add_run(label)
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(12)
        r_lbl.font.bold = True

        add_formatted_math_text(p_c, desc, font_size_pt=12.0)

    # -------------------------------------------------------------------------
    # 1.6 EPISTEMIC EVIDENCE-STATUS TAXONOMY AND THESIS STRUCTURE
    # -------------------------------------------------------------------------
    doc.add_heading("1.6 EPISTEMIC EVIDENCE-STATUS TAXONOMY AND THESIS STRUCTURE", level=2)

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "To uphold strict academic integrity, this report adopts a rigorous epistemic evidence-status taxonomy. "
        "Every quantitative claim, threshold, and performance measurement presented in this thesis is explicitly categorized into one of "
        "four evidence classes, defined in Table 1.1."
    )

    # Table 1.1
    p_t1_title = doc.add_paragraph()
    p_t1_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_title.paragraph_format.space_before = Pt(6)
    p_t1_title.paragraph_format.space_after = Pt(4)
    p_t1_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t1_title, "Table 1.1: Research data taxonomy and experimental verification standards.", font_size_pt=11.0, bold=True)

    t1_headers = ["Evidence Category", "Epistemic Definition & Scope", "Authoritative Source", "Verification Protocol"]
    t1_widths = [Inches(1.4), Inches(2.2), Inches(1.8), Inches(1.2)]

    t1_rows = [
        (
            "Empirical Profile",
            "Direct physical latency profiling on two-tier hardware: edge serverless function feasibility under 150 mCPU Linux cgroups container quota on AWS c7i host (mean = 10.7 ms) and cloud tier on NVIDIA Tesla T4 GPU running Triton Inference Server (mu = 16.0 RPS/worker at batch b=1).",
            "profiling/output-gpu-t4/triton_service_profiles.json",
            "Triton benchmarking, 150 mCPU cgroups profiling, & queuing-aware Spearman correlation (r_s = 0.821)"
        ),
        (
            "Formally Calibrated",
            "Statistical parameters calibrated on held-out validation data satisfying mathematical coverage guarantees (RAPS non-conformity threshold).",
            "calibration/configs/calibration_config.json",
            "Finite-sample quantile calibration (alpha = 0.10)"
        ),
        (
            "Algorithmically Synthesized",
            "Control policies, AST structures, and hyperparameters synthesized via evolutionary search over grammar specifications.",
            "output/champion_policy_v7_smooth.py",
            "Pareto dominance & multi-seed fitness verification"
        ),
        (
            "Evaluated Baseline",
            "Simulated executions of industry-standard control laws (Kubernetes HPA, KEDA, InferLine) under identical workload traces.",
            "output/paper_data/table2_multiseed_1300_runs.csv",
            "20 random seeds x 13 regimes (paired Wilcoxon tests)"
        )
    ]

    tbl_t1 = doc.add_table(rows=len(t1_rows) + 1, cols=4)
    tbl_t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t1.autofit = False
    apply_table_grid_borders(tbl_t1)

    for j, h in enumerate(t1_headers):
        c = tbl_t1.cell(0, j)
        c.width = t1_widths[j]
        set_cell_margins(c, top=40, bottom=40, left=40, right=40)
        p = c.paragraphs[0]
        p.paragraph_format.line_spacing = 1.1
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.bold = True

    for i, row_data in enumerate(t1_rows):
        row = tbl_t1.rows[i + 1]
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = t1_widths[j]
            set_cell_margins(c, top=30, bottom=30, left=30, right=30)
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_math_text(p, val, font_size_pt=9.5)

    p_post_t1 = doc.add_paragraph()
    p_post_t1.paragraph_format.space_before = Pt(8)
    p_post_t1.paragraph_format.space_after = Pt(6)
    p_post_t1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p_post_t1,
        "The remainder of this thesis is structured into ten cohesive chapters as follows. Chapter 2 surveys related literature in serverless autoscaling, "
        "conformal prediction, and split computing. Chapter 3 characterizes production arrival patterns from the Azure Functions 2019 dataset "
        "and defines the ContinuumBench suite across 13 diverse evaluation regimes. Chapter 4 presents the modular continuum architecture of CGDA "
        "and dual-horizon control principles. Chapter 5 formalizes the edge-tier RAPS calibration and fast-loop telemetry derivation. Chapter 6 describes "
        "offline evolutionary policy synthesis using OpenEvolve. Chapter 7 details online two-loop runtime orchestration, fast preemption, and cooldown hysteresis. "
        "Chapter 8 establishes the physical continuum testbed, hardware profiling on AWS c7i and NVIDIA Tesla T4, and the multi-seed evaluation protocol "
        "across five autoscaler archetypes. Chapter 9 presents the comprehensive empirical evaluation across 1,300 benchmark runs, statistical hypothesis tests, "
        "Pareto sensitivity, and container startup delay ladder dynamics. Finally, Chapter 10 appraises theoretical exchangeability bounds, systems constraints, "
        "threats to validity, synthesizes primary scientific takeaways, and identifies future research trajectories across cascading foundation models."
    )

    doc.add_page_break()
