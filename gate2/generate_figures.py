"""
generate_gate2_figures.py
Regenerates Figure 2 for both hardware pathways using the corrected
scrutiny-fixed data (queuing-aware, updated fractions, jitter, W_batch).
"""
import json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

# Universal data model injection
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.cross_gate_registry import load_registry
try:
    reg = load_registry()
except FileNotFoundError:
    from core.cross_gate_registry import CrossGateRegistry
    reg = CrossGateRegistry(fast_path_frac=0.5, cpu_mean_ms=10.0, cpu_std_ms=1.0, b8_p50_ms=1000.0)

MODELS       = ['q1', 'q2', 'q3', 'q4']
BATCH_SIZES  = reg.batch_sizes
CPU_MEAN_MS  = float(getattr(reg, "cpu_mean_ms", 10.7))
CPU_STD_MS   = float(getattr(reg, "cpu_std_ms", 1.2))
QUEUE_UTILS  = [0.30, 0.70, 0.95]

def load(profile_path, spearman_path):
    with open(profile_path) as f: profiles = json.load(f)
    with open(spearman_path) as f: spearman = json.load(f)
    return profiles, spearman

def make_figure(profiles, spearman, hardware_label, out_path):
    raw = profiles["gpu_profiles_raw"]
    rs_by_rho = spearman["results_by_queue_utilization"]

    # ── Layout: 3 heatmap panels + 1 degradation curve
    fig = plt.figure(figsize=(20, 5.5))
    fig.patch.set_facecolor("#0f1117")
    gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.35)

    pct_keys   = ["p50_ms", "p95_ms", "p99_ms"]
    pct_labels = ["p50 Latency (ms)", "p95 Latency (ms)", "p99 Latency (ms)"]
    bin_labels = ["|C|=1\n(Fast, CPU)", "|C|=2\n(Slow)", "|C|=3-5\n(Slow)", "|C|>5\n(Slow)"]

    for ax_idx, (pkey, plabel) in enumerate(zip(pct_keys, pct_labels)):
        ax = fig.add_subplot(gs[0, ax_idx])
        ax.set_facecolor("#1a1d27")

        matrix = np.zeros((4, len(BATCH_SIZES)))
        for col_idx, p in enumerate(raw):
            if pkey == "p50_ms":
                matrix[0, col_idx] = CPU_MEAN_MS
            elif pkey == "p95_ms":
                matrix[0, col_idx] = CPU_MEAN_MS + 2.0 * CPU_STD_MS
            else:
                matrix[0, col_idx] = CPU_MEAN_MS + 2.5 * CPU_STD_MS
            for row in range(1, 4):
                matrix[row, col_idx] = p[pkey]

        im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", vmin=0,
                       interpolation="nearest")

        ax.set_xticks(range(len(BATCH_SIZES)))
        ax.set_xticklabels([f"b={b}" for b in BATCH_SIZES],
                           fontsize=8, color="white")
        ax.set_yticks(range(4))
        ax.set_yticklabels(bin_labels, fontsize=7.5, color="white")
        ax.set_title(plabel, fontsize=9, color="white", pad=6)
        ax.set_xlabel("Batch Size b", fontsize=8, color="#aaaaaa")
        if ax_idx == 0:
            ax.set_ylabel("Set-Size Bin (q)\n"
                          "[ NOTE: q2/q3/q4 identical — constant FLOPs ]",
                          fontsize=7, color="#aaaaaa")

        for r in range(4):
            for c in range(len(BATCH_SIZES)):
                val = matrix[r, c]
                tc  = "white" if val > matrix.max() * 0.55 else "#111111"
                ax.text(c, r, f"{val:.0f}", ha="center", va="center",
                        fontsize=6.5, color=tc, fontweight="bold")

        cb = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
        cb.ax.tick_params(colors="white", labelsize=7)
        cb.set_label("ms", color="white", fontsize=7)

        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

    # ── Panel 4: r_s vs rho degradation curve
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.set_facecolor("#1a1d27")

    rho_vals = sorted(float(k) for k in rs_by_rho.keys())
    rs_vals  = [rs_by_rho[str(rho)]["r_s"] for rho in rho_vals]
    ov_vals  = [rs_by_rho[str(rho)]["fast_slow_overlap_frac"] for rho in rho_vals]

    ax4.plot(rho_vals, rs_vals, "o-", color="#4fc3f7", linewidth=2.5,
             markersize=9, zorder=3, label="Spearman $r_s$")
    ax4.fill_between(rho_vals, [0.40] * 3, rs_vals, alpha=0.12, color="#4fc3f7")
    ax4.axhline(y=0.40, color="#ef5350", linestyle="--", linewidth=1.8,
                label="Gate threshold ($r_s = 0.40$)", zorder=2)

    # Overlay overlap fraction on secondary axis
    ax4b = ax4.twinx()
    ax4b.plot(rho_vals, ov_vals, "s--", color="#ffb74d", linewidth=1.8,
              markersize=7, alpha=0.85, label="Fast/Slow overlap")
    ax4b.set_ylabel("Fast/Slow latency overlap fraction",
                    fontsize=7.5, color="#ffb74d")
    ax4b.tick_params(colors="#ffb74d", labelsize=7)
    ax4b.set_ylim(0, 0.6)

    for rho, rs in zip(rho_vals, rs_vals):
        ax4.annotate(f"$r_s$={rs:.3f}", (rho, rs),
                     textcoords="offset points", xytext=(4, 8),
                     fontsize=8, color="white",
                     arrowprops=dict(arrowstyle="-", color="#555", lw=0.8))

    ax4.set_xlabel("Queue Utilization ρ (M/M/1)", fontsize=9, color="#aaaaaa")
    ax4.set_ylabel("Spearman $r_s$", fontsize=9, color="white")
    ax4.set_title("Fix A: $r_s$ Graceful Degradation\nunder Queue Congestion",
                  fontsize=9, color="white", pad=6)
    ax4.set_ylim(0.5, 1.0)
    ax4.set_xlim(0.2, 1.05)
    ax4.tick_params(colors="white", labelsize=8)
    for spine in ax4.spines.values():
        spine.set_edgecolor("#444")

    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4b.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2,
               fontsize=7, loc="lower left",
               facecolor="#1a1d27", edgecolor="#555", labelcolor="white")

    # ── Suptitle
    fig.suptitle(
        f"Figure 2 — Gate 2 Service Time Surface & Spearman Correlation  |  {hardware_label}\n"
        "Scrutiny-hardened: queuing-aware $r_s$ · batch-formation delay · 5% GPU jitter · constant-FLOP disclosed",
        fontsize=10.5, color="white", fontweight="bold", y=1.01
    )

    fig.savefig(out_path, dpi=160, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Saved -> {out_path}")

if __name__ == "__main__":
    print("Generating Gate 2 figures...")

    t4_prof = os.path.join(REPO_ROOT, "gate2", "output-gpu-t4", "triton_service_profiles.json")
    t4_sp   = os.path.join(REPO_ROOT, "gate2", "output-gpu-t4", "gate2_spearman_result.json")
    t4_fig  = os.path.join(REPO_ROOT, "gate2", "output-gpu-t4", "figure2_profiling_surface.png")

    t4_profiles, t4_spearman = load(t4_prof, t4_sp)
    make_figure(t4_profiles, t4_spearman,
                "Tesla T4 GPU (Colab/Kaggle · CUDA 12.x)",
                t4_fig)

    cpu_prof = os.path.join(REPO_ROOT, "gate2", "output-cpu-c7i", "triton_service_profiles.json")
    cpu_sp   = os.path.join(REPO_ROOT, "gate2", "output-cpu-c7i", "gate2_spearman_result.json")
    cpu_fig  = os.path.join(REPO_ROOT, "gate2", "output-cpu-c7i", "figure2_profiling_surface.png")

    cpu_profiles, cpu_spearman = load(cpu_prof, cpu_sp)
    make_figure(cpu_profiles, cpu_spearman,
                "AWS c7i-flex.large CPU (PyTorch CPU-only)",
                cpu_fig)

    print("Done.")
