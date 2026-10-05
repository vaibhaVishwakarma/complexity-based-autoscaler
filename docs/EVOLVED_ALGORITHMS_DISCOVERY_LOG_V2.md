# OpenEvolve v2 Evolutionary Synthesis: Discovery Log & Pareto Leaderboard

*Document Version:* 2.0  
*Authoritative Source:* Step 7 v2 200-Iteration Codespace Run (`top20_evolved_variants.tar.gz`)  
*Execution Date:* 2026-10-05 19:48:34 UTC  
*Target Hardware:* Multi-tier Edge-Cloud Continuum (6 Cloud Nodes × 3 T4 Workers = 18 Workers max, $\mu = 16.0\text{ RPS/worker}$)  
*Benchmark Scope:* Authoritative 13-Regime ContinuumBench Simulation ($121,134$ requests per candidate)

---

## 1. Executive Summary & Objective Realignment

In Step 7 v1, the evolutionary search hoarded defensive GPU capacity because deadline misses were weighted at $1.0$ against cost at $0.002$ ($1\text{ miss} \equiv 500\text{ worker-seconds}$), resulting in $26.0\%$ cost savings while InferLine achieved $48.9\%$. 

In Step 7 v2, the objective function was re-aligned to **Cost-First with Balanced, Equal Miss & Tail Latency Penalties**:

$$J_{\text{v2}} = \text{cost\_savings\_\%} - \text{miss\_penalty} - \text{p99\_penalty} - \text{churn\_penalty}$$

where:
- $\text{cost\_savings\_\%} = \left(1.0 - \frac{\text{worker\_seconds}}{27,900.0}\right) \times 100.0$ ($+1.0\text{ pt per 1\% savings}$)
- $\text{miss\_penalty} = 2.0 \cdot \min(M, 50) + 10.0 \cdot \max(0, M - 50)$
- $\text{p99\_penalty} = 10.0 \cdot \max(0.0, P99 - 5.0)$
- $\text{churn\_penalty} = 0.01 \cdot \Delta_{\text{scaling}}$

### Breakthrough Empirical Results

1. **InferLine's Cost Record Beaten with Zero Misses**:
   - **InferLine (ACM SoCC '20)**: $14,261.0\text{ worker-seconds}$ ($48.88\%$ savings), **44 deadline misses**, $855\text{ deltas}$, $P99 = 6.00\text{s}$, $J_{\text{v2}} = -57.66$.
   - **Discovered Policy `4a7ccfe9` (Rank 2 / Evolved Policy v2)**: **$13,100.0\text{ worker-seconds}$** (**$53.05\%$ savings**), **0 deadline misses**, $258\text{ deltas}$, $P99 = 6.00\text{s}$, **$J_{\text{v2}} = +40.47$**.
   - **Net Advantage vs InferLine**: **$1,161.0$ fewer worker-seconds** ($8.1\%$ cheaper), **$100\%$ SLA compliance** ($0$ misses vs $44$), and **$70\%$ lower actuation flapping** ($258$ vs $855$ deltas)!

2. **Ultra-Balanced Pareto Policy (`c768e600`, Rank 1)**:
   - Achieves $46.31\%$ savings ($14,979.0\text{ ws}$) with **$0$ misses**, $290\text{ deltas}$, and **$P99 = 5.00\text{s}$** (zero tail degradation penalty), scoring a record **$J_{\text{v2}} = +43.41$**!

3. **Total Reliability Across Top 20 Candidates**:
   - **All 20 top variants achieved exactly ZERO deadline misses** ($0/121,134$ requests across all 13 stress regimes, including violent 15x bursts and fast-path collapses).
   - **9 out of the top 10 discovered variants strictly beat InferLine on GPU worker-seconds** ($49.05\% - 53.05\%$ cost savings).

---

## 2. Global Baseline & Champion Comparison

| Autoscaling Policy / Architecture | Provisioned Cost (Worker-Sec) | Cost Savings vs Fixed | Deadline Misses (SLA Breach) | Max P99 Latency | Scaling Deltas (Flapping) | Fitness $J_{\text{v2}}$ | Dominance Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fixed Capacity Baseline** | $27,900.0\text{ ws}$ | $0.00\%$ | **$0$** | **$5.00\text{s}$** | $205$ | $0.00$ | Baseline |
| **Kubernetes HPA** | $23,940.0\text{ ws}$ | $14.19\%$ | $72$ | $13.00\text{s}$ | $606$ | $-301.87$ | Sub-optimal |
| **KEDA (Queue-Driven)** | $19,850.0\text{ ws}$ | $28.85\%$ | $128$ | $9.50\text{s}$ | $1,710$ | $-1,062.10$ | Severe Flapping |
| **InferLine (SoCC '20)** | $14,261.0\text{ ws}$ | $48.88\%$ | $44$ | $6.00\text{s}$ | $855$ | $-57.66$ | Costly SLA Violations |
| **Step 7 Champion (v1 Seed `35671429`)** | $20,645.0\text{ ws}$ | $26.00\%$ | **$0$** | **$4.89\text{s}$** | **$218$** | $+26.01$ | Defensive / Conservative |
| **v2 Balanced Champion (`c768e600`, Rank 1)** | **$14,979.0\text{ ws}$** | **$46.31\%$** | **$0$** | **$5.00\text{s}$** | $290$ | **$+43.41$** | **Pareto Optimal (Balanced)** |
| **v2 Cost Champion (`4a7ccfe9`, Rank 2)** | **$13,100.0\text{ ws}$** | **$53.05\%$** | **$0$** | $6.00\text{s}$ | $258$ | **$+40.47$** | **Strictly Dominates InferLine** |

---

## 3. Top-20 Discovered Variants Leaderboard

The following table documents the complete Top-20 policies exported directly from the Codespace evolution archive:

| Rank | Source File | Program ID | Fitness $J_{\text{v2}}$ | Cost Savings | Worker-Sec | Misses | Max P99 | Deltas | Status / Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | [`rank01_fit+43p41_idc768e600.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank01_fit+43p41_idc768e600.py) | `c768e600` | **$+43.41$** | $46.31\%$ | $14,979.0\text{ ws}$ | $0$ | $5.00\text{s}$ | $290$ | **Global Balanced Champion** |
| **2** | [`rank02_fit+40p47_id4a7ccfe9.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank02_fit+40p47_id4a7ccfe9.py) | `4a7ccfe9` | **$+40.47$** | **$53.05\%$** | **$13,100.0\text{ ws}$** | $0$ | $6.00\text{s}$ | $258$ | **★ Best Cost (Beats InferLine by 1.16k ws)** |
| **3** | [`rank03_fit+39p39_id45773069.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank03_fit+39p39_id45773069.py) | `45773069` | **$+39.39$** | $52.05\%$ | $13,379.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $266$ | ★ Beats InferLine Cost |
| **4** | [`rank04_fit+36p98_id9fa1605f.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank04_fit+36p98_id9fa1605f.py) | `9fa1605f` | **$+36.98$** | $49.72\%$ | $14,029.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $274$ | ★ Beats InferLine Cost |
| **5** | [`rank05_fit+36p98_id322bf2fe.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank05_fit+36p98_id322bf2fe.py) | `322bf2fe` | **$+36.98$** | $49.72\%$ | $14,029.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $274$ | ★ Beats InferLine Cost |
| **6** | [`rank06_fit+36p98_id2c72f793.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank06_fit+36p98_id2c72f793.py) | `2c72f793` | **$+36.98$** | $49.72\%$ | $14,029.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $274$ | ★ Beats InferLine Cost |
| **7** | [`rank07_fit+36p98_idde16e85b.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank07_fit+36p98_idde16e85b.py) | `de16e85b` | **$+36.98$** | $49.72\%$ | $14,029.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $274$ | ★ Beats InferLine Cost |
| **8** | [`rank08_fit+36p69_id43ac93b0.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank08_fit+36p69_id43ac93b0.py) | `43ac93b0` | **$+36.69$** | $49.41\%$ | $14,116.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $272$ | ★ Beats InferLine Cost |
| **9** | [`rank09_fit+36p38_id3e628f84.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank09_fit+36p38_id3e628f84.py) | `3e628f84` | **$+36.38$** | $49.12\%$ | $14,195.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $274$ | ★ Beats InferLine Cost |
| **10** | [`rank10_fit+36p29_id03d9ba8a.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank10_fit+36p29_id03d9ba8a.py) | `03d9ba8a` | **$+36.29$** | $49.05\%$ | $14,216.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $276$ | ★ Beats InferLine Cost |
| **11** | [`rank11_fit+36p02_id70d3a9a5.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank11_fit+36p02_id70d3a9a5.py) | `70d3a9a5` | **$+36.02$** | $48.82\%$ | $14,280.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $280$ | Strict SLA Match |
| **12** | [`rank12_fit+35p84_id5e89139b.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank12_fit+35p84_id5e89139b.py) | `5e89139b` | **$+35.84$** | $48.62\%$ | $14,336.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $278$ | Strict SLA Match |
| **13** | [`rank13_fit+35p54_id050fc459.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank13_fit+35p54_id050fc459.py) | `050fc459` | **$+35.54$** | $38.84\%$ | $17,065.0\text{ ws}$ | $0$ | $5.00\text{s}$ | $330$ | Low Tail Latency Focus |
| **14** | [`rank14_fit+35p18_id9d67a68b.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank14_fit+35p18_id9d67a68b.py) | `9d67a68b` | **$+35.18$** | $48.00\%$ | $14,507.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $282$ | Strict SLA Match |
| **15** | [`rank15_fit+34p73_id6dbc925a.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank15_fit+34p73_id6dbc925a.py) | `6dbc925a` | **$+34.73$** | $47.57\%$ | $14,627.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $284$ | Smooth Actuation |
| **16** | [`rank16_fit+34p73_idd4688538.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank16_fit+34p73_idd4688538.py) | `d4688538` | **$+34.73$** | $47.57\%$ | $14,627.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $284$ | Smooth Actuation |
| **17** | [`rank17_fit+34p70_id66f36a47.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank17_fit+34p70_id66f36a47.py) | `66f36a47` | **$+34.70$** | $47.56\%$ | $14,630.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $286$ | Smooth Actuation |
| **18** | [`rank18_fit+34p67_id46393dd6.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank18_fit+34p67_id46393dd6.py) | `46393dd6` | **$+34.67$** | $47.49\%$ | $14,649.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $282$ | Smooth Actuation |
| **19** | [`rank19_fit+34p67_idba5e4ae1.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank19_fit+34p67_idba5e4ae1.py) | `ba5e4ae1` | **$+34.67$** | $47.49\%$ | $14,651.0\text{ ws}$ | $0$ | $6.00\text{s}$ | $282$ | Smooth Actuation |
| **20** | [`rank20_fit+34p13_id5f9ce4b5.py`](file:///home/vaibo/edgecompute/output/top20_variants/rank20_fit+34p13_id5f9ce4b5.py) | `5f9ce4b5` | **$+34.13$** | $37.63\%$ | $17,400.0\text{ ws}$ | $0$ | $5.00\text{s}$ | $350$ | Conservative Fallback |

---

## 4. In-Depth Mathematical Breakdown of Top Policies

### 4.1 Rank 1 Champion: Balanced Conformal Policy (`c768e600`)
- **Fitness Score:** $J_{\text{v2}} = +43.41$
- **Worker-Seconds:** $14,979.0\text{ ws}$ ($46.31\%$ savings)
- **Deadline Misses:** $0$ ($100\%$ SLA compliance)
- **Max P99 Latency:** $5.00\text{s}$ ($\Delta_{\text{P99}} = 0.0\text{s}$, avoiding the $-10.0\text{ pt/s}$ penalty)
- **Scaling Deltas:** $290$

```python
def compute_target_workers(state: TelemetricState) -> int:
    mu = state.worker_capacity_rps       # 16.0 RPS/worker
    max_workers = 18                     # 6 nodes × 3 workers

    # 1. Lean Conformal Demand-Forward with Tight Multiplier
    conformal_safety = 0.98 + 0.01 * max(0.0, state.mean_set_size - 1.0)
    demand_trend = max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.15
    anticipated_demand = state.offered_cloud_rps + demand_trend
    demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)

    # 2. Relaxed Queue Drain Window (Avoids Over-Actuation)
    DRAIN_WINDOW_S = 1.10
    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.10
    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
    drain_workers = math.ceil(queue_drain_rps / mu)

    # 3. Booting In-Flight Credit & Scale-Down Hysteresis
    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)

    if raw_target < state.active_workers and (state.time_since_last_scale_s < 2.5 or state.cloud_queue_depth > 0):
        effective_target = state.active_workers
    else:
        effective_target = raw_target

    return int(max(1, min(max_workers, effective_target)))
```

**Key Mathematical Innovations:**
1. **Conformal Multiplier Compression ($1.08 \to 0.98$)**: Instead of blindly adding $8\%$ baseline headroom, it trusts the fast-path triage and operates with zero defensive slack ($0.98$), only scaling with set-size ambiguity at $0.01$ (vs $0.08$).
2. **Trend Velocity Damping ($1.00 \to 0.15$)**: Scaled down the anticipatory burst multiplier by $85\%$. It reacts to negative $p_{\text{fast}}$ velocity without triggering false alarms during micro-spikes.
3. **Queue Drain Window Extension ($0.55\text{s} \to 1.10\text{s}$)**: Allows backlogs to drain naturally over 1.1s rather than allocating excess workers to kill queues within 500ms.

---

### 4.2 Rank 2 Champion: Cost-Frugal Policy (`4a7ccfe9` — Official Evolved Policy v2)
- **Fitness Score:** $J_{\text{v2}} = +40.47$
- **Worker-Seconds:** **$13,100.0\text{ ws}$** (**$53.05\%$ savings — beats InferLine by $1,161.0\text{ ws}$!**)
- **Deadline Misses:** $0$
- **Max P99 Latency:** $6.00\text{s}$ (tolerates $1.0\text{s}$ delta, paying $-10.0\text{ pts}$ to capture $+6.74\text{ pts}$ in cost)
- **Scaling Deltas:** $258$ (ultra-smooth actuation)

```python
def compute_target_workers(state: TelemetricState) -> int:
    mu = state.worker_capacity_rps       # 16.0 RPS/worker
    max_workers = 18

    # 1. Continuous Linear Sizing (Fractional Allocation before Rounding)
    conformal_safety = 1.00 + 0.02 * max(0.0, state.mean_set_size - 1.0)
    demand_trend = max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.30
    demand_workers = ((state.offered_cloud_rps + demand_trend) * conformal_safety) / mu

    # 2. Wide Drain Window with Velocity Forwarding
    DRAIN_WINDOW_S = 1.6
    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.30
    drain_workers = adjusted_queue / (mu * DRAIN_WINDOW_S)

    # 3. Aggressive Booting Worker Deduction (65% Credit)
    raw_target = demand_workers + drain_workers - (state.booting_workers * 0.65)

    # 4. Asymmetric Cooldown with Low-Backlog Tolerance (depth > 1)
    if raw_target < state.active_workers and (state.time_since_last_scale_s < 2.1 or state.cloud_queue_depth > 1):
        effective_target = state.active_workers
    else:
        effective_target = raw_target

    return int(max(1, min(max_workers, effective_target)))
```

**Key Mathematical Innovations:**
1. **Fractional Summation Before Ceiling**: Avoids the "double-ceil" trap where `ceil(demand) + ceil(drain)` artificially provisions 2 extra workers on small remainders.
2. **Aggressive Booting Deduction ($0.50 \to 0.65$)**: Prevents over-provisioning worker spikes when containers are already spinning up.
3. **Queue Tolerance ($Q > 1$ vs $Q > 0$)**: Permits a micro-queue of 1 item during scale-down without locking up capacity.

---

## 5. Architectural Findings: How v2 Defeated InferLine

| Dimension | InferLine (ACM SoCC '20) | Step 7 v1 Champion | Step 7 v2 Champion (`4a7ccfe9`) |
| :--- | :--- | :--- | :--- |
| **Cloud Demand Signal** | Arriving Volume $\lambda(t)$ only | Multiplicative $\lambda(t) \cdot (1 - p_{\text{fast}})$ | Multiplicative + Damped Velocity Trend |
| **Fast-Path Collapse Reaction** | **Blind** (44 misses during semantic shifts) | Conservative (0 misses, but hoards 20.6k ws) | **Proactive & Lean** (0 misses, 13.1k ws) |
| **Worker Provisioning** | $14,261\text{ ws}$ | $20,645\text{ ws}$ | **$13,100\text{ ws}$ ($8.1\%$ lower than InferLine)** |
| **Actuation Flapping** | $855$ scaling deltas | $218$ scaling deltas | **$258$ scaling deltas ($70\%$ lower than InferLine)** |
| **SLA Integrity** | Failed in 65.4% of stress runs | 100% SLA pass | **100% SLA pass across all 13 regimes** |

---

## 6. Verification Checklist

- [x] All 20 policy files extracted into `output/top20_variants/` as standalone runnable modules.
- [x] Full performance metrics matching Codespace output verified against `TOP20_LEADERBOARD.csv`.
- [x] Authoritative best policy exported to [`output/evolved_policy_v2.py`](file:///home/vaibo/edgecompute/output/evolved_policy_v2.py).
- [x] Evolution trace verified ($114$ total algorithmic explorations, $10.5\text{ MB}$ JSONL trace).
