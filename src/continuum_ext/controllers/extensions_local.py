"""
extensions_local.py — ContinuumBench Custom Controller Extensions

Role:
    Extension hook for ContinuumBench controller discovery. Defines all project-specific
    controllers not included in the upstream autoscaling_baselines.py module, including
    the `evolved_conformal` controller that bridges OpenEvolve candidate policies into
    the ContinuumBench simulation runtime.

Gate Stage:    All pipeline stages (used by Steps 5, 6, 7)
AGENTS.md Rule #1 — This file is extended (never modified) when adding new controllers.
AGENTS.md Rule #2 — evolved_conformal loads policy path from env var; no hardcoding.
AGENTS.md Rule #4 — Self-documenting header and inline comments.
"""

from __future__ import annotations

import importlib.util
import math
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from continuum_bench.controllers.autoscaling_baselines import _PlacementReplanMixin
from continuum_bench.controllers.interfaces import (
    ControllerAction,
    ControllerState,
    ScaleAction,
)


@dataclass
class SimpleAutoscaler(_PlacementReplanMixin):
    """A minimal, transparent queue-threshold autoscaler.

    Demonstrates how custom autoscalers integrate with ContinuumBench:
    1. Inspects queue_depths and current worker count for each pool in state.worker_pools.
    2. Decides to scale up or down based on simple thresholds.
    3. Delegates placement and worker activation to _PlacementReplanMixin (Eclypse substrate).
    """

    scale_up_queue_threshold: int = 4
    scale_down_queue_threshold: int = 1
    cooldown_epochs: int = 1

    _cooldowns: Dict[str, int] = field(default_factory=dict, init=False)

    def step(self, state: ControllerState) -> ControllerAction:
        """Evaluate worker pools and emit scaling & placement actions."""
        scale_actions: List[ScaleAction] = []
        metrics: Dict[str, Dict[str, int]] = {}

        for stage, snapshot in state.worker_pools.items():
            self._cooldowns[stage] = max(0, self._cooldowns.get(stage, 0) - 1)
            queue_len = int(state.queue_depths.get(stage, 0))
            current_workers = snapshot.active_workers
            desired_workers = current_workers

            # Scale up if queue exceeds threshold and below max
            if queue_len >= self.scale_up_queue_threshold and current_workers < snapshot.max_workers:
                desired_workers = min(snapshot.max_workers, current_workers + 1)
            # Scale down if queue is below threshold and above min
            elif queue_len <= self.scale_down_queue_threshold and current_workers > snapshot.min_workers:
                desired_workers = max(snapshot.min_workers, current_workers - 1)

            metrics[stage] = {
                "queue_length": queue_len,
                "current_workers": current_workers,
                "desired_workers": desired_workers,
            }

            if self._cooldowns[stage] == 0 and desired_workers != current_workers:
                scale_actions.append(ScaleAction(stage=stage, active_workers=desired_workers))
                self._cooldowns[stage] = max(0, int(self.cooldown_epochs))

        # Replan placement if necessary using Eclypse placement strategy (e.g. best_fit)
        placement, replan, replan_deferred, scale_actions = self._maybe_replan(
            state,
            scale_actions,
        )

        return ControllerAction(
            scale=scale_actions,
            placement=placement,
            metadata={
                "controller": "simple_autoscaler",
                "pool_metrics": metrics,
                "replan": replan,
            },
        )


def build(name: str, config: Dict[str, Any], runner: Any) -> Optional[Any]:
    """Controller extension hook loaded by ContinuumBench runner."""
    if name in {"simple", "simple_autoscaler", "basic_autoscaler"}:
        placement_cfg = config.get("placement", {})
        scaling_cfg = config.get("scaling", {})

        return SimpleAutoscaler(
            placement_strategy=str(placement_cfg.get("strategy", "best_fit")),
            replan_every_epochs=int(placement_cfg.get("place_every_epochs", 3)),
            scale_up_queue_threshold=int(scaling_cfg.get("queue_up_threshold", 4)),
            scale_down_queue_threshold=int(scaling_cfg.get("queue_down_threshold", 1)),
            cooldown_epochs=int(scaling_cfg.get("cooldown_epochs", 1)),
        )

    if name in {"fixed", "fixed_capacity"}:
        try:
            from continuum_bench.controllers.conformal_controllers import FixedCapacityController
        except ImportError:
            from continuum_ext.controllers.conformal_controllers import FixedCapacityController

        scaling_cfg = config.get("scaling", {})
        pool_cfg = scaling_cfg.get("pools", {}).get("CloudRefine", {})
        peak_workers = int(scaling_cfg.get("peak_workers", pool_cfg.get("max_workers", 8)))
        placement_cfg = config.get("placement", {})
        return FixedCapacityController(
            peak_workers=peak_workers,
            placement_strategy=str(placement_cfg.get("strategy", "best_fit")),
            replan_every_epochs=int(placement_cfg.get("place_every_epochs", 3)),
        )

    if name in {"inferline", "inferline_controller"}:
        try:
            from continuum_bench.controllers.conformal_controllers import InferLineController
        except ImportError:
            from continuum_ext.controllers.conformal_controllers import InferLineController

        inferline_cfg = config.get("autoscaling", {}).get("inferline", {})
        placement_cfg = config.get("placement", {})
        return InferLineController(
            placement_strategy=str(placement_cfg.get("strategy", "best_fit")),
            replan_every_epochs=int(placement_cfg.get("place_every_epochs", 3)),
            alpha_fast=float(inferline_cfg.get("alpha_fast", 0.60)),
            alpha_mid=float(inferline_cfg.get("alpha_mid", 0.20)),
            alpha_slow=float(inferline_cfg.get("alpha_slow", 0.05)),
            stabilise_epochs=int(inferline_cfg.get("stabilise_epochs", 15)),
            safety_margin=float(inferline_cfg.get("safety_margin", 1.15)),
            min_replicas=int(inferline_cfg.get("min_replicas", 1)),
            cooldown_epochs=int(inferline_cfg.get("cooldown_epochs", 2)),
        )

    if name in {"complexity_blind", "complexity_blind_predictive", "blind_predictive"}:
        try:
            from continuum_bench.controllers.conformal_controllers import ComplexityBlindPredictiveController
        except ImportError:
            from continuum_ext.controllers.conformal_controllers import ComplexityBlindPredictiveController

        cb_cfg = config.get("autoscaling", {}).get("complexity_blind", {})
        placement_cfg = config.get("placement", {})
        return ComplexityBlindPredictiveController(
            placement_strategy=str(placement_cfg.get("strategy", "best_fit")),
            replan_every_epochs=int(placement_cfg.get("place_every_epochs", 3)),
            alpha=float(cb_cfg.get("alpha", 0.30)),
            assumed_fp=float(cb_cfg.get("assumed_fp", 0.50)),
            safety_margin=float(cb_cfg.get("safety_margin", 1.20)),
            min_replicas=int(cb_cfg.get("min_replicas", 1)),
            cooldown_epochs=int(cb_cfg.get("cooldown_epochs", 2)),
        )

    if name in {"conformal", "conformal_autoscaler"}:
        try:
            from continuum_bench.controllers.conformal_controllers import ConformalAutoscalerController
        except ImportError:
            from continuum_ext.controllers.conformal_controllers import ConformalAutoscalerController

        ca_cfg = config.get("autoscaling", {}).get("conformal", {})
        placement_cfg = config.get("placement", {})
        return ConformalAutoscalerController(
            placement_strategy=str(placement_cfg.get("strategy", "best_fit")),
            replan_every_epochs=int(placement_cfg.get("place_every_epochs", 3)),
            fp_preempt_threshold=float(ca_cfg.get("fp_preempt_threshold", 0.35)),
            fp_recovery_threshold=float(ca_cfg.get("fp_recovery_threshold", 0.45)),
            set_size_recovery_max=float(ca_cfg.get("set_size_recovery_max", 1.80)),
            alpha_lambda=float(ca_cfg.get("alpha_lambda", 0.35)),
            safety_margin=float(ca_cfg.get("safety_margin", 1.20)),
            min_replicas=int(ca_cfg.get("min_replicas", 1)),
            cooldown_epochs=int(ca_cfg.get("cooldown_epochs", 2)),
        )

    if name in {"evolved_conformal", "evolved_conformal_autoscaler"}:
        policy_path = os.environ.get("EVOLUTION_CANDIDATE_PATH", "")
        if not policy_path:
            raise ValueError(
                "evolved_conformal controller requires EVOLUTION_CANDIDATE_PATH env var "
                "pointing to the candidate policy .py file."
            )
        placement_cfg = config.get("placement", {})
        return EvolvedConformalController(
            policy_path=policy_path,
            placement_strategy=str(placement_cfg.get("strategy", "best_fit")),
            replan_every_epochs=int(placement_cfg.get("place_every_epochs", 3)),
        )

    return None


# ─────────────────────────────────────────────────────────────────────────────
# EVOLVED CONFORMAL CONTROLLER
# Bridge between OpenEvolve candidate policy files and the ContinuumBench
# simulation runtime. Maps ControllerState → TelemetricState at each epoch
# using sliding-window velocity estimates for derived features.
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class EvolvedConformalController(_PlacementReplanMixin):
    """
    Runtime bridge between an OpenEvolve candidate policy and the ContinuumBench
    simulation engine.

    At each epoch, this controller:
    1. Extracts all observable signals from ControllerState (queue depths, metadata)
    2. Computes velocity / acceleration features via 3-epoch sliding windows
    3. Constructs a TelemetricState (frozen dataclass from the candidate policy module)
    4. Calls compute_target_workers(state) from the candidate policy
    5. Emits ScaleAction(stage="CloudRefine", active_workers=k_t)
    6. Delegates placement to _PlacementReplanMixin (Eclypse substrate)

    The policy path is loaded from EVOLUTION_CANDIDATE_PATH env var, set by
    openevolve_evaluator.py per evaluation call. This decouples the controller
    from hardcoded paths (AGENTS.md Rule #2).

    Args:
        policy_path: Absolute path to the candidate policy .py file.
        placement_strategy: Eclypse placement heuristic (default: best_fit).
        replan_every_epochs: Placement audit frequency.
    """

    policy_path: str = ""

    # Internal state — NOT constructor arguments
    _compute_fn: Any = field(default=None, init=False, repr=False)
    _TelemetricState: Any = field(default=None, init=False, repr=False)
    _load_error: Optional[str] = field(default=None, init=False, repr=False)

    # Sliding window histories for velocity/acceleration computation (3-epoch windows)
    _ingress_history: Deque[float] = field(default_factory=lambda: deque(maxlen=3), init=False)
    _p_fast_history: Deque[float] = field(default_factory=lambda: deque(maxlen=3), init=False)
    _queue_history: Deque[float] = field(default_factory=lambda: deque(maxlen=3), init=False)

    # Track last scale time for time_since_last_scale_s feature
    _last_scale_epoch: int = field(default=0, init=False)
    _step_seconds: float = field(default=1.0, init=False)

    # CloudRefine stage name (constant per architecture spec)
    _CLOUD_STAGE: str = field(default="CloudRefine", init=False)

    # Worker service rate (μ) — consistent with Gate 2 calibration
    _WORKER_CAPACITY_RPS: float = field(default=16.0, init=False)

    # SLA deadline — consistent with Gate 1 contract
    _SLA_DEADLINE_S: float = field(default=15.0, init=False)

    def __post_init__(self) -> None:
        """Load the candidate policy module from the specified path."""
        super().__post_init__()
        self._load_policy()

    def _load_policy(self) -> None:
        """Dynamically import compute_target_workers and TelemetricState from the candidate file."""
        try:
            spec = importlib.util.spec_from_file_location("candidate_policy", self.policy_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {self.policy_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._compute_fn = module.compute_target_workers
            self._TelemetricState = module.TelemetricState
        except Exception as e:
            self._load_error = str(e)

    def _velocity(self, history: Deque[float]) -> float:
        """Compute finite-difference velocity from a sliding window of values."""
        if len(history) < 2:
            return 0.0
        return history[-1] - history[-2]

    def _acceleration(self, history: Deque[float]) -> float:
        """Compute second-order finite difference (acceleration) from a sliding window."""
        if len(history) < 3:
            return 0.0
        return history[-1] - 2 * history[-2] + history[-3]

    def step(self, state: ControllerState) -> ControllerAction:
        """
        Map ControllerState → TelemetricState → compute_target_workers → ScaleAction.

        Feature extraction:
            - p_fast, mean_set_size: from state.metadata (injected by edge scenario)
            - ingress_rps: from state.metadata["ingress_lambda"] or estimated
            - cloud_queue_depth, oldest_task_age_s: from state.queue_depths / oldest_age_s
            - active_workers, booting_workers: from state.worker_pools["CloudRefine"]
            - Velocity/acceleration features: computed from 3-epoch sliding windows
        """
        scale_actions: List[ScaleAction] = []

        # ── If policy failed to load, fall back to conservative fixed capacity ─
        if self._compute_fn is None or self._TelemetricState is None:
            for stage, snapshot in state.worker_pools.items():
                scale_actions.append(ScaleAction(stage=stage, active_workers=snapshot.max_workers))
            placement, _, _, scale_actions = self._maybe_replan(state, scale_actions)
            return ControllerAction(
                scale=scale_actions,
                placement=placement,
                metadata={"controller": "evolved_conformal", "load_error": self._load_error},
            )

        # ── Extract telemetry from ControllerState ─────────────────────────────
        meta = state.metadata

        # Tier 1: Edge semantic triage
        p_fast = float(max(0.0, min(1.0, meta.get("fast_path_fraction", 0.5))))
        mean_set_size = float(meta.get("mean_set_size", 1.0))

        # Tier 3: Queue state for CloudRefine stage
        snapshot = state.worker_pools.get(self._CLOUD_STAGE)
        cloud_queue_depth = int(state.queue_depths.get(self._CLOUD_STAGE, 0))
        oldest_task_age_s = float(state.oldest_age_s.get(self._CLOUD_STAGE, 0.0))

        # Tier 4: Fleet state
        active_workers = int(snapshot.active_workers) if snapshot else 1
        booting_workers = int(snapshot.starting_workers) if snapshot else 0
        time_since_last_scale_s = (state.epoch - self._last_scale_epoch) * self._step_seconds

        # Tier 2: Traffic dynamics
        ingress_rps = float(meta.get("ingress_lambda", 0.0))
        if ingress_rps <= 0.0:
            capacity_denominator = max(1, active_workers)
            ingress_rps = cloud_queue_depth * (self._WORKER_CAPACITY_RPS / float(capacity_denominator))

        # Update sliding windows for velocity/acceleration computation
        self._p_fast_history.append(p_fast)
        self._ingress_history.append(ingress_rps)
        self._queue_history.append(float(cloud_queue_depth))

        p_fast_velocity = self._velocity(self._p_fast_history)
        ingress_acceleration = self._acceleration(self._ingress_history)
        cloud_queue_velocity = self._velocity(self._queue_history)

        # offered_cloud_rps: causal multiplicative demand
        offered_cloud_rps = ingress_rps * (1.0 - p_fast)

        # ── Construct TelemetricState (frozen dataclass from candidate module) ─
        telemetric_state = self._TelemetricState(
            p_fast=p_fast,
            p_fast_velocity=p_fast_velocity,
            mean_set_size=mean_set_size,
            ingress_rps=ingress_rps,
            ingress_acceleration=ingress_acceleration,
            offered_cloud_rps=offered_cloud_rps,
            cloud_queue_depth=cloud_queue_depth,
            cloud_queue_velocity=cloud_queue_velocity,
            oldest_task_age_s=oldest_task_age_s,
            active_workers=active_workers,
            booting_workers=booting_workers,
            time_since_last_scale_s=time_since_last_scale_s,
            worker_capacity_rps=self._WORKER_CAPACITY_RPS,
            sla_deadline_s=self._SLA_DEADLINE_S,
        )

        # ── Call the candidate policy function ────────────────────────────────
        try:
            k_target = int(self._compute_fn(telemetric_state))
            if snapshot:
                k_target = max(snapshot.min_workers, min(snapshot.max_workers, k_target))
            else:
                k_target = max(1, min(18, k_target))
        except Exception:
            k_target = active_workers

        # ── Emit ScaleAction for CloudRefine stage ────────────────────────────
        if snapshot and k_target != active_workers:
            scale_actions.append(ScaleAction(stage=self._CLOUD_STAGE, active_workers=k_target))
            self._last_scale_epoch = state.epoch

        placement, replan, replan_deferred, scale_actions = self._maybe_replan(
            state, scale_actions
        )

        return ControllerAction(
            scale=scale_actions,
            placement=placement,
            metadata={
                "controller": "evolved_conformal",
                "k_target": k_target,
                "p_fast": p_fast,
                "offered_cloud_rps": offered_cloud_rps,
                "cloud_queue_depth": cloud_queue_depth,
                "oldest_task_age_s": oldest_task_age_s,
            },
        )


