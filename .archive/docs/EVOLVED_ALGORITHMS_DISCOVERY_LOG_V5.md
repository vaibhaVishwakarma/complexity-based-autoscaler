# OpenEvolve v5 Realism-Aware Evolutionary Search: Discovery Log & Leaderboard

*Generated on: 2026-10-07 19:37:22 UTC*

## 1. Resource Consumption & Operational Telemetry

| Metric | Total Value | Note |
| :--- | :--- | :--- |
| **Total LLM Calls** | `3` | Mutation & crossover prompts |
| **Prompt Tokens** | `21,304` | Input context and instructions |
| **Completion Tokens** | `1,927` | Generated search/replace diffs |
| **Total Tokens Consumed** | **`23,231`** | Combined LLM token footprint |
| **Estimated API Cost** | **`$0.0022` USD** | Cost-effective synthesis |
| **Lines Added / Deleted** | `+71` / `-12` | Cumulative diff churn |
| **Net Code Churn** | `83` lines | Across all evaluated variants |

---

## 2. Objective Formulation: Dual-Tier Fitness $J_{\text{v5}}$

The **v5 Evolutionary Search** bridges the physical realism gap while preserving the canonical floor:
$$J_{\text{v5}} = J_{\text{canon}} + J_{\text{realism\_shocks}} + \text{InferLineBonus}$$
$$\text{where } J_{\text{canon}} = \text{CostSavings\%} - 100 \cdot M_{\text{canon}} - 10 \cdot \max(0, P99_{\text{canon}} - 6.0) - 0.01 \cdot \Delta_{\text{canon}}$$
$$J_{\text{realism\_shocks}} = +0.20 \cdot \max(0, 7031 - M_{\text{shock}}) \quad (T_{\text{init}} \in [15\text{s}, 50\text{s}, 150\text{s}, 250\text{s}, 300\text{s}])$$

### Authoritative Benchmarks Comparison
| Controller / Candidate | Canonical Cost | Cost Savings | Canonical Misses | Realism Shock Misses ($T_{\text{init}} \le 300\text{s}$) | Fitness $J_{\text{v5}}$ | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fixed Capacity Baseline** | 27,900.0 ws | 0.0% | 0 | 0 (Static Peak) | 0.00 | Static Floor |
| **InferLine Baseline** | 14,261.0 ws | 48.9% | 44 | 0 (Over-provisioned) | -4,356.0 | Degraded Floor |
| **v3 Champion (`bbd9b1c2`)** | 13,001.0 ws | **53.4%** | **0** | **2,379** (Delayed shock trap) | **+14.84** | Seed Baseline |
| **Current v5 Champion (`271e12f5`)** | **11874.0 ws** | **57.44%** | **0** | **6998** | **+71.77** | 🏆 **Frontier Champion** |

---

## 3. Discovered Policies Leaderboard (Top 30 Ranked by Fitness $J_{\text{v5}}$)

| Rank | Child ID | Island | Fitness $J_{\text{v5}}$ | Cost Savings | Canon Miss | Shock Miss | Shock Resilience | P99 Tail | Deltas | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `271e12f5` | Island 0 | **+71.77** | 57.44% | 0 | 6998 | 102 | 6.00s | 227 | Pareto Candidate |
| 2 | `1a45e8c0` | Island 0 | **+71.57** | 57.44% | 0 | 6999 | 101 | 6.00s | 227 | Pareto Candidate |
| 3 | `c43da2fd` | Island 0 | **-428.23** | 57.44% | 0 | 6998 | 102 | 6.00s | 227 | Pruned (<30.0) |
