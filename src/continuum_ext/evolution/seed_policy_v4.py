"""
seed_policy_v4.py — Step 6 v4: OpenEvolve Seed Program Initialized from v3 Champion (bbd9b1c2)

Role:
    Provides the initial candidate program for the Step 7 v4 Pareto-Optimal
    (Cost + Tail Latency) evolutionary search. Initialized directly from the
    v3 Global Champion (Program bbd9b1c2), which established 57.44% cost savings
    (11,874 worker-seconds), zero deadline misses (0/121,134 requests across all 13 regimes),
    and 228 scaling deltas, with maximum P99 tail latency of 6.00s.

Objective for v4:
    Evolve predictive spike suppression, task age urgency damping, and tight
    conformal headroom to shave P99 tail latency from 6.00s down to <= 5.00s
    while preserving > 55% cost savings and 0 deadline misses.

Gate Stage:    Step 6 v4 (OpenEvolve Seed Policy & Tail-Latency Fitness Engine)
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9

Inputs:
    TelemetricState — frozen dataclass populated by openevolve_evaluator_v4.py
    at each simulation timestep t.

Outputs:
    int — target worker count k_t in [1, 18] emitted to the ContinuumBench
    substrate scheduler via ScaleAction(stage="CloudRefine", active_workers=k_t).

AGENTS.md Compliance:
    Rule #1 — New versioned seed artifact (seed_policy_v4.py); previous seeds untouched.
    Rule #2 — Zero hardcoding; all operational variables derived dynamically from state.
    Rule #3 — Runs exclusively under ./.venv/bin/python.
    Rule #4 — Self-documenting with header, tier comments, and inline logic notes.
"""

import math
from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────────────
# TELEMETRIC STATE CONTRACT (FROZEN & IMMUTABLE)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TelemetricState:
    """
    Authoritative, immutable telemetric observation contract delivered
    to the autoscaler at timestep t. Every attribute is causally observable
    at time t with zero lookahead or oracle leakage.

    Hardware Context:
        - Cloud fleet: 6 nodes x 3 workers = 18 max workers
        - Worker service rate (mu): 16.0 RPS/worker (Tesla T4, profiled Gate 2)
        - SLA deadline: 15.0 seconds end-to-end
        - RAPS calibration: alpha=0.10, q_hat=0.79914
    """

    # --- TIER 1: EDGE SEMANTIC TRIAGE TELEMETRY ----------------------------
    p_fast: float
    """Empirical acceptance ratio: fraction of frames handled locally (|C(x)| = 1)."""

    p_fast_velocity: float
    """Rate of change: dp_fast/dt over a 3-epoch sliding window."""

    mean_set_size: float
    """Mean RAPS prediction set size E[|C(x)|]. Calibrated at alpha=0.10, q_hat=0.79914."""

    # --- TIER 2: CONTINUUM TRAFFIC DYNAMICS --------------------------------
    ingress_rps: float
    """Arriving Poisson sensor request rate lambda(t) at IoT sensor ingress."""

    ingress_acceleration: float
    """Second derivative d^2(lambda)/dt^2 indicating sudden ramp/burst onset."""

    offered_cloud_rps: float
    """Causal multiplicative demand: lambda_cloud(t) = ingress_rps * (1 - p_fast).
    Critical for suite2_decoupled_opposing: volume can drop while cloud demand doubles
    because p_fast collapses. This pre-computed feature makes that directly observable."""

    # --- TIER 3: CLUSTER QUEUE BACKLOG & AGING -----------------------------
    cloud_queue_depth: int
    """Current unserviced task backlog Q_t waiting at the CloudRefine ingress queue."""

    cloud_queue_velocity: float
    """Rate of backlog change: dQ/dt - differentiates transient bursts from growing queues."""

    oldest_task_age_s: float
    """Age of head-of-line queued task, measuring proximity to the 15.0s SLA deadline."""

    # --- TIER 4: WORKER FLEET & ACTUATION STATE ----------------------------
    active_workers: int
    """Currently active, healthy CloudRefine GPU workers (k_t in [1, 18])."""

    booting_workers: int
    """Workers currently spinning up, subject to 1.0s container startup delay."""

    time_since_last_scale_s: float
    """Elapsed seconds since the last scaling action (cooldown / drain tracking)."""

    # --- HARDWARE & CONTRACT CONSTANTS -------------------------------------
    worker_capacity_rps: float = 16.0
    """Profiled Tesla T4 service rate (mu): 0.0625s per inference (Gate 2 calibrated)."""

    sla_deadline_s: float = 15.0
    """End-to-end SLA latency budget: D = 15.0 seconds."""


# ─────────────────────────────────────────────────────────────────────────────
# EVOLVED POLICY FORMULA (INITIALIZED FROM V3 CHAMPION BBD9B1C2)
# ─────────────────────────────────────────────────────────────────────────────


# EVOLVE-BLOCK-START
def compute_target_workers(state: TelemetricState) -> int:
    """
    Pareto-Optimal Conformal Autoscaler Law (Cost-Supreme with Tail Latency Optimization).

    Mathematical Formulation:
        1. Conformal Headroom:
           safety = 1.00 + 0.008 * max(0.0, mean_set_size - 1.0)
           trend  = max(0.0, -p_fast_velocity) * ingress_rps * 0.14
           demand_workers = ((offered_cloud_rps + trend) * safety) / mu

        2. Efficiency-First Queue Drain:
           adjusted_queue = queue_depth + max(0.0, queue_velocity) * 0.04
           drain_workers  = adjusted_queue / (mu * 2.08)

        3. Resource Consolidation & 95% Booting Credit:
           raw_target = demand_workers + drain_workers - (booting_workers * 0.95)

        4. Scale-Down Hysteresis with Micro-Queue Slack:
           if raw_target < active_workers and (time_since_last_scale < 2.2 or queue_depth > 1):
               effective_target = active_workers
           else:
               effective_target = raw_target

        5. Feasible Capacity Clamp:
           k_t = clamp(effective_target, 1, 18)
    """
    mu = state.worker_capacity_rps       # 16.0 RPS/worker
    max_workers = 18                     # 6 nodes x 3 workers/node

    # --- Term 1: Continuous Sizing with Tight Conformal Multiplier -----------
    conformal_safety = 1.00 + 0.008 * max(0.0, state.mean_set_size - 1.0)
    demand_trend = max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.14
    demand_workers = ((state.offered_cloud_rps + demand_trend) * conformal_safety) / mu

    # --- Term 2: Efficiency-First Queue Drain with Wide Window ---------------
    DRAIN_WINDOW_S = 2.08
    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.04
    drain_workers = adjusted_queue / (mu * DRAIN_WINDOW_S)

    # --- Term 3: Resource Consolidation & Booting Credit (95%) --------------
    raw_target = demand_workers + drain_workers - (state.booting_workers * 0.95)

    # Asymmetric scale-down hysteresis with micro-queue tolerance (depth > 1)
    if raw_target < state.active_workers and (state.time_since_last_scale_s < 2.2 or state.cloud_queue_depth > 1):
        effective_target = state.active_workers
    else:
        effective_target = raw_target

    # --- Term 4: Final Clamp to Feasible Cluster Capacity --------------------
    return int(max(1, min(max_workers, effective_target)))
# EVOLVE-BLOCK-END
