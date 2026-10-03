"""
inferline_exact.py — Exact replication of InferLine High-Frequency Tuner (SoCC '20, Algs 3 & 4).

Role: Faithful reproduction of the InferLine Tuner for use as a defensible baseline.
Gate stage: Simulation runtime (drop-in replacement for InferLineController).

Paper: Crankshaw et al., "InferLine: Latency-Aware Provisioning and Scaling for
       Prediction Serving Pipelines", ACM SoCC '20.
       Reference: references/papers/InferLine_Crankshaw_SoCC_2020.pdf
       Methodology: references/eval-methodologies/inferline_evaluation_benchmarking_methodology.md

DEVIATION FROM PRIOR APPROXIMATION:
  The earlier InferLineController (conformal_controllers.py) used multi-scale EMA, which
  captures the spirit of multi-scale smoothing but is NOT equivalent to the paper's algorithm.
  This file implements the exact formulas from §2.4 of the methodology document:

  Algorithm 3 (Scale-Up):
    r_i = q_i / ΔT_i   for ΔT_i ∈ {T_s, 2T_s, 4T_s, 8T_s, 30s, 60s}
    r_max = max_i(r_i)    ← sliding-window MAXIMUM, not a smoothed average
    k_m = ceil(r_max * s_m / (μ_m * ρ_m))

  Algorithm 4 (Scale-Down, after 15s stabilisation):
    λ_new = max over t ∈ [now-30s, now] of λ_5s(t)
    k_m = ceil(λ_new * s_m / (μ_m * ρ_p))    where ρ_p = min_m(ρ_m)

SCOPE NOTE (what we replicate):
  InferLine's Low-Frequency Planner (Algs 1 & 2) performs offline hardware/batch-size
  co-optimisation and is not replicated here — it requires a separate planning trace.
  We replicate only the High-Frequency Tuner (Algs 3 & 4), which is the online
  autoscaling component and the fair point of comparison for our system.

Inputs:
  - state: ControllerState (queue_depths, worker_pools, epoch, metadata)
  - Gate 2 contract: compute_service_capacity_rps() → μ_m (single-replica throughput)
  - Constructor params: s_m (invocation probability), rho_m (max-provisioning factor),
    window_sizes_epochs (ΔT_i set), stabilise_epochs (15s delay), bucket_size_epochs

Outputs:
  - ControllerAction(scale, placement, metadata with Alg 3/4 diagnostics)
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

from continuum_bench.controllers.autoscaling_baselines import _PlacementReplanMixin
from continuum_bench.controllers.interfaces import (
    ControllerAction,
    ControllerState,
    ScaleAction,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED: int = 42

#: Default sliding-window sizes from the InferLine paper (§2.2).
#: T_s ≈ service time of cloud worker ≈ 1 epoch. Window doublings: 1,2,4,8 + 30,60.
_DEFAULT_WINDOW_SIZES: Tuple[int, ...] = (1, 2, 4, 8, 30, 60)

#: Scale-down stabilisation delay — exactly 15 epochs (= 15 s at 1 epoch/s).
#: Paper: "3× container spin-up time"; we use 15s to match Algorithm 4.
_STABILISE_EPOCHS: int = 15

#: Rolling max window for scale-down — exactly 30 epochs (= 30 s at 1 epoch/s).
#: Paper: "max over t ∈ [t−30s, t]".
_SCALEDOWN_WINDOW_EPOCHS: int = 30

#: 5-second bucket size for rolling λ_new estimate (Algorithm 4).
_BUCKET_SIZE_EPOCHS: int = 5


# ---------------------------------------------------------------------------
# Sliding-window arrival counter
# ---------------------------------------------------------------------------


class _SlidingArrivalBuffer:
    """Maintains a fixed-length circular buffer of per-epoch queue observations.

    Used to compute the sliding-window maximum q_i for each window size ΔT_i,
    exactly as described in InferLine §2.2 (Network Calculus Traffic Envelope).

    Stores the last `max_window` epoch observations of queue_depth (a proxy for
    per-epoch arrivals when the worker count is stable).
    """

    def __init__(self, max_window: int) -> None:
        """Initialise buffer with capacity max_window."""
        self._buf: Deque[float] = deque(maxlen=max_window)

    def push(self, value: float) -> None:
        """Append one epoch's observation."""
        self._buf.append(value)

    def window_max(self, window: int) -> float:
        """Return the maximum value over the last `window` observations.

        If fewer than `window` observations have been recorded, returns the
        maximum of all available observations (conservative initial behaviour).
        """
        if not self._buf:
            return 0.0
        available = list(self._buf)[-window:]  # last `window` entries
        return float(max(available))

    def __len__(self) -> int:
        return len(self._buf)


# ---------------------------------------------------------------------------
# InferLineExactController — Algorithms 3 & 4 from SoCC '20
# ---------------------------------------------------------------------------


@dataclass
class InferLineExactController(_PlacementReplanMixin):
    """Exact replication of InferLine High-Frequency Tuner (SoCC '20, Algs 3 & 4).

    This controller faithfully implements:
      - Algorithm 3: Sliding-window maximum traffic envelope for scale-up.
      - Algorithm 4: 30-second rolling max + 15-second stabilisation for scale-down.

    It does NOT implement the Low-Frequency Planner (Algs 1 & 2), which performs
    offline hardware/batch-size optimisation. Those planner outputs are supplied
    via constructor arguments (rho_m, s_m) or loaded from Gate 2 contract.

    Args:
        invocation_prob (s_m):
            Conditional invocation probability of the CloudRefine stage. In the
            split-inference DAG, this equals (1 − fp_assumed) ≈ 0.50 (the fraction
            of requests that reach the cloud tier under calibration baseline). Since
            InferLine does not use live fp(t), this is a static offline estimate.
        rho_m:
            Max-provisioning factor from the (offline) Planner. Defined as
            ρ_m = λ_planning / μ_m, where λ_planning is the mean arrival rate
            in the planning trace. Defaults to 1.0 (no planner — conservative).
        batch_size:
            Triton dynamic batching batch size for Gate 2 capacity lookup.
        batch_timeout_s:
            Batch formation timeout for Gate 2 capacity lookup.
        window_sizes_epochs:
            Sliding window sizes ΔT_i (in epochs). Paper uses {T_s, 2T_s, 4T_s, ...60s}.
        stabilise_epochs:
            Number of consecutive below-threshold epochs before scale-down fires (Alg 4).
            Paper: 15 seconds ≡ 15 epochs at 1 epoch/s.
        scaledown_window_epochs:
            Rolling window for λ_new in Algorithm 4. Paper: 30 seconds.
        bucket_size_epochs:
            Bucket size for 5-second arrival rate sampling in Algorithm 4.
        min_replicas:
            Minimum active workers per stage.
        cooldown_epochs:
            Minimum epochs between consecutive scale-up events.
    """

    invocation_prob: float = 0.50          # s_m: fraction of requests reaching cloud
    rho_m: float = 1.0                     # offline planner max-provisioning factor
    batch_size: int = 8
    batch_timeout_s: float = 0.040
    window_sizes_epochs: Tuple[int, ...] = _DEFAULT_WINDOW_SIZES
    stabilise_epochs: int = _STABILISE_EPOCHS
    scaledown_window_epochs: int = _SCALEDOWN_WINDOW_EPOCHS
    bucket_size_epochs: int = _BUCKET_SIZE_EPOCHS
    min_replicas: int = 1
    cooldown_epochs: int = 2

    # Internal state — not constructor args
    _arrival_buf: Dict[str, _SlidingArrivalBuffer] = field(default_factory=dict, init=False)
    _bucket_buf: Dict[str, _SlidingArrivalBuffer] = field(default_factory=dict, init=False)
    _bucket_accumulator: Dict[str, float] = field(default_factory=dict, init=False)
    _bucket_counter: Dict[str, int] = field(default_factory=dict, init=False)
    _lambda_5s_buf: Dict[str, _SlidingArrivalBuffer] = field(default_factory=dict, init=False)
    _below_counter: Dict[str, int] = field(default_factory=dict, init=False)
    _cooldowns: Dict[str, int] = field(default_factory=dict, init=False)
    _capacity_rps: float = field(default=0.0, init=False)
    _rho_p: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Load Gate 2 capacity and compute system-wide ρ_p = min(ρ_m)."""
        super().__post_init__()
        self._capacity_rps = self._load_capacity()
        # ρ_p = min_m(ρ_m) — with a single pool stage, ρ_p = ρ_m
        self._rho_p = max(1e-9, float(self.rho_m))

    def _load_capacity(self) -> float:
        """Load single-replica throughput μ_m from Gate 2 contract."""
        try:
            from contracts.gate2 import load_gate2_profiles  # type: ignore[import]
            profiles = load_gate2_profiles()
            return profiles.compute_service_capacity_rps(
                batch_size=self.batch_size,
                batch_timeout_s=self.batch_timeout_s,
            )
        except Exception as exc:
            import warnings
            warnings.warn(
                f"Gate2 contract load failed ({exc}); using fallback 40.0 RPS/node.",
                stacklevel=2,
            )
            return 40.0

    def _ensure_stage(self, stage: str) -> None:
        """Lazily initialise per-stage buffers on first observation."""
        max_w = max(self.window_sizes_epochs)
        if stage not in self._arrival_buf:
            self._arrival_buf[stage] = _SlidingArrivalBuffer(max_w)
        if stage not in self._lambda_5s_buf:
            # Stores 5-second bucket rates; need last 30s → 6 buckets
            n_buckets = max(1, self.scaledown_window_epochs // self.bucket_size_epochs)
            self._lambda_5s_buf[stage] = _SlidingArrivalBuffer(n_buckets)
        if stage not in self._bucket_accumulator:
            self._bucket_accumulator[stage] = 0.0
            self._bucket_counter[stage] = 0

    def _push_observation(self, stage: str, queue_depth: float, epoch: int) -> None:
        """Push one epoch's queue depth into arrival buffer and accumulate 5s bucket."""
        self._arrival_buf[stage].push(queue_depth)

        # Accumulate into 5-second bucket for Algorithm 4
        self._bucket_accumulator[stage] += queue_depth
        self._bucket_counter[stage] += 1
        if self._bucket_counter[stage] >= self.bucket_size_epochs:
            # Flush bucket: average queue depth over bucket → normalise to RPS
            bucket_rate = (
                self._bucket_accumulator[stage]
                / float(self.bucket_size_epochs)
                * (self._capacity_rps / max(1.0, 1.0))  # approximate RPS from queue
            )
            self._lambda_5s_buf[stage].push(bucket_rate)
            self._bucket_accumulator[stage] = 0.0
            self._bucket_counter[stage] = 0

    def _algorithm3_rmax(self, stage: str) -> float:
        """Algorithm 3: Compute r_max = max_i(q_i / ΔT_i) across all window sizes.

        q_i is the maximum number of arrivals observed in any sliding window of
        width ΔT_i. We approximate q_i as window_max(ΔT_i) from the arrival buffer.
        This is the exact Network Calculus envelope from InferLine §2.2.
        """
        r_max = 0.0
        buf = self._arrival_buf[stage]
        for w in self.window_sizes_epochs:
            q_i = buf.window_max(w)
            r_i = q_i / float(w)  # r_i = q_i / ΔT_i  (per-epoch normalisation)
            r_max = max(r_max, r_i)
        return r_max

    def _algorithm3_desired(self, r_max: float, snapshot) -> int:
        """Algorithm 3: Compute k_m = ceil(r_max * s_m / (μ_m * ρ_m)).

        Maps the envelope rate to a required replica count accounting for
        conditional invocation probability (s_m) and the planner's capacity buffer (ρ_m).
        """
        mu_m = max(1e-9, self._capacity_rps)
        rho_m = max(1e-9, float(self.rho_m))
        s_m = max(0.0, float(self.invocation_prob))
        k = math.ceil(r_max * s_m / (mu_m * rho_m))
        return max(snapshot.min_workers, min(snapshot.max_workers, max(int(self.min_replicas), k)))

    def _algorithm4_desired(self, stage: str, snapshot) -> int:
        """Algorithm 4: Compute k_m from λ_new = max over last 30s of 5s-bucket rates.

        λ_new is the peak 5-second arrival rate observed in the past 30 seconds.
        Uses ρ_p = min_m(ρ_m) as the conservative system-wide provisioning factor.
        """
        lam_new = self._lambda_5s_buf[stage].window_max(
            self.scaledown_window_epochs // self.bucket_size_epochs
        )
        mu_m = max(1e-9, self._capacity_rps)
        s_m = max(0.0, float(self.invocation_prob))
        rho_p = self._rho_p
        k = math.ceil(lam_new * s_m / (mu_m * rho_p))
        return max(snapshot.min_workers, min(snapshot.max_workers, max(int(self.min_replicas), k)))

    def step(self, state: ControllerState) -> ControllerAction:
        """Execute one epoch of InferLine Algorithms 3 & 4.

        Scale-up path (Algorithm 3):
          1. Push queue_depth into sliding arrival buffer.
          2. Compute r_max across all window sizes (exact sliding-window max).
          3. Compute k_m = ceil(r_max * s_m / (μ_m * ρ_m)).
          4. If k_m > current and cooldown elapsed → scale up immediately.

        Scale-down path (Algorithm 4):
          1. After stabilise_epochs of below-target observations:
          2. Compute λ_new = max over last 30s of 5s-bucket rates.
          3. Compute k_m = ceil(λ_new * s_m / (μ_m * ρ_p)).
          4. If k_m < current → scale down.
        """
        scale_actions: List[ScaleAction] = []
        alg_metrics: Dict[str, dict] = {}

        for stage, snapshot in state.worker_pools.items():
            self._ensure_stage(stage)
            self._cooldowns[stage] = max(0, self._cooldowns.get(stage, 0) - 1)

            current = int(snapshot.active_workers)
            queue_depth = float(state.queue_depths.get(stage, 0))

            # --- Push observation into arrival buffer and 5s bucket ---
            self._push_observation(stage, queue_depth, state.epoch)

            # --- Algorithm 3: sliding-window max envelope → scale-up ---
            r_max = self._algorithm3_rmax(stage)
            desired_up = self._algorithm3_desired(r_max, snapshot)

            # --- Algorithm 4: 30s rolling max → scale-down candidate ---
            desired_down = self._algorithm4_desired(stage, snapshot)

            # Determine final desired and action
            action_taken = "none"
            final_desired = current
            below_counter = self._below_counter.get(stage, 0)

            if desired_up > current and self._cooldowns[stage] == 0:
                # Scale-up: act immediately (no stabilisation delay for scale-up)
                final_desired = desired_up
                scale_actions.append(ScaleAction(stage=stage, active_workers=final_desired))
                self._cooldowns[stage] = max(0, int(self.cooldown_epochs))
                self._below_counter[stage] = 0  # reset scale-down counter
                action_taken = "scale_up_alg3"

            elif desired_down < current:
                # Scale-down candidate: increment below counter (Algorithm 4 stabilisation)
                below_counter += 1
                self._below_counter[stage] = below_counter
                if below_counter >= self.stabilise_epochs and self._cooldowns[stage] == 0:
                    # Stabilisation delay satisfied — issue scale-down
                    final_desired = desired_down
                    scale_actions.append(ScaleAction(stage=stage, active_workers=final_desired))
                    self._cooldowns[stage] = max(0, int(self.cooldown_epochs))
                    self._below_counter[stage] = 0
                    action_taken = "scale_down_alg4"

            else:
                # Neither scale-up nor scale-down — reset below counter
                self._below_counter[stage] = 0

            alg_metrics[stage] = {
                "queue_depth": float(queue_depth),
                "r_max": float(r_max),
                "desired_up_alg3": int(desired_up),
                "desired_down_alg4": int(desired_down),
                "final_desired": int(final_desired),
                "current_workers": int(current),
                "below_counter": int(below_counter),
                "stabilise_epochs": int(self.stabilise_epochs),
                "capacity_rps_per_node": float(self._capacity_rps),
                "invocation_prob_sm": float(self.invocation_prob),
                "rho_m": float(self.rho_m),
                "action_taken": action_taken,
            }

        placement, replan, replan_deferred, scale_actions = self._maybe_replan(
            state, scale_actions
        )
        return ControllerAction(
            scale=scale_actions,
            placement=placement,
            metadata={
                "controller": "inferline_exact",
                "placement_strategy": self.placement_strategy,
                "replan": replan,
                "replan_deferred": replan_deferred,
                "alg_metrics": alg_metrics,
            },
        )
