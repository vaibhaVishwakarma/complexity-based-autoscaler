#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch11_delay_ladder.py: Chapter 11 Builder for BCE497J Project Report

Drafts Chapter 11: Container Startup Sensitivity and Delay Ladder in complete academic depth:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations.
- Embedding Table 11.1 (authoritative delay ladder metrics) and Figure 11.1 (fig3_realism_delay_ladder_curves.png).
- Strict adherence to grounded testbed hardware and parameter provenance.
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


def build_chapter_11(doc: docx.Document):
    """Constructs the full academic content for Chapter 11: Container Startup Sensitivity and Delay Ladder."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 11  CONTAINER STARTUP SENSITIVITY AND DELAY LADDER", level=1)

    # -------------------------------------------------------------------------
    # 11.1 THE REALITY OF CONTAINER STARTUP LATENCY IN SERVERLESS CLOUD
    # -------------------------------------------------------------------------
    doc.add_heading("11.1 THE REALITY OF CONTAINER STARTUP LATENCY IN SERVERLESS CLOUD", level=2)

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
    # 11.2 THE 9-POINT DELAY LADDER ARCHITECTURE
    # -------------------------------------------------------------------------
    doc.add_heading("11.2 THE 9-POINT DELAY LADDER ARCHITECTURE", level=2)

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
        "Table 11.1 presents the complete performance metrics across all nine delay ladder rungs, summarizing SLA deadline misses, P99 tail latency, "
        "and cumulative compute expenditure in worker-seconds. Figure 11.1 illustrates the corresponding deadline miss trajectories and P99 tail "
        "latencies across the continuum."
    )

    # Embed Table 11.1
    p_t11_title = doc.add_paragraph()
    p_t11_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t11_title.paragraph_format.space_before = Pt(8)
    p_t11_title.paragraph_format.space_after = Pt(4)
    p_t11_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(
        p_t11_title,
        "Table 11.1: Physical delay ladder benchmark: SLA deadline misses, tail latency, and compute cost across 19,750 requests.",
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

    # Embed Figure 11.1
    fig11_path = "figures/fig3_realism_delay_ladder_curves.png"
    add_figure_with_caption(
        doc,
        fig11_path,
        "Figure 11.1: Performance sensitivity across container startup delays T_boot in [0.5, 300] s. "
        "Top row: Total SLA deadline misses across Suites 1, 2, and 3. Bottom row: P99 tail latency. "
        "The empirical tipping point at T* approx D_SLA = 15.0 s marks the transition where container boot delay "
        "exceeds the latency deadline, forcing dynamic autoscalers into physical queue saturation.",
        width_in=5.4
    )

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "Analysis of Table 11.1 and Figure 11.1 reveals four distinct operational regimes across the startup delay ladder:"
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
    doc.add_heading("11.3 TIPPING POINT ANALYSIS: T* APPROX D_SLA = 15.0 S", level=2)

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

    # OMML Equation 11.1: Queue waiting delay
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
    add_omml_equation(doc, omml_eq11_1, eq_number="11.1")

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
        "Requests arriving during this window can only be served by the initial W_0 workers. The maximum container startup delay T* that avoids "
        "violating D_SLA is formally bounded by Equation 11.2:"
    )

    # OMML Equation 11.2: Critical tipping point threshold
    omml_eq11_2 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>T</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> = </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>D</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>SLA</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> - (</m:t></m:r>'
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
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>cloud</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>) - </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Q</m:t></m:r>'
        '<m:r><m:t>(0)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>μ</m:t></m:r>'
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
    add_omml_equation(doc, omml_eq11_2, eq_number="11.2")

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "Assuming zero initial queue backlog (Q(0) = 0), Equation 11.2 yields T* approx D_SLA = 15.0 s. "
        "This relation establishes the Physical Tipping Point Theorem: "
        "If T_boot <= D_SLA, an autoscaler equipped with lookahead feed-forward telemetry can launch additional workers early enough "
        "that they become operational before waiting requests exceed D_SLA, mathematically guaranteeing 0 SLA deadline misses. "
        "Conversely, if T_boot > D_SLA, no dynamic control policy, even one possessing oracle knowledge of future arrivals, can prevent "
        "deadline misses for requests that arrive once existing capacity is exhausted. Beyond the tipping point, the operational objective "
        "of autoscaling transitions from SLA violation prevention to queue backlog mitigation."
    )

    # -------------------------------------------------------------------------
    # 11.4 COMPARATIVE CONTROLLER BREAKDOWN UNDER EXTREME COLD STARTS
    # -------------------------------------------------------------------------
    doc.add_heading("11.4 COMPARATIVE CONTROLLER BREAKDOWN UNDER EXTREME COLD STARTS", level=2)

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
    # 11.5 ARCHITECTURAL RECOMMENDATIONS FOR PRODUCTION SERVERLESS DEPLOYMENTS
    # -------------------------------------------------------------------------
    doc.add_heading("11.5 ARCHITECTURAL RECOMMENDATIONS FOR PRODUCTION SERVERLESS DEPLOYMENTS", level=2)

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
    build_chapter_11(test_doc)
    test_doc.save("test_ch11.docx")
    print("Chapter 11 built successfully!")
