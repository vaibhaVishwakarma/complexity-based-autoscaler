# Implementation Plan: Comprehensive Realism & Scale-Gap Bridging Architecture

## Goal Description
Our current testbed validated the core theoretical advantage of Evolved Conformal Autoscaling under isolated synthetic and trace workloads (Step 8: $N=20$ seeds, $1,300$ runs, $p < 10^{-15}$). However, real-world edge-cloud serving of modern machine learning models (from lightweight vision backbones to heavy Vision-Language Models and LLMs) introduces severe physical and infrastructural delays that are not captured in the 80-second Tier T0 benchmark:
1. **Smooth, Continuous Model Initialization Spectrum ($T_{\text{boot}} \in [0.5\text{s}, 1.0\text{s}, 5.0\text{s}, 15.0\text{s}, 50\text{s}, 100\text{s}, 150\text{s}, 200\text{s}, 250\text{s}, 300\text{s}]$)**: Replacing impulsive leaps with a rigorous, non-impulsive ladder spanning microVM snapshots ($0.5\text{s}$), standard cached containers ($1\text{s}-5\text{s}$), medium vision weights ($15\text{s}-50\text{s}$), and heavy multi-GPU VLM/LLM cold pulls and CUDA graph initialization ($100\text{s}-300\text{s}$).
2. **Unified Enterprise Elasticity ($k_{\min} \ge 1$)**: Eliminating the clutter of scale-to-zero ($k=0$) edge cases. All controllers operate with a warm baseline ($k_{\min} = 1$), isolating and evaluating the **elastic expansion envelope** ($k \in [1, 18]$) when sudden bursts hit.
3. **Network Transmission Delays & Bandwidth Contention**: Batching-based payload serialization ($B \times \text{bytes}$) over constrained uplinks (e.g., 50 Mbps cellular WAN) and non-zero packet jitter.
4. **Server-Side Dynamic GPU Batching**: Non-linear execution scaling ($\mu(B) = \frac{B}{T_0 + \beta B}$) and queue formation timeouts ($T_{\text{timeout}}$).
5. **Macro-Horizon Evaluation**: Extending simulation windows from 80s/120s to 1,800 seconds (30 minutes) using the full 14-day production Azure Functions trace dataset to allow multi-minute boot cycles to be physically observed.
6. **Closed-Loop Edge Backpressure & Graceful Degradation**: Preventing queue poisoning when cold boot delays exceed the SLA deadline ($T_{\text{boot}} > D$).

This plan establishes a principled, modular architecture to model, simulate, and benchmark these physical dynamics without corrupting the canonical Step 8 foundation.

---

## User Review Required

> [!IMPORTANT]
> **Macro-Horizon Benchmark Scaling Required for $T_{\text{boot}} \in [50\text{s}, 300\text{s}]$**
> In an 80-second simulation, a 100-second or 300-second cold start cannot physically finish booting before the experiment terminates. To rigorously evaluate multi-minute cold starts, we introduce a **Macro-Horizon Benchmark Suite** (`macro_azure_1800s.yaml`) running 1,800 seconds (30 minutes) using continuous slices from our 14-day Azure production trace (`data/azure_traces/azure_functions_2019_processed.npz`).

> [!NOTE]
> **Unified $k_{\min} \ge 1$ Baseline (Keep-Warm Enterprise Model)**
> Per user guidance, we declutter the evaluation by fixing $k_{\min} = 1$ across all controllers and regimes. All controllers (HPA, KEDA, InferLine, Evolved Conformal) start with 1 active worker, guaranteeing that baseline interactive requests are served, and focusing the evaluation squarely on **elastic surge expansion** under long boot times ($T_{\text{boot}} \in [0.5\text{s} \to 300\text{s}]$).

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Edge Layer [Edge Device Layer]
        Camera[Camera / Sensor Stream] --> EdgePre[Edge Preprocessing]
        EdgePre --> EdgeInfer[Edge Fast Inference]
        EdgeInfer --> ConformalTriage{Conformal Prediction<br/>Set Size |C(x)| > 1 ?}
        
        ConformalTriage -->|Certain: Local Exit| EdgeSink[Edge Local Result]
        ConformalTriage -->|Uncertain: Need Cloud| BackpressureGate{Cloud ETA < SLA D ?<br/>Queue + Boot Lag}
        
        BackpressureGate -->|ETA > D: Fallback| EdgeDegrade[Graceful Edge Fallback<br/>Local Low-Conf / Shed]
        BackpressureGate -->|ETA < D: Offload| EdgeBatcher[Edge WAN Batcher<br/>Payload: B * Size]
    end

    subgraph Network Layer [Calibrated Network WAN]
        EdgeBatcher -->|Bandwidth Contention<br/>T_net = RTT + (B*Size)/BW| WANLink[WAN Link with Jitter & Loss]
    end

    subgraph Cloud Layer [Cloud GPU Elastic Cluster - k >= 1]
        WANLink --> CloudIngress[Cloud Ingress Queue Q_t]
        
        CloudIngress --> DynamicBatcher[Triton Dynamic Batcher<br/>Timeout: T_timeout | Batch Size B]
        DynamicBatcher --> GPUWorkers[Active GPU Workers k_t >= 1<br/>mu(B) = B / (T_0 + beta*B)]
        
        GPUWorkers --> CloudSink[Cloud Refinement Result]
    end

    subgraph Control Layer [Multi-Horizon Elastic Controller]
        EdgeInfer -.->|Fast Signal: lambda_cloud(t)| FastController[Micro-Elastic Conformal Controller<br/>Fast Hysteresis + Booting Credit]
        CloudIngress -.->|Queue Q_t, Oldest Age| FastController
        
        ArrivalHistory[14-Day Azure Trace Window] -.->|Macro Trend: d*lambda/dt| MacroForecaster[Multi-Horizon Trend Forecaster<br/>Projects Demand over T_boot Horizon]
        
        FastController --> ActuationEngine[Actuation & Fleet Manager<br/>Clamped: k in [1, 18]]
        MacroForecaster --> ActuationEngine
        
        ActuationEngine -->|Booting Pipeline (T_boot)| GPUWorkers
    end
```

---

## Proposed Changes

### Component 1: Calibrated Physical Simulation Extensions (ContinuumBench Configs & Overlays)

#### [NEW] `configs/suites/macro_azure_deep_trace.yaml`
A 1,800-second (30-minute) macro-benchmark suite built directly from the 14-day production Azure Functions trace:
- Configured with `epochs: 1800`, `step_seconds: 1.0`, `min_workers: 1`.
- Supports multi-minute boot cycles across the continuous ladder:
  $$T_{\text{boot}} \in [0.5\text{s}, 1.0\text{s}, 5.0\text{s}, 15.0\text{s}, 50.0\text{s}, 100.0\text{s}, 150.0\text{s}, 200.0\text{s}, 250.0\text{s}, 300.0\text{s}]$$
- Incorporates calibrated WAN profiles (`edge_cloud_wan`: 42ms median latency, 150 Mbps bandwidth constraint, 0.2% packet drop).

#### [NEW] `configs/suites/suite_stress_realism_matrix.yaml`
Structured configuration declaring the smooth, non-impulsive delay ladder:
1. **Sub-second Snapshot Restore**: $T_{\text{boot}} = 0.5\text{s}, 1.0\text{s}$ (Firecracker SnapStart / CRIU).
2. **Container Cold Start**: $T_{\text{boot}} = 5.0\text{s}, 15.0\text{s}$ (Local cached PyTorch / CUDA context init).
3. **Medium Model Weight Pull**: $T_{\text{boot}} = 50.0\text{s}, 100.0\text{s}$ (ResNet-152, ViT-Base on cold host).
4. **Foundation Model / VLM Heavy Init**: $T_{\text{boot}} = 150.0\text{s}, 200.0\text{s}, 250.0\text{s}, 300.0\text{s}$ (Multi-GPU VLM, NCCL tensor-parallel synchronization, CUDA graph build).
All tiers strictly enforce $k_{\min} = 1$.

---

### Component 2: Network & Dynamic Batching Modeling

#### [NEW] `src/continuum_ext/realism/dynamic_batching_model.py`
Models the non-linear execution profile of GPU inference servers (Triton / vLLM):
```python
@dataclass
class TritonBatchingProfile:
    base_latency_s: float = 0.015       # T_0 (kernel launch + context)
    per_item_latency_s: float = 0.006   # beta (GEMM / forward pass scaling)
    max_batch_size: int = 16
    batch_timeout_s: float = 0.050      # max queue wait before firing

    def compute_service_rate_rps(self, batch_size: int) -> float:
        b = max(1, min(self.max_batch_size, batch_size))
        exec_time = self.base_latency_s + self.per_item_latency_s * b
        return b / exec_time
```

#### [NEW] `src/continuum_ext/realism/network_batch_link.py`
Calculates transmission latency as a function of batched payload volume and link bandwidth:
```python
def compute_wan_transfer_delay(
    batch_size: int,
    item_bytes: int = 200_000,
    base_rtt_ms: float = 42.0,
    bandwidth_mbps: float = 150.0,
    jitter_std_ms: float = 8.0,
) -> float:
    payload_mb = (batch_size * item_bytes * 8) / 1_000_000.0
    transfer_time_s = payload_mb / bandwidth_mbps
    rtt_s = max(0.005, (base_rtt_ms + np.random.normal(0, jitter_std_ms))) / 1000.0
    return rtt_s + transfer_time_s
```

---

### Component 3: Multi-Horizon Lookahead & Adaptive Edge Fallback

#### [NEW] `src/continuum_ext/controllers/multi_horizon_conformal_autoscaler.py`
Extends our evolved policy with:
1. **Multi-Horizon Lookahead ($T_{\text{lookahead}} = T_{\text{boot}}$)**:
   Predicts demand using conformal rate-of-change across the boot horizon:
   $$\hat{\lambda}_{\text{cloud}}(t + T_{\text{boot}}) = \lambda_{\text{cloud}}(t) + T_{\text{boot}} \cdot \frac{d\lambda_{\text{cloud}}}{dt}$$
2. **In-Flight Booting Accounting**:
   Explicitly credits workers in the $T_{\text{boot}}$ pipeline to eliminate panic over-provisioning:
   $$\text{target} = \max\left(1, \frac{\hat{\lambda}_{\text{cloud}}(t + T_{\text{boot}})}{\mu(B)} + \text{drain} - (\text{booting\_workers} \times 0.95)\right)$$
3. **Closed-Loop Edge Fallback Signal**:
   Emits an advisory signal back to the edge when:
   $$\text{Queue\_Delay}(t) + T_{\text{boot}} > D_{\text{SLA}}$$
   instructing the edge to degrade to local inference rather than sending poison tasks to a 300s dead-time cloud queue.

---

### Component 4: Unified Stress-Suite Runner

#### [NEW] `scripts/run_realism_gap_stress_suite.py`
Self-contained, reproducible test runner executing the complete spectrum across:
1. **Cold-Start Delay Ladder**: $[0.5\text{s}, 1.0\text{s}, 5.0\text{s}, 15.0\text{s}, 50.0\text{s}, 100.0\text{s}, 150.0\text{s}, 200.0\text{s}, 250.0\text{s}, 300.0\text{s}]$.
2. **Unified Baseline**: $k_{\min} = 1$ enforced across all runs.
3. **Controllers**: Evolved Conformal (Multi-Horizon) vs. InferLine vs. KEDA vs. HPA.
4. **Workloads**: 
   - Micro-stress triad (`suite1_spike`, `suite2_shock`, `suite3_azure`) for fast sensitivity sweeps ($T_{\text{boot}} \le 15\text{s}$).
   - Macro-horizon Azure trace ($1,800\text{s}$) for multi-minute cold starts ($T_{\text{boot}} \ge 50\text{s}$).

Outputs clean, typed JSON manifests and summary tables in `output/realism_stress_results/`.

---

## Plan B: Contingency & Recovery Architecture for Extreme Boot Latencies ($T_{\text{boot}} \ge 50\text{s}$)

To guarantee scientific rigor, prevent operational confusion, and avoid directory pollution:

### 1. Anticipated Vulnerability of Policy v3 under Multi-Minute Latencies
Policy v3 (`bbd9b1c2`) was synthesized for $T_{\text{boot}} = 1.0\text{s}$ with static sub-second parameters ($\text{DRAIN\_WINDOW\_S} = 2.08\text{s}$, hysteresis cooldown $2.2\text{s}$, and booting credit $0.95$). If evaluated directly under $T_{\text{boot}} \in [50\text{s}, 300\text{s}]$, holding $0.95 \times \text{booting\_workers}$ for several minutes could suppress timely scaling, creating queue buildup.

### 2. The Four-Tier Plan B Defense-in-Depth
If Policy v3 exhibits tail latency degradation or deadline misses as $T_{\text{boot}} \to 300\text{s}$, the system immediately activates Plan B:
1. **Tier B.1: Parametric Horizon Scaling (`src/continuum_ext/controllers/plan_b_adaptive_conformal.py`)**:
   Dynamically scales control parameters with operational $T_{\text{boot}}$:
   $$\tau_{\text{drain}}(T_{\text{boot}}) = \max(2.08, \gamma \cdot \sqrt{T_{\text{boot}}})$$
   $$\text{cooldown}(T_{\text{boot}}) = \max(2.2, \delta \cdot T_{\text{boot}})$$
   Discounts booting workers by remaining elapsed boot progress rather than a static 0.95 constant factor.
2. **Tier B.2: Second-Order Conformal Acceleration**:
   Adds arrival acceleration $\frac{d^2\lambda_{\text{cloud}}}{dt^2}$ to the demand lookahead to trigger scaling before exponential surges peak:
   $$\hat{\lambda}_{\text{cloud}}(t + T_{\text{boot}}) = \lambda_{\text{cloud}}(t) + T_{\text{boot}} \frac{d\lambda_{\text{cloud}}}{dt} + \frac{1}{2} T_{\text{boot}}^2 \frac{d^2\lambda_{\text{cloud}}}{dt^2}$$
3. **Tier B.3: Closed-Loop Edge Fallback (The Hard SLA Safety Net)**:
   When cloud queue wait plus boot lag exceeds the deadline budget ($\frac{Q(t)}{k \mu} + T_{\text{boot}} > D_{\text{SLA}}$), the edge router closes the cloud gate and serves ambiguous tasks locally using the edge student model with graceful confidence degradation. This mathematically guarantees **zero SLA violations** regardless of boot latency magnitude.
4. **Tier B.4: Branch-Isolated Evolutionary Re-adaptation (Branch `v4-evolution`)**:
   If automated genetic re-synthesis is required, OpenEvolve executes strictly on the isolated branch `v4-evolution` (`b32438c`) using the macro-realism evaluator. All candidate variants and logs are contained within `output/v4_evolution_runs/`. The `main` branch remains clean and untouched.

### 3. Strict Workspace Governance ("Anti-Mess" Directive)
To prevent directory pollution and messy refactoring loops:
- No ad-hoc, untracked scripts in the root directory.
- All Plan B code is centralized in [`src/continuum_ext/controllers/plan_b_adaptive_conformal.py`](file:///home/vaibo/edgecompute/src/continuum_ext/controllers/plan_b_adaptive_conformal.py).
- All Plan B evaluation outputs are routed to [`output/realism_stress_results/plan_b/`](file:///home/vaibo/edgecompute/output/realism_stress_results/plan_b/) with typed JSON manifests.
- The certified Step 8 dataset in `output/step8_multiseed_runs_v3/` remains immutable.

---

## Verification Plan

### Automated Tests
1. **Unit Test - Triton Batching & Network Models**:
   ```bash
   ./.venv/bin/pytest tests/test_realism_extensions.py -v
   ```
2. **Smoke Test - Multi-Scale Boot Sweep (Fast Sub-run)**:
   Run 3 delay points ($0.5\text{s}$, $5.0\text{s}$, $50.0\text{s}$) on `suite1_spike` with seed 42 to verify telemetry collection, $k \ge 1$ enforcement, and zero crashes:
   ```bash
   ./.venv/bin/python scripts/run_realism_gap_stress_suite.py --smoke --seeds 42
   ```
3. **Macro-Horizon Execution Check**:
   Run 300 epochs of `macro_azure_deep_trace.yaml` to verify the 14-day Azure trace slice loads smoothly:
   ```bash
   ./.venv/bin/python -m continuum_bench.cli run --config configs/suites/macro_azure_deep_trace.yaml --controller evolved_conformal --seed 42 --out output/test_macro
   ```

### Manual Verification
- Review resulting Pareto curves ($T_{\text{boot}}$ vs. Misses & Cost) to verify that the smooth delay progression yields smooth, monotonic curves without erratic jumps.
- Verify that $k \ge 1$ is strictly maintained across all controllers and that Conformal Multi-Horizon lookahead successfully mitigates tail latency even as $T_{\text{boot}}$ scales up to 300s.
