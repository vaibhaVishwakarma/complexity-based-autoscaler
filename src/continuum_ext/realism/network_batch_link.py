"""
src/continuum_ext/realism/network_batch_link.py — Calibrated WAN Batch Transmission Link
========================================================================================
Role:
    Models realistic network transit latency and bandwidth contention for batched offloading
    between Edge triage and Cloud refinement worker pools.
    Accounts for payload size, link bandwidth limits (Mbps), propagation RTT, packet loss,
    and stochastic packet jitter.

Empirical Grounding:
    Calibrated against ContinuumBench's authoritative F2 network profile
    (src/continuum_bench/calibration/network_profiles.yaml: 'edge_cloud_wan'):
        - Source tier: edge, Target tier: cloud
        - Base RTT: median 42.0 ms, P95 68.0 ms
        - Sustained bandwidth: 220.0 Mbps, Degraded: 140.0 Mbps
        - Packet loss: 0.2%
    Default image payload: 200,000 bytes (200 KB per frame).

Governance:
    AGENTS.md Rule #2 — Decoupled linkage with ContinuumBench network profile schemas.
    AGENTS.md Rule #3 — Python environment in ./.venv.
    AGENTS.md Rule #4 — Self-documenting architecture with inline commentary.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger("network_batch_link")


@dataclass
class CalibratedWanBatchLink:
    """
    Simulates edge-to-cloud WAN transmission dynamics with bandwidth contention.

    Attributes:
        base_rtt_ms: Physical round-trip propagation time in milliseconds (median 42.0 ms).
        p95_rtt_ms: 95th percentile WAN latency under standard load (68.0 ms).
        bandwidth_mbps: Sustained link throughput capacity (e.g. 150-220 Mbps).
        packet_loss_percent: Probability of packet drop requiring TCP retransmission (0.2%).
        retransmission_penalty_s: Delay penalty incurred when packet loss occurs (0.100s).
    """

    base_rtt_ms: float = 42.0
    p95_rtt_ms: float = 68.0
    bandwidth_mbps: float = 150.0
    packet_loss_percent: float = 0.2
    retransmission_penalty_s: float = 0.080

    @classmethod
    def from_continuumbench_profile(
        cls,
        profile_name: str = "edge_cloud_wan",
        profiles_yaml_path: Optional[str | Path] = None,
    ) -> CalibratedWanBatchLink:
        """
        Dynamically instantiate link from ContinuumBench's network_profiles.yaml.
        Falls back to verified profile defaults if file is absent.
        """
        default_path = Path("clones/ContinuumBench/src/continuum_bench/calibration/network_profiles.yaml")
        target_path = Path(profiles_yaml_path) if profiles_yaml_path else default_path

        if target_path.is_file():
            try:
                import yaml
                with open(target_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                profiles = data.get("profiles", {})
                if profile_name in profiles:
                    prof = profiles[profile_name]
                    lat = prof.get("latency_ms", {})
                    bw = prof.get("bandwidth_mbps", {})
                    med_rtt = float(lat.get("median", 42.0))
                    p95_rtt = float(lat.get("p95", 68.0))
                    sustained_bw = float(bw.get("sustained", 150.0))
                    loss = float(prof.get("loss_percent", 0.2))
                    logger.info(
                        f"Loaded ContinuumBench network profile '{profile_name}': "
                        f"RTT={med_rtt}ms (P95={p95_rtt}ms), BW={sustained_bw}Mbps, Loss={loss}%"
                    )
                    return cls(
                        base_rtt_ms=med_rtt,
                        p95_rtt_ms=p95_rtt,
                        bandwidth_mbps=sustained_bw,
                        packet_loss_percent=loss,
                    )
            except Exception as exc:
                logger.warning(f"Could not load network profile from {target_path} ({exc}); using defaults.")

        return cls()

    @property
    def jitter_std_ms(self) -> float:
        """Derived Gaussian jitter standard deviation matching median-to-P95 distance."""
        # For a Gaussian distribution, P95 is median + 1.645 * sigma
        delta = max(1.0, self.p95_rtt_ms - self.base_rtt_ms)
        return float(delta / 1.645)

    def compute_transmission_delay_s(
        self,
        batch_size: int = 1,
        item_bytes: int = 200_000,
        rng: Optional[np.random.Generator] = None,
    ) -> float:
        """
        Calculate total end-to-end WAN transfer latency for a batched offload payload.

        Formula:
            Payload_Megabits = (batch_size * item_bytes * 8) / 1,000,000
            T_serialization = Payload_Megabits / bandwidth_mbps
            T_propagation = max(5ms, Normal(base_rtt_ms, jitter_std_ms)) / 1000.0
            T_loss_penalty = retransmission_penalty_s if drop_event else 0.0
            T_total = T_serialization + T_propagation + T_loss_penalty
        """
        b = max(1, int(batch_size))
        payload_bits = b * item_bytes * 8.0
        serialization_time_s = payload_bits / (self.bandwidth_mbps * 1_000_000.0)

        # Stochastic jitter
        if rng is not None:
            jitter_ms = float(rng.normal(0.0, self.jitter_std_ms))
            drop_event = bool(rng.uniform(0.0, 100.0) < self.packet_loss_percent)
        else:
            jitter_ms = float(np.random.normal(0.0, self.jitter_std_ms))
            drop_event = bool(np.random.uniform(0.0, 100.0) < self.packet_loss_percent)

        propagation_time_s = max(0.005, (self.base_rtt_ms + jitter_ms) / 1000.0)
        loss_penalty_s = self.retransmission_penalty_s if drop_event else 0.0

        return serialization_time_s + propagation_time_s + loss_penalty_s
