#!/usr/bin/env python3
"""
scripts/render_cgda_explainer.py
3Blue1Brown-style Manim explainer video for CGDA with professional Jenny neural voiceover:
- Scene 1: The Complexity Blindness Paradox (Regime g: Flat ingress, triage collapses, offload surges)
- Scene 2: Mathematical Conformal Triage & Selective Accuracy (RAPS C(x), 97.66% selective top-1)
- Scene 3: Feed-Forward Conformal Derivative & Preemption (Δp(t) < -θ shock trigger)
- Scene 4: Dynamic Scaling: Preemption Eliminates Container Boot Lag (2-panel synchronized trajectory: Workers + P99 Latency vs SLO)
- Scene 5A: Boot Delay Ladder Benchmark (19,750 requests, 1s to 100s including 50s rung)
- Scene 5B: Universal Portability Across Modalities (Vision, SLM->LLM, VLM Cascades)
- Outro: Conformal-Gated Dual-Horizon Autoscaler
"""

from manim import *

# ── Color Palette & Aesthetic Constants ──────────────────────────────────────
BG_COLOR       = "#141414"
EDGE_COLOR     = "#83C167"  # Emerald Green
CLOUD_COLOR    = "#58C4DD"  # Cyan Blue
SHOCK_COLOR    = "#FF6B6B"  # Coral Red
ACCENT_COLOR   = "#FFD93D"  # Warm Gold
TEXT_COLOR     = "#EAEAEA"
MUTED_COLOR    = "#888888"
BOX_BG_COLOR   = "#1F1F1F"

class CGDAExplainer(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR

        # =====================================================================
        # SCENE 1: THE COMPLEXITY BLINDNESS PARADOX
        # =====================================================================
        title_s1 = Text("The Complexity Blindness Paradox", font_size=26, weight=BOLD, color=CLOUD_COLOR)
        subtitle_s1 = Text("Workload shifts semantically while aggregate ingress request rate λ(t) remains flat", font_size=15, color=MUTED_COLOR)
        header_s1 = VGroup(title_s1, subtitle_s1).arrange(DOWN, buff=0.12).to_edge(UP, buff=0.30)
        self.play(FadeIn(header_s1, shift=DOWN * 0.25), run_time=0.7)

        # Left: Workload Plot (Ingress vs Cloud Offload)
        ax1 = Axes(
            x_range=[0, 100, 20],
            y_range=[0, 120, 30],
            x_length=7.8,
            y_length=3.6,
            axis_config={"include_numbers": True, "font_size": 13, "color": MUTED_COLOR},
        ).move_to(LEFT * 2.3 + DOWN * 0.45)
        ax1_xlbl = ax1.get_x_axis_label(Text("Elapsed Time (s)", font_size=11, color=MUTED_COLOR), edge=DOWN, direction=DOWN).shift(DOWN * 0.15)
        ax1_ylbl = ax1.get_y_axis_label(Text("Rate (QPS)", font_size=11, color=MUTED_COLOR), edge=UP, direction=LEFT)
        plot_group1 = VGroup(ax1, ax1_xlbl, ax1_ylbl)
        self.play(FadeIn(plot_group1), run_time=0.6)

        # Ingress Curve λ(t) - Steady ~100 QPS with minor realistic jitter
        x_vals = [0, 15, 30, 40, 42, 60, 80, 100]
        y_ing  = [98, 102, 99, 100, 101, 99, 102, 100]
        curve_ing = ax1.plot_line_graph(x_values=x_vals, y_values=y_ing, line_color=TEXT_COLOR, stroke_width=2.5, vertex_dot_radius=0)

        # Cloud Offload Demand λ_slow(t): Nominal 28 QPS -> Spikes to 85 QPS at t=40s
        y_off  = [28, 30, 29, 30,  85,  84,  86,  85]
        curve_off = ax1.plot_line_graph(x_values=x_vals, y_values=y_off, line_color=CLOUD_COLOR, stroke_width=3.5, vertex_dot_radius=0)

        # Shaded fast-path absorption area
        poly_pts = [
            ax1.c2p(0, 28), ax1.c2p(15, 30), ax1.c2p(30, 29), ax1.c2p(40, 30),
            ax1.c2p(42, 85), ax1.c2p(60, 84), ax1.c2p(80, 86), ax1.c2p(100, 85),
            ax1.c2p(100, 100), ax1.c2p(80, 102), ax1.c2p(60, 99), ax1.c2p(42, 101),
            ax1.c2p(40, 100), ax1.c2p(30, 99), ax1.c2p(15, 102), ax1.c2p(0, 98),
        ]
        poly_fastpath = Polygon(*poly_pts, color=CLOUD_COLOR, fill_color=CLOUD_COLOR, fill_opacity=0.20, stroke_width=0)

        # Shock line at t=40s
        shock_v1 = DashedLine(ax1.c2p(40, 0), ax1.c2p(40, 115), color=SHOCK_COLOR, stroke_width=1.5)
        shock_lbl1 = Text("Semantic Shock\n(Triage Collapses)", font_size=11, color=SHOCK_COLOR, line_spacing=1.0).next_to(shock_v1, UP, buff=0.05)

        self.play(Create(curve_ing), Create(poly_fastpath), run_time=0.8)
        self.play(Create(shock_v1), FadeIn(shock_lbl1), Create(curve_off), run_time=0.8)

        # Right Callout Card: Problem Statement
        callout_s1_box = RoundedRectangle(corner_radius=0.15, width=4.5, height=3.8, fill_color=BOX_BG_COLOR, fill_opacity=0.92, stroke_color=SHOCK_COLOR, stroke_width=1.8).move_to(RIGHT * 4.4 + DOWN * 0.45)
        callout_title = Text("Why Autoscalers Fail", font_size=15, weight=BOLD, color=SHOCK_COLOR).move_to(callout_s1_box.get_top() + DOWN * 0.35)
        callout_b1 = Text("1. Total Ingress Rate λ(t) is Flat\n   • Volume scalers see 0 change\n   • No horizontal scaling triggered", font_size=12, color=TEXT_COLOR, line_spacing=1.2).next_to(callout_title, DOWN, buff=0.2, aligned_edge=LEFT).shift(RIGHT * 0.3)
        callout_b2 = Text("2. Semantic Drift Hits Edge\n   • Fast-path absorption collapses\n   • Cloud offload surges 3x (85 QPS)", font_size=12, color=TEXT_COLOR, line_spacing=1.2).next_to(callout_b1, DOWN, buff=0.15, aligned_edge=LEFT)
        callout_b3 = Text("3. Disaster: Queue Spike\n   • Unseen offload overflows buffer\n   • Cold-start lag misses SLA budget", font_size=12, color=ACCENT_COLOR, line_spacing=1.2).next_to(callout_b2, DOWN, buff=0.15, aligned_edge=LEFT)
        callout_s1 = VGroup(callout_s1_box, callout_title, callout_b1, callout_b2, callout_b3)
        self.play(FadeIn(callout_s1, shift=LEFT * 0.2), run_time=0.8)
        self.wait(13.17)

        # Clean Exit Scene 1
        self.play(
            FadeOut(header_s1), FadeOut(plot_group1), FadeOut(curve_ing),
            FadeOut(poly_fastpath), FadeOut(shock_v1), FadeOut(shock_lbl1),
            FadeOut(curve_off), FadeOut(callout_s1),
            run_time=0.6
        )
        self.wait(0.2)

        # =====================================================================
        # SCENE 2: MATHEMATICAL CONFORMAL TRIAGE & SELECTIVE ACCURACY
        # =====================================================================
        title_s2 = Text("Mathematical Conformal Triage & Selective Accuracy", font_size=25, weight=BOLD, color=CLOUD_COLOR)
        subtitle_s2 = Text("Guarantee statistical coverage while resolving simple queries locally at edge", font_size=15, color=MUTED_COLOR)
        header_s2 = VGroup(title_s2, subtitle_s2).arrange(DOWN, buff=0.12).to_edge(UP, buff=0.30)
        self.play(FadeIn(header_s2, shift=DOWN * 0.25), run_time=0.7)

        # Mathematical definition card
        def_box2 = RoundedRectangle(corner_radius=0.15, width=12.2, height=1.3, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=MUTED_COLOR, stroke_width=1.5)
        eq_def2 = MathTex(r"C(x) = \{\, y \in \mathcal{Y} : s(x, y) \le \hat{q} \,\}", font_size=22, color=TEXT_COLOR).move_to(def_box2.get_left() + RIGHT * 3.2)
        note_def2 = Text("RAPS calibrated on 5,000 images (q_hat = 0.79914)\nGuarantees 96.6% empirical test coverage under drift", font_size=12, color=MUTED_COLOR, line_spacing=1.1).move_to(def_box2.get_right() + LEFT * 3.4)
        def_card2 = VGroup(def_box2, eq_def2, note_def2).move_to(UP * 1.5)
        self.play(FadeIn(def_card2), run_time=0.7)

        # Dual branches: Singleton vs Ambiguous
        card_easy_box = RoundedRectangle(corner_radius=0.15, width=5.8, height=2.4, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=EDGE_COLOR, stroke_width=2.0)
        t_easy_title = Text("Confident Query: |C(x)| = 1", font_size=16, weight=BOLD, color=EDGE_COLOR).move_to(card_easy_box.get_top() + DOWN * 0.35)
        t_easy_math = MathTex(r"|C(x)| = 1 \implies \text{High Top-1 Accuracy}", font_size=16, color=ACCENT_COLOR).next_to(t_easy_title, DOWN, buff=0.15)
        t_easy_stats = Text("• Edge Selective Accuracy: 97.66% (Err: 2.34%)\n• 0 Cloud Cost • <1ms Local Edge Exit\n• Resolves nominal requests locally", font_size=13, color=TEXT_COLOR, line_spacing=1.2).next_to(t_easy_math, DOWN, buff=0.15)
        card_easy = VGroup(card_easy_box, t_easy_title, t_easy_math, t_easy_stats).move_to(LEFT * 3.2 + DOWN * 0.9)

        card_hard_box = RoundedRectangle(corner_radius=0.15, width=5.8, height=2.4, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=SHOCK_COLOR, stroke_width=2.0)
        t_hard_title = Text("Ambiguous Query: |C(x)| >= 2", font_size=16, weight=BOLD, color=SHOCK_COLOR).move_to(card_hard_box.get_top() + DOWN * 0.35)
        t_hard_math = MathTex(r"|C(x)| \ge 2 \implies \text{Offload to Cloud GPU}", font_size=16, color=CLOUD_COLOR).next_to(t_hard_title, DOWN, buff=0.15)
        t_hard_stats = Text("• Complex query forwarded over WAN\n• Local acceptance p(t) plummets\n• The Task: Alert cloud before queue builds!", font_size=13, color=TEXT_COLOR, line_spacing=1.2).next_to(t_hard_math, DOWN, buff=0.15)
        card_hard = VGroup(card_hard_box, t_hard_title, t_hard_math, t_hard_stats).move_to(RIGHT * 3.2 + DOWN * 0.9)

        self.play(FadeIn(card_easy, shift=RIGHT * 0.2), FadeIn(card_hard, shift=LEFT * 0.2), run_time=0.9)
        self.wait(14.50)

        # Clean Exit Scene 2
        self.play(FadeOut(header_s2), FadeOut(def_card2), FadeOut(card_easy), FadeOut(card_hard), run_time=0.6)
        self.wait(0.2)

        # =====================================================================
        # SCENE 3: FEED-FORWARD CONFORMAL DERIVATIVE & PREEMPTION
        # =====================================================================
        title_s3 = Text("Feed-Forward Conformal Derivative & Preemption", font_size=25, weight=BOLD, color=CLOUD_COLOR)
        subtitle_s3 = Text("Converting edge triage dynamics into proactive scaling commands", font_size=15, color=MUTED_COLOR)
        header_s3 = VGroup(title_s3, subtitle_s3).arrange(DOWN, buff=0.12).to_edge(UP, buff=0.30)
        self.play(FadeIn(header_s3, shift=DOWN * 0.25), run_time=0.7)

        # Telemetry Formula Card (Top)
        tele_box = RoundedRectangle(corner_radius=0.15, width=12.2, height=1.3, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=EDGE_COLOR, stroke_width=1.8).move_to(UP * 1.5)
        tele_math = MathTex(r"\Delta p(t) = \frac{p_{\text{fast}}(t) - p_{\text{fast}}(t - \Delta t)}{\Delta t} < -\theta_{\text{shock}}", font_size=20, color=EDGE_COLOR).move_to(tele_box.get_left() + RIGHT * 3.8)
        tele_note = Text("Derivative threshold triggers instant feed-forward preemption\nDispatched BEFORE requests cross WAN link into cloud queue", font_size=12, color=TEXT_COLOR, line_spacing=1.1).move_to(tele_box.get_right() + LEFT * 3.0)
        tele_card = VGroup(tele_box, tele_math, tele_note)
        self.play(FadeIn(tele_card), run_time=0.7)

        # Dual Loop Cards
        c_fast_box = RoundedRectangle(corner_radius=0.15, width=5.8, height=2.4, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=CLOUD_COLOR, stroke_width=1.8)
        t_fast_title = Text("Inner Fast Loop (Sub-Second)", font_size=15, weight=BOLD, color=CLOUD_COLOR).move_to(c_fast_box.get_top() + DOWN * 0.35)
        t_fast_desc = Text("• Sampling window Δt = 5.0s\n• Evaluates Δp(t) velocity in real time\n• Issues immediate preemption scale-out\n• Gains 5-10s head start over T_boot lag", font_size=12, color=TEXT_COLOR, line_spacing=1.2).next_to(t_fast_title, DOWN, buff=0.15)
        c_fast = VGroup(c_fast_box, t_fast_title, t_fast_desc).move_to(LEFT * 3.2 + DOWN * 0.9)

        c_slow_box = RoundedRectangle(corner_radius=0.15, width=5.8, height=2.4, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=ACCENT_COLOR, stroke_width=1.8)
        t_slow_title = Text("Outer Slow Loop (Macro Horizon)", font_size=15, weight=BOLD, color=ACCENT_COLOR).move_to(c_slow_box.get_top() + DOWN * 0.35)
        t_slow_desc = Text("• Stabilizes capacity: k*(t) = ⌈(λ + β q)/μ⌉\n• Asymmetric hysteresis prevents churn\n• Hardware Boot Credit C_boot prevents over-alloc\n• Zero actuator flapping in production", font_size=12, color=TEXT_COLOR, line_spacing=1.2).next_to(t_slow_title, DOWN, buff=0.15)
        c_slow = VGroup(c_slow_box, t_slow_title, t_slow_desc).move_to(RIGHT * 3.2 + DOWN * 0.9)

        self.play(FadeIn(c_fast, shift=RIGHT * 0.2), FadeIn(c_slow, shift=LEFT * 0.2), run_time=0.8)
        self.wait(12.63)

        # Clean Exit Scene 3
        self.play(FadeOut(header_s3), FadeOut(tele_card), FadeOut(c_fast), FadeOut(c_slow), run_time=0.6)
        self.wait(0.2)

        # =====================================================================
        # SCENE 4: DYNAMIC SCALING: PREEMPTION ELIMINATES BOOT LAG
        # =====================================================================
        title_s4 = Text("Dynamic Scaling: Preemption Eliminates Container Boot Lag", font_size=24, weight=BOLD, color=CLOUD_COLOR)
        subtitle_s4 = Text("Synchronized evaluation: active GPU workers & P99 latency tracking vs SLO budget", font_size=15, color=MUTED_COLOR)
        header_s4 = VGroup(title_s4, subtitle_s4).arrange(DOWN, buff=0.12).to_edge(UP, buff=0.30)
        self.play(FadeIn(header_s4, shift=DOWN * 0.25), run_time=0.7)

        # Top Plot: Active Workers k(t)
        ax_w = Axes(
            x_range=[0, 22, 5],
            y_range=[0, 18, 5],
            x_length=8.2,
            y_length=1.9,
            axis_config={"include_numbers": True, "font_size": 11, "color": MUTED_COLOR},
        ).move_to(LEFT * 2.3 + UP * 0.8)
        y_lbl_w = ax_w.get_y_axis_label(Text("Workers (k)", font_size=11, color=MUTED_COLOR), edge=UP, direction=LEFT)
        plot_w = VGroup(ax_w, y_lbl_w)

        # Shaded Boot Window for CGDA (t=2s to t=12s)
        boot_rect = Rectangle(
            width=ax_w.c2p(12, 0)[0] - ax_w.c2p(2, 0)[0],
            height=ax_w.c2p(0, 16)[1] - ax_w.c2p(0, 0)[1],
            fill_color=ACCENT_COLOR,
            fill_opacity=0.15,
            stroke_color=ACCENT_COLOR,
            stroke_width=1.0,
        ).move_to(ax_w.c2p(7, 8))
        boot_lbl = Text("Container Boot Window (T_boot = 10s)", font_size=10, color=ACCENT_COLOR).next_to(boot_rect, UP, buff=0.04)

        shock_v2 = DashedLine(ax_w.c2p(2, 0), ax_w.c2p(2, 17), color=SHOCK_COLOR, stroke_width=1.5)

        cgda_w = ax_w.plot_line_graph(x_values=[0, 2, 2.5, 12, 22], y_values=[4, 4, 14, 14, 14], line_color=EDGE_COLOR, stroke_width=3.2, vertex_dot_radius=0.05)
        near_w = ax_w.plot_line_graph(x_values=[0, 7, 7.5, 17.5, 22], y_values=[4, 4, 14, 14, 14], line_color=SHOCK_COLOR, stroke_width=2.8, vertex_dot_radius=0.05)

        self.play(FadeIn(plot_w), FadeIn(boot_rect), FadeIn(boot_lbl), Create(shock_v2), run_time=0.6)
        self.play(Create(cgda_w), Create(near_w), run_time=0.8)

        # Bottom Plot: End-to-End P99 Latency vs SLO Budget
        ax_l = Axes(
            x_range=[0, 22, 5],
            y_range=[0, 32, 10],
            x_length=8.2,
            y_length=1.9,
            axis_config={"include_numbers": True, "font_size": 11, "color": MUTED_COLOR},
        ).move_to(LEFT * 2.3 + DOWN * 1.55)
        x_lbl_l = ax_l.get_x_axis_label(Text("Elapsed Time (s)", font_size=11, color=MUTED_COLOR), edge=DOWN, direction=DOWN).shift(DOWN * 0.15)
        y_lbl_l = ax_l.get_y_axis_label(Text("P99 Latency (s)", font_size=11, color=MUTED_COLOR), edge=UP, direction=LEFT)
        plot_l = VGroup(ax_l, x_lbl_l, y_lbl_l)

        slo_line = DashedLine(ax_l.c2p(0, 15), ax_l.c2p(22, 15), color=ACCENT_COLOR, stroke_width=1.5)
        slo_lbl = Text("Service Level Objective (SLO = 15.0s)", font_size=10, color=ACCENT_COLOR).next_to(slo_line, UP, buff=0.04).shift(RIGHT * 1.5)

        cgda_l = ax_l.plot_line_graph(
            x_values=[0, 2, 5, 8, 12, 16, 22],
            y_values=[4.8, 4.9, 5.8, 5.5, 5.0, 4.8, 4.8],
            line_color=EDGE_COLOR,
            stroke_width=3.2,
            vertex_dot_radius=0.05,
        )
        near_l = ax_l.plot_line_graph(
            x_values=[0, 2, 5, 9, 12, 16, 17.5, 22],
            y_values=[4.8, 4.9, 12.0, 26.5, 28.0, 21.0, 14.5, 4.8],
            line_color=SHOCK_COLOR,
            stroke_width=2.8,
            vertex_dot_radius=0.05,
        )

        self.play(FadeIn(plot_l), Create(slo_line), FadeIn(slo_lbl), run_time=0.6)
        self.play(Create(cgda_l), Create(near_l), run_time=0.8)

        # Right Outcome Verdict Box
        verdict_box = RoundedRectangle(corner_radius=0.15, width=4.5, height=4.1, fill_color=BOX_BG_COLOR, fill_opacity=0.92, stroke_color=EDGE_COLOR, stroke_width=1.8).move_to(RIGHT * 4.4 + DOWN * 0.45)
        verdict_title = Text("Trajectory Outcome Verdict", font_size=14, weight=BOLD, color=ACCENT_COLOR).move_to(verdict_box.get_top() + DOWN * 0.35)
        
        t_cgda_head = Text("CGDA (Conformal-Gated):", font_size=12, weight=BOLD, color=EDGE_COLOR).next_to(verdict_title, DOWN, buff=0.2, aligned_edge=LEFT).shift(RIGHT * 0.3)
        t_cgda_b = Text("• Preempts at t = 2.0s\n• Ready at t = 12.0s (< SLO)\n• Max P99: 5.8s (< 15.0s budget)\n• 0 SLA Deadline Violations", font_size=11, color=TEXT_COLOR, line_spacing=1.15).next_to(t_cgda_head, DOWN, buff=0.1, aligned_edge=LEFT)

        t_near_head = Text("Nearest Reactive Scaler:", font_size=12, weight=BOLD, color=SHOCK_COLOR).next_to(t_cgda_b, DOWN, buff=0.18, aligned_edge=LEFT)
        t_near_b = Text("• Triggered at t = 7.5s (queue spike)\n• Ready at t = 17.5s (> SLO)\n• Max P99: 28.0s (Severe Spike)\n• 631 SLA Violations!", font_size=11, color=TEXT_COLOR, line_spacing=1.15).next_to(t_near_head, DOWN, buff=0.1, aligned_edge=LEFT)

        verdict_group = VGroup(verdict_box, verdict_title, t_cgda_head, t_cgda_b, t_near_head, t_near_b)
        self.play(FadeIn(verdict_group, shift=LEFT * 0.2), run_time=0.7)
        self.wait(14.83)

        # Clean Exit Scene 4
        self.play(
            FadeOut(header_s4), FadeOut(plot_w), FadeOut(boot_rect), FadeOut(boot_lbl),
            FadeOut(shock_v2), FadeOut(cgda_w), FadeOut(near_w),
            FadeOut(plot_l), FadeOut(slo_line), FadeOut(slo_lbl),
            FadeOut(cgda_l), FadeOut(near_l), FadeOut(verdict_group),
            run_time=0.6
        )
        self.wait(0.2)

        # =====================================================================
        # SCENE 5A: BOOT DELAY LADDER BENCHMARK
        # =====================================================================
        title_s5a = Text("Boot Delay Ladder Benchmark (19,750 Requests)", font_size=25, weight=BOLD, color=CLOUD_COLOR)
        subtitle_s5a = Text("Stress testing across container cold-start delay T_boot in [1, 100]s", font_size=15, color=MUTED_COLOR)
        header_s5a = VGroup(title_s5a, subtitle_s5a).arrange(DOWN, buff=0.12).to_edge(UP, buff=0.30)
        self.play(FadeIn(header_s5a, shift=DOWN * 0.25), run_time=0.7)

        # Table Headers
        th_boot = Text("Startup Lag (T_boot)", font_size=13, weight=BOLD, color=MUTED_COLOR).move_to(LEFT * 4.5 + UP * 1.7)
        th_cgda = Text("CGDA (Proposed)", font_size=13, weight=BOLD, color=EDGE_COLOR).move_to(LEFT * 2.0 + UP * 1.7)
        th_pred = Text("Nearest Predictive", font_size=13, weight=BOLD, color=TEXT_COLOR).move_to(RIGHT * 0.3 + UP * 1.7)
        th_react = Text("Reactive (CPU/Queue)", font_size=13, weight=BOLD, color=MUTED_COLOR).move_to(RIGHT * 2.6 + UP * 1.7)
        th_verdict = Text("Relative Outcome", font_size=13, weight=BOLD, color=ACCENT_COLOR).move_to(RIGHT * 5.0 + UP * 1.7)
        table_headers = VGroup(th_boot, th_cgda, th_pred, th_react, th_verdict)
        self.play(FadeIn(table_headers), run_time=0.5)

        # Ladder Rows: (T_boot, CGDA, Predictive, Reactive, Note)
        ladder_data = [
            ("1.0 s",   "0 misses", "0 misses",   "5 - 89",    "Competitive in nominal setting"),
            ("5.0 s",   "0 misses", "77 misses",  "6 - 69",    "Predictive begins failing"),
            ("10.0 s",  "0 misses", "631 misses", "110 - 339", "CGDA maintains 0 misses"),
            ("20.0 s",  "232",      "1,393",      "1,246+",    "83.3% Miss Reduction (T > D_SLA)"),
            ("50.0 s",  "1,328",    "2,174",      "4,000+",    "38.9% Reduction vs Predictive"),
            ("100.0 s", "2,176*",   "2,176*",     "8,000+",    "*Physical saturation boundary"),
        ]

        ladder_group = VGroup()
        for idx, (t_b, c_m, p_m, r_m, note) in enumerate(ladder_data):
            is_highlight = (idx in [2, 3])
            box_bg = EDGE_COLOR if idx == 2 else (ACCENT_COLOR if idx == 3 else BOX_BG_COLOR)
            stroke_col = ACCENT_COLOR if is_highlight else MUTED_COLOR
            stroke_w = 2.0 if is_highlight else 1.0

            r_box = RoundedRectangle(corner_radius=0.10, width=12.2, height=0.54, fill_color=box_bg, fill_opacity=0.3 if is_highlight else 0.8, stroke_color=stroke_col, stroke_width=stroke_w)
            
            t_col1 = Text(t_b, font_size=12, weight=BOLD if is_highlight else NORMAL, color=TEXT_COLOR).move_to(LEFT * 4.5)
            t_col2 = Text(c_m, font_size=12, weight=BOLD, color=EDGE_COLOR).move_to(LEFT * 2.0)
            t_col3 = Text(p_m, font_size=12, color=SHOCK_COLOR if "miss" in p_m or p_m in ["1,393", "2,174"] else TEXT_COLOR).move_to(RIGHT * 0.3)
            t_col4 = Text(r_m, font_size=12, color=SHOCK_COLOR if "+" in r_m or "-" in r_m else MUTED_COLOR).move_to(RIGHT * 2.6)
            t_col5 = Text(note, font_size=11, weight=BOLD if is_highlight else NORMAL, color=ACCENT_COLOR if is_highlight else MUTED_COLOR).move_to(RIGHT * 5.0)

            row_vg = VGroup(r_box, t_col1, t_col2, t_col3, t_col4, t_col5)
            ladder_group.add(row_vg)

        ladder_group.arrange(DOWN, buff=0.08).move_to(DOWN * 0.40)
        for row in ladder_group:
            box = row[0]
            for elem in row[1:]:
                elem.match_y(box)

        for row in ladder_group:
            self.play(FadeIn(row, shift=UP * 0.08), run_time=0.20)

        note_guarantee = Text("*Note: Zero misses physically impossible when T_boot > D_SLA (15s); CGDA provides superior damage mitigation.", font_size=11, color=ACCENT_COLOR).next_to(ladder_group, DOWN, buff=0.18)
        self.play(FadeIn(note_guarantee), run_time=0.5)
        self.wait(12.72)

        # Clean Exit Scene 5A
        self.play(FadeOut(header_s5a), FadeOut(table_headers), FadeOut(ladder_group), FadeOut(note_guarantee), run_time=0.6)
        self.wait(0.2)

        # =====================================================================
        # SCENE 5B: UNIVERSAL PORTABILITY ACROSS MODALITIES
        # =====================================================================
        title_s5b = Text("Universal Portability Across Modalities", font_size=25, weight=BOLD, color=CLOUD_COLOR)
        subtitle_s5b = Text("How conformal triage branches to SLM->LLM and Edge->Cloud VLM cascades", font_size=15, color=MUTED_COLOR)
        header_s5b = VGroup(title_s5b, subtitle_s5b).arrange(DOWN, buff=0.12).to_edge(UP, buff=0.30)
        self.play(FadeIn(header_s5b, shift=DOWN * 0.25), run_time=0.7)

        # 3 Branching Cards side-by-side
        # Card 1: Vision (Evaluated)
        b1_box = RoundedRectangle(corner_radius=0.15, width=3.8, height=3.6, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=EDGE_COLOR, stroke_width=2.0)
        b1_title = Text("1. Vision Triage\n(Evaluated Baseline)", font_size=14, weight=BOLD, color=EDGE_COLOR, line_spacing=1.1).move_to(b1_box.get_top() + DOWN * 0.45)
        b1_models = Text("Edge: EfficientNet-B0 (5.3M)\nCloud: ResNet-152 (11.5B)", font_size=12, color=TEXT_COLOR, line_spacing=1.2).next_to(b1_title, DOWN, buff=0.2)
        b1_metric_lbl = Text("Equivalent Metric:", font_size=12, weight=BOLD, color=ACCENT_COLOR).next_to(b1_models, DOWN, buff=0.2)
        b1_metric = MathTex(r"|C(x)| \le \hat{q}", font_size=16, color=EDGE_COLOR).next_to(b1_metric_lbl, DOWN, buff=0.1)
        b1_desc = Text("Discrete multi-class set.\nSingleton = Local Edge Top-1.", font_size=11, color=MUTED_COLOR, line_spacing=1.1).next_to(b1_metric, DOWN, buff=0.15)
        card_b1 = VGroup(b1_box, b1_title, b1_models, b1_metric_lbl, b1_metric, b1_desc).move_to(LEFT * 4.2 + DOWN * 0.5)

        # Card 2: SLM -> LLM (Generative)
        b2_box = RoundedRectangle(corner_radius=0.15, width=3.8, height=3.6, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=CLOUD_COLOR, stroke_width=2.0)
        b2_title = Text("2. SLM -> LLM\n(Generative Cascade)", font_size=14, weight=BOLD, color=CLOUD_COLOR, line_spacing=1.1).move_to(b2_box.get_top() + DOWN * 0.45)
        b2_models = Text("Edge: Llama-3.2-1B / Qwen-1.5B\nCloud: Llama-3.3-70B / DeepSeek", font_size=12, color=TEXT_COLOR, line_spacing=1.2).next_to(b2_title, DOWN, buff=0.2)
        b2_metric_lbl = Text("Equivalent Metric:", font_size=12, weight=BOLD, color=ACCENT_COLOR).next_to(b2_models, DOWN, buff=0.2)
        b2_metric = MathTex(r"\mathcal{H}_{\text{semantic}}(x) \le \tau", font_size=16, color=CLOUD_COLOR).next_to(b2_metric_lbl, DOWN, buff=0.1)
        b2_desc = Text("Semantic Entropy / CRC.\nLow dispersion = Local Text.", font_size=11, color=MUTED_COLOR, line_spacing=1.1).next_to(b2_metric, DOWN, buff=0.15)
        card_b2 = VGroup(b2_box, b2_title, b2_models, b2_metric_lbl, b2_metric, b2_desc).move_to(ORIGIN + DOWN * 0.5)

        # Card 3: Edge VLM -> Cloud VLM
        b3_box = RoundedRectangle(corner_radius=0.15, width=3.8, height=3.6, fill_color=BOX_BG_COLOR, fill_opacity=0.9, stroke_color=ACCENT_COLOR, stroke_width=2.0)
        b3_title = Text("3. Edge -> Cloud VLM\n(Multimodal Cascade)", font_size=14, weight=BOLD, color=ACCENT_COLOR, line_spacing=1.1).move_to(b3_box.get_top() + DOWN * 0.45)
        b3_models = Text("Edge: SmolVLM-2B / PaliGemma\nCloud: Qwen2-VL-72B", font_size=12, color=TEXT_COLOR, line_spacing=1.2).next_to(b3_title, DOWN, buff=0.2)
        b3_metric_lbl = Text("Equivalent Metric:", font_size=12, weight=BOLD, color=ACCENT_COLOR).next_to(b3_models, DOWN, buff=0.2)
        b3_metric = MathTex(r"\mathcal{R}_{\text{cross-modal}} \le \hat{q}", font_size=16, color=ACCENT_COLOR).next_to(b3_metric_lbl, DOWN, buff=0.1)
        b3_desc = Text("Conformal Risk Control.\nVisual QA = Local Camera.", font_size=11, color=MUTED_COLOR, line_spacing=1.1).next_to(b3_metric, DOWN, buff=0.15)
        card_b3 = VGroup(b3_box, b3_title, b3_models, b3_metric_lbl, b3_metric, b3_desc).move_to(RIGHT * 4.2 + DOWN * 0.5)

        branch_cards = VGroup(card_b1, card_b2, card_b3)
        self.play(FadeIn(branch_cards, shift=UP * 0.2), run_time=1.0)

        portability_footer = Text("Transferable: Controller only consumes dimensionless scalar telemetry p(t) and Δp(t).\nCritical for 100-300s LLM weight restoration delays (ServerlessLLM).", font_size=12, color=TEXT_COLOR, line_spacing=1.1).to_edge(DOWN, buff=0.25)
        self.play(FadeIn(portability_footer), run_time=0.6)
        self.wait(11.42)

        # Final Outro
        self.play(FadeOut(branch_cards), FadeOut(header_s5b), FadeOut(portability_footer), run_time=0.6)

        final_title = Text("Conformal-Gated Dual-Horizon Autoscaler", font_size=30, weight=BOLD, color=CLOUD_COLOR)
        final_sub = Text("Eliminating Complexity Blindness in Edge-Cloud Inference", font_size=18, color=EDGE_COLOR)
        final_meta = Text("Independent Personal Research Project • Publication Underway", font_size=14, color=MUTED_COLOR)
        outro_group = VGroup(final_title, final_sub, final_meta).arrange(DOWN, buff=0.25).move_to(ORIGIN)

        self.play(FadeIn(outro_group, scale=1.05), run_time=0.9)
        self.wait(6.08)
        self.play(FadeOut(outro_group), run_time=0.6)
        self.wait(0.3)
