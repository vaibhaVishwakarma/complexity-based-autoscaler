# EdgeCompute Documentation Index

This directory contains the authoritative technical specifications, benchmark reports, and architectural blueprints for the Conformal Autoscaler research paper.

---

## 1. Documentation Index

| Document | Primary Role | Scope & Key Contents |
|:---|:---|:---|
| **[`CONFORMAL_AUTOSCALER_STRATEGY.md`](CONFORMAL_AUTOSCALER_STRATEGY.md)** | **Master Strategy & Specification** | Single source of truth for the entire paper. Covers the 6 target systems, mathematical formulation of InferLine & Conformal Autoscaler, hardware profiling surface (T4 GPU), 3-suite workload taxonomy, and the 9-step execution roadmap. |
| **[`WORKLOAD_REGIMES_AND_INITIALIZATION.md`](WORKLOAD_REGIMES_AND_INITIALIZATION.md)** | **Regime & Initialization Spec** | Complete breakdown of all 12 workload regimes across Suites 1, 2, and 3. Specifies exact volume $\lambda(t)$, complexity $fp(t)$, initial instances (`initial_workers`), minimum replica floor (`min_workers`), and the scientific rationale for each regime. |
| **[`system_architecture.md`](system_architecture.md)** | **Physical & Simulated Architecture** | Detailed multi-tier architecture diagrams. Covers IoT, Edge, WAN, and Cloud tiers; request routing flow (Fast-path singleton vs Slow-path offload); discrete-time simulation mechanics; and controller visibility boundaries. |
| **[`PRELIMINARY_NON_CONFORMAL_BASELINES_REPORT.md`](PRELIMINARY_NON_CONFORMAL_BASELINES_REPORT.md)** | **Preliminary Empirical Report** | Stage 3 baseline evaluation on a 4-IoT / 8-Edge / 6-Cloud continuum. Reports comparative empirical performance across all 5 non-conformal baselines (Fixed, HPA, KEDA, InferLine, Blind), analysis of HPA flapping (117 deltas) vs InferLine stabilization (12 deltas), and the motivating Queue-Reaction Lag dilemma. |

---

## 2. Workload Regimes & Simulation Initialization Matrix (Quick Reference)

| Regime Key | Workload Name | Volume Pattern $\lambda(t)$ | Complexity Pattern $fp(t)$ | Initial Workers (`initial_workers`) | Minimum Floor (`min_workers`) | Maximum Ceiling (`max_workers`) | Scientific & Engineering Reasoning |
|:---|:---|:---|:---|:---:|:---:|:---:|:---|
| `suite1_flat` | **Steady-State Baseline** | Constant flat $\lambda = 100\text{ RPS}$ | Fixed $fp = 0.50$ | **4** | **1** | **12** | **Equilibrium warm start**: At $\lambda=100$ and $fp=0.50$, slow-path demand is $50\text{ RPS}$. 4 workers provide steady equilibrium from epoch 0, eliminating startup transients to measure pure steady-state drift and cost. |
| `suite1_spike` | **Volume Spike** | Base $60\text{ RPS}$, instantaneous $5\times$ spike to $300\text{ RPS}$ for 3 epochs | Fixed $fp = 0.50$ | **2** | **1** | **12** | **Sized for base rate**: Slow-path base is $30\text{ RPS}$ ($2$ workers). Initializing with peak workers would mask reactive latency; starting with 2 workers rigorously tests burst detection, scale-out speed, and buffer protection when traffic suddenly multiplies by 5×. |
| `suite1_burst` | **Bursty MMPP Traffic** | Two-state Markov process: Low $40\text{ RPS} \leftrightarrow$ High $200\text{ RPS}$ | Fixed $fp = 0.50$ | **2** | **1** | **12** | **Sized for low state**: Slow-path low is $20\text{ RPS}$. Tests whether the controller can absorb stochastic, heavy-tailed bursts without flapping prematurely or starving the queue during extended bursts. |
| `suite1_ramp` | **Continuous Volume Ramp** | Linear acceleration $20 \to 160\text{ RPS}$ over 100 epochs | Fixed $fp = 0.50$ | **1** | **1** | **12** | **Sized for ramp onset**: Slow-path onset is $10\text{ RPS}$. Tests the controller's ability to track a continuous derivative without lag-induced backlog or aggressive over-shooting. |
| `suite1_zero_begin` | **Cold Start (Scale-from-Zero)** | Starts at $\lambda = 0\text{ RPS}$, holds 4 epochs, then ramps to $120\text{ RPS}$ | Fixed $fp = 0.50$ | **0** | **0** | **12** | **Strict cold boot**: Zero initial instances and zero minimum floor. Verifies zero idle cost while load is zero, and measures exact latency and queue pileup during container startup delay ($1.0\text{s}$) when the first request arrives. |
| `suite1_zero_terminal` | **Scale-to-Zero (Reclamation)** | Starts at $120\text{ RPS}$ plateau, then ramps down to $0\text{ RPS}$ from epoch 80 to 150 | Fixed $fp = 0.50$ | **4** | **0** | **12** | **Tests idle spin-down**: Starts warm for the $120\text{ RPS}$ plateau ($60\text{ RPS}$ slow-path). Setting `min_workers=0` evaluates idle-worker reclamation, penalizing controllers that retain zombie replicas after load drains. |
| `suite2_shock` | **Steady RPS + Complexity Shock** | Constant flat $\lambda = 100\text{ RPS}$ (silent volume) | Sudden OOD drop at epoch 60: $0.70 \to 0.20$ | **2** | **1** | **12** | **Isolates complexity channel**: Sized for pre-shock load ($100 \times 0.30 = 30\text{ RPS}$). Volume is silent ($\lambda=100$). Tests whether conformal telemetry preemptively scales before queue backlog forms, exposing the queue-lag failure of baselines. |
| `suite2_recovery` | **Complexity Shock + Recovery** | Constant flat $\lambda = 100\text{ RPS}$ | Drops to $0.20$ at epoch 40, linearly recovers to $0.70$ over 60 epochs | **2** | **1** | **12** | **Tests recovery hysteresis**: Sized for nominal load. Evaluates scale-up during shock, and tests fast, safe scale-down without hysteresis or premature deallocation as the model returns to high confidence. |
| `suite2_opposing1` | **Opposing Shift 1 (Vol UP, fp DOWN)** | Volume ramps UP: $60 \to 160\text{ RPS}$ | $fp$ ramps DOWN: $0.70 \to 0.20$ | **2** | **1** | **12** | **Anti-symmetric demand explosion**: Slow-path jumps from $18 \to 128\text{ RPS}$ ($7.1\times$). Sized for pre-shift load ($18\text{ RPS}$). Tests whether controller scales for true GPU load or blindly follows volume ($2.67\times$). |
| `suite2_opposing2` | **Opposing Shift 2 (Vol DOWN, fp UP)** | Volume ramps DOWN: $160 \to 60\text{ RPS}$ | $fp$ ramps UP: $0.20 \to 0.70$ | **4** | **1** | **12** | **Accelerated reclamation**: Slow-path drops from $128 \to 18\text{ RPS}$ ($86\%$ reduction). Sized warm for the high-demand origin. Tests whether conformal scaler reclaims GPU cost faster than volume-based scalers. |
| `suite2_storm` | **Coupled Storm Surge** | Base $60\text{ RPS}$, spikes to $180\text{ RPS}$ during storm (epochs 50–80) | Base $0.65$, drops to $0.15$ during storm window | **2** | **1** | **12** | **Multiplicative worst-case stress**: Slow-path explodes from $21 \to 153\text{ RPS}$ ($7.3\times$). Sized for fair-weather load ($21\text{ RPS}$). Evaluates peak cluster headroom and stability without over-shooting post-storm. |
| `suite3_azure` | **Rolling Azure Macrobenchmark** | Real Azure 2019 trace with $2.0\times$ in-memory replay scaling | Continuous diurnal solar cycle ($0.65 \leftrightarrow 0.20$) + injected storm bursts | **2** | **0** | **12** | **Production macrobenchmark**: Sized for initial trace amplitude. Setting `min_workers=0` enables scale-to-zero during nocturnal troughs when invocations drop to near-zero, validating true diurnal energy/cost savings. |

---

## 3. Physical Multi-Tier Continuum Topology

- **IoT Tier (4 Nodes: `IoT_0` – `IoT_3`)**: Ingress source nodes generating $\lambda(t)$ Poisson arrivals.
- **Edge Tier (8 Nodes: `Edge_0` – `Edge_7`)**: Low-latency edge compute nodes hosting `EdgePreprocess`, `EdgeInference` (ONNX conformal scorer), and the `Sink`.
- **Cloud Tier (6 Nodes: `Cloud_0` – `Cloud_5`)**: Tesla T4 GPU nodes running Triton Inference Server, hosting dynamically scaled `CloudRefine` worker instances ($8$ CPU, $16$ GB RAM each; max 3 workers per cloud node).
- **WAN Transit Link**: Edge $\to$ Cloud transit profile ($25\text{ ms}$ latency, $1000\text{ Mbps}$ bandwidth).
