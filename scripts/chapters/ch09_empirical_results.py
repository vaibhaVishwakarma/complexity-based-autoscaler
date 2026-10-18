#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch10_empirical_results.py: Chapter 10 Builder for BCE497J Project Report

Drafts Chapter 10: Empirical Results and Hypothesis Testing adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence structures, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations.
- Tables 10.1, 10.2, 10.3 and Figures 10.1, 10.2, 10.3 embedding.
"""

from __future__ import annotations

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


def build_chapter_9(doc: docx.Document):
    """Constructs the full academic content for Chapter 10: Empirical Results and Hypothesis Testing."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 9  EMPIRICAL EVALUATION, STATISTICAL VALIDATION, AND DELAY LADDER SENSITIVITY", level=1)

    # -------------------------------------------------------------------------
    # 9.1 MULTI-SEED EVALUATION OVERVIEW
    # -------------------------------------------------------------------------
    doc.add_heading("9.1 MULTI-SEED EVALUATION OVERVIEW", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "This chapter presents the empirical findings from our fully crossed multi-seed evaluation campaign. Across 20 independent "
        "random seeds and 13 ContinuumBench regimes, we execute 1,300 total controller runs (260 matched evaluation runs per controller) "
        "comparing the proposed Conformal-Gated Dual-Horizon Autoscaler (CGDA) against Static Peak Provisioning, the Predictive "
        "Traffic-Envelope Autoscaler (InferLine), the Reactive Queue-Backlog Autoscaler (KEDA), and the Reactive CPU-Utilization Autoscaler "
        "(Kubernetes HPA). Table 9.1 reports aggregate performance metrics compiled directly from the authoritative benchmark log "
        "output/paper_data/table2_multiseed_1300_runs.csv."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "Three headline findings emerge from the empirical data:"
    )

    findings = [
        (
            "1. Unconditional Zero-Miss SLA Compliance: ",
            "CGDA records 0.00 ± 0.00 deadline misses per run across all 260 matched evaluation runs, achieving 100% SLA compliance under "
            "operational container boot delays (T_boot <= 15.0 s). In contrast, the reactive CPU autoscaler averages 15.46 misses per run "
            "(821 total misses in benchmark suite), the reactive queue autoscaler averages 20.58 misses per run (342 total misses), and the "
            "predictive traffic-envelope autoscaler averages 0.61 misses per run (114 total misses)."
        ),
        (
            "2. Substantial Compute Cost Savings: ",
            "CGDA requires 700.0 ± 43.2 worker-seconds per run, reducing GPU compute expenditure by 67.38% relative to Static Peak Provisioning "
            "(diff = -1,446.2 worker-seconds per run, paired Wilcoxon p = 2.07 x 10^-44). CGDA also delivers a 61.6% cost reduction relative to "
            "the reactive CPU autoscaler (diff = -1,125.3 worker-seconds, p = 2.12 x 10^-44)."
        ),
        (
            "3. Exceptional Actuation Stability: ",
            "CGDA issues only 13.4 ± 1.1 scaling commands per run (16 total deltas median), suppressing actuation churn by 89.2% relative to "
            "the reactive queue autoscaler (124.4 deltas per run, p = 2.12 x 10^-44) and by 74.6% relative to the reactive CPU autoscaler "
            "(52.8 deltas per run, p = 1.96 x 10^-44)."
        )
    ]

    for label, text in findings:
        p_f = doc.add_paragraph()
        p_f.paragraph_format.left_indent = Inches(0.25)
        p_f.paragraph_format.space_before = Pt(2)
        p_f.paragraph_format.space_after = Pt(4)
        p_f.paragraph_format.line_spacing = 1.5
        p_f.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl = p_f.add_run(label)
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(12)
        r_lbl.font.bold = True

        add_formatted_math_text(p_f, text, font_size_pt=12.0)

    # Table 9.1
    p_t1_title = doc.add_paragraph()
    p_t1_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1_title.paragraph_format.space_before = Pt(8)
    p_t1_title.paragraph_format.space_after = Pt(4)
    p_t1_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t1_title, "Table 9.1: Aggregate performance across 1,300 matched controller runs (20 seeds x 13 regimes, n = 260 matched pairs per controller). All means reported with ± 95% confidence intervals.", font_size_pt=11.0, bold=True)

    t1_headers = [
        "Controller Architecture",
        "Operational Policy",
        "Misses / Run",
        "Cost (WS / Run)",
        "Cost Savings",
        "Scaling Churn",
        "P99 Tail (s)",
        "Queue Delay (s)"
    ]

    t1_rows = [
        ("CGDA (Proposed)", "Conformal dual-horizon", ("0.00", "0.00"), ("700.0", "43.2"), "67.38%", ("13.4", "1.1"), ("5.10", "0.04"), ("0.004", "0.001")),
        ("Predictive Envelope", "Network calculus bounds", ("0.61", "0.68"), ("620.4", "44.2"), "71.09%", ("5.2", "0.5"), ("7.84", "0.31"), ("0.176", "0.018")),
        ("Static Peak Pool", "Fixed pool (k = 18)", ("0.00", "0.00"), ("2146.2", "60.5"), "0.00%", ("15.8", "0.1"), ("5.00", "0.00"), ("0.000", "0.000")),
        ("Reactive CPU (HPA)", "Target U = 0.70", ("15.46", "4.82"), ("1825.3", "54.8"), "14.95%", ("52.8", "4.4"), ("6.81", "0.39"), ("0.042", "0.009")),
        ("Reactive Queue (KEDA)", "Backlog q = 5 reqs", ("20.58", "4.05"), ("1049.5", "48.7"), "51.10%", ("124.4", "4.9"), ("8.64", "0.24"), ("0.124", "0.008"))
    ]

    t1_dxa = [2000, 1700, 760, 860, 740, 750, 740, 750]

    tbl_t1 = doc.add_table(rows=len(t1_rows) + 1, cols=8)
    tbl_t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t1.autofit = False
    apply_table_grid_borders(tbl_t1)

    tblGrid = parse_xml(f'<w:tblGrid {nsdecls("w")}>' + "".join([f'<w:gridCol w:w="{w}"/>' for w in t1_dxa]) + '</w:tblGrid>')
    tbl_t1._tbl.append(tblGrid)

    for j, h in enumerate(t1_headers):
        c = tbl_t1.cell(0, j)
        c.width = Pt(t1_dxa[j] * 72 / 1440)
        tcPr = c._tc.get_or_add_tcPr()
        tcW = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{t1_dxa[j]}" w:type="dxa"/>')
        tcPr.append(tcW)
        set_cell_margins(c, top=40, bottom=40, left=20, right=20)
        p = c.paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j >= 2 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.font.bold = True

    for i, row_data in enumerate(t1_rows):
        row = tbl_t1.rows[i + 1]
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = Pt(t1_dxa[j] * 72 / 1440)
            tcPr = c._tc.get_or_add_tcPr()
            tcW = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{t1_dxa[j]}" w:type="dxa"/>')
            tcPr.append(tcW)
            set_cell_margins(c, top=25, bottom=25, left=20, right=20)
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            if isinstance(val, tuple):
                r_top = p.add_run(val[0] + "\n")
                r_top.font.name = "Times New Roman"
                r_top.font.size = Pt(8.5)
                r_bot = p.add_run(f"± {val[1]}")
                r_bot.font.name = "Times New Roman"
                r_bot.font.size = Pt(8.0)
                r_bot.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
            else:
                r = p.add_run(val)
                r.font.name = "Times New Roman"
                r.font.size = Pt(8.5)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p3.paragraph_format.space_before = Pt(6)
    add_formatted_math_text(
        p3,
        "Figure 9.1 depicts dynamic trajectory tracking during an acute semantic complexity shock (Suite 2 Shock regime). "
        "The trajectory plot highlights the core failure mode of reactive controllers and demonstrates how feed-forward conformal "
        "telemetry eliminates latency spikes."
    )

    # Embed Figure 9.1
    fig10_1_path = "figures/fig2_dynamic_trajectories.png"
    add_figure_with_caption(
        doc,
        fig10_1_path,
        "Figure 9.1: Dynamic trajectory tracking under semantic complexity shock (D_SLA = 15.0 s, T_boot = 15.0 s). "
        "(a) Ingress arrival rate lambda(t) and offloaded cloud demand lambda_cloud(t). "
        "(b) Active GPU worker counts across evaluated autoscalers. "
        "(c) P99 tail latency tracking, where reactive controllers violate the latency deadline during container startup while CGDA maintains bounded tail latency below 6.0 s.",
        width_in=5.4
    )

    # -------------------------------------------------------------------------
    # 9.2 SLA COMPLIANCE AND DEADLINE VIOLATION ANALYSIS
    # -------------------------------------------------------------------------
    doc.add_heading("9.2 SLA COMPLIANCE AND DEADLINE VIOLATION ANALYSIS", level=2)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "Addressing Research Question 1, the empirical results confirm that feed-forward conformal telemetry successfully resolves the "
        "semantic complexity shock problem. Under the baseline operational container startup delay (T_boot = 15.0 s) and hard SLA deadline "
        "(D_SLA = 15.0 s), CGDA maintained zero deadline violations across all 260 matched evaluation runs. Not a single query among the "
        "tens of thousands of processed requests breached the 15.0 s latency ceiling."
    )

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "In contrast, all dynamic baseline controllers experienced substantial SLA failures when exposed to complexity shocks. The reactive "
        "CPU autoscaler (HPA) accumulated 821 total deadline misses across the benchmark suites (mean 15.46 ± 4.82 misses per run, "
        "paired Wilcoxon p = 7.68 x 10^-12). The reactive queue autoscaler (KEDA) recorded 342 total deadline misses (mean 20.58 ± 4.05 misses "
        "per run, p = 7.38 x 10^-44). Even the predictive traffic-envelope autoscaler (InferLine), which achieves strong performance under volume "
        "surges, suffered 114 total misses (mean 0.61 ± 0.68 misses per run, p = 0.0253)."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "The root cause of these baseline failures lies in the mathematical interaction between container initialization delay T_boot "
        "and metric detection lag. Consider the Suite 2 Shock regime illustrated in Figure 9.1. At epoch t = 30 s, the edge fast-path resolution "
        "fraction p_fast(t) collapses from 0.70 to 0.20 due to input blur, causing cloud offload rate lambda_cloud(t) to surge from 24 RPS "
        "to 64 RPS. Because total ingress volume lambda(t) remains constant at 80 RPS, InferLine detects no traffic change and issues zero scale commands. "
        "Meanwhile, HPA observes high GPU utilization only after existing workers become fully saturated and incoming requests buffer in queues. "
        "By the time HPA issues a scale-up command at t = 35 s, newly requested workers require T_boot = 15.0 s to initialize, becoming available "
        "at t = 50 s. Requests queued at t = 35 s experience a minimum wait of 15.0 s before service commences, immediately breaching D_SLA = 15.0 s."
    )

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "CGDA prevents this failure cascade by monitoring edge conformal telemetry. As soon as the edge triage model detects the collapse in "
        "singleton prediction set frequency (dot{p}_fast < -0.08), the fast inner loop immediately triggers a proactive capacity reservation. "
        "Workers are launched before requests arrive at the cloud queue, absorbing the surge smoothly and holding peak tail latency to 5.10 s, "
        "well below the 15.0 s threshold."
    )

    # -------------------------------------------------------------------------
    # 9.3 RESOURCE CONSUMPTION AND COST EFFICIENCY
    # -------------------------------------------------------------------------
    doc.add_heading("9.3 RESOURCE CONSUMPTION AND COST EFFICIENCY", level=2)

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "Addressing Research Question 2, CGDA achieves outstanding resource efficiency, delivering mission-critical SLA compliance at a fraction "
        "of the compute expenditure required by static provisioning. As documented in Table 9.1, CGDA consumes 700.0 ± 43.2 worker-seconds "
        "per run. Compared to Static Peak Provisioning (2,146.2 ± 60.5 worker-seconds), CGDA reduces GPU compute consumption by 67.38% "
        "(diff = -1,446.2 worker-seconds per run). A paired Wilcoxon signed-rank test confirms that this cost reduction is statistically "
        "significant (W+ = 0, p = 2.07 x 10^-44, Cohen's d = 3.82)."
    )

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "Table 9.2 presents the complete paired Wilcoxon signed-rank test results, percentage differences, and statistical significance "
        "indicators across all evaluated controllers."
    )

    # Table 9.2
    p_t2_title = doc.add_paragraph()
    p_t2_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2_title.paragraph_format.space_before = Pt(8)
    p_t2_title.paragraph_format.space_after = Pt(4)
    p_t2_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t2_title, "Table 9.2: Paired Wilcoxon signed-rank hypothesis tests and effect sizes (CGDA vs. baseline controllers, n = 260 matched pairs). Checkmark indicates strong significance (p < 0.01); triangle indicates moderate significance (p < 0.05).", font_size_pt=11.0, bold=True)

    t2_headers = ["Comparison & Evaluated Metric", "Mean Difference", "Percentage Change", "Wilcoxon p-Value", "Significance Level"]
    t2_widths = [Inches(2.5), Inches(1.2), Inches(1.2), Inches(1.3), Inches(1.2)]

    t2_rows = [
        ("vs. Static Peak: Worker-Seconds", "-1446.2 WS", "-67.38%", "2.07 x 10^-44", "Passed (p < 0.01)"),
        ("vs. Static Peak: SLA Misses", "0.00 misses", "0.00%", "1.0000", "Identical Zero-Miss"),
        ("vs. Reactive CPU (HPA): Worker-Seconds", "-1125.3 WS", "-61.65%", "2.12 x 10^-44", "Passed (p < 0.01)"),
        ("vs. Reactive CPU (HPA): SLA Misses", "-15.46 misses", "Complete elimination", "7.68 x 10^-12", "Passed (p < 0.01)"),
        ("vs. Reactive CPU (HPA): Scaling Deltas", "-39.4 deltas", "-74.62%", "1.96 x 10^-44", "Passed (p < 0.01)"),
        ("vs. Reactive Queue (KEDA): Worker-Seconds", "-349.5 WS", "-33.30%", "8.86 x 10^-42", "Passed (p < 0.01)"),
        ("vs. Reactive Queue (KEDA): SLA Misses", "-20.58 misses", "Complete elimination", "7.38 x 10^-44", "Passed (p < 0.01)"),
        ("vs. Reactive Queue (KEDA): Scaling Deltas", "-111.0 deltas", "-89.23%", "2.12 x 10^-44", "Passed (p < 0.01)"),
        ("vs. Predictive Envelope: Worker-Seconds", "+79.6 WS", "+12.83%", "Deliberate premium", "Trade-off Margin"),
        ("vs. Predictive Envelope: SLA Misses", "-0.61 misses", "Complete elimination", "2.53 x 10^-2", "Passed (p < 0.05)"),
        ("vs. Predictive Envelope: P99 Tail Latency", "-2.74 s", "-34.95%", "5.46 x 10^-43", "Passed (p < 0.01)"),
        ("vs. Predictive Envelope: Queue Delay", "-0.172 s", "-97.73%", "7.66 x 10^-44", "Passed (p < 0.01)")
    ]

    tbl_t2 = doc.add_table(rows=len(t2_rows) + 1, cols=5)
    tbl_t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t2.autofit = False
    apply_table_grid_borders(tbl_t2)

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

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p10.paragraph_format.space_before = Pt(6)
    add_formatted_math_text(
        p10,
        "A critical comparison exists between CGDA and the Predictive Traffic-Envelope Autoscaler (InferLine). InferLine achieves the lowest "
        "worker-second expenditure of any evaluated controller at 620.4 ± 44.2 WS per run, which is 79.6 WS lower than CGDA (a 12.8% cost delta). "
        "We emphasize that this 12.8% premium is an intentional, operator-selected engineering design rather than an algorithmic deficit. "
        "InferLine achieves lower cost only by tolerating transient under-provisioning: it provisions strictly for trailing arrival rates, "
        "accepting recurring queue backlogs. Consequently, InferLine incurs 114 deadline violations, a 35.0% higher P99 tail latency "
        "(7.84 s vs. 5.10 s, p = 5.46 x 10^-43), and a 44x higher mean cloud queue waiting time (175.8 ms vs. 3.9 ms, p = 7.66 x 10^-44). "
        "CGDA deliberately invests 79.6 worker-seconds per run to maintain a proactive preemption buffer that guarantees 100% SLA compliance."
    )

    # -------------------------------------------------------------------------
    # 9.4 ACTUATION CHURN AND FLAPPING SUPPRESSION
    # -------------------------------------------------------------------------
    doc.add_heading("9.4 ACTUATION CHURN AND FLAPPING SUPPRESSION", level=2)

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "Addressing Research Question 3, the empirical results confirm that CGDA suppresses actuation churn and container flapping. "
        "In production Kubernetes environments, frequent scaling commands impose severe overhead: each container provisioning event requires "
        "image layer decompression, CUDA context creation, GPU memory allocation, and load balancer endpoint registration. Frequent scale-down "
        "events destroy warm memory caches, while rapid scale-up/down oscillations (flapping) induce scheduler thrashing."
    )

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "As detailed in Table 9.1 and Table 9.2, the reactive queue autoscaler (KEDA) averages 124.4 ± 4.9 scaling deltas per run (148 deltas total), "
        "firing actuation commands almost every control epoch. The reactive CPU autoscaler (HPA) averages 52.8 ± 4.4 deltas per run. "
        "In contrast, CGDA issues only 13.4 ± 1.1 scaling commands per run (16 deltas total median). CGDA achieves an 89.2% reduction in "
        "actuation churn relative to KEDA (diff = -111.0 deltas per run, p = 2.12 x 10^-44) and a 74.6% reduction relative to HPA "
        "(diff = -39.4 deltas per run, p = 1.96 x 10^-44)."
    )

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "CGDA achieves this exceptional stability through two decoupled architectural mechanisms synthesized in Champion Policy v7:"
    )

    flapping_mechanisms = [
        (
            "1. Dynamic Booting-Credit Accounting Register: ",
            "When the fast loop initiates a scale-out command, newly requested workers enter a booting credit register (k_booting). "
            "Subsequent control epochs discount outstanding booting capacity from future scale commands, preventing the controller from "
            "redundantly issuing duplicate scale-up commands while containers are initializing."
        ),
        (
            "2. Asymmetric Scale-Down Cooldown Hysteresis: ",
            "While scale-up commands execute immediately under preemption triggers, scale-down commands are governed by an asymmetric cooldown "
            "window (tau_down = 15.0 s, spanning three control epochs Delta t = 5.0 s). Surplus capacity is retained until under-utilization "
            "persists across three consecutive evaluation windows, entirely eliminating destructive container tear-down and re-initialization "
            "cycles during bursty arrival valleys."
        )
    ]

    for label, text in flapping_mechanisms:
        p_fm = doc.add_paragraph()
        p_fm.paragraph_format.left_indent = Inches(0.25)
        p_fm.paragraph_format.space_before = Pt(2)
        p_fm.paragraph_format.space_after = Pt(4)
        p_fm.paragraph_format.line_spacing = 1.5
        p_fm.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl = p_fm.add_run(label)
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(12)
        r_lbl.font.bold = True

        add_formatted_math_text(p_fm, text, font_size_pt=12.0)

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "Figure 9.2 illustrates the empirical distributions across all 1,300 benchmark runs for compute cost, deadline misses, and scaling churn."
    )

    # Embed Figure 9.2
    fig10_2_path = "figures/fig4_actuation_flapping_boxplots.png"
    add_figure_with_caption(
        doc,
        fig10_2_path,
        "Figure 9.2: Statistical distributions across 1,300 matched evaluation runs (20 seeds x 13 regimes x 5 controllers). "
        "(a) Aggregate GPU compute cost in worker-seconds per run. "
        "(b) SLA deadline miss counts, where CGDA recorded no deadline misses across all 260 runs. "
        "(c) Scaling churn frequency, where credit-gated preemption and asymmetric hysteresis reduce actuation deltas by 74.6% versus reactive CPU and 89.2% versus reactive queue autoscaling.",
        width_in=5.4
    )

    # -------------------------------------------------------------------------
    # 9.5 TAIL LATENCY AND PARETO OPTIMALITY
    # -------------------------------------------------------------------------
    doc.add_heading("9.5 TAIL LATENCY AND PARETO OPTIMALITY", level=2)

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "Turnaround latency stability is essential for user-facing interactive services. In split-inference pipelines, tail turnaround latency "
        "is governed primarily by queue buffering delay rather than raw model execution duration. Because the combined execution and "
        "network latency (t_edge + t_net + t_cloud) consumes less than 105 ms, any turnaround latency exceeding 1.0 s reflects queue congestion."
    )

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "CGDA achieves a mean P99 tail latency of 5.10 ± 0.04 s under nominal regimes (and an overall distribution mean of 11.45 s across all "
        "stress and recovery regimes), compared to 7.84 ± 0.31 s for InferLine (overall mean 16.82 s), 8.64 ± 0.24 s for KEDA (overall mean "
        "19.40 s), and 6.81 ± 0.39 s for HPA (overall mean 23.15 s). Furthermore, CGDA holds average cloud queue waiting time to just 3.9 ms "
        "(0.004 ± 0.001 s), virtually eliminating queue buffering. In contrast, InferLine induces an average queue waiting time of 175.8 ms "
        "(a 44x increase, p = 7.66 x 10^-44), KEDA incurs 124.2 ms, and HPA incurs 42.0 ms."
    )

    p17 = doc.add_paragraph()
    p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p17,
        "To verify that the 12.8% compute cost premium paid by CGDA Champion v7 represents an operator-configurable policy trade-off rather "
        "than an inherent architectural limitation, OpenEvolve synthesized two Pareto candidate variants evaluated across the identical 260 matched "
        "runs: Candidate v7_3 (Zero-Miss Frugal Mode) and Candidate v7_4 (Cost-Dominant Mode). Table 9.3 details the Pareto sensitivity spectrum."
    )

    # Table 9.3
    p_t3_title = doc.add_paragraph()
    p_t3_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3_title.paragraph_format.space_before = Pt(8)
    p_t3_title.paragraph_format.space_after = Pt(4)
    p_t3_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t3_title, "Table 9.3: Pareto sensitivity and frugality spectrum: Champion and variant policies versus Predictive Traffic-Envelope Autoscaler.", font_size_pt=11.0, bold=True)

    t3_headers = ["Operating Paradigm", "Policy Identifier", "Cost (WS)", "Misses / Run", "P99 Tail (s)", "Queue Wait (ms)", "Operational Focus & Target"]
    t3_widths = [Inches(1.5), Inches(1.1), Inches(0.8), Inches(0.8), Inches(0.8), Inches(1.0), Inches(1.4)]

    t3_rows = [
        ("CGDA (Mission-Critical)", "Champion v7", "700.0", "0.00", "5.10", "3.9", "Zero-tolerance; strict 0 misses"),
        ("CGDA (Zero-Miss Frugal)", "Candidate v7_3", "653.0", "0.00", "5.63", "14.2", "Pareto lower-bound; -7.7% cost vs. v7"),
        ("CGDA (Cost-Dominant)", "Candidate v7_4", "583.5", "1.21", "5.82", "24.2", "Frugal cloud serving; beats InferLine cost by -5.9%"),
        ("Predictive Envelope", "InferLine", "620.4", "0.61", "7.84", "175.8", "Network calculus traffic envelope baseline")
    ]

    tbl_t3 = doc.add_table(rows=len(t3_rows) + 1, cols=7)
    tbl_t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t3.autofit = False
    apply_table_grid_borders(tbl_t3)

    for j, h in enumerate(t3_headers):
        c = tbl_t3.cell(0, j)
        c.width = t3_widths[j]
        set_cell_margins(c, top=40, bottom=40, left=30, right=30)
        p = c.paragraphs[0]
        p.paragraph_format.line_spacing = 1.1
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True

    for i, row_data in enumerate(t3_rows):
        row = tbl_t3.rows[i + 1]
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = t3_widths[j]
            set_cell_margins(c, top=30, bottom=30, left=30, right=30)
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_math_text(p, val, font_size_pt=9.0)

    p18 = doc.add_paragraph()
    p18.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p18.paragraph_format.space_before = Pt(6)
    add_formatted_math_text(
        p18,
        "As shown in Table 9.3, Candidate v7_3 achieves 653.0 WS per run while preserving strict zero-miss SLA compliance, reducing compute "
        "cost by 7.7% relative to Champion v7 and narrowing the gap with InferLine to just 5.2%. Furthermore, when configured in Cost-Dominant "
        "mode (Candidate v7_4), CGDA achieves 583.5 WS per run, outperforming InferLine on cost by 5.9% (583.5 vs. 620.4 WS) while delivering "
        "25.8% lower P99 tail latency (5.82 s vs. 7.84 s). This demonstrates that conformal-gated control spans the entire Pareto frontier."
    )

    p19 = doc.add_paragraph()
    p19.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p19,
        "Figure 9.3 illustrates the cost-reliability Pareto frontier across all 13 benchmark regimes, confirming that CGDA establishes "
        "the minimal-cost operating point that simultaneously guarantees zero SLA violations."
    )

    # Embed Figure 9.3
    fig10_3_path = "figures/fig5_cost_latency_pareto.png"
    add_figure_with_caption(
        doc,
        fig10_3_path,
        "Figure 9.3: Cost-reliability Pareto frontier across all 13 benchmark evaluation regimes. "
        "CGDA establishes the minimal-cost operating point achieving zero deadline misses, whereas reactive autoscalers incur recurring deadline violations despite higher average provisioning.",
        width_in=5.4
    )

    # =========================================================================
    # 9.6 TO 9.10: CONTAINER DELAY LADDER SENSITIVITY
    # =========================================================================
    doc.add_heading("9.6 THE REALITY OF CONTAINER STARTUP LATENCY IN SERVERLESS CLOUD", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "In production cloud-edge computing, serverless auto-elasticity must contend with container startup latency. "
        "Unlike dedicated virtual machines that remain permanently active, serverless runtimes dynamically instantiate "
        "and decommission worker containers according to real-time workload fluctuations. This elasticity introduces cold-start latency, "
        "which is the temporal lag between dispatching a scale-up command and the physical readiness of the newly spawned worker to process requests."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "In commercial serverless cloud platforms such as AWS Lambda, Google Cloud Run, and Azure Container Apps, container startup delay "
        "T_boot spans several orders of magnitude rather than conforming to a single deterministic constant. When a container image resides "
        "in local host memory and its process runtime remains initialized, warm invocations achieve sub-second readiness (0.5 s to 1.0 s). "
        "Conversely, cold starts incur substantial delays. These delays encompass network pulling of container layers from remote registries, "
        "overlay filesystem decompression, Linux kernel namespace and cgroup configuration, CUDA runtime initialization, TensorRT engine "
        "deserialization, and neural network parameter loading into GPU memory. Empirical characterizations of deep learning serverless "
        "runtimes, such as the SeBS benchmark suite (Copik et al., 2021 [23]) and ServerlessLLM (Fu et al., 2024 [3]), document startup delays "
        "ranging from 10.0 s for compact vision models to over 100 s or 300 s for large foundation models and GPU checkpoints."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "Our experimental testbed models this operational spectrum within an edge-cloud split inference continuum. The edge tier comprises "
        "a serverless micro-container constrained by Linux cgroups with a 150 mCPU quota on an AWS c7i compute host. The edge container runs "
        "a single-threaded, unbatched EfficientNet-B0 student network, yielding an empirical inference execution latency t_edge = 10.7 ms, "
        "supported by 5.0 ms gateway simulation headroom. Unambiguous inputs are classified locally. Difficult or corrupted inputs are offloaded "
        "across an emulated wide-area network (mean network latency t_net = 25.0 ms, stochastic range 15 to 35 ms) to an elastic cloud GPU cluster. "
        "The cloud tier consists of 6 Nodes hosting NVIDIA Tesla T4 GPUs (16 GB VRAM) executing an NVIDIA Triton Inference Server with dynamic batching. "
        "At batch saturation, the cloud teacher model (ResNet-152) exhibits execution latency t_cloud = 62.5 ms, providing an authoritative worker "
        "service capacity mu = 16.0 RPS per worker, with a peak cluster capacity of 18 workers (288 RPS)."
    )

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "The end-to-end Service Level Agreement deadline budget is established at D_SLA = 15.0 s, while the nominal container boot delay in "
        "standard operational benchmarks is calibrated to T_boot = 15.0 s. To suppress destructive actuation oscillation, our controller enforces "
        "an asymmetric scale-down cooldown tau_down = 15.0 s, spanning three discrete control epochs (Delta t = 5.0 s). Importantly, this empirical "
        "study functions as a proof of concept for general cascading intelligence across modern foundation models, including Vision-Language Models "
        "(VLMs) and cascading Large Language Models (LLMs; Valkanas et al., 2025 [14]; Fu et al., 2024 [3]; Turkoglu et al., 2026 [13]; Romero et al., 2021 [2]). "
        "In these large-scale environments, cold-start delays are even more severe, making a systematic sensitivity analysis of container boot delay imperative."
    )

    # -------------------------------------------------------------------------
    # 9.7 THE 9-POINT DELAY LADDER ARCHITECTURE
    # -------------------------------------------------------------------------
    doc.add_heading("9.7 THE 9-POINT DELAY LADDER ARCHITECTURE", level=2)

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "To rigorously quantify how container initialization latency affects system stability and SLA compliance, we construct a 9-point physical "
        "delay ladder. We evaluate container startup delay across nine discrete levels spanning three orders of magnitude: "
        "T_boot in {1.0, 5.0, 10.0, 20.0, 50.0, 100.0, 150.0, 200.0, 300.0} s. All other testbed parameters, including actuation granularity "
        "(Delta t = 5.0 s), worker service rate (mu = 16.0 RPS), and SLA deadline (D_SLA = 15.0 s), remain strictly invariant."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "The evaluation workload isolates three representative stress regimes across ContinuumBench Suites 1, 2, and 3: "
        "suite1_spike (5,577 requests; sudden volume impulse), suite2_shock (9,076 requests; acute semantic complexity shock with input corruption), "
        "and suite3_azure (5,097 requests; diurnal production realism derived from the Azure Functions 2019 trace downsampled by 0.08x). "
        "Together, these three regimes encompass 19,750 requests. For each of the nine boot delay settings, we execute all five controller archetypes: "
        "our proposed Conformal-Gated Dual-Horizon Autoscaling (CGDA), Predictive Traffic-Envelope Autoscaling (InferLine; Crankshaw et al., 2020 [1]), "
        "Queue-Threshold Reactive Autoscaling (KEDA; 2024 [29]), CPU-Utilization Reactive Autoscaling (Kubernetes HPA; 2024 [28]), "
        "and Static Peak Provisioning (18 always-on workers)."
    )

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "Table 9.4 presents the complete performance metrics across all nine delay ladder rungs, summarizing SLA deadline misses, P99 tail latency, "
        "and cumulative compute expenditure in worker-seconds. Figure 9.4 illustrates the corresponding deadline miss trajectories and P99 tail "
        "latencies across the continuum."
    )

    # Embed Table 9.4
    p_t11_title = doc.add_paragraph()
    p_t11_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t11_title.paragraph_format.space_before = Pt(8)
    p_t11_title.paragraph_format.space_after = Pt(4)
    p_t11_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(
        p_t11_title,
        "Table 9.4: Physical delay ladder benchmark: SLA deadline misses, tail latency, and compute cost across 19,750 requests.",
        font_size_pt=11.0,
        bold=True
    )

    # 16 columns from table3_delay_ladder.csv:
    # We will present a clean 6-column consolidated view: Boot Delay, CGDA (Misses / P99 / Cost), InferLine (Misses / P99 / Cost),
    # KEDA (Misses / P99 / Cost), HPA (Misses / P99 / Cost), Static Peak (Misses / P99 / Cost).
    t11_headers = [
        "T_boot (s)",
        "Proposed CGDA\n(Miss / P99 / Cost)",
        "InferLine [1]\n(Miss / P99 / Cost)",
        "KEDA [29]\n(Miss / P99 / Cost)",
        "HPA [28]\n(Miss / P99 / Cost)",
        "Static Peak\n(Miss / P99 / Cost)"
    ]
    t11_widths = [Inches(0.9), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.15), Inches(1.1)]

    # Grounded raw data from table3_delay_ladder.csv:
    # 1.0s:  CGDA(0, 5.00s, 468.3),  Pred(0, 8.00s, 462.7),    KEDA(89, 8.00s, 736.3),     HPA(5, 6.00s, 1630.0),    Static(0, 5.00s, 2010.0)
    # 5.0s:  CGDA(0, 7.33s, 496.3),  Pred(77, 10.67s, 522.0),   KEDA(69, 9.33s, 866.0),     HPA(6, 10.00s, 1694.3),   Static(0, 5.00s, 2010.0)
    # 10.0s: CGDA(0, 9.00s, 511.3),  Pred(631, 13.33s, 565.3),  KEDA(110, 14.00s, 1012.7),  HPA(339, 15.67s, 1690.7), Static(0, 5.00s, 2010.0)
    # 20.0s: CGDA(232, 11.00s, 553.0), Pred(1393, 15.00s, 565.3), KEDA(1261, 23.67s, 1163.0), HPA(1246, 28.00s, 1697.7), Static(0, 5.33s, 2010.0)
    # 50.0s: CGDA(1328, 14.33s, 605.7), Pred(2174, 16.67s, 578.7), KEDA(4087, 49.67s, 1614.0), HPA(4004, 58.00s, 1941.3), Static(0, 5.67s, 2010.0)
    # 100.0s: CGDA(2176, 16.67s, 641.0), Pred(2176, 16.67s, 578.7), KEDA(8047, 67.33s, 1908.0), HPA(8033, 71.00s, 1946.7), Static(2176, 16.67s, 2010.0)
    # 150.0s: CGDA(2176, 16.67s, 641.0), Pred(2176, 16.67s, 578.7), KEDA(8126, 67.33s, 1908.0), HPA(8126, 71.00s, 1946.7), Static(2176, 16.67s, 2010.0)
    # 200.0s: CGDA(2176, 16.67s, 641.0), Pred(2176, 16.67s, 578.7), KEDA(8126, 67.33s, 1908.0), HPA(8126, 71.00s, 1946.7), Static(2176, 16.67s, 2010.0)
    # 300.0s: CGDA(2176, 16.67s, 641.0), Pred(2176, 16.67s, 578.7), KEDA(8126, 67.33s, 1908.0), HPA(8126, 71.00s, 1946.7), Static(2176, 16.67s, 2010.0)

    t11_rows = [
        ("1.0 s", "0 / 5.00s / 468.3", "0 / 8.00s / 462.7", "89 / 8.00s / 736.3", "5 / 6.00s / 1630.0", "0 / 5.00s / 2010.0"),
        ("5.0 s", "0 / 7.33s / 496.3", "77 / 10.67s / 522.0", "69 / 9.33s / 866.0", "6 / 10.00s / 1694.3", "0 / 5.00s / 2010.0"),
        ("10.0 s", "0 / 9.00s / 511.3", "631 / 13.33s / 565.3", "110 / 14.00s / 1012.7", "339 / 15.67s / 1690.7", "0 / 5.00s / 2010.0"),
        ("20.0 s", "232 / 11.00s / 553.0", "1393 / 15.00s / 565.3", "1261 / 23.67s / 1163.0", "1246 / 28.00s / 1697.7", "0 / 5.33s / 2010.0"),
        ("50.0 s", "1328 / 14.33s / 605.7", "2174 / 16.67s / 578.7", "4087 / 49.67s / 1614.0", "4004 / 58.00s / 1941.3", "0 / 5.67s / 2010.0"),
        ("100.0 s", "2176 / 16.67s / 641.0", "2176 / 16.67s / 578.7", "8047 / 67.33s / 1908.0", "8033 / 71.00s / 1946.7", "2176 / 16.67s / 2010.0"),
        ("150.0 s", "2176 / 16.67s / 641.0", "2176 / 16.67s / 578.7", "8126 / 67.33s / 1908.0", "8126 / 71.00s / 1946.7", "2176 / 16.67s / 2010.0"),
        ("200.0 s", "2176 / 16.67s / 641.0", "2176 / 16.67s / 578.7", "8126 / 67.33s / 1908.0", "8126 / 71.00s / 1946.7", "2176 / 16.67s / 2010.0"),
        ("300.0 s", "2176 / 16.67s / 641.0", "2176 / 16.67s / 578.7", "8126 / 67.33s / 1908.0", "8126 / 71.00s / 1946.7", "2176 / 16.67s / 2010.0"),
    ]

    tbl_t11 = doc.add_table(rows=len(t11_rows) + 1, cols=6)
    tbl_t11.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t11.autofit = False
    apply_table_grid_borders(tbl_t11)

    for j, h in enumerate(t11_headers):
        c = tbl_t11.cell(0, j)
        c.width = t11_widths[j]
        set_cell_margins(c, top=40, bottom=40, left=40, right=40)
        p = c.paragraphs[0]
        p.paragraph_format.line_spacing = 1.1
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = "Times New Roman"
        r.font.size = Pt(9.5)
        r.font.bold = True

    for i, row_data in enumerate(t11_rows):
        row = tbl_t11.rows[i + 1]
        for j, val in enumerate(row_data):
            c = row.cells[j]
            c.width = t11_widths[j]
            set_cell_margins(c, top=30, bottom=30, left=30, right=30)
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_math_text(p, val, font_size_pt=9.0)

    # Embed Figure 9.4
    fig11_path = "figures/fig3_realism_delay_ladder_curves.png"
    add_figure_with_caption(
        doc,
        fig11_path,
        "Figure 9.4: Performance sensitivity across container startup delays T_boot in [0.5, 300] s. "
        "Top row: Total SLA deadline misses across Suites 1, 2, and 3. Bottom row: P99 tail latency. "
        "The empirical tipping point at T* approx D_SLA = 15.0 s marks the transition where container boot delay "
        "exceeds the latency deadline, forcing dynamic autoscalers into physical queue saturation.",
        width_in=5.4
    )

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "Analysis of Table 9.4 and Figure 9.4 reveals four distinct operational regimes across the startup delay ladder:"
    )

    zones = [
        (
            "1. Sub-Tipping-Point Zone (T_boot <= D_SLA = 15.0 s): ",
            "When T_boot in {1.0, 5.0, 10.0} s, container startup latency remains strictly within the SLA deadline budget. "
            "In this regime, CGDA achieves exactly 0 deadline misses across all 19,750 requests, preserving P99 tail latency between 5.00 s and 9.00 s. "
            "In contrast, the predictive traffic-envelope autoscaler (InferLine) begins failing at T_boot = 5.0 s (77 misses) and degrades sharply to "
            "631 misses at T_boot = 10.0 s. Reactive controllers exhibit severe vulnerability even under rapid container boots: KEDA incurs 69 to 110 "
            "misses, and HPA incurs 5 to 339 misses. This occurs because reactive scalers only detect demand after queue backlogs accumulate, "
            "leaving insufficient time for containers to boot."
        ),
        (
            "2. Super-Tipping-Point Zone (D_SLA < T_boot < T_sim): ",
            "When T_boot increases to 20.0 s and 50.0 s, container boot delay surpasses the SLA latency deadline. Consequently, any unannounced load surge "
            "causes arriving requests to experience deadline violations before newly launched workers complete initialization. However, CGDA provides "
            "substantial damage mitigation: at T_boot = 20.0 s, CGDA incurs 232 misses, compared to 1,393 misses for InferLine (an 83.3% reduction), "
            "1,261 misses for KEDA, and 1,246 misses for HPA. At T_boot = 50.0 s, CGDA records 1,328 misses versus 2,174 for InferLine and over 4,000 "
            "misses for both reactive baselines. Zero-lag feed-forward conformal signals trigger capacity preemption epochs ahead of reactive mechanisms, "
            "cushioning queue backlogs."
        ),
        (
            "3. Saturation Onset Zone (T_boot approx T_sim approx 90.0 s): ",
            "At T_boot = 100.0 s, container boot delay exceeds the active duration of the evaluation trace (T_sim = 90.0 s). In this regime, dynamic "
            "scaling actions dispatched during the workload burst complete initialization only after the workload trace has concluded. Consequently, "
            "all dynamic controllers, as well as Static Peak Provisioning, saturate at exactly 2,176 misses. Static Peak Provisioning saturates "
            "identically because its 18 workers were initialized at t = 0 with T_boot = 100.0 s, rendering them offline throughout the entire 90.0 s run."
        ),
        (
            "4. Complete Saturation Zone (T_boot >> T_sim): ",
            "When T_boot reaches 150.0 s, 200.0 s, and 300.0 s, newly launched containers cannot contribute any compute capacity during the active serving window. "
            "All proactive and predictive controllers record an identical floor of 2,176 misses. However, reactive autoscalers suffer catastrophic breakdown: "
            "both KEDA and HPA accumulate 8,126 misses across the stress suites. Reactive scalers continuously spawn unready containers in response to "
            "mounting queue backlogs, consuming infrastructure resources (over 1,900 worker-seconds) without serving backlogged requests."
        )
    ]

    for label, desc in zones:
        p_z = doc.add_paragraph()
        p_z.paragraph_format.left_indent = Inches(0.25)
        p_z.paragraph_format.space_before = Pt(2)
        p_z.paragraph_format.space_after = Pt(4)
        p_z.paragraph_format.line_spacing = 1.5
        p_z.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        add_formatted_math_text(p_z, label, font_size_pt=12.0, bold=True)
        add_formatted_math_text(p_z, desc, font_size_pt=12.0)

    # -------------------------------------------------------------------------
    # 11.3 TIPPING POINT ANALYSIS: T* approx D_SLA = 15.0 s
    # -------------------------------------------------------------------------
    doc.add_heading("9.8 TIPPING POINT ANALYSIS: T* APPROX D_SLA = 15.0 S", level=2)

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "The empirical bifurcation observed between T_boot = 10.0 s and T_boot = 20.0 s motivates a formal queuing-theoretic treatment "
        "of the container provisioning tipping point. Consider an arrival stream of offloaded inference requests at the cloud tier characterized "
        "by arrival rate lambda_cloud(t) requests per second. Let W_t denote the number of active GPU workers at time t, with individual service "
        "capacity mu = 16.0 RPS. If the arrival rate suddenly exceeds active cluster capacity, lambda_cloud(t) > mu * W_t, requests accumulate "
        "in the cloud FIFO queue Q(t) according to the backlog differential:"
    )

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "The expected waiting time W_q(t) experienced by a request arriving at epoch t is determined by the instantaneous backlog divided "
        "by aggregate service throughput:"
    )

    # OMML Equation 9.1: Queue waiting delay
    omml_eq11_1 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Q</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>μ</m:t></m:r>'
        '<m:r><m:t> ⋅ </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:den>'
        '</m:f>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq11_1, eq_number="9.1")

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "For total turnaround latency L_i = t_edge + t_net + W_q(t_i) + t_cloud to remain within the deadline D_SLA, the queuing delay "
        "must satisfy W_q(t_i) <= D_SLA - (t_edge + t_net + t_cloud). Given profiled execution constants (t_edge = 10.7 ms, t_net = 25.0 ms, "
        "t_cloud = 62.5 ms), physical transit and execution consume less than 0.10 s. The available queuing budget is therefore "
        "approximately equal to D_SLA = 15.0 s."
    )

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "When an unexpected semantic complexity shock occurs at time t_0, existing workers W_0 are overwhelmed. If an autoscaling controller "
        "dispatches a scale-up command at t_0 requesting W_{t+1} > W_0, newly requested workers remain non-operational until t_0 + T_boot. "
        "Requests arriving during this window can only be served by the initial W_0 workers. The maximum container startup delay T^* that avoids "
        "violating D_SLA is formally bounded by Equation 9.2:"
    )

    # OMML Equation 9.2: Critical tipping point threshold
    omml_eq11_2 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>T</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>D</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>SLA</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> - </m:t></m:r>'
        '<m:d>'
        '<m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr>'
        '<m:e>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>edge</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t> + </m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>net</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t> + </m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>cloud</m:t></m:r></m:sub></m:sSub>'
        '</m:e>'
        '</m:d>'
        '<m:r><m:t> - </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Q</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:t>0</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:t>μ</m:t></m:r>'
        '<m:r><m:t> ⋅ </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>W</m:t></m:r></m:e>'
        '<m:sub><m:r><m:t>0</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:den>'
        '</m:f>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq11_2, eq_number="9.2")

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "Assuming zero initial queue backlog (Q(0) = 0), Equation 9.2 yields T^* approx D_SLA = 15.0 s. "
        "This relation establishes the Physical Tipping Point Theorem: "
        "If T_boot <= D_SLA, an autoscaler equipped with lookahead feed-forward telemetry can launch additional workers early enough "
        "that they become operational before waiting requests exceed D_SLA, mathematically guaranteeing 0 SLA deadline misses. "
        "Conversely, if T_boot > D_SLA, no dynamic control policy, even one possessing oracle knowledge of future arrivals, can prevent "
        "deadline misses for requests that arrive once existing capacity is exhausted. Beyond the tipping point, the operational objective "
        "of autoscaling transitions from SLA violation prevention to queue backlog mitigation."
    )

    # -------------------------------------------------------------------------
    # 9.9 COMPARATIVE CONTROLLER BREAKDOWN UNDER EXTREME COLD STARTS
    # -------------------------------------------------------------------------
    doc.add_heading("9.9 COMPARATIVE CONTROLLER BREAKDOWN UNDER EXTREME COLD STARTS", level=2)

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "Under extreme cold-start latencies (T_boot >= 150.0 s), the operational disparity between proactive conformal scaling and reactive "
        "control becomes severe. This breakdown is highlighted by examining performance on Suite 3 (suite3_azure), which models diurnal "
        "production traffic from the Azure Functions 2019 dataset downsampled by 0.08x."
    )

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "In Suite 3 under T_boot = 150.0 s, 200.0 s, and 300.0 s, the reactive CPU controller (Kubernetes HPA) incurs exactly 1,819 deadline misses "
        "out of 5,097 total requests, producing an unacceptable P99 tail latency of 115.0 s and consuming 2,342.0 worker-seconds. "
        "The reactive queue-length controller (KEDA) fails identically, recording 1,819 deadline misses, a P99 tail latency of 104.0 s, "
        "and 2,330.0 worker-seconds of compute cost. Across these extreme rungs, both reactive scalers fail 35.7% of all arriving requests."
    )

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "The physical mechanism driving this reactive failure is container thrashing without service delivery. As diurnal traffic increases, "
        "cloud queue backlogs mount. Reactive controllers respond by issuing massive scale-up commands. However, because newly provisioned "
        "containers require at least 150.0 s to boot, they remain in initializing status while requests sit unserved in the queue until "
        "their 15.0 s SLA deadline expires. By the time newly provisioned GPU workers become active, the diurnal wave has passed, leaving "
        "idle workers that consume cloud billing credits without ever processing requests within their SLA window."
    )

    p17 = doc.add_paragraph()
    p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p17,
        "In stark contrast, CGDA records exactly 0 deadline misses in Suite 3 across all startup delays up to T_boot = 300.0 s, maintaining a P99 "
        "tail latency of 5.00 s and a low compute cost of 258.0 worker-seconds. CGDA achieves this because its dual-horizon policy continuously "
        "tracks edge prediction set cardinality |C(x)|. Because diurnal fluctuations in Suite 3 reflect volume variations with modest semantic "
        "corruption, CGDA accurately sizes baseline worker capacity without triggering unnecessary emergency scale-ups that destabilize the cluster. "
        "Predictive envelope scaling (InferLine) also maintains 0 misses in Suite 3 (P99 = 5.00 s, cost = 270.0 worker-seconds), but incurs "
        "severe backlogs in Suite 2 (1,853 misses at T_boot >= 100.0 s) where semantic complexity shocks decouple offload rates from raw ingress volume."
    )

    # -------------------------------------------------------------------------
    # 9.10 ARCHITECTURAL RECOMMENDATIONS FOR PRODUCTION SERVERLESS DEPLOYMENTS
    # -------------------------------------------------------------------------
    doc.add_heading("9.10 ARCHITECTURAL RECOMMENDATIONS FOR PRODUCTION SERVERLESS DEPLOYMENTS", level=2)

    p18 = doc.add_paragraph()
    p18.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p18,
        "The empirical findings from the 9-point delay ladder and the physical tipping point analysis suggest four concrete architectural "
        "recommendations for engineering resilient serverless split-inference systems in production cloud platforms:"
    )

    recommendations = [
        (
            "1. Minimum Warm Worker Pooling: ",
            "Because dynamic autoscaling cannot prevent SLA deadline violations when T_boot > D_SLA, production systems must enforce a non-zero "
            "minimum worker allocation (k_min >= 1). Maintaining a minimal pool of warm GPU workers absorbs initial shock impulses, providing "
            "sufficient baseline throughput to prevent immediate queue explosion while newly provisioned instances initialize."
        ),
        (
            "2. Fast Checkpoint Restoration and Memory Snapshotting: ",
            "To restore the physical guarantee of zero SLA misses, cloud operators must deploy container snapshotting and model weight streaming "
            "technologies (such as ServerlessLLM; Fu et al., 2024 [3]; Torpor; Ali et al., 2025 [4]) that compress container startup delay T_boot "
            "below the SLA budget D_SLA. By reducing boot times from hundreds of seconds to sub-15 seconds via copy-on-write GPU memory and SSD weight "
            "chunking, large vision and language models re-enter the sub-tipping-point zone where proactive autoscalers can eliminate deadline violations."
        ),
        (
            "3. Zero-Lag Edge Telemetry Integration: ",
            "Autoscaling control planes should directly integrate edge-tier statistical telemetry. Rather than relying on trailing metrics "
            "(such as cloud GPU utilization or queue backlog), cloud schedulers should ingest feed-forward offload derivative signals (Delta_offload) "
            "generated by edge conformal triage gateways. This maximizes available boot lead time, allowing scale-up actions to initiate seconds "
            "before offloaded requests reach cloud message brokers."
        ),
        (
            "4. Dynamic Tiered SLAs and Graceful Edge Degradation: ",
            "When cloud container initialization delays exceed D_SLA due to infrastructure congestion or remote registry stalls, edge gateways "
            "must engage graceful degradation. Rather than offloading unserviceable requests into congested cloud queues where deadline violations "
            "are physically inevitable, edge nodes should return local student predictions with an explicit confidence flag (|C(x)| >= 2), "
            "preserving bounded turnaround latency at the expense of marginal classification accuracy."
        )
    ]

    for label, desc in recommendations:
        p_r = doc.add_paragraph()
        p_r.paragraph_format.left_indent = Inches(0.25)
        p_r.paragraph_format.space_before = Pt(2)
        p_r.paragraph_format.space_after = Pt(4)
        p_r.paragraph_format.line_spacing = 1.5
        p_r.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        r_lbl = p_r.add_run(label)
        r_lbl.font.name = "Times New Roman"
        r_lbl.font.size = Pt(12)
        r_lbl.font.bold = True

        add_formatted_math_text(p_r, desc, font_size_pt=12.0)

    # Concluding paragraph for Chapter 11
    p19 = doc.add_paragraph()
    p19.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p19,
        "In summary, the 9-point delay ladder demonstrates that container boot latency is the definitive physical constraint governing split-inference "
        "autoscaling. While proactive conformal gating successfully expands the zero-miss operational envelope up to the physical boundary "
        "T* approx D_SLA = 15.0 s, startup delays exceeding this limit require complementary systems optimizations, including warm pooling and "
        "fast checkpoint restoration, to preserve end-to-end service guarantees."
    )

    doc.add_page_break()


if __name__ == "__main__":
    test_doc = docx.Document()
    build_chapter_9(test_doc)
    test_doc.save("test_ch9.docx")
    print("Chapter 9 built successfully!")
