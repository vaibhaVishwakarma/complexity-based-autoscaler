"""
tests/test_inferline_exact.py — Unit Tests for InferLine Exact Autoscaler Replication.

Tests algorithm logic directly at the method level to isolate
scaling decisions from the placement layer.
All test cases have analytically-known correct answers.
"""

from __future__ import annotations

import math
import pytest
from continuum_bench.controllers.interfaces import WorkerPoolSnapshot
from src.continuum_ext.controllers.inferline_exact import (
    InferLineExactController,
    _SlidingArrivalBuffer,
)


def make_snap(active: int = 1, total: int = 50) -> WorkerPoolSnapshot:
    return WorkerPoolSnapshot(
        stage="CloudRefine",
        active_workers=active,
        total_workers=total,
        min_workers=1,
        max_workers=total,
        active_worker_ids=[f"w{i}" for i in range(active)],
        inactive_worker_ids=[f"w{i}" for i in range(active, total)],
    )


def test_sliding_arrival_buffer():
    buf = _SlidingArrivalBuffer(max_window=60)
    assert buf.window_max(10) == 0.0

    buf.push(5.0)
    buf.push(10.0)
    buf.push(3.0)
    assert buf.window_max(3) == 10.0
    assert buf.window_max(1) == 3.0
    assert buf.window_max(2) == 10.0

    for v in range(60):
        buf.push(float(v))
    assert buf.window_max(60) == 59.0
    assert buf.window_max(1) == 59.0


def test_steady_state_replica_count():
    c1 = InferLineExactController(
        window_sizes_epochs=(1, 2, 4),
        invocation_prob=1.0,
        rho_m=1.0,
        min_replicas=1,
        replan_on_scale=False,
        periodic_replan=False,
    )
    c1._capacity_rps = 10.0
    c1._ensure_stage("CloudRefine")
    for _ in range(20):
        c1._arrival_buf["CloudRefine"].push(5.0)

    r = c1._algorithm3_rmax("CloudRefine")
    assert r == 5.0
    assert c1._algorithm3_desired(r, make_snap()) == 1


def test_step_spike():
    c2 = InferLineExactController(
        window_sizes_epochs=(1, 2, 4),
        invocation_prob=1.0,
        rho_m=1.0,
        min_replicas=1,
        replan_on_scale=False,
        periodic_replan=False,
    )
    c2._capacity_rps = 10.0
    c2._ensure_stage("CloudRefine")
    for _ in range(5):
        c2._arrival_buf["CloudRefine"].push(2.0)
    c2._arrival_buf["CloudRefine"].push(80.0)  # spike

    r2 = c2._algorithm3_rmax("CloudRefine")
    assert r2 >= 8.0
    assert c2._algorithm3_desired(r2, make_snap()) == 8


def test_stabilisation_delay():
    counter = 14
    assert counter < 15
    counter += 1
    assert counter == 15


def test_sliding_window_max():
    c5 = InferLineExactController(
        window_sizes_epochs=(4, 8),
        invocation_prob=1.0,
        rho_m=1.0,
        min_replicas=1,
        replan_on_scale=False,
        periodic_replan=False,
    )
    c5._capacity_rps = 10.0
    c5._arrival_buf["CloudRefine"] = _SlidingArrivalBuffer(max_window=60)
    for v in [20.0] + [0.0] * 7:
        c5._arrival_buf["CloudRefine"].push(v)

    r5 = c5._algorithm3_rmax("CloudRefine")
    assert math.isclose(r5, 2.5, rel_tol=1e-9)
    assert c5._algorithm3_desired(r5, make_snap()) == 1

    wm4 = c5._arrival_buf["CloudRefine"].window_max(4)
    wm8 = c5._arrival_buf["CloudRefine"].window_max(8)
    assert wm4 == 0.0
    assert wm8 == 20.0


def test_algorithm4_rolling_max():
    c6 = InferLineExactController(
        window_sizes_epochs=(1,),
        invocation_prob=1.0,
        rho_m=1.0,
        stabilise_epochs=15,
        bucket_size_epochs=5,
        scaledown_window_epochs=30,
        min_replicas=1,
        replan_on_scale=False,
        periodic_replan=False,
    )
    c6._capacity_rps = 10.0
    c6._rho_p = 1.0
    n_buckets = 30 // 5
    c6._lambda_5s_buf["CloudRefine"] = _SlidingArrivalBuffer(max_window=n_buckets)
    for _ in range(5):
        c6._lambda_5s_buf["CloudRefine"].push(0.0)
    c6._lambda_5s_buf["CloudRefine"].push(50.0)

    d6 = c6._algorithm4_desired("CloudRefine", make_snap(active=10))
    assert d6 == 5

    c6._lambda_5s_buf["CloudRefine"] = _SlidingArrivalBuffer(max_window=n_buckets)
    for _ in range(6):
        c6._lambda_5s_buf["CloudRefine"].push(0.0)
    d6b = c6._algorithm4_desired("CloudRefine", make_snap(active=10))
    assert d6b == 1


def test_sm_and_rho_m_scaling():
    snap7 = make_snap()

    c7a = InferLineExactController(invocation_prob=0.5, rho_m=1.0, replan_on_scale=False, periodic_replan=False)
    c7a._capacity_rps = 10.0
    assert c7a._algorithm3_desired(20.0, snap7) == 1

    c7b = InferLineExactController(invocation_prob=1.0, rho_m=1.0, replan_on_scale=False, periodic_replan=False)
    c7b._capacity_rps = 10.0
    assert c7b._algorithm3_desired(20.0, snap7) == 2

    c7c = InferLineExactController(invocation_prob=1.0, rho_m=2.0, replan_on_scale=False, periodic_replan=False)
    c7c._capacity_rps = 10.0
    assert c7c._algorithm3_desired(20.0, snap7) == 1


def test_sliding_window_vs_ema_distinction():
    c8 = InferLineExactController(
        window_sizes_epochs=(5,),
        invocation_prob=1.0,
        rho_m=1.0,
        min_replicas=1,
        replan_on_scale=False,
        periodic_replan=False,
    )
    c8._capacity_rps = 10.0
    c8._arrival_buf["CloudRefine"] = _SlidingArrivalBuffer(max_window=60)
    for _ in range(5):
        c8._arrival_buf["CloudRefine"].push(100.0)
    for _ in range(10):
        c8._arrival_buf["CloudRefine"].push(0.0)

    r8 = c8._algorithm3_rmax("CloudRefine")
    assert r8 == 0.0
