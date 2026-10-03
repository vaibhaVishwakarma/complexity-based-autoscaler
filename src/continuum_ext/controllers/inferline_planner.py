"""
inferline_planner.py — Full InferLine Low-Frequency Planner (Algorithms 1 & 2, SoCC '20).

Role: Offline planning component of the InferLine replication.
      Produces the (batch_size, initial_replicas, s_m, rho_m) configuration tuple
      that seeds the High-Frequency Tuner (InferLineExactController, Algs 3 & 4).

Paper: Crankshaw et al., "InferLine: Latency-Aware Provisioning and Scaling for
       Prediction Serving Pipelines", ACM SoCC '20.
       Reference: references/papers/InferLine_Crankshaw_SoCC_2020.pdf
       Methodology: references/eval-methodologies/inferline_evaluation_benchmarking_methodology.md

What this implements:
  Algorithm 1 — Find Feasible Initial Configuration:
    For each candidate (batch_size, k_replicas) starting from (b=1, k=1):
      Use the SLO Estimator (M/D/k queuing model) to predict P99 end-to-end latency.
      If SLO not met: increment replicas on the bottleneck stage (CloudRefine).
    Output: minimum (b, k) that satisfies the SLO under planning-trace load.

  Algorithm 2 — Greedy Cost Minimization:
    From the feasible config output of Alg 1, greedily try three mutations:
      (a) IncreaseBatch: b → next_b; recompute k to maintain SLO.
      (b) RemoveReplica: k → k−1; check SLO still holds.
      (c) DowngradeHardware: not applicable (single T4 tier in our setup).
    Accept the mutation if cost improves and SLO still holds.
    Repeat until no improving move exists.

SLO Estimator (replaces InferLine's discrete-event Estimator):
  InferLine uses a continuous-time discrete-event simulator as its Estimator.
  We implement an analytical M/D/k queuing approximation, which is a standard
  substitute for pipeline planning when a full simulation is unavailable:
    - Arrivals: Poisson(λ_slow) where λ_slow = λ_planning × s_m
    - Service:  Deterministic at T_s = p50_ms(b) / 1000  (from Gate 2 surface)
    - Servers:  k parallel workers
  We use the Pollaczek-Khinchine formula for M/D/k upper-bounded by M/M/k:
    E[Wq] ≤ E[Wq_MM1] = ρ / (k × μ × (1−ρ))  where ρ = λ_slow / (k × μ)
  P99 latency estimate = T_edge + T_wan + E[Wq] + T_s(b)
  where T_edge = 10.70ms (Gate 2 CPU profile), T_wan = 25ms (one-way WAN RTT).

Cost model (from paper §3):
  cost(b, k) = k × (GPU cost per replica per unit time)
  Since hardware is fixed (T4), the normalised cost is simply k replicas.
  Algorithm 2 minimises k while maintaining SLO.

Planning trace:
  The planning trace is the first `planning_fraction` (default 0.25 = 25%) of the
  workload's arrival rates. Mean arrival rate λ_planning is computed from this window.
  This mirrors InferLine's use of "sample trace" for planning (paper §4.2).

Inputs:
  - arrival_rates: array of per-epoch arrival rates (λ(t)) from workload generator.
  - planning_fraction: fraction of trace to use as planning window (default 0.25).
  - Gate 1 contract: s_m = 1 − fast_path_fraction.
  - Gate 2 contract: batch-size-indexed (p50_ms, μ_m) surface.

Outputs:
  - PlannerOutput dataclass: (batch_size, initial_replicas, s_m, rho_m, batch_timeout_s,
    mu_rps, lambda_planning, diagnostics)
  - Serialisable to JSON for archival and downstream loading by InferLineExactController.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants (immutable — AGENTS.md §2)
# ---------------------------------------------------------------------------

SEED: int = 42

#: Available batch sizes from the Gate 2 surface (Tesla T4 profiling).
_AVAILABLE_BATCH_SIZES: Tuple[int, ...] = (1, 2, 4, 8, 16, 32)

#: Batch formation timeout matched to Gate 2 standard evaluation (seconds).
_BATCH_TIMEOUT_S: float = 0.040

#: End-to-end SLO target (milliseconds). Paper uses 500ms for cascade pipelines.
_SLO_TARGET_MS: float = 500.0

#: Edge node inference latency from Gate 2 CPU profile (milliseconds).
_T_EDGE_MS: float = 10.70

#: One-way WAN latency from edge to cloud (milliseconds).
_T_WAN_MS: float = 25.0

#: Fraction of workload trace used as planning window (paper §4.2: first 25%).
_PLANNING_FRACTION: float = 0.25

#: Maximum utilisation allowed in planning (ρ < this prevents queue blowup).
_MAX_RHO: float = 0.95

#: Maximum replicas to search in Algorithm 1 before giving up.
_MAX_REPLICAS_SEARCH: int = 200


# ---------------------------------------------------------------------------
# Typed outputs
# ---------------------------------------------------------------------------


@dataclass
class BatchConfig:
    """Configuration for a single candidate (batch_size, k_replicas) pair."""
    batch_size: int
    k_replicas: int
    batch_timeout_s: float
    mu_rps: float          # single-replica throughput at this batch_size
    cost: float            # normalised cost (= k_replicas, T4 hardware fixed)
    p99_latency_ms: float  # estimated P99 E2E latency from SLO Estimator
    slo_pass: bool         # whether this config satisfies _SLO_TARGET_MS


@dataclass
class PlannerOutput:
    """Output of the InferLine Planner (Algorithms 1 & 2).

    This is the authoritative config consumed by InferLineExactController.
    Serialisable to JSON for archival and audit trail.
    """
    # Core planning outputs
    batch_size: int                # b* — optimal batch size from Algorithm 2
    initial_replicas: int          # k* — initial replica count from Algorithms 1+2
    batch_timeout_s: float         # τ — batch formation timeout
    mu_rps: float                  # μ_m — single-replica throughput at b*
    s_m: float                     # conditional invocation probability (from Gate 1)
    rho_m: float                   # max-provisioning factor = λ_planning×s_m / μ_m
    lambda_planning: float         # mean λ from planning trace
    lambda_slow_planning: float    # λ_slow = λ × s_m during planning trace

    # Diagnostics
    alg1_feasible_config: Dict     # intermediate config from Algorithm 1
    alg2_improvement: bool         # whether Algorithm 2 improved the config
    slo_target_ms: float           # SLO target used
    p99_estimate_ms: float         # estimated P99 at final config
    planning_fraction: float       # fraction of trace used
    planning_epochs: int           # number of epochs in planning window
    hardware: str                  # hardware tier (always "Tesla T4")


# ---------------------------------------------------------------------------
# Gate contract loaders
# ---------------------------------------------------------------------------


def _load_gate2_surface() -> Dict[int, Tuple[float, float]]:
    """Load Gate 2 batch surface → {batch_size: (p50_ms, mu_rps)}.

    Returns a mapping from each available batch size to its empirical
    P50 execution latency and throughput capacity at the standard timeout.
    Never hardcodes values — always loads from contracts.gate2.
    """
    try:
        from contracts.gate2 import load_gate2_profiles  # type: ignore[import]
        profiles = load_gate2_profiles()
        surface: Dict[int, Tuple[float, float]] = {}
        for entry in profiles.gpu_profiles_raw:
            b = entry.batch_size
            mu = profiles.compute_service_capacity_rps(b, _BATCH_TIMEOUT_S)
            surface[b] = (float(entry.p50_ms), float(mu))
        return surface
    except Exception as exc:
        raise RuntimeError(
            f"Gate2 contract required for InferLine Planner but failed to load: {exc}"
        ) from exc


def _load_gate1_s_m() -> float:
    """Load s_m = 1 − fast_path_fraction from Gate 1 contract.

    This is the conditional invocation probability of the CloudRefine stage —
    the fraction of requests that reach the cloud tier under calibration conditions.
    """
    try:
        from contracts.gate1 import load_gate1_config  # type: ignore[import]
        cfg = load_gate1_config()
        s_m = 1.0 - float(cfg.fast_path_fraction)
        return max(0.01, min(1.0, s_m))
    except Exception as exc:
        raise RuntimeError(
            f"Gate1 contract required for InferLine Planner but failed to load: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# SLO Estimator — M/D/k analytical queuing model
# ---------------------------------------------------------------------------


def _estimate_p99_latency_ms(
    lambda_slow: float,
    k: int,
    p50_ms: float,
    mu_rps: float,
) -> float:
    """Estimate P99 end-to-end latency using M/D/k queuing model.

    InferLine uses a discrete-event Estimator; we substitute a closed-form
    analytical M/D/k approximation, which is standard practice for planning
    phases in systems that lack a pre-built simulator.

    Model:
      - Arrivals: Poisson(λ_slow)  [M]
      - Service:  Deterministic T_s = p50_ms/1000  [D]
      - Servers:  k parallel workers  [k]

    For M/D/k, the mean waiting time is bounded from above by M/M/k:
      E[Wq_MM1] = C(k, a) / (k*μ - λ_slow)
    where C(k, a) is the Erlang-C probability (fraction waiting > 0).
    We add a P99 tail factor of 3× the mean wait (upper bound for exponential tails).

    Total P99 = T_edge + T_wan + E[Wq] × tail_factor + T_service
    where tail_factor = 3.0 conservatively bounds P99 for Poisson queuing.

    Args:
        lambda_slow: Effective arrival rate to cloud stage (requests/s).
        k:          Number of parallel cloud workers.
        p50_ms:     Median service time at given batch size (ms from Gate 2).
        mu_rps:     Single-worker throughput in requests/second.

    Returns:
        Estimated P99 end-to-end latency in milliseconds.
    """
    if k <= 0 or mu_rps <= 0.0:
        return float("inf")

    T_s = p50_ms / 1000.0  # service time in seconds
    total_mu = k * mu_rps
    rho = lambda_slow / total_mu  # system utilisation

    if rho >= _MAX_RHO:
        # Near-saturation: queue length → ∞, SLO guaranteed to fail
        return float("inf")

    if lambda_slow <= 0.0:
        # No load: only fixed latencies
        p99_ms = _T_EDGE_MS + _T_WAN_MS + (p50_ms * 1.2)  # 1.2× for p99 of deterministic
        return p99_ms

    # Erlang-C probability C(k, a) using the recursive formula
    # a = λ_slow / mu_rps  (offered load in Erlangs)
    a = lambda_slow / mu_rps
    erlang_c = _erlang_c(k, a)

    # Mean waiting time in queue (M/D/k is ≤ M/M/k, so this is an upper bound)
    mean_wait_s = erlang_c / (total_mu - lambda_slow)

    # P99 tail: for M/M/k, P(Wq > t) = C(k,a) × exp(−(kμ−λ)t)
    # P99 → P(Wq > t99) = 0.01 → t99 = −ln(0.01/C) / (kμ−λ)
    if erlang_c > 0.01:
        tail_rate = total_mu - lambda_slow
        t99_wait_s = -math.log(0.01 / erlang_c) / tail_rate
    else:
        # Very low Erlang-C: effectively no waiting
        t99_wait_s = mean_wait_s * 3.0

    # P99 service time: for deterministic (M/D), P99 ≈ p99_ms from Gate 2 surface
    # We use p50 × 1.2 as a conservative bound (jitter_cv ≈ 0.05 from Gate 2)
    T_service_p99_ms = p50_ms * 1.15

    # Total P99 E2E latency
    p99_ms = _T_EDGE_MS + _T_WAN_MS + (t99_wait_s * 1000.0) + T_service_p99_ms
    return float(p99_ms)


def _erlang_c(k: int, a: float) -> float:
    """Compute the Erlang-C probability C(k, a) — fraction of arrivals that wait.

    Uses the numerically stable recursive form to avoid overflow for large k.
    C(k, a) = (a^k / k!) × (k/(k−a)) / [sum_{n=0}^{k-1} (a^n/n!) + (a^k/k!)×(k/(k−a))]

    Args:
        k: Number of servers.
        a: Offered load = λ/μ (in Erlangs, NOT utilisation ρ = a/k).

    Returns:
        Erlang-C probability in [0, 1]. Returns 1.0 if system is overloaded (a ≥ k).
    """
    if a >= k:
        return 1.0  # overloaded — all arrivals wait

    # Compute using numerically stable log-space arithmetic
    log_a = math.log(a) if a > 0 else float("-inf")

    # Numerator: (a^k / k!) × (k / (k − a))
    log_numerator = k * log_a - _log_factorial(k) + math.log(k / (k - a))

    # Denominator: sum_{n=0}^{k-1} a^n/n!  + numerator_value
    log_terms = [n * log_a - _log_factorial(n) for n in range(k)]
    # Log-sum-exp for numerical stability
    max_log = max(max(log_terms), log_numerator)
    sum_exp = sum(math.exp(lt - max_log) for lt in log_terms) + math.exp(log_numerator - max_log)
    log_denominator = max_log + math.log(sum_exp)

    erlang_c = math.exp(log_numerator - log_denominator)
    return float(min(1.0, max(0.0, erlang_c)))


def _log_factorial(n: int) -> float:
    """Compute log(n!) using Stirling's approximation for large n, exact for small n."""
    if n <= 20:
        result = 0.0
        for i in range(2, n + 1):
            result += math.log(i)
        return result
    # Stirling: log(n!) ≈ n*log(n) - n + 0.5*log(2πn)
    return n * math.log(n) - n + 0.5 * math.log(2 * math.pi * n)


# ---------------------------------------------------------------------------
# Algorithm 1 — Find Feasible Configuration
# ---------------------------------------------------------------------------


def algorithm1_find_feasible(
    lambda_planning: float,
    s_m: float,
    gate2_surface: Dict[int, Tuple[float, float]],
    slo_target_ms: float = _SLO_TARGET_MS,
    start_batch_size: int = 1,
) -> BatchConfig:
    """Algorithm 1: Find minimum feasible (batch_size, k_replicas) under planning load.

    Starts at (b=start_batch_size, k=1). Increments k_replicas until the SLO
    Estimator confirms the configuration meets slo_target_ms.

    This mirrors InferLine Algorithm 1:
      'Start with b=1, k=1. While not feasible: scale up the bottleneck stage.'
    Since our pipeline has only one scalable stage (CloudRefine), the bottleneck
    is always CloudRefine, so we simply increment k.

    Args:
        lambda_planning: Mean total arrival rate from planning trace (requests/s).
        s_m:             Conditional invocation probability (fraction reaching cloud).
        gate2_surface:   {batch_size: (p50_ms, mu_rps)} from Gate 2 contract.
        slo_target_ms:   End-to-end SLO target in milliseconds.
        start_batch_size: Initial batch size to try (Algorithm 1 starts at b=1).

    Returns:
        BatchConfig with the minimum (b, k) that satisfies the SLO.

    Raises:
        RuntimeError: If no feasible config is found within _MAX_REPLICAS_SEARCH.
    """
    lambda_slow = lambda_planning * s_m

    if start_batch_size not in gate2_surface:
        # Fall back to smallest available batch size
        start_batch_size = min(gate2_surface.keys())

    p50_ms, mu_rps = gate2_surface[start_batch_size]

    for k in range(1, _MAX_REPLICAS_SEARCH + 1):
        p99 = _estimate_p99_latency_ms(lambda_slow, k, p50_ms, mu_rps)
        if p99 <= slo_target_ms:
            cost = float(k)  # normalised cost = replica count (T4 hardware fixed)
            return BatchConfig(
                batch_size=start_batch_size,
                k_replicas=k,
                batch_timeout_s=_BATCH_TIMEOUT_S,
                mu_rps=mu_rps,
                cost=cost,
                p99_latency_ms=p99,
                slo_pass=True,
            )

    raise RuntimeError(
        f"Algorithm 1 failed to find feasible config for λ_planning={lambda_planning:.2f}, "
        f"s_m={s_m:.4f}, b={start_batch_size} within {_MAX_REPLICAS_SEARCH} replicas."
    )


# ---------------------------------------------------------------------------
# Algorithm 2 — Greedy Cost Minimization
# ---------------------------------------------------------------------------


def algorithm2_minimize_cost(
    initial_config: BatchConfig,
    lambda_planning: float,
    s_m: float,
    gate2_surface: Dict[int, Tuple[float, float]],
    slo_target_ms: float = _SLO_TARGET_MS,
) -> Tuple[BatchConfig, bool]:
    """Algorithm 2: Greedy cost minimization from a feasible initial config.

    At each iteration, evaluates three mutations:
      (a) IncreaseBatch: b → next larger batch size, recompute minimum k.
      (b) RemoveReplica: k → k−1, verify SLO still holds.
      (c) DowngradeHardware: not applicable (single T4 tier in our setup).

    Accepts the mutation that gives the greatest cost reduction while still
    satisfying the SLO. Terminates when no improving mutation exists.

    This mirrors InferLine Algorithm 2 exactly, adapted to our single-stage,
    single-hardware-tier pipeline.

    Args:
        initial_config: Feasible config from Algorithm 1.
        lambda_planning: Mean total arrival rate from planning trace.
        s_m:             Conditional invocation probability.
        gate2_surface:   {batch_size: (p50_ms, mu_rps)} from Gate 2 contract.
        slo_target_ms:   End-to-end SLO target in milliseconds.

    Returns:
        Tuple of (optimised BatchConfig, improved: bool).
        'improved' is True if Algorithm 2 found a cheaper config than Alg 1.
    """
    lambda_slow = lambda_planning * s_m
    current = initial_config
    improved = False
    batch_sizes_sorted = sorted(gate2_surface.keys())

    while True:
        best_candidate: Optional[BatchConfig] = None

        # --- Mutation (a): IncreaseBatch ---
        # Higher batch size amortises GPU execution cost across more requests,
        # potentially allowing fewer replicas to meet the same SLO.
        current_b_idx = batch_sizes_sorted.index(current.batch_size) if current.batch_size in batch_sizes_sorted else -1
        if current_b_idx >= 0 and current_b_idx < len(batch_sizes_sorted) - 1:
            next_b = batch_sizes_sorted[current_b_idx + 1]
            next_p50_ms, next_mu_rps = gate2_surface[next_b]
            # Find minimum k at the new batch size
            for k_try in range(1, current.k_replicas + 1):
                p99_try = _estimate_p99_latency_ms(lambda_slow, k_try, next_p50_ms, next_mu_rps)
                if p99_try <= slo_target_ms:
                    candidate = BatchConfig(
                        batch_size=next_b,
                        k_replicas=k_try,
                        batch_timeout_s=_BATCH_TIMEOUT_S,
                        mu_rps=next_mu_rps,
                        cost=float(k_try),
                        p99_latency_ms=p99_try,
                        slo_pass=True,
                    )
                    if candidate.cost < current.cost:
                        if best_candidate is None or candidate.cost < best_candidate.cost:
                            best_candidate = candidate
                    break  # found minimum k for this batch size

        # --- Mutation (b): RemoveReplica ---
        # One fewer replica reduces cost by 1 unit; verify SLO still holds.
        if current.k_replicas > 1:
            k_reduced = current.k_replicas - 1
            p99_reduced = _estimate_p99_latency_ms(
                lambda_slow, k_reduced, gate2_surface[current.batch_size][0], current.mu_rps
            )
            if p99_reduced <= slo_target_ms:
                candidate_reduce = BatchConfig(
                    batch_size=current.batch_size,
                    k_replicas=k_reduced,
                    batch_timeout_s=_BATCH_TIMEOUT_S,
                    mu_rps=current.mu_rps,
                    cost=float(k_reduced),
                    p99_latency_ms=p99_reduced,
                    slo_pass=True,
                )
                if best_candidate is None or candidate_reduce.cost < best_candidate.cost:
                    best_candidate = candidate_reduce

        # --- Accept best improving mutation or stop ---
        if best_candidate is None or best_candidate.cost >= current.cost:
            break  # no improving mutation — local optimum reached

        current = best_candidate
        improved = True

    return current, improved


# ---------------------------------------------------------------------------
# InferLinePlanner — combined entry point
# ---------------------------------------------------------------------------


class InferLinePlanner:
    """Full InferLine Low-Frequency Planner: Algorithms 1 & 2 with SLO Estimator.

    Usage:
        planner = InferLinePlanner()
        output = planner.plan(arrival_rates=workload.arrival_rates_array)
        # output.batch_size, output.initial_replicas, output.s_m, output.rho_m
        # → feed into InferLineExactController

    The planner is stateless and can be called once per workload before simulation.
    """

    def __init__(
        self,
        slo_target_ms: float = _SLO_TARGET_MS,
        planning_fraction: float = _PLANNING_FRACTION,
    ) -> None:
        """Load Gate 1 and Gate 2 contracts; configure SLO and planning window.

        Args:
            slo_target_ms:      P99 SLO target in milliseconds (default 500ms).
            planning_fraction:  Fraction of trace to use as planning window (default 0.25).
        """
        self.slo_target_ms = float(slo_target_ms)
        self.planning_fraction = float(planning_fraction)

        # Load Gate contracts at construction (fail fast if unavailable)
        self._gate2_surface = _load_gate2_surface()
        self._s_m = _load_gate1_s_m()

    def plan(
        self,
        arrival_rates: "List[float]",
        output_path: Optional[Path] = None,
    ) -> PlannerOutput:
        """Run Algorithms 1 & 2 on the provided arrival rate trace.

        Args:
            arrival_rates: Per-epoch arrival rates λ(t) from the workload generator.
                           Must be non-empty. First planning_fraction is the planning window.
            output_path:   Optional path to write the PlannerOutput JSON for archival.

        Returns:
            PlannerOutput with the cost-optimal feasible configuration.
        """
        if not arrival_rates:
            raise ValueError("arrival_rates must be non-empty")

        # --- Extract planning window (first 25% of trace) ---
        n_planning = max(1, int(len(arrival_rates) * self.planning_fraction))
        planning_window = arrival_rates[:n_planning]
        lambda_planning = float(sum(planning_window) / len(planning_window))

        # --- Load planning parameters ---
        s_m = self._s_m
        lambda_slow = lambda_planning * s_m

        # --- Algorithm 1: Find feasible config starting at b=1, k=1 ---
        alg1_config = algorithm1_find_feasible(
            lambda_planning=lambda_planning,
            s_m=s_m,
            gate2_surface=self._gate2_surface,
            slo_target_ms=self.slo_target_ms,
            start_batch_size=1,  # Paper: always starts from smallest batch
        )

        # --- Algorithm 2: Greedy cost minimization ---
        optimal_config, alg2_improved = algorithm2_minimize_cost(
            initial_config=alg1_config,
            lambda_planning=lambda_planning,
            s_m=s_m,
            gate2_surface=self._gate2_surface,
            slo_target_ms=self.slo_target_ms,
        )

        # --- Compute ρ_m = λ_slow_planning / μ_m (max-provisioning factor) ---
        mu_m = optimal_config.mu_rps
        rho_m = (lambda_slow / mu_m) if mu_m > 0 else 1.0

        output = PlannerOutput(
            batch_size=optimal_config.batch_size,
            initial_replicas=optimal_config.k_replicas,
            batch_timeout_s=optimal_config.batch_timeout_s,
            mu_rps=optimal_config.mu_rps,
            s_m=s_m,
            rho_m=float(rho_m),
            lambda_planning=float(lambda_planning),
            lambda_slow_planning=float(lambda_slow),
            alg1_feasible_config=asdict(alg1_config),
            alg2_improvement=alg2_improved,
            slo_target_ms=self.slo_target_ms,
            p99_estimate_ms=optimal_config.p99_latency_ms,
            planning_fraction=self.planning_fraction,
            planning_epochs=n_planning,
            hardware="Tesla T4",
        )

        if output_path is not None:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(asdict(output), f, indent=2)

        return output

    @property
    def s_m(self) -> float:
        """Return the conditional invocation probability loaded from Gate 1."""
        return self._s_m

    @property
    def gate2_surface(self) -> Dict[int, Tuple[float, float]]:
        """Return the Gate 2 batch surface {batch_size: (p50_ms, mu_rps)}."""
        return dict(self._gate2_surface)
