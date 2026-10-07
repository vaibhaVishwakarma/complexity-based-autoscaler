"""
src/continuum_ext/realism/dynamic_batching_model.py — Dynamic GPU Inference Batching Profile
=============================================================================================
Role:
    Models non-linear execution scaling and queue formation dynamics of production GPU
    inference servers (NVIDIA Triton Inference Server / vLLM / TorchServe).
    Computes effective service capacity mu(B) and per-batch execution latency as a function
    of dynamic batch size B and batch formation timeout tau_timeout.

Empirical Grounding:
    Calibrated against Gate 2 empirical Tesla T4 GPU Triton profiling manifest
    (gate2/output-gpu-t4/triton_service_profiles.json and contracts/gate2.py).
    Execution time follows affine scaling: T_exec(b) = T_base + beta * b.
    Measured on ResNet-152 on Tesla T4:
        b=1:  15.52 ms
        b=2:  17.23 ms
        b=4:  30.91 ms
        b=8:  62.67 ms
        b=16: 105.64 ms
        b=32: 205.94 ms
    Linear fit: T_base = 0.0091s, beta = 0.0061s (R^2 > 0.998).

Governance:
    AGENTS.md Rule #2 — Decoupled linkage with Gate 2 contracts.
    AGENTS.md Rule #4 — Self-documenting architecture with inline commentary.
    AGENTS.md Rule #5 — Tool grounding (uses contracts/gate2.py schema).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("dynamic_batching_model")


@dataclass
class TritonDynamicBatchingModel:
    """
    Simulates NVIDIA Triton dynamic batching behavior on GPU workers.

    Attributes:
        base_latency_s: Constant kernel launch and CUDA context overhead (T_base).
        per_item_latency_s: Marginal compute time per batched tensor (beta).
        max_batch_size: Configured dynamic batching upper limit (max_batch_size in config.pbtxt).
        batch_timeout_s: Maximum delay before an incomplete batch is dispatched (max_queue_delay_microseconds).
        jitter_cv: Empirical coefficient of variation for GPU execution jitter (5%).
    """

    base_latency_s: float = 0.0091
    per_item_latency_s: float = 0.0061
    max_batch_size: int = 16
    batch_timeout_s: float = 0.040
    jitter_cv: float = 0.05

    @classmethod
    def from_gate2_contract(
        cls,
        manifest_path: Optional[str | Path] = None,
        max_batch_size: int = 16,
        batch_timeout_s: float = 0.040,
    ) -> TritonDynamicBatchingModel:
        """
        Dynamically instantiate model from Gate 2 authoritative profiling manifest.
        Falls back to empirically fitted Tesla T4 constants if file is absent.
        """
        default_path = Path("gate2/output-gpu-t4/triton_service_profiles.json")
        target_path = Path(manifest_path) if manifest_path else default_path

        if target_path.is_file():
            try:
                from contracts.gate2 import load_gate2_profiles
                profile = load_gate2_profiles(target_path)
                # Compute linear fit between b=1 and b=16
                p1 = profile.get_batch_profile(1)
                p16 = profile.get_batch_profile(16) if 16 in profile.batch_sizes else profile.get_batch_profile(8)
                t1 = p1.p50_ms / 1000.0
                tb = p16.p50_ms / 1000.0
                beta = (tb - t1) / (p16.batch_size - 1)
                base = max(0.005, t1 - beta * 1.0)
                logger.info(
                    f"Loaded Gate 2 Triton profile: {profile.hardware}, "
                    f"fitted T_base={base*1000:.2f}ms, beta={beta*1000:.2f}ms"
                )
                return cls(
                    base_latency_s=float(base),
                    per_item_latency_s=float(beta),
                    max_batch_size=max_batch_size,
                    batch_timeout_s=batch_timeout_s,
                    jitter_cv=float(p1.jitter_cv),
                )
            except Exception as exc:
                logger.warning(f"Could not load Gate 2 manifest ({exc}); using verified Tesla T4 defaults.")

        return cls(max_batch_size=max_batch_size, batch_timeout_s=batch_timeout_s)

    def compute_execution_time_s(self, batch_size: int) -> float:
        """
        Compute deterministic GPU forward-pass latency for batch size b.
        T_exec(b) = T_base + beta * clamp(b, 1, max_batch_size)
        """
        b = max(1, min(self.max_batch_size, int(batch_size)))
        return self.base_latency_s + self.per_item_latency_s * b

    def compute_service_rate_rps(self, batch_size: int) -> float:
        """
        Compute steady-state worker service throughput capacity mu(b) (RPS/worker).
        Includes the batch formation timeout window tau_timeout:
        mu(b) = b / (T_exec(b) + tau_timeout)
        """
        b = max(1, min(self.max_batch_size, int(batch_size)))
        cycle_time = self.compute_execution_time_s(b) + self.batch_timeout_s
        return float(b / cycle_time)

    def form_batch(self, queue_depth: int) -> tuple[int, float]:
        """
        Simulate Triton dynamic batch formation given current ingress queue depth Q.

        Returns:
            (dispatched_batch_size, estimated_wait_and_exec_latency_s)
        """
        if queue_depth <= 0:
            return 0, 0.0

        # Dispatched batch is clamped by available items and hardware max_batch_size
        batch_size = min(queue_depth, self.max_batch_size)
        exec_latency = self.compute_execution_time_s(batch_size)

        # If queue has fewer items than max_batch_size, worker waited up to batch_timeout_s
        formation_delay = self.batch_timeout_s if batch_size < self.max_batch_size else 0.0
        total_latency = formation_delay + exec_latency

        return batch_size, total_latency
