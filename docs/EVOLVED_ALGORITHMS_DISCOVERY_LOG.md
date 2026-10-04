# OpenEvolve Evolutionary Conformal Autoscaler Discovery Log

> **Notice**: This document tracks the simulation-in-the-loop synthesis of
> adaptive conformal scaling policies across 13 diverse workload regimes
> on ContinuumBench (121,134 requests). Real-time telemetry is recorded on
> every LLM synthesis call and multi-stage cascade evaluation.

## 1. Executive Status & Best Policy to Date

- **Best Program ID**: `35671429-9085-4ec6-abdd-9ddebc56f15f` (Iteration 103)
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Primary Fitness $J$**: **1152.5520**
- **Deadline Misses**: **0** (InferLine: 44, Fixed: 0)
- **Worker-Seconds**: **19,544.0** (**29.95% savings** vs Fixed Capacity; InferLine: 14,261.0 / 48.9%)
- **Churn Deltas**: **394** (InferLine: 855, KEDA: 1,710)
- **Tail Safety (P99)**: **5.00s** (InferLine: 6.0s, SLA Deadline: 10.0s)

### Benchmark Baseline Comparison Matrix

| Controller / Policy | Type | Worker-Seconds | Cost Savings vs Fixed | Deadline Misses | Churn Deltas | Max P99 Latency |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fixed Capacity** | Static Peak | 27,900.0 | 0.0% | 0 | 205 | 5.0s |
| **InferLine Tuner** | Reactive Envelope | 14,261.0 | 48.9% | 44 | 855 | 6.0s |
| **Kubernetes HPA** | Reactive Util | 23,940.0 | 14.2% | 72 | 606 | 13.0s |
| **KEDA** | Reactive Concurrency | 19,850.0 | 28.9% | 128 | 1710 | 9.5s |
| **Conformal Seed Baseline** | Conformal ACI | 16,675.0 | 40.2% | 824 | 4628 | 7.0s |
| **⭐ Best Evolved Policy** | **Conformal Evolved** | **19,544.0** | **29.95%** | **0** | **394** | **5.00s** |

---

## 2. LLM Call & Synthesis Telemetry

- **Total LLM Calls**: 109 (Successful: 108 | Rejected/Error: 1)
- **Total Token Budget Consumed**: 2,123,042 tokens (2,007,127 prompt + 64,171 completion/thinking)
- **Model**: `gemini-2.5-flash` via Google AI Studio (`temperature: 0.7`, `max_tokens: 8192`)

---

## 3. Discovered Algorithms Summary Table

| Iter | Program ID | Branch Origin | Fitness $J$ | Misses | Worker-Sec | Savings | Deltas | Max P99 | Regimes | Status vs InferLine |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | `e2779dc5` | Island 0 | **15.34** | 905 | 17,198.0 | 38.4% | 5132 | 16.00s | 13/13 | Evaluated |
| 2 | `c1bd42d6` | Island 1 | **122.59** | 824 | 16,675.0 | 40.2% | 4628 | 16.00s | 13/13 | Evaluated |
| 3 | `0c0e07c4` | Island 2 | **143.90** | 817 | 17,018.0 | 39.0% | 4328 | 16.00s | 13/13 | Evaluated |
| 4 | `e7605d6a` | Island 0 | **32.48** | 893 | 16,980.0 | 39.1% | 5038 | 16.00s | 13/13 | Evaluated |
| 5 | `074db9b7` | Island 1 | **329.73** | 356 | 19,556.0 | 29.9% | 9730 | 15.00s | 13/13 | Evaluated |
| 6 | `1cb9f42d` | Island 2 | **298.79** | 631 | 17,973.0 | 35.6% | 4912 | 16.00s | 13/13 | Evaluated |
| 7 | `d6c970aa` | Island 0 | **39.27** | 890 | 16,937.0 | 39.3% | 4964 | 16.00s | 13/13 | Evaluated |
| 8 | `b16dc69a` | Island 1 | **276.47** | 504 | 18,984.0 | 32.0% | 7858 | 15.00s | 13/13 | Evaluated |
| 9 | `08c1f81f` | Island 2 | **307.92** | 624 | 17,658.0 | 36.7% | 4882 | 16.00s | 13/13 | Evaluated |
| 10 | `25e6bdb7` | Island 0 | **32.48** | 893 | 16,980.0 | 39.1% | 5038 | 16.00s | 13/13 | Evaluated |
| 11 | `25994bf4` | Island 1 | **81.06** | 660 | 18,339.0 | 34.3% | 8672 | 16.00s | 13/13 | Evaluated |
| 12 | `6355ef42` | Island 2 | **307.92** | 624 | 17,658.0 | 36.7% | 4882 | 16.00s | 13/13 | Evaluated |
| 13 | `c2b54f07` | Island 0 | **32.48** | 893 | 16,980.0 | 39.1% | 5038 | 16.00s | 13/13 | Evaluated |
| 14 | `6e0356e9` | Island 1 | **312.39** | 468 | 18,925.0 | 32.2% | 7862 | 16.00s | 13/13 | Evaluated |
| 15 | `f49a0fcd` | Island 2 | **307.92** | 624 | 17,658.0 | 36.7% | 4882 | 16.00s | 13/13 | Evaluated |
| 16 | `5ec4c043` | Island 0 | **-11.21** | 919 | 17,375.0 | 37.7% | 5376 | 16.00s | 13/13 | Evaluated |
| 17 | `27e51b22` | Island 1 | **179.12** | 561 | 18,312.0 | 34.4% | 8692 | 16.00s | 13/13 | Evaluated |
| 18 | `53a923b2` | Island 2 | **307.92** | 624 | 17,658.0 | 36.7% | 4882 | 16.00s | 13/13 | Evaluated |
| 19 | `8e67e83e` | Island 0 | **-50.20** | 963 | 17,318.0 | 37.9% | 5278 | 16.00s | 13/13 | Evaluated |
| 20 | `0ea9c50d` | Island 1 | **266.35** | 513 | 18,944.0 | 32.1% | 7882 | 15.04s | 13/13 | Evaluated |
| 21 | `156e49a4` | Island 2 | **305.26** | 629 | 17,941.0 | 35.7% | 4824 | 16.00s | 13/13 | Evaluated |
| 22 | `228b63b7` | Island 0 | **11.66** | 926 | 16,838.0 | 39.6% | 4800 | 16.00s | 13/13 | Evaluated |
| 23 | `3e4a80c2` | Island 1 | **301.63** | 480 | 18,904.0 | 32.2% | 7838 | 16.00s | 13/13 | Evaluated |
| 24 | `fc431309` | Island 2 | **320.63** | 621 | 17,005.0 | 39.1% | 4714 | 16.00s | 13/13 | Evaluated |
| 25 | `372a88ba` | Island 0 | **496.65** | 384 | 18,275.0 | 34.5% | 5871 | 17.00s | 13/13 | Evaluated |
| 26 | `b8bca682` | Island 1 | **329.48** | 455 | 18,928.0 | 32.2% | 7780 | 16.00s | 13/13 | Evaluated |
| 27 | `0ad43fbc` | Island 2 | **320.63** | 621 | 17,005.0 | 39.1% | 4714 | 16.00s | 13/13 | Evaluated |
| 28 | `be2aa9ac` | Island 0 | **32.41** | 893 | 17,014.0 | 39.0% | 5038 | 16.00s | 13/13 | Evaluated |
| 30 | `b28b6d42` | Island 2 | **320.63** | 621 | 17,005.0 | 39.1% | 4714 | 16.00s | 13/13 | Evaluated |
| 32 | `ca307cbb` | Island 1 | **263.01** | 507 | 18,866.0 | 32.4% | 8072 | 15.00s | 13/13 | Evaluated |
| 33 | `0edc1707` | Island 2 | **314.19** | 624 | 17,075.0 | 38.8% | 4780 | 16.00s | 13/13 | Evaluated |
| 34 | `127258cf` | Island 0 | **469.04** | 420 | 17,985.0 | 35.5% | 5715 | 17.00s | 13/13 | Evaluated |
| 35 | `ebe232b6` | Island 1 | **312.39** | 468 | 18,925.0 | 32.2% | 7862 | 16.00s | 13/13 | Evaluated |
| 36 | `9db825a3` | Island 2 | **311.20** | 620 | 17,669.0 | 36.7% | 4896 | 16.00s | 13/13 | Evaluated |
| 37 | `b125f4cd` | Island 0 | **496.65** | 384 | 18,275.0 | 34.5% | 5871 | 17.00s | 13/13 | Evaluated |
| 38 | `86fea0ef` | Island 1 | **272.44** | 507 | 18,951.0 | 32.1% | 7880 | 15.04s | 13/13 | Evaluated |
| 39 | `1eb20966` | Island 2 | **305.26** | 629 | 17,941.0 | 35.7% | 4824 | 16.00s | 13/13 | Evaluated |
| 40 | `d68ce5a9` | Island 0 | **496.65** | 384 | 18,275.0 | 34.5% | 5871 | 17.00s | 13/13 | Evaluated |
| 41 | `f5ff08a9` | Island 1 | **301.63** | 480 | 18,904.0 | 32.2% | 7838 | 16.00s | 13/13 | Evaluated |
| 42 | `1e1cd732` | Island 2 | **305.26** | 629 | 17,941.0 | 35.7% | 4824 | 16.00s | 13/13 | Evaluated |
| 43 | `727f7c6f` | Island 0 | **373.41** | 509 | 17,863.0 | 36.0% | 5864 | 16.00s | 13/13 | Evaluated |
| 44 | `919f8430` | Island 1 | **209.43** | 588 | 19,106.0 | 31.5% | 7514 | 16.00s | 13/13 | Evaluated |
| 45 | `5ee2380e` | Island 2 | **311.20** | 620 | 17,669.0 | 36.7% | 4896 | 16.00s | 13/13 | Evaluated |
| 46 | `837bd9dc` | Island 0 | **506.98** | 388 | 18,219.0 | 34.7% | 5585 | 14.00s | 13/13 | Evaluated |
| 47 | `8dd7f784` | Island 1 | **358.79** | 428 | 18,774.0 | 32.7% | 7740 | 15.00s | 13/13 | Evaluated |
| 48 | `43bd74f1` | Island 2 | **306.09** | 629 | 17,925.0 | 35.8% | 4808 | 16.00s | 13/13 | Evaluated |
| 49 | `10344c28` | Island 0 | **506.98** | 388 | 18,219.0 | 34.7% | 5585 | 14.00s | 13/13 | Evaluated |
| 50 | `ee175139` | Island 1 | **358.79** | 428 | 18,774.0 | 32.7% | 7740 | 15.00s | 13/13 | Evaluated |
| 51 | `88b335eb` | Island 2 | **307.92** | 624 | 17,658.0 | 36.7% | 4882 | 16.00s | 13/13 | Evaluated |
| 52 | `0083bd23` | Island 0 | **536.32** | 412 | 18,910.0 | 32.2% | 4500 | 13.24s | 13/13 | Evaluated |
| 53 | `6b353f38` | Island 1 | **329.48** | 455 | 18,928.0 | 32.2% | 7780 | 16.00s | 13/13 | Evaluated |
| 54 | `0efd6348` | Island 2 | **705.99** | 136 | 18,819.0 | 32.5% | 6627 | 12.00s | 13/13 | Evaluated |
| 55 | `f13e1d00` | Island 0 | **506.98** | 388 | 18,219.0 | 34.7% | 5585 | 14.00s | 13/13 | Evaluated |
| 56 | `239503e9` | Island 1 | **327.42** | 457 | 18,760.0 | 32.8% | 7788 | 15.00s | 13/13 | Evaluated |
| 57 | `91a18882` | Island 2 | **305.26** | 629 | 17,941.0 | 35.7% | 4824 | 16.00s | 13/13 | Evaluated |
| 58 | `ba168308` | Island 0 | **345.42** | 551 | 17,910.0 | 35.8% | 5582 | 16.00s | 13/13 | Evaluated |
| 59 | `cf092150` | Island 1 | **358.79** | 428 | 18,774.0 | 32.7% | 7740 | 15.00s | 13/13 | Evaluated |
| 60 | `01418977` | Island 2 | **9.92** | 919 | 16,712.0 | 40.1% | 4980 | 16.00s | 13/13 | Evaluated |
| 61 | `ed80eb99` | Island 0 | **1149.23** | 0 | 20,957.0 | 24.9% | 404 | 5.00s | 13/13 | ✅ Beats Misses |
| 62 | `f02231fc` | Island 1 | **278.87** | 528 | 18,835.0 | 32.5% | 7336 | 16.00s | 13/13 | Evaluated |
| 63 | `353eeb32` | Island 2 | **587.49** | 335 | 18,677.0 | 33.1% | 5030 | 16.00s | 13/13 | Evaluated |
| 64 | `fd184f2d` | Island 0 | **505.26** | 391 | 18,588.0 | 33.4% | 5558 | 15.00s | 13/13 | Evaluated |
| 65 | `28d20725` | Island 1 | **358.79** | 428 | 18,774.0 | 32.7% | 7740 | 15.00s | 13/13 | Evaluated |
| 66 | `123a97cf` | Island 2 | **399.96** | 511 | 18,138.0 | 35.0% | 5282 | 16.00s | 13/13 | Evaluated |
| 67 | `97af42a3` | Island 0 | **418.37** | 464 | 18,385.0 | 34.1% | 5844 | 16.00s | 13/13 | Evaluated |
| 68 | `a1ccc293` | Island 1 | **238.35** | 512 | 18,895.0 | 32.3% | 8464 | 16.00s | 13/13 | Evaluated |
| 69 | `94fec1f5` | Island 2 | **577.32** | 352 | 18,710.0 | 32.9% | 4892 | 16.00s | 13/13 | Evaluated |
| 70 | `601f19e3` | Island 0 | **528.08** | 366 | 18,334.0 | 34.3% | 5596 | 17.00s | 13/13 | Evaluated |
| 71 | `2d1e0898` | Island 1 | **795.86** | 86 | 20,647.0 | 26.0% | 5760 | 11.00s | 13/13 | Evaluated |
| 72 | `c3845087` | Island 2 | **1149.83** | 0 | 20,955.0 | 24.9% | 392 | 5.00s | 13/13 | ✅ Beats Misses |
| 73 | `1cca2390` | Island 0 | **528.08** | 366 | 18,334.0 | 34.3% | 5596 | 17.00s | 13/13 | Evaluated |
| 74 | `16c01f60` | Island 1 | **217.07** | 542 | 19,083.0 | 31.6% | 8282 | 15.00s | 13/13 | Evaluated |
| 75 | `78497c29` | Island 2 | **663.42** | 274 | 19,359.0 | 30.6% | 4704 | 14.00s | 13/13 | Evaluated |
| 76 | `23bebabc` | Island 0 | **528.08** | 366 | 18,334.0 | 34.3% | 5596 | 17.00s | 13/13 | Evaluated |
| 77 | `f0c63bf5` | Island 1 | **795.86** | 86 | 20,647.0 | 26.0% | 5760 | 11.00s | 13/13 | Evaluated |
| 78 | `3db31c2f` | Island 2 | **1149.83** | 0 | 20,955.0 | 24.9% | 392 | 5.00s | 13/13 | ✅ Beats Misses |
| 79 | `2ca72076` | Island 0 | **425.01** | 537 | 18,515.0 | 33.6% | 4246 | 16.00s | 13/13 | Evaluated |
| 80 | `4fcac7bc` | Island 1 | **78.80** | 686 | 18,718.0 | 32.9% | 8182 | 16.00s | 13/13 | Evaluated |
| 81 | `fdf4ba0f` | Island 2 | **616.81** | 367 | 19,365.0 | 30.6% | 3776 | 16.00s | 13/13 | Evaluated |
| 82 | `3d4c66c7` | Island 0 | **335.46** | 570 | 17,688.0 | 36.6% | 5410 | 16.00s | 13/13 | Evaluated |
| 83 | `99a3ccc2` | Island 1 | **238.35** | 512 | 18,895.0 | 32.3% | 8464 | 16.00s | 13/13 | Evaluated |
| 84 | `04260a62` | Island 2 | **1149.83** | 0 | 20,955.0 | 24.9% | 392 | 5.00s | 13/13 | ✅ Beats Misses |
| 85 | `8b38417b` | Island 0 | **1149.23** | 0 | 20,957.0 | 24.9% | 404 | 5.00s | 13/13 | ✅ Beats Misses |
| 86 | `1a222eef` | Island 1 | **773.25** | 105 | 20,321.0 | 27.2% | 5844 | 11.00s | 13/13 | Evaluated |
| 87 | `672e6ce7` | Island 2 | **1149.19** | 0 | 21,127.0 | 24.3% | 398 | 5.00s | 13/13 | ✅ Beats Misses |
| 88 | `fe289a78` | Island 0 | **1149.23** | 0 | 20,957.0 | 24.9% | 404 | 5.00s | 13/13 | ✅ Beats Misses |
| 89 | `ae2297a1` | Island 1 | **22.90** | 735 | 18,420.0 | 34.0% | 8332 | 16.00s | 13/13 | Evaluated |
| 90 | `95470523` | Island 2 | **1147.91** | 0 | 21,416.0 | 23.2% | 412 | 5.00s | 13/13 | ✅ Beats Misses |
| 91 | `cf0c24db` | Island 0 | **1147.26** | 0 | 21,642.0 | 22.4% | 416 | 5.00s | 13/13 | ✅ Beats Misses |
| 92 | `e387a429` | Island 1 | **238.35** | 512 | 18,895.0 | 32.3% | 8464 | 16.00s | 13/13 | Evaluated |
| 93 | `bacc4797` | Island 2 | **1149.83** | 0 | 20,955.0 | 24.9% | 392 | 5.00s | 13/13 | ✅ Beats Misses |
| 94 | `9137e41e` | Island 0 | **1150.07** | 0 | 20,583.0 | 26.2% | 402 | 5.00s | 13/13 | ✅ Beats Misses |
| 95 | `483c15ff` | Island 1 | **768.23** | 110 | 20,595.0 | 26.2% | 5831 | 11.00s | 13/13 | Evaluated |
| 96 | `70c5ec11` | Island 2 | **1150.26** | 0 | 20,692.0 | 25.8% | 394 | 5.00s | 13/13 | ✅ Beats Misses |
| 97 | `9dbcc7e1` | Island 0 | **1149.23** | 0 | 20,957.0 | 24.9% | 404 | 5.00s | 13/13 | ✅ Beats Misses |
| 98 | `ba3a0aa5` | Island 1 | **261.52** | 487 | 18,658.0 | 33.1% | 8510 | 15.04s | 13/13 | Evaluated |
| 99 | `92137c24` | Island 2 | **1149.83** | 0 | 20,955.0 | 24.9% | 392 | 5.00s | 13/13 | ✅ Beats Misses |
| 100 | `45913bb1` | Island 0 | **1150.07** | 0 | 20,583.0 | 26.2% | 402 | 5.00s | 13/13 | ✅ Beats Misses |
| 101 | `b2131f9d` | Island 1 | **229.36** | 527 | 18,840.0 | 32.5% | 8346 | 16.00s | 13/13 | Evaluated |
| 102 | `27f02192` | Island 2 | **1149.97** | 0 | 20,833.0 | 25.3% | 394 | 5.00s | 13/13 | ✅ Beats Misses |
| 103 | `35671429` | Island 0 | **1152.55** | 0 | 19,544.0 | 29.9% | 394 | 5.00s | 13/13 | ✅ Beats Misses |
| 104 | `d98afbe7` | Island 1 | **238.35** | 512 | 18,895.0 | 32.3% | 8464 | 16.00s | 13/13 | Evaluated |
| 105 | `48abe3ca` | Island 2 | **1147.60** | 0 | 21,519.0 | 22.9% | 414 | 5.00s | 13/13 | ✅ Beats Misses |
| 106 | `2a964d24` | Island 0 | **429.22** | 531 | 18,460.0 | 33.8% | 4284 | 16.00s | 13/13 | Evaluated |
| 107 | `08b3d8e9` | Island 1 | **780.88** | 101 | 20,628.0 | 26.1% | 5764 | 11.00s | 13/13 | Evaluated |
| 108 | `8d41365c` | Island 2 | **1149.97** | 0 | 20,833.0 | 25.3% | 394 | 5.00s | 13/13 | ✅ Beats Misses |
| 109 | `3bb38ddc` | Island 0 | **411.31** | 488 | 17,780.0 | 36.3% | 5519 | 14.00s | 13/13 | Evaluated |

---

## 4. Chronological Iteration Breakdown & Code Innovations

### Iteration 1: Program `e2779dc5-1735-4306-986c-4d827b244b72`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 6051 prompt tokens, 606 completion tokens (total: 6657) | Latency: 188.81s
- **Composite Fitness $J$**: **15.3440**
- **13-Regime Benchmark Performance**: 905 misses, 17,198.0 worker-s (38.36% savings), 5132 deltas, Max P99: 16.00s
- **Innovation Rationale**: To optimize cost savings while maintaining tail safety and reducing actuation churn, we will enhance the demand-forward term by incorporating the derivative signals (`p_fast_velocity` and `ingress_acceleration`) to anticipate transient bursts and prevent premature scale-down.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,21 +140,19 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Velocity Anticipation ─────────
+    # Incorporate p_fast_velocity and ingress_acceleration to proactively scale
+    # ahead of demand spikes, reducing queue buildup and tail latency.
+    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps) + max(0.0, state.ingress_acceleration * 0.1)
+    SAFETY_MARGIN = 1.15
+    demand_workers = math.ceil((anticipated_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.2) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
     effective_target = demand_workers + drain_workers - state.booting_workers
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
```

### Iteration 2: Program `c1bd42d6-4b1b-4a57-9405-80689bd15c91`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 6031 prompt tokens, 341 completion tokens (total: 6372) | Latency: 178.1s
- **Composite Fitness $J$**: **122.5900**
- **13-Regime Benchmark Performance**: 824 misses, 16,675.0 worker-s (40.23% savings), 4628 deltas, Max P99: 16.00s
- **Innovation Rationale**: We integrate continuous complexity dynamics by factoring in `p_fast_velocity` for proactive scaling during surges and smooth decay during relaxation, combined with non-linear capacity modulation via `mean_set_size`.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,11 +140,17 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
+    # Factor in complexity surge (-p_fast_velocity when < 0) and model ambiguity (mean_set_size)
+    complexity_surge = max(0.0, -state.p_fast_velocity)
+    relaxation_factor = max(0.0, state.p_fast_velocity)
+    
+    # Non-linear ambiguity modulation
+    ambiguity_boost = max(1.0, state.mean_set_size)
+    
+    SAFETY_MARGIN = 1.20 + 0.5 * complexity_surge - 0.1 * relaxation_factor
+    adjusted_demand = state.offered_cloud_rps * ambiguity_boost
+    demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
```

### Iteration 3: Program `0c0e07c4-c225-4223-bb9b-8a7ead8b4c0e`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 6106 prompt tokens, 545 completion tokens (total: 6651) | Latency: 181.15s
- **Composite Fitness $J$**: **143.9040**
- **13-Regime Benchmark Performance**: 817 misses, 17,018.0 worker-s (39.00% savings), 4328 deltas, Max P99: 16.00s
- **Innovation Rationale**: We augment the demand-forward and drain terms with a conformal safety headroom proportional to `state.mean_set_size` and stabilize actuation using `state.time_since_last_scale_s`.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,21 +140,17 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
+    # Scale safety headroom dynamically using RAPS prediction set size (mean_set_size)
+    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0)
+    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.45
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
+    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
     effective_target = demand_workers + drain_workers - state.booting_workers
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
```

### Iteration 4: Program `e7605d6a-d9ba-43e7-affa-194cc997ffef`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 9330 prompt tokens, 574 completion tokens (total: 9904) | Latency: 180.05s
- **Composite Fitness $J$**: **32.4800**
- **13-Regime Benchmark Performance**: 893 misses, 16,980.0 worker-s (39.14% savings), 5038 deltas, Max P99: 16.00s
- **Innovation Rationale**: We will refine the safety margin dynamically based on `mean_set_size` and queue velocity to balance tail safety and cost savings, while incorporating deadband hysteresis to reduce scaling deltas and improve churn stability.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,21 +140,18 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
+    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
     effective_target = demand_workers + drain_workers - state.booting_workers
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
```

### Iteration 5: Program `074db9b7-2eca-4313-b219-8cb3bf2a221f`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `c1bd42d6-4b1b-4a57-9405-80689bd15c91`
- **LLM Call Telemetry**: 6508 prompt tokens, 423 completion tokens (total: 6931) | Latency: 182.4s
- **Composite Fitness $J$**: **329.7280**
- **13-Regime Benchmark Performance**: 356 misses, 19,556.0 worker-s (29.91% savings), 9730 deltas, Max P99: 15.00s
- **Innovation Rationale**: We refine the continuous complexity and ingress acceleration handling to provide even more precise proactive scaling under sudden surges.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,14 +141,15 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0) and model ambiguity (mean_set_size)
+    # Factor in complexity surge, ingress acceleration, and model ambiguity
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
+    acceleration_boost = max(0.0, state.ingress_acceleration * 0.05)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size)
+    ambiguity_boost = state.mean_set_size ** 1.2
     
-    SAFETY_MARGIN = 1.20 + 0.5 * complexity_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.22 + 0.6 * complexity_surge + acceleration_boost - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 6: Program `1cb9f42d-883f-40d9-af45-a42aca3f6ebc`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0c0e07c4-c225-4223-bb9b-8a7ead8b4c0e`
- **LLM Call Telemetry**: 6520 prompt tokens, 422 completion tokens (total: 6942) | Latency: 181.78s
- **Composite Fitness $J$**: **298.7940**
- **13-Regime Benchmark Performance**: 631 misses, 17,973.0 worker-s (35.58% savings), 4912 deltas, Max P99: 16.00s
- **Innovation Rationale**: We refine the conformal headroom factor and queue drain window to proactively catch sudden collapse while retaining cost efficiency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,13 +141,13 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size (mean_set_size)
-    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0)
+    # Scale safety headroom dynamically using RAPS prediction set size and velocity
+    conformal_factor = 1.0 + 0.18 * max(0.0, state.mean_set_size - 1.0) + 0.05 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
+    DRAIN_WINDOW_S = 0.40
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.5) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 7: Program `d6c970aa-310e-4978-ae17-86e248a79214`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `e2779dc5-1735-4306-986c-4d827b244b72`
- **LLM Call Telemetry**: 12569 prompt tokens, 507 completion tokens (total: 13076) | Latency: 180.08s
- **Composite Fitness $J$**: **39.2660**
- **13-Regime Benchmark Performance**: 890 misses, 16,937.0 worker-s (39.29% savings), 4964 deltas, Max P99: 16.00s
- **Innovation Rationale**: We introduce adaptive conformal uncertainty scaling and hysteresis damping to reduce actuation churn while safeguarding tail latency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,16 +140,16 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Velocity Anticipation ─────────
-    # Incorporate p_fast_velocity and ingress_acceleration to proactively scale
-    # ahead of demand spikes, reducing queue buildup and tail latency.
-    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps) + max(0.0, state.ingress_acceleration * 0.1)
-    SAFETY_MARGIN = 1.15
-    demand_workers = math.ceil((anticipated_demand * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
+    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps)
+    demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.2) / DRAIN_WINDOW_S
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.25
+    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
```

### Iteration 8: Program `b16dc69a-8180-4bbb-8e28-1a066a844b5b`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `c1bd42d6-4b1b-4a57-9405-80689bd15c91`
- **LLM Call Telemetry**: 9740 prompt tokens, 490 completion tokens (total: 10230) | Latency: 181.39s
- **Composite Fitness $J$**: **276.4720**
- **13-Regime Benchmark Performance**: 504 misses, 18,984.0 worker-s (31.96% savings), 7858 deltas, Max P99: 15.00s
- **Innovation Rationale**: Refined the safety margin calculation by integrating both `cloud_queue_velocity` and `ingress_acceleration` to preemptively ramp up before traffic spikes cause queue buildup, while balancing cost savings.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,14 +141,16 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0) and model ambiguity (mean_set_size)
+    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and ingress acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.1)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
     
-    SAFETY_MARGIN = 1.20 + 0.5 * complexity_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.20 + 0.4 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 9: Program `08c1f81f-4e04-42ac-8efb-4c205a9bb00e`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `1cb9f42d-883f-40d9-af45-a42aca3f6ebc`
- **LLM Call Telemetry**: 9683 prompt tokens, 462 completion tokens (total: 10145) | Latency: 178.73s
- **Composite Fitness $J$**: **307.9240**
- **13-Regime Benchmark Performance**: 624 misses, 17,658.0 worker-s (36.71% savings), 4882 deltas, Max P99: 16.00s
- **Innovation Rationale**: We refine the conformal headroom and drain window parameters slightly to improve responsiveness while maintaining our high cost savings and stability.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.18 * max(0.0, state.mean_set_size - 1.0) + 0.05 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.04 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.5) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.42
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 10: Program `25e6bdb7-dfc4-429f-972b-b6baf49d880a`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 14732 prompt tokens, 484 completion tokens (total: 15216) | Latency: 180.81s
- **Composite Fitness $J$**: **32.4800**
- **13-Regime Benchmark Performance**: 893 misses, 16,980.0 worker-s (39.14% savings), 5038 deltas, Max P99: 16.00s
- **Innovation Rationale**: To optimize cost savings while maintaining safety, we incorporate dynamic conformal uncertainty adaptation (`mean_set_size`) into the safety margin and add velocity damping to the queue-drain term. This reduces over-provisioning during stable periods while proactively absorbing spikes.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,17 +140,15 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
+    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
```

### Iteration 11: Program `25994bf4-b5f2-4547-8cfc-0248143bc2b0`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `b16dc69a-8180-4bbb-8e28-1a066a844b5b`
- **LLM Call Telemetry**: 13138 prompt tokens, 762 completion tokens (total: 13900) | Latency: 177.52s
- **Composite Fitness $J$**: **81.0620**
- **13-Regime Benchmark Performance**: 660 misses, 18,339.0 worker-s (34.27% savings), 8672 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the safety margin and queue drain responsiveness to balance responsiveness with cost savings and churn stability.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -144,20 +144,20 @@
     # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and ingress acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.1)
-    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.015)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.20 + 0.4 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.18 + 0.35 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.6
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 12: Program `6355ef42-3b24-4cfb-9e08-7ab528abaeeb`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0c0e07c4-c225-4223-bb9b-8a7ead8b4c0e`
- **LLM Call Telemetry**: 12780 prompt tokens, 440 completion tokens (total: 13220) | Latency: 175.45s
- **Composite Fitness $J$**: **307.9240**
- **13-Regime Benchmark Performance**: 624 misses, 17,658.0 worker-s (36.71% savings), 4882 deltas, Max P99: 16.00s
- **Innovation Rationale**: We refine the demand calculation by adding a small positive coefficient for `p_fast_velocity` and slightly tightening the queue drain window to improve responsiveness during fast-path collapses while maintaining stability.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,13 +141,13 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size (mean_set_size)
-    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0)
+    # Scale safety headroom dynamically using RAPS prediction set size and velocity
+    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
+    DRAIN_WINDOW_S = 0.42
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 13: Program `c2b54f07-f5aa-498a-b45e-a83e8965a44f`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 16940 prompt tokens, 450 completion tokens (total: 17390) | Latency: 176.13s
- **Composite Fitness $J$**: **32.4800**
- **13-Regime Benchmark Performance**: 893 misses, 16,980.0 worker-s (39.14% savings), 5038 deltas, Max P99: 16.00s
- **Innovation Rationale**: We incorporate conformal uncertainty bounds (`mean_set_size`) into the demand safety margin and add queue velocity damping to prevent queue buildup while maintaining actuation stability and cost efficiency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,17 +140,14 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
```

### Iteration 14: Program `6e0356e9-7362-4f25-9568-b9c1f88295f3`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `c1bd42d6-4b1b-4a57-9405-80689bd15c91`
- **LLM Call Telemetry**: 15438 prompt tokens, 495 completion tokens (total: 15933) | Latency: 178.3s
- **Composite Fitness $J$**: **312.3900**
- **13-Regime Benchmark Performance**: 468 misses, 18,925.0 worker-s (32.17% savings), 7862 deltas, Max P99: 16.00s
- **Innovation Rationale**: I have refined the demand-forward and continuous complexity dynamics by integrating explicit queue velocity (`cloud_queue_velocity`) and ingress acceleration (`ingress_acceleration`) to preempt queue formation more effectively under sudden burst regimes.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,14 +141,16 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0) and model ambiguity (mean_set_size)
+    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.20 + 0.5 * complexity_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.18 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 15: Program `f49a0fcd-1bd1-45e3-b866-091d4b1c9d11`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0c0e07c4-c225-4223-bb9b-8a7ead8b4c0e`
- **LLM Call Telemetry**: 14889 prompt tokens, 450 completion tokens (total: 15339) | Latency: 176.08s
- **Composite Fitness $J$**: **307.9240**
- **13-Regime Benchmark Performance**: 624 misses, 17,658.0 worker-s (36.71% savings), 4882 deltas, Max P99: 16.00s
- **Innovation Rationale**: To restore and surpass our peak performance score (307.9) while maintaining high cost savings and stability, we will adjust the conformal headroom factor and queue drain window back to the optimal calibrated parameters discovered in Program 1/2.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,13 +141,13 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size (mean_set_size)
-    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0)
+    # Scale safety headroom dynamically using RAPS prediction set size and velocity
+    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
+    DRAIN_WINDOW_S = 0.42
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 16: Program `5ec4c043-ba21-491d-8512-5fd7d4134fa8`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `25e6bdb7-dfc4-429f-972b-b6baf49d880a`
- **LLM Call Telemetry**: 16900 prompt tokens, 512 completion tokens (total: 17412) | Latency: 176.26s
- **Composite Fitness $J$**: **-11.2100**
- **13-Regime Benchmark Performance**: 919 misses, 17,375.0 worker-s (37.72% savings), 5376 deltas, Max P99: 16.00s
- **Innovation Rationale**: To improve cost savings while maintaining strict SLA safety and reducing scaling flapping, we can incorporate ingress velocity and acceleration into the conformal demand forecast, allowing the autoscaler to anticipate traffic ramps earlier without over-provisioning during steady states.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,14 +140,14 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    # ── Term 1: Conformal Demand-Forward with Velocity & Acceleration Anticipation ──
+    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps) + 0.2 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.25
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 17: Program `27e51b22-b407-4e31-bb98-b5dae18300ae`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `b16dc69a-8180-4bbb-8e28-1a066a844b5b`
- **LLM Call Telemetry**: 18015 prompt tokens, 341 completion tokens (total: 18356) | Latency: 210.91s
- **Composite Fitness $J$**: **179.1160**
- **13-Regime Benchmark Performance**: 561 misses, 18,312.0 worker-s (34.37% savings), 8692 deltas, Max P99: 16.00s
- **Innovation Rationale**: To optimize the continuous complexity scaling policy, we refine the safety margin coefficients and slightly streamline the queue drain window to improve cost savings while maintaining strict SLA compliance.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,14 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
     
-    SAFETY_MARGIN = 1.20 + 0.4 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.16 + 0.38 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.6
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 18: Program `53a923b2-9d8a-46d5-a8ba-ead2d78df2ab`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `1cb9f42d-883f-40d9-af45-a42aca3f6ebc`
- **LLM Call Telemetry**: 17129 prompt tokens, 468 completion tokens (total: 17597) | Latency: 202.57s
- **Composite Fitness $J$**: **307.9240**
- **13-Regime Benchmark Performance**: 624 misses, 17,658.0 worker-s (36.71% savings), 4882 deltas, Max P99: 16.00s
- **Innovation Rationale**: To optimize the fitness score, we will slightly refine the drain window and conformal coefficients to balance cost savings and deadline performance, restoring peak fitness.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.18 * max(0.0, state.mean_set_size - 1.0) + 0.05 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.5) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.42
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 19: Program `8e67e83e-58a1-4f7a-a261-749ba736f073`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `d6c970aa-310e-4978-ae17-86e248a79214`
- **LLM Call Telemetry**: 19209 prompt tokens, 714 completion tokens (total: 19923) | Latency: 193.92s
- **Composite Fitness $J$**: **-50.1960**
- **13-Regime Benchmark Performance**: 963 misses, 17,318.0 worker-s (37.93% savings), 5278 deltas, Max P99: 16.00s
- **Innovation Rationale**: We can refine the conformal demand-forward policy by adding a smoothing/hysteresis term on scaling deltas and scaling acceleration to further suppress flap churn while maintaining tight latency bounds.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,8 +142,8 @@
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
     # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps)
+    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
@@ -152,8 +152,14 @@
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Subtract In-Flight Booting Workers & Apply Scaling Stability Hysteresis ──
+    raw_target = demand_workers + drain_workers - state.booting_workers
+    
+    # Hysteresis dampening to prevent scaling oscillation / flapping
+    if abs(raw_target - state.active_workers) <= 1 and state.time_since_last_scale_s < 1.0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 20: Program `0ea9c50d-819d-4d1f-95ce-11df73b31cb7`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `b16dc69a-8180-4bbb-8e28-1a066a844b5b`
- **LLM Call Telemetry**: 18013 prompt tokens, 188 completion tokens (total: 18201) | Latency: 195.46s
- **Composite Fitness $J$**: **266.3520**
- **13-Regime Benchmark Performance**: 513 misses, 18,944.0 worker-s (32.10% savings), 7882 deltas, Max P99: 15.04s
- **Innovation Rationale**: Refined the complexity surge and relaxation coefficients to further optimize the safety margin dynamics and enhance cost savings without sacrificing tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,7 +150,7 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
     
-    SAFETY_MARGIN = 1.20 + 0.4 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.15 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 21: Program `156e49a4-5b22-4cbb-adc9-70d7a54e35a9`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `53a923b2-9d8a-46d5-a8ba-ead2d78df2ab`
- **LLM Call Telemetry**: 17181 prompt tokens, 465 completion tokens (total: 17646) | Latency: 192.33s
- **Composite Fitness $J$**: **305.2580**
- **13-Regime Benchmark Performance**: 629 misses, 17,941.0 worker-s (35.70% savings), 4824 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refine the drain budget window and conformal safety headroom factors slightly to improve responsiveness during transient bursts while maintaining high cost efficiency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.04 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.40
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 22: Program `228b63b7-1f3c-427b-93f0-441f01c33b9f`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `e7605d6a-d9ba-43e7-affa-194cc997ffef`
- **LLM Call Telemetry**: 19142 prompt tokens, 490 completion tokens (total: 19632) | Latency: 192.69s
- **Composite Fitness $J$**: **11.6640**
- **13-Regime Benchmark Performance**: 926 misses, 16,838.0 worker-s (39.65% savings), 4800 deltas, Max P99: 16.00s
- **Innovation Rationale**: To improve cost savings while maintaining safety against deadline misses, we incorporate velocity anticipation and fine-tuned conformal uncertainty bounds. This helps reduce unnecessary worker-seconds during stable periods while proactively preventing queue spikes.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,14 +140,14 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty & Velocity Anticipation ──
+    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.5
+    demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.2
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 23: Program `3e4a80c2-c49b-4f43-a80f-cf025b68dbf2`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `6e0356e9-7362-4f25-9568-b9c1f88295f3`
- **LLM Call Telemetry**: 18089 prompt tokens, 187 completion tokens (total: 18276) | Latency: 195.48s
- **Composite Fitness $J$**: **301.6320**
- **13-Regime Benchmark Performance**: 480 misses, 18,904.0 worker-s (32.24% savings), 7838 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the complexity-surge and relaxation coefficients slightly to improve cost savings and churn stability while preserving tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,7 +150,7 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.18 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.17 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 24: Program `fc431309-efb4-4598-a7af-839b09b023df`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `156e49a4-5b22-4cbb-adc9-70d7a54e35a9`
- **LLM Call Telemetry**: 17199 prompt tokens, 478 completion tokens (total: 17677) | Latency: 193.66s
- **Composite Fitness $J$**: **320.6300**
- **13-Regime Benchmark Performance**: 621 misses, 17,005.0 worker-s (39.05% savings), 4714 deltas, Max P99: 16.00s
- **Innovation Rationale**: To improve cost savings while maintaining safety, let's fine-tune the drain window and conformal headroom slightly to reduce over-provisioning worker-seconds during steady-state traffic.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.04 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.45
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 25: Program `372a88ba-376b-474e-8194-7c48f869bdba`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `8e67e83e-58a1-4f7a-a261-749ba736f073`
- **LLM Call Telemetry**: 19315 prompt tokens, 1218 completion tokens (total: 28334) | Latency: 229.53s
- **Composite Fitness $J$**: **496.6500**
- **13-Regime Benchmark Performance**: 384 misses, 18,275.0 worker-s (34.50% savings), 5871 deltas, Max P99: 17.00s
- **Innovation Rationale**: The current fitness decline (-50.19) is primarily driven by 963 deadline misses, likely caused by a sign error in the `p_fast_velocity` demand prediction and an overly aggressive scale-down policy. I am correcting the demand-trend logic to properly anticipate cloud RPS spikes when local acceptance collapses, increasing the conformal safety margin, and implementing asymmetric hysteresis to ensure rapid scale-up while damping scale-down oscillations.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,32 +141,36 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps) + 0.15 * max(0.0, state.ingress_acceleration)
-    demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
+    # Incorporate p_fast_velocity (dp_fast/dt). If p_fast drops, demand rises.
+    # conformal_safety scales with mean_set_size (RAPS uncertainty).
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.25
-    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # Drain backlog within 0.6s window; use velocity to anticipate queue growth.
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers & Apply Scaling Stability Hysteresis ──
-    raw_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    # Subtract 50% of booting workers to account for their imminent capacity.
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
     
-    # Hysteresis dampening to prevent scaling oscillation / flapping
-    if abs(raw_target - state.active_workers) <= 1 and state.time_since_last_scale_s < 1.0:
-        effective_target = state.active_workers
+    # Asymmetric hysteresis: Scale up immediately; scale down with 2.0s cooldown.
+    if raw_target < state.active_workers:
+        if state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+        else:
+            effective_target = raw_target
     else:
         effective_target = raw_target
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    # ── Term 4: Urgency Guard (SLA Rescue) ─────────────────────
+    # Panic if predicted latency (age + queue clearing time) exceeds safety threshold.
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 26: Program `b8bca682-8e24-40e1-8416-b135c2fdc4bc`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `3e4a80c2-c49b-4f43-a80f-cf025b68dbf2`
- **LLM Call Telemetry**: 17796 prompt tokens, 182 completion tokens (total: 17978) | Latency: 195.4s
- **Composite Fitness $J$**: **329.4840**
- **13-Regime Benchmark Performance**: 455 misses, 18,928.0 worker-s (32.16% savings), 7780 deltas, Max P99: 16.00s
- **Innovation Rationale**: Fine-tuned the safety margin coefficients and ambiguity modulation exponent to better balance worker churn and deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -148,9 +148,9 @@
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.17 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
+    SAFETY_MARGIN = 1.16 + 0.44 * complexity_surge + queue_surge + accel_surge - 0.13 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 27: Program `0ad43fbc-134b-41ed-b360-785bacf02639`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `156e49a4-5b22-4cbb-adc9-70d7a54e35a9`
- **LLM Call Telemetry**: 17201 prompt tokens, 468 completion tokens (total: 17669) | Latency: 195.56s
- **Composite Fitness $J$**: **320.6300**
- **13-Regime Benchmark Performance**: 621 misses, 17,005.0 worker-s (39.05% savings), 4714 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the conformal headroom and drain window parameters slightly to balance cost savings and deadline misses based on the top-performing seed configuration.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.04 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.45
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 28: Program `be2aa9ac-dc3c-4051-8845-a6cd2feb1d15`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `c2b54f07-f5aa-498a-b45e-a83e8965a44f`
- **LLM Call Telemetry**: 17668 prompt tokens, 623 completion tokens (total: 18291) | Latency: 192.42s
- **Composite Fitness $J$**: **32.4120**
- **13-Regime Benchmark Performance**: 893 misses, 17,014.0 worker-s (39.02% savings), 5038 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refining the demand forecast by incorporating velocity anticipation and adding light scale-down hysteresis will stabilize scaling actions and improve cost savings while preserving low tail latency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,7 +142,8 @@
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
     conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, -state.p_fast_velocity) * state.ingress_rps
+    demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.5
@@ -150,9 +151,12 @@
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Subtract In-Flight Booting Workers & Apply Scaling Hysteresis ─
+    raw_target = demand_workers + drain_workers - state.booting_workers
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 1.5 and state.cloud_queue_depth == 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 30: Program `b28b6d42-87da-4a43-89e3-28ef2e4360f6`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0c0e07c4-c225-4223-bb9b-8a7ead8b4c0e`
- **LLM Call Telemetry**: 19410 prompt tokens, 444 completion tokens (total: 19854) | Latency: 192.63s
- **Composite Fitness $J$**: **320.6300**
- **13-Regime Benchmark Performance**: 621 misses, 17,005.0 worker-s (39.05% savings), 4714 deltas, Max P99: 16.00s
- **Innovation Rationale**: To recover cost savings and balance tail safety while maintaining stable scaling actuation, we can restore the conformal headroom velocity term and fine-tune the queue drain buffer to handle workload fluctuations without incurring excessive worker-seconds.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,13 +141,13 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size (mean_set_size)
-    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0)
+    # Scale safety headroom dynamically using RAPS prediction set size and velocity
+    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
+    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
     DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 32: Program `ca307cbb-df71-47ef-a63f-285ef8f8fcaa`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `6e0356e9-7362-4f25-9568-b9c1f88295f3`
- **LLM Call Telemetry**: 17756 prompt tokens, 411 completion tokens (total: 18167) | Latency: 197.06s
- **Composite Fitness $J$**: **263.0080**
- **13-Regime Benchmark Performance**: 507 misses, 18,866.0 worker-s (32.38% savings), 8072 deltas, Max P99: 15.00s
- **Innovation Rationale**: Refined safety margins and scaling coefficients to improve cost efficiency and churn stability during dynamic workload shifts.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,14 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.18 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.16 + 0.43 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.52
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 33: Program `0edc1707-efa7-47cd-9a49-1098e0d22d7e`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `53a923b2-9d8a-46d5-a8ba-ead2d78df2ab`
- **LLM Call Telemetry**: 17205 prompt tokens, 470 completion tokens (total: 17675) | Latency: 192.72s
- **Composite Fitness $J$**: **314.1900**
- **13-Regime Benchmark Performance**: 624 misses, 17,075.0 worker-s (38.80% savings), 4780 deltas, Max P99: 16.00s
- **Innovation Rationale**: I have tuned the conformal factor coefficients and queue-drain window to optimize the trade-off between deadline safety and resource over-provisioning.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.035 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.45
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.42) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 34: Program `127258cf-a8e1-458c-84ba-33bc2f1d8432`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `e2779dc5-1735-4306-986c-4d827b244b72`
- **LLM Call Telemetry**: 17694 prompt tokens, 1005 completion tokens (total: 21201) | Latency: 198.92s
- **Composite Fitness $J$**: **469.0400**
- **13-Regime Benchmark Performance**: 420 misses, 17,985.0 worker-s (35.54% savings), 5715 deltas, Max P99: 17.00s
- **Innovation Rationale**: This evolution fixes the "InferLine blindness" by correctly utilizing the `p_fast_velocity` signal to anticipate cloud demand surges when edge performance collapses, and incorporates asymmetric hysteresis to stabilize scaling while maintaining safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,27 +140,31 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Velocity Anticipation ─────────
-    # Incorporate p_fast_velocity and ingress_acceleration to proactively scale
-    # ahead of demand spikes, reducing queue buildup and tail latency.
-    anticipated_demand = state.offered_cloud_rps + (max(0.0, state.p_fast_velocity) * state.ingress_rps) + max(0.0, state.ingress_acceleration * 0.1)
-    SAFETY_MARGIN = 1.15
-    demand_workers = math.ceil((anticipated_demand * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
+    # Use mean_set_size (RAPS uncertainty) to scale safety margin.
+    # Predict demand surge from p_fast collapse: demand_trend = -dp_fast/dt * ingress.
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.2) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    # Subtract 50% of booting workers; apply 2s scale-down cooldown if queue exists.
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    # ── Term 4: Urgency Guard (SLA Rescue) ─────────────────────
+    # Panic if predicted latency (age + queue clearing time) exceeds 13.5s threshold.
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 35: Program `ebe232b6-8a9c-4c69-ab70-68b3a68a1570`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `c1bd42d6-4b1b-4a57-9405-80689bd15c91`
- **LLM Call Telemetry**: 17709 prompt tokens, 484 completion tokens (total: 18193) | Latency: 195.37s
- **Composite Fitness $J$**: **312.3900**
- **13-Regime Benchmark Performance**: 468 misses, 18,925.0 worker-s (32.17% savings), 7862 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the continuous complexity scaling term by incorporating velocity surge, ingress acceleration, and a non-linear ambiguity boost to enhance preemptive scaling before queues form.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,14 +141,16 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0) and model ambiguity (mean_set_size)
+    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.20 + 0.5 * complexity_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.18 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 36: Program `9db825a3-c26d-4144-bff6-93023fb5357e`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0ad43fbc-134b-41ed-b360-785bacf02639`
- **LLM Call Telemetry**: 17192 prompt tokens, 469 completion tokens (total: 17661) | Latency: 193.78s
- **Composite Fitness $J$**: **311.2020**
- **13-Regime Benchmark Performance**: 620 misses, 17,669.0 worker-s (36.67% savings), 4896 deltas, Max P99: 16.00s
- **Innovation Rationale**: I will optimize the conformal factor and drain window parameters slightly to improve queue draining responsiveness during sudden load collapses while maintaining actuation stability.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.135 * max(0.0, state.mean_set_size - 1.0) + 0.025 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.42
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.42) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 37: Program `b125f4cd-522d-4db1-9fbd-3aa839fc4386`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 18285 prompt tokens, 977 completion tokens (total: 19262) | Latency: 189.47s
- **Composite Fitness $J$**: **496.6500**
- **13-Regime Benchmark Performance**: 384 misses, 18,275.0 worker-s (34.50% savings), 5871 deltas, Max P99: 17.00s
- **Innovation Rationale**: We will refine the scaling formula by incorporating conformal uncertainty adaptation via `mean_set_size`, predicting incoming workload trends using `p_fast_velocity`, and adding asymmetric scale-down cooldown with queue-based braking to improve cost savings and tail safety while minimizing flapping.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,29 +140,31 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
+    # Scale safety margin dynamically using RAPS uncertainty (mean_set_size).
+    # Anticipate demand surge from p_fast collapse via p_fast_velocity.
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    
+    # Asymmetric hysteresis: scale up immediately, scale down with cooldown and queue check.
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    # ── Term 4: Urgency Guard (SLA Rescue) ─────────────────────
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 38: Program `86fea0ef-dd7b-459d-9d7c-41b02fecb02a`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `b16dc69a-8180-4bbb-8e28-1a066a844b5b`
- **LLM Call Telemetry**: 17771 prompt tokens, 188 completion tokens (total: 17959) | Latency: 196.14s
- **Composite Fitness $J$**: **272.4380**
- **13-Regime Benchmark Performance**: 507 misses, 18,951.0 worker-s (32.08% savings), 7880 deltas, Max P99: 15.04s
- **Innovation Rationale**: Refined the continuous complexity scaling coefficients and base safety margin to balance churn stability and cost savings while maintaining robust deadline safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,7 +150,7 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
     
-    SAFETY_MARGIN = 1.20 + 0.4 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.16 + 0.44 * complexity_surge + queue_surge + accel_surge - 0.13 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 39: Program `1eb20966-792c-4575-97fe-ffefc33bcc51`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0edc1707-efa7-47cd-9a49-1098e0d22d7e`
- **LLM Call Telemetry**: 17212 prompt tokens, 485 completion tokens (total: 17697) | Latency: 191.37s
- **Composite Fitness $J$**: **305.2580**
- **13-Regime Benchmark Performance**: 629 misses, 17,941.0 worker-s (35.70% savings), 4824 deltas, Max P99: 16.00s
- **Innovation Rationale**: To recover from the fitness dip and reduce deadline misses while keeping cost savings high, we fine-tune the conformal headroom coefficient and slightly tighten the drain window responsiveness to accelerate queue clearing during fast-path collapse.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.035 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.145 * max(0.0, state.mean_set_size - 1.0) + 0.04 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.42) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.40
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 40: Program `d68ce5a9-135d-4023-9b15-e43ffa0309ae`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `25e6bdb7-dfc4-429f-972b-b6baf49d880a`
- **LLM Call Telemetry**: 21566 prompt tokens, 948 completion tokens (total: 22514) | Latency: 189.67s
- **Composite Fitness $J$**: **496.6500**
- **13-Regime Benchmark Performance**: 384 misses, 18,275.0 worker-s (34.50% savings), 5871 deltas, Max P99: 17.00s
- **Innovation Rationale**: To improve the fitness score, we will enhance the conformal scaling formula with proactive uncertainty adaptation, velocity-damped queue draining, and asymmetric hysteresis cooldown. This balances tail safety, minimizes flapping, and optimizes worker utilization.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,26 +141,29 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    # Incorporate p_fast_velocity and RAPS uncertainty (mean_set_size).
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
-    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    
+    # Asymmetric hysteresis: scale up immediately, scale down with cooldown and queue check.
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    # ── Term 4: Urgency Guard (SLA Rescue) ─────────────────────
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 41: Program `f5ff08a9-b843-4363-b2ce-fe068049407d`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `6e0356e9-7362-4f25-9568-b9c1f88295f3`
- **LLM Call Telemetry**: 20164 prompt tokens, 203 completion tokens (total: 20367) | Latency: 194.69s
- **Composite Fitness $J$**: **301.6320**
- **13-Regime Benchmark Performance**: 480 misses, 18,904.0 worker-s (32.24% savings), 7838 deltas, Max P99: 16.00s
- **Innovation Rationale**: To optimize cost savings and stability while maintaining tail safety, we fine-tune the safety margin base and scaling weights slightly to reduce excess worker-seconds during stable periods while retaining rapid surge reactivity.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,7 +150,7 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.18 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.17 + 0.43 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 42: Program `1e1cd732-7ed4-4b8d-bd0a-e7263bf52145`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `9db825a3-c26d-4144-bff6-93023fb5357e`
- **LLM Call Telemetry**: 17213 prompt tokens, 482 completion tokens (total: 17695) | Latency: 196.15s
- **Composite Fitness $J$**: **305.2580**
- **13-Regime Benchmark Performance**: 629 misses, 17,941.0 worker-s (35.70% savings), 4824 deltas, Max P99: 16.00s
- **Innovation Rationale**: To balance tail safety (minimizing deadline misses) and cost efficiency, we slightly refine the demand conformal factor and queue drain responsiveness, protecting against fast-path collapse while preventing excessive provisioning churn.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.135 * max(0.0, state.mean_set_size - 1.0) + 0.025 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.42) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.40
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 43: Program `727f7c6f-c76b-42b0-85e0-56a02cded585`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `be2aa9ac-dc3c-4051-8845-a6cd2feb1d15`
- **LLM Call Telemetry**: 19423 prompt tokens, 727 completion tokens (total: 20150) | Latency: 198.7s
- **Composite Fitness $J$**: **373.4140**
- **13-Regime Benchmark Performance**: 509 misses, 17,863.0 worker-s (35.97% savings), 5864 deltas, Max P99: 16.00s
- **Innovation Rationale**: I will refine the conformal safety scaling and queue drain damping to improve convergence stability and reduce actuation churn while safeguarding against deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,19 +141,19 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + max(0.0, -state.p_fast_velocity) * state.ingress_rps
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, -state.p_fast_velocity) * state.ingress_rps + 0.1 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    DRAIN_WINDOW_S = 0.6
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers & Apply Scaling Hysteresis ─
-    raw_target = demand_workers + drain_workers - state.booting_workers
-    if raw_target < state.active_workers and state.time_since_last_scale_s < 1.5 and state.cloud_queue_depth == 0:
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
         effective_target = state.active_workers
     else:
         effective_target = raw_target
```

### Iteration 44: Program `919f8430-008b-46e1-bd54-8132d178bb01`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `b16dc69a-8180-4bbb-8e28-1a066a844b5b`
- **LLM Call Telemetry**: 17771 prompt tokens, 410 completion tokens (total: 18181) | Latency: 199.28s
- **Composite Fitness $J$**: **209.4280**
- **13-Regime Benchmark Performance**: 588 misses, 19,106.0 worker-s (31.52% savings), 7514 deltas, Max P99: 16.00s
- **Innovation Rationale**: Optimized safety margin coefficients and refinement parameters to improve fitness while balancing cost savings and deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,14 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
     
-    SAFETY_MARGIN = 1.20 + 0.4 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.16 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.48
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 45: Program `5ee2380e-be94-4dfe-ad5c-5d16568c5317`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `156e49a4-5b22-4cbb-adc9-70d7a54e35a9`
- **LLM Call Telemetry**: 19457 prompt tokens, 472 completion tokens (total: 19929) | Latency: 197.27s
- **Composite Fitness $J$**: **311.2020**
- **13-Regime Benchmark Performance**: 620 misses, 17,669.0 worker-s (36.67% savings), 4896 deltas, Max P99: 16.00s
- **Innovation Rationale**: To restore fitness and improve tail safety while retaining cost efficiency, we slightly refine the conformal headroom factor and drain window responsiveness to reduce deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.04 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.145 * max(0.0, state.mean_set_size - 1.0) + 0.035 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.42
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.42) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 46: Program `837bd9dc-efde-4836-8801-bdb0594946e0`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `b125f4cd-522d-4db1-9fbd-3aa839fc4386`
- **LLM Call Telemetry**: 19529 prompt tokens, 590 completion tokens (total: 20119) | Latency: 192.33s
- **Composite Fitness $J$**: **506.9820**
- **13-Regime Benchmark Performance**: 388 misses, 18,219.0 worker-s (34.70% savings), 5585 deltas, Max P99: 14.00s
- **Innovation Rationale**: To further improve cost savings without sacrificing tail safety or stability, we can optimize the conformal safety multiplier and refine the queue drain damping window to allow slightly more aggressive scale-down during steady-state traffic periods while retaining robust burst protection.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,16 +141,15 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Scale safety margin dynamically using RAPS uncertainty (mean_set_size).
-    # Anticipate demand surge from p_fast collapse via p_fast_velocity.
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    # Slightly lean out safety margin for cost savings while preserving uncertainty buffer.
+    conformal_safety = 1.08 + 0.10 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 47: Program `8dd7f784-0781-4ef5-a70a-15ed4013a311`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `a6cc2775-9fad-4d0e-84bc-7dd13ef660b3`
- **LLM Call Telemetry**: 20173 prompt tokens, 144 completion tokens (total: 20317) | Latency: 200.89s
- **Composite Fitness $J$**: **358.7920**
- **13-Regime Benchmark Performance**: 428 misses, 18,774.0 worker-s (32.71% savings), 7740 deltas, Max P99: 15.00s
- **Innovation Rationale**: We refine the safety margin coefficients to further optimize cost savings while maintaining robust tail safety under sudden spikes.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,7 +150,7 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.15 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.14 * relaxation_factor
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 48: Program `43bd74f1-977f-435a-b7c0-173ae44c89d8`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `6355ef42-3b24-4cfb-9e08-7ab528abaeeb`
- **LLM Call Telemetry**: 19457 prompt tokens, 464 completion tokens (total: 19921) | Latency: 199.52s
- **Composite Fitness $J$**: **306.0900**
- **13-Regime Benchmark Performance**: 629 misses, 17,925.0 worker-s (35.75% savings), 4808 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the conformal headroom factor and drain window parameters slightly to improve queue draining responsiveness during sudden load spikes.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.145 * max(0.0, state.mean_set_size - 1.0) + 0.035 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.40
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.42) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 49: Program `10344c28-4f62-4d25-af57-6730f7ad328b`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `b125f4cd-522d-4db1-9fbd-3aa839fc4386`
- **LLM Call Telemetry**: 21364 prompt tokens, 598 completion tokens (total: 21962) | Latency: 191.12s
- **Composite Fitness $J$**: **506.9820**
- **13-Regime Benchmark Performance**: 388 misses, 18,219.0 worker-s (34.70% savings), 5585 deltas, Max P99: 14.00s
- **Innovation Rationale**: To optimize the fitness score, we can fine-tune the conformal safety multiplier and queue-drain window to extract higher cost savings while preserving strict tail safety. Specifically, slightly leaning out the safety margin and reducing the drain window slightly will lower worker-seconds without introducing deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,16 +141,15 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Scale safety margin dynamically using RAPS uncertainty (mean_set_size).
-    # Anticipate demand surge from p_fast collapse via p_fast_velocity.
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    # Slightly optimize safety margin for better cost savings while preserving buffer.
+    conformal_safety = 1.08 + 0.10 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 50: Program `ee175139-d9fd-4f68-a886-c814013cc3f3`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `86fea0ef-dd7b-459d-9d7c-41b02fecb02a`
- **LLM Call Telemetry**: 17447 prompt tokens, 481 completion tokens (total: 17928) | Latency: 199.68s
- **Composite Fitness $J$**: **358.7920**
- **13-Regime Benchmark Performance**: 428 misses, 18,774.0 worker-s (32.71% savings), 7740 deltas, Max P99: 15.00s
- **Innovation Rationale**: To recover the higher fitness score from previous successful runs (around 358), we will fine-tune the Safety Margin coefficients and non-linear ambiguity modulation back towards the balanced parameters of Program 1.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,16 +141,16 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and ingress acceleration
+    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.1)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.16 + 0.44 * complexity_surge + queue_surge + accel_surge - 0.13 * relaxation_factor
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 51: Program `88b335eb-079f-409a-9ad1-bcb4b96b49bb`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `1e1cd732-7ed4-4b8d-bd0a-e7263bf52145`
- **LLM Call Telemetry**: 19455 prompt tokens, 231 completion tokens (total: 19686) | Latency: 197.64s
- **Composite Fitness $J$**: **307.9240**
- **13-Regime Benchmark Performance**: 624 misses, 17,658.0 worker-s (36.71% savings), 4882 deltas, Max P99: 16.00s
- **Innovation Rationale**: To recover the fitness score while maintaining stability, let's optimize the drain window and velocity coefficients to slightly increase responsiveness without incurring extra churn or deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -146,8 +146,8 @@
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.42
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 52: Program `0083bd23-02bb-4bfa-afe3-cccdf3302da8`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `d68ce5a9-135d-4023-9b15-e43ffa0309ae`
- **LLM Call Telemetry**: 18492 prompt tokens, 836 completion tokens (total: 19328) | Latency: 189.93s
- **Composite Fitness $J$**: **536.3200**
- **13-Regime Benchmark Performance**: 412 misses, 18,910.0 worker-s (32.22% savings), 4500 deltas, Max P99: 13.24s
- **Innovation Rationale**: To improve cost savings while maintaining tail safety and reducing actuation churn, we can refine the conformal safety margin and drain window parameters. We'll also adjust the hysteresis cooldown conditions to reduce scaling deltas.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,22 +141,22 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Incorporate p_fast_velocity and RAPS uncertainty (mean_set_size).
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    # Lean out safety margin slightly for better cost savings while preserving buffer.
+    conformal_safety = 1.08 + 0.10 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
     raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
     
-    # Asymmetric hysteresis: scale up immediately, scale down with cooldown and queue check.
-    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+    # Asymmetric hysteresis: scale up immediately, scale down with a slightly extended cooldown.
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.5 and state.cloud_queue_depth > 0:
         effective_target = state.active_workers
     else:
         effective_target = raw_target
```

### Iteration 53: Program `6b353f38-bb73-4491-bf35-f2399fe390bf`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `ebe232b6-8a9c-4c69-ab70-68b3a68a1570`
- **LLM Call Telemetry**: 19891 prompt tokens, 187 completion tokens (total: 20078) | Latency: 199.09s
- **Composite Fitness $J$**: **329.4840**
- **13-Regime Benchmark Performance**: 455 misses, 18,928.0 worker-s (32.16% savings), 7780 deltas, Max P99: 16.00s
- **Innovation Rationale**: Adjust the non-linear ambiguity exponent and base safety margin coefficients to further optimize the trade-off between cost savings and tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -148,9 +148,9 @@
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.06)
     
-    SAFETY_MARGIN = 1.18 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.16 + 0.43 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 54: Program `0efd6348-3384-48d6-9b7f-4fd414dc52f3`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `fc431309-efb4-4598-a7af-839b09b023df`
- **LLM Call Telemetry**: 19442 prompt tokens, 993 completion tokens (total: 32584) | Latency: 252.51s
- **Composite Fitness $J$**: **705.9920**
- **13-Regime Benchmark Performance**: 136 misses, 18,819.0 worker-s (32.55% savings), 6627 deltas, Max P99: 12.00s
- **Innovation Rationale**: To improve the fitness score, we must address the high churn (4,714 deltas) and significant deadline misses (621) by stabilizing the scaling logic and removing the counter-productive subtraction of booting workers. This modification integrates demand and queue terms before rounding to reduce jitter, adds a scale-down cooldown for stability, and implements a proportional SLA rescue instead of a cluster-wide spike.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,33 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    # ── Term 1: Semantic-Aware Demand (RPS) ──
+    # Base multiplier + headroom for prediction complexity (mean_set_size) 
+    # and proactive response to semantic collapse (negative p_fast_velocity).
+    conformal_factor = 1.15 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.50 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * conformal_factor
+    # Proactive surge term for sudden ingress acceleration
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.20
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    # Drain backlog over a 0.5s window, incorporating queue velocity to catch growth early.
+    drain_rps = (state.cloud_queue_depth + state.cloud_queue_velocity * 0.45) / 0.50
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation ──
+    # Sum all RPS requirements before ceiling to minimize rounding-induced flapping.
+    # We do not subtract booting_workers; the target represents desired total fleet size.
+    total_rps = demand_rps + surge_rps + max(0.0, drain_rps)
+    effective_target = math.ceil(total_rps / mu)
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    # ── Term 4: Stability & SLA Safety ──
+    # Hysteresis: Prevent aggressive down-scaling if a scaling action occurred recently (<2s).
+    if effective_target < state.active_workers and state.time_since_last_scale_s < 2.0:
+        effective_target = state.active_workers
+
+    # Proportional SLA Rescue: If tasks age beyond 10s, increment capacity to clear backlog
+    # without the massive churn caused by a binary jump to max_workers.
+    if state.oldest_task_age_s > 10.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 2)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 55: Program `f13e1d00-bad1-49fa-bb03-4fe6e59639b2`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `127258cf-a8e1-458c-84ba-33bc2f1d8432`
- **LLM Call Telemetry**: 20703 prompt tokens, 586 completion tokens (total: 21289) | Latency: 199.27s
- **Composite Fitness $J$**: **506.9820**
- **13-Regime Benchmark Performance**: 388 misses, 18,219.0 worker-s (34.70% savings), 5585 deltas, Max P99: 14.00s
- **Innovation Rationale**: To improve the fitness score and regain peak performance, we will refine the safety margin and drain window parameters slightly to balance cost savings and deadline misses, incorporating a tighter uncertainty factor.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,16 +141,15 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Use mean_set_size (RAPS uncertainty) to scale safety margin.
-    # Predict demand surge from p_fast collapse: demand_trend = -dp_fast/dt * ingress.
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    # Slightly optimize safety margin for better cost savings while preserving buffer.
+    conformal_safety = 1.08 + 0.10 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
     anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 56: Program `239503e9-7a4a-42de-889f-50bc5e5ea501`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `ee175139-d9fd-4f68-a886-c814013cc3f3`
- **LLM Call Telemetry**: 19886 prompt tokens, 147 completion tokens (total: 20033) | Latency: 201.2s
- **Composite Fitness $J$**: **327.4200**
- **13-Regime Benchmark Performance**: 457 misses, 18,760.0 worker-s (32.76% savings), 7788 deltas, Max P99: 15.00s
- **Innovation Rationale**: We slightly tune the safety margin baseline and complexity scaling weights to improve churn stability and cost efficiency while preserving tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,7 +150,7 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
+    SAFETY_MARGIN = 1.13 + 0.39 * complexity_surge + queue_surge + accel_surge - 0.16 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 57: Program `91a18882-7535-403b-b426-1558ca07bc6a`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `f49a0fcd-1bd1-45e3-b866-091d4b1c9d11`
- **LLM Call Telemetry**: 17785 prompt tokens, 428 completion tokens (total: 18213) | Latency: 193.24s
- **Composite Fitness $J$**: **305.2580**
- **13-Regime Benchmark Performance**: 629 misses, 17,941.0 worker-s (35.70% savings), 4824 deltas, Max P99: 16.00s
- **Innovation Rationale**: I will slightly adjust the conformal headroom coefficient and drain window to improve responsiveness and reduce deadline misses while keeping churn stable.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,12 +142,12 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.0 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.04 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.40
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 58: Program `ba168308-3f88-42df-947a-64b94124a700`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `228b63b7-1f3c-427b-93f0-441f01c33b9f`
- **LLM Call Telemetry**: 20497 prompt tokens, 665 completion tokens (total: 21162) | Latency: 187.72s
- **Composite Fitness $J$**: **345.4200**
- **13-Regime Benchmark Performance**: 551 misses, 17,910.0 worker-s (35.81% savings), 5582 deltas, Max P99: 16.00s
- **Innovation Rationale**: To improve tail safety and reduce deadline misses while keeping cost efficiency high, we refine the demand-forward safety margin and add asymmetric scale-down hysteresis to prevent premature capacity drops during queue drain phases.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,18 +141,22 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty & Velocity Anticipation ──
-    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.5
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.6
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.2
+    DRAIN_WINDOW_S = 0.55
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 59: Program `cf092150-7ee4-4396-ac60-7a2d60cb950d`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `27e51b22-b407-4e31-bb98-b5dae18300ae`
- **LLM Call Telemetry**: 17486 prompt tokens, 688 completion tokens (total: 18174) | Latency: 197.45s
- **Composite Fitness $J$**: **358.7920**
- **13-Regime Benchmark Performance**: 428 misses, 18,774.0 worker-s (32.71% savings), 7740 deltas, Max P99: 15.00s
- **Innovation Rationale**: We fine-tune the safety margin coefficients and queue drain window to improve cost efficiency and churn stability while preserving tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -144,20 +144,20 @@
     # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and ingress acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.1)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.16 + 0.38 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.6
+    DRAIN_WINDOW_S = 0.5
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 60: Program `01418977-ebfa-4d79-8111-8182939cbfc0`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0ad43fbc-134b-41ed-b360-785bacf02639`
- **LLM Call Telemetry**: 19976 prompt tokens, 471 completion tokens (total: 20447) | Latency: 193.6s
- **Composite Fitness $J$**: **9.9160**
- **13-Regime Benchmark Performance**: 919 misses, 16,712.0 worker-s (40.10% savings), 4980 deltas, Max P99: 16.00s
- **Innovation Rationale**: We refine the conformal safety scaling and queue-drain response to handle rapid ingress transitions more smoothly, reducing actuation churn while preserving deadline guarantees.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,13 +141,13 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
+    # Scale safety headroom dynamically using RAPS prediction set size and semantic velocity
+    conformal_factor = 1.0 + 0.12 * max(0.0, state.mean_set_size - 1.0) + 0.025 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.50
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
```

### Iteration 61: Program `ed80eb99-ae5d-439d-b397-5707fcf4389a`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `e7605d6a-d9ba-43e7-affa-194cc997ffef`
- **LLM Call Telemetry**: 20487 prompt tokens, 976 completion tokens (total: 24214) | Latency: 192.09s
- **Composite Fitness $J$**: **1149.2260**
- **13-Regime Benchmark Performance**: 0 misses, 20,957.0 worker-s (24.89% savings), 404 deltas, Max P99: 5.00s
- **Innovation Rationale**: Re-incorporating high-performing demand-forward and asymmetric scaling logic from Island 0 leaders to eliminate the 893 deadline misses caused by aggressive scale-down and lack of trend prediction.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,32 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
+    # Anticipate demand surge from p_fast collapse (semantic drift) via p_fast_velocity.
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
-    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    # Subtract only 50% of booting workers to avoid under-provisioning during ramps.
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    
+    # Asymmetric hysteresis: scale up immediately, scale down with 3.0s cooldown and queue check.
+    if raw_target < state.active_workers and (state.time_since_last_scale_s < 3.0 or state.cloud_queue_depth > 0):
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    # ── Term 4: Urgency Guard (SLA Rescue) ─────────────────────
+    # Use clearance estimation to trigger max-capacity rescue before deadlines miss.
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.0 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 62: Program `f02231fc-cc81-4275-85d0-603182c74ba1`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `ee175139-d9fd-4f68-a886-c814013cc3f3`
- **LLM Call Telemetry**: 20737 prompt tokens, 338 completion tokens (total: 21075) | Latency: 200.62s
- **Composite Fitness $J$**: **278.8700**
- **13-Regime Benchmark Performance**: 528 misses, 18,835.0 worker-s (32.49% savings), 7336 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the safety margin coefficients and slightly shortened the drain window to improve prompt responsiveness under sudden surge conditions while preserving cost efficiency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,14 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
+    SAFETY_MARGIN = 1.12 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.16 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.48
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 63: Program `353eeb32-73a9-49fe-97c1-8d9f8de0540d`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `9db825a3-c26d-4144-bff6-93023fb5357e`
- **LLM Call Telemetry**: 18259 prompt tokens, 287 completion tokens (total: 18546) | Latency: 197.69s
- **Composite Fitness $J$**: **587.4860**
- **13-Regime Benchmark Performance**: 335 misses, 18,677.0 worker-s (33.06% savings), 5030 deltas, Max P99: 16.00s
- **Innovation Rationale**: To optimize the cost-efficiency and stability trade-offs, we add a gentle scale-down cooldown hysteresis using `state.time_since_last_scale_s` and slightly lean out the drain window to reduce unnecessary worker-seconds while preserving tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -151,7 +151,13 @@
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    raw_target = demand_workers + drain_workers - state.booting_workers
+    
+    # Hysteresis: Prevent rapid scale-down flapping if scaling occurred recently
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 64: Program `fd184f2d-c34f-403e-8a8d-b7bfe09adc98`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `ba168308-3f88-42df-947a-64b94124a700`
- **LLM Call Telemetry**: 18740 prompt tokens, 515 completion tokens (total: 19255) | Latency: 193.28s
- **Composite Fitness $J$**: **505.2640**
- **13-Regime Benchmark Performance**: 391 misses, 18,588.0 worker-s (33.38% savings), 5558 deltas, Max P99: 15.00s
- **Innovation Rationale**: We refine the conformal safety buffer and velocity response to improve tail safety and reduce deadline misses while keeping worker costs lean.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,13 +141,13 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty & Velocity Anticipation ──
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.6
+    conformal_safety = 1.15 + 0.15 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.75 + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.55
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    DRAIN_WINDOW_S = 0.5
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 65: Program `28d20725-ac6d-4609-aa56-d30d9575b00a`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `6e0356e9-7362-4f25-9568-b9c1f88295f3`
- **LLM Call Telemetry**: 20755 prompt tokens, 181 completion tokens (total: 20936) | Latency: 198.5s
- **Composite Fitness $J$**: **358.7920**
- **13-Regime Benchmark Performance**: 428 misses, 18,774.0 worker-s (32.71% savings), 7740 deltas, Max P99: 15.00s
- **Innovation Rationale**: We refine the complexity-adaptive safety margin and ambiguity exponent to better balance tail safety and cost efficiency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -148,9 +148,9 @@
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.18 + 0.45 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
```

### Iteration 66: Program `123a97cf-8ea4-47f6-a478-15cdf87133de`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `1e1cd732-7ed4-4b8d-bd0a-e7263bf52145`
- **LLM Call Telemetry**: 20351 prompt tokens, 655 completion tokens (total: 21006) | Latency: 189.46s
- **Composite Fitness $J$**: **399.9640**
- **13-Regime Benchmark Performance**: 511 misses, 18,138.0 worker-s (34.99% savings), 5282 deltas, Max P99: 16.00s
- **Innovation Rationale**: To address the recent fitness regression and achieve an optimal balance between cost efficiency and deadline safety, we will tune the conformal scaling factor and incorporate hysteresis/cooldown management to minimize unnecessary actuation churn.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,16 +142,22 @@
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
     # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
+    conformal_factor = 1.08 + 0.12 * max(0.0, state.mean_set_size - 1.0) + 0.02 * max(0.0, state.p_fast_velocity)
     demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.50
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    raw_target = demand_workers + drain_workers - state.booting_workers
+
+    # Hysteresis: Prevent rapid scale-down flapping if scaling occurred recently
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 67: Program `97af42a3-d88c-4b86-b475-7a6d2e66c061`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `727f7c6f-c76b-42b0-85e0-56a02cded585`
- **LLM Call Telemetry**: 21082 prompt tokens, 528 completion tokens (total: 21610) | Latency: 189.25s
- **Composite Fitness $J$**: **418.3700**
- **13-Regime Benchmark Performance**: 464 misses, 18,385.0 worker-s (34.10% savings), 5844 deltas, Max P99: 16.00s
- **Innovation Rationale**: We refine the demand-forward anticipation term and balance the drain window and safety factors to recover high fitness while maintaining zero deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,13 +141,13 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + max(0.0, -state.p_fast_velocity) * state.ingress_rps + 0.1 * max(0.0, state.ingress_acceleration)
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, -state.p_fast_velocity) * state.ingress_rps * 0.8 + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 68: Program `a1ccc293-5a06-4acc-b2fb-413840552a62`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `86fea0ef-dd7b-459d-9d7c-41b02fecb02a`
- **LLM Call Telemetry**: 20756 prompt tokens, 806 completion tokens (total: 21562) | Latency: 195.99s
- **Composite Fitness $J$**: **238.3500**
- **13-Regime Benchmark Performance**: 512 misses, 18,895.0 worker-s (32.28% savings), 8464 deltas, Max P99: 16.00s
- **Innovation Rationale**: To restore fitness and improve churn stability while maintaining strong tail safety, we refine the safety margin coefficients and decouple the queue-drain velocity damping to prevent premature worker scaling and excessive fluctuations.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -144,22 +144,22 @@
     # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and ingress acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.1)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.16 + 0.44 * complexity_surge + queue_surge + accel_surge - 0.13 * relaxation_factor
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 69: Program `94fec1f5-114d-4cd3-bcdf-5de3be2b0357`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `f49a0fcd-1bd1-45e3-b866-091d4b1c9d11`
- **LLM Call Telemetry**: 20474 prompt tokens, 272 completion tokens (total: 20746) | Latency: 190.81s
- **Composite Fitness $J$**: **577.3200**
- **13-Regime Benchmark Performance**: 352 misses, 18,710.0 worker-s (32.94% savings), 4892 deltas, Max P99: 16.00s
- **Innovation Rationale**: To improve fitness and recover strong tail safety while maintaining cost savings, we can add a lightweight scaling cooldown/hysteresis check to suppress rapid actuation churn, combined with a slightly more responsive conformal demand multiplier.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -151,7 +151,13 @@
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    raw_target = demand_workers + drain_workers - state.booting_workers
+
+    # Hysteresis: Prevent rapid scale-down flapping if scaling occurred recently
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 70: Program `601f19e3-939a-4b1f-96e8-9dd8bca6798a`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `800ebce7-8d30-4a33-b144-bcebab6a14e8`
- **LLM Call Telemetry**: 21014 prompt tokens, 936 completion tokens (total: 21950) | Latency: 189.96s
- **Composite Fitness $J$**: **528.0820**
- **13-Regime Benchmark Performance**: 366 misses, 18,334.0 worker-s (34.29% savings), 5596 deltas, Max P99: 17.00s
- **Innovation Rationale**: We refine the scaling law by combining Conformal uncertainty adaptation (`mean_set_size`), `p_fast_velocity` trend anticipation for semantic drift, damped queue velocity (`cloud_queue_velocity`), and an asymmetric scale-down cooldown with queue check to minimize worker-seconds while preserving zero deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,29 +140,27 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 71: Program `2d1e0898-942b-4093-a192-b6057fb4a464`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `3385f5d0-2f7a-4e49-9e49-7648bc6f99b8`
- **LLM Call Telemetry**: 17879 prompt tokens, 418 completion tokens (total: 18297) | Latency: 187.61s
- **Composite Fitness $J$**: **795.8560**
- **13-Regime Benchmark Performance**: 86 misses, 20,647.0 worker-s (26.00% savings), 5760 deltas, Max P99: 11.00s
- **Innovation Rationale**: Refined the demand-forward and ambiguity modulation logic to dynamically adapt to complexity surges and relaxation patterns, improving preemptive scaling while maintaining cost efficiency and tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,12 +140,16 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Lean out safety margin slightly for better cost savings while preserving buffer.
-    conformal_safety = 1.08 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
-    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
+    # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
+    complexity_surge = max(0.0, -state.p_fast_velocity)
+    relaxation_factor = max(0.0, state.p_fast_velocity)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
+
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
+    adjusted_demand = state.offered_cloud_rps * ambiguity_boost
+    demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
     DRAIN_WINDOW_S = 0.55
```

### Iteration 72: Program `c3845087-4aeb-4060-ae1a-5e05ec8cb72e`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0efd6348-3384-48d6-9b7f-4fd414dc52f3`
- **LLM Call Telemetry**: 22316 prompt tokens, 1185 completion tokens (total: 31517) | Latency: 211.18s
- **Composite Fitness $J$**: **1149.8300**
- **13-Regime Benchmark Performance**: 0 misses, 20,955.0 worker-s (24.89% savings), 392 deltas, Max P99: 5.00s
- **Innovation Rationale**: To improve fitness, we must reduce the high churn (6,627 deltas) and deadline misses (136) observed in the current policy. We'll achieve this by: (1) incorporating `booting_workers` into the target logic to prevent redundant scaling actions while workers are in flight; (2) increasing the queue drainage window and the down-scaling hysteresis for better stability; and (3) implementing a more nuanced, multi-stage SLA rescue mechanism.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,32 +141,37 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Semantic-Aware Demand (RPS) ──
-    # Base multiplier + headroom for prediction complexity (mean_set_size) 
-    # and proactive response to semantic collapse (negative p_fast_velocity).
-    conformal_factor = 1.15 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.50 * max(0.0, -state.p_fast_velocity)
-    demand_rps = state.offered_cloud_rps * conformal_factor
-    # Proactive surge term for sudden ingress acceleration
-    surge_rps = max(0.0, state.ingress_acceleration) * 0.20
+    # Headroom for complexity (mean_set_size) and semantic collapse (p_fast_velocity).
+    c_factor = 1.20 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.40 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * c_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.30
 
     # ── Term 2: Queue Drain Budget (RPS) ──
-    # Drain backlog over a 0.5s window, incorporating queue velocity to catch growth early.
-    drain_rps = (state.cloud_queue_depth + state.cloud_queue_velocity * 0.45) / 0.50
+    # Drain backlog over a 0.7s window. Dampen velocity to avoid over-reacting to noise.
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.70
 
     # ── Term 3: Target Calculation ──
-    # Sum all RPS requirements before ceiling to minimize rounding-induced flapping.
-    # We do not subtract booting_workers; the target represents desired total fleet size.
-    total_rps = demand_rps + surge_rps + max(0.0, drain_rps)
-    effective_target = math.ceil(total_rps / mu)
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
 
     # ── Term 4: Stability & SLA Safety ──
-    # Hysteresis: Prevent aggressive down-scaling if a scaling action occurred recently (<2s).
-    if effective_target < state.active_workers and state.time_since_last_scale_s < 2.0:
-        effective_target = state.active_workers
+    # Use 'provisioned' (active + booting) as a reference to minimize redundant scaling.
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # Proportional SLA Rescue: If tasks age beyond 10s, increment capacity to clear backlog
-    # without the massive churn caused by a binary jump to max_workers.
-    if state.oldest_task_age_s > 10.0 and state.cloud_queue_depth > 0:
-        effective_target = max(effective_target, state.active_workers + 2)
+    if desired_k < state.active_workers:
+        # Scale-down hysteresis: wait for cooldown and ensure queue is clear.
+        if state.time_since_last_scale_s < 4.0 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        # Maintain target if desired is already covered by workers in-flight.
+        effective_target = provisioned
+
+    # Proactive SLA Rescue: escalate capacity as tasks age to prevent deadline misses.
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 73: Program `1cca2390-16d1-4d73-a950-0d902279380e`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `25e6bdb7-dfc4-429f-972b-b6baf49d880a`
- **LLM Call Telemetry**: 18955 prompt tokens, 933 completion tokens (total: 19888) | Latency: 191.22s
- **Composite Fitness $J$**: **528.0820**
- **13-Regime Benchmark Performance**: 366 misses, 18,334.0 worker-s (34.29% savings), 5596 deltas, Max P99: 17.00s
- **Innovation Rationale**: To improve the autoscaler's fitness score (specifically targeting zero-miss stability, reduced flapping, and efficient cost savings), we will incorporate predictive demand trends (`p_fast_velocity` and `ingress_acceleration`), robust queue-drain damping, and an asymmetric hysteresis guard for scale-down decisions.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,27 +140,27 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
+    # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
     conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
-    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 74: Program `16c01f60-f161-4bd6-8734-1411b15d0db4`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `b16dc69a-8180-4bbb-8e28-1a066a844b5b`
- **LLM Call Telemetry**: 20448 prompt tokens, 394 completion tokens (total: 20842) | Latency: 197.79s
- **Composite Fitness $J$**: **217.0740**
- **13-Regime Benchmark Performance**: 542 misses, 19,083.0 worker-s (31.60% savings), 8282 deltas, Max P99: 15.00s
- **Innovation Rationale**: We refine the safety margin coefficients and queue-drain dynamics to balance cost savings and deadline stability.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,16 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.1)
     
-    SAFETY_MARGIN = 1.20 + 0.4 * complexity_surge + queue_surge + accel_surge - 0.1 * relaxation_factor
+    SAFETY_MARGIN = 1.15 + 0.38 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.52
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 75: Program `78497c29-f06d-449a-95ac-56fbe8175262`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `88b335eb-079f-409a-9ad1-bcb4b96b49bb`
- **LLM Call Telemetry**: 20905 prompt tokens, 642 completion tokens (total: 21547) | Latency: 188.7s
- **Composite Fitness $J$**: **663.4220**
- **13-Regime Benchmark Performance**: 274 misses, 19,359.0 worker-s (30.61% savings), 4704 deltas, Max P99: 14.00s
- **Innovation Rationale**: To improve cost efficiency and churn stability while avoiding deadline misses, we refine the demand-forward and queue-drain terms by integrating a smoother scale-down hysteresis and utilizing proactive ingress acceleration.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,17 +141,20 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    conformal_factor = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0) + 0.25 * max(0.0, -state.p_fast_velocity)
+    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor + max(0.0, state.ingress_acceleration) * 0.20) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.40) / DRAIN_WINDOW_S
+    DRAIN_WINDOW_S = 0.50
+    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    raw_target = demand_workers + drain_workers - state.booting_workers
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.5 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 76: Program `23bebabc-c44b-48bb-9745-2cc057a04c2a`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `127258cf-a8e1-458c-84ba-33bc2f1d8432`
- **LLM Call Telemetry**: 21385 prompt tokens, 619 completion tokens (total: 22004) | Latency: 192.72s
- **Composite Fitness $J$**: **528.0820**
- **13-Regime Benchmark Performance**: 366 misses, 18,334.0 worker-s (34.29% savings), 5596 deltas, Max P99: 17.00s
- **Innovation Rationale**: To recover fitness and optimize cost savings while maintaining tail safety and churn stability, we will fine-tune the conformal safety margin and drain window. Slightly lowering the baseline safety multiplier from `1.12` to `1.10` reduces unnecessary GPU worker-seconds, while refining the cooldown and queue velocity damping prevents flapping.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,16 +141,15 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Use mean_set_size (RAPS uncertainty) to scale safety margin.
-    # Predict demand surge from p_fast collapse: demand_trend = -dp_fast/dt * ingress.
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    # Lean out safety margin slightly for better cost efficiency without risking SLA misses.
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
     anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 77: Program `f0c63bf5-5b15-4dd7-a5cd-30695b937575`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `28d20725-ac6d-4609-aa56-d30d9575b00a`
- **LLM Call Telemetry**: 20434 prompt tokens, 732 completion tokens (total: 32770) | Latency: 237.77s
- **Composite Fitness $J$**: **795.8560**
- **13-Regime Benchmark Performance**: 86 misses, 20,647.0 worker-s (26.00% savings), 5760 deltas, Max P99: 11.00s
- **Innovation Rationale**: To improve fitness, I will restore the superior velocity-aware queue draining, asymmetric hysteresis scaling, and clearance-based urgency guard from the high-performing Attempt 1. These modifications specifically target the high churn and poor tail safety observed in the current metrics.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -154,23 +154,24 @@
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    # Incorporate cloud_queue_velocity to differentiate transient spikes from sustained backlogs.
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    # Use partial booting offset and asymmetric hysteresis to reduce churn stability penalties.
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.5 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    # ── Term 4: Urgency Guard (SLA Clearance Rescue) ─────────────────────
+    # Forecast if current max capacity can clear the queue before the 15s deadline.
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 78: Program `3db31c2f-f751-42f8-a049-7eb6dae3f15b`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `f49a0fcd-1bd1-45e3-b866-091d4b1c9d11`
- **LLM Call Telemetry**: 18993 prompt tokens, 917 completion tokens (total: 19910) | Latency: 178.74s
- **Composite Fitness $J$**: **1149.8300**
- **13-Regime Benchmark Performance**: 0 misses, 20,955.0 worker-s (24.89% savings), 392 deltas, Max P99: 5.00s
- **Innovation Rationale**: To recover the high fitness achieved by Program 1 (1149.83), we reintroduce proactive scale-down hysteresis, smoother RPS aggregation, and multi-tier SLA rescue protections while maintaining conformal telemetry integration.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,31 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    # ── Term 1: Semantic-Aware Demand (RPS) ──
+    c_factor = 1.20 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.40 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * c_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.30
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.70
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation & Hysteresis ──
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        if state.time_since_last_scale_s < 4.0 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 79: Program `2ca72076-96f3-4a11-bfd2-62dd9057df83`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `228b63b7-1f3c-427b-93f0-441f01c33b9f`
- **LLM Call Telemetry**: 20933 prompt tokens, 660 completion tokens (total: 21593) | Latency: 186.89s
- **Composite Fitness $J$**: **425.0100**
- **13-Regime Benchmark Performance**: 537 misses, 18,515.0 worker-s (33.64% savings), 4246 deltas, Max P99: 16.00s
- **Innovation Rationale**: To optimize cost efficiency and tail safety, we refine the conformal demand safety margin and incorporate asymmetric scale-down cooldown hysteresis to prevent flapping churn while maintaining zero SLA deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,18 +141,22 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty & Velocity Anticipation ──
-    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.5
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.6
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.2
+    DRAIN_WINDOW_S = 0.55
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.5 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 80: Program `4fcac7bc-a4e4-4cf0-b75c-f94e30451a44`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `f5ff08a9-b843-4363-b2ce-fe068049407d`
- **LLM Call Telemetry**: 21057 prompt tokens, 756 completion tokens (total: 21813) | Latency: 195.87s
- **Composite Fitness $J$**: **78.8040**
- **13-Regime Benchmark Performance**: 686 misses, 18,718.0 worker-s (32.91% savings), 8182 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refining the scaling formula to optimize cost savings and maintain high tail safety by tightening the safety margin parameters and smoothing queue drain dynamics.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -144,22 +144,20 @@
     # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
-    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.07)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.015)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.04)
     
-    SAFETY_MARGIN = 1.17 + 0.43 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
+    SAFETY_MARGIN = 1.10 + 0.35 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 81: Program `fdf4ba0f-a52b-4cf3-b3af-f1441dbc277b`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `53a923b2-9d8a-46d5-a8ba-ead2d78df2ab`
- **LLM Call Telemetry**: 21509 prompt tokens, 484 completion tokens (total: 21993) | Latency: 187.57s
- **Composite Fitness $J$**: **616.8100**
- **13-Regime Benchmark Performance**: 367 misses, 19,365.0 worker-s (30.59% savings), 3776 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the conformal autoscaler logic to incorporate robust scale-down hysteresis and anti-flapping controls from high-performing variants, while maintaining strong demand-forward and conformal safety headroom.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -151,7 +151,11 @@
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    raw_target = demand_workers + drain_workers - state.booting_workers
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 3.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 82: Program `3d4c66c7-745a-4019-9cbe-8edb12fcaaf0`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `228b63b7-1f3c-427b-93f0-441f01c33b9f`
- **LLM Call Telemetry**: 20839 prompt tokens, 653 completion tokens (total: 21492) | Latency: 187.91s
- **Composite Fitness $J$**: **335.4640**
- **13-Regime Benchmark Performance**: 570 misses, 17,688.0 worker-s (36.60% savings), 5410 deltas, Max P99: 16.00s
- **Innovation Rationale**: To improve cost savings while maintaining safety, we refine the safety margin and scaling hysteresis to allow leaner operation during steady states without risking deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,18 +141,22 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty & Velocity Anticipation ──
-    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.5
+    conformal_safety = 1.05 + 0.06 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.4
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.2
+    DRAIN_WINDOW_S = 0.55
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 83: Program `99a3ccc2-28db-4963-b4a7-3bd303a8004b`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `f5ff08a9-b843-4363-b2ce-fe068049407d`
- **LLM Call Telemetry**: 21059 prompt tokens, 754 completion tokens (total: 21813) | Latency: 196.19s
- **Composite Fitness $J$**: **238.3500**
- **13-Regime Benchmark Performance**: 512 misses, 18,895.0 worker-s (32.28% savings), 8464 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refine the safety margin and queue drain coefficients slightly to balance cost savings and tail safety while keeping code clean and focused.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -148,18 +148,16 @@
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.17 + 0.43 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 84: Program `04260a62-1d88-46fe-ab4b-6cfc311f0fa0`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0edc1707-efa7-47cd-9a49-1098e0d22d7e`
- **LLM Call Telemetry**: 21489 prompt tokens, 904 completion tokens (total: 22393) | Latency: 177.67s
- **Composite Fitness $J$**: **1149.8300**
- **13-Regime Benchmark Performance**: 0 misses, 20,955.0 worker-s (24.89% savings), 392 deltas, Max P99: 5.00s
- **Innovation Rationale**: Refined the scaling logic to incorporate smooth demand-forward estimation, precise queue drainage, and robust hysteresis to maintain high cost efficiency while eliminating deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,31 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.035 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    # ── Term 1: Semantic-Aware Demand (RPS) ──
+    c_factor = 1.20 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.40 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * c_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.30
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.45
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.42) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.70
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation & Hysteresis ──
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        if state.time_since_last_scale_s < 4.0 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 85: Program `8b38417b-453a-4d1a-a65b-986d75ca2ff0`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `25e6bdb7-dfc4-429f-972b-b6baf49d880a`
- **LLM Call Telemetry**: 20982 prompt tokens, 910 completion tokens (total: 21892) | Latency: 182.61s
- **Composite Fitness $J$**: **1149.2260**
- **13-Regime Benchmark Performance**: 0 misses, 20,957.0 worker-s (24.89% savings), 404 deltas, Max P99: 5.00s
- **Innovation Rationale**: I will enhance the autoscaling formula by incorporating predictive demand trends from $p_{fast}$ collapse and adaptive RAPS uncertainty bounds, along with an asymmetric scaling cooldown to eliminate flapping while preventing deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,27 +140,27 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
-    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and (state.time_since_last_scale_s < 3.0 or state.cloud_queue_depth > 0):
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.0 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 86: Program `1a222eef-797c-4acc-95f9-a653521e33fb`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `f0c63bf5-5b15-4dd7-a5cd-30695b937575`
- **LLM Call Telemetry**: 21086 prompt tokens, 727 completion tokens (total: 21813) | Latency: 190.38s
- **Composite Fitness $J$**: **773.2480**
- **13-Regime Benchmark Performance**: 105 misses, 20,321.0 worker-s (27.16% savings), 5844 deltas, Max P99: 11.00s
- **Innovation Rationale**: Optimized the conformal safety margin and queue drain window to improve resource efficiency and reduce scaling churn while maintaining strict tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,23 +141,20 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
-    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.07)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.015)
     
-    # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
+    SAFETY_MARGIN = 1.10 + 0.35 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    # Incorporate cloud_queue_velocity to differentiate transient spikes from sustained backlogs.
-    DRAIN_WINDOW_S = 0.55
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    DRAIN_WINDOW_S = 0.60
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.30
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 87: Program `672e6ce7-8880-40a5-aac4-ce0afba58379`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `1cb9f42d-883f-40d9-af45-a42aca3f6ebc`
- **LLM Call Telemetry**: 21448 prompt tokens, 1007 completion tokens (total: 25923) | Latency: 196.14s
- **Composite Fitness $J$**: **1149.1860**
- **13-Regime Benchmark Performance**: 0 misses, 21,127.0 worker-s (24.28% savings), 398 deltas, Max P99: 5.00s
- **Innovation Rationale**: Reverting to the stable high-performing logic structure while refining coefficients to balance cost and safety. The current failure (631 misses, -2912 churn) stems from improper handling of booting workers and incorrect semantic velocity polarity.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,36 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.18 * max(0.0, state.mean_set_size - 1.0) + 0.05 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    # ── Term 1: Semantic-Aware Demand (RPS) ──
+    # Headroom for complexity (mean_set_size) and semantic collapse (negative p_fast_velocity).
+    c_factor = 1.18 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.45 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * c_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.25
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.5) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    # Drain backlog over a responsive 0.6s window.
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.60
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation & Hysteresis ──
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        # Scale-down hysteresis: wait for cooldown and ensure queue is clear.
+        if state.time_since_last_scale_s < 4.0 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        # Maintain state if desired is already covered by workers in-flight.
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    # Escalate capacity as tasks age to prevent deadline misses.
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 88: Program `fe289a78-aa36-4ae3-8ef3-dab9e7c07086`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `e7605d6a-d9ba-43e7-affa-194cc997ffef`
- **LLM Call Telemetry**: 21253 prompt tokens, 885 completion tokens (total: 22138) | Latency: 179.46s
- **Composite Fitness $J$**: **1149.2260**
- **13-Regime Benchmark Performance**: 0 misses, 20,957.0 worker-s (24.89% savings), 404 deltas, Max P99: 5.00s
- **Innovation Rationale**: I will enhance the autoscaling formula by incorporating velocity-damped demand forecasting and asymmetric hysteresis to prevent flapping while robustly managing queue spikes and tail latency.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,27 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Dynamically scale safety margin using mean_set_size conformal uncertainty bound.
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_safety) / mu)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    demand_trend = -state.p_fast_velocity * state.ingress_rps
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
-    queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and (state.time_since_last_scale_s < 3.0 or state.cloud_queue_depth > 0):
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
+    est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
+    if (state.oldest_task_age_s + est_clearance_s) > 13.0 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 89: Program `ae2297a1-d386-4708-8ac0-76265ff7bd5d`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `a6cc2775-9fad-4d0e-84bc-7dd13ef660b3`
- **LLM Call Telemetry**: 21002 prompt tokens, 751 completion tokens (total: 21753) | Latency: 194.78s
- **Composite Fitness $J$**: **22.9000**
- **13-Regime Benchmark Performance**: 735 misses, 18,420.0 worker-s (33.98% savings), 8332 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined safety and queue-drain parameters to optimize cost savings and reduce churn while preserving tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -144,22 +144,20 @@
     # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
-    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.07)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.015)
     
     # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.15 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.14 * relaxation_factor
+    SAFETY_MARGIN = 1.12 + 0.38 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.58
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.32
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 90: Program `95470523-74aa-4a01-a68d-ddb2d41ff771`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `1e1cd732-7ed4-4b8d-bd0a-e7263bf52145`
- **LLM Call Telemetry**: 21522 prompt tokens, 951 completion tokens (total: 22473) | Latency: 179.57s
- **Composite Fitness $J$**: **1147.9080**
- **13-Regime Benchmark Performance**: 0 misses, 21,416.0 worker-s (23.24% savings), 412 deltas, Max P99: 5.00s
- **Innovation Rationale**: To recover the high cost efficiency and stable actuation of the original hybrid baseline while preventing deadline misses from semantic fast-path collapse, we refine the demand headroom and queue drainage logic with balanced tuning parameters.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,25 +141,32 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    # Scale safety headroom dynamically using RAPS prediction set size and semantic velocity
+    conformal_factor = 1.12 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.35 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * conformal_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.25
 
     # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    DRAIN_WINDOW_S = 0.50
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + max(0.0, v_adj) * 0.40) / DRAIN_WINDOW_S
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation & Provisioned Hysteresis ──────────────────
+    desired_k = math.ceil((demand_rps + surge_rps + drain_rps) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        if state.time_since_last_scale_s < 3.5 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 91: Program `cf0c24db-c491-4fa2-bb12-62a5dca55c37`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `0083bd23-02bb-4bfa-afe3-cccdf3302da8`
- **LLM Call Telemetry**: 19059 prompt tokens, 841 completion tokens (total: 19900) | Latency: 180.07s
- **Composite Fitness $J$**: **1147.2560**
- **13-Regime Benchmark Performance**: 0 misses, 21,642.0 worker-s (22.43% savings), 416 deltas, Max P99: 5.00s
- **Innovation Rationale**: To improve the autoscaler's fitness and minimize deadline misses while maintaining strong cost savings and smoothness, we will refine the conformal safety margin and anticipation terms to handle sudden traffic surges and semantic drift even more tightly, while keeping the smoothing and cooldown logic robust against flapping.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,23 +140,23 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Lean out safety margin slightly for better cost savings while preserving buffer.
-    conformal_safety = 1.08 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
+    # Slightly elevate safety margin to eliminate edge misses during p_fast transitions.
+    conformal_safety = 1.10 + 0.12 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.20 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.55
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    DRAIN_WINDOW_S = 0.5
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
-    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    raw_target = demand_workers + drain_workers - state.booting_workers
     
-    # Asymmetric hysteresis: scale up immediately, scale down with a slightly extended cooldown.
-    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.5 and state.cloud_queue_depth > 0:
+    # Asymmetric hysteresis: scale up immediately, scale down with cooldown and queue check.
+    if raw_target < state.active_workers and (state.time_since_last_scale_s < 3.0 or state.cloud_queue_depth > 0):
         effective_target = state.active_workers
     else:
         effective_target = raw_target
```

### Iteration 92: Program `e387a429-98b9-4b25-ae74-86396603016f`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `a6cc2775-9fad-4d0e-84bc-7dd13ef660b3`
- **LLM Call Telemetry**: 20976 prompt tokens, 399 completion tokens (total: 21375) | Latency: 195.1s
- **Composite Fitness $J$**: **238.3500**
- **13-Regime Benchmark Performance**: 512 misses, 18,895.0 worker-s (32.28% savings), 8464 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the safety margin and queue drain window to balance tail latency and worker stability, restoring peak fitness.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,16 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.15 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.14 * relaxation_factor
+    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 93: Program `bacc4797-3fd9-4f41-a2ab-b1821f83a290`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `1e1cd732-7ed4-4b8d-bd0a-e7263bf52145`
- **LLM Call Telemetry**: 21606 prompt tokens, 916 completion tokens (total: 22522) | Latency: 179.69s
- **Composite Fitness $J$**: **1149.8300**
- **13-Regime Benchmark Performance**: 0 misses, 20,955.0 worker-s (24.89% savings), 392 deltas, Max P99: 5.00s
- **Innovation Rationale**: To address the deadline misses and optimize the balance between cost savings and tail safety, we refine the demand-forward and drain scaling laws with proper hysteresis and graceful proportional SLA rescue, mirroring the high-performing baseline structure.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,31 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.14 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    # ── Term 1: Semantic-Aware Demand (RPS) ──
+    c_factor = 1.20 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.40 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * c_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.30
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.40
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.45) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.70
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation & Hysteresis ──
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        if state.time_since_last_scale_s < 4.0 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 94: Program `9137e41e-1a6c-47d1-b961-064b55db3a73`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `ed80eb99-ae5d-439d-b397-5707fcf4389a`
- **LLM Call Telemetry**: 21487 prompt tokens, 562 completion tokens (total: 22049) | Latency: 180.66s
- **Composite Fitness $J$**: **1150.0740**
- **13-Regime Benchmark Performance**: 0 misses, 20,583.0 worker-s (26.23% savings), 402 deltas, Max P99: 5.00s
- **Innovation Rationale**: Refined the conformal demand-forward safety and drain window parameters slightly to further optimize worker-seconds while maintaining zero deadline misses and smooth actuation.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,15 +141,15 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
-    # Anticipate demand surge from p_fast collapse (semantic drift) via p_fast_velocity.
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    # Slightly optimized conformal safety factor for improved cost savings without tail risk.
+    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 95: Program `483c15ff-7dd0-4d53-bfeb-a245f05de45b`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `f0c63bf5-5b15-4dd7-a5cd-30695b937575`
- **LLM Call Telemetry**: 21018 prompt tokens, 729 completion tokens (total: 21747) | Latency: 187.81s
- **Composite Fitness $J$**: **768.2300**
- **13-Regime Benchmark Performance**: 110 misses, 20,595.0 worker-s (26.18% savings), 5831 deltas, Max P99: 11.00s
- **Innovation Rationale**: Refined the proactive scaling coefficients and queue-drain window parameters to further enhance cost savings and churn stability while preserving tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,23 +141,20 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
-    queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
-    accel_surge = max(0.0, state.ingress_acceleration * 0.02)
+    queue_surge = max(0.0, state.cloud_queue_velocity * 0.075)
+    accel_surge = max(0.0, state.ingress_acceleration * 0.018)
     
-    # Non-linear ambiguity modulation
-    ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
+    ambiguity_boost = max(1.0, state.mean_set_size ** 1.06)
     
-    SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
+    SAFETY_MARGIN = 1.11 + 0.38 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    # Incorporate cloud_queue_velocity to differentiate transient spikes from sustained backlogs.
-    DRAIN_WINDOW_S = 0.55
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    DRAIN_WINDOW_S = 0.58
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.32
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 96: Program `70c5ec11-b54e-4773-b178-7d71fac95b72`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `53a923b2-9d8a-46d5-a8ba-ead2d78df2ab`
- **LLM Call Telemetry**: 21571 prompt tokens, 915 completion tokens (total: 22486) | Latency: 210.62s
- **Composite Fitness $J$**: **1150.2560**
- **13-Regime Benchmark Performance**: 0 misses, 20,692.0 worker-s (25.84% savings), 394 deltas, Max P99: 5.00s
- **Innovation Rationale**: To resolve the regression and restore high cost efficiency while maintaining tail safety and low churn, we incorporate InferLine's stable demand calculation combined with conformal headroom and a smooth scale-down hysteresis mechanism.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,25 +141,30 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    conformal_factor = 1.15 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.40 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * conformal_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.20
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.60
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation & Hysteresis ──
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        if state.time_since_last_scale_s < 3.5 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 97: Program `9dbcc7e1-7e32-470f-9b2c-641551327a68`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `f13e1d00-bad1-49fa-bb03-4fe6e59639b2`
- **LLM Call Telemetry**: 21100 prompt tokens, 1126 completion tokens (total: 24243) | Latency: 191.02s
- **Composite Fitness $J$**: **1149.2260**
- **13-Regime Benchmark Performance**: 0 misses, 20,957.0 worker-s (24.89% savings), 404 deltas, Max P99: 5.00s
- **Innovation Rationale**: To restore the fitness score and eliminate the 388 deadline misses, we must revert the aggressive cost-saving measures that compromised tail safety. Specifically, we will re-strengthen the conformal safety margin, restore the more robust asymmetric hysteresis (preventing scale-down if a queue exists or during cooldown), and tighten the urgency guard threshold.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,29 +141,30 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    # Slightly optimize safety margin for better cost savings while preserving buffer.
-    conformal_safety = 1.08 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    # Increase safety margin to 1.12 to absorb Poisson variance and semantic drift.
+    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.55
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    # Use a 0.6s window with higher velocity damping to smooth out burst response.
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
-    # Subtract 50% of booting workers; apply 2s scale-down cooldown if queue exists.
+    # Subtract 50% of booting workers. Prevent scale-down if a queue exists OR within 3s cooldown.
     raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
-    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.0 and state.cloud_queue_depth > 0:
+    if raw_target < state.active_workers and (state.time_since_last_scale_s < 3.0 or state.cloud_queue_depth > 0):
         effective_target = state.active_workers
     else:
         effective_target = raw_target
 
     # ── Term 4: Urgency Guard (SLA Rescue) ─────────────────────
-    # Panic if predicted latency (age + queue clearing time) exceeds 13.5s threshold.
+    # Panic if predicted latency (age + queue clearing time) exceeds 13.0s threshold.
     est_clearance_s = state.cloud_queue_depth / (max_workers * mu)
-    if (state.oldest_task_age_s + est_clearance_s) > 13.5 and state.cloud_queue_depth > 0:
+    if (state.oldest_task_age_s + est_clearance_s) > 13.0 and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
```

### Iteration 98: Program `ba3a0aa5-0505-4e52-9e19-5bc33b976b27`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `ca307cbb-df71-47ef-a63f-285ef8f8fcaa`
- **LLM Call Telemetry**: 20976 prompt tokens, 435 completion tokens (total: 21411) | Latency: 195.44s
- **Composite Fitness $J$**: **261.5240**
- **13-Regime Benchmark Performance**: 487 misses, 18,658.0 worker-s (33.13% savings), 8510 deltas, Max P99: 15.04s
- **Innovation Rationale**: To recover and exceed the previous high fitness of ~773-795 while maintaining robust tail safety, we optimize the safety margin coefficients and queue drain window to balance cost savings against deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,14 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.16 + 0.43 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
+    SAFETY_MARGIN = 1.13 + 0.41 * complexity_surge + queue_surge + accel_surge - 0.14 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.52
+    DRAIN_WINDOW_S = 0.56
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
```

### Iteration 99: Program `92137c24-faed-4622-a160-f8d263c4eb00`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `53a923b2-9d8a-46d5-a8ba-ead2d78df2ab`
- **LLM Call Telemetry**: 21488 prompt tokens, 1092 completion tokens (total: 24016) | Latency: 186.29s
- **Composite Fitness $J$**: **1149.8300**
- **13-Regime Benchmark Performance**: 0 misses, 20,955.0 worker-s (24.89% savings), 392 deltas, Max P99: 5.00s
- **Innovation Rationale**: To restore fitness from 307.9 to >1100, we must move away from the aggressive `booting_workers` subtraction (which causes deadline misses via the "HPA drain drop") and the binary "Urgency Guard" (which causes excessive flapping). We will adopt a "Provisioned-Reference" model that uses total fleet size (active + booting) as the target, combined with multi-stage proportional SLA rescue and strict down-scale hysteresis.

```python

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,26 +140,37 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    # Scale safety headroom dynamically using RAPS prediction set size and velocity
-    conformal_factor = 1.0 + 0.16 * max(0.0, state.mean_set_size - 1.0) + 0.03 * max(0.0, state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor) / mu)
+    # ── Term 1: Semantic-Aware Demand (RPS) ──
+    # Headroom for complexity (mean_set_size) and semantic collapse (negative p_fast_velocity).
+    c_factor = 1.20 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.40 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * c_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.30
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.42
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    # Drain backlog over a 0.7s window. Dampen velocity to avoid over-reacting to noise.
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.70
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Target Calculation & Hysteresis ──
+    # Sum all RPS requirements before ceiling to minimize rounding-induced flapping.
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        # Scale-down hysteresis: wait for cooldown and ensure queue is clear.
+        if state.time_since_last_scale_s < 4.0 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        # Maintain target if desired is already covered by workers in-flight.
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ──
+    # Escalate capacity as tasks age to prevent misses without binary max-worker churn.
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 100: Program `45913bb1-720b-4db5-a426-f02980e56637`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `fe289a78-aa36-4ae3-8ef3-dab9e7c07086`
- **LLM Call Telemetry**: 18855 prompt tokens, 520 completion tokens (total: 19375) | Latency: 175.32s
- **Composite Fitness $J$**: **1150.0740**
- **13-Regime Benchmark Performance**: 0 misses, 20,583.0 worker-s (26.23% savings), 402 deltas, Max P99: 5.00s
- **Innovation Rationale**: We refine the conformal safety factor and queue drain window to further enhance cost savings while maintaining strict 0-miss tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,14 +141,14 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
-    conformal_safety = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0)
+    conformal_safety = 1.09 + 0.10 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.2 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.6
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.4
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

### Iteration 101: Program `b2131f9d-ecb1-4886-8159-06cefdc73ecf`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `3e4a80c2-c49b-4f43-a80f-cf025b68dbf2`
- **LLM Call Telemetry**: 20977 prompt tokens, 393 completion tokens (total: 21370) | Latency: 194.23s
- **Composite Fitness $J$**: **229.3600**
- **13-Regime Benchmark Performance**: 527 misses, 18,840.0 worker-s (32.47% savings), 8346 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined safety margins and relaxation dynamics to balance tail safety with cost savings.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,16 +150,14 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.05)
     
-    SAFETY_MARGIN = 1.17 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.12 * relaxation_factor
+    SAFETY_MARGIN = 1.12 + 0.38 * complexity_surge + queue_surge + accel_surge - 0.16 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 102: Program `27f02192-b8d0-4566-80bf-c013e811440a`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `c3845087-4aeb-4060-ae1a-5e05ec8cb72e`
- **LLM Call Telemetry**: 21880 prompt tokens, 525 completion tokens (total: 22405) | Latency: 218.66s
- **Composite Fitness $J$**: **1149.9740**
- **13-Regime Benchmark Performance**: 0 misses, 20,833.0 worker-s (25.33% savings), 394 deltas, Max P99: 5.00s
- **Innovation Rationale**: We can fine-tune the conformal headroom factor and queue drain time constant to slightly optimize worker-seconds while preserving zero deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,15 +141,15 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Semantic-Aware Demand (RPS) ──
-    # Headroom for complexity (mean_set_size) and semantic collapse (p_fast_velocity).
-    c_factor = 1.20 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.40 * max(0.0, -state.p_fast_velocity)
+    # Calibrated headroom for complexity (mean_set_size) and semantic collapse (p_fast_velocity).
+    c_factor = 1.18 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.38 * max(0.0, -state.p_fast_velocity)
     demand_rps = state.offered_cloud_rps * c_factor
-    surge_rps = max(0.0, state.ingress_acceleration) * 0.30
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.25
 
     # ── Term 2: Queue Drain Budget (RPS) ──
-    # Drain backlog over a 0.7s window. Dampen velocity to avoid over-reacting to noise.
+    # Drain backlog over a 0.65s window with refined velocity dampening.
     v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
-    drain_rps = (state.cloud_queue_depth + v_adj * 0.45) / 0.70
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.42) / 0.65
 
     # ── Term 3: Target Calculation ──
     desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
```

### Iteration 103: Program `35671429-9085-4ec6-abdd-9ddebc56f15f`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `be2aa9ac-dc3c-4051-8845-a6cd2feb1d15`
- **LLM Call Telemetry**: 18530 prompt tokens, 745 completion tokens (total: 19275) | Latency: 191.57s
- **Composite Fitness $J$**: **1152.5520**
- **13-Regime Benchmark Performance**: 0 misses, 19,544.0 worker-s (29.95% savings), 394 deltas, Max P99: 5.00s
- **Innovation Rationale**: To improve cost savings while maintaining tail safety and zero deadline misses, we refine the demand forecast safety margin and the scale-down hysteresis window. By tightening the conformal safety factor slightly when set sizes are normal and increasing the scale-down cooldown, we reduce unnecessary worker-seconds without compromising responsiveness.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,19 +141,19 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
     anticipated_demand = state.offered_cloud_rps + max(0.0, -state.p_fast_velocity) * state.ingress_rps
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.5
-    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
+    DRAIN_WINDOW_S = 0.55
+    adjusted_queue = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
     queue_drain_rps = max(0.0, adjusted_queue) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers & Apply Scaling Hysteresis ─
-    raw_target = demand_workers + drain_workers - state.booting_workers
-    if raw_target < state.active_workers and state.time_since_last_scale_s < 1.5 and state.cloud_queue_depth == 0:
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and (state.time_since_last_scale_s < 2.5 or state.cloud_queue_depth > 0):
         effective_target = state.active_workers
     else:
         effective_target = raw_target
```

### Iteration 104: Program `d98afbe7-f6f0-4e31-949c-628a038e95f9`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `ee175139-d9fd-4f68-a886-c814013cc3f3`
- **LLM Call Telemetry**: 21002 prompt tokens, 725 completion tokens (total: 21727) | Latency: 179.37s
- **Composite Fitness $J$**: **238.3500**
- **13-Regime Benchmark Performance**: 512 misses, 18,895.0 worker-s (32.28% savings), 8464 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the continuous complexity surge factors and queue-drain window parameters to restore high-performance trade-offs between cost savings and tail safety.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,25 +141,21 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Continuous Complexity & Demand-Forward Provisioning ──────────
-    # Factor in complexity surge (-p_fast_velocity when < 0), relaxation, queue velocity, and acceleration
     complexity_surge = max(0.0, -state.p_fast_velocity)
     relaxation_factor = max(0.0, state.p_fast_velocity)
     queue_surge = max(0.0, state.cloud_queue_velocity * 0.08)
     accel_surge = max(0.0, state.ingress_acceleration * 0.02)
     
-    # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
     SAFETY_MARGIN = 1.14 + 0.40 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
```

### Iteration 105: Program `48abe3ca-4ed6-489b-a26f-7e93933565bb`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `0efd6348-3384-48d6-9b7f-4fd414dc52f3`
- **LLM Call Telemetry**: 21351 prompt tokens, 578 completion tokens (total: 21929) | Latency: 165.21s
- **Composite Fitness $J$**: **1147.6020**
- **13-Regime Benchmark Performance**: 0 misses, 21,519.0 worker-s (22.87% savings), 414 deltas, Max P99: 5.00s
- **Innovation Rationale**: To optimize our cost-savings and stability balance, we will re-introduce the stable provisioned offset (active + booting) and refined cooldown hysteresis from our top-performing variant, avoiding aggressive down-scaling while ensuring zero deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -152,21 +152,22 @@
     # Drain backlog over a 0.5s window, incorporating queue velocity to catch growth early.
     drain_rps = (state.cloud_queue_depth + state.cloud_queue_velocity * 0.45) / 0.50
 
-    # ── Term 3: Target Calculation ──
-    # Sum all RPS requirements before ceiling to minimize rounding-induced flapping.
-    # We do not subtract booting_workers; the target represents desired total fleet size.
-    total_rps = demand_rps + surge_rps + max(0.0, drain_rps)
-    effective_target = math.ceil(total_rps / mu)
+    # ── Term 3: Target Calculation & Hysteresis ──
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Stability & SLA Safety ──
-    # Hysteresis: Prevent aggressive down-scaling if a scaling action occurred recently (<2s).
-    if effective_target < state.active_workers and state.time_since_last_scale_s < 2.0:
-        effective_target = state.active_workers
+    if desired_k < state.active_workers:
+        if state.time_since_last_scale_s < 3.5 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        effective_target = provisioned
 
-    # Proportional SLA Rescue: If tasks age beyond 10s, increment capacity to clear backlog
-    # without the massive churn caused by a binary jump to max_workers.
-    if state.oldest_task_age_s > 10.0 and state.cloud_queue_depth > 0:
-        effective_target = max(effective_target, state.active_workers + 2)
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 106: Program `2a964d24-d234-41cb-a3f0-43db21afcff5`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `2ca72076-96f3-4a11-bfd2-62dd9057df83`
- **LLM Call Telemetry**: 20504 prompt tokens, 492 completion tokens (total: 20996) | Latency: 170.57s
- **Composite Fitness $J$**: **429.2200**
- **13-Regime Benchmark Performance**: 531 misses, 18,460.0 worker-s (33.84% savings), 4284 deltas, Max P99: 16.00s
- **Innovation Rationale**: Refined the demand anticipation and queue-drain dynamics to balance cost savings and tail safety by using more robust coefficient settings.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,9 +140,9 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Conformal Demand-Forward with Uncertainty & Velocity Anticipation ──
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
-    anticipated_demand = state.offered_cloud_rps + max(0.0, state.p_fast_velocity) * state.ingress_rps * 0.6
+    # ── Term 1: Conformal Demand-Forward with Uncertainty Adaptation ─────────
+    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
+    anticipated_demand = state.offered_cloud_rps + max(0.0, -state.p_fast_velocity) * state.ingress_rps
     demand_workers = math.ceil((anticipated_demand * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
```

### Iteration 107: Program `08b3d8e9-db36-4a43-842e-146d8481a981`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `a6cc2775-9fad-4d0e-84bc-7dd13ef660b3`
- **LLM Call Telemetry**: 20976 prompt tokens, 570 completion tokens (total: 21546) | Latency: 167.53s
- **Composite Fitness $J$**: **780.8840**
- **13-Regime Benchmark Performance**: 101 misses, 20,628.0 worker-s (26.06% savings), 5764 deltas, Max P99: 11.00s
- **Innovation Rationale**: Refined the continuous complexity factors and safety margins to better balance cost savings and deadline performance, restoring optimal scoring.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,20 +150,21 @@
     # Non-linear ambiguity modulation
     ambiguity_boost = max(1.0, state.mean_set_size ** 1.08)
     
-    SAFETY_MARGIN = 1.15 + 0.42 * complexity_surge + queue_surge + accel_surge - 0.14 * relaxation_factor
+    SAFETY_MARGIN = 1.12 + 0.38 * complexity_surge + queue_surge + accel_surge - 0.15 * relaxation_factor
     adjusted_demand = state.offered_cloud_rps * ambiguity_boost
     demand_workers = math.ceil((adjusted_demand * SAFETY_MARGIN) / mu)
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
+    DRAIN_WINDOW_S = 0.55
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
+    raw_target = demand_workers + drain_workers - int(state.booting_workers * 0.5)
+    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.5 and state.cloud_queue_depth > 0:
+        effective_target = state.active_workers
+    else:
+        effective_target = raw_target
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 108: Program `8d41365c-d1ae-40ea-9142-b99dac29a7c9`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `78497c29-f06d-449a-95ac-56fbe8175262`
- **LLM Call Telemetry**: 19079 prompt tokens, 987 completion tokens (total: 20066) | Latency: 161.37s
- **Composite Fitness $J$**: **1149.9740**
- **13-Regime Benchmark Performance**: 0 misses, 20,833.0 worker-s (25.33% savings), 394 deltas, Max P99: 5.00s
- **Innovation Rationale**: To resolve the performance regression and restore high cost efficiency while preserving tail safety, we refine the demand-forward multiplier and queuing dynamics with a robust, well-damped scaling law similar to our top-performing variant.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,29 +140,31 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1 & Conformal Headroom: Demand-Forward Provisioning ─────────────
-    conformal_factor = 1.12 + 0.12 * max(0.0, state.mean_set_size - 1.0) + 0.25 * max(0.0, -state.p_fast_velocity)
-    demand_workers = math.ceil((state.offered_cloud_rps * conformal_factor + max(0.0, state.ingress_acceleration) * 0.20) / mu)
+    # ── Term 1: Semantic-Aware Demand (RPS) ──
+    c_factor = 1.18 + 0.15 * max(0.0, state.mean_set_size - 1.0) + 0.38 * max(0.0, -state.p_fast_velocity)
+    demand_rps = state.offered_cloud_rps * c_factor
+    surge_rps = max(0.0, state.ingress_acceleration) * 0.25
 
-    # ── Term 2: Queue Drain Budget with Velocity ─────────────────────────────
-    DRAIN_WINDOW_S = 0.50
-    queue_drain_rps = (state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
+    # ── Term 2: Queue Drain Budget (RPS) ──
+    v_adj = max(-10.0, min(20.0, state.cloud_queue_velocity))
+    drain_rps = (state.cloud_queue_depth + v_adj * 0.42) / 0.65
 
-    # ── Term 3: Subtract In-Flight Booting & Factor in Cooldown/Hysteresis ────
-    raw_target = demand_workers + drain_workers - state.booting_workers
-    if raw_target < state.active_workers and state.time_since_last_scale_s < 2.5 and state.cloud_queue_depth > 0:
-        effective_target = state.active_workers
-    else:
-        effective_target = raw_target
+    # ── Term 3: Target Calculation & Hysteresis ──
+    desired_k = math.ceil((demand_rps + surge_rps + max(0.0, drain_rps)) / mu)
+    provisioned = state.active_workers + state.booting_workers
+    effective_target = desired_k
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
-    # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
-    # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
-    time_remaining = state.sla_deadline_s - state.oldest_task_age_s
-    if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+    if desired_k < state.active_workers:
+        if state.time_since_last_scale_s < 4.0 or state.cloud_queue_depth > 0:
+            effective_target = state.active_workers
+    elif desired_k <= provisioned:
+        effective_target = provisioned
+
+    # ── Term 4: Proportional SLA Rescue ─────────────────────────────────────
+    if state.oldest_task_age_s > 8.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, provisioned + 1)
+    if state.oldest_task_age_s > 12.0 and state.cloud_queue_depth > 0:
+        effective_target = max(effective_target, state.active_workers + 4)
 
     # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
```

### Iteration 109: Program `3bb38ddc-947a-4016-950f-b5a72beb1ca1`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `601f19e3-939a-4b1f-96e8-9dd8bca6798a`
- **LLM Call Telemetry**: 20347 prompt tokens, 522 completion tokens (total: 20869) | Latency: 170.63s
- **Composite Fitness $J$**: **411.3100**
- **13-Regime Benchmark Performance**: 488 misses, 17,780.0 worker-s (36.27% savings), 5519 deltas, Max P99: 14.00s
- **Innovation Rationale**: I will refine the conformal safety margin and drain window parameters slightly to improve cost savings while maintaining strict SLA compliance and zero deadline misses.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -141,14 +141,14 @@
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
     # ── Term 1: Conformal Demand-Forward with Uncertainty & Trend ───────────
-    conformal_safety = 1.10 + 0.10 * max(0.0, state.mean_set_size - 1.0)
+    conformal_safety = 1.08 + 0.08 * max(0.0, state.mean_set_size - 1.0)
     demand_trend = -state.p_fast_velocity * state.ingress_rps
-    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.15 * max(0.0, state.ingress_acceleration)
+    anticipated_rps = state.offered_cloud_rps + max(0.0, demand_trend) + 0.12 * max(0.0, state.ingress_acceleration)
     demand_workers = math.ceil((anticipated_rps * conformal_safety) / mu)
 
     # ── Term 2: Queue Drain Budget with Velocity Damping ───────────────────
-    DRAIN_WINDOW_S = 0.55
-    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.35
+    DRAIN_WINDOW_S = 0.6
+    q_adj = state.cloud_queue_depth + max(0.0, state.cloud_queue_velocity) * 0.3
     drain_workers = math.ceil(max(0.0, q_adj) / (mu * DRAIN_WINDOW_S))
 
     # ── Term 3: Asymmetric Scaling & Booting Offset ─────────────────────────
```

---

## 5. Failed LLM Calls & Feedback Diagnostics

The following LLM calls encountered syntax, formatting, or boundary rejections and were handled by OpenEvolve's feedback loop:

| Iter | Island | Duration | Error Diagnostic |
|:---:|:---:|:---:|:---|
| 31 | Island 0 | 2.75s | `None of the 1 SEARCH block(s) matched the parent program` |
