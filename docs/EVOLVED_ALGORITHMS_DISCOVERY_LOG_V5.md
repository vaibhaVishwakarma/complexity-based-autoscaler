# OpenEvolve v5 Realism-Aware Evolutionary Search: Discovery Log & Leaderboard

*Generated on: 2026-10-07 09:17:33 UTC*

## 1. Resource Consumption & Operational Telemetry

| Metric | Total Value | Note |
| :--- | :--- | :--- |
| **Total LLM Calls** | `0` | Mutation & crossover prompts |
| **Prompt Tokens** | `0` | Input context and instructions |
| **Completion Tokens** | `0` | Generated search/replace diffs |
| **Total Tokens Consumed** | **`0`** | Combined LLM token footprint |
| **Estimated API Cost** | **`$0.0000` USD** | Cost-effective synthesis |
| **Lines Added / Deleted** | `+0` / `-0` | Cumulative diff churn |
| **Net Code Churn** | `0` lines | Across all evaluated variants |

---

## 2. Objective Formulation: Dual-Tier Fitness $J_{\text{v5}}$

The **v5 Evolutionary Search** bridges the physical realism gap while preserving the canonical floor:
$$J_{\text{v5}} = J_{\text{canon}} + J_{\text{realism\_shocks}} + \text{InferLineBonus}$$
$$\text{where } J_{\text{canon}} = \text{CostSavings\%} - 100 \cdot M_{\text{canon}} - 10 \cdot \max(0, P99_{\text{canon}} - 6.0) - 0.01 \cdot \Delta_{\text{canon}}$$
$$J_{\text{realism\_shocks}} = -0.02 \cdot M_{\text{shock}} \quad (T_{\text{init}} \in [15\text{s}, 50\text{s}, 150\text{s}, 250\text{s}, 300\text{s}])$$

### Authoritative Benchmarks Comparison
| Controller / Candidate | Canonical Cost | Cost Savings | Canonical Misses | Realism Shock Misses ($T_{\text{init}} \le 300\text{s}$) | Fitness $J_{\text{v5}}$ | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fixed Capacity Baseline** | 27,900.0 ws | 0.0% | 0 | 0 (Static Peak) | 0.00 | Static Floor |
| **InferLine Baseline** | 14,261.0 ws | 48.9% | 44 | 0 (Over-provisioned) | -4,356.0 | Degraded Floor |
| **v3 Champion (`bbd9b1c2`)** | 13,001.0 ws | **53.4%** | **0** | **2,379** (Delayed shock trap) | **+14.84** | Seed Baseline |

---

## 3. Discovered Policies Leaderboard (Top 30 Ranked by Fitness $J_{\text{v5}}$)

| Rank | Child ID | Island | Fitness $J_{\text{v5}}$ | Cost Savings | Canon Miss | Shock Miss | Shock Resilience | P99 Tail | Deltas | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
