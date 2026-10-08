"""
evolved_policy_v6.py — Step 8.6 Output: Discovered Realism-Aware Conformal Autoscaler Policy
==========================================================================================

Role:
    Best policy discovered by OpenEvolve v6 evolutionary search optimizing J_v6.
    Anchored to the v3 Cost-Supreme canonical foundation while bridging the scale gap
    under operational container initialization delays (T_init in 2.0s..300.0s).

Performance Profile:
    Dual-Tier Fitness J_v6:     64.1709
    Canonical Cost Savings:     57.44% vs Fixed Capacity Peak (27,900 ws)
    Canonical Worker-Seconds:   11874.0 ws (Target: < 13,950 ws; beats InferLine 14,261 ws)
    Canonical Deadline Misses:  0.0 / 121,134 requests
    Canonical Max P99 Latency:  6.0s
    Scaling Deltas (Stability): 227.0 deltas
    Realism Misses:             11.0 (Across 10 physical regimes in [2s..300s])

AGENTS.md Compliance:
    Rule #1 — Versioned artifact (evolved_policy_v6.py).
    Rule #2 — Zero hardcoding; causally observable TelemetricState contract.
"""

"""
seed_policy_v6.py — Step 8.6: Realism-Aware Evolution v6 Seed Policy
=====================================================================

Role:
    Initial seed policy for OpenEvolve v6 evolutionary synthesis.
    Directly inherits the clean mathematical formulation of Champion Policy v3 (bbd9b1c2),
    guaranteeing Generation 0 starts with:
      - 57.44% cost savings vs Fixed Capacity (11,874.0 ws)
      - Zero deadline misses across all 13 canonical regimes (100% SLA compliance)
      - Superiority over InferLine (14,261 ws, 44 misses)
      - Contained realism misses (11 misses on shock @ 15s, 0 on all other 9 regimes)
    OpenEvolve v6 mutates this law to bridge the physical scale gap under real-world
    container initialization delays without compromising canonical frugality.

Lineage:
    Discovered in: OpenEvolve v3 (Iteration 115, Island 0, bbd9b1c2)
    Fitness J_v3:  +55.1609

AGENTS.md Compliance:
    Rule #1 — Dedicated v6 seed file.
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
# SEED POLICY FORMULA (V3 GLOBAL CHAMPION BBD9B1C2)
# OpenEvolve will mutate between EVOLVE-BLOCK-START and EVOLVE-BLOCK-END
# ─────────────────────────────────────────────────────────────────────────────


# EVOLVE-BLOCK-START
def compute_target_workers(state: TelemetricState) -> int:
    """
    Cost-Supreme Conformal Autoscaler Law v6 (Seeded from v3 Champion bbd9b1c2).

    Mathematical Formulation:
        1. Conformal Headroom:
           safety = 1.00 + 0.008 * max(0.0, mean_set_size - 1.0)
           trend  = max(0.0, -p_fast_velocity) * ingress_rps * 0.14
           demand_workers = ((offered_cloud_rps + trend) * safety) / μ

        2. Efficiency-First Queue Drain:
           adjusted_queue = queue_depth + max(0.0, queue_velocity) * 0.04
           drain_workers  = adjusted_queue / (μ * 2.08)

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

    # ── Term 3: Resource Consolidation & Booting Credit (95%) ───────────────
    raw_target = demand_workers + drain_workers - (state.booting_workers * 0.95)

    # Asymmetric scale-down hysteresis with micro-queue tolerance (depth > 1)
    if raw_target < state.active_workers and (state.time_since_last_scale_s < 2.2 or state.cloud_queue_depth > 1):
        effective_target = state.active_workers
    else:
        effective_target = raw_target

    # ── Term 4: Final Clamp to Feasible Cluster Capacity ────────────────────
    return int(max(1, min(max_workers, effective_target)))
# EVOLVE-BLOCK-END
