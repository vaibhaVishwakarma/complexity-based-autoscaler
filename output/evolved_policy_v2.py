"""
evolved_policy_v2.py — Step 7 v2 Output: Discovered Cost-First Conformal Autoscaler Policy

Role:
    Best policy discovered by OpenEvolve v2 evolutionary search across
    200 iterations optimizing Cost-First / Equal Miss & P99.

Provenance:
    Search configuration: configs/evolution/openevolve_config_v2.yaml
    Seed program:         src/continuum_ext/evolution/seed_policy_v2.py
    Evaluator:            src/continuum_ext/evolution/openevolve_evaluator_v2.py
    MAP-Elites archive:   output/evolution_runs_v2/openevolve_db/

Performance (authoritative 13-regime benchmark):
    Fitness J_v2 (combined_score): 40.4666
    Cost savings vs Fixed:         53.05%
    Churn stability:               1742.0
    Tail safety:                   9.0
    Deadline misses:               0.0
    Worker-seconds:                13100.0
    Scaling deltas:                258.0

AGENTS.md Compliance:
    Rule #1 — Saved as new versioned artifact (evolved_policy_v2.py).
"""

"""
seed_policy_v2.py — Step 6 v2: OpenEvolve Seed Program for Cost-First Evolution

Role:
    Provides the initial candidate program for the Cost-First / Equal Miss & P99
    evolutionary search (v2). Initialized from the Step 7 champion policy (Program 35671429),
    providing a robust, verified starting point with zero deadline misses and 25-30% cost
    savings, ready to be mutated to shed defensive slack and beat InferLine's 48.9% savings.

Gate Stage:    Step 6 v2 (OpenEvolve Evaluator & Fitness Engine)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9

Inputs:
    TelemetricState — frozen dataclass populated by openevolve_evaluator_v2.py
    at each simulation timestep t.

Outputs:
    int — target worker count k_t ∈ [1, 18] emitted to the ContinuumBench
    substrate scheduler via ScaleAction(stage="CloudRefine", active_workers=k_t).

AGENTS.md Compliance:
    Rule #1 — New versioned seed artifact (seed_policy_v2.py); seed_policy.py untouched.
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
# EVOLVABLE POLICY FORMULA (INITIAL V2 CANDIDATE)
# ─────────────────────────────────────────────────────────────────────────────


# EVOLVE-BLOCK-START
def compute_target_workers(state: TelemetricState) -> int:
    """
    Cost-First Conformal Autoscaler Law (v2 Seed).

    Objective:
        1. Maximize Cost Savings (% reduction in worker-seconds vs Fixed Capacity).
           Target to beat: InferLine's 48.9% savings (14,261 worker-seconds).
        2. Keep deadline misses and P99 latency degradation balanced with equal weights.
           Tolerate low single-digit misses (<= 5 out of 121k) under violent shocks
           to shed unnecessary defensive buffering.
        3. Maintain actuation stability (low scaling deltas).
    """
    # Extract hardware constants from the typed state contract
    mu = state.worker_capacity_rps       # 16.0 RPS/worker
    max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)

    # ── Term 1: Lean Conformal Demand-Forward ──────────────────────────────
    conformal_safety = 1.00 + 0.02 * max(0.0, state.mean_set_size - 1.0)
    demand_trend = max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.30
    demand_workers = ((state.offered_cloud_rps + demand_trend) * conformal_safety) / mu

    # ── Term 2: Efficiency-First Queue Drain ───────────────────────────────
    DRAIN_WINDOW_S = 1.6
    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.30
    drain_workers = adjusted_queue / (mu * DRAIN_WINDOW_S)

    # ── Term 3: Resource Consolidation & Booting Credit ────────────────────
    raw_target = demand_workers + drain_workers - (state.booting_workers * 0.65)

    # Asymmetric scale-down hysteresis
    if raw_target < state.active_workers and (state.time_since_last_scale_s < 2.1 or state.cloud_queue_depth > 1):
        effective_target = state.active_workers
    else:
        effective_target = raw_target

    # ── Term 4: Final Clamp to Feasible Cluster Capacity ────────────────────
    return int(max(1, min(max_workers, effective_target)))
# EVOLVE-BLOCK-END
