#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch06_openevolve.py: Chapter 6 Builder for BCE497J Project Report

Drafts Chapter 6: Offline AST Policy Synthesis via OpenEvolve adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations via scripts.omml_builder.
- Publication-grade Table 6.1 and Table 6.2 embedding.
- Strict grounding in src/continuum_ext/evolution/, configs/evolution/, and output/champion_policy_v7_smooth.py.
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


def build_chapter_6(doc: docx.Document):
    """Constructs the full academic content for Chapter 6: Offline AST Policy Synthesis via OpenEvolve."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 6  OFFLINE AST POLICY SYNTHESIS VIA OPENEVOLVE", level=1)

    # =========================================================================
    # 6.1 MOTIVATION FOR SYMBOLIC PROGRAM SYNTHESIS IN ELASTIC CONTROL
    # =========================================================================
    doc.add_heading("6.1 MOTIVATION FOR SYMBOLIC PROGRAM SYNTHESIS IN ELASTIC CONTROL", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "Designing autoscaling controllers for multi-tier edge-cloud serving pipelines presents severe theoretical and practical challenges. "
        "In split computing environments, computational demand is governed by non-linear interactions among arriving request rates, edge triage "
        "acceptance fractions, and wide-area queuing dynamics. When cloud worker provisioning involves a non-zero container initialization delay "
        "(such as the nominal baseline T_boot = 15.0 s) that directly matches the end-to-end Service Level Agreement latency budget (D_SLA = 15.0 s), "
        "the temporal margin for reactive scaling vanishes entirely. Handcrafted heuristic controllers, such as classical proportional-integral-derivative "
        "(PID) loops or threshold-based rules (e.g., Kubernetes Horizontal Pod Autoscaler), suffer from rigid parameter coupling. Tuning thresholds to "
        "respond aggressively to load spikes inevitably induces destructive capacity oscillations and worker thrashing during load recesses, whereas "
        "conservative tuning leads to queue overflow and severe SLA deadline violations."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "Deep Reinforcement Learning (DRL) has been proposed to overcome heuristic limitations by learning continuous control policies in complex "
        "state spaces. However, DRL exhibits critical vulnerabilities that prevent reliable deployment in production cloud infrastructure. Neural "
        "policies operate as opaque black boxes whose decision logic cannot be formally audited, verified, or bounded by system operators. "
        "Furthermore, DRL agents suffer from reward brittleness and generalize poorly when confronted with out-of-distribution workload dynamics, "
        "often taking catastrophic actions in unseen corner regimes. Finally, evaluating a deep neural policy at every control epoch introduces "
        "non-trivial memory footprints and computational overhead within the control loop itself."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "To resolve the conflict between adaptability and safety, this research adopts the paradigm of symbolic program synthesis via OpenEvolve "
        "(OpenEvolve, 2024). OpenEvolve navigates a constrained Abstract Syntax Tree (AST) grammar to synthesize explicit, human-readable Python "
        "control programs. Rather than learning continuous weights inside an uninterpretable neural network, OpenEvolve searches for algebraic and "
        "logical compositions over physical telemetric state variables. The synthesized policies execute in O(1) time per control epoch, require zero "
        "matrix operations or runtime retraining, and can be fully inspected, formally bounded, and statically checked by site reliability engineers "
        "prior to production deployment."
    )

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "The underlying experimental system is grounded in a two-tier edge-cloud architecture. The edge tier operates as a serverless micro-container "
        "constrained by Linux cgroups to a 150 mCPU quota on an AWS c7i compute host, running an unbatched EfficientNet-B0 student model in t_edge = 10.7 ms "
        "(with 5.0 ms gateway simulation headroom). The cloud tier consists of 6 nodes equipped with NVIDIA Tesla T4 GPUs (16 GB) running NVIDIA Triton "
        "Inference Server with dynamic batching. Each cloud worker provides an empirical service capacity of mu = 16.0 RPS at batch saturation "
        "(t_cloud = 62.5 ms), yielding a cluster peak capacity of 18 workers (288 RPS). Incoming requests consist of an image ingress stream from "
        "IoT devices drawn from the Tiny ImageNet-C benchmark and the downsampled Microsoft Azure Functions 2019 trace (0.08x scaling). "
        "Crucially, this architecture serves as an empirical proof of concept for general cascading intelligence across modern foundation models, "
        "including Vision-Language Models (VLMs) and cascading Large Language Models (LLMs; Chen et al., 2023 [5]; Patel et al., 2024 [27]; "
        "Romero et al., 2021 [21]; Sheng et al., 2024)."
    )

    # =========================================================================
    # 6.2 DOMAIN-SPECIFIC AST GRAMMAR DESIGN
    # =========================================================================
    doc.add_heading("6.2 DOMAIN-SPECIFIC AST GRAMMAR DESIGN", level=2)

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "Unconstrained code synthesis produces brittle, uninterpretable programs prone to syntax crashes and infinite loops. To ensure physical "
        "causality and search efficiency, we formulate a strongly typed domain-specific grammar (src/continuum_ext/evolution/grammar_v7.py). "
        "The search space is strictly bounded by an immutable telemetric observation contract, defined by the TelemetricState data structure "
        "(output/champion_policy_v7_smooth.py). Every attribute delivered to the policy function compute_target_workers(state) is causally observable "
        "at epoch boundary t with zero lookahead or oracle leakage."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "The telemetric observation contract partitions system metrics into four physical tiers: "
        "(1) Edge Semantic Triage Telemetry: the empirical fast-path fraction p_fast, the 3-epoch complexity velocity dp_fast/dt, and the mean "
        "RAPS prediction set size E[|C(x)|] calibrated at alpha = 0.10 and q_hat = 0.79914; "
        "(2) Continuum Traffic Dynamics: arriving IoT sensor request rate lambda(t), ingress acceleration d^2lambda/dt^2, and offered cloud demand "
        "lambda_cloud(t) = lambda(t) * (1 - p_fast); "
        "(3) Cluster Queue Backlog and Aging: current unserviced backlog Q_t waiting at the cloud queue, queue growth velocity dQ/dt, and the age of "
        "the head-of-line queued task measuring proximity to the 15.0 s SLA deadline; and "
        "(4) Worker Fleet and Actuation State: currently active operational GPU workers k_t in [1, 18], booting workers C_boot undergoing container "
        "initialization, and elapsed time since the last scaling action. Table 6.1 details the formal specification of the telemetric contract and grammar primitives."
    )

    # Table 6.1: Telemetric Observation Contract and Grammar Primitives
    p_t61_title = doc.add_paragraph()
    p_t61_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t61_title.paragraph_format.space_before = Pt(8)
    p_t61_title.paragraph_format.space_after = Pt(4)
    p_t61_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t61_title, "Table 6.1: Telemetric observation contract and AST grammar primitive specifications.", font_size_pt=11.0, bold=True)

    t61_headers = ["Telemetric Tier / Category", "Variable / Symbol", "Data Type", "Physical Interpretation & Bounds"]
    t61_widths = [Inches(1.8), Inches(1.3), Inches(0.9), Inches(2.6)]

    t61_rows = [
        ("Tier 1: Edge Semantic Triage", "p_fast", "float", "Fraction of queries resolved locally at edge (|C(x)| = 1), bounded in [0.0, 1.0]."),
        ("Tier 1: Edge Semantic Triage", "p_fast_velocity", "float", "Discrete backward derivative dp_fast/dt over 3-epoch sliding window."),
        ("Tier 1: Edge Semantic Triage", "mean_set_size", "float", "Mean RAPS prediction set cardinality E[|C(x)|], nominal 7.25 classes."),
        ("Tier 2: Continuum Traffic", "ingress_rps", "float", "Arriving Poisson IoT image request rate lambda(t) at sensor ingress."),
        ("Tier 2: Continuum Traffic", "ingress_acceleration", "float", "Second derivative d^2lambda/dt^2 indicating sudden traffic ramp onset."),
        ("Tier 2: Continuum Traffic", "offered_cloud_rps", "float", "Causal offload demand: lambda_cloud(t) = lambda(t) * (1 - p_fast)."),
        ("Tier 3: Queue Backlog & Age", "cloud_queue_depth", "int", "Current unserviced task backlog Q_t waiting in CloudRefine ingress queue."),
        ("Tier 3: Queue Backlog & Age", "cloud_queue_velocity", "float", "Rate of backlog growth dQ/dt separating transient spikes from sustained queues."),
        ("Tier 3: Queue Backlog & Age", "oldest_task_age_s", "float", "Head-of-line task queuing age, indicating proximity to D_SLA = 15.0 s."),
        ("Tier 4: Fleet & Actuation", "active_workers", "int", "Active, operational GPU worker instances k_t clamped in [1, 18]."),
        ("Tier 4: Fleet & Actuation", "booting_workers", "int", "Workers currently spinning up subject to container startup lag T_boot."),
        ("Tier 4: Fleet & Actuation", "time_since_last_scale_s", "float", "Elapsed seconds since last scaling actuation for cooldown tracking."),
        ("Hardware / Contract Bounds", "worker_capacity_rps", "float", "Profiled Tesla T4 service rate mu = 16.0 RPS (t_cloud = 0.0625 s)."),
        ("Hardware / Contract Bounds", "sla_deadline_s", "float", "End-to-end Service Level Agreement latency budget D_SLA = 15.0 s."),
    ]

    tbl61 = doc.add_table(rows=len(t61_rows) + 1, cols=4)
    tbl61.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl61.autofit = False

    # Header Row
    hdr_cells61 = tbl61.rows[0].cells
    for i, title in enumerate(t61_headers):
        hdr_cells61[i].width = t61_widths[i]
        set_cell_margins(hdr_cells61[i], top=70, bottom=70, left=90, right=90)
        p = hdr_cells61[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.bold = True

    # Data Rows
    for row_idx, data in enumerate(t61_rows):
        row_cells = tbl61.rows[row_idx + 1].cells
        for col_idx, text in enumerate(data):
            row_cells[col_idx].width = t61_widths[col_idx]
            set_cell_margins(row_cells[col_idx], top=50, bottom=50, left=80, right=80)
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            add_formatted_math_text(p, text, font_size_pt=9.5)

    # Apply uniform grid borders to Table 6.1
    apply_table_grid_borders(tbl61)

    p_after_t61 = doc.add_paragraph()
    p_after_t61.paragraph_format.space_before = Pt(2)
    p_after_t61.paragraph_format.space_after = Pt(6)

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "The AST grammar allows mathematical compositions including arithmetic operators (+, -, *, /), rectification operators (max, min), "
        "hyperbolic saturation functions (tanh), and logical conditional expressions (if-then-else). To enforce safety, the grammar bans while loops, "
        "arbitrary recursion, dynamic execution (eval, exec), and external network or filesystem calls. Every candidate program is constrained to "
        "return an integer worker allocation k_t clamped within the physical cluster limits [1, 18]."
    )

    # =========================================================================
    # 6.3 MULTI-OBJECTIVE FITNESS EVALUATION
    # =========================================================================
    doc.add_heading("6.3 MULTI-OBJECTIVE FITNESS EVALUATION", level=2)

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "Candidate AST programs are evaluated using a multi-objective fitness engine (src/continuum_ext/evolution/openevolve_evaluator_v7.py). "
        "The evaluation objective resolves the fundamental trade-off between infrastructure cost minimization, tail latency containment, and "
        "strict Service Level Agreement compliance. The master fitness objective J_v7 is structured into canonical evaluation, operational realism "
        "evaluation, and competitive baseline dominance bonuses:"
    )

    # OMML Equation 6.1: Evolutionary multi-objective fitness function
    omml_eq6_1 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>J</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>v7</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = -</m:t></m:r>'
        '<m:sSubSup>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>∑</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>r</m:t></m:r><m:r><m:t>=1</m:t></m:r></m:sub>'
        '<m:sup><m:r><m:t>13</m:t></m:r></m:sup>'
        '</m:sSubSup>'
        '<m:r><m:t>[</m:t></m:r>'
        '<m:r><m:t>1000 ⋅ </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>m</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>r</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>Θ</m:t></m:r>'
        '<m:r><m:t>) + </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>ws</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>r</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>Θ</m:t></m:r>'
        '<m:r><m:t>) - </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>B</m:t></m:r>'
        '<m:r><m:t> ⋅ 𝕀[</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>m</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>r</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>Θ</m:t></m:r>'
        '<m:r><m:t>) = 0]</m:t></m:r>'
        '<m:r><m:t>]</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq6_1, eq_number="6.1")

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "In Equation (6.1), m_r(Theta) represents the total deadline violation count in regime r, ws_r(Theta) denotes the cumulative worker-second "
        "expenditure, and B represents a zero-miss bonus that rewards policies operating strictly within the SLA-safe envelope. The 1000x penalty "
        "multiplier on deadline misses enforces absolute prioritization of SLA compliance: a policy that reduces compute expenditure by shedding "
        "workers but incurs even a single SLA violation is heavily penalized and eliminated from the Pareto front."
    )

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "A critical enhancement introduced in the v7 evaluator is True SLO Accountability. Earlier evaluator iterations tracked only completed "
        "requests that exceeded the latency deadline D_SLA. However, pathological controllers could artificially suppress miss counts by freezing "
        "provisioning, allowing unserved requests to accumulate indefinitely in ingress queues. Under True SLO Accountability, the evaluator computes "
        "M = max(slo_violation_count, deadline_miss_count), strictly penalizing both completed deadline misses and unserved tasks abandoned in intermediate "
        "queues upon simulation termination."
    )

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "To manage computational budget during evolutionary search, the evaluator implements a three-stage cascade filter: "
        "(1) Stage 1: Pure Validity Gate (~0.05 s), performing static AST syntax validation, while-loop checks, and 5 boundary unit tests; "
        "(2) Stage 2: Multi-Stress Micro-Tranche Gate (~3.0 s), filtering non-viable candidates across three high-stress workload slices (flat, "
        "shock with T_boot = 1.0 s, and shock with T_boot = 5.0 s); and "
        "(3) Stage 3: Full Dual-Tier Parallelized Benchmark (~35 s), evaluating surviving candidates across all 13 canonical regimes and the "
        "physically grounded Realism Triad (suite2_shock at [2s, 5s, 15s], suite1_spike at [5s, 15s, 50s], and suite3_azure at [15s, 50s, 150s, 300s])."
    )

    # =========================================================================
    # 6.4 EVOLUTIONARY SEARCH DYNAMICS AND PARETO CONVERGENCE
    # =========================================================================
    doc.add_heading("6.4 EVOLUTIONARY SEARCH DYNAMICS AND PARETO CONVERGENCE", level=2)

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "The evolutionary synthesis campaign was executed using OpenEvolve across a budget of 150 iterations (configs/evolution/openevolve_config_v7.yaml). "
        "The search utilized a dual-stream large language model ensemble acting as mutation and crossover operators: "
        "Stream A (Creative Explorer) deployed an LLM configured with high temperature (0.85) and 65% selection weight to introduce structural "
        "topological innovations in the AST; Stream B (Precision Calibrator) operated at low temperature (0.40) with 35% weight to fine-tune continuous "
        "algebraic coefficients and threshold constants."
    )

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "To prevent population collapse into local optima, the engine enforced a progressive 3-strike anti-stagnation gating protocol: "
        "Strike 1 imposed a soft diversity penalty (-1.0) on structurally repetitive programs; "
        "Strike 2 applied a moderate penalty (-25.0) accompanied by diagnostic reflection prompts injected into the LLM context; and "
        "Strike 3 executed local branch pruning (-500.0) to force exploration of distinct topological niches."
    )

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "The evolutionary population exhibited dynamic Pareto convergence across iterations. Early generations explored aggressive cost-reduction "
        "heuristics that dropped worker allocations prematurely during traffic dips, resulting in heavy deadline miss penalties in Suite 2 (complexity shocks). "
        "Subsequent generations discovered that maintaining a small, conformal-scaled safety margin prevented queue explosions during sudden edge confidence "
        "collapses. In Iteration 1, the search synthesized Candidate c614055a (Program ID c614055a-5b35-4a25-9093-d678fd5d1da4), which achieved a record "
        "composite fitness score of +63.3943. This candidate delivered 56.39% cost savings versus static peak provisioning (27,900 worker-seconds), "
        "achieved zero canonical deadline misses, held maximum P99 latency to 14.00 s under extreme multi-second startup delays, and suppressed actuation "
        "churn to 200 total deltas across the entire stress triad."
    )

    # =========================================================================
    # 6.5 DEEP-DIVE INTO CHAMPION POLICY V7
    # =========================================================================
    doc.add_heading("6.5 DEEP-DIVE INTO CHAMPION POLICY V7", level=2)

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "The synthesized program, archived as champion_policy_v7_smooth.py, represents an elegant, closed-form control law. Analysis of its "
        "Abstract Syntax Tree reveals that the evolutionary process independently discovered classical control-theoretic principles, including "
        "proportional feed-forward demand sizing, derivative shock preemption, integral queue draining, and state-dependent hysteresis. "
        "The complete policy executes in four distinct mathematical terms:"
    )

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "Term 1 (Continuous Sizing with Conformal Multiplier): The policy scales incoming offered cloud demand lambda_cloud(t) using an empirical "
        "conformal safety factor and a derivative demand trend:"
    )

    # OMML Equation 6.2: Conformal demand term
    omml_eq6_2 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>demand</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:d>'
        '<m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr>'
        '<m:e>'
        '<m:sSub>'
        '<m:e><m:r><m:t>λ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>cloud</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '<m:r><m:t> + </m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>trend</m:t></m:r>'
        '</m:e>'
        '</m:d>'
        '<m:r><m:t> ⋅ </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>S</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>conf</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:t>μ</m:t></m:r>'
        '</m:den>'
        '</m:f>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq6_2, eq_number="6.2")

    p17 = doc.add_paragraph()
    p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p17,
        "where S_conf = 1.00 + 0.008 * max(0.0, mean_set_size - 1.0) dynamically inflates capacity when mean prediction set size expands beyond "
        "singletons, and trend = max(0.0, -p_fast_velocity) * ingress_rps * 0.14 preemptively projects demand growth during edge confidence declines."
    )

    p18 = doc.add_paragraph()
    p18.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p18,
        "Term 2 (Efficiency-First Queue Drain): Unserviced queue backlog Q_t is drained across an empirically synthesized drain window D = 2.08 s, "
        "damped by queue velocity dQ/dt:"
    )

    # OMML Equation 6.3: Queue drain term
    omml_eq6_3 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>drain</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Q</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t> + </m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>max</m:t></m:r>'
        '<m:r><m:t>(0.0, Δ</m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Q</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>) ⋅ 0.04</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:t>μ ⋅ 2.08</m:t></m:r>'
        '</m:den>'
        '</m:f>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq6_3, eq_number="6.3")

    p19 = doc.add_paragraph()
    p19.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p19,
        "Term 3 (Preemptive Edge Surge and Hyperbolic Booting Credit): The policy identifies acute edge collapse when velocity drops below "
        "theta_shock = 0.15 (specifically evaluated as max(0.0, -0.08 - p_fast_velocity) * ingress_rps * 0.18). Crucially, the policy mitigates "
        "booting worker thrashing through a hyperbolic credit discount function:"
    )

    # OMML Equation 6.4: Booting credit discount
    omml_eq6_4 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>B</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:t>0.95</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:t>1.0 + 2.8 ⋅ [</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>max</m:t></m:r>'
        '<m:r><m:t>(0.0, Δ</m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>Q</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t>) + 1.5 ⋅ </m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>max</m:t></m:r>'
        '<m:r><m:t>(0.0, </m:t></m:r>'
        '<m:sSub><m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>age</m:t></m:r></m:e><m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>head</m:t></m:r></m:sub></m:sSub>'
        '<m:r><m:t> - 0.8)]</m:t></m:r>'
        '</m:den>'
        '</m:f>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq6_4, eq_number="6.4")

    p20 = doc.add_paragraph()
    p20.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p20,
        "When queue pressure is low and tasks are fresh, B_t approaches 0.95, giving full credit to currently booting workers and suppressing "
        "redundant scale-out commands. However, when queue backlog accelerates or head-of-line task age exceeds 0.8 s, B_t drops sharply toward "
        "zero, discounting booting workers and authorizing emergency scale-out capacity before tasks exceed the 15.0 s deadline."
    )

    p21 = doc.add_paragraph()
    p21.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p21,
        "Term 4 (Asymmetric Hysteresis and Micro-Queue Protection): Scale-down commands are blocked if elapsed time since the last scaling action "
        "is under 2.5 s, if unserviced queue backlog exists (Q_t > 0), if head task age exceeds 0.8 s, or if queue growth is non-negative (dQ/dt > -0.1). "
        "Finally, the effective allocation is clamped within cluster hardware limits: k*(t) = int(max(1, min(18, effective_target))). "
        "Table 6.2 summarizes the mathematical formulation and parameter grounding of Champion Policy v7."
    )

    # Table 6.2: Synthesized Champion Policy v7 Architecture and Mathematical Parameters
    p_t62_title = doc.add_paragraph()
    p_t62_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t62_title.paragraph_format.space_before = Pt(8)
    p_t62_title.paragraph_format.space_after = Pt(4)
    p_t62_title.paragraph_format.line_spacing = 1.15
    add_formatted_math_text(p_t62_title, "Table 6.2: Synthesized Champion Policy v7 components and mathematical parameters.", font_size_pt=11.0, bold=True)

    t62_headers = ["Functional Component", "Mathematical Expression / Logic", "Tuned Parameter", "Operational Role"]
    t62_widths = [Inches(1.8), Inches(2.2), Inches(1.1), Inches(1.5)]

    t62_rows = [
        ("Conformal Headroom", "safety = 1.00 + 0.008 * max(0.0, |C| - 1.0)", "slope = 0.008", "Inflates worker target as prediction sets expand."),
        ("Feed-Forward Trend", "trend = max(0.0, -p_fast_velocity) * ingress * 0.14", "gain = 0.14", "Preemptively projects cloud arrival rate."),
        ("Queue Drain Window", "drain = (Q + max(0, dQ) * 0.04) / (mu * 2.08)", "D = 2.08 s", "Drains backlog smoothly without over-provisioning."),
        ("Edge Collapse Surge", "surge = max(0.0, -0.08 - p_fast_velocity) * ingress * 0.18", "theta = 0.08", "Injects immediate workers during confidence crashes."),
        ("Hyperbolic Credit", "B_t = 0.95 / (1.0 + 2.8 * pressure_factor)", "base = 0.95", "Discounts booting workers as task age exceeds 0.8s."),
        ("Scale-Down Cooldown", "Guard: time_since_scale < 2.5s or Q > 0 or age > 0.8s", "tau = 2.5s / 15.0s", "Suppresses high-frequency downscaling churn."),
        ("Capacity Clamp", "k_target = int(max(1, min(18, effective_target)))", "k_max = 18", "Enforces cloud cluster hardware boundaries."),
    ]

    tbl62 = doc.add_table(rows=len(t62_rows) + 1, cols=4)
    tbl62.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl62.autofit = False

    # Header Row
    hdr_cells62 = tbl62.rows[0].cells
    for i, title in enumerate(t62_headers):
        hdr_cells62[i].width = t62_widths[i]
        set_cell_margins(hdr_cells62[i], top=70, bottom=70, left=90, right=90)
        p = hdr_cells62[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(title)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        r.font.bold = True

    # Data Rows
    for row_idx, data in enumerate(t62_rows):
        row_cells = tbl62.rows[row_idx + 1].cells
        for col_idx, text in enumerate(data):
            row_cells[col_idx].width = t62_widths[col_idx]
            set_cell_margins(row_cells[col_idx], top=50, bottom=50, left=80, right=80)
            p = row_cells[col_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx in [2] else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            add_formatted_math_text(p, text, font_size_pt=9.5)

    # Apply uniform grid borders to Table 6.2
    apply_table_grid_borders(tbl62)

    p_after_t62 = doc.add_paragraph()
    p_after_t62.paragraph_format.space_before = Pt(2)
    p_after_t62.paragraph_format.space_after = Pt(6)
    doc.add_page_break()
