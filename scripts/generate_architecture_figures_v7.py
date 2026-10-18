#!/usr/bin/env python3
"""
scripts/generate_architecture_figures_v7.py — Modular Publication-Grade Architecture Figures

Role:
    Generates authentic, high-impact systems architecture and control-loop diagrams
    modeled directly on top systems publications:
    - Fig 1 (Image 6 style — Tran & Kim, FGCS '24, Fig. 2): Two-Stage Modular Cloud-Edge Systems Architecture
    - Fig 2 (Image 5 style — Tran & Kim, FGCS '24, Fig. 3): Closed-Loop Telemetry & Control Feedback Interaction

Governance:
    AGENTS.md Rule #1 — Versioned generation script (_v7.py).
    AGENTS.md Rule #3 — Workspace virtual environment (.venv).
    AGENTS.md Rule #4 — Self-documenting structure.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.patheffects as pe

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = WORKSPACE_ROOT / "figures"
PAPER_FIGURES_DIR = WORKSPACE_ROOT / "paper" / "figures"
DATA_FIGURES_DIR = WORKSPACE_ROOT / "output" / "paper_data" / "figure_data"

for d in [FIGURES_DIR, PAPER_FIGURES_DIR, DATA_FIGURES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif", "STIXGeneral", "Liberation Serif"],
    "mathtext.fontset": "stix",
    "axes.edgecolor": "#222222",
    "axes.linewidth": 0.9,
    "figure.autolayout": False,
})


def save_fig(fig: plt.Figure, name: str) -> None:
    for dest in [FIGURES_DIR, PAPER_FIGURES_DIR]:
        png_path = dest / f"{name}.png"
        pdf_path = dest / f"{name}.pdf"
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        fig.savefig(pdf_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Saved {name} (PNG & PDF) to {FIGURES_DIR} and {PAPER_FIGURES_DIR}")


# ==============================================================================
# MODULAR DIAGRAM CARD PRIMITIVE
# ==============================================================================
class DiagramCard:
    """A self-contained modular visual card with bounded layout and anchor ports."""
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        lines: Optional[List[str]] = None,
        fc: str = "#ffffff",
        ec: str = "#333333",
        lw: float = 1.0,
        ls: str = "-",
        rounding: float = 1.2,
        title_color: str = "#000000",
        title_size: float = 8.5,
        body_color: str = "#333333",
        body_size: float = 7.2,
        line_spacing: float = 2.4,
    ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.title = title
        self.lines = lines or []
        self.fc = fc
        self.ec = ec
        self.lw = lw
        self.ls = ls
        self.rounding = rounding
        self.title_color = title_color
        self.title_size = title_size
        self.body_color = body_color
        self.body_size = body_size
        self.line_spacing = line_spacing

    @property
    def port_left(self) -> Tuple[float, float]:
        return (self.x, self.y + self.h / 2.0)

    @property
    def port_right(self) -> Tuple[float, float]:
        return (self.x + self.w, self.y + self.h / 2.0)

    @property
    def port_top(self) -> Tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h)

    @property
    def port_bottom(self) -> Tuple[float, float]:
        return (self.x + self.w / 2.0, self.y)

    def port_top_at(self, frac: float) -> Tuple[float, float]:
        return (self.x + self.w * frac, self.y + self.h)

    def port_bottom_at(self, frac: float) -> Tuple[float, float]:
        return (self.x + self.w * frac, self.y)

    def port_left_at(self, frac: float) -> Tuple[float, float]:
        return (self.x, self.y + self.h * frac)

    def port_right_at(self, frac: float) -> Tuple[float, float]:
        return (self.x + self.w, self.y + self.h * frac)

    def draw(self, ax: plt.Axes) -> None:
        patch = FancyBboxPatch(
            (self.x, self.y),
            self.w,
            self.h,
            boxstyle=f"round,pad=0.2,rounding_size={self.rounding}",
            facecolor=self.fc,
            edgecolor=self.ec,
            linewidth=self.lw,
            linestyle=self.ls,
            zorder=3,
        )
        ax.add_patch(patch)

        # Title position
        title_y = self.y + self.h - (2.8 if self.lines else self.h / 2.0)
        ax.text(
            self.x + self.w / 2.0,
            title_y,
            self.title,
            ha="center",
            va="center",
            fontsize=self.title_size,
            fontweight="bold",
            color=self.title_color,
            zorder=4,
        )

        # Body lines
        if self.lines:
            start_y = title_y - 2.8
            for i, line in enumerate(self.lines):
                cur_y = start_y - i * self.line_spacing
                ax.text(
                    self.x + self.w / 2.0,
                    cur_y,
                    line,
                    ha="center",
                    va="center",
                    fontsize=self.body_size,
                    color=self.body_color,
                    zorder=4,
                )


def draw_orthogonal_arrow(
    ax: plt.Axes,
    p_start: Tuple[float, float],
    p_end: Tuple[float, float],
    color: str = "#222222",
    lw: float = 1.3,
    mutation_scale: float = 11.0,
    rad: float = 0.0,
    armA: Optional[float] = None,
    armB: Optional[float] = None,
    angleA: float = 0,
    angleB: float = 90,
    connectionstyle: Optional[str] = None,
    zorder: int = 5,
) -> None:
    """Draws a clean orthogonal connection with right angles."""
    if connectionstyle is None:
        if p_start[0] == p_end[0] or p_start[1] == p_end[1]:
            conn = "arc3,rad=0.0"
        else:
            conn = f"angle,angleA={angleA},angleB={angleB},rad={rad}"
    else:
        conn = connectionstyle

    patch = FancyArrowPatch(
        p_start,
        p_end,
        connectionstyle=conn,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=lw,
        color=color,
        zorder=zorder,
    )
    ax.add_patch(patch)


# ==============================================================================
# FIGURE 1: TWO-STAGE MODULAR CLOUD-EDGE ARCHITECTURE (IMAGE 6 STYLE)
# ==============================================================================
def generate_figure_1_two_stage_architecture() -> None:
    """
    Renders Fig 1: Two-Stage Modular Cloud-Edge Systems Architecture.
    Matches Tran & Kim, FGCS '24, Fig. 2 (figures-reformating/6.png) with mathematical precision:
      - Left: SERVICE DEPLOYMENT STAGE (Online Continuum Serving)
      - Right: SERVICE PREPARATION STAGE (Offline Synthesis & Calibration)
      - Red Transfer Arrow bridging the two stages
      - Discrete bottom legend for proposed vs standard continuum components
    """
    fig, ax = plt.subplots(figsize=(15.2, 9.2), dpi=300)
    ax.set_xlim(0, 152)
    ax.set_ylim(0, 92)
    ax.axis("off")

    # Colors adhering to FGCS '24 Fig. 2 theme
    c_prop_bg = "#fffde7"       # Soft yellow for proposed additions
    c_prop_border = "#f57f17"   # Warm amber border
    c_infra_bg = "#eeeeee"      # Crisp neutral gray for infrastructure
    c_infra_border = "#424242"  # Charcoal border
    c_agent_bg = "#e3f2fd"      # Soft light blue for agents
    c_agent_border = "#1565c0"  # Deep blue border
    c_operator_bg = "#fce4ec"   # Soft rose pink for actuators
    c_operator_border = "#c2185b"
    c_calib_bg = "#e8f5e9"      # Mint green for calibration bank
    c_calib_border = "#2e7d32"

    # --------------------------------------------------------------------------
    # 1. LEFT STAGE: SERVICE DEPLOYMENT STAGE (ONLINE SERVING)
    # --------------------------------------------------------------------------
    # Outer frame
    frame_deploy = FancyBboxPatch(
        (4, 4), 84, 83,
        boxstyle="round,pad=0.2,rounding_size=1.5",
        facecolor="#ffffff", edgecolor="#111111", linewidth=1.5, zorder=1
    )
    ax.add_patch(frame_deploy)
    ax.text(46, 84.5, "SERVICE DEPLOYMENT STAGE\n(ONLINE CONTINUUM SERVING)",
            ha="center", va="center", fontsize=9.0, fontweight="bold", color="#c62828")

    # 1A. Upper Container: Proposed Solution Components (Light Yellow)
    cont_prop = FancyBboxPatch(
        (6, 45.5), 80, 36.5,
        boxstyle="round,pad=0.2,rounding_size=1.2",
        facecolor=c_prop_bg, edgecolor=c_prop_border, linewidth=1.2, zorder=2
    )
    ax.add_patch(cont_prop)
    ax.text(46, 79.5, "Proposed Solution: Conformal-Gated Edge-Cloud Control Plane",
            ha="center", va="center", fontsize=9.0, fontweight="bold", color="#e65100")

    # Card 1: Edge Gateway Tier
    card_edge = DiagramCard(
        x=8, y=47.5, w=35, h=29,
        title="Edge Gateway Tier\n(AWS c7i Compute Instance)",
        lines=[
            "Student Classifier: EfficientNet-B0 (10.7 ms)",
            "RAPS Conformal Triage Router (Adaptive alpha_t)",
            "|C(x)| = 1 -> Fast Local Inference (0 WAN)",
            "|C(x)| > 1 -> Cloud Offload Channel",
            "Zero-Lag Telemetry Streaming: v(t)",
        ],
        fc="#ffffff", ec="#1e88e5", lw=1.2, rounding=1.0,
        title_color="#0d47a1", title_size=8.2, body_color="#222222", body_size=6.9,
    )
    card_edge.draw(ax)

    # Card 2: Conformal-Gated Autoscaler (CGDA)
    card_cgda = DiagramCard(
        x=49, y=47.5, w=35, h=29,
        title="Conformal-Gated Autoscaler\n(Dual-Horizon Decision Engine)",
        lines=[
            "Phase 1: Conformal Derivative Preemption",
            "Dynamic Credit: B_t = B_max * tanh(gamma * |dp|)",
            "Preemption: delta_pre = ceil(lambda_slow / mu) - k(t)",
            "Phase 2: Capacity Stabilization & Hysteresis",
            "Target: k*(t) = ceil((lambda_slow + beta*q) / mu)",
            "Shared Lock: Booting Credit Register C_boot(t)",
        ],
        fc="#ffffff", ec=c_prop_border, lw=1.2, rounding=1.0,
        title_color="#b71c1c", title_size=8.2, body_color="#222222", body_size=6.8,
    )
    card_cgda.draw(ax)

    # 1B. Lower Container: Standard Continuum Infrastructure (Light Gray)
    cont_infra = FancyBboxPatch(
        (6, 6.5), 80, 32.5,
        boxstyle="round,pad=0.2,rounding_size=1.2",
        facecolor=c_infra_bg, edgecolor=c_infra_border, linewidth=1.2, zorder=2
    )
    ax.add_patch(cont_infra)
    ax.text(46, 36.5, "Heterogeneous Continuum Serving Substrate",
            ha="center", va="center", fontsize=9.0, fontweight="bold", color="#37474f")

    # Card 3: Edge Fast Sink
    card_sink = DiagramCard(
        x=8, y=8.5, w=22, h=25,
        title="Local Fast Sink\n(|C(x)| = 1)",
        lines=[
            "Zero WAN Propagation",
            "72% Nominal Traffic",
            "Edge Latency: 10.7 ms",
            "Defends 15s SLO at 100%",
        ],
        fc="#ffffff", ec="#2e7d32", lw=1.1, rounding=1.0,
        title_color="#1b5e20", title_size=7.8, body_color="#222222", body_size=6.6,
    )
    card_sink.draw(ax)

    # Card 4: WAN Transport & Ingress Queue
    card_wan = DiagramCard(
        x=34, y=8.5, w=24, h=25,
        title="WAN Ingress Buffer\n& Telemetry Channel",
        lines=[
            "WAN Delay: 25.0 ms",
            "Bandwidth: 1000 Mbps",
            "Queue Backlog: q(t)",
            "Prometheus Telemetry Sink",
            "Push-based epoch metrics",
        ],
        fc="#ffffff", ec="#8e24aa", lw=1.1, rounding=1.0,
        title_color="#4a148c", title_size=7.8, body_color="#222222", body_size=6.6,
    )
    card_wan.draw(ax)

    # Card 5: Cloud GPU Worker Pool
    card_gpu = DiagramCard(
        x=62, y=8.5, w=22, h=25,
        title="Cloud GPU Workers\n(NVIDIA Tesla T4)",
        lines=[
            "Teacher: ResNet-152",
            "Batching: b in [1, 32]",
            "Rate: mu = 16.0 RPS",
            "Startup: T_boot in [0.5, 300]s",
            "Actuation: Delta k_t pods",
        ],
        fc="#ffffff", ec="#0277bd", lw=1.1, rounding=1.0,
        title_color="#01579b", title_size=7.8, body_color="#222222", body_size=6.6,
    )
    card_gpu.draw(ax)

    # Internal Intra-Deployment Arrows (Passing cleanly through corridor y in [39, 45.5])
    # Edge -> Local Fast Sink
    draw_orthogonal_arrow(ax, card_edge.port_bottom_at(0.3), card_sink.port_top, color="#2e7d32", lw=1.4)
    ax.text(18.5, 42.0, "Fast Local Exit", fontsize=6.6, fontweight="bold", color="#2e7d32", ha="center")

    # Edge -> WAN Offload
    draw_orthogonal_arrow(ax, card_edge.port_bottom_at(0.8), card_wan.port_top_at(0.3), color="#8e24aa", lw=1.4)
    ax.text(36.0, 42.0, "Cloud Offload", fontsize=6.6, fontweight="bold", color="#8e24aa", ha="center")

    # Zero-lag telemetry: Edge -> CGDA
    draw_orthogonal_arrow(ax, card_edge.port_right, card_cgda.port_left, color="#0d47a1", lw=1.6)
    ax.text(46.0, 63.5, "Zero-Lag\nv(t)", fontsize=7.2, fontweight="bold", color="#0d47a1", ha="center")

    # Telemetry Feedback: WAN/Prometheus -> CGDA
    draw_orthogonal_arrow(ax, card_wan.port_top_at(0.75), card_cgda.port_bottom_at(0.25), color="#4a148c", lw=1.3)
    ax.text(54.0, 42.0, "Queue q(t)", fontsize=6.6, fontweight="bold", color="#4a148c", ha="center")

    # Scaling Actuation: CGDA -> Cloud GPU
    draw_orthogonal_arrow(ax, card_cgda.port_bottom_at(0.75), card_gpu.port_top, color="#c62828", lw=1.6)
    ax.text(75.2, 42.0, "Actuation Delta k_t", fontsize=6.8, fontweight="bold", color="#c62828", ha="center")


    # --------------------------------------------------------------------------
    # 2. RIGHT STAGE: SERVICE PREPARATION STAGE (OFFLINE SYNTHESIS)
    # --------------------------------------------------------------------------
    # Outer frame
    frame_prep = FancyBboxPatch(
        (102, 4), 46, 83,
        boxstyle="round,pad=0.2,rounding_size=1.5",
        facecolor="#ffffff", edgecolor="#111111", linewidth=1.5, zorder=1
    )
    ax.add_patch(frame_prep)
    ax.text(125, 84.5, "SERVICE PREPARATION STAGE\n(OFFLINE SYNTHESIS)",
            ha="center", va="center", fontsize=9.0, fontweight="bold", color="#0d47a1")

    # Inner Container: Evolutionary Synthesis (Light Yellow)
    cont_prep = FancyBboxPatch(
        (104, 6.5), 42, 74.5,
        boxstyle="round,pad=0.2,rounding_size=1.2",
        facecolor=c_prop_bg, edgecolor="#0288d1", linewidth=1.2, zorder=2
    )
    ax.add_patch(cont_prep)
    ax.text(125, 78.5, "OpenEvolve Symbolic Evolutionary Policy Search",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color="#01579b")

    # Card 6: Top Search Engine
    card_evo = DiagramCard(
        x=105.5, y=56.5, w=39, h=19.5,
        title="OpenEvolve Symbolic Search Engine",
        lines=[
            "Multi-Objective Pareto Evolutionary Search:",
            "min {Resource Cost (WS), SLA Violations, Churn}",
            "Discovers closed-form deterministic O(1) decision logic",
            "Synthesizes robust anti-thrashing credit lock",
        ],
        fc="#ffffff", ec="#f57f17", lw=1.2, rounding=1.0,
        title_color="#e65100", title_size=7.8, body_color="#222222", body_size=6.6,
    )
    card_evo.draw(ax)

    # Sub-Container: Empirical Calibration & Validation Testbed (Light Blue)
    cont_calib = FancyBboxPatch(
        (105.5, 8.5), 39, 42,
        boxstyle="round,pad=0.2,rounding_size=1.0",
        facecolor="#e1f5fe", edgecolor="#0277bd", linewidth=1.1, zorder=3
    )
    ax.add_patch(cont_calib)
    ax.text(125, 47.5, "Empirical Calibration & Validation Testbed",
            ha="center", va="center", fontsize=8.0, fontweight="bold", color="#01579b")

    # 2x2 Grid of White Sub-Cards inside Calibration Container
    card_g1 = DiagramCard(
        x=107.0, y=28.0, w=17.5, h=16.5,
        title="Workload Traces",
        lines=[
            "Azure 2019 Diurnal",
            "TinyImageNet-C",
            "Volume + Shock",
        ],
        fc="#ffffff", ec="#0288d1", lw=0.9, rounding=0.8,
        title_color="#01579b", title_size=7.2, body_color="#333333", body_size=6.4,
    )
    card_g1.draw(ax)

    card_g2 = DiagramCard(
        x=125.5, y=28.0, w=17.5, h=16.5,
        title="Hardware Profiles",
        lines=[
            "AWS c7i CPU",
            "Tesla T4 GPU",
            "Boot Ladder [0.5, 300]s",
        ],
        fc="#ffffff", ec="#00897b", lw=0.9, rounding=0.8,
        title_color="#004d40", title_size=7.2, body_color="#333333", body_size=6.4,
    )
    card_g2.draw(ax)

    card_g3 = DiagramCard(
        x=107.0, y=10.5, w=17.5, h=16.0,
        title="Conformal Risk",
        lines=[
            "RAPS Calibration",
            "Coverage: 1 - alpha",
            "Quantile q_hat",
        ],
        fc="#ffffff", ec="#7b1fa2", lw=0.9, rounding=0.8,
        title_color="#4a148c", title_size=7.2, body_color="#333333", body_size=6.4,
    )
    card_g3.draw(ax)

    card_g4 = DiagramCard(
        x=125.5, y=10.5, w=17.5, h=16.0,
        title="Evaluation Harness",
        lines=[
            "13 Benchmark Suites",
            "20-Seed Matching",
            "Multi-Tier Simulator",
        ],
        fc="#ffffff", ec="#c2185b", lw=0.9, rounding=0.8,
        title_color="#880e4f", title_size=7.2, body_color="#333333", body_size=6.4,
    )
    card_g4.draw(ax)

    # Vertical Arrow: Calibration Testbed -> Evolutionary Search (in corridor y in [50.5, 56.5])
    draw_orthogonal_arrow(ax, (125, 50.5), (125, 56.5), color="#01579b", lw=1.4)
    ax.text(125, 53.5, "Empirical Fitness Evaluation", fontsize=6.6, fontweight="bold", color="#01579b", ha="center")


    # --------------------------------------------------------------------------
    # 3. INTER-STAGE BOLD RED TRANSFER ARROW (IN CORRIDOR x in [88, 102])
    # --------------------------------------------------------------------------
    draw_orthogonal_arrow(
        ax,
        (105.5, 66.0),
        (84.0, 66.0),
        color="#d32f2f",
        lw=2.4,
        mutation_scale=16.0,
        zorder=6,
    )
    # Badge text atop the red arrow (floats completely in corridor [88, 102])
    bbox_trans = FancyBboxPatch(
        (88.5, 68.0), 12.0, 6.0,
        boxstyle="round,pad=0.2,rounding_size=0.8",
        facecolor="#ffffff", edgecolor="#d32f2f", linewidth=1.2, zorder=7
    )
    ax.add_patch(bbox_trans)
    ax.text(94.5, 71.0, "Policy Transfer\nArtifact",
            ha="center", va="center", fontsize=7.0, fontweight="bold", color="#b71c1c", zorder=8)


    # --------------------------------------------------------------------------
    # 4. BOTTOM LEGEND (MATCHING 6.PNG EXACTLY)
    # --------------------------------------------------------------------------
    leg_x = 10
    leg_y = 1.0

    # Swatch 1: Proposed solution
    ax.add_patch(FancyBboxPatch((leg_x, leg_y), 3.5, 2.0, boxstyle="round,pad=0.1,rounding_size=0.4",
                               facecolor=c_prop_bg, edgecolor=c_prop_border, linewidth=1.0))
    ax.text(leg_x + 4.5, leg_y + 1.0, "Proposed Solution Components (CGDA, Conformal Triage, OpenEvolve)",
            va="center", fontsize=7.6, color="#222222")

    # Swatch 2: Default continuum components
    ax.add_patch(FancyBboxPatch((leg_x + 78, leg_y), 3.5, 2.0, boxstyle="round,pad=0.1,rounding_size=0.4",
                               facecolor=c_infra_bg, edgecolor=c_infra_border, linewidth=1.0))
    ax.text(leg_x + 82.5, leg_y + 1.0, "Standard Continuum / Infrastructure Components (Kubernetes, GPU, Buffer)",
            va="center", fontsize=7.6, color="#222222")

    save_fig(fig, "fig1_system_architecture")
    plt.close()


# ==============================================================================
# FIGURE 2: CLOSED-LOOP CONTROL INTERACTION (IMAGE 5 STYLE)
# ==============================================================================
def generate_figure_control_loop() -> None:
    """
    Renders Fig 2: Closed-Loop Telemetry & Control Feedback Interaction.
    Matches Tran & Kim, FGCS '24, Fig. 3 (figures-reformating/5.png) with mathematical precision:
      - 3 Columns, 2 Vertical Nodes
      - Strict Orthogonal (90-degree right angle) Arrows
      - Zero Text Collisions and Generous Bounding Card Padding
    """
    fig, ax = plt.subplots(figsize=(11.5, 8.2), dpi=300)
    ax.set_xlim(0, 115)
    ax.set_ylim(0, 82)
    ax.axis("off")

    c_ctrl_bg = "#fffde7"
    c_ctrl_border = "#f57f17"
    c_env_bg = "#e8eaf6"
    c_env_border = "#283593"
    c_action_bg = "#e8f5e9"
    c_action_border = "#2e7d32"
    c_state_bg = "#ffffff"
    c_state_border = "#0277bd"
    c_reward_bg = "#ffebee"
    c_reward_border = "#c62828"

    # --- TOP NODE: CONFORMAL-GATED CONTROLLER ---
    card_top = DiagramCard(
        x=28, y=57.5, w=59, h=21,
        title="Decision Engine: Conformal-Gated Autoscaler (CGDA)",
        lines=[
            "Phase 1 (Fast Loop): Conformal Derivative Preemption",
            "B_t = B_max * tanh(gamma * |dp|),  delta_pre = ceil(lambda_slow / mu) - k(t)",
            "Phase 2 (Slow Loop): Capacity Re-Anchoring with Asymmetric Cooldown",
            "k*(t) = ceil((lambda_slow + beta * q) / mu),  tau_down >= 15.0 s",
            "Anti-Thrashing Mutual Exclusion: Credit Lock C_boot(t)",
        ],
        fc=c_ctrl_bg, ec=c_ctrl_border, lw=1.6, rounding=1.5,
        title_color="#e65100", title_size=9.2, body_color="#222222", body_size=7.5, line_spacing=2.6,
    )
    card_top.draw(ax)

    # --- CENTER NODE: STATE TELEMETRY S_t ---
    card_state = DiagramCard(
        x=30, y=30.0, w=55, h=19.5,
        title="State Telemetry (S_t)",
        lines=[
            "Zero-Lag Conformal Telemetry Vector:",
            "v(t) = < lambda(t), p_fast(t), p_dot_fast(t), c_bar(t), alpha_t >",
            "Cloud Backlog Queue Depth: q(t)  *  Active Cloud Workers: k(t)",
            "WAN Ingress Delay: delta_t_WAN = 25.0 ms",
        ],
        fc=c_state_bg, ec=c_state_border, lw=1.4, ls="--", rounding=1.2,
        title_color="#01579b", title_size=8.8, body_color="#222222", body_size=7.3, line_spacing=2.6,
    )
    card_state.draw(ax)

    # --- BOTTOM NODE: CLOUD-EDGE CONTINUUM ENVIRONMENT ---
    card_bot = DiagramCard(
        x=26, y=4.0, w=63, h=20,
        title="Cloud-Edge Continuum Serving Environment",
        lines=[
            "Edge Gateway: AWS c7i Compute Instance (EfficientNet-B0 Student, 10.7 ms)",
            "Conformal Gating: RAPS (|C(x)| = 1 -> Fast Exit, |C(x)| > 1 -> Cloud Offload)",
            "Cloud GPU Tier: NVIDIA Tesla T4 Pool (ResNet-152, Dynamic Batching b in [1, 32])",
            "Physical Startup Delay Ladder: T_boot in [0.5, 300] s",
        ],
        fc=c_env_bg, ec=c_env_border, lw=1.6, rounding=1.5,
        title_color="#1a237e", title_size=9.2, body_color="#222222", body_size=7.4, line_spacing=2.5,
    )
    card_bot.draw(ax)

    # --- LEFT NODE: REWARD / OBJECTIVE SIGNALS R_t ---
    card_reward = DiagramCard(
        x=3.5, y=28.5, w=22.5, h=22.5,
        title="Reward / Signals (R_t)",
        lines=[
            "SLA Violations",
            "(D_SLA = 15.0 s)",
            "Resource Cost (WS)",
            "Actuation Flapping",
            "Queue Saturation",
        ],
        fc=c_reward_bg, ec=c_reward_border, lw=1.4, ls="--", rounding=1.2,
        title_color="#b71c1c", title_size=8.5, body_color="#333333", body_size=7.0, line_spacing=2.6,
    )
    card_reward.draw(ax)

    # --- RIGHT NODE: ACTION A_t ---
    card_action = DiagramCard(
        x=89.0, y=28.5, w=22.5, h=22.5,
        title="Action (A_t)",
        lines=[
            "Scaling Delta: Delta k_t",
            "Pod Scale Up / Down",
            "Delta k_t in [-k_dn, +k_up]",
            "Register Lock C_boot",
            "Hysteresis Cooldown",
        ],
        fc=c_action_bg, ec=c_action_border, lw=1.4, ls="--", rounding=1.2,
        title_color="#1b5e20", title_size=8.5, body_color="#333333", body_size=7.0, line_spacing=2.6,
    )
    card_action.draw(ax)

    # --- STRICT ORTHOGONAL 90-DEGREE CONNECTIONS (MATCHING 5.PNG) ---
    # 1. Controller -> Action -> Environment (Green Path)
    # From top controller right edge, right then down to Action top
    draw_orthogonal_arrow(ax, (87, 68), (100.25, 51), color="#2e7d32", lw=1.8, angleA=0, angleB=90)
    ax.text(94, 71.5, "Actuation Decision", fontsize=7.2, fontweight="bold", color="#2e7d32", ha="center")

    # From Action bottom, down then left to Environment right edge
    draw_orthogonal_arrow(ax, (100.25, 28.5), (89, 14), color="#2e7d32", lw=1.8, angleA=-90, angleB=180)
    ax.text(97, 10.5, "Pod Scaling\nActuation", fontsize=7.2, fontweight="bold", color="#2e7d32", ha="center")

    # 2. Environment -> State -> Controller (Blue Path)
    # Environment top to State bottom
    draw_orthogonal_arrow(ax, (57.5, 24), (57.5, 30), color="#0277bd", lw=1.8)
    ax.text(64.5, 27.0, "Ingress Telemetry", fontsize=7.0, fontweight="bold", color="#0277bd", ha="left")

    # State top to Controller bottom
    draw_orthogonal_arrow(ax, (57.5, 49.5), (57.5, 57.5), color="#0277bd", lw=1.8)
    ax.text(64.5, 53.5, "Zero-Lag Signal v(t)", fontsize=7.0, fontweight="bold", color="#0277bd", ha="left")

    # 3. Environment -> Reward -> Controller (Red Path)
    # From Environment left, left then up to Reward bottom
    draw_orthogonal_arrow(ax, (26, 14), (14.75, 28.5), color="#c62828", lw=1.8, angleA=180, angleB=90)
    ax.text(18, 10.5, "QoS & Cost\nTelemetry", fontsize=7.2, fontweight="bold", color="#c62828", ha="center")

    # From Reward top, up then right to Controller left edge
    draw_orthogonal_arrow(ax, (14.75, 51), (28, 68), color="#c62828", lw=1.8, angleA=90, angleB=0)
    ax.text(21, 71.5, "Objective Feedback", fontsize=7.2, fontweight="bold", color="#c62828", ha="center")

    save_fig(fig, "fig_control_loop")
    plt.close()


def main() -> None:
    print("=" * 70)
    print("Generating Publication Architecture Figures (Images 5 & 6 Style)...")
    print("=" * 70)
    generate_figure_1_two_stage_architecture()
    generate_figure_control_loop()
    print("=" * 70)
    print("[SUCCESS] All architecture diagrams cleanly generated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
