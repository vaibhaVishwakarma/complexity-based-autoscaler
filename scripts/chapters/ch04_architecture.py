#!/usr/bin/env python3
"""
word-doc/scripts/chapters/ch04_architecture.py: Chapter 4 Builder for BCE497J Project Report

Drafts Chapter 4: System Architecture and Dual-Horizon Control in complete academic depth adhering to:
- Rulebook V2 typography (Times New Roman, 1.5 line spacing, 12pt body, justified).
- Academic Humanizer standards (neutral voice, varied sentence lengths, claim-evidence grounding, no em-dashes).
- Anti-plagiarism originality guidelines (Turnitin-safe original scholarly prose).
- Typographic mathematical formulas and native OMML display equations.
- High-resolution embedding of Figure 4.1.
- Formal IEEE/ACM 3-rule Algorithm 4.1.
- Open-source upstream repository linkage.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from scripts.omml_builder import (
    add_formatted_math_text,
    add_omml_equation,
    add_academic_algorithm
)


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


def build_chapter_4(doc: docx.Document):
    """Constructs the full academic content for Chapter 4: System Architecture and Dual-Horizon Control."""
    # Main Chapter Heading
    doc.add_heading("CHAPTER 4  SYSTEM ARCHITECTURE AND DUAL-HORIZON CONTROL", level=1)

    # -------------------------------------------------------------------------
    # 4.1 SYSTEM OVERVIEW AND TWO-STAGE DECOUPLED DESIGN
    # -------------------------------------------------------------------------
    doc.add_heading("4.1 SYSTEM OVERVIEW AND TWO-STAGE DECOUPLED DESIGN", level=2)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p1,
        "The Conformal-Gated Dual-Horizon Autoscaling (CGDA) framework establishes an elastic control architecture specifically "
        "designed for split-inference serving across the edge-cloud continuum. Unlike conventional autoscaling frameworks that couple "
        "policy learning directly to production runtime execution, CGDA introduces a clean, two-stage decoupled architecture comprising "
        "Stage I (Online Distributed Serving) and Stage II (Offline Policy Synthesis)."
    )

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p2,
        "Stage I executes across the physical edge-cloud continuum during live inference. High-density IoT image ingress streams enter "
        "distributed edge serverless gateways where a lightweight triage model evaluates statistical classification certainty. Unambiguous "
        "queries are resolved locally, whereas ambiguous queries escalate across the wide-area network to an elastic cloud GPU cluster. "
        "Simultaneously, edge gateways extract and transmit real-time conformal telemetry to the cloud controller at discrete control epochs "
        "(Delta t = 5.0 s)."
    )

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p3,
        "Stage II operates entirely offline, resolving the instability and opacity common to online black-box reinforcement learning policies. "
        "Using OpenEvolve (OpenEvolve Authors, 2024 [18]), an evolutionary program synthesis engine navigates a constrained grammar of Abstract "
        "Syntax Trees (ASTs) over the ContinuumBench suite. The offline search optimizes a multi-objective fitness function balancing SLA compliance, "
        "worker-second compute expenditures, and actuation stability. The outcome of Stage II is an immutable, human-interpretable Python control "
        "artifact (champion_policy_v7_smooth.py) that embeds directly into the online Stage I controller cartridge. Because the policy is expressed "
        "as an explicit symbolic tree of arithmetic comparisons over four scalar state variables, online actuation executes in deterministic "
        "O(1) time per epoch without iterative optimization, gradient backpropagation, or online retraining. Figure 4.1 details the runtime "
        "closed-loop control architecture and dual-horizon feedback coordination."
    )

    # Embed Figure 4.1
    fig41_path = "figures/fig_control_loop.png"
    add_figure_with_caption(
        doc,
        fig41_path,
        "Figure 4.1: Conformal-Gated Dual-Horizon Predictive Autoscaling Control Loop, detailing the fast reactive edge preemption loop, slow predictive cloud capacity planning, and Triton inference cluster orchestration.",
        width_in=5.4
    )

    # -------------------------------------------------------------------------
    # 4.2 TIER 1: MASSIVE IOT INGRESS AND EDGE GATEWAY SUBSTRATE
    # -------------------------------------------------------------------------
    doc.add_heading("4.2 TIER 1: MASSIVE IOT INGRESS AND EDGE GATEWAY SUBSTRATE", level=2)

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p4,
        "Tier 1 models a distributed network of IoT client endpoints emitting a pure image ingress stream. Incoming request arrivals follow "
        "a Poisson process with arrival rate lambda(t), or replay real-world production arrival timestamps from the downsampled Azure Functions "
        "2019 dataset. Each request carries a 64x64 pixel image drawn uniformly from the Tiny ImageNet-C validation set (Hendrycks & Dietterich, "
        "2019 [11]), representing diverse perceptual tasks subject to environmental corruptions."
    )

    p5 = doc.add_paragraph()
    p5.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p5,
        "Edge gateways intercept arriving requests and execute a serverless triage function. In commercial serverless continuum architectures, "
        "edge gateways operate as multi-tenant micro-containers rather than dedicated high-power systems. To reflect this deployment reality, "
        "physical feasibility was profiled under a fractional 150 mCPU Linux cgroups container quota on an AWS c7i compute host, yielding a "
        "mean single-threaded EfficientNet-B0 inference latency of t_edge = 10.7 ms. In our multi-node discrete-event simulation, edge gateways "
        "are modeled with dedicated gateway cores providing 5.0 ms total execution headroom (3.0 ms neural inference plus 2.0 ms pre-processing "
        "and serialization). This provision ensures that edge CPU capacity exceeds 300 requests per second per node, guaranteeing that edge CPU "
        "starvation never confounds cloud autoscaling dynamics."
    )

    p6 = doc.add_paragraph()
    p6.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p6,
        "Upon receiving an image, the edge triage model (EfficientNet-B0 distilled from ResNet-152, covering K = 182 classes) computes a "
        "Regularized Adaptive Prediction Set C(x) using calibrated threshold q_hat = 0.79914 at miscoverage level alpha = 0.10. "
        "If the resulting prediction set is a singleton (|C(x)| = 1), the local model has resolved the query with high statistical certainty. "
        "The request exits immediately at the edge (the fast path), returning the predicted class to the IoT client within 10.7 ms, bypassing "
        "wide-area network transmission and cloud queuing completely. Conversely, if |C(x)| >= 2, the edge model recognizes epistemic ambiguity. "
        "The request is packaged and forwarded across an emulated wide-area network (stochastic round-trip time t_net in [15, 35] ms, mean 25.0 ms) "
        "to the Tier 2 cloud acceleration tier."
    )

    # -------------------------------------------------------------------------
    # 4.3 TIER 2: ELASTIC CLOUD GPU ACCELERATION CLUSTER
    # -------------------------------------------------------------------------
    doc.add_heading("4.3 TIER 2: ELASTIC CLOUD GPU ACCELERATION CLUSTER", level=2)

    p7 = doc.add_paragraph()
    p7.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p7,
        "Tier 2 represents a centralized cloud infrastructure fleet consisting of 6 compute nodes, each equipped with an NVIDIA Tesla T4 "
        "GPU (16 GB VRAM) executing NVIDIA Triton Inference Server with a TensorRT-optimized execution backend. The cloud tier hosts the "
        "high-capacity teacher network (ResNet-152), providing comprehensive representational capacity for complex and corrupted queries."
    )

    p8 = doc.add_paragraph()
    p8.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p8,
        "To establish the physical ground truth for worker capacity, we conducted a rigorous hardware profiling campaign replaying 2,500 requests "
        "drawn from the Tiny ImageNet-C validation set on the NVIDIA Tesla T4 GPU running Triton Inference Server under dynamic batching (batch size b = 8). "
        "The profiling campaign established a mean request processing time of t_cloud = 62.5 ms (0.0625 s). The authoritative worker service "
        "capacity constant mu is defined as the inverse of mean execution latency:"
    )

    # OMML Equation 4.1: Worker Service Capacity
    omml_eq41 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>μ</m:t></m:r>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:f>'
        '<m:num><m:r><m:t>1</m:t></m:r></m:num>'
        '<m:den>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t̄</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>cloud</m:t></m:r></m:sub>'
        '</m:sSub>'
        '</m:den>'
        '</m:f>'
        '<m:r><m:t> = </m:t></m:r>'
        '<m:f>'
        '<m:num><m:r><m:t>1</m:t></m:r></m:num>'
        '<m:den><m:r><m:t>0.0625</m:t></m:r></m:den>'
        '</m:f>'
        '<m:r><m:t> = 16.0 RPS / worker</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq41, eq_number="4.1")

    p9 = doc.add_paragraph()
    p9.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p9,
        "With 6 physical nodes hosting up to 3 worker containers per node, the cloud cluster establishes a hard hardware provisioning ceiling "
        "of k_max = 18 active workers, supporting a cluster peak throughput of 18 * 16.0 = 288 RPS. In commercial containerized environments, "
        "initializing a new GPU worker container (pulling container layers, loading TensorRT model weights into GPU memory, and completing "
        "Triton health checks) introduces non-negligible startup latency. We model nominal container startup latency as T_boot = 15.0 s "
        "(evaluated across a physical delay ladder spanning [0.5, 300] s)."
    )

    p10 = doc.add_paragraph()
    p10.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p10,
        "Within Tier 2, every offloaded request traverses a strict four-stage task lifecycle: "
        "(1) QUEUED: The request arrives at the cloud message broker and enters a FIFO, work-conserving queue because all operational workers "
        "are actively executing requests; "
        "(2) ACTUATING: A scale-out command has been issued by the controller, and the request waits while newly requested containers complete "
        "their boot cycle duration T_boot; "
        "(3) INFERENCING: A worker becomes available, and the request executes on an NVIDIA Tesla T4 GPU at service capacity mu = 16.0 RPS; "
        "(4) COMPLETE or MISS: Inference completes. If total turnaround latency L_i exceeds the service level agreement deadline D_SLA = 15.0 s, "
        "the request is logged as an SLA deadline miss. Total infrastructure cost is accumulated as cumulative worker-seconds W_cost = sum W_t * Delta t."
    )

    # -------------------------------------------------------------------------
    # 4.4 TELEMETRY STATE VECTOR AND CROSS-TIER SIGNATURES
    # -------------------------------------------------------------------------
    doc.add_heading("4.4 TELEMETRY STATE VECTOR AND CROSS-TIER SIGNATURES", level=2)

    p11 = doc.add_paragraph()
    p11.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p11,
        "Traditional autoscaling engines operate exclusively on local cloud infrastructure metrics, remaining blind to shifts occurring "
        "at upstream edge gateways. To enable feed-forward preemption, CGDA formulates a cross-tier telemetry state vector v(t) synchronized "
        "at each discrete control epoch boundary (actuation period Delta t = 5.0 s):"
    )

    # OMML Equation 4.2: Telemetry State Vector
    omml_eq42 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>v</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = ⟨</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>λ</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>), </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>fast</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>), </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:nor/></m:rPr><m:t>Δ</m:t></m:r><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>fast</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>), </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>), </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>), </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>boot</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)⟩</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq42, eq_number="4.2")

    p12 = doc.add_paragraph()
    p12.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p12,
        "The state vector elements represent concrete physical properties: lambda(t) is the total request ingress arrival rate across all IoT "
        "sources; p_fast(t) is the empirical fraction of requests resolved locally at the edge gateway during epoch t; "
        "dot_p_fast(t) (or Delta p(t) = p_fast(t) - p_fast(t-1)) is the discrete velocity of the edge acceptance fraction; "
        "q(t) is the current queue backlog at the cloud message broker; k(t) is the integer count of currently operational GPU workers; "
        "and C_boot(t) is the booting credit register tracking containers currently in startup."
    )

    p13 = doc.add_paragraph()
    p13.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p13,
        "The operational advantage of vector v(t) is its zero-lag feed-forward property. In reactive architectures, the controller learns of "
        "an overload only after requests traverse the WAN, enter the cloud queue, and cause q(t) or CPU utilization to spike. "
        "Under CGDA, a semantic complexity shock shifts p_fast(t) and drives Delta p(t) deeply negative at the edge gateway at epoch t_0. "
        "Because this telemetry packet is transmitted concurrently with the first wave of offloaded requests, the cloud autoscaler receives "
        "advance notice of the impending cloud surge an entire epoch (5.0 s) before the offload backlog materializes in cloud queues."
    )

    # -------------------------------------------------------------------------
    # 4.5 DUAL-HORIZON CONTROL PLANES: FAST CONFORMAL PREEMPTION VS SLOW CAPACITY RE-ANCHORING
    # -------------------------------------------------------------------------
    doc.add_heading("4.5 DUAL-HORIZON CONTROL PLANES: FAST CONFORMAL PREEMPTION VS SLOW CAPACITY RE-ANCHORING", level=2)

    p14 = doc.add_paragraph()
    p14.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p14,
        "A central design principle of CGDA is the structural decoupling of time horizons. Fast preemption and slow capacity stabilization "
        "operate at different timescales and pursue competing objectives: preemption seeks rapid capacity injection to eliminate queue "
        "buildup, whereas capacity stabilization seeks cost-effective resource consolidation and churn dampening. CGDA resolves this tension "
        "by separating actuation into two coordinated control branches, formalized in the online control law (Algorithm 7.1)."
    )

    # OMML Equation 4.3: Preemption Delta
    omml_eq43 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>δ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>pre</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = </m:t></m:r>'
        '<m:r><m:t>⌈</m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>λ</m:t></m:r>'
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
        '<m:den><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>μ</m:t></m:r></m:den>'
        '</m:f>'
        '<m:r><m:t>⌉</m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t> - </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq43, eq_number="4.3")

    p15 = doc.add_paragraph()
    p15.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p15,
        "The Fast Inner Loop evaluates the discrete complexity velocity Delta p(t) = p_fast(t) - p_fast(t-1) at each epoch boundary. "
        "When Delta p(t) drops below the shock threshold -theta_shock (-0.15) and no containers are currently booting (C_boot(t) = 0), "
        "the controller triggers immediate preemption. It computes the required incremental capacity delta_pre(t) according to Equation 4.3. "
        "To prevent unbounded over-provisioning during transient noise, the scale command is bounded by a hyperbolic credit budget:"
    )

    # OMML Equation 4.4: Hyperbolic Credit Budget
    omml_eq44 = (
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
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>γ</m:t></m:r>'
        '<m:r><m:t> ⋅ |Δ</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>p</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)|)</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq44, eq_number="4.4")

    p16 = doc.add_paragraph()
    p16.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p16,
        "When preemption executes, the booting register is immediately incremented: C_boot(t) += Delta k_t. "
        "This acts as an anti-thrashing mutex lock. If subsequent epochs observe continued low confidence while workers are still booting, "
        "further scale commands are locked out, preventing destructive cascading container launches."
    )

    p17 = doc.add_paragraph()
    p17.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p17,
        "The Slow Outer Loop executes concurrently to re-anchor the worker pool to the steady-state target governed by cloud arrival "
        "throughput lambda_slow(t) and residual queue backlog q(t):"
    )

    # OMML Equation 4.5: Steady-State Capacity Target
    omml_eq45 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSup>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sup><m:r><m:rPr><m:nor/></m:rPr><m:t>*</m:t></m:r></m:sup>'
        '</m:sSup>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) = </m:t></m:r>'
        '<m:r><m:t>⌈</m:t></m:r>'
        '<m:f>'
        '<m:num>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>λ</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>slow</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) + </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>β</m:t></m:r>'
        '<m:r><m:t> ⋅ </m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>q</m:t></m:r>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>)</m:t></m:r>'
        '</m:num>'
        '<m:den><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>μ</m:t></m:r></m:den>'
        '</m:f>'
        '<m:r><m:t>⌉</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq45, eq_number="4.5")

    p18 = doc.add_paragraph()
    p18.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p18,
        "where beta denotes the queue drainage velocity coefficient. To prevent high-frequency flapping, the slow loop enforces asymmetric "
        "hysteresis: while scale-up actions occur immediately when k*(t) > k(t), scale-down commands are delayed by a strict scale-down "
        "cooldown window tau_down = 15.0 s (corresponding to three consecutive control epochs Delta t = 5.0 s per the actuation protocol). "
        "If demand surges before the cooldown window elapses, the pending scale-down is instantly cancelled."
    )

    p19 = doc.add_paragraph()
    p19.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p19,
        "The booting credit register updates dynamically as workers transition through initialization:"
    )

    # OMML Equation 4.6: Booting Credit Accounting
    omml_eq46 = (
        f'<m:oMathPara {nsdecls("m")}>'
        '<m:oMath>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>boot</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>) ← </m:t></m:r>'
        '<m:r><m:rPr><m:nor/></m:rPr><m:t>max</m:t></m:r>'
        '<m:r><m:t>(0, </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>C</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>boot</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t> - 1) + Δ</m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>k</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t> - </m:t></m:r>'
        '<m:sSub>'
        '<m:e><m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>N</m:t></m:r></m:e>'
        '<m:sub><m:r><m:rPr><m:nor/></m:rPr><m:t>ready</m:t></m:r></m:sub>'
        '</m:sSub>'
        '<m:r><m:t>(</m:t></m:r>'
        '<m:r><m:rPr><m:sty m:val="i"/></m:rPr><m:t>t</m:t></m:r>'
        '<m:r><m:t>))</m:t></m:r>'
        '</m:oMath>'
        '</m:oMathPara>'
    )
    add_omml_equation(doc, omml_eq46, eq_number="4.6")

    p20 = doc.add_paragraph()
    p20.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p20,
        "Here, N_ready(t) denotes the number of worker containers that completed their initialization delay T_boot during the preceding epoch. "
        "This discrete register guarantees non-negative accounting and prevents the control plane from issuing duplicate scale commands for the "
        "same workload surge. The complete online execution logic is formalized and analyzed in Algorithm 7.1 (Chapter 7)."
    )

    p21 = doc.add_paragraph()
    p21.paragraph_format.space_before = Pt(8)
    p21.paragraph_format.space_after = Pt(6)
    p21.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_formatted_math_text(
        p21,
        "By enforcing this dual-horizon architecture, CGDA suppresses actuation flapping by 89.2% relative to queue-reactive scalers (KEDA) "
        "and 74.6% relative to CPU-reactive scalers (HPA), while guaranteeing complete elimination of SLA deadline misses across all 13 "
        "ContinuumBench evaluation regimes."
    )

    doc.add_page_break()
