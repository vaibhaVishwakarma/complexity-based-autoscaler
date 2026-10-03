"""Workload package."""

from typing import Any, Dict

from continuum_bench.workload.mmpp import (
    JitteredBurstSpec,
    JitteredBurstWorkload,
    MMPPWorkload,
    PhaseBurstSpec,
    PhaseBurstWorkload,
    PiecewiseRegimeWorkload,
    RegimeSegment,
    WorkloadStream,
    build_stream as _build_stream_mmpp,
)
from continuum_bench.workload.conformal_workloads import (
    REGIME_INITIALIZATION_PROFILES,
    WorkloadStream2D,
    build_2d_stream,
    get_regime_initialization,
)


def build_stream(config: Dict[str, Any], seed: int) -> WorkloadStream:
    """Build a workload stream, delegating 2D conformal generators to build_2d_stream."""
    generator = str(config.get("generator", "piecewise")).lower()
    if generator.startswith("suite"):
        return build_2d_stream(config, seed)
    try:
        return _build_stream_mmpp(config, seed)
    except ValueError:
        return build_2d_stream(config, seed)


__all__ = [
    "JitteredBurstSpec",
    "JitteredBurstWorkload",
    "MMPPWorkload",
    "PhaseBurstSpec",
    "PhaseBurstWorkload",
    "PiecewiseRegimeWorkload",
    "RegimeSegment",
    "WorkloadStream",
    "WorkloadStream2D",
    "build_stream",
    "build_2d_stream",
    "REGIME_INITIALIZATION_PROFILES",
    "get_regime_initialization",
]
