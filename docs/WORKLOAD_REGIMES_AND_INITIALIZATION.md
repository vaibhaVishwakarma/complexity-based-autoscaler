# Workload Regimes & Simulation Initialization Specification

**Document Role**: Authoritative reference for workload regime patterns, infrastructure initialization, and mathematical rationale across all 3 benchmarking suites.  
**Associated Configs**: [`configs/suites/`](file:///home/vaibo/edgecompute/configs/suites/)  
**Generator Implementation**: [`src/continuum_ext/workload/conformal_workloads.py`](file:///home/vaibo/edgecompute/src/continuum_ext/workload/conformal_workloads.py)  
**Governance Compliance**: Adheres strictly to [`AGENTS.md`](file:///home/vaibo/edgecompute/AGENTS.md) Rule #2 (Decoupled Linkage) and Rule #6 (Dataset Integrity).

---

## 1. Executive Summary & Initialization Philosophy

In distributed continuum computing, autoscaling performance is heavily influenced by boundary initialization:
1. **Cold-Start Regimes**: Starting a simulation with pre-allocated warm replicas artificially masks container boot latency, image pull overhead, and cold-start queue accumulation.
2. **Drain / Scale-to-Zero Regimes**: Enforcing `min_workers > 0` prevents measuring idle worker reclamation and zombie replica waste.
3. **Steady-State Regimes**: Starting with 0 or 1 worker introduces artificial initialization transients that corrupt equilibrium measurements.

To ensure benchmark reproducibility and scientific validity, every regime is assigned an explicit, principled initialization profile matching its physical workload pattern.

---

## 2. Complete Regime Pattern & Infrastructure Initialization Matrix

| Regime Key | Workload Name | Volume Pattern $\lambda(t)$ | Complexity Pattern $fp(t)$ | Initial Replicas (`initial_workers`) | Minimum Floor (`min_workers`) | Maximum Ceiling (`max_workers`) | Scientific & Engineering Reasoning |
|:---|:---|:---|:---|:---:|:---:|:---:|:---|
| `suite1_flat` | **Steady-State Baseline** | Constant flat $\lambda = 100\text{ RPS}$ | Fixed $fp = 0.50$ | **4** | **1** | **12** | **Equilibrium start**: Slow-path load is $50\text{ RPS}$. 4 workers provide steady-state equilibrium from epoch 0, eliminating startup transients to measure pure steady-state drift and cost. |
| `suite1_spike` | **Volume Spike** | Base $60\text{ RPS}$, instantaneous $5\times$ spike to $300\text{ RPS}$ for 3 epochs | Fixed $fp = 0.50$ | **2** | **1** | **12** | **Sized for base rate**: Slow-path base is $30\text{ RPS}$ ($2$ workers). Tests burst detection latency, scale-out speed, and buffer protection when traffic suddenly multiplies by 5× without pre-warning. |
| `suite1_burst` | **Bursty MMPP Traffic** | Markov-modulated Poisson process: Low $40\text{ RPS} \leftrightarrow$ High $200\text{ RPS}$ | Fixed $fp = 0.50$ | **2** | **1** | **12** | **Sized for low state**: Slow-path low is $20\text{ RPS}$. Tests whether the controller can absorb stochastic, heavy-tailed bursts without flapping prematurely or starving the queue during extended bursts. |
| `suite1_ramp` | **Continuous Volume Ramp** | Linear acceleration $20 \to 160\text{ RPS}$ over 100 epochs | Fixed $fp = 0.50$ | **1** | **1** | **12** | **Sized for ramp onset**: Slow-path onset is $10\text{ RPS}$. Tests the controller's ability to track a continuous derivative without lag-induced backlog or aggressive over-shooting. |
| `suite1_zero_begin` | **Cold Start (Scale-from-Zero)** | Starts at $\lambda = 0\text{ RPS}$, holds for 4 epochs, then ramps to $120\text{ RPS}$ | Fixed $fp = 0.50$ | **0** | **0** | **12** | **Strict cold boot**: Zero initial instances and zero minimum floor. Verifies zero idle cost while load is zero, and measures exact latency and queue pileup during container startup delay ($1.0\text{s}$). |
| `suite1_zero_terminal` | **Scale-to-Zero (Reclamation)** | Starts at $120\text{ RPS}$ plateau, then ramps down to $0\text{ RPS}$ from epoch 80 to 150 | Fixed $fp = 0.50$ | **4** | **0** | **12** | **Tests idle spin-down**: Starts warm for the $120\text{ RPS}$ plateau ($60\text{ RPS}$ slow-path). Setting `min_workers=0` evaluates idle-worker reclamation, penalizing controllers that retain zombie replicas after load drains. |
| `suite2_shock` | **Steady RPS + Complexity Shock** | Constant flat $\lambda = 100\text{ RPS}$ (silent volume) | Sudden OOD drop at epoch 60: $0.70 \to 0.20$ | **2** | **1** | **12** | **Isolates complexity channel**: Sized for pre-shock load ($100 \times 0.30 = 30\text{ RPS}$). Volume is silent ($\lambda=100$). Tests whether conformal telemetry preemptively scales before queue backlog forms, exposing the queue-lag failure of baselines. |
| `suite2_recovery` | **Complexity Shock + Recovery** | Constant flat $\lambda = 100\text{ RPS}$ | Drops to $0.20$ at epoch 40, linearly recovers to $0.70$ over 60 epochs | **2** | **1** | **12** | **Tests recovery hysteresis**: Sized for nominal load. Evaluates scale-up during shock, and tests fast, safe scale-down without hysteresis or premature deallocation as the model returns to high confidence. |
| `suite2_opposing1` | **Opposing Shift 1 (Vol UP, fp DOWN)** | Volume ramps UP: $60 \to 160\text{ RPS}$ | $fp$ ramps DOWN: $0.70 \to 0.20$ | **2** | **1** | **12** | **Anti-symmetric demand explosion**: Slow-path jumps from $18 \to 128\text{ RPS}$ ($7.1\times$). Sized for pre-shift load ($18\text{ RPS}$). Tests whether controller scales for true GPU load or blindly follows volume ($2.67\times$). |
| `suite2_opposing2` | **Opposing Shift 2 (Vol DOWN, fp UP)** | Volume ramps DOWN: $160 \to 60\text{ RPS}$ | $fp$ ramps UP: $0.20 \to 0.70$ | **4** | **1** | **12** | **Accelerated reclamation**: Slow-path drops from $128 \to 18\text{ RPS}$ ($86\%$ reduction). Sized warm for the high-demand origin. Tests whether conformal scaler reclaims GPU cost faster than volume-based scalers. |
| `suite2_storm` | **Coupled Storm Surge** | Base $60\text{ RPS}$, spikes to $180\text{ RPS}$ during storm (epochs 50–80) | Base $0.65$, drops to $0.15$ during storm window | **2** | **1** | **12** | **Multiplicative worst-case stress**: Slow-path explodes from $21 \to 153\text{ RPS}$ ($7.3\times$). Sized for fair-weather load ($21\text{ RPS}$). Evaluates peak cluster headroom and stability without over-shooting post-storm. |
| `suite3_azure` | **Rolling Azure Macrobenchmark** | Real Azure 2019 trace with $2.0\times$ in-memory replay scaling | Continuous diurnal solar cycle ($0.65 \leftrightarrow 0.20$) + injected storm bursts | **2** | **0** | **12** | **Production macrobenchmark**: Sized for initial trace amplitude. Setting `min_workers=0` enables scale-to-zero during nocturnal troughs when invocations drop to near-zero, validating true diurnal energy/cost savings. |

---

## 3. Physical Continuum Infrastructure Topology

All 12 suite configurations share the unified, scaled multi-tier physical infrastructure:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CONTINUUM INFRASTRUCTURE TIERS                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. IoT Sensor Tier: 4 Nodes (IoT_0 .. IoT_3)                                           │
│    • Resources per node: 4.0 CPU, 8.0 GB RAM, 64.0 GB Storage                          │
│    • Role: Hosts CameraSource generator (pinned via placement_layers: ['iot'])         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Edge Compute Tier: 8 Nodes (Edge_0 .. Edge_7)                                       │
│    • Resources per node: 24.0 CPU, 64.0 GB RAM, 2000.0 GB Storage                      │
│    • Role: Hosts EdgePreprocess, EdgeInference (Conformal Scorer), and Sink            │
│    • Pinned via placement_layers: ['edge']                                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. Cloud GPU Tier: 6 Nodes (Cloud_0 .. Cloud_5)                                        │
│    • Resources per node: 24.0 CPU, 48.0 GB RAM, 1000.0 GB Storage                     │
│    • Worker Spec: CloudRefineWorker requires 8.0 CPU, 16.0 GB RAM                      │
│    • Maximum Workers per Cloud Node: 24.0 / 8.0 = 3 workers                            │
│    • Dynamic Distribution: 12 workers distribute across 4 separate physical nodes      │
│      (e.g., Cloud_0: 3, Cloud_1: 3, Cloud_2: 3, Cloud_3: 3)                            │
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
