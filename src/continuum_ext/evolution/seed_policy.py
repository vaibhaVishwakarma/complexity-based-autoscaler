"""
seed_policy.py — Step 6: OpenEvolve Seed Program (Initial Candidate Policy)

Role:
    Provides the initial seed program submitted to the OpenEvolve evolutionary
    search. Defines the authoritative TelemetricState contract (the frozen, typed
    observation schema) and the baseline conformal scaling formula bounded within
    EVOLVE-BLOCK-START/END markers.

Gate Stage:    Step 6 (OpenEvolve Evaluator & Fitness Engine)
Roadmap Ref:   docs/STEP6_OPENEVOLVE_SYNTHESIS_SPECIFICATION.md Section 7
Strategy Ref:  docs/CONFORMAL_AUTOSCALER_STRATEGY.md Section 9

Inputs:
    TelemetricState — frozen dataclass populated by openevolve_evaluator.py
    at each simulation timestep t.

Outputs:
    int — target worker count k_t ∈ [1, 18] emitted to the ContinuumBench
    substrate scheduler via ScaleAction(stage="CloudRefine", active_workers=k_t).

AGENTS.md Compliance:
    Rule #1 — This is the seed v1; new discovered policies saved as evolved_policy.py
    Rule #2 — No hardcoded upstream gate p-values; TelemetricState values are live signals
    Rule #3 — Runs exclusively under ./.venv/bin/python
    Rule #4 — Self-documenting with header, tier comments, and inline logic notes
"""

import math
from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────────────
# TELEMETRIC STATE CONTRACT
# Authoritative, immutable observation schema for the Conformal Autoscaler.
# Every attribute is causally observable at timestep t with zero lookahead.
# DO NOT ADD NEW FIELDS — the schema is frozen; feature additions require a
# new versioned seed file (AGENTS.md Rule #1).
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
# SEED CONFORMAL SCALING POLICY
# This formula is the INITIAL seed submitted to OpenEvolve. The LLM will
# iteratively mutate the code between EVOLVE-BLOCK-START and EVOLVE-BLOCK-END
# to discover superior policies. The seed implements a deterministic,
# multiplicative demand-forward + queue-drain conformal law.
# ─────────────────────────────────────────────────────────────────────────────


# EVOLVE-BLOCK-START
def compute_target_workers(state: TelemetricState) -> int:
    """
    Conformal Autoscaler Scaling Law v1 (Seed Policy).

    Computes the optimal target worker count k_t for the CloudRefine stage
    given the current telemetric state. Returns an integer in [1, max_workers=18].

    Strategy (Seed):
        1. Demand-Forward Term: Provision workers to serve the causal cloud demand
           λ_cloud = ingress_rps * (1 - p_fast), with a 20% safety margin to absorb
           Poisson variance without SLA violations.
        2. Queue-Drain Budget: Add extra workers needed to drain the current backlog Q_t
           within a 0.5-epoch drain window, preventing head-of-line blocking.
        3. Booting Offset: Subtract workers already spinning up to avoid over-provisioning.
        4. Urgency Guard: If oldest_task_age_s is within 3.0s of the SLA deadline,
           immediately clamp to max workers — a last-resort SLA rescue.
        5. Clamp to [1, 18]: Ensure k_t is always a valid integer in the feasible range.

    Failure modes this seed is designed to address:
        - HPA drain drop (72 misses in zero_terminal): booting_workers offset + urgency guard
        - KEDA flapping (1710 deltas): demand-forward term provides smoother scaling
        - InferLine semantic blindness (44 misses): offered_cloud_rps uses p_fast directly
    """
    # Extract hardware constants from the typed state contract
    mu = state.worker_capacity_rps       # 16.0 RPS/worker
    max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)

    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
    SAFETY_MARGIN = 1.20
    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)

    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
    DRAIN_WINDOW_S = 0.5
    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
    drain_workers = math.ceil(queue_drain_rps / mu)

    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
    # Workers already booting will contribute capacity shortly; avoid double-counting.
    effective_target = demand_workers + drain_workers - state.booting_workers

    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
    # immediately clamp to max workers to prevent a deadline miss cascade.
    SLA_RESCUE_MARGIN_S = 3.0
    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
        effective_target = max_workers

    # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
    # k_t must always be a valid integer in [1, max_workers].
    k_t = int(max(1, min(max_workers, effective_target)))
    return k_t
# EVOLVE-BLOCK-END
