#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch03_workload.py: Chapter 3 Builder for BCE497J Project Report

Drafts Chapter 3: Workload Traces and Continuum Benchmarks in complete academic depth adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations.
- High-resolution embedding of Figure 3.1 and Figure 3.2.
- Comprehensive 13-regime specification Table 3.1.
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


def build_chapter_3(doc: docx.Document):
    """Constructs the full academic content for Chapter 3: Workload Traces and Continuum Benchmarks."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 3  WORKLOAD TRACES AND CONTINUUM BENCHMARKS", level=1)

    # -------------------------------------------------------------------------
    # 3.1 PRODUCTION TRACE CHARACTERISTICS: MICROSOFT AZURE FUNCTIONS 2019
    # -------------------------------------------------------------------------
    doc.add_heading("3.1 PRODUCTION TRACE CHARACTERISTICS: MICROSOFT AZURE FUNCTIONS 2019", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "Evaluating elastic autoscaling policies in edge-cloud continuum environments requires empirical workloads that capture "
        "the burstiness, non-stationarity, and diurnal variance characteristic of production cloud deployments. Synthetic benchmarks often "
        "rely on idealized distributions (such as stationary Poisson processes or regular sinusoidal waves) that fail to reproduce the "
        "stochastic micro-bursts observed in commercial serverless platforms. To provide a realistic empirical foundation, our workload "
        "generator incorporates real-world invocation traces from the Microsoft Azure Functions 2019 dataset (Shahrad et al., 2020 [15])."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "The Azure Functions 2019 dataset comprises a 14-day record capturing billions of function invocations across tens of thousands of "
        "serverless applications executing in Microsoft Azure data centers. Production analysis reveals that 82% of serverless functions are "
        "invoked fewer than once per minute on average, while a small subset of high-throughput functions generates immense invocation volumes "
        "exhibiting sharp diurnal cycles and sudden, unannounced spikes. We extract a representative 120-minute diurnal window exhibiting a "
        "morning ramp, midday plateau, and afternoon decay, matching the standard benchmark window used in continuum literature."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "Because raw production traces in hyperscale cloud environments aggregate hundreds of thousands of concurrent users, direct replay "
        "would vastly exceed the capacity of a controlled experimental edge-cloud cluster. We apply a calibrated downsampling factor of "
        "r = 0.08x to map the raw invocation trace (averaging approximately 200 requests per second) into our testbed operating range "
        "(averaging approximately 16 requests per second). Crucially, this downsampling factor aligns nominal mean throughput with the physical "
        "saturation service capacity of a single cloud GPU worker (mu = 16.0 RPS per worker, derived from physical NVIDIA Tesla T4 GPU profiling). "
        "Downsampling is performed using a Poisson sampling thinning process that preserves the empirical coefficient of variation, autocorrelation "
        "structure, and burstiness of the original trace without introducing synthetic smoothing artifacts."
    )

    # Embed Figure 3.1
    fig31_path = "figures/fig_workload_characterization.png"
    add_figure_with_caption(
        doc,
        fig31_path,
        "Figure 3.1: Workload trace characterization and empirical arrival dynamics from the Microsoft Azure Functions 2019 dataset downsampled by 0.08x.",
        width_in=5.4
    )

    # -------------------------------------------------------------------------
    # 3.2 CONTINUUMBENCH: BENCHMARK SUITE DESIGN AND TAXONOMY
    # -------------------------------------------------------------------------
    doc.add_heading("3.2 CONTINUUMBENCH: BENCHMARK SUITE DESIGN AND TAXONOMY", level=2)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "While production traces capture aggregate temporal dynamics, they do not systematically isolate specific operational failure modes, "
        "such as cold starts, sharp load shedding, or sudden drops in classification confidence. To provide rigorous, reproducible evaluation, "
        "we construct the ContinuumBench suite, building upon the ECLYPSE continuum simulation framework (Massa et al., 2026 [14]) and the "
        "ContinuumBench benchmark methodology (Li et al., 2026 [16])."
    )

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "The ContinuumBench architecture decouples total ingress arrival rate lambda(t) from the semantic complexity of the arriving queries. "
        "In traditional cloud workloads, request volume serves as a reliable proxy for compute demand. In a two-tier continuum with local triage, "
        "however, total request volume is partitioned at the edge gateway into two distinct streams:"
    )

    p6 = doc.add_paragraph()
    p6.paragraph_format.left_indent = Inches(0.25)
    p6.paragraph_format.space_before = Pt(2)
    p6.paragraph_format.space_after = Pt(2)
    add_formatted_math_text(
        p6,
        "1. Local Edge Traffic: lambda_edge(t) = p_fast(t) * lambda(t), representing queries resolved locally by the serverless student model "
        "(EfficientNet-B0 under a 150 mCPU container quota on AWS c7i host, t_edge = 10.7 ms), terminating at the edge with zero cloud latency."
    )

    p7 = doc.add_paragraph()
    p7.paragraph_format.left_indent = Inches(0.25)
    p7.paragraph_format.space_before = Pt(2)
    p7.paragraph_format.space_after = Pt(4)
    add_formatted_math_text(
        p7,
        "2. Cloud Offload Traffic: lambda_cloud(t) = (1 - p_fast(t)) * lambda(t), representing difficult or corrupted queries forwarded "
        "across the WAN (mean RTT t_net = 25.0 ms) to the elastic NVIDIA Tesla T4 cloud GPU cluster."
    )

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "To systematically challenge autoscaling policies across this decoupled continuum, ContinuumBench organizes evaluations into three "
        "complementary suites: Suite 1 evaluates synthetic rate dynamics under stationary semantic complexity; Suite 2 evaluates semantic "
        "complexity shocks where input clarity shifts independently of volume; and Suite 3 evaluates long-horizon production trace replay."
    )

    # -------------------------------------------------------------------------
    # 3.3 THE 13 EVALUATION REGIMES
    # -------------------------------------------------------------------------
    doc.add_heading("3.3 THE 13 EVALUATION REGIMES", level=2)

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "ContinuumBench formalizes 13 distinct evaluation regimes across the three suites. Table 3.1 details the operational parameters, "
        "arrival rate functions, semantic fast-path fractions, and primary stress dimensions for each regime."
    )

    # Table 3.1: The 13 Evaluation Regimes
    p_t3_title = doc.add_paragraph()
    p_t3_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3_title.paragraph_format.space_before = Pt(8)
    p_t3_title.paragraph_format.space_after = Pt(4)
    p_t3_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(
        p_t3_title,
        "Table 3.1: Systematic specification of the 13 ContinuumBench evaluation regimes across volume dynamics, semantic shifts, and production traces.",
        font_size_pt=11.0,
        bold=True
    )

    t3_headers = [
        "Suite",
        "Regime Identifier",
        "Workload Pattern",
        "Ingress Profile lambda(t)",
        "Fast-Path p_fast(t)",
        "Primary Operational Stress"
    ]
    t3_widths = [
        Inches(0.6),
        Inches(1.3),
        Inches(1.2),
        Inches(1.1),
        Inches(0.9),
        Inches(1.5)
    ]

    t3_rows = [
        (
            "1",
            "suite1_flat",
            "Constant low-load",
            "Stationary 60 QPS",
            "p_fast = 0.50 (flat)",
            "Baseline quiescence; verifies zero unnecessary over-provisioning."
        ),
        (
            "1",
            "suite1_spike",
            "Instantaneous impulse",
            "5x surge: 20 -> 100 QPS",
            "p_fast = 0.50 (flat)",
            "Peak provisioning speed; tests rapid queue build-up mitigation."
        ),
        (
            "1",
            "suite1_burst",
            "Sustained oscillations",
            "Cyclic 40-200 QPS",
            "p_fast = 0.50 (flat)",
            "Queue stability; tests dampening against cyclic volume waves."
        ),
        (
            "1",
            "suite1_ramp",
            "Linearly increasing load",
            "Linear 20 -> 160 QPS",
            "p_fast = 0.50 (flat)",
            "Ramp tracking; tests steady-state tracking without trailing error."
        ),
        (
            "1",
            "suite1_zero_begin",
            "Cold start from idle",
            "Step 0 -> 120 QPS",
            "p_fast = 0.50 (flat)",
            "Container boot delay; tests cold-start recovery under heavy load."
        ),
        (
            "1",
            "suite1_zero_terminal",
            "Graceful drain to zero",
            "Step 120 -> 0 QPS",
            "p_fast = 0.50 (flat)",
            "Scale-down hysteresis; verifies avoidance of rapid container thrashing."
        ),
        (
            "2",
            "suite2_shock",
            "Sudden complexity shift",
            "Stationary 60 QPS",
            "Collapse: 0.70 -> 0.20",
            "Semantic blindness; tests offload surge detection at constant volume."
        ),
        (
            "2",
            "suite2_recovery",
            "Complexity shock & return",
            "Stationary 60 QPS",
            "0.70 -> 0.20 -> 0.70",
            "Overshoot control; verifies rapid capacity release upon recovery."
        ),
        (
            "2",
            "suite2_compound_stress",
            "Concurrent stress shock",
            "Surge: 40 -> 100 QPS",
            "Collapse: 0.70 -> 0.20",
            "Worst-case compound stress; simultaneous volume and complexity surge."
        ),
        (
            "2",
            "suite2_compound_relief",
            "Concurrent load relief",
            "Drop: 100 -> 40 QPS",
            "Recovery: 0.20 -> 0.70",
            "Under-provisioning risk; tests stability during compound deflation."
        ),
        (
            "2",
            "suite2_decoupled_opposing",
            "Opposing decoupled shifts",
            "Surge: 40 -> 120 QPS",
            "Increase: 0.40 -> 0.80",
            "Decoupled dynamics; tests prevention of false scaling on volume alone."
        ),
        (
            "2",
            "suite2_storm",
            "Multi-axis volatility storm",
            "Perturbed 30-150 QPS",
            "Chaotic 0.15-0.85",
            "Extreme volatility; tests stability under high-variance dual noise."
        ),
        (
            "3",
            "suite3_azure",
            "Production trace replay",
            "Diurnal downsampled 0.08x",
            "Correlated 0.35-0.65",
            "Production realism; validates long-horizon efficiency and zero misses."
        )
    ]

    tbl_t3 = doc.add_table(rows=len(t3_rows) + 1, cols=6)
    tbl_t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_t3.autofit = False
    apply_table_grid_borders(tbl_t3)

    for j, h in enumerate(t3_headers):
        c = tbl_t3.cell(0, j)
        c.width = t3_widths[j]
        set_cell_margins(c, top=40, bottom=40, left=35, right=35)
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
            add_formatted_math_text(p, val, font_size_pt=8.5)

    p10 = doc.add_paragraph()
    p10.paragraph_format.space_before = Pt(8)
    p10.paragraph_format.space_after = Pt(6)
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "Figure 3.2 presents the complete empirical workload dynamics across all 13 ContinuumBench regimes, visualizing how input volume "
        "lambda(t) and edge triage acceptance p_fast(t) evolve under synthetic rate spikes, semantic complexity shocks, and production trace replay."
    )

    # Embed Figure 3.2
    fig32_path = "figures/fig_all_13_regimes_workload.png"
    add_figure_with_caption(
        doc,
        fig32_path,
        "Figure 3.2: Complete workload profiles across all 13 ContinuumBench evaluation regimes, illustrating decoupled ingress arrival rates lambda(t) and local triage fractions p_fast(t).",
        width_in=5.4
    )

    # -------------------------------------------------------------------------
    # 3.4 MODELING SEMANTIC COMPLEXITY SHOCKS
    # -------------------------------------------------------------------------
    doc.add_heading("3.4 MODELING SEMANTIC COMPLEXITY SHOCKS", level=2)

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "In a split-inference continuum, incoming requests are evaluated by the edge triage function using Regularized Adaptive Prediction Sets "
        "(RAPS; Angelopoulos et al., 2021 [7]). Let N_total(t) denote the total number of IoT image requests arriving at the edge gateway during "
        "control epoch t (where epoch duration is Delta t = 5.0 s), and let N_local(t) denote the subset of requests resolved locally with "
        "singleton prediction sets (|C(x)| = 1). The local acceptance fraction is defined as:"
    )

    # OMML Equation 3.1: Local Triage Acceptance Fraction
    omml_eq31 = (
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
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>N</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>local</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>N</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>total</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:den>'
        '</m:f>'
        '<m:r><m:t> ∈ [0, 1]</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq31, eq_number="3.1")

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "The effective arrival rate directed toward the cloud GPU acceleration cluster is consequently governed by the unabsorbed fraction:"
    )

    # OMML Equation 3.2: Cloud Arrival Demand
    omml_eq32 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>λ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>cloud</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = (1 - </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>fast</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)) ⋅ </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>λ</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq32, eq_number="3.2")

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "We formalize the discrete velocity of the edge acceptance fraction as the difference between consecutive control epochs:"
    )

    # OMML Equation 3.3: Discrete Complexity Velocity
    omml_eq33 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:t>Δ</m:t></m:r>'
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
    add_omml_equation(doc, omml_eq33, eq_number="3.3")

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "A semantic complexity shock occurs when input corruptions degrade classification certainty, driving p_fast(t) down sharply. "
        "For instance, in regime suite2_shock, the fast-path fraction collapses from nominal p_fast = 0.70 to p_fast = 0.20 while aggregate "
        "ingress arrival rate remains constant at lambda(t) = 60 QPS. Under nominal conditions, cloud arrival demand is only "
        "(1 - 0.70) * 60 = 18 QPS, requiring approximately 2 active cloud workers (since mu = 16.0 RPS per worker). "
        "Following the shock, cloud demand surges to (1 - 0.20) * 60 = 48 QPS, demanding at least 3 to 4 active workers. "
        "Because ingress volume lambda(t) remains completely flat, reactive CPU scalers (HPA) and predictive rate scalers (InferLine) "
        "fail to detect any impending change. Our controller detects this condition via the shock threshold:"
    )

    # OMML Equation 3.4: Shock Condition
    omml_eq34 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:t>Δ</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) &lt; -</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>θ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>shock</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq34, eq_number="3.4")

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "where theta_shock = 0.15 denotes the calibrated preemption shock threshold. This condition flags that edge triage absorption has dropped "
        "by more than 15 percentage points in a single epoch, triggering immediate capacity reservation before the surge reaches cloud queues."
    )

    # -------------------------------------------------------------------------
    # 3.5 WORKLOAD VALIDATION AND REPRODUCIBILITY PROTOCOL
    # -------------------------------------------------------------------------
    doc.add_heading("3.5 WORKLOAD VALIDATION AND REPRODUCIBILITY PROTOCOL", level=2)

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "To guarantee mathematical rigor and eliminate evaluation artifacts, ContinuumBench enforces a strict reproducibility protocol: "
        "(1) Multi-Seed Pseudo-Random Control: All 13 regimes are evaluated across 20 independent, matched pseudo-random seeds (seeds 1 to 20). "
        "Each random seed governs both Poisson arrival timestamps and image sampling indices, ensuring identical request sequences across "
        "all five evaluated controller archetypes. Across 20 seeds, 13 regimes, and 5 controllers, the complete benchmark suite spans exactly "
        "1,300 full controller executions (260 matched evaluation runs per controller). "
        "(2) Empirical Vision Data Binding: Every synthetic and trace-driven request is bound to an authentic image sampled uniformly from the "
        "Tiny ImageNet-C validation set (Hendrycks & Dietterich, 2019 [11]). No synthetic classification confidence scores or fabricated latency "
        "values are injected at any point. "
        "(3) Open Configuration Manifests: All workload parameters, including arrival rates, corruption injection epochs, and container startup delays, "
        "are specified in version-controlled YAML manifests within configs/suites/. The evaluation harness executes without hardcoded controller overrides, "
        "enabling independent verification directly within the workspace."
    )

    doc.add_page_break()
