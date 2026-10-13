#!/usr/bin/env python3
"""
generate_testbed_figure.py — Publication Testbed Architecture & Controller Tap Diagram

Role:
    Generates high-DPI (300+ DPI) publication-quality architectural diagram
    illustrating the ContinuumBench simulation testbed and how all five autoscalers
    (Proposed Conformal, InferLine, HPA, KEDA, Static Peak) plug into distinct
    observability taps across the edge-cloud continuum.

Output:
    - figures/fig_testbed_architecture.png
    - figures/fig_testbed_architecture.pdf
    - paper-template/figures/fig_testbed_architecture.png
    - paper-template/figures/fig_testbed_architecture.pdf

Compliance:
    AGENTS.md Rule #3 — Workspace virtual environment (.venv/bin/python)
    AGENTS.md Rule #4 — Self-documenting structure
    AGENTS.md Rule #5 — Grounded in standard matplotlib
"""

import logging
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TestbedFigGen")

FIGURES_DIR = Path("figures")
PAPER_TEMPLATE_FIGURES_DIR = Path("paper-template/figures")

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
PAPER_TEMPLATE_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Cohesive paradigm color palette matching paper
COLORS = {
    "proposed": "#1a5fb4",     # Royal Blue (Proposed Conformal-Gated)
    "inferline": "#26a269",    # Forest Green (InferLine SoCC '20)
    "hpa": "#c01c28",          # Crimson Red (Kubernetes HPA)
    "keda": "#e66100",         # Amber/Orange (KEDA Queue Scaler)
    "static": "#5c3566",       # Deep Purple/Slate (Static Peak)
    "edge": "#1c71d8",         # Edge tier accent
    "wan": "#f57900",          # WAN accent
    "cloud": "#2ec27e",        # Cloud tier accent
    "neutral_dark": "#2e3436",
    "neutral_bg": "#f8f9fa",
}


def generate_testbed_diagram():
    """Renders the comprehensive testbed architecture and pluggable controller taps."""
    logger.info("Rendering ContinuumBench testbed architecture diagram...")

    fig, ax = plt.subplots(figsize=(14.4, 8.4), dpi=300)
    ax.set_xlim(0, 144)
    ax.set_ylim(0, 84)
    ax.axis("off")

    # =========================================================================
    # 1. TOP CONTAINER: ContinuumBench Simulation Pipeline (Lifecycle Stages 1-4)
    # =========================================================================
    box_pipeline = FancyBboxPatch(
        (2, 49), 140, 33,
        boxstyle="round,pad=0.8,rounding_size=2.0",
        linewidth=1.8, edgecolor="#3584e4", facecolor="#f6f9fc"
    )
    ax.add_patch(box_pipeline)
    ax.text(
        72, 80.2,
        r"ContinuumBench Simulation Testbed: Discrete-Event Edge-Cloud Serving Pipeline ($\Delta t = 1.0\mathrm{s}$ Control Loop)",
        ha="center", va="center", fontsize=11.5, fontweight="bold", color="#1c71d8"
    )

    # --- Stage 1: Workload Ingress Generator ---
    b_ingress = FancyBboxPatch((4, 52), 19, 25, boxstyle="round,pad=0.5,rounding_size=1.2",
                               linewidth=1.2, edgecolor="#555555", facecolor="#ffffff")
    ax.add_patch(b_ingress)
    ax.text(13.5, 74.2, "1. Ingress Generator", ha="center", va="center", fontsize=9.2, fontweight="bold", color="#2e3436")
    ax.text(13.5, 63.5, "13 Benchmark Regimes\n• Suite 1: Volume Dynamics\n• Suite 2: Semantic Shifts\n• Suite 3: Azure 24h Trace\n\nIngress Rate: $\\lambda(t)$",
            ha="center", va="center", fontsize=7.8, color="#333333")

    # --- Stage 2: Edge Gateway Tier ---
    b_edge = FancyBboxPatch((27, 52), 27, 25, boxstyle="round,pad=0.5,rounding_size=1.2",
                            linewidth=1.3, edgecolor=COLORS["edge"], facecolor="#f0f7ff")
    ax.add_patch(b_edge)
    ax.text(40.5, 74.2, "2. Edge Gateway (Local Node)", ha="center", va="center", fontsize=9.2, fontweight="bold", color=COLORS["edge"])
    
    # Sub-box: EfficientNet Student
    b_stud = FancyBboxPatch((28.5, 63.5), 24, 7.5, boxstyle="round,pad=0.4,rounding_size=1.0",
                            linewidth=1.0, edgecolor="#1c71d8", facecolor="#e1f0ff")
    ax.add_patch(b_stud)
    ax.text(40.5, 67.2, "Student: EfficientNet-B0\n(10.7ms ONNX Runtime)", ha="center", va="center", fontsize=7.6)

    # Sub-box: RAPS Conformal Triage
    b_raps = FancyBboxPatch((28.5, 54), 24, 7.5, boxstyle="round,pad=0.4,rounding_size=1.0",
                            linewidth=1.0, edgecolor="#1c71d8", facecolor="#bbdeea")
    ax.add_patch(b_raps)
    ax.text(40.5, 57.7, "Conformal RAPS Triage\n$|C(x)|=1 \\rightarrow$ Local Exit ($p_{\\mathrm{fast}}$)\n$|C(x)|\\geq 2 \\rightarrow$ WAN Offload",
            ha="center", va="center", fontsize=7.4, fontweight="bold")

    # --- Stage 3: WAN Transport & Network Delay Buffer ---
    b_wan = FancyBboxPatch((58, 52), 23, 25, boxstyle="round,pad=0.5,rounding_size=1.2",
                           linewidth=1.3, edgecolor=COLORS["wan"], facecolor="#fff8f0")
    ax.add_patch(b_wan)
    ax.text(69.5, 74.2, "3. WAN Network Link", ha="center", va="center", fontsize=9.2, fontweight="bold", color=COLORS["wan"])
    ax.text(69.5, 63.5, "In-Flight Packet Transit\n• Bandwidth & RTT Model\n• Latency Delay $t_{\\mathrm{net}}$\n\nOffload Demand:\n$\\lambda_{\\mathrm{slow}}(t) = (1 - p_{\\mathrm{fast}})\\lambda(t)$",
            ha="center", va="center", fontsize=7.6, color="#5c3566")

    # --- Stage 4: Cloud GPU Cluster ---
    b_cloud = FancyBboxPatch((85, 52), 55, 25, boxstyle="round,pad=0.5,rounding_size=1.2",
                             linewidth=1.3, edgecolor=COLORS["cloud"], facecolor="#f2faf5")
    ax.add_patch(b_cloud)
    ax.text(112.5, 74.2, "4. Cloud Accelerated Serving Tier (Triton GPU Cluster)", ha="center", va="center", fontsize=9.2, fontweight="bold", color="#1b5e20")

    # Cloud FIFO Queue
    b_queue = FancyBboxPatch((87, 54), 19, 16.5, boxstyle="round,pad=0.4,rounding_size=1.0",
                             linewidth=1.1, edgecolor="#e66100", facecolor="#fff3e0")
    ax.add_patch(b_queue)
    ax.text(96.5, 62.2, "Cloud FIFO Queue\n$Q_{\\mathrm{cloud}}(t)$\nVelocity: $\\dot{Q}$\nHead-of-Line: $\\tau$",
            ha="center", va="center", fontsize=7.8, fontweight="bold", color="#b23e00")

    # GPU Worker Pool
    b_workers = FancyBboxPatch((109, 54), 29, 16.5, boxstyle="round,pad=0.4,rounding_size=1.0",
                               linewidth=1.1, edgecolor="#26a269", facecolor="#e8f5e9")
    ax.add_patch(b_workers)
    ax.text(123.5, 62.2, "GPU Worker Pool ($k \\in [1, 18]$)\n• Triton Dynamic Batching ($b \\in [1, 32]$)\n• Profiled Rate: $\\mu = 16.0$ RPS/worker\n• Active Pool: $W_{\\mathrm{active}}(t)$\n• Startup Pool: $W_{\\mathrm{booting}}(t)$ ($T_{\\mathrm{boot}}$)",
            ha="center", va="center", fontsize=7.4, color="#1b5e20")

    # Pipeline Flow Arrows
    ax.add_patch(FancyArrowPatch((23, 64.5), (27, 64.5), arrowstyle="-|>", mutation_scale=10, linewidth=1.2, color="#333333"))
    ax.add_patch(FancyArrowPatch((54, 60), (58, 60), arrowstyle="-|>", mutation_scale=10, linewidth=1.2, color=COLORS["wan"]))
    ax.add_patch(FancyArrowPatch((81, 62), (87, 62), arrowstyle="-|>", mutation_scale=10, linewidth=1.2, color=COLORS["wan"]))
    ax.add_patch(FancyArrowPatch((106, 62), (109, 62), arrowstyle="-|>", mutation_scale=10, linewidth=1.2, color="#26a269"))

    # =========================================================================
    # 2. MIDDLE SECTION: Two Clean Observability Channels (No Overlap)
    # =========================================================================
    # Channel A: High-Velocity Edge Conformal Telemetry Channel (Left side)
    b_chan_edge = FancyBboxPatch((4, 38.5), 58, 7.5, boxstyle="round,pad=0.4,rounding_size=1.0",
                                 linewidth=1.3, edgecolor="#813d9c", facecolor="#faf6fd", linestyle="--")
    ax.add_patch(b_chan_edge)
    ax.text(33, 43.5, "⚡ High-Velocity Conformal Telemetry Bus (Zero-Lag Edge Push)",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color="#813d9c")
    ax.text(33, 40.2, "$\\mathbf{v}(t) = \\langle \\lambda(t), p_{\\mathrm{fast}}(t), \\dot{p}_{\\mathrm{fast}}(t), \\bar{c}(t), \\alpha_t \\rangle$ (Streams before queries cross WAN)",
            ha="center", va="center", fontsize=7.4, color="#5c3566")

    # Arrow from Edge RAPS down to Telemetry Channel
    ax.add_patch(FancyArrowPatch((40.5, 54), (40.5, 46), arrowstyle="-|>", mutation_scale=10, linewidth=1.2, color="#813d9c", linestyle="--"))

    # Channel B: Standard Cloud Observability Bus (Right side)
    b_chan_cloud = FancyBboxPatch((66, 38.5), 76, 7.5, boxstyle="round,pad=0.4,rounding_size=1.0",
                                  linewidth=1.3, edgecolor="#2e3436", facecolor="#f5f7fa", linestyle="-.")
    ax.add_patch(b_chan_cloud)
    ax.text(104, 43.5, "Standard Cloud Observability Bus (Observed only after WAN transit & queueing)",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color="#2e3436")
    ax.text(104, 40.2, "Cloud Metrics: Queue Depth $Q_{\\mathrm{cloud}}(t)$, Velocity $\\dot{Q}$, Active Workers $W_{\\mathrm{active}}$, Booting Workers $W_{\\mathrm{booting}}$",
            ha="center", va="center", fontsize=7.4, color="#444444")

    # Arrow from Cloud Queue down to Cloud Observability Channel
    ax.add_patch(FancyArrowPatch((96.5, 54), (96.5, 46), arrowstyle="-|>", mutation_scale=10, linewidth=1.2, color="#b23e00", linestyle="-."))
    ax.add_patch(FancyArrowPatch((123.5, 54), (123.5, 46), arrowstyle="-|>", mutation_scale=10, linewidth=1.2, color="#26a269", linestyle="-."))

    # =========================================================================
    # 3. BOTTOM CONTAINER: Pluggable Controller Execution Substrate
    # =========================================================================
    box_controllers = FancyBboxPatch(
        (2, 3), 140, 32.5,
        boxstyle="round,pad=0.8,rounding_size=2.0",
        linewidth=1.8, edgecolor="#2e3436", facecolor="#ffffff"
    )
    ax.add_patch(box_controllers)
    ax.text(
        72, 33.5,
        "Pluggable Controller Execution Substrate: Controller.step(state) -> ControllerAction(scale, placement)",
        ha="center", va="center", fontsize=10.5, fontweight="bold", color="#2e3436"
    )

    # Controller 1: Proposed Conformal Autoscaler (Champion c614055a)
    b_ctrl_prop = FancyBboxPatch((4, 5.5), 26, 25, boxstyle="round,pad=0.4,rounding_size=1.2",
                                 linewidth=1.5, edgecolor=COLORS["proposed"], facecolor="#f0f5fc")
    ax.add_patch(b_ctrl_prop)
    ax.text(17, 28.2, "Proposed Conformal Scaler\n(Champion c614055a)",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color=COLORS["proposed"])
    ax.text(17, 16.5, "Observability Taps:\n[1] ⚡ Edge Telemetry Bus $\\mathbf{v}(t)$\n[2] Cloud Queue $Q(t), \\dot{Q}(t)$\n[3] Booting Workers $W_{\\mathrm{booting}}$\n\nControl Laws:\n• Surge Anticipation: $\\dot{p}_{\\mathrm{fast}}$\n• Hyperbolic Credit: $\\frac{0.95}{1+2.8p}$\n• Velocity-Gated Hysteresis\n• Set Uncertainty Headroom",
            ha="center", va="center", fontsize=7.0, color="#1c2833")

    # Controller 2: InferLine SoCC '20
    b_ctrl_infer = FancyBboxPatch((32, 5.5), 25, 25, boxstyle="round,pad=0.4,rounding_size=1.2",
                                  linewidth=1.4, edgecolor=COLORS["inferline"], facecolor="#f2faf5")
    ax.add_patch(b_ctrl_infer)
    ax.text(44.5, 28.2, "Offline Envelope Scaler\n(InferLine SoCC '20)",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color=COLORS["inferline"])
    ax.text(44.5, 16.5, "Observability Taps:\n[1] Cloud Queue Arrivals $\\lambda_{\\mathrm{slow}}^{\\mathrm{obs}}$\n[2] Offline Profiling Table $\\mu(b)$\n[Blind to Edge Telemetry $\\mathbf{v}(t)$]\n\nControl Laws:\n• Multi-Scale EMA (fast, mid, slow)\n• Envelope: $\\max(\\mathrm{EMAs}) \\cdot 1.15$\n• 15s Scale-Down Stabilization\n• Network Calculus Bounds",
            ha="center", va="center", fontsize=7.0, color="#1c2833")

    # Controller 3: Kubernetes HPA
    b_ctrl_hpa = FancyBboxPatch((59, 5.5), 25, 25, boxstyle="round,pad=0.4,rounding_size=1.2",
                                linewidth=1.4, edgecolor=COLORS["hpa"], facecolor="#fdf2f2")
    ax.add_patch(b_ctrl_hpa)
    ax.text(71.5, 28.2, "Reactive Utilization Scaler\n(Kubernetes HPA)",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color=COLORS["hpa"])
    ax.text(71.5, 16.5, "Observability Taps:\n[1] Cloud Queue Depth $Q_{\\mathrm{cloud}}(t)$\n[2] Active Workers $W_{\\mathrm{active}}(t)$\n[Blind to Edge Telemetry $\\mathbf{v}(t)$]\n\nControl Laws:\n• Utilization: $\\rho = Q / W_{\\mathrm{active}}$\n• Target: $\\rho^* = 0.70$ ($\\pm 10\\%$ tol)\n• Ratio: $\\lceil W \\cdot (\\rho / 0.7) \\rceil$\n• 1-Epoch Cooldown Window",
            ha="center", va="center", fontsize=7.0, color="#1c2833")

    # Controller 4: KEDA Queue Scaler
    b_ctrl_keda = FancyBboxPatch((86, 5.5), 25, 25, boxstyle="round,pad=0.4,rounding_size=1.2",
                                 linewidth=1.4, edgecolor=COLORS["keda"], facecolor="#fff8f0")
    ax.add_patch(b_ctrl_keda)
    ax.text(98.5, 28.2, "Reactive Queue Scaler\n(KEDA Queue Trigger)",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color=COLORS["keda"])
    ax.text(98.5, 16.5, "Observability Taps:\n[1] Cloud Queue Depth $Q_{\\mathrm{cloud}}(t)$\n[Blind to Edge Telemetry $\\mathbf{v}(t)$]\n[Blind to Worker Utilization $\\mu$]\n\nControl Laws:\n• Raw Backlog Target: 10 req/pod\n• Sizing Rule: $\\lceil Q / 10 \\rceil$\n• 2-Epoch Cooldown Window\n• Zero Utilization Feedback",
            ha="center", va="center", fontsize=7.0, color="#1c2833")

    # Controller 5: Static Peak Provisioning
    b_ctrl_static = FancyBboxPatch((113, 5.5), 27, 25, boxstyle="round,pad=0.4,rounding_size=1.2",
                                   linewidth=1.4, edgecolor=COLORS["static"], facecolor="#f8f5fa")
    ax.add_patch(b_ctrl_static)
    ax.text(126.5, 28.2, "Static Peak Capacity\n(Fixed Baseline)",
            ha="center", va="center", fontsize=8.2, fontweight="bold", color=COLORS["static"])
    ax.text(126.5, 16.5, "Observability Taps:\n[Open Loop: Zero Taps]\n[Blind to All Dynamics]\n\nControl Laws:\n• Fixed Provisioning: $k(t) = 18$\n• Over-provisions for peak spike\n• Zero SLA Misses\n• Incurs 51.5% Resource Waste",
            ha="center", va="center", fontsize=7.0, color="#1c2833")

    # =========================================================================
    # 4. OBSERVABILITY TAP CONNECTIONS (Vertical, Non-Overlapping Arrows)
    # =========================================================================
    # Proposed Tap 1: from Telemetry Bus down into Proposed Scaler
    ax.add_patch(FancyArrowPatch((17, 38.5), (17, 30.5), arrowstyle="-|>", mutation_scale=10, linewidth=1.4, color="#813d9c", linestyle="--"))
    
    # Proposed Tap 2: from Cloud Observability Bus (left corner) into Proposed Scaler
    ax.add_patch(FancyArrowPatch((70, 38.5), (25, 30.5), arrowstyle="-|>", mutation_scale=10, linewidth=1.1, color=COLORS["proposed"], linestyle=":"))

    # InferLine Tap: from Cloud Observability Bus into InferLine
    ax.add_patch(FancyArrowPatch((80, 38.5), (44.5, 30.5), arrowstyle="-|>", mutation_scale=10, linewidth=1.1, color=COLORS["inferline"], linestyle=":"))

    # HPA Tap: from Cloud Observability Bus straight down into HPA
    ax.add_patch(FancyArrowPatch((95, 38.5), (71.5, 30.5), arrowstyle="-|>", mutation_scale=10, linewidth=1.1, color=COLORS["hpa"], linestyle=":"))

    # KEDA Tap: from Cloud Observability Bus straight down into KEDA
    ax.add_patch(FancyArrowPatch((110, 38.5), (98.5, 30.5), arrowstyle="-|>", mutation_scale=10, linewidth=1.1, color=COLORS["keda"], linestyle=":"))

    # Actuation Action Banner
    ax.text(
        72, 1.8,
        r"Target Sizing Actuation: Active Controller returns $k(t) \in [1, 18]$ $\rightarrow$ Worker Pool Manager scales replicas and triggers cold-start boots ($T_{\mathrm{boot}}$)",
        ha="center", va="center", fontsize=8.0, fontweight="bold", color="#1c2833",
        bbox=dict(boxstyle="round,pad=0.3", fc="#eef2f7", ec="#3584e4", linewidth=1.0)
    )

    out_png = FIGURES_DIR / "fig_testbed_architecture.png"
    out_pdf = FIGURES_DIR / "fig_testbed_architecture.pdf"
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(PAPER_TEMPLATE_FIGURES_DIR / "fig_testbed_architecture.png", dpi=300, bbox_inches="tight")
    plt.savefig(PAPER_TEMPLATE_FIGURES_DIR / "fig_testbed_architecture.pdf", bbox_inches="tight")
    plt.close()
    logger.info(f"Successfully generated updated testbed architecture diagram: {out_png}")


if __name__ == "__main__":
    generate_testbed_diagram()
