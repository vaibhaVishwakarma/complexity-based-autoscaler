"""
conformal_controllers.py — Six-Competitor Controller Cohort for Conformal Autoscaler Evaluation.

Role: Controller implementations for Stage 3 benchmarking of the Conformal Autoscaler pipeline.
Gate stage: Simulation runtime (each controller drives worker-pool decisions per epoch).

Inputs (from ContinuumBench runner):
  - state: ControllerState
      state.worker_pools     — dict[stage_name → WorkerPoolSnapshot]
      state.queue_depths     — dict[stage_name → int]
      state.epoch            — current simulation epoch (int)
      state.metadata         — dict carrying conformal telemetry injected by the scenario:
            "fast_path_fraction"  float — current fp(t) from gate1 scoring
            "mean_set_size"       float — average conformal set size
            "effective_alpha"     float — realised miscoverage rate
      state.placement        — current service→node mapping
  - Gate 2 contract: contracts.gate2 — batch-size-aware capacity surface for InferLineController.
  - Gate 1 contract: contracts.gate1 — calibrated q_hat / alpha for conformal decision boundary.

Outputs:
  Each controller's `step(state)` returns a ControllerAction with:
    - scale:     list[ScaleAction(stage, active_workers)]
    - placement: optional dict[service_id → node_id]
    - metadata:  controller diagnostics dict (logged by runner)

Controllers Implemented:
  1. FixedCapacityController      — static peak-provisioned baseline (over-provision oracle).
  2. InferLineController          — multi-scale traffic-envelope predictive autoscaler
                                    (reimplements SoCC '20 Algorithms 3 & 4).
  3. ComplexityBlindPredictiveController — EMA forecast on λ(t) only; ignores fp signal.
  4. ConformalAutoscalerController       — our proposed system: uses λ_slow = λ * (1 - fp)
                                    with proactive preemption on fp↓ and
                                    fast scale-down on fp recovery.

Note: HPAController and KEDAController already exist in autoscaling_baselines.py.
      They are part of the 6-competitor cohort and are imported directly from there.
      This file adds only the four controllers not present in the baseline module.
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
# Constants (immutable — AGENTS.md §2)
# ---------------------------------------------------------------------------

#: Canonical RNG seed for all tie-breaking and stochastic tie-breaks.
SEED: int = 42

#: Fallback capacity (RPS/node) if Gate 2 contract cannot be loaded.
#: Conservative lower bound — avoids over-provisioning on load failure.
_GATE2_FALLBACK_RPS_PER_NODE: float = 40.0

#: Fallback fast-path fraction if metadata field is absent.
_FP_DEFAULT: float = 0.50


# ---------------------------------------------------------------------------
# Gate 2 dynamic capacity helper
# ---------------------------------------------------------------------------


def _load_gate2_capacity(batch_size: int = 8, batch_timeout_s: float = 0.040) -> float:
    """Load the Gate 2 hardware profile and return capacity in RPS/node.

    Uses contracts.gate2.load_gate2_profiles() + compute_service_capacity_rps().
    Falls back to _GATE2_FALLBACK_RPS_PER_NODE if the contract cannot be loaded,
    logging a warning. Never hardcodes the capacity value (AGENTS.md §2).

    Args:
        batch_size:      Triton dynamic batching batch size (default 8 per strategy §3.2).
        batch_timeout_s: Batch formation timeout in seconds (default 40 ms).

    Returns:
        Estimated capacity in RPS per node.
    """
    try:
        # Lazy import to avoid hard dep at module import time
        from contracts.gate2 import load_gate2_profiles  # type: ignore[import]

        profiles = load_gate2_profiles()
        return profiles.compute_service_capacity_rps(
            batch_size=batch_size,
            batch_timeout_s=batch_timeout_s,
        )
    except Exception as exc:  # pragma: no cover — contract path may not exist in unit tests
        import warnings
        warnings.warn(
            f"Gate2 contract load failed ({exc}); "
            f"falling back to {_GATE2_FALLBACK_RPS_PER_NODE} RPS/node.",
            stacklevel=2,
        )
        return _GATE2_FALLBACK_RPS_PER_NODE


def _load_gate1_q_hat() -> float:
    """Load the Gate 1 calibrated q_hat for conformal coverage boundary.

    Returns q_hat from Gate1CalibrationConfig, or a safe default of 1.0 if
    the contract is unavailable. Never hardcodes the q_hat value (AGENTS.md §2).
    """
    try:
        from contracts.gate1 import load_gate1_config  # type: ignore[import]

        cfg = load_gate1_config()
        return float(cfg.q_hat)
    except Exception as exc:  # pragma: no cover
        import warnings
        warnings.warn(f"Gate1 contract load failed ({exc}); defaulting q_hat=1.0.", stacklevel=2)
        return 1.0


# ---------------------------------------------------------------------------
# 1. FixedCapacityController
# ---------------------------------------------------------------------------


@dataclass
class FixedCapacityController(_PlacementReplanMixin):
    """Fixed peak-provisioned static baseline — the over-provision oracle.

    Behaviour: Immediately scales every stage to `peak_workers` and holds.
    No scaling decisions are made after the initial provisioning.
    This sets the theoretical minimum SLO violation rate (always-on GPU cost).

    Use-case: Establishes the 'money is no object' upper bound on SLO satisfaction
    and the lower bound on cost efficiency. All other controllers must beat it on cost.

    Args:
        peak_workers: Number of workers to maintain at all times per stage.
        placement_strategy: Eclypse placement heuristic.
    """

    peak_workers: int = 25

    def step(self, state: ControllerState) -> ControllerAction:
        """Hold every stage at peak_workers; scale on first epoch only."""
        scale_actions: List[ScaleAction] = []

        for stage, snapshot in state.worker_pools.items():
            # Only emit a ScaleAction if the current active count differs from peak
            desired = max(
                snapshot.min_workers,
                min(snapshot.max_workers, int(self.peak_workers)),
            )
            if snapshot.active_workers != desired:
                scale_actions.append(ScaleAction(stage=stage, active_workers=desired))

        placement, replan, replan_deferred, scale_actions = self._maybe_replan(
            state, scale_actions
        )
        return ControllerAction(
            scale=scale_actions,
            placement=placement,
            metadata={
                "controller": "fixed_capacity",
                "peak_workers": int(self.peak_workers),
                "placement_strategy": self.placement_strategy,
                "replan": replan,
                "replan_deferred": replan_deferred,
            },
        )


# ---------------------------------------------------------------------------
# 2. InferLineController
# ---------------------------------------------------------------------------


@dataclass
class InferLineController(_PlacementReplanMixin):
    """InferLine-style multi-scale traffic envelope autoscaler (SoCC '20, Algs 3 & 4).

    InferLine computes a traffic envelope using multi-scale exponential smoothing
    over a history of observed arrival rates, then provisions workers to satisfy
    the envelope under the current service capacity budget. It adds a stabilisation
    delay before acting on a scale-down decision to avoid thrashing.

    Key design decisions (per strategy §6 and SoCC '20):
      - Multi-scale EMA: maintains short (α_fast), medium (α_mid), and long (α_slow)
        smoothed estimates. The envelope = max(fast, mid, long) provides headroom.
      - Stabilisation delay: scale-down is deferred until the envelope stays below
        the current provisioning for `stabilise_epochs` consecutive epochs (~15 s).
      - Batch-size optimisation: capacity per node is loaded from Gate 2 contract
        (never hardcoded) via `compute_service_capacity_rps(batch_size, timeout)`.
      - Complexity blindness: does NOT consume fp(t) from metadata. Operates purely
        on observed queue depth as the utilisation proxy (mirrors InferLine's design).

    Args:
        alpha_fast:         EMA weight for fast (reactive) envelope. Larger = more reactive.
        alpha_mid:          EMA weight for medium envelope.
        alpha_slow:         EMA weight for slow (trend) envelope.
        stabilise_epochs:   Epochs envelope must stay below threshold before scale-down.
        batch_size:         Triton batch size for Gate 2 capacity lookup.
        batch_timeout_s:    Batch formation timeout for Gate 2 capacity lookup.
        safety_margin:      Multiplicative headroom factor on the envelope (e.g. 1.15 = 15%).
        min_replicas:       Minimum active workers per stage.
        cooldown_epochs:    Minimum epochs between scale-up events.
    """

    alpha_fast: float = 0.60
    alpha_mid: float = 0.20
    alpha_slow: float = 0.05
    stabilise_epochs: int = 15         # ~15 s at 1 epoch/s before acting on scale-down
    batch_size: int = 8
    batch_timeout_s: float = 0.040
    safety_margin: float = 1.15       # 15% headroom above envelope
    min_replicas: int = 1
    cooldown_epochs: int = 2

    # Internal state — not constructor arguments
    _ema_fast: Dict[str, float] = field(default_factory=dict, init=False)
    _ema_mid: Dict[str, float] = field(default_factory=dict, init=False)
    _ema_slow: Dict[str, float] = field(default_factory=dict, init=False)
    _below_counter: Dict[str, int] = field(default_factory=dict, init=False)
    _cooldowns: Dict[str, int] = field(default_factory=dict, init=False)
    _capacity_rps: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Initialise placement mixin and load Gate 2 capacity once."""
        super().__post_init__()
        # Load capacity from Gate 2 contract (never hardcoded — AGENTS.md §2)
        self._capacity_rps = _load_gate2_capacity(
            batch_size=self.batch_size,
            batch_timeout_s=self.batch_timeout_s,
        )

    def _update_ema(self, stage: str, observed: float) -> Tuple[float, float, float]:
        """Update three EMA estimates with new observation; return (fast, mid, slow)."""
        # Initialise to first observation if not yet seen
        prev_fast = self._ema_fast.get(stage, observed)
        prev_mid = self._ema_mid.get(stage, observed)
        prev_slow = self._ema_slow.get(stage, observed)

        new_fast = self.alpha_fast * observed + (1.0 - self.alpha_fast) * prev_fast
        new_mid = self.alpha_mid * observed + (1.0 - self.alpha_mid) * prev_mid
        new_slow = self.alpha_slow * observed + (1.0 - self.alpha_slow) * prev_slow

        self._ema_fast[stage] = new_fast
        self._ema_mid[stage] = new_mid
        self._ema_slow[stage] = new_slow

        return new_fast, new_mid, new_slow

    def step(self, state: ControllerState) -> ControllerAction:
        """Return InferLine-style scale and placement actions."""
        scale_actions: List[ScaleAction] = []
        envelope_metrics: Dict[str, dict] = {}

        for stage, snapshot in state.worker_pools.items():
            # Decrement cooldown counter
            self._cooldowns[stage] = max(0, self._cooldowns.get(stage, 0) - 1)

            # Use queue depth per active worker as the utilisation signal (InferLine §3.1)
            current = max(1, int(snapshot.active_workers))
            observed_queue = float(state.queue_depths.get(stage, 0))
            # Normalise to effective RPS: queue items × capacity_per_worker
            observed_rps = observed_queue * (self._capacity_rps / float(current))

            # Update multi-scale EMAs (Algorithm 3 in SoCC '20)
            fast, mid, slow = self._update_ema(stage, observed_rps)

            # Traffic envelope = max of three scales + safety margin (Algorithm 4)
            envelope = max(fast, mid, slow) * self.safety_margin
            desired_workers = math.ceil(envelope / max(1e-9, self._capacity_rps))
            min_replicas = max(snapshot.min_workers, int(self.min_replicas))
            desired_workers = max(min_replicas, min(snapshot.max_workers, desired_workers))

            current_workers = int(snapshot.active_workers)

            # Scale-up: act immediately if envelope exceeds current provisioning
            if desired_workers > current_workers and self._cooldowns[stage] == 0:
                scale_actions.append(ScaleAction(stage=stage, active_workers=desired_workers))
                self._cooldowns[stage] = max(0, int(self.cooldown_epochs))
                self._below_counter[stage] = 0

            # Scale-down: enforce stabilisation delay (Algorithm 4, §3.4)
            elif desired_workers < current_workers:
                self._below_counter[stage] = self._below_counter.get(stage, 0) + 1
                if self._below_counter[stage] >= self.stabilise_epochs:
                    # Envelope has been below threshold for long enough — safe to shrink
                    scale_actions.append(ScaleAction(stage=stage, active_workers=desired_workers))
                    self._below_counter[stage] = 0
            else:
                # Envelope within current provisioning — reset stability counter
                self._below_counter[stage] = 0

            envelope_metrics[stage] = {
                "ema_fast": float(fast),
                "ema_mid": float(mid),
                "ema_slow": float(slow),
                "envelope_rps": float(envelope),
                "desired_workers": int(desired_workers),
                "below_counter": int(self._below_counter.get(stage, 0)),
                "capacity_rps_per_node": float(self._capacity_rps),
            }

        placement, replan, replan_deferred, scale_actions = self._maybe_replan(
            state, scale_actions
        )
        return ControllerAction(
            scale=scale_actions,
            placement=placement,
            metadata={
                "controller": "inferline",
                "placement_strategy": self.placement_strategy,
                "replan": replan,
                "replan_deferred": replan_deferred,
                "envelope_metrics": envelope_metrics,
            },
        )


# ---------------------------------------------------------------------------
# 3. ComplexityBlindPredictiveController
# ---------------------------------------------------------------------------


@dataclass
class ComplexityBlindPredictiveController(_PlacementReplanMixin):
    """Complexity-blind predictive autoscaler — EMA forecast on λ(t), fp ignored.

    This controller represents the class of predictive ML-serving autoscalers that
    forecast traffic volume (λ) but have no mechanism to observe or react to
    changes in request complexity (fp). It assumes fp is constant at the calibration
    baseline (fp_assumed = FP_SUITE1_FIXED = 0.50) when computing required capacity.

    Design:
      - Uses a single EMA forecast of observed queue depth as a proxy for arrival rate.
      - Applies a fixed assumed_fp to convert volume forecast → effective slow-path load.
      - Provisions `ceil(λ_forecast * (1 - assumed_fp) / capacity_rps)` workers.
      - Includes a cooldown to prevent thrashing.

    Why this matters: In Suite 2 and 3, fp diverges from assumed_fp — causing this
    controller to systematically under-provision when fp drops and over-provision when
    fp rises. This gap quantifies the value of the conformal fp telemetry.

    Args:
        alpha:             EMA weight for queue-depth smoothing. Larger = more reactive.
        assumed_fp:        Fixed fast-path assumption (never updated from metadata).
        batch_size:        Triton batch size for Gate 2 capacity lookup.
        batch_timeout_s:   Batch timeout for Gate 2 capacity lookup.
        safety_margin:     Headroom multiplier on forecast before provisioning.
        min_replicas:      Minimum active workers per stage.
        cooldown_epochs:   Minimum epochs between scale events.
    """

    alpha: float = 0.30
    assumed_fp: float = 0.50              # frozen at calibration baseline — never updated
    batch_size: int = 8
    batch_timeout_s: float = 0.040
    safety_margin: float = 1.20
    min_replicas: int = 1
    cooldown_epochs: int = 2

    _ema: Dict[str, float] = field(default_factory=dict, init=False)
    _cooldowns: Dict[str, int] = field(default_factory=dict, init=False)
    _capacity_rps: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Initialise placement mixin and load Gate 2 capacity once."""
        super().__post_init__()
        # Load capacity from Gate 2 contract (never hardcoded — AGENTS.md §2)
        self._capacity_rps = _load_gate2_capacity(
            batch_size=self.batch_size,
            batch_timeout_s=self.batch_timeout_s,
        )

    def step(self, state: ControllerState) -> ControllerAction:
        """Return complexity-blind EMA-predictive scale and placement actions."""
        scale_actions: List[ScaleAction] = []
        forecast_metrics: Dict[str, dict] = {}

        for stage, snapshot in state.worker_pools.items():
            self._cooldowns[stage] = max(0, self._cooldowns.get(stage, 0) - 1)

            observed_queue = float(state.queue_depths.get(stage, 0))
            prev_ema = self._ema.get(stage, observed_queue)

            # EMA forecast of queue depth
            ema = self.alpha * observed_queue + (1.0 - self.alpha) * prev_ema
            self._ema[stage] = ema

            # Convert queue-depth forecast to estimated arrival RPS
            # (assumes 1 queue item represents 1 unserviced RPS unit at current capacity)
            lambda_forecast = ema * (self._capacity_rps / max(1, snapshot.active_workers))

            # Complexity-blind: assume fp is always assumed_fp (never from metadata)
            # λ_slow = λ * (1 - fp)  ← fp is frozen at assumed_fp
            lambda_slow = lambda_forecast * (1.0 - self.assumed_fp)

            desired_workers = math.ceil(
                lambda_slow * self.safety_margin / max(1e-9, self._capacity_rps)
            )
            min_replicas = max(snapshot.min_workers, int(self.min_replicas))
            desired_workers = max(min_replicas, min(snapshot.max_workers, desired_workers))

            forecast_metrics[stage] = {
                "observed_queue": float(observed_queue),
                "ema_queue": float(ema),
                "lambda_forecast_rps": float(lambda_forecast),
                "assumed_fp": float(self.assumed_fp),
                "lambda_slow_rps": float(lambda_slow),
                "desired_workers": int(desired_workers),
                "actual_fp_from_metadata": float(
                    state.metadata.get("fast_path_fraction", _FP_DEFAULT)
                ),  # logged but NOT used in decisions
            }

            if self._cooldowns[stage] == 0 and desired_workers != snapshot.active_workers:
                scale_actions.append(ScaleAction(stage=stage, active_workers=desired_workers))
                self._cooldowns[stage] = max(0, int(self.cooldown_epochs))

        placement, replan, replan_deferred, scale_actions = self._maybe_replan(
            state, scale_actions
        )
        return ControllerAction(
            scale=scale_actions,
            placement=placement,
            metadata={
                "controller": "complexity_blind_predictive",
                "placement_strategy": self.placement_strategy,
                "replan": replan,
                "replan_deferred": replan_deferred,
                "forecast_metrics": forecast_metrics,
            },
        )


# ---------------------------------------------------------------------------
# 4. ConformalAutoscalerController
# ---------------------------------------------------------------------------


@dataclass
class ConformalAutoscalerController(_PlacementReplanMixin):
    """Conformal Autoscaler — our proposed system (Strategy §8).

    This controller is the central contribution of the paper. It consumes the
    real-time conformal prediction telemetry (fast_path_fraction, mean_set_size,
    effective_alpha) injected into state.metadata by the edge inference layer, and
    makes worker-pool decisions based on the effective GPU slow-path load:

        λ_slow(t) = λ(t) × (1 − fp(t))

    where fp(t) is the live fast_path_fraction from Gate 1 conformal scoring.

    Key mechanisms (per strategy §8.3):

    1. PROACTIVE PREEMPTION on fp↓:
       When fp(t) drops below fp_preempt_threshold (complexity increasing), the
       controller immediately scales up to handle the increase in slow-path load
       BEFORE the queue backlog grows. This is the primary differentiation from
       all reactive baselines (including InferLine which waits for queue signals).

    2. FAST SCALE-DOWN on fp↑:
       When fp(t) ≥ fp_recovery_threshold AND mean_set_size ≤ set_size_recovery_max
       for `recovery_epochs_required` consecutive epochs, the controller asserts that
       the model has returned to a simpler operating point and scales down.

    3. COVERAGE-BOUNDED DECISIONS:
       The set_size field from conformal scoring signals ambiguity: large sets mean
       the model is uncertain and more requests will fall to the slow path. The
       controller adds headroom proportional to mean_set_size deviation from 1.0.

    Metadata fields consumed (injected by scenario edge layer):
      fast_path_fraction  (float): fraction of requests resolved at edge [0, 1]
      mean_set_size       (float): average conformal prediction set size (1.0 = certain)
      effective_alpha     (float): realised miscoverage rate (should track gate1 alpha)

    Args:
        capacity_rps_per_node:  Override for RPS/node (0 = load from Gate 2 contract).
        fp_preempt_threshold:   fp below this triggers proactive scale-up.
        fp_recovery_threshold:  fp above this (with low set size) allows scale-down.
        set_size_recovery_max:  Max mean_set_size to permit scale-down.
        set_size_headroom_coef: Headroom multiplier per unit set_size above 1.0.
        recovery_epochs_required: Consecutive epochs of recovery signal before shrink.
        alpha_lambda:           EMA weight for λ_slow(t) smoothing.
        safety_margin:          Base headroom multiplier on capacity estimate.
        min_replicas:           Minimum active workers per stage.
        cooldown_epochs:        Minimum epochs between scale-up events.
        batch_size:             Triton batch size for Gate 2 capacity lookup.
        batch_timeout_s:        Batch timeout for Gate 2 capacity lookup.
    """

    capacity_rps_per_node: float = 0.0        # 0 = auto-load from Gate 2
    fp_preempt_threshold: float = 0.35        # below this → proactive scale-up
    fp_recovery_threshold: float = 0.45       # above this (sustained) → scale-down allowed
    set_size_recovery_max: float = 1.80       # mean_set_size ≤ this for scale-down
    set_size_headroom_coef: float = 0.10      # extra headroom per unit set_size above 1.0
    recovery_epochs_required: int = 3         # epochs of recovery signal before shrink
    alpha_lambda: float = 0.35               # EMA weight for λ_slow smoothing
    safety_margin: float = 1.20
    min_replicas: int = 1
    cooldown_epochs: int = 2
    batch_size: int = 8
    batch_timeout_s: float = 0.040

    # Internal state — not constructor args
    _ema_lambda_slow: Dict[str, float] = field(default_factory=dict, init=False)
    _cooldowns: Dict[str, int] = field(default_factory=dict, init=False)
    _recovery_counter: Dict[str, int] = field(default_factory=dict, init=False)
    _capacity_rps: float = field(default=0.0, init=False)
    _q_hat: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Load Gate 1 and Gate 2 contracts; initialise placement mixin."""
        super().__post_init__()

        # Load capacity from Gate 2 contract (never hardcoded — AGENTS.md §2)
        if self.capacity_rps_per_node > 0.0:
            self._capacity_rps = float(self.capacity_rps_per_node)
        else:
            self._capacity_rps = _load_gate2_capacity(
                batch_size=self.batch_size,
                batch_timeout_s=self.batch_timeout_s,
            )

        # Load Gate 1 q_hat for coverage-bounded headroom decisions
        self._q_hat = _load_gate1_q_hat()

    def _fp(self, state: ControllerState) -> float:
        """Extract fast_path_fraction from metadata; fall back to default if absent."""
        raw = state.metadata.get("fast_path_fraction", _FP_DEFAULT)
        return float(max(0.0, min(1.0, raw)))

    def _mean_set_size(self, state: ControllerState) -> float:
        """Extract mean_set_size from metadata; default = 1.0 (certain predictions)."""
        return float(state.metadata.get("mean_set_size", 1.0))

    def _in_recovery(self, fp_t: float, mean_set_size: float) -> bool:
        """Return True when both fp and set_size signals indicate model recovery."""
        return (
            fp_t >= self.fp_recovery_threshold
            and mean_set_size <= self.set_size_recovery_max
        )

    def _compute_desired_workers(
        self,
        stage: str,
        snapshot,
        lambda_slow_ema: float,
        mean_set_size: float,
        fp_t: float,
    ) -> int:
        """Compute the desired worker count for a stage given the conformal signals.

        Headroom is amplified when:
          (a) fp_t is below preemption threshold (proactive headroom on fp drop), or
          (b) mean_set_size is above 1.0 (model ambiguity → more slow-path spill).
        """
        # Base desired from EMA of λ_slow
        base_margin = self.safety_margin

        # Proactive headroom: amplify when fp drops below preemption threshold
        if fp_t < self.fp_preempt_threshold:
            # Extra headroom proportional to distance below threshold
            deficit = self.fp_preempt_threshold - fp_t
            base_margin += deficit  # e.g., fp=0.20 → deficit=0.15 → margin=1.35

        # Coverage-bounded headroom: amplify when set_size indicates ambiguity
        set_size_excess = max(0.0, mean_set_size - 1.0)
        base_margin += self.set_size_headroom_coef * set_size_excess

        desired = math.ceil(lambda_slow_ema * base_margin / max(1e-9, self._capacity_rps))
        min_replicas = max(snapshot.min_workers, int(self.min_replicas))
        return max(min_replicas, min(snapshot.max_workers, desired))

    def step(self, state: ControllerState) -> ControllerAction:
        """Return conformal-aware scale and placement actions.

        Decision logic:
          1. Compute λ_slow(t) = queue_depth × capacity_rps / active_workers × (1 − fp(t)).
          2. Update EMA of λ_slow with alpha_lambda.
          3. Compute desired_workers with proactive + coverage-bounded headroom.
          4. Proactive scale-up: emit immediately if fp < fp_preempt_threshold (no cooldown).
          5. Normal scale-up: emit with cooldown if desired > current.
          6. Fast scale-down: emit only if recovery_counter ≥ recovery_epochs_required
             AND fp ≥ fp_recovery_threshold AND mean_set_size ≤ set_size_recovery_max.
        """
        scale_actions: List[ScaleAction] = []
        conformal_metrics: Dict[str, dict] = {}

        # Extract conformal telemetry from metadata (injected by scenario edge layer)
        fp_t = self._fp(state)
        mean_set_size = self._mean_set_size(state)
        effective_alpha = float(state.metadata.get("effective_alpha", 0.10))

        for stage, snapshot in state.worker_pools.items():
            self._cooldowns[stage] = max(0, self._cooldowns.get(stage, 0) - 1)

            current_workers = int(snapshot.active_workers)
            observed_queue = float(state.queue_depths.get(stage, 0))

            # --- Compute λ_slow (effective GPU demand) ---
            # λ_slow = (queue rate estimate) × (1 − fp) measures actual slow-path load
            capacity_denominator = max(1, current_workers)
            lambda_hat = observed_queue * (self._capacity_rps / float(capacity_denominator))
            lambda_slow_t = lambda_hat * (1.0 - fp_t)

            # EMA smoothing of λ_slow to reduce noise
            prev_ema = self._ema_lambda_slow.get(stage, lambda_slow_t)
            ema_lambda_slow = (
                self.alpha_lambda * lambda_slow_t + (1.0 - self.alpha_lambda) * prev_ema
            )
            self._ema_lambda_slow[stage] = ema_lambda_slow

            # --- Compute desired workers with conformal headroom ---
            desired_workers = self._compute_desired_workers(
                stage, snapshot, ema_lambda_slow, mean_set_size, fp_t
            )

            # --- Update recovery counter ---
            if self._in_recovery(fp_t, mean_set_size):
                self._recovery_counter[stage] = self._recovery_counter.get(stage, 0) + 1
            else:
                self._recovery_counter[stage] = 0  # reset on any non-recovery epoch

            recovery_count = self._recovery_counter.get(stage, 0)

            # --- Scaling decisions ---
            proactive_triggered = False

            if desired_workers > current_workers:
                # Scale-up path
                if fp_t < self.fp_preempt_threshold:
                    # PROACTIVE PREEMPTION: bypass cooldown when fp drops sharply
                    # The conformal signal is the early warning — act before queue grows
                    scale_actions.append(ScaleAction(stage=stage, active_workers=desired_workers))
                    self._cooldowns[stage] = max(0, int(self.cooldown_epochs))
                    self._recovery_counter[stage] = 0
                    proactive_triggered = True
                elif self._cooldowns[stage] == 0:
                    # Normal scale-up (within cooldown bounds)
                    scale_actions.append(ScaleAction(stage=stage, active_workers=desired_workers))
                    self._cooldowns[stage] = max(0, int(self.cooldown_epochs))
                    self._recovery_counter[stage] = 0

            elif desired_workers < current_workers:
                # Scale-down path: require sustained recovery signal
                if (
                    recovery_count >= self.recovery_epochs_required
                    and self._in_recovery(fp_t, mean_set_size)
                    and self._cooldowns[stage] == 0
                ):
                    # FAST SCALE-DOWN: fp has recovered, set_size is low, sustained
                    scale_actions.append(ScaleAction(stage=stage, active_workers=desired_workers))
                    self._cooldowns[stage] = max(0, int(self.cooldown_epochs))
                    self._recovery_counter[stage] = 0

            conformal_metrics[stage] = {
                "fp_t": float(fp_t),
                "mean_set_size": float(mean_set_size),
                "effective_alpha": float(effective_alpha),
                "q_hat": float(self._q_hat),
                "lambda_slow_t": float(lambda_slow_t),
                "ema_lambda_slow": float(ema_lambda_slow),
                "desired_workers": int(desired_workers),
                "current_workers": int(current_workers),
                "recovery_counter": int(recovery_count),
                "proactive_triggered": bool(proactive_triggered),
                "capacity_rps_per_node": float(self._capacity_rps),
            }

        placement, replan, replan_deferred, scale_actions = self._maybe_replan(
            state, scale_actions
        )
        return ControllerAction(
            scale=scale_actions,
            placement=placement,
            metadata={
                "controller": "conformal_autoscaler",
                "placement_strategy": self.placement_strategy,
                "replan": replan,
                "replan_deferred": replan_deferred,
                "fp_t": float(fp_t),
                "mean_set_size": float(mean_set_size),
                "conformal_metrics": conformal_metrics,
            },
        )
