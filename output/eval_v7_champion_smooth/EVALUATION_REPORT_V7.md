# Step 8.5/8.7 Physical Delay Ladder Empirical Evaluation Report
**Comprehensive Realism Stress Evaluation Across Physical Delay Ladder ($T_{\text{boot}} \in [0.5\text{s} \to 300\text{s}]$)**

---

## 1. Executive Summary

- **Evaluated Policy Artifact**: [`champion_policy_v7_smooth.py`](/home/vaibo/auto-edgecompute/output/champion_policy_v7_smooth.py)
- **Timestamp**: 2026-10-14 04:29:21 UTC
- **Total Tested Conditions**: 135 runs (5 controllers × 3 regimes × 10 delays)
- **Zero-NaN Certification**: Verified 100% complete diagnostic telemetry across all 15 columns
- **Total Champion v7 Deadline Misses**: **10,264** across all tested delay conditions
- **Mean Champion v7 P99 Tail Latency**: **12.59s** (SLA Budget: $15.0\text{s}$)
- **Total Champion v7 Worker-Seconds**: **15,596.0 ws**
- **Total Champion v7 Actuation Churn**: **390 deltas**

---

## 2. Regime-by-Regime Benchmark Results

### Regime: `suite1_spike`

| Controller | Startup Delay (s) | Deadline Misses | P99 Latency (s) | Queue Wait (s) | Worker-Seconds | Flaps (Deltas) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **evolved_conformal** |   1.0 | 0 | 5.00 | 0.0038 | 484.0 | 17 |
| **evolved_conformal** |   5.0 | 0 | 11.00 | 0.3479 | 568.0 | 23 |
| **evolved_conformal** |  10.0 | 0 | 12.00 | 0.5030 | 568.0 | 23 |
| **evolved_conformal** |  20.0 | 0 | 12.00 | 0.6290 | 568.0 | 23 |
| **evolved_conformal** |  50.0 | 199 | 17.00 | 1.3595 | 635.0 | 25 |
| **evolved_conformal** | 100.0 | 323 | 17.00 | 2.0961 | 726.0 | 25 |
| **evolved_conformal** | 150.0 | 323 | 17.00 | 2.0961 | 726.0 | 25 |
| **evolved_conformal** | 200.0 | 323 | 17.00 | 2.0961 | 726.0 | 25 |
| **evolved_conformal** | 300.0 | 323 | 17.00 | 2.0961 | 726.0 | 25 |
| *fixed_capacity* |   1.0 | 0 | 5.00 | 0.0000 | 1,710.0 | 16 |
| *fixed_capacity* |   5.0 | 0 | 5.00 | 0.0000 | 1,710.0 | 16 |
| *fixed_capacity* |  10.0 | 0 | 5.00 | 0.0025 | 1,710.0 | 16 |
| *fixed_capacity* |  20.0 | 0 | 6.00 | 0.0319 | 1,710.0 | 16 |
| *fixed_capacity* |  50.0 | 0 | 6.00 | 0.1045 | 1,710.0 | 16 |
| *fixed_capacity* | 100.0 | 323 | 17.00 | 2.0961 | 1,710.0 | 16 |
| *fixed_capacity* | 150.0 | 323 | 17.00 | 2.0961 | 1,710.0 | 16 |
| *fixed_capacity* | 200.0 | 323 | 17.00 | 2.0961 | 1,710.0 | 16 |
| *fixed_capacity* | 300.0 | 323 | 17.00 | 2.0961 | 1,710.0 | 16 |
| *hpa* |   1.0 | 0 | 5.00 | 0.0075 | 1,455.0 | 35 |
| *hpa* |   5.0 | 0 | 9.00 | 0.0902 | 1,455.0 | 35 |
| *hpa* |  10.0 | 0 | 13.00 | 0.2996 | 1,455.0 | 35 |
| *hpa* |  20.0 | 324 | 24.00 | 1.2734 | 1,455.0 | 35 |
| *hpa* |  50.0 | 1,413 | 48.00 | 6.2144 | 1,659.0 | 18 |
| *hpa* | 100.0 | 2,463 | 48.00 | 7.7635 | 1,659.0 | 18 |
| *hpa* | 150.0 | 2,463 | 48.00 | 7.7635 | 1,659.0 | 18 |
| *hpa* | 200.0 | 2,463 | 48.00 | 7.7635 | 1,659.0 | 18 |
| *hpa* | 300.0 | 2,463 | 48.00 | 7.7635 | 1,659.0 | 18 |
| *inferline* |   1.0 | 0 | 10.00 | 0.2964 | 632.0 | 10 |
| *inferline* |   5.0 | 0 | 12.00 | 0.4814 | 632.0 | 10 |
| *inferline* |  10.0 | 0 | 12.00 | 0.5772 | 632.0 | 10 |
| *inferline* |  20.0 | 0 | 12.00 | 0.6740 | 632.0 | 10 |
| *inferline* |  50.0 | 321 | 17.00 | 1.6862 | 672.0 | 11 |
| *inferline* | 100.0 | 323 | 17.00 | 2.0961 | 672.0 | 11 |
| *inferline* | 150.0 | 323 | 17.00 | 2.0961 | 672.0 | 11 |
| *inferline* | 200.0 | 323 | 17.00 | 2.0961 | 672.0 | 11 |
| *inferline* | 300.0 | 323 | 17.00 | 2.0961 | 672.0 | 11 |
| *keda* |   1.0 | 39 | 8.00 | 0.1746 | 689.0 | 103 |
| *keda* |   5.0 | 19 | 9.00 | 0.1537 | 793.0 | 89 |
| *keda* |  10.0 | 21 | 14.00 | 0.3713 | 900.0 | 81 |
| *keda* |  20.0 | 359 | 24.00 | 1.3769 | 1,099.0 | 69 |
| *keda* |  50.0 | 1,464 | 48.00 | 6.3339 | 1,607.0 | 18 |
| *keda* | 100.0 | 2,463 | 48.00 | 7.7635 | 1,607.0 | 18 |
| *keda* | 150.0 | 2,463 | 48.00 | 7.7635 | 1,607.0 | 18 |
| *keda* | 200.0 | 2,463 | 48.00 | 7.7635 | 1,607.0 | 18 |
| *keda* | 300.0 | 2,463 | 48.00 | 7.7635 | 1,607.0 | 18 |

---

### Regime: `suite2_shock`

| Controller | Startup Delay (s) | Deadline Misses | P99 Latency (s) | Queue Wait (s) | Worker-Seconds | Flaps (Deltas) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **evolved_conformal** |   1.0 | 0 | 5.00 | 0.0018 | 663.0 | 19 |
| **evolved_conformal** |   5.0 | 0 | 6.00 | 0.0375 | 663.0 | 19 |
| **evolved_conformal** |  10.0 | 0 | 10.00 | 0.2589 | 708.0 | 23 |
| **evolved_conformal** |  20.0 | 232 | 16.00 | 1.1893 | 833.0 | 29 |
| **evolved_conformal** |  50.0 | 1,129 | 21.00 | 1.9232 | 924.0 | 16 |
| **evolved_conformal** | 100.0 | 1,853 | 28.00 | 2.0632 | 939.0 | 16 |
| **evolved_conformal** | 150.0 | 1,853 | 28.00 | 2.0632 | 939.0 | 16 |
| **evolved_conformal** | 200.0 | 1,853 | 28.00 | 2.0632 | 939.0 | 16 |
| **evolved_conformal** | 300.0 | 1,853 | 28.00 | 2.0632 | 939.0 | 16 |
| *fixed_capacity* |   1.0 | 0 | 5.00 | 0.0000 | 1,890.0 | 16 |
| *fixed_capacity* |   5.0 | 0 | 5.00 | 0.0002 | 1,890.0 | 16 |
| *fixed_capacity* |  10.0 | 0 | 5.00 | 0.0023 | 1,890.0 | 16 |
| *fixed_capacity* |  20.0 | 0 | 5.00 | 0.0091 | 1,890.0 | 16 |
| *fixed_capacity* |  50.0 | 0 | 6.00 | 0.0237 | 1,890.0 | 16 |
| *fixed_capacity* | 100.0 | 1,853 | 28.00 | 2.0632 | 1,890.0 | 16 |
| *fixed_capacity* | 150.0 | 1,853 | 28.00 | 2.0632 | 1,890.0 | 16 |
| *fixed_capacity* | 200.0 | 1,853 | 28.00 | 2.0632 | 1,890.0 | 16 |
| *fixed_capacity* | 300.0 | 1,853 | 28.00 | 2.0632 | 1,890.0 | 16 |
| *hpa* |   1.0 | 0 | 5.00 | 0.0033 | 1,635.0 | 35 |
| *hpa* |   5.0 | 0 | 8.00 | 0.0539 | 1,635.0 | 35 |
| *hpa* |  10.0 | 9 | 13.00 | 0.2048 | 1,635.0 | 35 |
| *hpa* |  20.0 | 330 | 23.00 | 0.7510 | 1,635.0 | 35 |
| *hpa* |  50.0 | 1,320 | 46.00 | 4.1177 | 1,839.0 | 18 |
| *hpa* | 100.0 | 3,844 | 50.00 | 5.9460 | 1,839.0 | 18 |
| *hpa* | 150.0 | 3,844 | 50.00 | 5.9460 | 1,839.0 | 18 |
| *hpa* | 200.0 | 3,844 | 50.00 | 5.9460 | 1,839.0 | 18 |
| *hpa* | 300.0 | 3,844 | 50.00 | 5.9460 | 1,839.0 | 18 |
| *inferline* |   1.0 | 0 | 9.00 | 0.1805 | 486.0 | 7 |
| *inferline* |   5.0 | 77 | 15.00 | 0.6041 | 664.0 | 12 |
| *inferline* |  10.0 | 631 | 23.00 | 1.4098 | 794.0 | 16 |
| *inferline* |  20.0 | 1,393 | 28.00 | 1.9601 | 794.0 | 16 |
| *inferline* |  50.0 | 1,853 | 28.00 | 2.0632 | 794.0 | 16 |
| *inferline* | 100.0 | 1,853 | 28.00 | 2.0632 | 794.0 | 16 |
| *inferline* | 150.0 | 1,853 | 28.00 | 2.0632 | 794.0 | 16 |
| *inferline* | 200.0 | 1,853 | 28.00 | 2.0632 | 794.0 | 16 |
| *inferline* | 300.0 | 1,853 | 28.00 | 2.0632 | 794.0 | 16 |
| *keda* |   1.0 | 33 | 8.00 | 0.0984 | 895.0 | 121 |
| *keda* |   5.0 | 28 | 9.00 | 0.1508 | 999.0 | 112 |
| *keda* |  10.0 | 49 | 14.00 | 0.3304 | 1,184.0 | 102 |
| *keda* |  20.0 | 380 | 23.00 | 0.8614 | 1,389.0 | 73 |
| *keda* |  50.0 | 1,337 | 47.00 | 4.1723 | 1,776.0 | 25 |
| *keda* | 100.0 | 3,844 | 50.00 | 5.9460 | 1,787.0 | 18 |
| *keda* | 150.0 | 3,844 | 50.00 | 5.9460 | 1,787.0 | 18 |
| *keda* | 200.0 | 3,844 | 50.00 | 5.9460 | 1,787.0 | 18 |
| *keda* | 300.0 | 3,844 | 50.00 | 5.9460 | 1,787.0 | 18 |

---

### Regime: `suite3_azure`

| Controller | Startup Delay (s) | Deadline Misses | P99 Latency (s) | Queue Wait (s) | Worker-Seconds | Flaps (Deltas) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **evolved_conformal** |   1.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** |   5.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** |  10.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** |  20.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** |  50.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** | 100.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** | 150.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** | 200.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| **evolved_conformal** | 300.0 | 0 | 5.00 | 0.0012 | 258.0 | 1 |
| *fixed_capacity* |   1.0 | 0 | 5.00 | 0.0000 | 2,430.0 | 16 |
| *fixed_capacity* |   5.0 | 0 | 5.00 | 0.0000 | 2,430.0 | 16 |
| *fixed_capacity* |  10.0 | 0 | 5.00 | 0.0000 | 2,430.0 | 16 |
| *fixed_capacity* |  20.0 | 0 | 5.00 | 0.0008 | 2,430.0 | 16 |
| *fixed_capacity* |  50.0 | 0 | 5.00 | 0.0012 | 2,430.0 | 16 |
| *fixed_capacity* | 100.0 | 0 | 5.00 | 0.0012 | 2,430.0 | 16 |
| *fixed_capacity* | 150.0 | 0 | 5.00 | 0.0012 | 2,430.0 | 16 |
| *fixed_capacity* | 200.0 | 0 | 5.00 | 0.0012 | 2,430.0 | 16 |
| *fixed_capacity* | 300.0 | 0 | 5.00 | 0.0012 | 2,430.0 | 16 |
| *hpa* |   1.0 | 5 | 8.00 | 0.0541 | 1,800.0 | 162 |
| *hpa* |   5.0 | 6 | 13.00 | 0.1936 | 1,993.0 | 140 |
| *hpa* |  10.0 | 330 | 21.00 | 0.6226 | 1,982.0 | 142 |
| *hpa* |  20.0 | 592 | 37.00 | 1.9965 | 2,003.0 | 138 |
| *hpa* |  50.0 | 1,271 | 80.00 | 9.5984 | 2,326.0 | 28 |
| *hpa* | 100.0 | 1,726 | 115.00 | 1.8073 | 2,342.0 | 20 |
| *hpa* | 150.0 | 1,535 | 4.00 | 0.0000 | 2,342.0 | 20 |
| *hpa* | 200.0 | 1,535 | 4.00 | 0.0000 | 2,342.0 | 20 |
| *hpa* | 300.0 | 1,535 | 4.00 | 0.0000 | 2,342.0 | 20 |
| *inferline* |   1.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* |   5.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* |  10.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* |  20.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* |  50.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* | 100.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* | 150.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* | 200.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *inferline* | 300.0 | 0 | 5.00 | 0.0012 | 270.0 | 0 |
| *keda* |   1.0 | 17 | 8.00 | 0.0549 | 625.0 | 75 |
| *keda* |   5.0 | 22 | 10.00 | 0.0585 | 806.0 | 92 |
| *keda* |  10.0 | 40 | 14.00 | 0.1915 | 954.0 | 70 |
| *keda* |  20.0 | 522 | 24.00 | 0.6421 | 1,001.0 | 67 |
| *keda* |  50.0 | 1,286 | 54.00 | 3.1874 | 1,459.0 | 47 |
| *keda* | 100.0 | 1,740 | 104.00 | 4.3527 | 2,330.0 | 20 |
| *keda* | 150.0 | 1,535 | 4.00 | 0.0000 | 2,330.0 | 20 |
| *keda* | 200.0 | 1,535 | 4.00 | 0.0000 | 2,330.0 | 20 |
| *keda* | 300.0 | 1,535 | 4.00 | 0.0000 | 2,330.0 | 20 |

---

## 3. Physical Realism Tipping Points & Trade-Off Analysis

1. **Sub-SLA Delays ($T_{\text{boot}} \le 15.0\text{s}$)**:
   - Conformal feed-forward preemption absorbs complexity shocks and burst surges before task deadlines expire, maintaining zero or near-zero deadline misses.
2. **Super-SLA Delays ($T_{\text{boot}} \ge 50.0\text{s}$)**:
   - When container initialization latency exceeds the 15.0s SLA deadline, newly provisioned workers arrive too late to rescue in-flight requests during acute shocks.
   - All reactive and proactive controllers exhibit a physical saturation knee where tail latency tracks startup lag unless cushioned by large buffer thresholds.

---

## 4. Provenance & Reproducibility

- **Evaluation Harness**: `scripts/evaluate_v7_raw_results.py`
- **Output CSV**: `output/eval_v7_champion_smooth/summary_v7_vs_baselines.csv`
- **Output Report**: `output/eval_v7_champion_smooth/EVALUATION_REPORT_V7.md`
