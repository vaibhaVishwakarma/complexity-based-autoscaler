"""
gate2_recompute_spearman.py
Reads existing profiling JSONs (old or new format) and recomputes
the queuing-aware Spearman r_s at rho=[0.3, 0.7, 0.95].
Saves updated gate2_spearman_result.json for each pathway.
"""
import json, math, sys
import numpy as np
from scipy import stats
import os

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

SEED             = reg.random_seed
BLOCK_SIZE       = reg.window_size
CORRELATION_TYPE = "spearman"
# Fix C: Updated from 0.3827 (T=0.70) to 0.50 (Gate 1 T=1.0 RAPS actual)
FAST_PATH_FRAC   = float(getattr(reg, "fast_path_frac", 0.50))
BIN_FRACS        = {1: FAST_PATH_FRAC, 2: 0.05, 3: 0.10, 4: round(max(0.0, 1.0 - FAST_PATH_FRAC - 0.15), 4)}
BATCH_DIST       = {1: 0.05, 2: 0.10, 4: 0.25, 8: 0.35, 16: 0.20, 32: 0.05}
CPU_MEAN_MS      = float(getattr(reg, "cpu_mean_ms", 10.7))
CPU_STD_MS       = float(getattr(reg, "cpu_std_ms", 1.2))
JITTER_CV        = 0.05
ARRIVAL_RATE_RPS = 50.0
QUEUE_UTILS      = [0.3, 0.7, 0.95]
N_REQUESTS       = 25_000

def compute_spearman(profiles_raw, hardware_name):
    rng = np.random.default_rng(SEED)

    # Build latency lookups — support both old and new format
    lat_by_b, jitter_by_b, wbatch_by_b = {}, {}, {}
    for p in profiles_raw:
        b = p["batch_size"]
        lat_by_b[b]    = p["p50_ms"]
        # New format has these; old format: compute from p50
        jitter_by_b[b] = p.get("jitter_sigma_ms",  p["p50_ms"] * JITTER_CV)
        wbatch_by_b[b] = p.get("batch_formation_wait_ms_mean",
                                (b - 1) / ARRIVAL_RATE_RPS * 1000.0)

    batch_values = list(BATCH_DIST.keys())
    batch_probs  = np.array([BATCH_DIST[b] for b in batch_values], dtype=np.float64)
    batch_probs /= batch_probs.sum()

    bin_set_sizes = [1, 2, 4, 10]
    bin_fracs_arr = np.array([BIN_FRACS[k] for k in [1,2,3,4]], dtype=np.float64)
    bin_fracs_arr /= bin_fracs_arr.sum()

    bin_assignments = rng.choice(len(bin_set_sizes), size=N_REQUESTS, p=bin_fracs_arr)

    # Mean slow-path latency for M/M/1 service rate
    mean_slow_ms = sum(BATCH_DIST[b] * lat_by_b[b] for b in batch_values) / sum(BATCH_DIST.values())
    mu_per_sec   = 1000.0 / mean_slow_ms

    results_by_rho = {}
    for rho in QUEUE_UTILS:
        mean_Wq_ms = (rho / (mu_per_sec * (1.0 - rho)) * 1000.0) if rho < 1.0 else 5000.0

        set_sizes  = np.zeros(N_REQUESTS)
        t_services = np.zeros(N_REQUESTS)

        for i in range(N_REQUESTS):
            c_size = bin_set_sizes[int(bin_assignments[i])]
            set_sizes[i] = float(c_size)
            Wq_i = float(rng.exponential(scale=max(mean_Wq_ms, 0.01)))

            if c_size == 1:
                base = max(1.0, float(rng.normal(CPU_MEAN_MS, CPU_STD_MS)))
                t_services[i] = base + (Wq_i * 0.1 if rho > 0.7 else 0.0)
            else:
                b_i     = int(rng.choice(batch_values, p=batch_probs))
                jitter  = float(rng.normal(0.0, jitter_by_b[b_i]))
                w_batch = wbatch_by_b[b_i]
                t_services[i] = max(1.0, lat_by_b[b_i] + jitter + w_batch + Wq_i)

        r_s, p_value = stats.spearmanr(set_sizes, t_services)
        r_s, p_value = float(r_s), float(p_value)
        t_stat = r_s * math.sqrt(N_REQUESTS - 2) / math.sqrt(max(1 - r_s**2, 1e-12))
        gate_pass = bool(r_s > 0.40 and p_value < 0.001)

        fast_mask = (set_sizes == 1)
        slow_mask = ~fast_mask
        overlap   = float(np.mean(t_services[fast_mask] > np.percentile(t_services[slow_mask], 5))) \
                    if slow_mask.sum() > 0 else 0.0

        results_by_rho[rho] = {
            "queue_utilization_rho":  rho,
            "mean_Wq_ms":             round(mean_Wq_ms, 3),
            "r_s":                    r_s,
            "p_value":                p_value,
            "t_statistic":            float(t_stat),
            "n_samples":              N_REQUESTS,
            "gate_pass":              gate_pass,
            "fast_slow_overlap_frac": overlap,
            "fast_path_mean_ms":      float(np.mean(t_services[fast_mask])),
            "slow_path_mean_ms":      float(np.mean(t_services[slow_mask])),
        }

    return {
        "hardware":            hardware_name,
        "n_requests":          N_REQUESTS,
        "fast_path_frac":      FAST_PATH_FRAC,
        "bin_fracs":           BIN_FRACS,
        "batch_dist":          BATCH_DIST,
        "jitter_cv":           JITTER_CV,
        "arrival_rate_rps":    ARRIVAL_RATE_RPS,
        "results_by_queue_utilization": results_by_rho,
        "gate_pass_all_rho":   all(v["gate_pass"] for v in results_by_rho.values()),
        "gate_pass_rho_0_7":   results_by_rho[0.7]["gate_pass"],
        "constant_flop_disclosure": (
            "ResNet-152 has 11.56B FLOPs regardless of input. "
            "q2/q3/q4 share identical execution latency per batch size b. "
            "Set-size signal is in routing decision only."
        ),
        "scrutiny_fixes": {
            "fix_A_queuing":       "M/M/1 queue model at rho=[0.3, 0.7, 0.95]",
            "fix_B_constant_flop": "Disclosed — q2/q3/q4 identical by design",
            "fix_C_fp_frac":       "Updated 0.3827→0.50 (Gate 1 T=1.0 RAPS actual)",
            "fix_D_batch_wait":    f"W_batch=(b-1)/lambda*1000ms at lambda={ARRIVAL_RATE_RPS}rps",
            "fix_E_jitter":        f"Gaussian sigma={JITTER_CV*100}% of p50 added to slow-path",
            "fix_F_monotonicity":  "Verified in profile_triton_service.py assert_monotonicity()",
        },
    }

def process(profile_path, out_path, label):
    print(f"\n{'='*60}")
    print(f"Processing: {label}")
    print(f"  Profile: {profile_path}")

    with open(profile_path) as f:
        data = json.load(f)

    profiles_raw = data.get("gpu_profiles_raw", [])
    hardware     = data.get("hardware", label)

    if not profiles_raw:
        print("  ERROR: no gpu_profiles_raw found"); return

    # Monotonicity check
    for i in range(len(profiles_raw) - 1):
        b0, b1 = profiles_raw[i], profiles_raw[i+1]
        if b1["p50_ms"] <= b0["p50_ms"]:
            print(f"  MONOTONICITY FAIL: b={b1['batch_size']} p50={b1['p50_ms']:.2f} "
                  f"<= b={b0['batch_size']} p50={b0['p50_ms']:.2f}")
            return
    print("  [MONOTONICITY] PASS")

    result = compute_spearman(profiles_raw, hardware)

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Saved -> {out_path}")

    for rho in QUEUE_UTILS:
        r = result["results_by_queue_utilization"][rho]
        verdict = "PASS ✅" if r["gate_pass"] else "FAIL ❌"
        print(f"  rho={rho:.2f}  r_s={r['r_s']:.4f}  p={r['p_value']:.2e}"
              f"  W_q={r['mean_Wq_ms']:.1f}ms  overlap={r['fast_slow_overlap_frac']:.4f}  {verdict}")
    print(f"  Gate 2 Pass (rho=0.7): {result['gate_pass_rho_0_7']}")
    print(f"  Gate 2 Pass (all rho): {result['gate_pass_all_rho']}")

if __name__ == "__main__":
    t4_profile  = os.path.join(REPO_ROOT, "gate2", "output-gpu-t4", "triton_service_profiles.json")
    t4_out      = os.path.join(REPO_ROOT, "gate2", "output-gpu-t4", "gate2_spearman_result.json")
    cpu_profile = os.path.join(REPO_ROOT, "gate2", "output-cpu-c7i", "triton_service_profiles.json")
    cpu_out     = os.path.join(REPO_ROOT, "gate2", "output-cpu-c7i", "gate2_spearman_result.json")

    process(t4_profile, t4_out, "Tesla T4 (GPU)")
    process(cpu_profile, cpu_out, "AWS c7i-flex CPU")
    print("\nDone.")
