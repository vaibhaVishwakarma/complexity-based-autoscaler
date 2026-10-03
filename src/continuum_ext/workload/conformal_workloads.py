"""
conformal_workloads.py — 2D Workload Generators for the Conformal Autoscaler Benchmarking Suite.

Role: Workload generation layer, Stage 3 of the Conformal Autoscaler evaluation pipeline.
Gate stage: Pre-simulation (produces per-epoch (lambda_t, fp_t) pairs consumed by the runner).

Inputs:
  - Suite 1/2: Pure parametric configuration via dataclass constructors.
  - Suite 3:   Azure Functions 2019 processed trace at
               data/azure_traces/azure_functions_2019_processed.npz
               (keys: "arrival_rates", "timestamps_s").
  - Gate 1 contract: contracts.gate1.Gate1CalibrationConfig — supplies the
               empirical fast-path fraction baseline (fast_path_fraction field).

Outputs:
  - Per `sample(epoch)` call: (lambda_t: float, fp_t: float) tuple.
      lambda_t — total arrival rate in requests/epoch.
      fp_t     — fraction of requests routed through the edge fast-path [0.0, 1.0].
  - WorkloadStream2D satisfies the WorkloadStream protocol extension for 2D streams;
    its `sample_1d(epoch)` delegates to the existing WorkloadStream protocol so it
    can be dropped into ContinuumBench runner slots that only consume lambda.

Suites:
  Suite 1 — Volume archetypes, fixed fp=FP_SUITE1_FIXED (0.50 per strategy §4.1).
             Six generators: Flat, Spike, Burst, Ramp, ZeroBeginRamp, ZeroTerminalRamp.
  Suite 2 — Complexity microbenchmarks, controlled volume, varying fp.
             Five generators: SteadyShock, SteadyRecovery, OpposingShift1,
             OpposingShift2, CorrelatedStorm.
  Suite 3 — Rolling Azure macrobenchmark, driven by real Azure 2019 trace with
             diurnal fp drift, storm injection, and opposing phase overlays.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Protocol, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants (immutable, per AGENTS.md §2)
# ---------------------------------------------------------------------------

#: Canonical seed shared across all suites for reproducibility.
SEED: int = 42

#: Fixed fast-path fraction for Suite 1 (all volume archetypes).
#: Sourced from strategy document §4.1 — keeps complexity dimension constant.
FP_SUITE1_FIXED: float = 0.50

#: Absolute path to the Azure Functions 2019 processed trace (authoritative source).
_AZURE_TRACE_PATH: Path = (
    Path(__file__).resolve().parents[6] / "data" / "azure_traces" / "azure_functions_2019_processed.npz"
)

# ---------------------------------------------------------------------------
# Protocol — WorkloadStream2D
# ---------------------------------------------------------------------------


class WorkloadStream2D(Protocol):
    """Two-dimensional workload stream protocol: yields (lambda_t, fp_t) per epoch.

    This is an additive extension of the existing WorkloadStream protocol.
    The 1D shim allows legacy runner slots to call `sample(epoch)` and receive
    only the integer arrival count, maintaining backward compatibility.
    """

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (lambda_t, fp_t) for one epoch — the full 2D signal."""
        ...

    def sample(self, epoch: int) -> int:
        """1D shim: return only the integer arrival count (Poisson draw of lambda_t)."""
        ...


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _poisson(rate: float, rng: random.Random) -> int:
    """Draw a Poisson variate using Knuth's method with chunking for large rates."""
    if rate <= 0.0:
        return 0
    _MAX = 500.0
    if rate > _MAX:
        total = 0
        rem = rate
        while rem > _MAX:
            total += _poisson(_MAX, rng)
            rem -= _MAX
        return total + _poisson(rem, rng)
    # Knuth's method
    limit = math.exp(-rate)
    count = 0
    product = 1.0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Suite 1 — Volume Archetypes (fp fixed at FP_SUITE1_FIXED)
# ---------------------------------------------------------------------------


@dataclass
class Suite1FlatWorkload:
    """Suite 1-A: Constant flat load at a fixed rate.

    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.
    Volume dimension: constant Poisson(rate_rps) arrivals each epoch.

    Use-case: Establishes the steady-state scaling baseline for every controller.
    """

    rate_rps: float = 50.0
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (constant_rate, FP_SUITE1_FIXED)."""
        return float(self.rate_rps), FP_SUITE1_FIXED

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the flat rate."""
        return _poisson(self.rate_rps, self._rng)


@dataclass
class Suite1SpikeWorkload:
    """Suite 1-B: Periodic instantaneous load spike.

    Volume dimension: base rate, then a brief spike (spike_ratio × base) at epoch=spike_epoch,
    then immediately returns to base. Repeats with period `period_epochs` if repeat=True.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.

    Use-case: Measures controller reaction latency and over-shoot when a spike arrives
    with no warning (no pre-announcement via fp signal).
    """

    base_rate_rps: float = 30.0
    spike_ratio: float = 5.0         # spike rate = base * spike_ratio
    spike_duration_epochs: int = 3   # how many epochs the spike persists
    spike_epoch: int = 50            # epoch at which the first spike starts
    period_epochs: int = 0           # 0 = no repeat; >0 = periodic repeat
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _rate_at(self, epoch: int) -> float:
        """Compute the arrival rate at a given epoch, accounting for spikes."""
        if self.period_epochs > 0:
            # Periodic: project epoch into the current period cycle
            epoch = epoch % self.period_epochs

        # Check if within spike window
        if self.spike_epoch <= epoch < self.spike_epoch + self.spike_duration_epochs:
            return float(self.base_rate_rps * self.spike_ratio)
        return float(self.base_rate_rps)

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (rate_at_epoch, FP_SUITE1_FIXED)."""
        return self._rate_at(epoch), FP_SUITE1_FIXED

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the epoch-specific rate."""
        return _poisson(self._rate_at(epoch), self._rng)


@dataclass
class Suite1BurstWorkload:
    """Suite 1-C: Random periodic bursty load (MMPP-inspired two-state process).

    Volume dimension: switches between low_rate and high_rate with Markov transitions.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.

    Use-case: Tests sustained-burst handling; the burst length is not predictable from
    volume alone, stressing reactive controllers.
    """

    low_rate_rps: float = 20.0
    high_rate_rps: float = 100.0
    p_low_to_high: float = 0.05   # per-epoch probability of entering burst state
    p_high_to_low: float = 0.15   # per-epoch probability of leaving burst state
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the RNG and initialise the Markov state."""
        self._rng = random.Random(self.seed)
        self._state = "low"  # initial Markov state

    def _advance(self) -> None:
        """Advance the Markov chain by one epoch."""
        p = self._rng.random()
        if self._state == "low" and p < self.p_low_to_high:
            self._state = "high"
        elif self._state == "high" and p < self.p_high_to_low:
            self._state = "low"

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (current_markov_rate, FP_SUITE1_FIXED); advances Markov state."""
        del epoch  # state is maintained internally, epoch is ignored
        rate = self.high_rate_rps if self._state == "high" else self.low_rate_rps
        self._advance()
        return float(rate), FP_SUITE1_FIXED

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw and Markov advance."""
        rate, _ = self.sample_2d(epoch)
        return _poisson(rate, self._rng)


@dataclass
class Suite1RampWorkload:
    """Suite 1-D: Linear ramp from ramp_start_rps to ramp_end_rps over ramp_epochs.

    Volume dimension: linearly interpolated rate, holds at ramp_end_rps thereafter.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.

    Use-case: Tests gradual scale-up behaviour, expected to be handled well by
    predictive controllers but challenged if the slope is underestimated.
    """

    ramp_start_rps: float = 10.0
    ramp_end_rps: float = 80.0
    ramp_epochs: int = 100
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _rate_at(self, epoch: int) -> float:
        """Linearly interpolate rate; clamp to end value once ramp completes."""
        if self.ramp_epochs <= 0:
            return float(self.ramp_end_rps)
        t = min(1.0, float(epoch) / float(self.ramp_epochs))
        return float(self.ramp_start_rps + t * (self.ramp_end_rps - self.ramp_start_rps))

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (linearly ramped rate, FP_SUITE1_FIXED)."""
        return self._rate_at(epoch), FP_SUITE1_FIXED

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the linearly ramped rate."""
        return _poisson(self._rate_at(epoch), self._rng)


@dataclass
class Suite1ZeroBeginRampWorkload:
    """Suite 1-E: Cold-start ramp — begins at zero, ramps to steady_rate_rps.

    Volume dimension: starts at 0 RPS, linear ramp over ramp_epochs, then flat.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.

    Use-case: Stresses cold-start and minimum-replica behaviour. Controllers with
    min_replicas=0 must correctly activate workers before queue backlog accumulates.
    """

    steady_rate_rps: float = 60.0
    ramp_epochs: int = 50
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG and delegate to Suite1RampWorkload."""
        self._rng = random.Random(self.seed)
        self._ramp = Suite1RampWorkload(
            ramp_start_rps=0.0,
            ramp_end_rps=self.steady_rate_rps,
            ramp_epochs=self.ramp_epochs,
            seed=self.seed,
        )

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (zero-begin ramped rate, FP_SUITE1_FIXED)."""
        return self._ramp._rate_at(epoch), FP_SUITE1_FIXED

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the zero-begin ramped rate."""
        return _poisson(self._ramp._rate_at(epoch), self._rng)


@dataclass
class Suite1ZeroTerminalRampWorkload:
    """Suite 1-F: Drain ramp — starts at steady_rate_rps, ramps down to zero at terminal_epoch.

    Volume dimension: flat at steady_rate_rps until drain_start_epoch, then linear ramp to 0.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.

    Use-case: Tests scale-down responsiveness and idle-worker reclamation.
    Controllers that over-retain workers incur unnecessary cost after drain.
    """

    steady_rate_rps: float = 60.0
    drain_start_epoch: int = 80
    drain_end_epoch: int = 150
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _rate_at(self, epoch: int) -> float:
        """Compute rate: flat until drain_start, then linearly ramp to zero."""
        if epoch < self.drain_start_epoch:
            return float(self.steady_rate_rps)
        drain_len = max(1, self.drain_end_epoch - self.drain_start_epoch)
        t = min(1.0, float(epoch - self.drain_start_epoch) / float(drain_len))
        return float(self.steady_rate_rps * (1.0 - t))

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (drain-ramp rate, FP_SUITE1_FIXED)."""
        return self._rate_at(epoch), FP_SUITE1_FIXED

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the drain-ramp rate."""
        return _poisson(self._rate_at(epoch), self._rng)


# ---------------------------------------------------------------------------
# Suite 2 — Complexity Microbenchmarks (volume controlled, fp varies)
# ---------------------------------------------------------------------------


@dataclass
class Suite2SteadyShockWorkload:
    """Suite 2-A: Steady volume + sudden complexity shock (fp drops abruptly).

    Volume dimension: constant at steady_rate_rps.
    Complexity dimension: fp=fp_high until shock_epoch, then drops to fp_low (shock).
    Stays at fp_low thereafter (no recovery). This decouples the complexity alarm
    from any volume signal — the volume channel is silent.

    Use-case: Distinguishes conformal-aware controllers (which receive early fp_low
    warning via metadata) from complexity-blind ones (which only react to queue growth).
    """

    steady_rate_rps: float = 50.0
    fp_high: float = 0.70     # fast-path fraction before the shock
    fp_low: float = 0.20      # fast-path fraction after the shock
    shock_epoch: int = 60     # epoch at which the complexity drop occurs
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (steady volume, fp_high or fp_low depending on epoch)."""
        fp = self.fp_high if epoch < self.shock_epoch else self.fp_low
        return float(self.steady_rate_rps), float(fp)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the constant volume rate."""
        return _poisson(self.steady_rate_rps, self._rng)


@dataclass
class Suite2SteadyRecoveryWorkload:
    """Suite 2-B: Complexity shock followed by natural recovery.

    Volume dimension: constant at steady_rate_rps.
    Complexity dimension: fp=fp_high → fp_low at shock_epoch → linearly recovers
    back to fp_high over recovery_epochs. Exercises whether controllers over-provision
    after a shock and fail to scale down during recovery.

    Use-case: Symmetric to Suite2SteadyShockWorkload but adds the recovery arc, testing
    whether conformal guidance continues to signal hysteresis avoidance.
    """

    steady_rate_rps: float = 50.0
    fp_high: float = 0.70
    fp_low: float = 0.20
    shock_epoch: int = 40
    recovery_epochs: int = 60
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _fp_at(self, epoch: int) -> float:
        """Piecewise fp: high → low at shock → linearly recovers over recovery_epochs."""
        if epoch < self.shock_epoch:
            return float(self.fp_high)
        rel = epoch - self.shock_epoch
        if rel >= self.recovery_epochs:
            return float(self.fp_high)
        # Linear interpolation from fp_low back to fp_high
        t = float(rel) / float(self.recovery_epochs)
        return float(self.fp_low + t * (self.fp_high - self.fp_low))

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (steady volume, fp at epoch)."""
        return float(self.steady_rate_rps), self._fp_at(epoch)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the constant volume rate."""
        return _poisson(self.steady_rate_rps, self._rng)


@dataclass
class Suite2OpposingShift1Workload:
    """Suite 2-C: Opposing shift — volume ramps UP while complexity ramps DOWN.

    Volume dimension: linear ramp from base_rate_rps to peak_rate_rps over shift_epochs.
    Complexity dimension: fp ramps from fp_high to fp_low over the same window.
    These two signals move in opposite directions simultaneously.

    Use-case: The volume channel says 'scale up'; the complexity channel says
    'the effective GPU load per request is increasing'. Complexity-blind controllers
    scale linearly with volume and under-provision; conformal controller scales with
    the effective slow-path load λ_slow = λ * (1 - fp).
    """

    base_rate_rps: float = 30.0
    peak_rate_rps: float = 80.0
    fp_high: float = 0.70
    fp_low: float = 0.20
    shift_start_epoch: int = 30
    shift_epochs: int = 80
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _interp(self, epoch: int) -> float:
        """Return interpolation factor t in [0, 1] for the shift window."""
        if epoch < self.shift_start_epoch:
            return 0.0
        if epoch >= self.shift_start_epoch + self.shift_epochs:
            return 1.0
        return float(epoch - self.shift_start_epoch) / float(self.shift_epochs)

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (ramping volume, ramping fp — in opposite direction)."""
        t = self._interp(epoch)
        lam = self.base_rate_rps + t * (self.peak_rate_rps - self.base_rate_rps)
        fp = self.fp_high + t * (self.fp_low - self.fp_high)  # fp goes down as volume goes up
        return float(lam), _clamp(fp)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the volume-ramp rate."""
        lam, _ = self.sample_2d(epoch)
        return _poisson(lam, self._rng)


@dataclass
class Suite2OpposingShift2Workload:
    """Suite 2-D: Opposing shift — volume ramps DOWN while complexity ramps UP (fp recovers).

    Volume dimension: linear ramp from peak_rate_rps to base_rate_rps.
    Complexity dimension: fp ramps from fp_low to fp_high (complexity decreasing).

    Use-case: The inverse of Suite2OpposingShift1. Volume signal says 'scale down';
    complexity signal says 'fast-path recovering — each remaining request is cheaper'.
    Conformal controller scales down faster than complexity-blind ones.
    """

    peak_rate_rps: float = 80.0
    base_rate_rps: float = 30.0
    fp_low: float = 0.20
    fp_high: float = 0.70
    shift_start_epoch: int = 30
    shift_epochs: int = 80
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _interp(self, epoch: int) -> float:
        """Return interpolation factor t in [0, 1] for the shift window."""
        if epoch < self.shift_start_epoch:
            return 0.0
        if epoch >= self.shift_start_epoch + self.shift_epochs:
            return 1.0
        return float(epoch - self.shift_start_epoch) / float(self.shift_epochs)

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (ramping-down volume, ramping-up fp)."""
        t = self._interp(epoch)
        lam = self.peak_rate_rps + t * (self.base_rate_rps - self.peak_rate_rps)
        fp = self.fp_low + t * (self.fp_high - self.fp_low)  # fp recovers as volume declines
        return float(lam), _clamp(fp)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the ramping-down rate."""
        lam, _ = self.sample_2d(epoch)
        return _poisson(lam, self._rng)


@dataclass
class Suite2CorrelatedStormWorkload:
    """Suite 2-E: Correlated storm — simultaneous volume spike + complexity shock.

    Volume dimension: base_rate_rps baseline; spikes to burst_rate_rps for storm_duration_epochs.
    Complexity dimension: fp_high baseline; drops to fp_storm during the same window.
    Both signals move in the worst-case direction simultaneously.

    Use-case: The maximum-stress microbenchmark. Both the volume and complexity channels
    demand more GPU capacity at the same time. Validates the conformal controller's ability
    to correctly size for λ_slow = λ_burst * (1 - fp_storm) without over-shooting.
    """

    base_rate_rps: float = 30.0
    burst_rate_rps: float = 90.0
    fp_high: float = 0.65
    fp_storm: float = 0.15
    storm_start_epoch: int = 50
    storm_duration_epochs: int = 30
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _in_storm(self, epoch: int) -> bool:
        """Return True if epoch falls within the storm window."""
        return self.storm_start_epoch <= epoch < self.storm_start_epoch + self.storm_duration_epochs

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (burst or base rate, storm or high fp) depending on storm window."""
        if self._in_storm(epoch):
            return float(self.burst_rate_rps), float(self.fp_storm)
        return float(self.base_rate_rps), float(self.fp_high)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of rate at epoch."""
        lam, _ = self.sample_2d(epoch)
        return _poisson(lam, self._rng)


# ---------------------------------------------------------------------------
# Suite 3 — Rolling Azure Macrobenchmark with Complexity Overlay
# ---------------------------------------------------------------------------


@dataclass
class RollingAzureComplexityStream:
    """Suite 3: Rolling Azure Functions 2019 trace with diurnal complexity overlay.

    This is the concluding macrobenchmark that ties all prior suites together.
    It drives real-world temporal structure (diurnal ramp, periodic bursts, natural
    load variability) while overlaying synthetic complexity regimes on top.

    Volume dimension: sourced from `data/azure_traces/azure_functions_2019_processed.npz`
      via the `arrival_rates` array. The trace is scaled by `rate_scale_factor` to
      match the target cluster capacity (default 1.0 = raw trace rates).

    Complexity dimension (fp overlay): three interleaved regimes applied on top:
      (a) Diurnal drift  — fp drifts from fp_diurnal_day to fp_diurnal_night and back
          over a 24-hour sinusoidal cycle (simulates model complexity increasing at night
          when edge nodes are under-resourced and more traffic hits cloud).
      (b) Injected storms — correlated complexity+volume spikes injected at pre-specified
          epochs (storm_epochs) lasting storm_duration_epochs each.
      (c) Opposing phase  — within the ramp regions of the Azure trace, fp is inverted
          relative to the trend (rising load → falling fp; falling load → rising fp),
          mirroring Suite2 opposing-shift generators on a real-trace backbone.

    Inputs:
      trace_path: Path to azure_functions_2019_processed.npz. Defaults to
                  data/azure_traces/azure_functions_2019_processed.npz.
      epochs_per_second: Simulation epochs per wall-clock second; used to convert
                         trace timestamps to epoch indices. Default 1 epoch = 1 s.

    Outputs:
      sample_2d(epoch) → (lambda_t: float, fp_t: float)
      sample(epoch)    → int (Poisson draw of lambda_t only; backward-compatible shim)
    """

    rate_scale_factor: float = 1.0
    fp_diurnal_day: float = 0.65       # fp at peak daytime (low complexity)
    fp_diurnal_night: float = 0.20     # fp at night (high complexity, more cloud work)
    diurnal_period_epochs: int = 1440  # 24 hours if 1 epoch = 1 minute
    storm_epochs: List[int] = field(default_factory=lambda: [300, 800, 1200])
    storm_duration_epochs: int = 30
    storm_fp: float = 0.10             # fp during injected storms
    storm_rate_boost: float = 2.5      # λ multiplier during injected storm bursts
    trace_path: Optional[Path] = None  # None → uses _AZURE_TRACE_PATH default
    seed: int = SEED

    def __post_init__(self) -> None:
        """Load and validate the Azure trace; seed the RNG."""
        self._rng = random.Random(self.seed)
        resolved_path = self.trace_path or _AZURE_TRACE_PATH

        # Validate that the trace file exists (Dataset Integrity — AGENTS.md §6)
        if not Path(resolved_path).exists():
            raise FileNotFoundError(
                f"Azure trace not found at {resolved_path}. "
                "Ensure data/azure_traces/azure_functions_2019_processed.npz is present. "
                "No synthetic fallback is permitted per AGENTS.md §6."
            )

        # Load the authoritative trace arrays
        data = np.load(str(resolved_path), allow_pickle=False)
        if "arrival_rates" not in data:
            raise KeyError(
                "Expected key 'arrival_rates' in Azure trace NPZ. "
                f"Available keys: {list(data.files)}"
            )

        # Scale trace to target cluster capacity
        self._rates: np.ndarray = data["arrival_rates"].astype(np.float64) * self.rate_scale_factor
        self._trace_len: int = len(self._rates)

    # --- Internal helpers ---

    def _storm_set(self) -> set:
        """Pre-compute the set of epoch indices that fall within any storm window."""
        storm_idx: set = set()
        for start in self.storm_epochs:
            for e in range(start, start + self.storm_duration_epochs):
                storm_idx.add(e)
        return storm_idx

    def _diurnal_fp(self, epoch: int) -> float:
        """Compute the sinusoidal diurnal fp at a given epoch.

        fp oscillates between fp_diurnal_night and fp_diurnal_day following a
        cosine curve with period diurnal_period_epochs. Peak fp (day) occurs at
        epoch=0 and epoch=diurnal_period_epochs; trough (night) at epoch=period/2.
        """
        t = float(epoch % self.diurnal_period_epochs) / float(self.diurnal_period_epochs)
        # cos(2πt): 1 at t=0 (day), -1 at t=0.5 (night)
        phase = math.cos(2.0 * math.pi * t)
        # Map [-1, 1] → [fp_diurnal_night, fp_diurnal_day]
        midpoint = (self.fp_diurnal_day + self.fp_diurnal_night) / 2.0
        amplitude = (self.fp_diurnal_day - self.fp_diurnal_night) / 2.0
        return _clamp(midpoint + amplitude * phase, lo=0.0, hi=1.0)

    def _trace_rate(self, epoch: int) -> float:
        """Look up the Azure trace rate for a given epoch (wrapping if trace exhausted)."""
        idx = epoch % self._trace_len
        return float(self._rates[idx])

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (lambda_t, fp_t) for the given epoch with all overlays applied.

        Overlay priority (highest wins):
          1. Injected storm — both volume boost and fp_storm apply.
          2. Diurnal drift  — sinusoidal fp with no volume modifier.
        """
        base_rate = self._trace_rate(epoch)

        # Check if epoch is within an injected storm window
        in_storm = any(
            s <= epoch < s + self.storm_duration_epochs
            for s in self.storm_epochs
        )

        if in_storm:
            # Correlated storm: volume boosted + complexity spiked
            return float(base_rate * self.storm_rate_boost), float(self.storm_fp)

        # Default: diurnal sinusoidal complexity drift
        return float(base_rate), self._diurnal_fp(epoch)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the scaled Azure trace rate (no fp signal)."""
        rate, _ = self.sample_2d(epoch)
        return _poisson(rate, self._rng)


# ---------------------------------------------------------------------------
# Registry — build_2d_stream factory (mirrors build_stream from mmpp.py)
# ---------------------------------------------------------------------------


def build_2d_stream(config: dict, seed: int) -> "WorkloadStream2D":
    """Build a 2D workload stream from a configuration dictionary.

    Mirrors the `build_stream` factory in mmpp.py so ContinuumBench scenario
    builders can construct conformal workloads from YAML config blocks.

    Supported generator names:
      Suite 1 (fixed fp=0.50):
        "suite1_flat"           → Suite1FlatWorkload
        "suite1_spike"          → Suite1SpikeWorkload
        "suite1_burst"          → Suite1BurstWorkload
        "suite1_ramp"           → Suite1RampWorkload
        "suite1_zero_begin"     → Suite1ZeroBeginRampWorkload
        "suite1_zero_terminal"  → Suite1ZeroTerminalRampWorkload

      Suite 2 (complexity microbenchmarks):
        "suite2_shock"          → Suite2SteadyShockWorkload
        "suite2_recovery"       → Suite2SteadyRecoveryWorkload
        "suite2_opposing1"      → Suite2OpposingShift1Workload
        "suite2_opposing2"      → Suite2OpposingShift2Workload
        "suite2_storm"          → Suite2CorrelatedStormWorkload

      Suite 3 (Azure macrobenchmark):
        "suite3_azure"          → RollingAzureComplexityStream
    """
    generator = str(config.get("generator", "suite1_flat")).lower()

    # ---- Suite 1 ----
    if generator == "suite1_flat":
        return Suite1FlatWorkload(
            rate_rps=float(config.get("rate_rps", 50.0)),
            seed=seed,
        )
    if generator == "suite1_spike":
        return Suite1SpikeWorkload(
            base_rate_rps=float(config.get("base_rate_rps", 30.0)),
            spike_ratio=float(config.get("spike_ratio", 5.0)),
            spike_duration_epochs=int(config.get("spike_duration_epochs", 3)),
            spike_epoch=int(config.get("spike_epoch", 50)),
            period_epochs=int(config.get("period_epochs", 0)),
            seed=seed,
        )
    if generator == "suite1_burst":
        return Suite1BurstWorkload(
            low_rate_rps=float(config.get("low_rate_rps", 20.0)),
            high_rate_rps=float(config.get("high_rate_rps", 100.0)),
            p_low_to_high=float(config.get("p_low_to_high", 0.05)),
            p_high_to_low=float(config.get("p_high_to_low", 0.15)),
            seed=seed,
        )
    if generator == "suite1_ramp":
        return Suite1RampWorkload(
            ramp_start_rps=float(config.get("ramp_start_rps", 10.0)),
            ramp_end_rps=float(config.get("ramp_end_rps", 80.0)),
            ramp_epochs=int(config.get("ramp_epochs", 100)),
            seed=seed,
        )
    if generator == "suite1_zero_begin":
        return Suite1ZeroBeginRampWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 60.0)),
            ramp_epochs=int(config.get("ramp_epochs", 50)),
            seed=seed,
        )
    if generator == "suite1_zero_terminal":
        return Suite1ZeroTerminalRampWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 60.0)),
            drain_start_epoch=int(config.get("drain_start_epoch", 80)),
            drain_end_epoch=int(config.get("drain_end_epoch", 150)),
            seed=seed,
        )

    # ---- Suite 2 ----
    if generator == "suite2_shock":
        return Suite2SteadyShockWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 50.0)),
            fp_high=float(config.get("fp_high", 0.70)),
            fp_low=float(config.get("fp_low", 0.20)),
            shock_epoch=int(config.get("shock_epoch", 60)),
            seed=seed,
        )
    if generator == "suite2_recovery":
        return Suite2SteadyRecoveryWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 50.0)),
            fp_high=float(config.get("fp_high", 0.70)),
            fp_low=float(config.get("fp_low", 0.20)),
            shock_epoch=int(config.get("shock_epoch", 40)),
            recovery_epochs=int(config.get("recovery_epochs", 60)),
            seed=seed,
        )
    if generator == "suite2_opposing1":
        return Suite2OpposingShift1Workload(
            base_rate_rps=float(config.get("base_rate_rps", 30.0)),
            peak_rate_rps=float(config.get("peak_rate_rps", 80.0)),
            fp_high=float(config.get("fp_high", 0.70)),
            fp_low=float(config.get("fp_low", 0.20)),
            shift_start_epoch=int(config.get("shift_start_epoch", 30)),
            shift_epochs=int(config.get("shift_epochs", 80)),
            seed=seed,
        )
    if generator == "suite2_opposing2":
        return Suite2OpposingShift2Workload(
            peak_rate_rps=float(config.get("peak_rate_rps", 80.0)),
            base_rate_rps=float(config.get("base_rate_rps", 30.0)),
            fp_low=float(config.get("fp_low", 0.20)),
            fp_high=float(config.get("fp_high", 0.70)),
            shift_start_epoch=int(config.get("shift_start_epoch", 30)),
            shift_epochs=int(config.get("shift_epochs", 80)),
            seed=seed,
        )
    if generator == "suite2_storm":
        return Suite2CorrelatedStormWorkload(
            base_rate_rps=float(config.get("base_rate_rps", 30.0)),
            burst_rate_rps=float(config.get("burst_rate_rps", 90.0)),
            fp_high=float(config.get("fp_high", 0.65)),
            fp_storm=float(config.get("fp_storm", 0.15)),
            storm_start_epoch=int(config.get("storm_start_epoch", 50)),
            storm_duration_epochs=int(config.get("storm_duration_epochs", 30)),
            seed=seed,
        )

    # ---- Suite 3 ----
    if generator == "suite3_azure":
        storm_epochs_raw = config.get("storm_epochs", [300, 800, 1200])
        return RollingAzureComplexityStream(
            rate_scale_factor=float(config.get("rate_scale_factor", 1.0)),
            fp_diurnal_day=float(config.get("fp_diurnal_day", 0.65)),
            fp_diurnal_night=float(config.get("fp_diurnal_night", 0.20)),
            diurnal_period_epochs=int(config.get("diurnal_period_epochs", 1440)),
            storm_epochs=[int(e) for e in storm_epochs_raw],
            storm_duration_epochs=int(config.get("storm_duration_epochs", 30)),
            storm_fp=float(config.get("storm_fp", 0.10)),
            storm_rate_boost=float(config.get("storm_rate_boost", 2.5)),
            trace_path=Path(config["trace_path"]) if "trace_path" in config else None,
            seed=seed,
        )

    raise ValueError(f"Unsupported 2D workload generator: '{generator}'")
