"""
seed_policy_v3.py — Step 6 v3: OpenEvolve Seed Program Initialized from v2 Cost Champion

Role:
    Provides the initial candidate program for the Step 7 v3 Cost-Supreme evolutionary
    search. Initialized directly from the Step 7 v2 Cost Champion (Program 4a7ccfe9),
    which established a baseline of 53.05% cost savings (13,100.0 worker-seconds),
    zero deadline misses, and 258 scaling deltas, beating InferLine by 1,161 worker-seconds.

Gate Stage:    Step 6 v3 (OpenEvolve Seed Policy & Fitness Engine)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9

Inputs:
    TelemetricState — frozen dataclass populated by openevolve_evaluator_v3.py
    at each simulation timestep t.

Outputs:
    int — target worker count k_t ∈ [1, 18] emitted to the ContinuumBench
    substrate scheduler via ScaleAction(stage="CloudRefine", active_workers=k_t).

AGENTS.md Compliance:
    Rule #1 — New versioned seed artifact (seed_policy_v3.py); previous seeds untouched.
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
        - Cloud fleet: 6 nodes × 3 workers = 18 max workers
        - Worker service rate (μ): 16.0 RPS/worker (Tesla T4, profiled Gate 2)
        - SLA deadline: 15.0 seconds end-to-end
        - RAPS calibration: α=0.10, q̂=0.79914
    """

    # ─── TIER 1: EDGE SEMANTIC TRIAGE TELEMETRY ────────────────────────────
    p_fast: float
    """Empirical acceptance ratio: fraction of frames handled locally (|C(x)| = 1)."""

    p_fast_velocity: float
    """Rate of change: dp_fast/dt over a 3-epoch sliding window."""

    mean_set_size: float
    """Mean RAPS prediction set size E[|C(x)|]. Calibrated at alpha=0.10, q_hat=0.79914."""

    # ─── TIER 2: CONTINUUM TRAFFIC DYNAMICS ────────────────────────────────
    ingress_rps: float
    """Arriving Poisson sensor request rate λ(t) at IoT sensor ingress."""

    ingress_acceleration: float
    """Second derivative d²(λ)/dt² indicating sudden ramp/burst onset."""

    offered_cloud_rps: float
    """Causal multiplicative demand: λ_cloud(t) = ingress_rps × (1 - p_fast).
    Critical for suite2_decoupled_opposing: volume can drop while cloud demand doubles
    because p_fast collapses. This pre-computed feature makes that directly observable."""

    # ─── TIER 3: CLUSTER QUEUE BACKLOG & AGING ─────────────────────────────
    cloud_queue_depth: int
    """Current unserviced task backlog Q_t waiting at the CloudRefine ingress queue."""

    cloud_queue_velocity: float
    """Rate of backlog change: dQ/dt — differentiates transient bursts from growing queues."""

    oldest_task_age_s: float
    """Age of head-of-line queued task, measuring proximity to the 15.0s SLA deadline."""

    # ─── TIER 4: WORKER FLEET & ACTUATION STATE ────────────────────────────
    active_workers: int
    """Currently active, healthy CloudRefine GPU workers (k_t ∈ [1, 18])."""

    booting_workers: int
    """Workers currently spinning up, subject to 1.0s container startup delay."""

    time_since_last_scale_s: float
    """Elapsed seconds since the last scaling action (cooldown / drain tracking)."""

    # ─── HARDWARE & CONTRACT CONSTANTS ─────────────────────────────────────
    worker_capacity_rps: float = 16.0
    """Profiled Tesla T4 service rate (μ): 0.0625s per inference (Gate 2 calibrated)."""

    sla_deadline_s: float = 15.0
    """End-to-end SLA latency budget: D = 15.0 seconds."""


# ─────────────────────────────────────────────────────────────────────────────
# EVOLVABLE POLICY FORMULA (INITIAL V3 CANDIDATE — FROM 4a7ccfe9)
# ─────────────────────────────────────────────────────────────────────────────


# EVOLVE-BLOCK-START
def compute_target_workers(state: TelemetricState) -> int:
    """
    Cost-Supreme Conformal Autoscaler Law (v3 Seed).

    Objective:
        1. Maximize Cost Savings (% reduction in worker-seconds vs Fixed Capacity 27,900 ws).
           Target: Push beyond 53.05% towards 55-60% savings.
        2. Keep P99 Tail Latency within the 6.0s safety envelope (SLA budget is 15.0s).
        3. Zero deadline misses across all regimes.
        4. Maintain ultra-low actuation flapping (< 260 deltas).
    """
    # Extract hardware constants from the typed state contract
    mu = state.worker_capacity_rps       # 16.0 RPS/worker
    max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)

    # ── Term 1: Continuous Sizing with Tight Conformal Multiplier ───────────
    conformal_safety = 1.00 + 0.02 * max(0.0, state.mean_set_size - 1.0)
    demand_trend = max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.30
    demand_workers = ((state.offered_cloud_rps + demand_trend) * conformal_safety) / mu

    # ── Term 2: Efficiency-First Queue Drain with Wide Window ───────────────
    DRAIN_WINDOW_S = 1.6
    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.30
    drain_workers = adjusted_queue / (mu * DRAIN_WINDOW_S)

    # ── Term 3: Resource Consolidation & Aggressive Booting Credit (65%) ───
    raw_target = demand_workers + drain_workers - (state.booting_workers * 0.65)

    # Asymmetric scale-down hysteresis with micro-queue tolerance (depth > 1)
    if raw_target < state.active_workers and (state.time_since_last_scale_s < 2.1 or state.cloud_queue_depth > 1):
        effective_target = state.active_workers
    else:
        effective_target = raw_target

    # ── Term 4: Final Clamp to Feasible Cluster Capacity ────────────────────
    return int(max(1, min(max_workers, effective_target)))
# EVOLVE-BLOCK-END
