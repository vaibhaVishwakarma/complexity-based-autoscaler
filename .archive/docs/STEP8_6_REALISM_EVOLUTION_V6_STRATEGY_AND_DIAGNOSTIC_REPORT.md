# Step 8.6: Realism-Aware Evolution v6 — Strategy, Forensic Diagnosis & v3-Anchored Architecture

**Authoritative Roadmap for Next-Generation Conformal Autoscaler Synthesis**  
*Document Version: 1.0 — Date: October 2026*  
*Workspace Governance: AGENTS.md Compliant | Version Immutability | Zero Oracle Leakage | Zero Git Push*

---

## 1. Executive Summary & Mission Statement

The mission of **OpenEvolve v6** is to synthesize a production-grade, mathematically optimal, and physically resilient autoscaler scaling law that bridges the **scale gap under real-world model functional readiness delays** ($T_{\text{init}} \in [2.0\text{s} \to 300.0\text{s}]$) while unconditionally preserving the cost-supreme efficiency and zero-miss SLA compliance achieved by the **v3 Global Champion (`bbd9b1c2`)**.

### Authoritative Target Thresholds for v6:
1. **Canonical Cost Savings $> 50\%$**: Total worker-seconds across the 13 canonical regimes must remain strictly below $13,950\text{ ws}$ (relative to the $27,900.0\text{ ws}$ fixed capacity peak; v3 Champion achieved $57.44\%$ / $11,874.0\text{ ws}$).
2. **Canonical Deadline Misses Strictly Between $0 - 10$**: Across all $121,134$ requests in the 13 canonical suites at $T_{\text{init}} = 1.0\text{s}$, deadline misses must remain $\le 10$ (target: 0 misses).
3. **Physical Realism Containment Grounded in Step 8.5 Tipping Points**:
   - **Diurnal Production Workloads (`suite3_azure`)**: Strict zero deadline misses across all boot delays up to $300\text{s}$ (5 minutes).
   - **Acute Poisson Spikes (`suite1_spike`)**: Strict zero deadline misses up to the $50.0\text{s}$ tipping point.
   - **Opposing Semantic Shocks (`suite2_shock`)**: Near-zero misses ($\le 11$ misses) up to the $15.0\text{s}$ SLA deadline tipping point, with max P99 latency within the $15.0\text{s}$ SLA budget.
   - **Total Expected Realism Misses for Seed Baseline**: $\mathbf{\approx 11\text{ misses}}$ across all 10 realism regimes.
4. **Decisive Dominance Over Industry & Academic Baselines**:
   - Outperform **InferLine** ($44\text{ misses}$ canonical, $\approx 45\text{ misses}$ realism, high actuation churn).
   - Outperform **Kubernetes HPA** ($> 10,000\text{ misses}$ realism, $> 50\%$ higher operational cost).
   - Outperform **KEDA** ($> 10,000\text{ misses}$ realism, severe activation flapping).

---

## 2. In-Depth Retrospective: Learnings from Past Evolution Runs (v1 to v5)

Every iteration of OpenEvolve in this project has revealed critical operational and physical insights. Table 1 catalogs the progression from v1 to v5 and how v6 systematically addresses each past failure mode.

### Table 1: Multi-Version Evolution Progression & Corrective Actions

| Version | Core Objective | Primary Breakthrough | Critical Bottleneck / Failure Mode | Root Cause Analysis | Corrective Action in v6 |
|:---|:---|:---|:---|:---|:---|
| **v1** | Baseline genetic synthesis | Proved feasibility of LLM-driven autoscaling laws on ContinuumBench | Module import crashes, unsafe builtins, non-terminating policies | Unconstrained code generation without AST boundaries | **Stage 1 AST Purity Gate**: Strict whitelist of modules + 5 boundary unit tests. |
| **v2** | Island MAP-Elites search | Introduced continuous feature descriptors (cost savings vs churn) | Scale-to-zero queue traps and cold-start death spirals | Simulator allowed $k_{\min}=0$; controllers starved queues to inflate cost savings | **Enterprise Baseline Gating**: Enforce $k_{\min} \ge 1$ across all suites. |
| **v3** | Cost-Supreme search ($P99 \le 6.0\text{s}$) | **Discovered Global Champion `bbd9b1c2`**: $+55.16$ fitness, $57.44\%$ savings, 0 misses, 227 flaps | High candidate evaluation latency (~160s serial); evaluated only $T_{\text{init}} = 1.0\text{s}$ | Serial execution across 13 suites; physical container startup delays not modeled | **Parallelized execution** via `ThreadPoolExecutor` + **Tier 2 Realism Layer**. |
| **v4** | Multi-island realism exploration | Explored derivative lookahead under startup delays | Island drift, divergent fitness functions, high mutation stagnation | Fragmented populations competed with conflicting island objectives | **Unified Population (Island 0)** with strict signature deduplication. |
| **v5** | Unified population + signature deduplication | Enforced duplicate signature rejection; maintained 0 canonical misses | **Candidates clustered at $\sim 6,983$ shock misses** ($< 1\%$ improvement over 7,031 seed) | **The Physical Duration Trap**: Evaluated $50\text{s}, 150\text{s}, 300\text{s}$ delays on 90s shock traces where shock hits at second 60. New workers physically never arrived before simulation end. 7,020 misses was an unavoidable physical floor. Moreover, `suite3_azure` was omitted from Tier 2, and the fitness gradient was completely flattened ($+0.20$ reward capped at $+10$ pts vs $+57.4$ cost). | **Anchor to v3 criteria; ground Tier 2 in Step 8.5 physical tipping points; include `suite3_azure`; restore active gradient in $J_{\text{v6}}$.** |

---

## 3. Forensic Post-Mortem of the v5 Evolution Run

Analysis of the 52-iteration Codespace run (`temp/evolution_v5_results_bundle.tar.gz`) revealed why all top-ranking controllers (`a073059d`, `e473c80a`, `2870ae3e`) clustered tightly between $6,981$ and $6,989$ shock misses:

### 3.1 The Physical "Dead-Time Queuing" Boundary
In `configs/suites/suite2_shock.yaml`, the total simulation duration is **90 epochs (90 seconds)**. The opposing semantic collapse occurs at **epoch 60** ($p_{\text{fast}}$ drops from $0.70 \to 0.20$), causing offered cloud demand to surge from $30 \to 80\text{ RPS}$.
There are **only 30 seconds remaining** in the simulation before completion.

In `openevolve_evaluator_v5.py`, the realism benchmark tested:
- `suite2_shock` @ $15.0\text{s}$ delay: Workers boot at epoch 75 (15 seconds before trace end). Result: **11 misses** (P99 $14.0\text{s} \le 15.0\text{s}$ SLA).
- `suite2_shock` @ $50.0\text{s}$ delay: Workers boot at epoch 110 (after simulation terminates!). Result: **1,939 misses**.
- `suite2_shock` @ $150.0\text{s}$ delay: Workers boot at epoch 210 (after simulation terminates!). Result: **2,379 misses**.
- `suite2_shock` @ $300.0\text{s}$ delay: Workers boot at epoch 360 (after simulation terminates!). Result: **2,379 misses**.
- `suite1_spike` @ $50.0\text{s}$ delay: Workers absorb burst before deadline expiration. Result: **0 misses**.
- `suite1_spike` @ $300.0\text{s}$ delay: Workers boot after burst window ends. Result: **323 misses**.

Summing these misses:
$$11 + 1,939 + 2,379 + 2,379 + 0 + 323 = \mathbf{7,031\text{ misses (Seed Baseline)}}$$

Out of these 7,031 misses, **6,697 misses ($95.2\%$) occurred in tests where new workers could physically never come online before the simulation ended**. The unserviced deficit accumulated into the queue, and with a $15.0\text{s}$ SLA deadline, practically every request arriving during the shock missed the deadline.

### 3.2 The Reactive Autoscaler Deadlock
Because an autoscaler acts purely on cloud provisioning (leaving request routing unchanged), it cannot prevent physical dead-time queuing once the dead time exceeds the deadline itself ($T_{\text{init}} > D_{\text{SLA}} = 15.0\text{s}$). The only way an autoscaler could eliminate those 6,697 misses is by maintaining 6–8 workers statically from epoch 0. However:
- Keeping 6–8 workers online during steady state increases worker-seconds by $> 4,000\text{ ws}$, reducing canonical cost savings below $50\%$.
- In v5, cost savings contributed $+1.0 \times \text{Savings\%}$, and dropping below fixed capacity triggered severe penalties.
- Consequently, evolution faced an unresolvable trade-off: either suffer canonical cost destruction or remain pinned at the physical floor of $\approx 6,981\text{ shock misses}$.

### 3.3 Fitness Gradient Flattening
In v5, the shock reward was formulated as:
$$\text{Reward} = 0.20 \times \max(0, 7031 - M_{\text{shock}})$$
Since no policy could achieve fewer than $6,981$ misses without static overprovisioning, the maximum obtainable reward was:
$$0.20 \times (7031 - 6981) = \mathbf{+10.0\text{ points}}$$
This $+10.0\text{ point}$ ceiling was dwarfed by the $+57.44\text{ point}$ canonical cost term and the $-100.0\text{ point}$ penalty per canonical miss. Any mutation that added conservative buffering lost $2 - 4$ points in cost while gaining at most $+0.8$ points on shock misses. As a result, the evolutionary gradient drove all candidates into an identical plateau.

---

## 4. Empirical Ground Truth: Step 8.5 Performance Baseline

Table 2 presents the definitive ground-truth benchmark from Step 8.5 (120 completed simulations) evaluating container startup delays across the authoritative stress triad.

### Table 2: Step 8.5 Multi-Baseline Realism Sensitivity Sweep

| Workload Regime | Startup Delay $T_{\text{boot}}$ (s) | Evolved Conformal v3 (`bbd9b1c2`) | InferLine | Kubernetes HPA | KEDA | Ground Truth Interpretation |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **`suite3_azure`** | 0.5 | **0 misses** ($858\text{ ws}$, 11 flaps) | 5 misses ($1065\text{ ws}$, 88 flaps) | 0 misses ($1999\text{ ws}$, 138 flaps) | 7 misses ($727\text{ ws}$, 88 flaps) | Perfect zero-miss compliance. |
| | 1.0 | **0 misses** ($858\text{ ws}$, 11 flaps) | 5 misses ($1065\text{ ws}$, 88 flaps) | 0 misses ($1999\text{ ws}$, 138 flaps) | 7 misses ($727\text{ ws}$, 88 flaps) | Flawless baseline tracking. |
| | 5.0 | **0 misses** ($858\text{ ws}$, 11 flaps) | 0 misses ($991\text{ ws}$, 51 flaps) | 2 misses ($2004\text{ ws}$, 131 flaps) | 0 misses ($1064\text{ ws}$, 85 flaps) | Resilient absorption. |
| | 15.0 | **0 misses** ($963\text{ ws}$, 13 flaps) | 12 misses ($880\text{ ws}$, 40 flaps) | 249 misses ($1933\text{ ws}$, 139 flaps) | 264 misses ($1266\text{ ws}$, 59 flaps) | Standard controllers begin SLA collapse. |
| | 50.0 | **0 misses** ($1023\text{ ws}$, 15 flaps) | 0 misses ($1089\text{ ws}$, 32 flaps) | 1,410 misses ($2145\text{ ws}$, 70 flaps) | 1,420 misses ($1955\text{ ws}$, 40 flaps) | Massive HPA/KEDA queue starvation. |
| | 100.0–300.0 | **0 misses** ($953\text{ ws}$, 13 flaps) | 0 misses ($1079\text{ ws}$, 30 flaps) | 1,766 misses ($2379\text{ ws}$, 18 flaps) | 1,766 misses ($2335\text{ ws}$, 18 flaps) | **Evolved Conformal beats HPA/KEDA by $>10,000$ misses.** |
| **`suite1_spike`** | 0.5–1.0 | **0 misses** ($848\text{ ws}$, 29 flaps) | 6 misses ($837\text{ ws}$, 66 flaps) | 0 misses ($1455\text{ ws}$, 35 flaps) | 22 misses ($689\text{ ws}$, 103 flaps) | Flawless acute burst handling. |
| | 5.0 | **0 misses** ($848\text{ ws}$, 29 flaps) | 5 misses ($837\text{ ws}$, 58 flaps) | 0 misses ($1455\text{ ws}$, 35 flaps) | 3 misses ($793\text{ ws}$, 89 flaps) | Clean absorption. |
| | 15.0 | **0 misses** ($848\text{ ws}$, 29 flaps) | 0 misses ($791\text{ ws}$, 50 flaps) | 175 misses ($1455\text{ ws}$, 35 flaps) | 193 misses ($1036\text{ ws}$, 78 flaps) | HPA/KEDA suffer severe queue backlog. |
| | 50.0 | **0 misses** ($848\text{ ws}$, 29 flaps) | 0 misses ($868\text{ ws}$, 48 flaps) | 1,098 misses ($1659\text{ ws}$, 18 flaps) | 1,098 misses ($1607\text{ ws}$, 18 flaps) | **$50\times$ boot lag generalization; beats all baselines.** |
| | 100.0–300.0 | 323 misses ($1066\text{ ws}$) | 323 misses ($1175\text{ ws}$) | 1,098 misses ($1659\text{ ws}$, 18 flaps) | 1,098 misses ($1607\text{ ws}$, 18 flaps) | Delayed worker queue buildup. |
| **`suite2_shock`** | 0.5–1.0 | **0 misses** ($1098\text{ ws}$, 21 flaps) | 0 misses ($1098\text{ ws}$, 68 flaps) | 0 misses ($1635\text{ ws}$, 35 flaps) | 25 misses ($1152\text{ ws}$, 128 flaps) | Flawless dual-dimensional tracking. |
| | 5.0 | **0 misses** ($1098\text{ ws}$, 21 flaps) | 3 misses ($1064\text{ ws}$, 42 flaps) | 66 misses ($1635\text{ ws}$, 35 flaps) | 94 misses ($1269\text{ ws}$, 108 flaps) | InferLine, HPA, KEDA all violate SLA. |
| | 15.0 | **11 misses** (P99 $14.0\text{s} \le 15.0\text{s}$) | 11 misses (P99 $14.0\text{s}$) | 687 misses ($1635\text{ ws}$, P99 $38\text{s}$) | 698 misses ($1485\text{ ws}$, P99 $39\text{s}$) | **Graceful compliance at physical tipping point.** |
| | 50.0–300.0 | $1,939 - 2,379\text{ misses}$ | $1,891 - 2,379\text{ misses}$ | $1,371\text{ misses}$ ($1839\text{ ws}$, P99 $72\text{s}$) | $1,371\text{ misses}$ ($1819\text{ ws}$, P99 $72\text{s}$) | Physical dead-time queuing beyond SLA budget. |

---

## 5. The v6 Goto Strategy: v3 Foundation + Grounded Realism Layer

### 5.1 Architecture Overview
The v6 strategy reconciles the proven reliability of v3 with the physical realities uncovered in Step 8.5:
1. **Preserve the Authoritative v3 Canonical Benchmark (Tier 1)**: All 13 canonical regimes evaluated at baseline $T_{\text{init}} = 1.0\text{s}$ ($121,134$ requests).
2. **Layer a Grounded Physical Realism Suite (Tier 2)**: Include 10 regimes testing the operational spectrum where autoscaling is physically operable:
   - `suite3_azure` @ $15\text{s}, 50\text{s}, 150\text{s}, 300\text{s}$ (Diurnal production: tests multi-minute boot resilience).
   - `suite1_spike` @ $5\text{s}, 15\text{s}, 50\text{s}$ (Acute bursts: tests containment up to the $50\text{s}$ tipping point).
   - `suite2_shock` @ $2\text{s}, 5\text{s}, 15\text{s}$ (Opposing semantic shock: tests triage drift containment up to the $15\text{s}$ tipping point).
3. **Seed with Clean v3 Global Champion (`bbd9b1c2`)**: Start Generation 0 directly from the clean, uncorrupted v3 champion law.
4. **Formulate a Balanced, Active Composite Fitness Function $J_{\text{v6}}$**: Anchor to v3's proven Cost-Supreme formula, add a linear realism miss penalty, and reward dominance over InferLine.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 OPENEVOLVE v6 SEARCH PIPELINE                         │
│                                                                                        │
│   Seed Policy: Clean v3 Global Champion (bbd9b1c2)                                    │
│   Population:  Unified Single-Population (Island 0) with Signature Deduplication       │
│   LLM Engine:  Multi-Model Routing (gemini-3.5-flash-lite @ 0.6, temp=0.7)            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: PURE VALIDITY GATE (~0.05s)                                                  │
│  - AST syntax parse & forbidden module audit                                           │
│  - 5 TelemetricState boundary condition tests (quiescent, shock, booting, drain, surge)│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Passed
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: MULTI-STRESS MICRO-TRANCHE GATE (~3.0s)                                      │
│  - suite1_flat @ 1.0s (baseline frugality)                                             │
│  - suite2_shock @ 1.0s (semantic drift response)                                       │
│  - suite2_shock @ 5.0s (moderate startup delay absorption)                             │
│  Filter: Total misses <= 5, Max P99 <= 15.0s, Fitness J >= -100.0                       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Passed
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: FULL DUAL-TIER BENCHMARK (PARALLELIZED ~40s)                                 │
│                                                                                        │
│  ┌────────────────────────────────────────┐  ┌───────────────────────────────────────┐ │
│  │ TIER 1: CANONICAL 13 SUITES (FROM v3)  │  │ TIER 2: PHYSICAL REALISM SUITES       │ │
│  │ Baseline T_init = 1.0s                 │  │ Grounded in Step 8.5 Tipping Points   │ │
│  │ 1. suite1_flat       8. suite2_relief  │  │ 1. suite3_azure @ 15s, 50s, 150s, 300s │ │
│  │ 2. suite1_spike      9. suite2_decouple│  │    (diurnal multi-minute boots)       │ │
│  │ 3. suite1_burst     10. suite2_storm   │  │ 2. suite1_spike @ 5s, 15s, 50s         │ │
│  │ 4. suite1_ramp      11. suite1_zero_beg│  │    (acute burst tipping points)       │ │
│  │ 5. suite1_zero_term 12. suite2_stress  │  │ 3. suite2_shock @ 2s, 5s, 15s          │ │
│  │ 6. suite2_shock     13. suite3_azure   │  │    (semantic collapse tipping points) │ │
│  │ 7. suite2_recovery                     │  │                                       │ │
│  │ Total: 121,134 requests                │  │ Seed Expected: ~11 misses total       │ │
│  │ Seed Baseline: 0 misses, 57.44% savings│  │ InferLine: ~45 | HPA: >4k | KEDA: >4k │ │
│  └────────────────────────────────────────┘  └───────────────────────────────────────┘ │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  COMPOSITE FITNESS J_v6 CALCULATION & SIGNATURE DEDUPLICATION                          │
│  J_v6 = J_v3_core(Tier 1) + J_realism(Tier 2) + Baseline_Dominance_Bonus               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Mathematical Specification of Composite Fitness $J_{\text{v6}}$

The fitness function seamlessly integrates the proven v3 criteria with the Tier 2 realism expansion:

$$J_{\text{v6}} = J_{\text{v3\_core}} + J_{\text{realism}} + B_{\text{dominance}}$$

### 6.1 Component 1: $J_{\text{v3\_core}}$ (Tier 1 Canonical 13 Regimes)
Directly inherits the v3 Cost-Supreme criteria:
$$\text{CostSavings\%} = \left(1.0 - \frac{\text{WorkerSeconds}_{\text{canon}}}{27,900.0}\right) \times 100.0$$
$$\text{MissPenalty}_{\text{canon}} = 2.0 \times \min(M_{\text{canon}}, 10.0) + 20.0 \times \max(0.0, M_{\text{canon}} - 10.0)$$
$$\text{P99Penalty}_{\text{canon}} = 10.0 \times \max(0.0, P99_{\text{canon}} - 6.0)$$
$$\text{ChurnPenalty}_{\text{canon}} = 0.01 \times \Delta_{\text{canon}}$$
$$J_{\text{v3\_core}} = \text{CostSavings\%} - \text{MissPenalty}_{\text{canon}} - \text{P99Penalty}_{\text{canon}} - \text{ChurnPenalty}_{\text{canon}}$$

### 6.2 Component 2: $J_{\text{realism}}$ (Tier 2 Physical Realism Triad)
Active, non-flattened gradient rewarding shock containment:
$$J_{\text{realism}} = -1.0 \times M_{\text{realism}} - 5.0 \times \max(0.0, P99_{\text{realism}} - 15.0)$$
- For the v3 Seed Baseline ($M_{\text{realism}} \approx 11$ misses), this deducts only $-11.0\text{ points}$.
- A candidate that successfully eliminates the 11 misses on `suite2_shock @ 15s` gains $+11.0\text{ points}$.
- Any candidate suffering hundreds of misses is decisively penalized.

### 6.3 Component 3: $B_{\text{dominance}}$ (Industry Baseline Dominance Bonus)
Awards explicit credit for beating established controllers across both cost and SLA compliance:
$$B_{\text{dominance}} = B_{\text{canon\_inferline}} + B_{\text{realism\_inferline}}$$
Where:
$$B_{\text{canon\_inferline}} = \begin{cases} 
+10.0 & \text{if } M_{\text{canon}} = 0 \text{ and } \text{Cost}_{\text{canon}} < 14,261.0\text{ ws} \\
0 & \text{otherwise}
\end{cases}$$
$$B_{\text{realism\_inferline}} = \begin{cases} 
+10.0 & \text{if } M_{\text{realism}} < 45 \text{ and } \text{Cost}_{\text{realism}} < \text{Cost}_{\text{InferLine, realism}} \\
0 & \text{otherwise}
\end{cases}$$

### 6.4 Expected Fitness Baseline for Clean Seed (`bbd9b1c2`)
- $\text{CostSavings\%}$: $+57.44$
- $\text{MissPenalty}_{\text{canon}}$: $0.0$ ($0$ misses)
- $\text{P99Penalty}_{\text{canon}}$: $0.0$ ($P99 = 6.0\text{s}$)
- $\text{ChurnPenalty}_{\text{canon}}$: $-2.27$ ($227$ flaps)
- $J_{\text{realism}}$: $-11.0$ ($11$ misses on shock @ 15s)
- $B_{\text{canon\_inferline}}$: $+10.0$ ($11,874\text{ ws} < 14,261\text{ ws}$)
- $B_{\text{realism\_inferline}}$: $+10.0$ ($11\text{ misses} < 45\text{ misses}$)
$$\mathbf{J_{\text{v6, seed}} \approx 57.44 - 0.0 - 0.0 - 2.27 - 11.00 + 10.00 + 10.00 = +64.17}$$

---

## 7. LLM Prompt Directives & Physical Grounding

To prevent the LLM from generating ineffective micro-tweaks or hallucinating unbootable strategies, the prompt in `configs/evolution/openevolve_config_v6.yaml` is grounded in physical causality:

1. **Explicit Causal Signals**:
   - `p_fast_velocity`: Rate of semantic triage change over a 3-epoch window. A negative velocity ($< -0.05$) signals that edge triage is collapsing and cloud traffic will surge within 1–2 seconds.
   - `cloud_queue_velocity`: Rate of backlog change ($dQ/dt$). Differentiates transient Poisson noise from accumulating queues.
   - `oldest_task_age_s`: Proximity of head-of-line requests to the $15.0\text{s}$ SLA budget.
   - `booting_workers`: Number of instances already spinning up.
2. **Physical Delay Awareness**:
   - Explicitly instructs the LLM that containers take $2\text{s} - 50\text{s}$ to boot. During this dead time, newly ordered workers cannot process requests.
   - Instructs the LLM to modulate the booting credit dynamically: discount booting workers when $dQ/dt > 0$ or oldest task age $> 2.0\text{s}$ (accelerating scale-up), but retain full booting credit during steady state.
   - Emphasizes that steady-state overprovisioning must be avoided to preserve $> 50\%$ canonical savings.

---

## 8. Implementation & Verification Protocol

### 8.1 Dedicated Versioned Files (`AGENTS.md` Rule 1)
- `src/continuum_ext/evolution/seed_policy_v6.py`: Clean v3 Champion (`bbd9b1c2`).
- `src/continuum_ext/evolution/openevolve_evaluator_v6.py`: Parallelized dual-tier evaluator.
- `configs/evolution/openevolve_config_v6.yaml`: Grounded configuration and prompt.
- `scripts/run_evolution_v6.py`: Main CLI runner.
- `scripts/run_unattended_v6.py`: Unattended daemon with auto-recovery and top-30 variant extraction.

### 8.2 Execution & Verification Roadmap
1. **Stage 1 & 2 Verification**: Unit-test AST safety, boundary contracts, and micro-tranche execution using `./.venv/bin/python`.
2. **Stage 3 Baseline Verification**: Run `seed_policy_v6.py` through Stage 3 to verify:
   - Canonical misses $= 0$.
   - Canonical savings $> 50\%$.
   - Realism misses $\le 15$.
   - Baseline fitness $J_{\text{v6}} \approx +64.17$.
3. **Local 3-Iteration Dry Run**: Verify end-to-end prompt formatting, LLM mutation, candidate scoring, and leaderboard generation.
4. **Local Git Commit**: Commit all new files locally (**strictly zero git push**).
5. **Codespace Deployment Bundle**: Package clean launch scripts for unattended long-horizon search.

---

## 9. Cloned Repositories Compliance Audit & Logical Pitfalls Prevention

To guarantee absolute scientific integrity and operational stability, we conducted an exhaustive audit of all cloned dependencies (`clones/ContinuumBench`, `clones/eclypse`, `clones/openevolve`):

### 9.1 Cloned Repositories Audit
1. **`ContinuumBench` (`clones/ContinuumBench/`)**:
   - **Contract & Interface**: Extends `extensions_local.py` via `build()` hook as recommended in upstream documentation (`src/continuum_bench/controllers/README.md`). Zero monkey-patching of core packages.
   - **Zero Oracle Leakage (`AGENTS.md` Rule 5)**: `evolved_conformal` receives only causally observable metrics via `TelemetricState` (arrival rates, queue depths, sliding-window velocities, active workers, booting workers). No controller accesses future arrivals, internal simulator metadata, or ground-truth startup delays.
   - **Enterprise Baseline Gating**: Enforces `min_workers: 1` on `CloudRefine` and `min_replicas: 1` across autoscalers to prevent artificial scale-to-zero queue traps.
2. **`eclypse` (`clones/eclypse/`)**:
   - Substrate pinned to 0.8.1. All substrate models (service graphs, node resource capacities, placement audits) are executed via Eclypse primitives without mutating internal runtime state.
3. **`openevolve` (`clones/openevolve/`)**:
   - Cascade evaluation protocol (`evaluator.cascade_evaluation: true`) strictly expects `evaluate_stage1`, `evaluate_stage2`, and `evaluate_stage3` returning `EvaluationResult(metrics=..., artifacts=...)`.
   - All entries in `metrics` are sanitized and explicitly cast to Python `float`.
   - Primary ranking metric is `combined_score`.
   - Diff-based evolution enforces `# EVOLVE-BLOCK-START` and `# EVOLVE-BLOCK-END` delimiters.

### 9.2 Logical & Common-Sense Pitfalls Addressed
1. **Disk Space Exhaustion Prevention**: Raw simulation directories generate ~20 MB of epoch logs per candidate. In v6, simulation directories are pruned immediately after extracting `summary.json`, preventing disk-full crashes during 150-iteration Codespace runs.
2. **Infinite Loop / Re-entrant Guard**: Candidate policies are algebraically closed formulas. Stage 1 AST inspection explicitly forbids `While` AST nodes to prevent non-terminating loops.
3. **Division-by-Zero Protection**: Stage 1 executes 5 diverse stress boundary tests (quiescent, saturation shock, booting in flight, negative velocity, zero ingress). Any exception (such as `ZeroDivisionError` on `drain_window`) rejects the candidate in $<0.05\text{s}$ before entering costly simulations.
4. **Signature Deduplication Gating**: Retains strict signature hashing (`sig_key = f"{cost:.1f}_{canon_misses}_{realism_misses}_{deltas}"`) to prevent stagnation in MAP-Elites.

---

## 10. The Definitive Pre-Flight Implementation Checklist for v6

- [ ] **1. Environment Verification**: Workspace venv `./.venv/bin/python` verified with `continuum_bench`, `openevolve`, and `eclypse`.
- [ ] **2. Version Immutability (`AGENTS.md` Rule 1)**: All existing v5 files (`openevolve_evaluator_v5.py`, `openevolve_config_v5.yaml`, `seed_policy_v5.py`) preserved untouched.
- [ ] **3. Seed Policy Initialization**: `src/continuum_ext/evolution/seed_policy_v6.py` initialized from clean v3 Champion (`bbd9b1c2`).
- [ ] **4. Parallel Evaluator Engine**: `src/continuum_ext/evolution/openevolve_evaluator_v6.py` implements Stage 1 AST purity + While-guard + 5 boundary unit tests; Stage 2 micro-tranche filter; and Stage 3 parallel dual-tier benchmark with ephemeral disk cleanup.
- [ ] **5. Config & Prompt Grounding**: `configs/evolution/openevolve_config_v6.yaml` configures multi-model routing and physically grounded prompt directives.
- [ ] **6. Unattended CLI Harness**: `scripts/run_evolution_v6.py` and `scripts/run_unattended_v6.py` implemented with automated top-30 variant extraction.
- [ ] **7. Automated Unit Verification**: Seed passes Stage 1, Stage 2, and Stage 3 with 0 canonical misses, $>50\%$ cost savings, and $\le 15$ realism misses.
- [ ] **8. 3-Iteration Dry Run**: Validates mutation pipeline, logging, and leaderboard generation locally.
- [ ] **9. Local Git Commit**: Commit all new files locally (**STRICTLY ZERO GIT PUSH**).
- [ ] **10. Codespace Deployment Packaging**: Provide clean launch command for unattended Codespace execution.

---

## 11. Conclusion

By grounding the evaluation framework in the empirical tipping points discovered in Step 8.5, restoring the proven v3 canonical criteria, and initializing from the clean v3 Global Champion, **OpenEvolve v6** breaks free from the dead-time queuing deadlock of v5. It provides a true, active evolutionary gradient that empowers the search to discover deployably robust autoscaling laws that conquer real-world container startup delays while cementing cost supremacy.
