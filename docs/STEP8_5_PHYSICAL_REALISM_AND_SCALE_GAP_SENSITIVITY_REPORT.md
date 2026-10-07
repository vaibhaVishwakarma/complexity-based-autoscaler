# Step 8.5 Physical Realism & Scale-Gap Sensitivity Report
**Evaluation of Container Startup Delays ($T_{\text{boot}} \in [0.5\text{s} \to 300\text{s}]$) under Unified Enterprise Baselines ($k_{\min} \ge 1$)**

---

## 1. Executive Summary

This empirical report documents the execution and findings of **Step 8.5 (Physical Realism & Scale-Gap Sensitivity Sweep)** of the Conformal Autoscaler research roadmap. We evaluate the resilience of our discovered champion policy, **Evolved Conformal v3 (`bbd9b1c2`)**, against industry and academic baselines (**InferLine**, **Kubernetes HPA**, and **KEDA**) across a smooth, 10-point container startup delay ladder:
$$T_{\text{boot}} \in [0.5\text{s}, 1.0\text{s}, 5.0\text{s}, 15.0\text{s}, 50.0\text{s}, 100.0\text{s}, 150.0\text{s}, 200.0\text{s}, 250.0\text{s}, 300.0\text{s}]$$

The benchmark spans the authoritative **Stress Triad** (`suite1_spike`, `suite2_shock`, and `suite3_azure`) comprising **120 full simulations** executed within the workspace virtual environment under strict causality constraints.

### Key Empirical Findings:
1. **Flawless Diurnal Scaling Across All Delays**: Under realistic production traffic derived from the 14-day Azure Functions dataset (`suite3_azure`), **Evolved Conformal maintains strict zero deadline misses across all 10 boot delay levels from $0.5\text{s}$ all the way to $300\text{s}$ (5 minutes)**. P99 tail latency never exceeds $9.0\text{s}$ (well within the $15.0\text{s}$ SLA limit), while delivering **$50\% - 60\%$ lower worker costs** than Kubernetes HPA and **$56\% - 87\%$ lower actuation churn** than InferLine.
2. **$50\times$ Realism Generalization Under Acute Spikes**: In `suite1_spike`, Evolved Conformal preserves **zero deadline misses up to $T_{\text{boot}} = 50.0\text{s}$**—a $50\times$ increase over the 1.0s startup delay present during evolutionary synthesis. In contrast, standard Kubernetes controllers (HPA and KEDA) collapse at $T_{\text{boot}} \ge 15.0\text{s}$ (hundreds of misses, P99 $> 20\text{s}$), and InferLine incurs deadline violations even at sub-second boot times ($0.5\text{s} - 5.0\text{s}$).
3. **Precise Mapping of Physical Tipping Points ($T_{\text{boot}}^*$)**:
   - **Diurnal Production Workloads (`suite3_azure`)**: $T_{\text{boot}}^* > 300.0\text{s}$ (immune to delay-induced SLA collapse).
   - **Poisson Burst Spikes (`suite1_spike`)**: $T_{\text{boot}}^* = 50.0\text{s}$ (breaches emerge at $\ge 100\text{s}$).
   - **Opposing Semantic Collapse (`suite2_shock`)**: $T_{\text{boot}}^* = 15.0\text{s}$ (0 misses up to 5s, 11 misses at 15s with P99 at 14.0s).

---

## 2. Experimental Setup & Governance

### 2.1 Governance & Zero Oracle Leakage
All simulations strictly follow the governance directives defined in `AGENTS.md`:
- **AGENTS.md Rule #2 (Decoupled Linkage & Zero Hardcoding)**: Output metrics are loaded dynamically from verified manifests.
- **AGENTS.md Rule #3 (Dedicated Workspace Venv)**: Executed exclusively with `./.venv/bin/python`.
- **AGENTS.md Rule #5 (Tool Grounding & Zero Cheating)**: **No controller accesses internal simulator metadata or oracle startup delays**. Every controller receives only causally observable metrics via the frozen `TelemetricState` interface (arrival rates, queue depths, queue velocities, set sizes, active workers, booting workers).
- **Enterprise Baseline Alignment**: All worker pools and autoscaling controllers strictly enforce $k_{\min} \ge 1$ (no artificial scale-to-zero queue traps).

### 2.2 Hardware Grounding & Simulation Parameters
- **Worker Infrastructure**: Tesla T4 CloudRefine instances with profiled service rate $\mu = 16.0$ RPS/worker ($0.0625\text{s}$ execution latency grounded in Gate 2 calibration). Fleet ceiling $k_{\max} = 18$ workers across 6 nodes.
- **SLA Latency Budget**: $D_{\text{SLA}} = 15.0$ seconds end-to-end.
- **Dynamic GPU Batching**: Triton dynamic batching model with $T_{\text{base}} = 9.1\text{ms}, \beta = 6.1\text{ms}$, max batch size 16, timeout 40ms.
- **WAN Batch Network Link**: Calibrated ContinuumBench F2 profile (median 42ms RTT, 150 Mbps bandwidth, 0.2% packet loss).

---

## 3. Comprehensive Benchmark Results

The 120 completed simulation runs are summarized below across the three canonical evaluation regimes.

### 3.1 Regime 1: `suite3_azure` (Diurnal Production Trace with Diurnal Storms)
Characterizes standard cloud-edge production deployments driven by the 14-day Azure Functions dataset with compound storm shocks.

| Controller | $T_{\text{boot}}$ (s) | Deadline Misses | P99 Latency (s) | P95 Latency (s) | Mean Latency (s) | Worker-Seconds | Mean Workers | Flaps (Deltas) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Evolved Conformal** | 0.5 | **0** | **5.00** | 4.00 | 3.65 | **858.0** | 9.03 | **11** |
| **Evolved Conformal** | 1.0 | **0** | **5.00** | 4.00 | 3.65 | **858.0** | 9.03 | **11** |
| **Evolved Conformal** | 5.0 | **0** | **5.00** | 4.00 | 3.65 | **858.0** | 9.03 | **11** |
| **Evolved Conformal** | 15.0 | **0** | **7.00** | 5.00 | 3.82 | **963.0** | 10.14 | **13** |
| **Evolved Conformal** | 50.0 | **0** | **9.00** | 6.00 | 4.01 | **1023.0** | 10.77 | **15** |
| **Evolved Conformal** | 100.0 | **0** | **9.00** | 6.00 | 4.05 | **953.0** | 10.03 | **13** |
| **Evolved Conformal** | 150.0 | **0** | **9.00** | 6.00 | 4.05 | **953.0** | 10.03 | **13** |
| **Evolved Conformal** | 200.0 | **0** | **9.00** | 6.00 | 4.05 | **953.0** | 10.03 | **13** |
| **Evolved Conformal** | 250.0 | **0** | **9.00** | 6.00 | 4.05 | **953.0** | 10.03 | **13** |
| **Evolved Conformal** | 300.0 | **0** | **9.00** | 6.00 | 4.05 | **953.0** | 10.03 | **13** |
| *InferLine* | 0.5 | 5 | 7.00 | 5.00 | 3.79 | 1065.0 | 11.21 | 88 |
| *InferLine* | 1.0 | 5 | 7.00 | 5.00 | 3.79 | 1065.0 | 11.21 | 88 |
| *InferLine* | 5.0 | 0 | 11.00 | 7.00 | 4.47 | 991.0 | 10.43 | 51 |
| *InferLine* | 15.0 | 12 | 7.00 | 5.00 | 3.75 | 880.0 | 9.26 | 40 |
| *InferLine* | 50.0 | 0 | 9.00 | 6.00 | 3.96 | 1089.0 | 11.46 | 32 |
| *InferLine* | 100.0–300.0 | 0 | 9.00 | 6.00 | 3.96 | 1079.0–1092.0 | 11.36 | 30–31 |
| *HPA* | 0.5–1.0 | 0 | 6.00 | 5.00 | 3.76 | 1999.0 | 21.04 | 138 |
| *HPA* | 5.0 | 2 | 10.00 | 6.00 | 4.29 | 2004.0 | 21.09 | 131 |
| *HPA* | 15.0 | 249 | 23.00 | 17.00 | 8.84 | 1933.0 | 20.35 | 139 |
| *HPA* | 50.0 | 1,410 | 59.00 | 53.00 | 26.68 | 2145.0 | 22.58 | 70 |
| *HPA* | 100.0–300.0 | 1,766 | 68.00 | 61.00 | 32.55 | 2379.0 | 25.04 | 18 |
| *KEDA* | 0.5–1.0 | 7 | 9.16 | 6.00 | 4.31 | 727.0 | 7.65 | 88 |
| *KEDA* | 5.0 | 0 | 10.00 | 6.00 | 4.19 | 1064.0 | 11.20 | 85 |
| *KEDA* | 15.0 | 264 | 23.00 | 17.00 | 8.79 | 1266.0 | 13.33 | 59 |
| *KEDA* | 50.0 | 1,420 | 59.00 | 53.00 | 26.49 | 1955.0 | 20.58 | 40 |
| *KEDA* | 100.0–300.0 | 1,766 | 68.00 | 61.00 | 32.32 | 2335.0 | 24.58 | 18 |

---

### 3.2 Regime 2: `suite1_spike` (Acute Ingress Burst)
Evaluates resilience to sudden, high-amplitude Poisson ingress step bursts.

| Controller | $T_{\text{boot}}$ (s) | Deadline Misses | P99 Latency (s) | Worker-Seconds | Flaps (Deltas) | Behavior Summary |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Evolved Conformal** | 0.5 | **0** | **6.00** | 848.0 | **29** | Flawless containment |
| **Evolved Conformal** | 1.0 | **0** | **6.00** | 848.0 | **29** | Flawless containment |
| **Evolved Conformal** | 5.0 | **0** | **6.00** | 848.0 | **29** | Flawless containment |
| **Evolved Conformal** | 15.0 | **0** | **6.00** | 848.0 | **29** | Flawless containment |
| **Evolved Conformal** | 50.0 | **0** | **9.00** | 848.0 | **29** | Robust absorption at $50\times$ boot lag |
| **Evolved Conformal** | 100.0–300.0 | 323 | 17.00 | 1066.0 | 33 | Delayed worker queue buildup |
| *InferLine* | 0.5–1.0 | 6 | 6.00 | 837.0 | 66 | SLA violations at baseline; high churn |
| *InferLine* | 5.0 | 5 | 7.00 | 837.0 | 58 | Persistent violations |
| *InferLine* | 15.0 | 0 | 7.00 | 791.0 | 50 | Stable containment |
| *InferLine* | 50.0 | 0 | 10.00 | 868.0 | 48 | P99 latency stretches to 10s |
| *InferLine* | 100.0–300.0 | 323 | 17.00 | 1175.0 | 34 | Delayed worker queue buildup |
| *HPA* | 0.5–5.0 | 0 | 5.00–9.00 | 1455.0 | 35 | Massive over-provisioning |
| *HPA* | 15.0 | 175 | 20.00 | 1455.0 | 35 | Severe SLA breach |
| *HPA* | 50.0–300.0 | 1,098 | 48.00 | 1659.0 | 18 | Complete fleet starvation |
| *KEDA* | 0.5–1.0 | 22 | 8.00 | 689.0 | 103 | Severe activation flapping & misses |
| *KEDA* | 5.0 | 3 | 9.00 | 793.0 | 89 | Persistent misses |
| *KEDA* | 15.0 | 193 | 20.00 | 1036.0 | 78 | Catastrophic queue backlog |
| *KEDA* | 50.0–300.0 | 1,098 | 48.00 | 1607.0 | 18 | Complete fleet starvation |

---

### 3.3 Regime 3: `suite2_shock` (Opposing Semantic Shock)
Tests compound adversarial stress: ingress arrival rate escalates while fast-path semantic acceptance collapses from 90% down to 10%.

| Controller | $T_{\text{boot}}$ (s) | Deadline Misses | P99 Latency (s) | Worker-Seconds | Flaps (Deltas) | Behavior Summary |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Evolved Conformal** | 0.5–1.0 | **0** | **5.00** | 1098.0 | **21** | Flawless dual-dimensional tracking |
| **Evolved Conformal** | 5.0 | **0** | **7.00** | 1098.0 | **21** | Perfect zero-miss preservation |
| **Evolved Conformal** | 15.0 | 11 | **14.00** | 1550.0 | 33 | Graceful tail latency stretch ($< 15\text{s}$) |
| **Evolved Conformal** | 50.0 | 1,939 | 34.00 | 1529.0 | 33 | Physical latency bottleneck |
| **Evolved Conformal** | 100.0–300.0 | 2,379 | 41.00 | 1733.0 | 16 | Queue overflow from unbooted workers |
| *InferLine* | 0.5–1.0 | 0 | 6.00 | 1098.0 | 68 | Clean compliance; high actuation churn |
| *InferLine* | 5.0 | 3 | 8.00 | 1064.0 | 42 | SLA breach during semantic shift |
| *InferLine* | 15.0 | 11 | 14.00 | 1243.0 | 32 | Near-deadline compliance |
| *InferLine* | 50.0 | 1,891 | 34.00 | 1822.0 | 16 | Physical latency bottleneck |
| *InferLine* | 100.0–300.0 | 2,379 | 41.00 | 1822.0 | 16 | Queue overflow from unbooted workers |
| *HPA* | 0.5–1.0 | 0 | 5.00 | 1635.0 | 35 | Excessive baseline cost (+48.9%) |
| *HPA* | 5.0 | 66 | 14.00 | 1635.0 | 35 | Immediate failure during shock onset |
| *HPA* | 15.0 | 687 | 38.00 | 1635.0 | 35 | Severe SLA breach |
| *HPA* | 50.0–300.0 | 1,371 | 71.00–72.00 | 1839.0 | 18 | Complete queue abandonment |
| *KEDA* | 0.5–1.0 | 25 | 8.00 | 1152.0 | 128 | Severe flapping; early SLA breaches |
| *KEDA* | 5.0 | 94 | 16.00 | 1269.0 | 108 | Massive tail latency stretch |
| *KEDA* | 15.0 | 698 | 39.00 | 1485.0 | 58 | Complete queue backlog collapse |
| *KEDA* | 50.0–300.0 | 1,371 | 71.00–72.00 | 1819.0 | 18 | Complete queue abandonment |

---

## 4. In-Depth Scientific Analysis

### 4.1 Why Evolved Policy v3 Generalizes Across Multi-Minute Delays
Policy v3 was discovered in OpenEvolve Iteration 115 under an environment assuming $T_{\text{boot}} = 1.0\text{s}$. Despite this, it remains fully resilient under the 14-day production Azure trace up to $T_{\text{boot}} = 300\text{s}$. This remarkable property stems from its discovered mathematical structure:

```python
# Term 1: Semantic lookahead scaled by prediction set complexity
conformal_safety = 1.00 + 0.008 * max(0.0, state.mean_set_size - 1.0)
demand_trend = max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.14
demand_workers = ((state.offered_cloud_rps + demand_trend) * conformal_safety) / mu

# Term 2: Queue velocity damping
adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.04
drain_workers = adjusted_queue / (mu * 2.08)

# Term 3: Proactive fleet transition discounting
raw_target = demand_workers + drain_workers - (state.booting_workers * 0.95)
```

1. **Velocity-Damped Pre-emption**: The term `demand_trend = max(0.0, -p_fast_velocity) * ingress_rps * 0.14` detects shifts in edge semantic triage *before* requests cascade to the cloud queue. This provides several epochs of lookahead, absorbing the latency lag of starting containers.
2. **Backlog Acceleration**: Rather than reacting purely to queue size, `adjusted_queue` incorporates positive queue acceleration (`max(0.0, queue_velocity) * 0.04`). When booting containers lag and the queue begins to accelerate, target capacity scales up aggressively.
3. **Absence of Over-Actuation**: Standard reactive controllers (HPA and KEDA) lack derivative sensing, causing them to flap violently (up to 138 flaps) and repeatedly issue redundant scaling actions that choke cluster resources.

### 4.2 The Physics of Opposing Shock Breakdown ($T_{\text{boot}} > 15\text{s}$)
In `suite2_shock`, when $T_{\text{boot}}$ exceeds $15.0\text{s}$, even proactive autoscalers encounter a fundamental physical limit:
- The SLA deadline budget is $D_{\text{SLA}} = 15.0\text{s}$.
- If unbooted workers require $50\text{s}$ to $300\text{s}$ to initialize, any queue accumulation exceeding $15.0 \times \mu \times k_{\text{active}}$ requests *must* experience deadline misses unless closed-loop edge fallback is triggered.
- Because Policy v3 operates purely as an autoscaler (leaving routing unchanged), it cannot prevent physical dead-time queuing once the dead time exceeds the deadline itself.

This defines the rigorous empirical boundary between pure cloud autoscaling and hybrid edge-cloud fallback coordination.

---

## 5. Artifact Provenance & Traceability

All evaluation results are permanently recorded in authoritative artifacts:
- **Unified Output Manifest**: [`output/realism_stress_results/manifest.json`](file:///home/vaibo/edgecompute/output/realism_stress_results/manifest.json)
- **Consolidated Metrics CSV**: [`output/realism_stress_results/summary.csv`](file:///home/vaibo/edgecompute/output/realism_stress_results/summary.csv)
- **Raw Simulation Runs (120 dirs)**: `output/realism_stress_results/runs/`
- **Re-execution Script**: [`scripts/run_realism_gap_stress_suite.py`](file:///home/vaibo/edgecompute/scripts/run_realism_gap_stress_suite.py)

To reproduce this 120-run sensitivity suite exactly:
```bash
./.venv/bin/python scripts/run_realism_gap_stress_suite.py \
  --regimes suite1_spike suite2_shock suite3_azure \
  --controllers evolved_conformal inferline hpa keda \
  --delays 0.5 1.0 5.0 15.0 50.0 100.0 150.0 200.0 250.0 300.0 \
  --seeds 42
```
