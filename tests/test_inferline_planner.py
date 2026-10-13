"""
tests/test_inferline_planner.py — Unit Tests for InferLine Algorithms 1 & 2 Planner.

All test cases have analytically pre-computed correct answers.
Tests Erlang-C, SLO Estimator, Algorithm 1 feasibility, and Algorithm 2 cost minimization.
"""

from __future__ import annotations

import math
import pytest
from src.continuum_ext.controllers.inferline_planner import (
    _erlang_c,
    _estimate_p99_latency_ms,
    _log_factorial,
    algorithm1_find_feasible,
    algorithm2_minimize_cost,
    BatchConfig,
    InferLinePlanner,
)


def test_erlang_c():
    # C(k=1, a=0) — zero load → no waiting
    assert math.isclose(_erlang_c(1, 0.0), 0.0, abs_tol=1e-9)

    # C(k=1, a=0.5) — M/M/1 with ρ=0.5 → C(1,0.5) = ρ = 0.5
    assert math.isclose(_erlang_c(1, 0.5), 0.5, abs_tol=1e-9)

    # C(k=2, a=1.0) — M/M/2 with a=1 (ρ=0.5): C(2,1) = 1/3 ≈ 0.3333
    assert math.isclose(_erlang_c(2, 1.0), 1.0 / 3.0, abs_tol=1e-6)

    # Overloaded: a >= k → returns 1.0
    assert _erlang_c(2, 2.0) == 1.0
    assert _erlang_c(3, 5.0) == 1.0


def test_slo_estimator():
    # Zero load → P99 = edge + WAN + service only (no queuing)
    p99_zero = _estimate_p99_latency_ms(0.0, k=1, p50_ms=62.67, mu_rps=77.92)
    assert p99_zero < 500.0
    assert p99_zero >= 35.7

    # Near-saturation → P99 = inf
    p99_sat = _estimate_p99_latency_ms(78.0, k=1, p50_ms=62.67, mu_rps=77.92)
    assert math.isinf(p99_sat)

    # More workers reduce latency
    p99_k1 = _estimate_p99_latency_ms(30.0, k=1, p50_ms=62.67, mu_rps=77.92)
    p99_k4 = _estimate_p99_latency_ms(30.0, k=4, p50_ms=62.67, mu_rps=77.92)
    assert p99_k4 < p99_k1


def test_algorithm1_feasible_config():
    surface_test = {
        1: (15.52, 18.01),  # b=1: p50=15.52ms, μ=18.01 RPS
        8: (62.67, 77.92),  # b=8: p50=62.67ms, μ=77.92 RPS
    }

    # Low load: λ_planning=5 RPS, s_m=1.0 → λ_slow=5 RPS
    cfg_low = algorithm1_find_feasible(
        lambda_planning=5.0,
        s_m=1.0,
        gate2_surface=surface_test,
        slo_target_ms=500.0,
        start_batch_size=1,
    )
    assert cfg_low.slo_pass
    assert cfg_low.k_replicas == 1

    # High load: λ_planning=70 RPS, s_m=1.0
    cfg_high = algorithm1_find_feasible(
        lambda_planning=70.0,
        s_m=1.0,
        gate2_surface=surface_test,
        slo_target_ms=500.0,
        start_batch_size=1,
    )
    assert cfg_high.slo_pass
    assert cfg_high.k_replicas >= 4


def test_algorithm2_cost_minimization():
    surface_full = {
        1: (15.52, 18.01),
        2: (17.23, 34.95),
        4: (30.91, 56.41),
        8: (62.67, 77.92),
        16: (105.64, 109.86),
        32: (205.94, 130.11),
    }

    initial_low = BatchConfig(
        batch_size=1,
        k_replicas=1,
        batch_timeout_s=0.040,
        mu_rps=18.01,
        cost=1.0,
        p99_latency_ms=50.0,
        slo_pass=True,
    )
    opt_low, _ = algorithm2_minimize_cost(
        initial_config=initial_low,
        lambda_planning=5.0,
        s_m=1.0,
        gate2_surface=surface_full,
        slo_target_ms=500.0,
    )
    assert opt_low.cost <= initial_low.cost
    assert opt_low.slo_pass

    cfg_alg1_high = algorithm1_find_feasible(
        lambda_planning=40.0,
        s_m=0.5,
        gate2_surface=surface_full,
        slo_target_ms=500.0,
        start_batch_size=1,
    )
    opt_high, _ = algorithm2_minimize_cost(
        initial_config=cfg_alg1_high,
        lambda_planning=40.0,
        s_m=0.5,
        gate2_surface=surface_full,
        slo_target_ms=500.0,
    )
    assert opt_high.cost <= cfg_alg1_high.cost
    assert opt_high.slo_pass


def test_inferline_planner_integration():
    planner = InferLinePlanner(slo_target_ms=500.0, planning_fraction=0.25)
    assert math.isclose(planner.s_m, 0.50, abs_tol=1e-4)
    assert len(planner.gate2_surface) == 6

    _, mu_b8 = planner.gate2_surface[8]
    assert abs(mu_b8 - 77.92) < 0.5

    arrival_rates = [50.0] * 200
    output = planner.plan(arrival_rates)

    assert output is not None
    assert abs(output.lambda_planning - 50.0) < 0.01
    assert abs(output.lambda_slow_planning - 25.0) < 0.01
    assert output.p99_estimate_ms < 500.0
    assert output.rho_m < 1.0
    assert output.initial_replicas >= 1
    assert output.hardware == "Tesla T4"
    assert output.planning_epochs == 50
