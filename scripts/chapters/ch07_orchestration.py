#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch07_orchestration.py: Chapter 7 Builder for BCE497J Project Report

Drafts Chapter 7: Online Two-Loop Orchestration and Hysteresis adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations via scripts.omml_builder.
- Publication-grade Figure 7.1 and Algorithm 7.1 embedding.
- Strict grounding in output/champion_policy_v7_smooth.py and verified repository artifacts.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from scripts.omml_builder import add_formatted_math_text, add_omml_equation, add_academic_algorithm


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


def build_chapter_7(doc: docx.Document):
    """Constructs the full academic content for Chapter 7: Online Two-Loop Orchestration and Hysteresis."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 7  ONLINE TWO-LOOP ORCHESTRATION AND HYSTERESIS", level=1)

    # =========================================================================
    # 7.1 ONLINE DUAL-HORIZON ORCHESTRATION ARCHITECTURE
    # =========================================================================
    doc.add_heading("7.1 ONLINE DUAL-HORIZON ORCHESTRATION ARCHITECTURE", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "The Conformal-Gated Dual-Horizon Autoscaler (CGDA) resolves the fundamental conflict between rapid disturbance rejection and steady-state "
        "provisioning stability through a decoupled two-loop architecture. In single-loop autoscaling systems, scaling decisions attempt to satisfy "
        "competing requirements simultaneously: responding immediately to sudden traffic spikes while filtering out high-frequency noise to avoid "
        "destabilizing worker churn. When applied to multi-tier split inference pipelines where container boot delay (T_boot = 15.0 s) matches the "
        "entire end-to-end Service Level Agreement budget (D_SLA = 15.0 s), single-loop controllers inevitably fail. They either react too late, "
        "causing queue buildup and SLA deadline misses, or over-react, triggering violent worker flapping and excessive cloud resource expenditure."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "CGDA resolves this dilemma by separating control authority into two distinct temporal horizons: a fast inner preemption loop and a slow outer "
        "stabilization loop. The fast inner loop operates at the discrete control epoch frequency (Delta t = 5.0 s), monitoring derivatives of the edge "
        "conformal triage signal to detect semantic complexity shocks before requests accumulate in cloud queues. The slow outer loop operates over an "
        "asymmetric hysteresis horizon (tau_down = 15.0 s, spanning exactly three control epochs), re-anchoring cluster worker capacity to steady-state "
        "queuing equilibrium and suppressing premature scale-down commands."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "The runtime execution of CGDA is strictly bounded. At each epoch boundary t, the controller samples the telemetric state vector "
        "sigma(t) = (lambda(t), p_fast(t), k(t), C_boot(t)) and evaluates an algebraic decision tree synthesized via evolutionary search. "
        "The entire decision rule executes in O(1) time per epoch, evaluating arithmetic comparisons and bounded functions without matrix operations, "
        "iterative optimization, or runtime model retraining. While empirically demonstrated on split vision inference across our edge serverless "
        "testbed (150 mCPU Linux cgroups quota on AWS c7i compute hosts, EfficientNet-B0 inference t_edge = 10.7 ms, and cloud NVIDIA Tesla T4 GPUs "
        "with worker capacity mu = 16.0 RPS at batch saturation t_cloud = 62.5 ms), the dual-horizon control paradigm serves as a general proof of concept "
        "for modern cascading foundation models, including Vision-Language Models (VLMs) and cascading Large Language Models (LLMs; Chen et al., 2023 [5]; "
        "Patel et al., 2024 [27]; Romero et al., 2021 [21]; Sheng et al., 2024)."
    )

    # =========================================================================
    # 7.2 PHASE 1: FAST-LOOP CONFORMAL PREEMPTION
    # =========================================================================
    doc.add_heading("7.2 PHASE 1: FAST-LOOP CONFORMAL PREEMPTION", level=2)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "Phase 1 executes the fast inner loop, designed for proactive disturbance preemption. The edge serverless gateway continuously evaluates "
        "arriving image queries using the calibrated RAPS non-conformity threshold (q_hat = 0.79914 at alpha = 0.10). Requests producing singleton sets "
        "(|C(x)| = 1) exit locally at the edge in 10.7 ms, while ambiguous requests (|C(x)| >= 2) offload to the cloud. At each epoch boundary t, the "
        "controller computes the complexity velocity Delta p(t) = p_fast(t) - p_fast(t-1). When environmental corruptions or domain shifts suddenly "
        "degrade input clarity, edge confidence collapses, driving Delta p(t) below the preemption shock threshold theta_shock = 0.15."
    )

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "Upon detecting an acute complexity shock (Delta p(t) < -theta_shock), the fast loop evaluates whether the cloud fleet has idle booting "
        "capacity. If the booting worker register satisfies C_boot(t) = 0, indicating that no previous scaling action is currently pending, the fast loop "
        "triggers an immediate preemption event. The required scale-out capacity delta_pre(t) is estimated by projecting the surge in cloud-directed demand:"
    )

    # OMML Equation 7.1: Preemption scaling delta
    omml_eq7_1 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>δ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>pre</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = </m:t></m:r>'
        '<m:d>'
        '<m:dPr><m:begChr m:val="⌈"/><m:endChr m:val="⌉"/><m:grow m:val="1"/></m:dPr>'
        '<m:e>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:t>λ</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) ⋅ (1 - </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>fast</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>))</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:t>μ</m:t></m:r>'
        '</m:den>'
        '</m:f>'
        '</m:e>'
        '</m:d>'
        '<m:r><m:t> - </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq7_1, eq_number="7.1")

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "If delta_pre(t) > 0, the controller immediately emits a scale-out command of Delta k_t = min(delta_pre(t), k_max_up) workers, bypassing "
        "the slow outer loop entirely. Simultaneously, to modulate the scaling intensity during extreme shocks, the controller computes a hyperbolic "
        "credit budget B_t that bounds proactive resource expansion according to the acute severity of the shock:"
    )

    # OMML Equation 7.2: Hyperbolic credit budget
    omml_eq7_2 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>B</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>B</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>max</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> ⋅ </m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>tanh</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>γ</m:t></m:r>'
        '<m:r><m:t> ⋅ |Δ</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)|)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq7_2, eq_number="7.2")

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "Crucially, Phase 1 enforces a strict anti-thrashing invariant through the booting register C_boot(t). Whenever a scale-out command is issued, "
        "the register increments: C_boot(t) <- C_boot(t) + Delta k_t. While C_boot(t) > 0, newly requested container instances remain in initializing state. "
        "During this startup period (T_boot = 15.0 s), all subsequent fast-loop preemption triggers are gated and suppressed. This register lock prevents "
        "cascaded, runaway scale-out commands during a single container boot cycle, holding scaling churn to 16 deltas per run (an 89.2% churn reduction "
        "compared to reactive queue autoscalers at 148 deltas per run)."
    )

    # =========================================================================
    # 7.3 PHASE 2: SLOW-LOOP CAPACITY RE-ANCHORING AND QUEUE DRAINING
    # =========================================================================
    doc.add_heading("7.3 PHASE 2: SLOW-LOOP CAPACITY RE-ANCHORING AND QUEUE DRAINING", level=2)

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "If the fast inner loop does not fire (either because edge confidence is stable or because the booting register is locked), control passes "
        "to Phase 2: the slow outer loop. The objective of Phase 2 is to maintain long-term capacity equilibrium, absorb sustained workload shifts, "
        "and clear any residual request queues that accumulated during transient surges. The controller evaluates the effective cloud arrival rate "
        "lambda_slow(t) = (1 - p_fast(t)) * lambda(t) and calculates the steady-state target capacity k*(t):"
    )

    # OMML Equation 7.3: Steady-state capacity target
    omml_eq7_3 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = </m:t></m:r>'
        '<m:d>'
        '<m:dPr><m:begChr m:val="⌈"/><m:endChr m:val="⌉"/><m:grow m:val="1"/></m:dPr>'
        '<m:e>'
        '<m:f>'
        '<m:num>'
        '<m:sSub>'
        '<m:e><m:r><m:t>λ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>slow</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) + </m:t></m:r>'
        '<m:r><m:t>β</m:t></m:r>'
        '<m:r><m:t> ⋅ </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den>'
        '<m:r><m:t>μ</m:t></m:r>'
        '</m:den>'
        '</m:f>'
        '</m:e>'
        '</m:d>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq7_3, eq_number="7.3")

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "In Equation (7.3), q(t) denotes the current unserviced queue backlog waiting at the cloud ingress buffer, and beta represents the queue "
        "draining damping coefficient. When queue backlog is zero (q(t) = 0), the target capacity aligns exactly with the classical M/M/m "
        "steady-state provisioning requirement ceil(lambda_cloud / mu). When backlog accumulates, the term beta * q(t) temporarily expands target capacity "
        "to drain pending tasks within the SLA window, preventing tail latency inflation."
    )

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "The interaction between Phase 1 and Phase 2 creates an efficient division of labor: Phase 1 provides derivative feed-forward control to "
        "absorb rapid onset complexity shocks, while Phase 2 provides proportional-integral feedback to handle sustained macro-scale diurnal demand "
        "and clear residual queue buildup."
    )

    # =========================================================================
    # 7.4 ASYMMETRIC COOLDOWN HYSTERESIS
    # =========================================================================
    doc.add_heading("7.4 ASYMMETRIC COOLDOWN HYSTERESIS", level=2)

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "In cloud-edge elastic serving, provisioning penalties are fundamentally asymmetric. An under-provisioned epoch causes queue accumulation, "
        "latency spikes, and irreversible SLA deadline violations (a severe penalty). Conversely, an over-provisioned epoch expends only modest "
        "worker-seconds (at an infrastructure cost of approximately $0.000016 per worker-second on commercial cloud pricing). To reflect this cost "
        "asymmetry, Phase 2 implements asymmetric cooldown hysteresis with state-dependent suppression:"
    )

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "Scale-Up Dynamics: If k*(t) > k(t) and C_boot(t) = 0, the controller immediately executes a scale-out command of Delta k_t = min(k*(t) - k(t), "
        "k_max_up) workers, registers the booting capacity in C_boot(t), and records the actuation timestamp t_last_scale = t. There is zero delay "
        "imposed on scale-up."
    )

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "Scale-Down Dynamics: If k*(t) < k(t) and C_boot(t) = 0, the controller strictly blocks immediate capacity reductions. A scale-down command "
        "is permitted only if the elapsed time since the last scaling action exceeds the cooldown hysteresis window tau_down = 15.0 s (spanning exactly "
        "three control epochs Delta t = 5.0 s):"
    )

    # OMML Equation 7.4: Asymmetric hysteresis scale-down actuation
    omml_eq7_4 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>Δ</m:t></m:r><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> = -</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>min</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) - </m:t></m:r>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>), </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>max_down</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>)        if  (</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t> - </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>last_scale</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>) ≥ </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>τ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>down</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq7_4, eq_number="7.4")

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "If demand rebounds or queue backlog forms before the tau_down = 15.0 s cooldown expires, the pending scale-down action is cancelled "
        "immediately. This asymmetric hysteresis prevents limit-cycle oscillations (hunting) where controllers scale down during brief traffic valleys, "
        "only to be caught under-provisioned seconds later. In multi-seed benchmark evaluations across 1,300 controller runs, this mechanism eliminated "
        "flapping entirely, reducing actuation deltas by 89.2% relative to KEDA (16 deltas vs 148 deltas; Wilcoxon signed-rank p = 4.31 x 10^-31)."
    )

    # =========================================================================
    # 7.5 FORMAL CONTROL LOOP ALGORITHM WALKTHROUGH
    # =========================================================================
    doc.add_heading("7.5 FORMAL CONTROL LOOP ALGORITHM WALKTHROUGH", level=2)

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "Algorithm 7.1 formally presents the complete Conformal-Gated Dual-Horizon Control Loop executed at every epoch boundary Delta t = 5.0 s. "
        "The algorithm requires as input the telemetric observation tuple v(t), the current "
        "active worker count k(t), the booting worker register C_boot(t), the unserviced queue backlog q(t), the profiled service capacity mu = 16.0 RPS, "
        "and the cooldown parameter tau_down = 15.0 s."
    )

    # Algorithm 7.1 Embedding via add_academic_algorithm
    alg_lines = [
        (1, 0, "deltaK_t <- 0"),
        (2, 0, "// Phase 1: Fast-Loop Conformal Preemption"),
        (3, 0, "Δp(t) <- p_fast(t) - p_fast(t - 1)"),
        (4, 0, "if Δp(t) < -theta_shock and C_boot(t) = 0 then"),
        (5, 1, "B_t <- B_max * tanh(γ * |Δp(t)|)"),
        (6, 1, "delta_pre <- ceil((λ(t) * (1 - p_fast(t))) / μ) - k(t)"),
        (7, 1, "if delta_pre > 0 then"),
        (8, 2, "deltaK_t <- min(delta_pre, k_max_up)"),
        (9, 2, "C_boot(t) <- C_boot(t) + deltaK_t"),
        (10, 2, "t_last_scale <- t"),
        (11, 2, "return deltaK_t"),
        (12, 1, "end if"),
        (13, 0, "end if"),
        (14, 0, "// Phase 2: Slow-Loop Capacity Re-Anchoring and Asymmetric Hysteresis"),
        (15, 0, "lambda_slow(t) <- (1 - p_fast(t)) * λ(t)"),
        (16, 0, "k*(t) <- ceil((lambda_slow(t) + β * q(t)) / μ)"),
        (17, 0, "if k*(t) > k(t) and C_boot(t) = 0 then"),
        (18, 1, "deltaK_t <- min(k*(t) - k(t), k_max_up)"),
        (19, 1, "C_boot(t) <- C_boot(t) + deltaK_t"),
        (20, 1, "t_last_scale <- t"),
        (21, 0, "else if k*(t) < k(t) and C_boot(t) = 0 then"),
        (22, 1, "if (t - t_last_scale) >= tau_down then"),
        (23, 2, "deltaK_t <- -min(k(t) - k*(t), k_max_down)"),
        (24, 2, "t_last_scale <- t"),
        (25, 1, "end if"),
        (26, 0, "end if"),
        (27, 0, "return deltaK_t"),
    ]

    add_academic_algorithm(
        doc,
        alg_num=1,
        title="Conformal-Gated Dual-Horizon Control Loop",
        inputs="Ingress telemetry v(t) = <λ(t), p_fast(t), p_fast_velocity, mean_set_size, α_t>; active workers k(t); booting register C_boot(t); queue backlog q(t); cloud service rate μ; cooldown window τ_down.",
        outputs="Scaling actuation command Δk_t in ℤ.",
        lines=alg_lines,
        width_in=5.8
    )

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "A rigorous step-by-step walkthrough of Algorithm 7.1 demonstrates its stability properties: "
        "Line 1 initializes the scaling command to zero. "
        "Lines 3-13 execute Phase 1: if complexity velocity Delta p(t) indicates an acute shock exceeding threshold theta_shock = 0.15 and no workers "
        "are currently initializing (C_boot(t) = 0), the algorithm computes the hyperbolic credit budget B_t (Line 5) and projects preemption delta "
        "delta_pre (Line 6). If additional capacity is needed, the command is issued immediately (Line 8), locked in the booting register (Line 9), "
        "and returned (Line 11), successfully preempting the workload before requests accumulate in cloud queues."
    )

    p17 = doc.add_paragraph()
    p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p17,
        "If Phase 1 does not fire, Lines 15-26 execute Phase 2: the algorithm evaluates steady-state offered load lambda_slow(t) and computes the "
        "re-anchored worker target k*(t) accounting for queue backlog q(t) with damping coefficient beta (Line 16). If the cluster is under-provisioned "
        "and unlocked, an immediate scale-out command is issued (Lines 17-20). Conversely, if the cluster is over-provisioned, scale-down is strictly "
        "gated by the asymmetric cooldown condition (t - t_last_scale) >= tau_down (Lines 21-25). If the full tau_down = 15.0 s cooldown has not elapsed, "
        "the scale-down branch evaluates to false, returning Delta k_t = 0 (Line 27)."
    )

    p18 = doc.add_paragraph()
    p18.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p18,
        "By combining derivative preemption with asymmetric hysteresis, Algorithm 7.1 achieves deterministic, deadlock-free control. "
        "The booting register guarantees that at most one batch of initializing workers is in flight at any instant, while the cooldown window "
        "guarantees that worker capacity remains bounded and stable across fluctuating edge-cloud workloads."
    )
    doc.add_page_break()
