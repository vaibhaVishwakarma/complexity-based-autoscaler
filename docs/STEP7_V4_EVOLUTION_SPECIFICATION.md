# Step 7 v4: Pareto-Optimal (Cost-Supreme + Tail Latency) Evolution Specification

*Version:* 1.0  
*Date:* 2026-10-06  
*Status:* Draft / Ready for Execution  
*Branch:* `v4-evolution`  
*Target Champion Seed:* `bbd9b1c2` (Discovered in v3, 57.44% cost savings, 0 misses, 6.00s max P99)

---

## 1. Executive Summary & Problem Formulation

In Step 7 v3, OpenEvolve discovered the **Cost-Supreme Champion** (`bbd9b1c2`), which achieved:
- **$57.44\%$ cost savings** vs Fixed Capacity ($11,874\text{ worker-seconds}$ vs $27,900\text{ ws}$).
- **Zero deadline misses** across all $13$ stress regimes ($0 / 121,134$ requests).
- **$228$ scaling deltas** ($73.3\%$ fewer actuations than InferLine).
- **Max P99 tail latency**: $6.00\text{s}$ (well within the $15.0\text{s}$ SLA deadline).

### The Motivation for Version 4
While v3 proved that the Conformal Autoscaler vastly outperforms InferLine in cost, zero-miss reliability, and stability, its P99 tail latency in sudden shock/burst regimes (`suite1_spike` at $6.0\text{s}$, `suite1_burst` at $5.4\text{s}$) reached the $6.0\text{s}$ envelope. 

The objective of **Version 4** is to explore the Pareto frontier between cost and latency:
> **Core Objective**: Retain the champion's $> 55\%$ cost savings and $100\%$ zero-miss SLA compliance while guiding mutations to actively suppress tail latency spikes, driving maximum P99 latency across all regimes from $6.00\text{s}$ down to $\le 5.00\text{s}$.

---

## 2. Mathematical Fitness Function Formulation ($J_{v4}$)

The fitness metric $J_{v4}$ balances base cost dominance with a steep gradient penalizing tail latency spikes and deadline misses:

$$J_{v4} = S_{\text{cost}} - P_{\text{miss}} - P_{p99} - P_{\text{churn}} + B_{\text{tail}}$$

### 1. Cost Savings Foundation ($S_{\text{cost}}$)
$$S_{\text{cost}} = \left(1.0 - \frac{\text{total\_worker\_seconds}}{27,900.0}\right) \times 100.0$$
Provides $+1.0$ point per $1\%$ cost savings vs Fixed Capacity ($27,900.0\text{ ws}$).

### 2. Zero-Tolerance Deadline Miss Penalty ($P_{\text{miss}}$)
$$P_{\text{miss}} = 3.0 \times \min(M, 50.0) + 15.0 \times \max(0.0, M - 50.0)$$
Guarantees that any policy permitting SLA violations ($M > 0$) is immediately purged from the elite pool.

### 3. Tail Latency Suppression Penalty ($P_{p99}$)
Unlike v3 (which used a relaxed $6.0\text{s}$ baseline), v4 tightens the target envelope to $5.00\text{s}$ (the empirical lower latency bound in ContinuumBench):
$$P_{p99} = 15.0 \times \max(0.0, \text{max\_p99\_s} - 5.0) + 5.0 \times \max(0.0, \text{mean\_p99\_s} - 4.8)$$

**Gradient Analysis**:
- Seed `bbd9b1c2` has $\text{max\_p99} = 6.00\text{s}$. Its penalty is $15.0 \times (6.0 - 5.0) = 15.0$ points.
- A mutant policy that injects preemptive surge provisioning during spikes (spending $\sim 150$ extra worker-seconds $\approx 0.54\%$ cost savings) achieves $\text{max\_p99} \le 5.00\text{s}$.
- Net fitness impact:
  $$\Delta J = -0.54 + 15.0 = +14.46\text{ points}$$
This provides a decisive optimization gradient for tail latency reduction without sacrificing steady-state frugality!

### 4. Continuous Sub-5.0s Tail Bonus ($B_{\text{tail}}$)
$$B_{\text{tail}} = 2.0 \times \max(0.0, 5.0 - \text{mean\_p99\_s})$$
Rewards policies that achieve tight queuing delays across all 13 regimes.

### 5. Actuation Churn Penalty ($P_{\text{churn}}$)
$$P_{\text{churn}} = 0.01 \times \text{total\_deltas}$$

---

## 3. Asymmetric Island Topology & Directed Mutation Prompts

OpenEvolve v4 configures three specialized research islands in `configs/evolution/openevolve_config_v4.yaml`:

| Island | Role / Specialization | Key Telemetric Causal Signals | Directed Mutation Strategy |
| :---: | :--- | :--- | :--- |
| **Island 0** | **Core Conformal Branch** | `p_fast`, `ingress_rps`, `mean_set_size` | Preserves lean steady-state cost; dynamically shortens drain window during detected surges. |
| **Island 1** | **Acceleration & Causal Dynamics** | `ingress_acceleration`, `cloud_queue_velocity` | Detects sudden step-surges ($d^2\lambda/dt^2$) and pre-emptively provisions before queue delay accumulates. |
| **Island 2** | **Task-Age Urgency & Drain Hybrid** | `oldest_task_age_s`, `cloud_queue_depth` | Modulates queue drain window dynamically based on head-of-line task aging. |

---

## 4. Multi-Key API Quota Auto-Rotation

To prevent evolution interruptions due to Gemini API rate limits or quota exhaustion:
1. **Dynamic Key Pool**: Keys are stored in `.env.backup` with masked telemetry logging.
2. **Pre-Flight Health Verification**: `scratch/run_evolution_v4.py` checks the active key via ping before starting and auto-selects the first working key.
3. **In-Flight Quota Recovery**: OpenEvolve's OpenAI-compatible interface is patched to catch HTTP 429 (`resource_exhausted`) and seamlessly rotate to the next backup key without losing iteration progress.

---

## 4.1. Real-Time Resource & Code Mutation Churn Monitoring

OpenEvolve v4 introduces full-spectrum telemetric tracking recorded to `output/evolution_runs_v4/evolution_telemetry_summary.json` and mirrored in real time to [`docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md`](file:///home/vaibo/edgecompute/docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md):

1. **LLM Token Consumption**:
   - **Prompt Tokens**: Input context, candidate code, evaluation artifacts, and system instructions.
   - **Completion Tokens**: Generated diff blocks, reasoning thoughts, and mutation explanations.
   - **Total Tokens Consumed**: Cumulative sum across all iterations.
   - **Model Breakdown**: Per-model consumption across `gemini-3.5-flash-lite`, `gemini-flash-lite-latest`, and `gemini-3-flash-preview`.
2. **Code Mutation Churn**:
   - **Lines Added (`+`)**: Total number of code lines inserted across all mutation events.
   - **Lines Deleted (`-`)**: Total number of code lines pruned/replaced across all mutation events.
   - **Net Line Delta**: Cumulative net growth or shrinkage of evolved policy codebases.
   - **Mutation Edit Hunks**: Total count of atomic search/replace unified diff patches synthesized and validated.

---

## 5. Execution Commands

### In Development / Verification
```bash
# Verify Stage 1 AST and boundary tests:
./.venv/bin/python -c "from continuum_ext.evolution.openevolve_evaluator_v4 import evaluate_stage1; evaluate_stage1('src/continuum_ext/evolution/seed_policy_v4.py')"

# Run a 2-iteration dry-run:
./.venv/bin/python scratch/run_evolution_v4.py --dry-run
```

### Full Production Evolution (Unattended)
```bash
nohup ./.venv/bin/python scratch/run_evolution_v4.py --iterations 200 > evolution_v4.log 2>&1 &
```
Real-time discovery metrics, token consumption, code churn, and policy comparisons are automatically synced to [`docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md`](file:///home/vaibo/edgecompute/docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V4.md).

