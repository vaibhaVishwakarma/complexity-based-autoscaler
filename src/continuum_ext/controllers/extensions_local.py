from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
        from continuum_bench.controllers.conformal_controllers import FixedCapacityController

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
        from continuum_bench.controllers.conformal_controllers import InferLineController

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
        from continuum_bench.controllers.conformal_controllers import ComplexityBlindPredictiveController

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
        from continuum_bench.controllers.conformal_controllers import ConformalAutoscalerController

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

    return None

