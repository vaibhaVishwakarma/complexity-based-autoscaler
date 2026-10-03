"""
conformal_workloads.py — 2D Workload Generators for the Conformal Autoscaler Benchmarking Suite.

Role: Workload generation layer, Stage 3 of the Conformal Autoscaler evaluation pipeline.
Gate stage: Pre-simulation (produces per-epoch (lambda_t, fp_t) pairs consumed by the runner).

Inputs:
  - Suite 1/2: Pure parametric configuration via dataclass constructors (doubled capacity scale).
  - Suite 3:   Azure Functions 2019 processed trace at
               data/azure_traces/azure_functions_2019_processed.npz
               (keys: "arrival_rates", "timestamps_s") scaled by rate_scale_factor=2.0.
  - Gate 1 contract: contracts.gate1.Gate1CalibrationConfig — supplies the
               empirical fast-path fraction baseline (fast_path_fraction field).

Outputs:
  - Per `sample_2d(epoch)` call: (lambda_t: float, fp_t: float) tuple.
      lambda_t — total arrival rate in requests/epoch (doubled capacity tier).
      fp_t     — fraction of requests routed through the edge fast-path [0.0, 1.0].
  - WorkloadStream2D satisfies the WorkloadStream protocol extension for 2D streams;
    its `sample(epoch)` delegates to the existing WorkloadStream protocol so it
    can be dropped into ContinuumBench runner slots that only consume lambda.

Suites (Doubled Production Capacity Tier):
  Suite 1 — Volume archetypes, fixed fp=FP_SUITE1_FIXED (0.50 per strategy §4.1).
             Six generators: Flat (100 RPS), Spike (60->300 RPS), Burst (40-200 RPS),
             Ramp (20->160 RPS), ZeroBeginRamp (0->120 RPS, cold start),
             ZeroTerminalRamp (120->0 RPS, scale-to-zero).
  Suite 2 — Complexity microbenchmarks, controlled volume, varying fp.
             Five generators: SteadyShock (100 RPS), SteadyRecovery (100 RPS),
             OpposingShift1 (60->160 RPS, fp: 0.70->0.20),
             OpposingShift2 (160->60 RPS, fp: 0.20->0.70),
             CorrelatedStorm (60->180 RPS, fp: 0.65->0.15).
  Suite 3 — Rolling Azure macrobenchmark, driven by real Azure 2019 trace with
             rate_scale_factor=2.0, diurnal fp drift, and injected OOD storms.

Regime Initialization Metadata:
  Each workload specifies its recommended initial_workers and min_workers
  so simulations match the physical regime requirements (e.g. Zero-Begin starts
  with 0 instances, Zero-Terminal scales to 0).
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants (immutable, per AGENTS.md §2)
# ---------------------------------------------------------------------------

#: Canonical seed shared across all suites for reproducibility.
SEED: int = 42

#: Authoritative SHA256 checksum for the Azure Functions 2019 trace (AGENTS.md §6).
AZURE_TRACE_SHA256: str = "9aeabacb08f01b34f46efc252db76248a55094cdae1f0e86c8eda39fa09b7447"

#: Fixed fast-path fraction for Suite 1 (all volume archetypes).
#: Sourced from strategy document §4.1 — keeps complexity dimension constant.
FP_SUITE1_FIXED: float = 0.50

def _find_azure_trace_path() -> Path:
    """Resolve the authoritative Azure trace path from workspace root."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "data" / "azure_traces" / "azure_functions_2019_processed.npz"
        if candidate.exists():
            return candidate
    return Path("/home/vaibo/edgecompute/data/azure_traces/azure_functions_2019_processed.npz")


#: Absolute path to the Azure Functions 2019 processed trace (authoritative source).
_AZURE_TRACE_PATH: Path = _find_azure_trace_path()

# ---------------------------------------------------------------------------
# Regime Initialization Profiles (Aligned with Experiment Requirements)
# ---------------------------------------------------------------------------

REGIME_INITIALIZATION_PROFILES: Dict[str, Dict[str, Any]] = {
    "suite1_flat": {
        "initial_workers": 4,
        "min_workers": 1,
        "description": "Steady-state baseline, warm start at equilibrium (100 RPS)",
    },
    "suite1_spike": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "Sized for base rate (60 RPS), tests rapid scale-out on 5x spike (300 RPS)",
    },
    "suite1_burst": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "Sized for low state (40 RPS), tests burst queue handling up to 200 RPS",
    },
    "suite1_ramp": {
        "initial_workers": 1,
        "min_workers": 1,
        "description": "Begins at ramp onset (20 RPS), tests continuous linear scale tracking to 160 RPS",
    },
    "suite1_zero_begin": {
        "initial_workers": 0,
        "min_workers": 0,
        "description": "Cold start from zero load (0 RPS) and zero instances, tests container boot delay",
    },
    "suite1_zero_terminal": {
        "initial_workers": 4,
        "min_workers": 0,
        "description": "Warm start (120 RPS), ramps to zero, tests idle reclamation and scale-to-zero",
    },
    "suite2_shock": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "Steady volume (100 RPS), tests proactive preemption on sudden OOD drop (fp: 0.70->0.20)",
    },
    "suite2_recovery": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "Steady volume (100 RPS), tests hysteresis avoidance during natural fp recovery",
    },
    "suite2_compound_stress": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "Volume surges (60->160 RPS) while fp plunges (0.70->0.20), compounding cloud stress (18->128 RPS)",
    },
    "suite2_compound_relief": {
        "initial_workers": 4,
        "min_workers": 1,
        "description": "Volume drops (160->60 RPS) while fp recovers (0.20->0.70), compounding cloud relief (128->18 RPS)",
    },
    "suite2_decoupled_opposing": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "True opposing test: Ingress surges 3x (50->150 RPS) while fp rises (0.40->0.80), holding cloud demand constant at 30 RPS",
    },
    "suite2_opposing1": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "Legacy alias for suite2_compound_stress",
    },
    "suite2_opposing2": {
        "initial_workers": 4,
        "min_workers": 1,
        "description": "Legacy alias for suite2_compound_relief",
    },
    "suite2_storm": {
        "initial_workers": 2,
        "min_workers": 1,
        "description": "Coupled storm surge (60->180 RPS + fp: 0.65->0.15), worst-case multiplicative stress",
    },
    "suite3_azure": {
        "initial_workers": 2,
        "min_workers": 0,
        "description": "2x scaled Azure 2019 trace with diurnal solar drift and injected OOD storm bursts",
    },
}


def get_regime_initialization(generator_name: str) -> Dict[str, Any]:
    """Return recommended {'initial_workers': int, 'min_workers': int} for the specified regime."""
    gen = str(generator_name).lower()
    return dict(REGIME_INITIALIZATION_PROFILES.get(
        gen,
        {"initial_workers": 2, "min_workers": 1, "description": "Default multi-node configuration"}
    ))


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
# Suite 1 — Volume Archetypes (fp fixed at FP_SUITE1_FIXED, Doubled Rates)
# ---------------------------------------------------------------------------


@dataclass
class Suite1FlatWorkload:
    """Suite 1-A: Constant flat load at a fixed rate (doubled to 100 RPS).

    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.
    Volume dimension: constant Poisson(rate_rps) arrivals each epoch.
    Recommended Init: initial_workers=4, min_workers=1 (warm start at equilibrium).
    """

    rate_rps: float = 100.0
    recommended_initial_workers: int = 4
    recommended_min_workers: int = 1
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
    """Suite 1-B: Periodic instantaneous load spike (base 60 RPS, 5x spike to 300 RPS).

    Volume dimension: base rate, then a brief spike (spike_ratio × base) at epoch=spike_epoch,
    then immediately returns to base. Repeats with period `period_epochs` if repeat=True.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.
    Recommended Init: initial_workers=2, min_workers=1 (sized for base rate).
    """

    base_rate_rps: float = 60.0
    spike_ratio: float = 5.0         # spike rate = 60 * 5 = 300 RPS
    spike_duration_epochs: int = 3   # how many epochs the spike persists
    spike_epoch: int = 50            # epoch at which the first spike starts
    period_epochs: int = 0           # 0 = no repeat; >0 = periodic repeat
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 1
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _rate_at(self, epoch: int) -> float:
        """Compute the arrival rate at a given epoch, accounting for spikes."""
        if self.period_epochs > 0:
            epoch = epoch % self.period_epochs

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
    """Suite 1-C: Random periodic bursty load (low 40 RPS, high 200 RPS).

    Volume dimension: switches between low_rate and high_rate with Markov transitions.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.
    Recommended Init: initial_workers=2, min_workers=1 (sized for low state).
    """

    low_rate_rps: float = 40.0
    high_rate_rps: float = 200.0
    p_low_to_high: float = 0.05   # per-epoch probability of entering burst state
    p_high_to_low: float = 0.15   # per-epoch probability of leaving burst state
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 1
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the RNG and initialise the Markov state."""
        self._rng = random.Random(self.seed)
        self._state = "low"

    def _advance(self) -> None:
        """Advance the Markov chain by one epoch."""
        p = self._rng.random()
        if self._state == "low" and p < self.p_low_to_high:
            self._state = "high"
        elif self._state == "high" and p < self.p_high_to_low:
            self._state = "low"

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (current_markov_rate, FP_SUITE1_FIXED); advances Markov state."""
        del epoch
        rate = self.high_rate_rps if self._state == "high" else self.low_rate_rps
        self._advance()
        return float(rate), FP_SUITE1_FIXED

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw and Markov advance."""
        rate, _ = self.sample_2d(epoch)
        return _poisson(rate, self._rng)


@dataclass
class Suite1RampWorkload:
    """Suite 1-D: Linear ramp from 20 to 160 RPS over ramp_epochs.

    Volume dimension: linearly interpolated rate, holds at ramp_end_rps thereafter.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.
    Recommended Init: initial_workers=1, min_workers=1 (tracks ramp onset).
    """

    ramp_start_rps: float = 20.0
    ramp_end_rps: float = 160.0
    ramp_epochs: int = 100
    recommended_initial_workers: int = 1
    recommended_min_workers: int = 1
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
    """Suite 1-E: Cold-start ramp — begins at zero, ramps to 120 RPS.

    Volume dimension: starts at 0 RPS, linear ramp over ramp_epochs, then flat.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.
    Recommended Init: initial_workers=0, min_workers=0 (STRICT COLD START).
    """

    steady_rate_rps: float = 120.0
    ramp_epochs: int = 50
    recommended_initial_workers: int = 0
    recommended_min_workers: int = 0
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
    """Suite 1-F: Drain ramp — starts at 120 RPS, ramps down to zero (Scale-to-Zero).

    Volume dimension: flat at 120 RPS until drain_start_epoch, then linear ramp to 0.
    Complexity dimension: fixed fp=FP_SUITE1_FIXED throughout.
    Recommended Init: initial_workers=4, min_workers=0 (TESTS SCALE-TO-ZERO).
    """

    steady_rate_rps: float = 120.0
    drain_start_epoch: int = 80
    drain_end_epoch: int = 150
    recommended_initial_workers: int = 4
    recommended_min_workers: int = 0
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
# Suite 2 — Complexity Microbenchmarks (Doubled Rates, Varying fp)
# ---------------------------------------------------------------------------


@dataclass
class Suite2SteadyShockWorkload:
    """Suite 2-A: Steady volume (100 RPS) + sudden complexity shock (fp: 0.70->0.20).

    Volume dimension: constant at steady_rate_rps = 100.0.
    Complexity dimension: fp=fp_high until shock_epoch, then drops to fp_low.
    Recommended Init: initial_workers=2, min_workers=1.
    """

    steady_rate_rps: float = 100.0
    fp_high: float = 0.70     # fast-path fraction before the shock
    fp_low: float = 0.20      # fast-path fraction after the shock
    shock_epoch: int = 60     # epoch at which the complexity drop occurs
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 1
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
    """Suite 2-B: Complexity shock (100 RPS) followed by natural recovery (fp: 0.20->0.70).

    Volume dimension: constant at steady_rate_rps = 100.0.
    Complexity dimension: fp drops to 0.20 at shock_epoch, recovers to 0.70 over recovery_epochs.
    Recommended Init: initial_workers=2, min_workers=1.
    """

    steady_rate_rps: float = 100.0
    fp_high: float = 0.70
    fp_low: float = 0.20
    shock_epoch: int = 40
    recovery_epochs: int = 60
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 1
    seed: int = SEED

    def __post_init__(self) -> None:
        """Seed the internal RNG."""
        self._rng = random.Random(self.seed)

    def _fp_at(self, epoch: int) -> float:
        """Piecewise fp: high -> low at shock -> linearly recovers over recovery_epochs."""
        if epoch < self.shock_epoch:
            return float(self.fp_high)
        rel = epoch - self.shock_epoch
        if rel >= self.recovery_epochs:
            return float(self.fp_high)
        t = float(rel) / float(self.recovery_epochs)
        return float(self.fp_low + t * (self.fp_high - self.fp_low))

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (steady volume, fp at epoch)."""
        return float(self.steady_rate_rps), self._fp_at(epoch)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the constant volume rate."""
        return _poisson(self.steady_rate_rps, self._rng)


@dataclass
class Suite2CompoundStressWorkload:
    """Suite 2-C: Compounding stress — Volume UP (60->160 RPS) while fp DOWN (0.70->0.20).

    Volume dimension: linear ramp from 60 to 160 RPS over shift_epochs.
    Complexity dimension: fp ramps from 0.70 to 0.20 over the same window.
    Cloud demand compounds upward: 18 RPS -> 128 RPS (7.1x surge).
    Recommended Init: initial_workers=2, min_workers=1.
    """

    base_rate_rps: float = 60.0
    peak_rate_rps: float = 160.0
    fp_high: float = 0.70
    fp_low: float = 0.20
    shift_start_epoch: int = 30
    shift_epochs: int = 80
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 1
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
        """Return (ramping volume, ramping fp — compounding cloud stress)."""
        t = self._interp(epoch)
        lam = self.base_rate_rps + t * (self.peak_rate_rps - self.base_rate_rps)
        fp = self.fp_high + t * (self.fp_low - self.fp_high)
        return float(lam), _clamp(fp)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the volume-ramp rate."""
        lam, _ = self.sample_2d(epoch)
        return _poisson(lam, self._rng)


#: Backward compatibility alias
Suite2OpposingShift1Workload = Suite2CompoundStressWorkload


@dataclass
class Suite2CompoundReliefWorkload:
    """Suite 2-D: Compounding relief — Volume DOWN (160->60 RPS) while fp UP (0.20->0.70).

    Volume dimension: linear ramp from 160 to 60 RPS.
    Complexity dimension: fp ramps from 0.20 to 0.70.
    Cloud demand compounds downward: 128 RPS -> 18 RPS (86% drop).
    Recommended Init: initial_workers=4, min_workers=1.
    """

    peak_rate_rps: float = 160.0
    base_rate_rps: float = 60.0
    fp_low: float = 0.20
    fp_high: float = 0.70
    shift_start_epoch: int = 30
    shift_epochs: int = 80
    recommended_initial_workers: int = 4
    recommended_min_workers: int = 1
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
        """Return (ramping-down volume, ramping-up fp — compounding cloud relief)."""
        t = self._interp(epoch)
        lam = self.peak_rate_rps + t * (self.base_rate_rps - self.peak_rate_rps)
        fp = self.fp_low + t * (self.fp_high - self.fp_low)
        return float(lam), _clamp(fp)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the ramping-down rate."""
        lam, _ = self.sample_2d(epoch)
        return _poisson(lam, self._rng)


#: Backward compatibility alias
Suite2OpposingShift2Workload = Suite2CompoundReliefWorkload


@dataclass
class Suite2DecoupledOpposingWorkload:
    """Suite 2-F: Decoupled Opposing — Volume UP (50->150 RPS) while fp UP (0.40->0.80).

    Ingress volume surges 3x, but fast-path ratio rises simultaneously such that
    cloud slow-path demand remains constant at exactly 30 RPS:
        lambda_cloud(0) = 50 * (1 - 0.40) = 30.0 RPS
        lambda_cloud(T) = 150 * (1 - 0.80) = 30.0 RPS
    Directly tests whether volume-only autoscalers over-provision while the
    conformal autoscaler holds allocation steady.
    Recommended Init: initial_workers=2, min_workers=1.
    """

    start_rate_rps: float = 50.0
    end_rate_rps: float = 150.0
    fp_start: float = 0.40
    fp_end: float = 0.80
    shift_start_epoch: int = 20
    shift_epochs: int = 80
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 1
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
        """Return (ramping volume, ramping fp — maintaining constant 30 RPS cloud demand)."""
        t = self._interp(epoch)
        lam = self.start_rate_rps + t * (self.end_rate_rps - self.start_rate_rps)
        fp = self.fp_start + t * (self.fp_end - self.fp_start)
        return float(lam), _clamp(fp)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the ramping rate."""
        lam, _ = self.sample_2d(epoch)
        return _poisson(lam, self._rng)


@dataclass
class Suite2CorrelatedStormWorkload:
    """Suite 2-E: Correlated storm — Coupled volume surge (60->180 RPS) + complexity shock (fp: 0.65->0.15).

    Volume dimension: base 60 RPS, spikes to 180 RPS during storm window.
    Complexity dimension: fp 0.65 baseline, drops to 0.15 during storm.
    Recommended Init: initial_workers=2, min_workers=1.
    """

    base_rate_rps: float = 60.0
    burst_rate_rps: float = 180.0
    fp_high: float = 0.65
    fp_storm: float = 0.15
    storm_start_epoch: int = 50
    storm_duration_epochs: int = 30
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 1
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
# Suite 3 — Rolling Azure Macrobenchmark (Scaled x2.0, Diurnal fp Drift)
# ---------------------------------------------------------------------------


@dataclass
class RollingAzureComplexityStream:
    """Suite 3: Rolling Azure Functions 2019 trace with 2.0x scale multiplier & diurnal overlay.

    Volume dimension: sourced from `data/azure_traces/azure_functions_2019_processed.npz`
      scaled by rate_scale_factor = 2.0 (doubled cluster load, preserving 100% trace realism).
    Complexity dimension: diurnal sinusoidal drift (0.65 day -> 0.20 night) + storm bursts.
    Recommended Init: initial_workers=2, min_workers=0.
    """

    rate_scale_factor: float = 2.0     # 2.0x scale factor on Azure trace
    fp_diurnal_day: float = 0.65       # fp at peak daytime (low complexity)
    fp_diurnal_night: float = 0.20     # fp at night (high complexity, more cloud work)
    diurnal_period_epochs: int = 1440  # 24 hours if 1 epoch = 1 minute
    storm_epochs: List[int] = field(default_factory=lambda: [300, 800, 1200])
    storm_duration_epochs: int = 30
    storm_fp: float = 0.10             # fp during injected storms
    storm_rate_boost: float = 2.5      # λ multiplier during injected storm bursts
    recommended_initial_workers: int = 2
    recommended_min_workers: int = 0
    trace_path: Optional[Path] = None
    seed: int = SEED

    def __post_init__(self) -> None:
        """Load and validate the Azure trace; seed the RNG."""
        self._rng = random.Random(self.seed)
        resolved_path = self.trace_path or _AZURE_TRACE_PATH

        # Validate that the trace file exists (Dataset Integrity — AGENTS.md §6)
        p = Path(resolved_path)
        if not p.exists():
            raise FileNotFoundError(
                f"Azure trace not found at {resolved_path}. "
                "Ensure data/azure_traces/azure_functions_2019_processed.npz is present. "
                "No synthetic fallback is permitted per AGENTS.md §6."
            )

        # Verify dataset integrity via authoritative SHA256 (AGENTS.md §6)
        with open(p, "rb") as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest()
        if actual_sha != AZURE_TRACE_SHA256:
            raise ValueError(
                f"Azure trace checksum mismatch at {resolved_path}. "
                f"Expected {AZURE_TRACE_SHA256}, got {actual_sha}."
            )

        # Load the authoritative trace arrays (immutable source artifact)
        data = np.load(str(resolved_path), allow_pickle=False)
        if "arrival_rates" not in data:
            raise KeyError(
                "Expected key 'arrival_rates' in Azure trace NPZ. "
                f"Available keys: {list(data.files)}"
            )

        # Scale trace in memory by rate_scale_factor (default 2.0x)
        self._rates: np.ndarray = data["arrival_rates"].astype(np.float64) * self.rate_scale_factor
        self._trace_len: int = len(self._rates)

    def _diurnal_fp(self, epoch: int) -> float:
        """Compute the sinusoidal diurnal fp at a given epoch."""
        t = float(epoch % self.diurnal_period_epochs) / float(self.diurnal_period_epochs)
        phase = math.cos(2.0 * math.pi * t)
        midpoint = (self.fp_diurnal_day + self.fp_diurnal_night) / 2.0
        amplitude = (self.fp_diurnal_day - self.fp_diurnal_night) / 2.0
        return _clamp(midpoint + amplitude * phase, lo=0.0, hi=1.0)

    def _trace_rate(self, epoch: int) -> float:
        """Look up the Azure trace rate for a given epoch (wrapping if trace exhausted)."""
        idx = epoch % self._trace_len
        return float(self._rates[idx])

    def sample_2d(self, epoch: int) -> Tuple[float, float]:
        """Return (lambda_t, fp_t) for the given epoch with all overlays applied."""
        base_rate = self._trace_rate(epoch)

        in_storm = any(
            s <= epoch < s + self.storm_duration_epochs
            for s in self.storm_epochs
        )

        if in_storm:
            return float(base_rate * self.storm_rate_boost), float(self.storm_fp)

        return float(base_rate), self._diurnal_fp(epoch)

    def sample(self, epoch: int) -> int:
        """1D shim: Poisson draw of the scaled Azure trace rate (no fp signal)."""
        rate, _ = self.sample_2d(epoch)
        return _poisson(rate, self._rng)


# ---------------------------------------------------------------------------
# Registry — build_2d_stream factory (mirrors build_stream from mmpp.py)
# ---------------------------------------------------------------------------


def build_2d_stream(config: dict, seed: int) -> "WorkloadStream2D":
    """Build a 2D workload stream from a configuration dictionary with doubled capacity defaults."""
    generator = str(config.get("generator", "suite1_flat")).lower()

    # ---- Suite 1 ----
    if generator == "suite1_flat":
        return Suite1FlatWorkload(
            rate_rps=float(config.get("rate_rps", 100.0)),
            seed=seed,
        )
    if generator == "suite1_spike":
        return Suite1SpikeWorkload(
            base_rate_rps=float(config.get("base_rate_rps", 60.0)),
            spike_ratio=float(config.get("spike_ratio", 5.0)),
            spike_duration_epochs=int(config.get("spike_duration_epochs", 3)),
            spike_epoch=int(config.get("spike_epoch", 50)),
            period_epochs=int(config.get("period_epochs", 0)),
            seed=seed,
        )
    if generator == "suite1_burst":
        return Suite1BurstWorkload(
            low_rate_rps=float(config.get("low_rate_rps", 40.0)),
            high_rate_rps=float(config.get("high_rate_rps", 200.0)),
            p_low_to_high=float(config.get("p_low_to_high", 0.05)),
            p_high_to_low=float(config.get("p_high_to_low", 0.15)),
            seed=seed,
        )
    if generator == "suite1_ramp":
        return Suite1RampWorkload(
            ramp_start_rps=float(config.get("ramp_start_rps", 20.0)),
            ramp_end_rps=float(config.get("ramp_end_rps", 160.0)),
            ramp_epochs=int(config.get("ramp_epochs", 100)),
            seed=seed,
        )
    if generator == "suite1_zero_begin":
        return Suite1ZeroBeginRampWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 120.0)),
            ramp_epochs=int(config.get("ramp_epochs", 50)),
            seed=seed,
        )
    if generator == "suite1_zero_terminal":
        return Suite1ZeroTerminalRampWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 120.0)),
            drain_start_epoch=int(config.get("drain_start_epoch", 80)),
            drain_end_epoch=int(config.get("drain_end_epoch", 150)),
            seed=seed,
        )

    # ---- Suite 2 ----
    if generator == "suite2_shock":
        return Suite2SteadyShockWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 100.0)),
            fp_high=float(config.get("fp_high", 0.70)),
            fp_low=float(config.get("fp_low", 0.20)),
            shock_epoch=int(config.get("shock_epoch", 60)),
            seed=seed,
        )
    if generator == "suite2_recovery":
        return Suite2SteadyRecoveryWorkload(
            steady_rate_rps=float(config.get("steady_rate_rps", 100.0)),
            fp_high=float(config.get("fp_high", 0.70)),
            fp_low=float(config.get("fp_low", 0.20)),
            shock_epoch=int(config.get("shock_epoch", 40)),
            recovery_epochs=int(config.get("recovery_epochs", 60)),
            seed=seed,
        )
    if generator in ("suite2_compound_stress", "suite2_opposing1"):
        return Suite2CompoundStressWorkload(
            base_rate_rps=float(config.get("base_rate_rps", 60.0)),
            peak_rate_rps=float(config.get("peak_rate_rps", 160.0)),
            fp_high=float(config.get("fp_high", 0.70)),
            fp_low=float(config.get("fp_low", 0.20)),
            shift_start_epoch=int(config.get("shift_start_epoch", 30)),
            shift_epochs=int(config.get("shift_epochs", 80)),
            seed=seed,
        )
    if generator in ("suite2_compound_relief", "suite2_opposing2"):
        return Suite2CompoundReliefWorkload(
            peak_rate_rps=float(config.get("peak_rate_rps", 160.0)),
            base_rate_rps=float(config.get("base_rate_rps", 60.0)),
            fp_low=float(config.get("fp_low", 0.20)),
            fp_high=float(config.get("fp_high", 0.70)),
            shift_start_epoch=int(config.get("shift_start_epoch", 30)),
            shift_epochs=int(config.get("shift_epochs", 80)),
            seed=seed,
        )
    if generator == "suite2_decoupled_opposing":
        return Suite2DecoupledOpposingWorkload(
            start_rate_rps=float(config.get("start_rate_rps", 50.0)),
            end_rate_rps=float(config.get("end_rate_rps", 150.0)),
            fp_start=float(config.get("fp_start", 0.40)),
            fp_end=float(config.get("fp_end", 0.80)),
            shift_start_epoch=int(config.get("shift_start_epoch", 20)),
            shift_epochs=int(config.get("shift_epochs", 80)),
            seed=seed,
        )
    if generator == "suite2_storm":
        return Suite2CorrelatedStormWorkload(
            base_rate_rps=float(config.get("base_rate_rps", 60.0)),
            burst_rate_rps=float(config.get("burst_rate_rps", 180.0)),
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
            rate_scale_factor=float(config.get("rate_scale_factor", 2.0)),
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
