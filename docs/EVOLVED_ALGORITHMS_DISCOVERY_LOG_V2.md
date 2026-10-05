# OpenEvolve v2 Evolutionary Synthesis: Discovery Log & Pareto Frontier

*Generated on: 2026-10-05 14:29:24 UTC*

## 1. Executive Summary & Objective Alignment

The **v2 Evolutionary Search** optimizes the **Cost-First / Equal Miss & P99** fitness formulation:
$$J_{\text{v2}} = \text{cost\_savings\_\%} - \left(2.0 \cdot \min(M, 50) + 10.0 \cdot \max(0, M - 50)\right) - 10.0 \cdot \max(0.0, P99 - 5.0) - 0.01 \cdot \Delta$$

| Policy / Model | Worker-Sec (Cost) | Cost Savings vs Fixed | Deadline Misses | P99 Tail Latency | Scaling Deltas | Fitness $J_{\text{v2}}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fixed Capacity Baseline** | 27,900.0 ws | 0.0% | 0 | 5.00s | 205 | 0.00 |
| **InferLine Baseline** | 14,261.0 ws | **48.9%** | 44 | 6.00s | 855 | -57.66 |
| **Step 7 Champion (Seed)** | 20,645.0 ws | 26.0% | **0** | **4.89s** | **218** | **+26.01** |
| **Current v2 Champion (1239f391)** | **12716.0 ws** | **54.42%** | **156** | **9.00s** | **2899** | **+-1174.57** |

---

## 2. Top-10 Discovered Policies (Ranked by Fitness $J_{\text{v2}}$)

| Rank | Child ID | Island | Fitness $J_{\text{v2}}$ | Cost Savings | Misses | P99 Latency | Worker-Sec | Deltas | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `1239f391` | Island 0 | **-1174.57** | 54.42% | 156 | 9.00s | 12716.0 | 2899 | Beats InferLine Cost |
