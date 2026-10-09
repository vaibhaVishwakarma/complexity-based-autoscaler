"""
seed_policy_v7.py — Step 8.7: Realism-Aware Evolution v7 Seed Policy
=====================================================================

Role:
    Initial seed policy for OpenEvolve v7 evolutionary synthesis.
    Directly inherits the verified mathematical formulation of Candidate c509fa80,
    which evolved dynamic booting credit modulation and demonstrated:
      - 57.35% cost savings vs Fixed Capacity (11,899.0 ws)
      - Zero deadline misses across all 13 canonical regimes (100% SLA compliance)
      - Superiority over InferLine (14,261 ws, 44 misses)
      - 20 fewer deadline misses than Champion v3 on extreme 50s shock
      - 2 fewer actuation flaps than Champion v3 (225 deltas vs 227 deltas)

Lineage:
    Discovered in: OpenEvolve v6 (Candidate c509fa80, Rank #2)
    Inherent Score: +64.1013

AGENTS.md Compliance:
    Rule #1 — Dedicated versioned v7 seed file.
    Rule #2 — Zero hardcoding; strictly adheres to frozen TelemetricState contract.
    Rule #4 — Self-documenting structure.
"""

from __future__ import annotations

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
    """Causal multiplicative demand: λ_cloud(t) = ingress_rps × (1 - p_fast)."""

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
    """Workers currently spinning up, subject to container/model initialization delay."""

    time_since_last_scale_s: float
    """Elapsed seconds since the last scaling action (cooldown / drain tracking)."""

    # ─── HARDWARE & CONTRACT CONSTANTS ─────────────────────────────────────
    worker_capacity_rps: float = 16.0
    """Profiled Tesla T4 service rate (μ): 0.0625s per inference (Gate 2 calibrated)."""

    sla_deadline_s: float = 15.0
    """End-to-end SLA latency budget: D = 15.0 seconds."""


# ─────────────────────────────────────────────────────────────────────────────
# SEED POLICY FORMULA (OPENEVOLVE V7 SEED)
# OpenEvolve will mutate between EVOLVE-BLOCK-START and EVOLVE-BLOCK-END
# ─────────────────────────────────────────────────────────────────────────────


# EVOLVE-BLOCK-START
def compute_target_workers(state: TelemetricState) -> int:
    """
    Cost-Supreme Conformal Autoscaler Law v7 (Seeded from Candidate c509fa80).

    Mathematical Formulation:
        1. Conformal Headroom:
           safety = 1.00 + 0.008 * max(0.0, mean_set_size - 1.0)
           trend  = max(0.0, -p_fast_velocity) * ingress_rps * 0.14
           demand_workers = ((offered_cloud_rps + trend) * safety) / μ

        2. Efficiency-First Queue Drain:
           adjusted_queue = queue_depth + max(0.0, queue_velocity) * 0.04
           drain_workers  = adjusted_queue / (μ * 2.08)

        3. Dynamic Booting Credit & Pre-emptive Lookahead:
           if queue_velocity > 0 or oldest_task_age_s > 1.2:
               booting_credit = 0.25
           else:
               booting_credit = 0.95
           raw_target = demand_workers + drain_workers - (booting_workers * booting_credit)

        4. Scale-Down Hysteresis with Task Age & Micro-Queue Protection:
           if raw_target < active_workers and (time_since_last_scale < 2.2 or queue_depth > 1 or oldest_task_age_s > 1.0):
               effective_target = active_workers
           else:
               effective_target = raw_target

        5. Feasible Capacity Clamp:
           k_t = clamp(effective_target, 1, 18)
    """
    # Extract hardware constants from the typed state contract
    mu = state.worker_capacity_rps       # 16.0 RPS/worker
    max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)

    # ── Term 1: Continuous Sizing with Tight Conformal Multiplier ───────────
    conformal_safety = 1.00 + 0.008 * max(0.0, state.mean_set_size - 1.0)
    demand_trend = max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.14
    demand_workers = ((state.offered_cloud_rps + demand_trend) * conformal_safety) / mu

    # ── Term 2: Efficiency-First Queue Drain with Wide Window ───────────────
    DRAIN_WINDOW_S = 2.08
    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.04
    drain_workers = adjusted_queue / (mu * DRAIN_WINDOW_S)

    # ── Term 3: Dynamic Booting Credit & Pre-emptive Velocity Lookahead ─────
    # Modulate booting credit dynamically: discount when queues accelerate or tasks age
    if state.cloud_queue_velocity > 0.0 or state.oldest_task_age_s > 1.2:
        booting_credit = 0.25
    else:
        booting_credit = 0.95

    raw_target = demand_workers + drain_workers - (state.booting_workers * booting_credit)

    # Asymmetric scale-down hysteresis with task age and queue protection
    if raw_target < state.active_workers and (
        state.time_since_last_scale_s < 2.2
        or state.cloud_queue_depth > 1
        or state.oldest_task_age_s > 1.0
    ):
        effective_target = state.active_workers
    else:
        effective_target = raw_target

    # ── Term 4: Final Clamp to Feasible Cluster Capacity ────────────────────
    return int(max(1, min(max_workers, effective_target)))
# EVOLVE-BLOCK-END
