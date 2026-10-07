"""
src/continuum_ext/realism/__init__.py — Physical Realism & Hardware Modeling Extensions
========================================================================================
Exposes calibrated modules for dynamic GPU batching, WAN batch transmission latency,
and multi-horizon realism overlays for ContinuumBench.
"""

from src.continuum_ext.realism.dynamic_batching_model import TritonDynamicBatchingModel
from src.continuum_ext.realism.network_batch_link import CalibratedWanBatchLink

__all__ = ["TritonDynamicBatchingModel", "CalibratedWanBatchLink"]
