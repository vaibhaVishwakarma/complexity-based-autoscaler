#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch09_evaluation_protocol.py: Chapter 9 Builder for BCE497J Project Report

Drafts Chapter 9: Evaluation Protocol and Baseline Comparisons adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence structures, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations.
- Tables 9.1 and 9.2.
"""

from __future__ import annotations

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from scripts.omml_builder import add_formatted_math_text, add_omml_equation


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


def build_chapter_9(doc: docx.Document):
    """Constructs the full academic content for Chapter 9: Evaluation Protocol and Baseline Comparisons."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 9  EVALUATION PROTOCOL AND BASELINE COMPARISONS", level=1)

    # -------------------------------------------------------------------------
    # 9.1 EXPERIMENTAL EVALUATION DESIGN AND RESEARCH QUESTIONS
    # -------------------------------------------------------------------------
    doc.add_heading("9.1 EXPERIMENTAL EVALUATION DESIGN AND RESEARCH QUESTIONS", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "Evaluating elastic autoscalers in split-inference serving pipelines introduces methodological requirements absent from "
        "traditional web microservice benchmarks. In conventional stateless microservices, request execution latencies remain largely "
        "independent of input semantics, allowing reactive autoscalers to track incoming load using trailing CPU utilization or request "
        "arrival volume. In contrast, split computing pipelines exhibit strong decoupling between raw request arrival rates and backend "
        "computational demand. When environmental perturbations degrade input clarity, edge confidence collapses, diverting requests to the "
        "cloud tier without altering ingress arrival volume."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "To rigorously assess whether Conformal-Gated Dual-Horizon Autoscaling resolves this complexity blindness, our experimental "
        "evaluation is structured around four primary research questions:"
    )

    rq_items = [
        (
            "Research Question 1 (SLA Deadline Compliance under Semantic Shocks): ",
            "Can feed-forward conformal telemetry enable an elastic cloud autoscaler to maintain strict zero-miss SLA compliance "
            "(turnaround latency L_i <= D_SLA = 15.0 s) when subjected to unannounced semantic complexity shocks where raw request arrival "
            "rates lambda(t) remain flat?"
        ),
        (
            "Research Question 2 (Resource Efficiency and Cost Minimization): ",
            "What cumulative GPU compute expenditure (measured in worker-seconds) does CGDA incur relative to static peak provisioning and "
            "industry-standard autoscaling archetypes? Can proactive capacity reservation achieve complete SLA compliance without incurring "
            "excessive idle cost?"
        ),
        (
            "Research Question 3 (Actuation Stability and Churn Suppression): ",
            "Does the decoupled two-loop control architecture with asymmetric scale-down cooldown (tau_down = 15.0 s, spanning three control "
            "epochs Delta t = 5.0 s) successfully eliminate container flapping and actuator wear relative to reactive threshold controllers?"
        ),
        (
            "Research Question 4 (Container Startup Delay Sensitivity and Tipping Point): ",
            "How does autoscaler performance degrade as container initialization delay T_boot scales across the 9-point delay ladder "
            "ranging from 0.5 s to 300 s? Does an empirical tipping point exist where proactive preemption can no longer prevent queue saturation?"
        )
    ]

    for label, text in rq_items:
        p_rq = doc.add_paragraph()
        p_rq.paragraph_format.left_indent = Inches(0.25)
        p_rq.paragraph_format.space_before = Pt(2)
        p_rq.paragraph_format.space_after = Pt(4)
        p_rq.paragraph_format.line_spacing = 1.5
        p_rq.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl = p_rq.add_run(label)
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(12)
        r_lbl.font.bold = True

        add_formatted_math_text(p_rq, text, font_size_pt=12.0)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "We frame this empirical evaluation as a rigorous proof of concept for general cascading intelligence across modern foundation "
        "models, including Vision-Language Models (VLMs) and cascading Large Language Models (LLMs; Valkanas et al., 2025 [68]; Fu et al., "
        "2024 [51]; Turkoglu et al., 2026 [62]; Romero et al., 2021 [31]). While our physical testbed characterizes split vision classification, "
        "the underlying control principles govern any multi-tier architecture where statistical uncertainty sets regulate escalation from "
        "lightweight triage functions to resource-intensive cloud foundation models."
    )

    # -------------------------------------------------------------------------
    # 9.2 BASELINE AUTOSCALING ARCHETYPES
    # -------------------------------------------------------------------------
    doc.add_heading("9.2 BASELINE AUTOSCALING ARCHETYPES", level=2)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "To establish rigorous performance bounds, CGDA is evaluated against four established autoscaling archetypes representing the "
        "full spectrum of industrial and academic practice: static provisioning, reactive utilization tracking, event-driven queue monitoring, "
        "and predictive pipeline-aware traffic envelope modeling."
    )

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "1. Static Peak Provisioning: This policy fixes worker capacity at the cluster provisioning upper bound k(t) = k_max = 18 workers "
        "for all t in [0, T], delivering a constant peak throughput of 288.0 RPS. Static provisioning serves as the empirical zero-miss gold standard "
        "and upper bound for resource consumption. It represents the brute-force over-provisioning strategy that cloud operators adopt when "
        "autoscalers prove too slow to guarantee latency agreements under unpredictable traffic surges."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "2. Reactive CPU-Utilization Autoscaler (Kubernetes HPA; Kubernetes Authors, 2024 [35]): This controller models the default Horizontal "
        "Pod Autoscaler deployed in Kubernetes clusters. At each epoch Delta t = 5.0 s, the controller samples trailing average GPU utilization "
        "U(t) across active workers and computes desired capacity using the standard proportional formula:"
    )

    # OMML Equation 9.1: HPA formula
    ns_m = nsdecls("m")
    omml_eq9_1 = (
        f'<m:oMathPara {ns_m}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>desired</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> + 1) = </m:t></m:r>'
        '<m:r><m:t>⌈</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>current</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) ⋅ </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>U</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>U</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>target</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:den>'
        '</m:f>'
        '<m:r><m:t>⌉</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq9_1, eq_number="9.1")

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "Here, target utilization is established at U_target = 0.70 (70%). The fundamental weakness of HPA in split computing is metric lag: "
        "GPU utilization increases only after offloaded requests traverse the network, clear the queue, and begin execution. By the time U(t) "
        "exceeds 0.70, requests have already buffered in queues, and newly provisioned containers require T_boot = 15.0 s to become operational, "
        "making deadline misses inevitable."
    )

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "3. Reactive Queue-Backlog Autoscaler (KEDA; KEDA Core Team, 2024 [41]): This controller models Kubernetes Event-driven Autoscaling, "
        "monitoring the outstanding request backlog q(t) within the cloud ingress broker. Desired capacity scales proportionally with queue depth:"
    )

    # OMML Equation 9.2: KEDA formula
    omml_eq9_2 = (
        f'<m:oMathPara {ns_m}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>desired</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> + 1) = </m:t></m:r>'
        '<m:r><m:t>⌈</m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>target</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:den>'
        '</m:f>'
        '<m:r><m:t>⌉</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq9_2, eq_number="9.2")

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "Here, target queue backlog is set to q_target = 5 requests per worker. While KEDA detects congestion earlier than HPA, it exhibits "
        "acute actuation instability: transient arrival bursts trigger rapid scale-up commands, followed immediately by scale-down commands "
        "as soon as backlogs momentarily clear, creating severe container flapping and scheduler overhead."
    )

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "4. Predictive Traffic-Envelope Autoscaler (InferLine; Crankshaw et al., 2020 [24]): InferLine represents the academic state of the "
        "art in pipeline-aware inference serving. Using network calculus, InferLine bounds request arrival rates via empirical traffic envelopes "
        "and computes per-stage worker allocations to satisfy deadline D_SLA. InferLine is highly cost-frugal under standard volume shifts. "
        "However, because InferLine derives its traffic envelope strictly from total request arrival rates lambda(t) at the ingress gateway, "
        "it is blind to semantic complexity shifts: when input corruption drops edge resolution from 70% to 20% while lambda(t) remains flat, "
        "InferLine maintains baseline provisioning, allowing cloud queues to collapse."
    )

    # Table 9.1
    p_t1_title = doc.add_paragraph()
    p_t1_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_title.paragraph_format.space_before = Pt(8)
    p_t1_title.paragraph_format.space_after = Pt(4)
    p_t1_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t1_title, "Table 9.1: Formal specifications and control laws of evaluated autoscaler archetypes.", font_size_pt=11.0, bold=True)

    t1_headers = ["Autoscaler Archetype", "Control Paradigm", "Ingress Telemetry", "Target Metric", "Hysteresis Window", "Identified Vulnerability"]
    t1_widths = [Inches(1.4), Inches(1.1), Inches(1.1), Inches(1.0), Inches(1.0), Inches(1.8)]

    t1_rows = [
        ("Static Peak", "Fixed Capacity", "None", "k = 18 workers", "None", "Massive compute cost over-provisioning"),
        ("Kubernetes HPA", "Reactive Utilization", "Trailing GPU Load", "U_target = 0.70", "None", "Metric lag; fails during complexity shocks"),
        ("KEDA Queue", "Reactive Backlog", "Queue Backlog q(t)", "q_target = 5 reqs", "None", "High actuation flapping and churn"),
        ("InferLine", "Predictive Envelope", "Total Ingress lambda(t)", "D_SLA = 15.0 s", "Envelope bounds", "Complexity blindness; ignores triage offload fraction"),
        ("CGDA (Proposed)", "Dual-Horizon Gated", "Conformal Telemetry", "Zero SLA misses", "tau_down = 15.0 s", "Deliberate 12.8% preemption cost premium")
    ]

    tbl_t1 = doc.add_table(rows=len(t1_rows) + 1, cols=6)
    tbl_t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t1.autofit = False

    for j, h in enumerate(t1_headers):
        c = tbl_t1.cell(0, j)
        c.width = t1_widths[j]
        set_cell_margins(c, top=40, bottom=40, left=30, right=30)
        p = c.paragraphs[0]
        p.paragraph_format.line_spacing = 1.1
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
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
            add_formatted_math_text(p, val, font_size_pt=9.0)

    # -------------------------------------------------------------------------
    # 9.3 MULTI-SEED MATCHED EVALUATION PROTOCOL
    # -------------------------------------------------------------------------
    doc.add_heading("9.3 MULTI-SEED MATCHED EVALUATION PROTOCOL", level=2)

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p11.paragraph_format.space_before = Pt(6)
    add_formatted_math_text(
        p11,
        "To eliminate random perturbation artifacts and evaluate statistical robustness, we enforce a fully crossed experimental protocol: "
        "20 independent random seeds across 13 benchmark regimes for 5 autoscaling controllers, yielding exactly 1,300 total controller "
        "executions and 260 matched evaluation pairs per controller. The 20 random seeds (seeds 1042 through 1061) govern Poisson arrival time "
        "realizations and per-request image sampling from Tiny ImageNet-C. Critically, for any given (regime, seed) pair, all five controllers "
        "execute against the exact same sequence of request timestamps and input images, ensuring strictly matched pairwise comparisons."
    )

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "The 13 benchmark stress regimes are partitioned into three distinct suites (Table 9.2). Suite 1 exercises synthetic rate dynamics "
        "to confirm that CGDA maintains stability on conventional workloads. Suite 2 introduces complexity shocks, compound multi-axis stress, "
        "and decoupled arrival-complexity regimes to test semantic awareness. Suite 3 replays the Azure Functions 2019 trace to establish "
        "production realism."
    )

    # Table 9.2
    p_t2_title = doc.add_paragraph()
    p_t2_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_title.paragraph_format.space_before = Pt(8)
    p_t2_title.paragraph_format.space_after = Pt(4)
    p_t2_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t2_title, "Table 9.2: Complete taxonomy of the 13 ContinuumBench stress regimes across evaluation suites.", font_size_pt=11.0, bold=True)

    t2_headers = ["Suite", "Regime Identifier", "Arrival Volume Pattern", "Semantic Offload Shift", "Target Stress Dimension"]
    t2_widths = [Inches(0.6), Inches(1.8), Inches(1.8), Inches(1.6), Inches(1.6)]

    t2_rows = [
        ("1", "suite1_flat", "Constant low-load (60 RPS)", "Constant p_fast = 0.50", "Baseline quiescence & idle cost"),
        ("1", "suite1_spike", "Instantaneous 5x surge (300 RPS)", "Constant p_fast = 0.50", "Peak capacity provisioning"),
        ("1", "suite1_burst", "Sustained bursty arrivals (40-200 RPS)", "Constant p_fast = 0.50", "Queue stability under Poisson jitter"),
        ("1", "suite1_ramp", "Linear increase (20 to 160 RPS)", "Constant p_fast = 0.50", "Ramp tracking & scale-up lead time"),
        ("1", "suite1_zero_begin", "Cold-start from zero (0 to 120 RPS)", "Constant p_fast = 0.50", "Container boot latency lag"),
        ("1", "suite1_zero_terminal", "Drain to zero (120 to 0 RPS)", "Constant p_fast = 0.50", "Scale-down cooldown hysteresis"),
        ("2", "suite2_shock", "Flat arrival volume (80 RPS)", "p_fast drops 0.70 -> 0.20", "Semantic complexity blindness"),
        ("2", "suite2_recovery", "Step shock followed by quiet", "p_fast drops 0.70 -> 0.20 -> 0.70", "Overshoot control & de-allocation"),
        ("2", "suite2_compound_stress", "Volume surge + complexity shock", "lambda: 50 -> 150 RPS, p_fast: 0.8 -> 0.2", "Worst-case multi-axis saturation"),
        ("2", "suite2_compound_relief", "Volume drop + complexity relief", "lambda: 150 -> 50 RPS, p_fast: 0.2 -> 0.8", "Under-provisioning avoidance"),
        ("2", "suite2_decoupled_opposing", "Volume rises while complexity drops", "lambda: 40 -> 160 RPS, p_fast: 0.4 -> 0.8", "Decoupled volume-complexity dynamics"),
        ("2", "suite2_storm", "High-variance stochastic oscillations", "Volatile random walk across lambda and p_fast", "Extreme turbulence & actuation stability"),
        ("3", "suite3_azure", "Azure Functions 2019 diurnal replay", "Trace-driven diurnal variance (0.08x scale)", "Production serverless macrobenchmark")
    ]

    tbl_t2 = doc.add_table(rows=len(t2_rows) + 1, cols=5)
    tbl_t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t2.autofit = False

    for j, h in enumerate(t2_headers):
        c = tbl_t2.cell(0, j)
        c.width = t2_widths[j]
        set_cell_margins(c, top=40, bottom=40, left=30, right=30)
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
            add_formatted_math_text(p, val, font_size_pt=9.0)

    # -------------------------------------------------------------------------
    # 9.4 STATISTICAL SIGNIFICANCE TESTING FRAMEWORK
    # -------------------------------------------------------------------------
    doc.add_heading("9.4 STATISTICAL SIGNIFICANCE TESTING FRAMEWORK", level=2)

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p13.paragraph_format.space_before = Pt(6)
    add_formatted_math_text(
        p13,
        "System performance distributions in serverless computing frequently exhibit heavy tails, multimodality, and point masses at zero "
        "(such as zero-miss executions), violating the normality assumptions required by Student t-tests. Consequently, this study employs "
        "non-parametric statistical methods. All paired comparisons are conducted via two-sided Wilcoxon signed-rank tests with Pratt "
        "zero-difference handling across the n = 260 matched evaluation pairs per controller."
    )

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "For matched pairs (X_i, Y_i) representing CGDA and baseline metric observations for the i-th (regime, seed) trial, absolute "
        "differences |D_i| = |X_i - Y_i| are ranked in ascending order. The test statistic W+ sums the ranks of positive differences:"
    )

    # OMML Equation 9.3: Wilcoxon signed-rank statistic
    omml_eq9_3 = (
        f'<m:oMathPara {ns_m}>'
        '<m:oMath>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>+</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> = </m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>∑</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r><m:r><m:rPr><m:nor/></m:rPr><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>n</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>sgn(</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>D</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>) ⋅ </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>R</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:d>'
        '<m:dPr><m:begChr m:val="|"/><m:endChr m:val="|"/></m:dPr>'
        '<m:e>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>D</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>i</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:e>'
        '</m:d>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq9_3, eq_number="9.3")

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "To quantify practical significance beyond statistical p-values, we compute standardized Cohen's d effect sizes using the standard "
        "deviation of paired differences as the denominator. Effect sizes |d| >= 0.8 are classified as large effects. To prevent false "
        "discovery inflation across multi-metric hypothesis testing, significance p-values are adjusted using the Holm-Bonferroni step-down "
        "procedure, controlling the Family-Wise Error Rate (FWER) at alpha = 0.01 (denoted by a checkmark) and alpha = 0.05 (denoted by a triangle)."
    )

    # -------------------------------------------------------------------------
    # 9.5 EVALUATION METRICS AND INSTRUMENTATION
    # -------------------------------------------------------------------------
    doc.add_heading("9.5 EVALUATION METRICS AND INSTRUMENTATION", level=2)

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "System performance is captured across five orthogonal metrics instrumented directly within the simulation engine:"
    )

    metric_items = [
        (
            "1. SLA Deadline Violations (Misses): ",
            "The count and rate of processed requests whose total turnaround latency exceeds the hard SLA deadline budget D_SLA = 15.0 s. "
            "In mission-critical serving, any non-zero miss rate constitutes an SLA breach."
        ),
        (
            "2. GPU Compute Expenditure (Worker-Seconds): ",
            "The time integral of provisioned GPU worker capacity over evaluation horizon T: WS = integral_0^T k(t) dt. Because cloud providers "
            "bill container instances based on allocated wall-clock duration, worker-seconds represent the direct economic cost of serving."
        ),
        (
            "3. 99th Percentile Tail Latency (P99): ",
            "The 99th percentile end-to-end turnaround latency across all completed requests, capturing the worst-case experience of degraded queries."
        ),
        (
            "4. Cloud Queue Waiting Time (W_q): ",
            "The mean duration requests spend buffered in the cloud message broker waiting for an available GPU worker."
        ),
        (
            "5. Actuation Churn (Scaling Deltas): ",
            "The total number of scaling events where k(t+1) != k(t). High churn indicates container flapping, inducing scheduler overhead, "
            "network thrashing, and memory deallocation stress."
        )
    ]

    for label, text in metric_items:
        p_m = doc.add_paragraph()
        p_m.paragraph_format.left_indent = Inches(0.25)
        p_m.paragraph_format.space_before = Pt(2)
        p_m.paragraph_format.space_after = Pt(4)
        p_m.paragraph_format.line_spacing = 1.5
        p_m.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl = p_m.add_run(label)
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(12)
        r_lbl.font.bold = True

        add_formatted_math_text(p_m, text, font_size_pt=12.0)
    doc.add_page_break()
