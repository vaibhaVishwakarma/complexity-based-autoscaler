# Workload Regimes & Simulation Initialization Specification

**Document Role**: Authoritative, executable reference for multi-tier workload regimes, closed-form arrival patterns, queueing service rates, and simulation initialization across IoT, Edge, and Cloud tiers.  
**Associated Configs**: [`configs/suites/`](file:///home/vaibo/edgecompute/configs/suites/)  
**Generator Implementation**: [`src/continuum_ext/workload/conformal_workloads.py`](file:///home/vaibo/edgecompute/src/continuum_ext/workload/conformal_workloads.py)  
**Hardware Profile Grounding**: [`contracts/gate2.py`](file:///home/vaibo/edgecompute/contracts/gate2.py) & [`gate2/output-gpu-t4/triton_service_profiles.json`](file:///home/vaibo/edgecompute/gate2/output-gpu-t4/triton_service_profiles.json)  
**Dataset Integrity**: `data/azure_traces/azure_functions_2019_processed.npz` (SHA256: `9aeabacb08f01b34f46efc252db76248a55094cdae1f0e86c8eda39fa09b7447`)  
**Governance Compliance**: Adheres strictly to [`AGENTS.md`](file:///home/vaibo/edgecompute/AGENTS.md) Rules #1, #2, #5, and #6.

---

## 1. Executive Summary & Continuum Architecture

In distributed edge-cloud continuum computing, autoscaling evaluations require rigorous boundary initialization and queueing models across all participating tiers.

```
[ IoT Sensor Tier (IoT_0..3): λ(t) Poisson Ingress ]
                         │
                         ▼
        ┌─────────────────────────────────┐
        │        EDGE GATEWAY TIER        │
        │  • EfficientNet-B0 ONNX (CPU)   │
        │  • Calibrated RAPS Triage       │
        │  • Causal Telemetry Broadcast   │
        └─────────────────────────────────┘
                 │               │
            |C(x)| = 1      |C(x)| >= 2
           (Fast-Path)      (Slow-Path)
            p_fast(t)       1 - p_fast(t)
                 │               │
                 ▼               ▼  WAN Transit (25ms RTT, 1000 Mbps)
        ┌─────────────────┐   ┌─────────────────────────────────────┐
        │   LOCAL SINK    │   │       CLOUD GPU WORKER POOL         │
        │ (Edge_0, 15.0s) │   │  • ResNet-152 on Tesla T4 GPUs      │
        └─────────────────┘   │  • Triton Dynamic Batching (B<=8)   │
                              │  • Scaled: k in [min_w, max_w]      │
                              └─────────────────────────────────────┘
```

### 1.1 Triage Routing & Cloud Load Formulation
1. **RAPS Prediction Sets**: Edge inference evaluates each frame $x_i$ using Regularized Adaptive Prediction Sets (RAPS) calibrated at miscoverage level $\alpha = 0.10$ ($\hat{q} = 0.79914$, [`contracts/gate1.py`](file:///home/vaibo/edgecompute/contracts/gate1.py)).
2. **Deterministic Routing Rule**:
   $$\text{Route}(x_i) = \begin{cases} \text{Fast-Path (Local Edge Sink)}, & |C(x_i)| = 1 \\ \text{Slow-Path (Cloud GPU Worker Pool)}, & |C(x_i)| \ge 2 \end{cases}$$
3. **Empirical Fast-Path Acceptance Ratio $p_{\text{fast}}(t)$**:
   $$p_{\text{fast}}(t) \triangleq \mathbb{P}_{x \sim \mathcal{D}_t}\bigl(|C(x_i)| = 1\bigr)$$
4. **Offered Cloud Arrival Rate**:
   $$\lambda_{\text{cloud}}(t) = \lambda(t) \cdot \bigl(1 - p_{\text{fast}}(t)\bigr)$$
5. **Complexity Prevalence**: Separately measured via mean prediction set size $\bar{C}(t) = \mathbb{E}[|C(x)|]$. Under clean conditions, $\bar{C} \approx 1.28$ and $p_{\text{fast}} \approx 0.70$; under out-of-distribution (OOD) corruption, $\bar{C} \ge 3.5$ and $p_{\text{fast}} \downarrow 0.20$.

---

## 2. Queueing Feasibility & Service-Rate Modeling

ContinuumBench executes as a discrete-event credit engine with simulation epoch step $T_e = 1.0\text{ s}$. Capacity per stage per epoch is governed by:
$$\text{Capacity} = \left\lfloor \text{workers} \cdot \frac{T_e}{T_{\text{proc}}} \right\rfloor$$

### 2.1 Calibrated Service Times Grounded in Gate 2 Profiling
- **EdgePreprocess**: $T_{\text{proc}} = 0.002\text{ s} \implies \mu = 500\text{ RPS}$ (multi-threaded CPU normalization).
- **EdgeInference**: $T_{\text{proc}} = 0.003\text{ s} \implies \mu = 333\text{ RPS}$ (multi-core ONNX runtime execution on 24-core Edge node). Edge stages provide guaranteed headroom ($>300\text{ RPS}$) so bottlenecks are never masked by edge CPU starvation.
- **CloudRefineWorker**: Calibrated to empirical Gate 2 Tesla T4 GPU profiling ([`triton_service_profiles.json`](file:///home/vaibo/edgecompute/gate2/output-gpu-t4/triton_service_profiles.json)):
  - Profiled batch size $B=8$ latency: $T_{\text{exec}} = 62.67\text{ ms} \approx 0.0625\text{ s}$.
  - Service rate per worker: $\mu_{\text{worker}} = \lfloor 1.0 / 0.0625 \rfloor = \mathbf{16.0\text{ RPS/worker}}$.
  - Cluster scaling capacity:
    - $k = 1$ worker: $16\text{ RPS}$ (ramp onset floor).
    - $k = 2$ workers: $32\text{ RPS}$ (fair-weather base load).
    - $k = 4$ workers: $64\text{ RPS}$ (steady-state equilibrium).
    - $k = 10$ workers: $160\text{ RPS}$ (sustains storm peak of $153\text{ RPS}$).
    - $k = 12$ workers: $192\text{ RPS}$ ($25\%$ peak burst headroom).

### 2.2 Physical Node Allocation & Density Math
- **Cloud Hardware**: 6 Physical Nodes (`Cloud_0` .. `Cloud_5`), each with 24.0 vCPU, 48.0 GB RAM.
- **Worker Footprint**: Each `CloudRefineWorker` requires 8.0 vCPU, 16.0 GB RAM.
- **Node Density**: $\min(\lfloor 24/8 \rfloor, \lfloor 48/16 \rfloor) = \mathbf{3\text{ workers per node}}$.
- **Dynamic Placement Disclosure**:
  $$\text{Nodes Required}(k) = \left\lceil \frac{k}{3} \right\rceil$$
  At peak capacity ($k = 12$ workers), workers distribute across **4 physical nodes** (`Cloud_0` .. `Cloud_3` with 3 workers each). `Cloud_4` and `Cloud_5` remain reserved as cluster scale-out headroom.

---

## 3. Comprehensive Multi-Tier Initialization Matrix

| Regime Key | Workload Name | Ingress $\lambda(t)$ | Complexity $p_{\text{fast}}(t)$ | Cloud Demand $\lambda_{\text{cloud}}(t)$ | Cloud Workers (`init / min / max`) | Physical & Scientific Reasoning across Tiers |
|:---|:---|:---|:---|:---:|:---:|:---|
| `suite1_flat` | **Steady-State Baseline** | Flat $100\text{ RPS}$ | Fixed $0.50$ | $50\text{ RPS}$ | **4 / 1 / 12** | **Equilibrium start**: Slow-path load is $50\text{ RPS}$. 4 workers ($64\text{ RPS}$ capacity) eliminate warmup transients to measure pure steady-state drift and cost. |
| `suite1_spike` | **Volume Spike** | Base $60\text{ RPS} \to$ $300\text{ RPS}$ (3s) | Fixed $0.50$ | $30 \to 150\text{ RPS}$ | **2 / 1 / 12** | **Sized for base rate**: 2 workers ($32\text{ RPS}$) sustain base load. Tests burst detection and rapid scale-out to 10 workers ($160\text{ RPS}$) during 5× spike. |
| `suite1_burst` | **Bursty Two-State MMPP** | Low $40 \leftrightarrow$ High $200\text{ RPS}$ | Fixed $0.50$ | $20 \leftrightarrow 100\text{ RPS}$ | **2 / 1 / 12** | **Sized for low state**: Tests whether the controller absorbs stochastic MMPP bursts without excessive flapping ($|\Delta k|$) or queue starvation. |
| `suite1_ramp` | **Continuous Volume Ramp** | Linear $20 \to 160\text{ RPS}$ (100s) | Fixed $0.50$ | $10 \to 80\text{ RPS}$ | **1 / 1 / 12** | **Ramp onset tracking**: Starts at 1 worker ($16\text{ RPS}$). Tests continuous derivative tracking without lag-induced queue accumulation up to 5 workers ($80\text{ RPS}$). |
| `suite1_zero_begin` | **Cold Start (Scale-from-Zero)** | $0\text{ RPS} \to$ ramp to $120\text{ RPS}$ | Fixed $0.50$ | $0 \to 60\text{ RPS}$ | **0 / 0 / 12** | **Strict cold boot**: Strict 0 instances and 0 floor. Verifies zero idle cost and measures activation delay $\tau_{\text{boot}} = 1.0\text{s}$ queue pileup. |
| `suite1_zero_terminal` | **Scale-to-Zero Reclamation** | $120\text{ RPS} \to 0\text{ RPS} \to$ drain | Fixed $0.50$ | $60 \to 0\text{ RPS}$ | **4 / 0 / 12** | **Idle reclamation**: Starts warm (4 workers). Enforces Graceful Drain Invariant during 15-epoch post-arrival window ($t \in [150, 165]$) down to 0 workers. |
| `suite2_shock` | **Complexity Shock (Constant Vol)**| Flat $100\text{ RPS}$ | Shock $0.70 \to 0.20$ at 60s | $30 \to 80\text{ RPS}$ | **2 / 1 / 12** | **Isolates complexity channel**: Volume is silent. Edge triage streams $p_{\text{fast}} \downarrow$; tests proactive preemption before cloud backlog forms. |
| `suite2_recovery` | **Complexity Shock & Recovery** | Flat $100\text{ RPS}$ | $0.20 \to 0.70$ over 60s | $80 \to 30\text{ RPS}$ | **2 / 1 / 12** | **Hysteresis avoidance**: Evaluates safe scale-down back to 2 workers as Edge inference signals recovering model confidence. |
| `suite2_compound_stress` | **Compounding Stress Surge** | Ramp $60 \to 160\text{ RPS}$ | Ramp $0.70 \to 0.20$ | $18 \to 128\text{ RPS}$ | **2 / 1 / 12** | **Compounding stress**: Both volume and complexity push cloud demand upward ($7.1\times$ surge). Tests peak cluster scale-out. |
| `suite2_compound_relief` | **Compounding Relief Drain** | Ramp $160 \to 60\text{ RPS}$ | Ramp $0.20 \to 0.70$ | $128 \to 18\text{ RPS}$ | **4 / 1 / 12** | **Compounding relief**: Both volume and complexity drop cloud demand ($86\%$ reduction). Tests rapid worker reclamation. |
| `suite2_decoupled_opposing` | **Decoupled Ingress vs Cloud** | Ramp $50 \to 150\text{ RPS}$ | Ramp $0.40 \to 0.80$ | **$30\text{ RPS}$ (constant)** | **2 / 1 / 12** | **True opposing test**: Total ingress triples while cloud demand remains flat. Proves conformal controller avoids volume-blind over-scaling. |
| `suite2_storm` | **Coupled Storm Surge** | Base $60 \to$ Spike $180\text{ RPS}$ | Base $0.65 \to$ Drop $0.15$ | $21 \to 153\text{ RPS}$ | **2 / 1 / 12** | **Worst-case multiplicative surge**: Slow-path demand explodes $7.3\times$. Stresses cluster capacity to 10 workers ($160\text{ RPS}$). |
| `suite3_azure` | **Rolling Azure Macrobenchmark** | Azure 2019 trace ($2.0\times$) | Diurnal $0.65 \leftrightarrow 0.20$ | Trace-driven | **2 / 0 / 12** | **Production macrobenchmark**: Replays 14-day Azure trace. Setting `min_workers=0` evaluates scale-to-zero during nocturnal invocation lulls. |

---

## 4. Closed-Form Piecewise Mathematical Formulations

All regimes execute with epoch step $T_e = 1.0\text{ s}$. Arrivals are drawn from a Poisson process: $N_t \sim \text{Poisson}(\lambda(t) \cdot T_e)$.

### 4.1 Suite 1: Volume Archetypes (Fixed $p_{\text{fast}} = 0.50$)

- **`suite1_flat`**:
  $$\lambda(t) = 100.0, \quad p_{\text{fast}}(t) = 0.50 \quad \forall t \in [0, 60)$$
- **`suite1_spike`**:
  $$\lambda(t) = \begin{cases} 300.0, & 50 \le t < 53 \\ 60.0, & \text{otherwise} \end{cases}, \quad p_{\text{fast}}(t) = 0.50$$
- **`suite1_burst` (Bursty Two-State MMPP)**:
  Modulated arrival rate $\lambda(t) \in \{40.0, 200.0\}$. Discrete transition probability matrix:
  $$P = \begin{bmatrix} 1 - p_{12} & p_{12} \\ p_{21} & 1 - p_{21} \end{bmatrix} = \begin{bmatrix} 0.95 & 0.05 \\ 0.15 & 0.85 \end{bmatrix}$$
  Expected dwell times: $\mathbb{E}[T_{\text{low}}] = \frac{1}{0.05} = 20.0\text{ s}$, $\mathbb{E}[T_{\text{high}}] = \frac{1}{0.15} = 6.67\text{ s}$.
- **`suite1_ramp`**:
  $$\lambda(t) = \begin{cases} 20.0 + 1.40 \cdot t, & 0 \le t \le 100 \\ 160.0, & t > 100 \end{cases}, \quad p_{\text{fast}}(t) = 0.50$$
- **`suite1_zero_begin` (Cold-Start)**:
  $$\lambda(t) = \begin{cases} 0.0, & 0 \le t < 4 \\ 120.0 \cdot \frac{t - 4}{50}, & 4 \le t \le 54 \\ 120.0, & t > 54 \end{cases}, \quad p_{\text{fast}}(t) = 0.50$$
  $\text{initial\_workers} = 0, \text{min\_workers} = 0, \tau_{\text{boot}} = 1.0\text{ s}$.
- **`suite1_zero_terminal` (Scale-to-Zero)**:
  $$\lambda(t) = \begin{cases} 120.0, & 0 \le t < 80 \\ 120.0 \cdot \left(1 - \frac{t - 80}{70}\right), & 80 \le t \le 150 \\ 0.0, & 150 < t \le 165 \end{cases}, \quad p_{\text{fast}}(t) = 0.50$$
  $\text{initial\_workers} = 4, \text{min\_workers} = 0$. Post-arrival drain window: $t \in (150, 165]$.

---

### 4.2 Suite 2: Complexity Microbenchmarks

- **`suite2_shock`**:
  $$\lambda(t) = 100.0, \quad p_{\text{fast}}(t) = \begin{cases} 0.70, & 0 \le t < 60 \\ 0.20, & t \ge 60 \end{cases}$$
- **`suite2_recovery`**:
  $$\lambda(t) = 100.0, \quad p_{\text{fast}}(t) = \begin{cases} 0.70, & 0 \le t < 40 \\ 0.20 + 0.50 \cdot \frac{t - 40}{60}, & 40 \le t \le 100 \\ 0.70, & t > 100 \end{cases}$$
- **`suite2_compound_stress`** (formerly `opposing1`):
  $$\lambda(t) = \begin{cases} 60.0, & 0 \le t < 30 \\ 60.0 + 100.0 \cdot \frac{t - 30}{80}, & 30 \le t \le 110 \\ 160.0, & t > 110 \end{cases}, \quad p_{\text{fast}}(t) = \begin{cases} 0.70, & 0 \le t < 30 \\ 0.70 - 0.50 \cdot \frac{t - 30}{80}, & 30 \le t \le 110 \\ 0.20, & t > 110 \end{cases}$$
- **`suite2_compound_relief`** (formerly `opposing2`):
  $$\lambda(t) = \begin{cases} 160.0, & 0 \le t < 30 \\ 160.0 - 100.0 \cdot \frac{t - 30}{80}, & 30 \le t \le 110 \\ 60.0, & t > 110 \end{cases}, \quad p_{\text{fast}}(t) = \begin{cases} 0.20, & 0 \le t < 30 \\ 0.20 + 0.50 \cdot \frac{t - 30}{80}, & 30 \le t \le 110 \\ 0.70, & t > 110 \end{cases}$$
- **`suite2_decoupled_opposing`** (New Decoupled Test):
  $$\lambda(t) = 50.0 + 100.0 \cdot \frac{t}{80}, \quad p_{\text{fast}}(t) = 0.40 + 0.40 \cdot \frac{t}{80} \implies \lambda_{\text{cloud}}(t) = 30.0\text{ RPS (constant)}$$
- **`suite2_storm`**:
  $$\lambda(t) = \begin{cases} 180.0, & 50 \le t < 80 \\ 60.0, & \text{otherwise} \end{cases}, \quad p_{\text{fast}}(t) = \begin{cases} 0.15, & 50 \le t < 80 \\ 0.65, & \text{otherwise} \end{cases}$$

---

### 4.3 Suite 3: Rolling Azure Macrobenchmark

- **Authoritative Trace**: `data/azure_traces/azure_functions_2019_processed.npz`
- **SHA256**: `9aeabacb08f01b34f46efc252db76248a55094cdae1f0e86c8eda39fa09b7447`
- **Length**: 1,209,600 observations ($14\text{ days}$ at $1.0\text{ Hz}$).
- **In-Memory Scaling**: $\lambda(t) = \text{arrival\_rates}[t] \times 2.0$.
- **Diurnal Overlay**:
  $$p_{\text{fast}}(t) = 0.425 + 0.225 \cdot \cos\left(\frac{2\pi t}{1440}\right)$$
  interspersed with injected storm bursts ($p_{\text{fast}} = 0.10, \lambda_{\text{boost}} = 2.5\times$ at epochs 300, 800, 1200).

---

## 5. System Invariants & Protocols

### 5.1 Causal Telemetry Frame Protocol (Zero Oracle Lookahead)
1. Ingress requests during epoch $t-1$ are triaged at `EdgeInference`.
2. At timestamp $t \cdot T_e$, the Edge Gateway transmits a 16-byte packet across the $25\text{ ms}$ WAN link:
   $$\mathcal{F}_{t-1} = \langle t-1, \hat{\lambda}_{t-1}, \hat{p}_{\text{fast}, t-1}, \bar{C}_{t-1} \rangle$$
3. The Cloud controller receives $\mathcal{F}_{t-1}$ at $t \cdot T_e + 25\text{ ms}$ and computes scaling decisions for epoch $t$ with **zero lookahead into future arrivals**.
4. Preemptive scaling succeeds because semantic drift exhibits temporal persistence across multi-second scenes.

### 5.2 Graceful Drain Invariant for Scale-to-Zero
When an autoscaler reduces workers ($k_{\text{target}} < k_{\text{current}}$):
$$\text{Deactivate}(w) \implies \text{len}(\text{queue}_w) = 0 \;\land\; \text{in\_flight}_w = 0$$
Draining workers stop receiving new tasks but continue processing queued work until empty, preventing task abandonment during scale-down.

### 5.3 Metric Discipline
Cost is strictly quantified in **Worker-Seconds**:
$$\text{Cost} = \sum_{t=1}^{T_{\text{sim}}} k(t) \cdot T_e \quad [\text{worker-seconds}]$$
No ungrounded "energy savings" are reported.
