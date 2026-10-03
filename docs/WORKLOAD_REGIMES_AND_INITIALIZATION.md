# Workload Regimes & Simulation Initialization Specification

**Document Role**: Authoritative reference for multi-tier workload regime patterns, infrastructure initialization across IoT, Edge, and Cloud tiers, and mathematical/physical rationale across all 3 benchmarking suites.  
**Associated Configs**: [`configs/suites/`](file:///home/vaibo/edgecompute/configs/suites/)  
**Generator Implementation**: [`src/continuum_ext/workload/conformal_workloads.py`](file:///home/vaibo/edgecompute/src/continuum_ext/workload/conformal_workloads.py)  
**Governance Compliance**: Adheres strictly to [`AGENTS.md`](file:///home/vaibo/edgecompute/AGENTS.md) Rule #2 (Decoupled Linkage) and Rule #6 (Dataset Integrity).

---

## 1. Executive Summary & Multi-Tier Initialization Philosophy

In distributed continuum computing, autoscaling performance is heavily influenced by boundary initialization across **all physical tiers**:
1. **IoT Sensor Tier (`CameraSource`)**: Controls ingress generation, frame arrival rate $\lambda(t)$, and empirical fast-path sampling $P(\text{high}) = fp(t)$. Starting a cold regime requires the sensor to emit $\lambda=0$ to test zero-traffic quiescence.
2. **Edge Compute Tier (`EdgePreprocess`, `EdgeInference`, `Sink`)**: Fixed singleton pipeline pinned to Edge compute nodes. Must remain active and ready to triage incoming frames immediately, providing guaranteed low-latency local execution ($~0.25\text{s}$) for singleton prediction sets without warm-up lag.
3. **Cloud GPU Tier (`CloudRefineWorker`)**: Dynamically scaled GPU worker pool. Boundary conditions (`initial_workers`, `min_workers`) must match the physical test requirements:
   - **Cold-Start Regimes**: Must start with **0 instances** and **min_workers = 0**; pre-warming masks container boot latency, image pull overhead, and cold-start queue accumulation.
   - **Drain / Scale-to-Zero Regimes**: Enforcing `min_workers > 0` prevents measuring idle worker reclamation and zombie replica waste.
   - **Steady-State Regimes**: Must start with **equilibrium instances** (e.g. 4 workers) to eliminate artificial initialization transients from corrupting steady-state drift measurements.

---

## 2. Comprehensive Multi-Tier Infrastructure Initialization Matrix

| Regime Key | Workload Name | IoT Tier Instances (`CameraSource`) | Edge Tier Instances (`Preprocess`, `Inference`, `Sink`) | Cloud GPU Workers (`initial` / `min` / `max`) | Scientific & Physical Reasoning across All Tiers |
|:---|:---|:---|:---|:---:|:---|
| `suite1_flat` | **Steady-State Baseline** | **4 IoT Nodes** (`IoT_0..3`)<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Emits flat $\lambda = 100\text{ RPS}$ ($fp = 0.50$ fixed) | **8 Edge Nodes** (`Edge_0..7`)<br/>• `EdgePreprocess` (4 CPU, 8GB)<br/>• `EdgeInference` (6 CPU, 12GB)<br/>• `Sink` (1 CPU, 2GB)<br/>• Pinned to `Edge_0` (11/24 CPU, 45.8% util) | **4 / 1 / 12**<br/>Placed on `Cloud_0..1` (2 nodes) | **Warm equilibrium across all tiers**: Edge absorbs $50\text{ RPS}$ fast-path; 4 Cloud workers absorb $50\text{ RPS}$ slow-path from epoch 0. Zero startup transients on any tier to measure pure steady-state drift and cost. |
| `suite1_spike` | **Volume Spike** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Base $60\text{ RPS} \to 300\text{ RPS}$ instantaneous spike at epoch 50 | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• Edge ingress buffer (256 MB) absorbs micro-bursts during WAN queueing | **2 / 1 / 12**<br/>Sized for $30\text{ RPS}$ base slow-path | **Sized for base rate**: Edge handles $30\text{ RPS}$ base ($150\text{ RPS}$ peak). Tests burst detection, WAN link ingress buffering, and reactive cloud spin-up to 10+ workers without warm masking. |
| `suite1_burst` | **Bursty MMPP Traffic** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Markov switching: Low $40 \leftrightarrow$ High $200\text{ RPS}$ | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• Store-forward buffer with TTL=90s | **2 / 1 / 12**<br/>Sized for $20\text{ RPS}$ low slow-path | **Tests stochastic surge absorption**: Edge continuously triages $50\%$ fast-path. Tests whether cloud controller absorbs stochastic heavy-tailed bursts without flapping or queue starvation. |
| `suite1_ramp` | **Continuous Volume Ramp** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Linear ramp $20 \to 160\text{ RPS}$ over 100 epochs | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• Edge utilization ramps smoothly $10\% \to 75\%$ | **1 / 1 / 12**<br/>Starts at 1 worker ($10\text{ RPS}$ slow-path onset) | **Ramp onset tracking**: Both Edge and Cloud start at minimal footprint and track continuous derivatives without lag-induced buffer accumulation. |
| `suite1_zero_begin` | **Cold Start (Scale-from-Zero)** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Epochs 0–3: $\lambda = 0\text{ RPS}$ (zero emission)<br/>• Epoch 4+: Ramps to $120\text{ RPS}$ | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• Always-on listener (ready for first arrival)<br/>• Zero CPU load while $\lambda = 0$ | **0 / 0 / 12**<br/>**Strict zero instances** on Cloud GPU tier | **Strict cold boot**: Measures exact container spin-up delay ($startup\_delay\_s = 1.0\text{s}$) and queue pileup on Cloud when the first offloaded request crosses the WAN link. |
| `suite1_zero_terminal` | **Scale-to-Zero (Reclamation)** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• $120\text{ RPS}$ plateau $\to 0\text{ RPS}$ drain (epochs 80–150) | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• Drains local queues to 0 items | **4 / 0 / 12**<br/>Scales down to **0 workers** upon drain | **Idle reclamation & scale-to-zero**: Evaluates complete deallocation of cloud GPU resources down to $0$ instances once IoT emission ceases. |
| `suite2_shock` | **Steady RPS + Complexity Shock** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Flat $\lambda = 100\text{ RPS}$ (silent volume channel) | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• Inference detects OOD drop: $fp = 0.70 \to 0.20$ at ep 60 | **2 / 1 / 12**<br/>Sized for $30\text{ RPS}$ pre-shock slow-path | **Isolates complexity channel**: Volume is silent across IoT/Edge. Edge triage streams $fp \downarrow$ to controller; tests proactive preemption before cloud backlog forms. |
| `suite2_recovery` | **Complexity Shock + Recovery** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Flat $\lambda = 100\text{ RPS}$ | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• $fp$ drops to $0.20$ at ep 40, recovers to $0.70$ over 60 epochs | **2 / 1 / 12**<br/>Sized for pre-shock baseline | **Hysteresis avoidance**: Evaluates safe scale-down back to 2 workers as Edge inference signals recovering model confidence. |
| `suite2_opposing1` | **Opposing Shift 1 (Vol UP, fp DOWN)** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Volume ramps UP: $60 \to 160\text{ RPS}$ | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• $fp$ ramps DOWN: $0.70 \to 0.20$ | **2 / 1 / 12**<br/>Sized for $18\text{ RPS}$ pre-shift slow-path | **Anti-symmetric demand**: Slow-path jumps $7.1\times$ ($18 \to 128\text{ RPS}$). Edge utilization remains moderate while cloud GPU tier must scale to 8–10 workers. |
| `suite2_opposing2` | **Opposing Shift 2 (Vol DOWN, fp UP)** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Volume ramps DOWN: $160 \to 60\text{ RPS}$ | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• $fp$ ramps UP: $0.20 \to 0.70$ | **4 / 1 / 12**<br/>Sized warm for $128\text{ RPS}$ slow-path origin | **Accelerated reclamation**: True GPU demand drops by $86\%$ ($128 \to 18\text{ RPS}$). Edge signals fast recovery, enabling rapid cloud worker spin-down. |
| `suite2_storm` | **Coupled Storm Surge** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Base $60\text{ RPS} \to$ Spikes to $180\text{ RPS}$ during storm | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• Severe OOD storm: $fp$ drops $0.65 \to 0.15$ | **2 / 1 / 12**<br/>Sized for $21\text{ RPS}$ fair-weather load | **Worst-case multiplicative surge**: Slow-path demand explodes $7.3\times$ ($21 \to 153\text{ RPS}$). Stresses peak cluster capacity across all 6 Cloud GPU nodes. |
| `suite3_azure` | **Rolling Azure Macrobenchmark** | **4 IoT Nodes**<br/>• 1 active `CameraSource` on `IoT_0`<br/>• Azure 2019 trace ($2.0\times$ in-memory replay scaling) | **8 Edge Nodes**<br/>• Preprocess, Inference, Sink on `Edge_0`<br/>• 24h diurnal solar drift ($fp: 0.65 \leftrightarrow 0.20$) + storm bursts | **2 / 0 / 12**<br/>`min_workers=0` for nocturnal troughs | **Production macrobenchmark**: Edge tracks diurnal solar drift. Setting `min_workers=0` validates scale-to-zero and energy savings during nocturnal invocation lulls. |

---

## 3. Physical Continuum Infrastructure Topology

All 12 suite configurations share the unified, scaled multi-tier physical infrastructure:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CONTINUUM INFRASTRUCTURE TIERS                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. IoT Sensor Tier: 4 Nodes (IoT_0 .. IoT_3)                                           │
│    • Resources per node: 4.0 CPU, 8.0 GB RAM, 64.0 GB Storage                          │
│    • Deployed Service: CameraSource instance placed on IoT_0 (2.0 CPU, 4.0 GB RAM)     │
│    • Role: Hosts CameraSource generator (pinned via placement_layers: ['iot'])         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Edge Compute Tier: 8 Nodes (Edge_0 .. Edge_7)                                       │
│    • Resources per node: 24.0 CPU, 64.0 GB RAM, 2000.0 GB Storage                      │
│    • Deployed Services on Edge_0:                                                      │
│      - EdgePreprocess: 4.0 CPU, 8.0 GB RAM (0.10s frame normalization)                 │
│      - EdgeInference:  6.0 CPU, 12.0 GB RAM (0.15s TinyViT ResNet-152 ONNX triage)     │
│      - Sink:           1.0 CPU, 2.0 GB RAM (15.0s SLO deadline)                        │
│    • Aggregate Edge_0 Utilization: 11.0 / 24.0 CPU (45.8%), 22.0 / 64.0 GB RAM (34.4%)│
│    • Headroom: 7 idle nodes (Edge_1 .. Edge_7) available for edge scale-out            │
│    • Role: Pinned via placement_layers: ['edge']                                       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. Cloud GPU Tier: 6 Nodes (Cloud_0 .. Cloud_5)                                        │
│    • Resources per node: 24.0 CPU, 48.0 GB RAM, 1000.0 GB Storage                     │
│    • Worker Spec: CloudRefineWorker requires 8.0 CPU, 16.0 GB RAM                      │
│    • Maximum Workers per Cloud Node: 24.0 / 8.0 = 3 workers                            │
│    • Dynamic Distribution: 12 workers distribute across 4 separate physical nodes      │
│      (e.g., Cloud_0: 3, Cloud_1: 3, Cloud_2: 3, Cloud_3: 3)                            │
│    • Role: Pinned via placement_layers: ['cloud']                                      │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. WAN Transit Link: Edge_0 -> Cloud_0                                                 │
│    • Network Profile: Latency = 25.0 ms, Bandwidth = 1000.0 Mbps                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Architectural Verification & Reproducibility Checklist

To reproduce any suite with its exact regime initialization:

```bash
# 1. Cold Start Benchmark (Suite 1-E: starts at w=0, min=0)
./.venv/bin/python -m continuum_bench.cli run \
  --config configs/suites/suite1_zero_begin.yaml \
  --controller hpa \
  --seed 42 \
  --out runs/cold_start_hpa/

# 2. Scale-to-Zero Benchmark (Suite 1-F: starts at w=4, scales to w=0)
./.venv/bin/python -m continuum_bench.cli run \
  --config configs/suites/suite1_zero_terminal.yaml \
  --controller inferline \
  --seed 42 \
  --out runs/scale_to_zero_inferline/

# 3. Complexity Shock Benchmark (Suite 2-A: sudden OOD drop at constant volume)
./.venv/bin/python -m continuum_bench.cli run \
  --config configs/suites/suite2_shock.yaml \
  --controller conformal \
  --seed 42 \
  --out runs/shock_conformal/
```

Every configuration is guaranteed deterministic and decoupled per [`AGENTS.md`](file:///home/vaibo/edgecompute/AGENTS.md).
