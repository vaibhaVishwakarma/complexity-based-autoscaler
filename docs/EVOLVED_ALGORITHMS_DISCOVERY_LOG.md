# OpenEvolve Evolutionary Conformal Autoscaler Discovery Log

> **Notice**: This document tracks the simulation-in-the-loop synthesis of
> adaptive conformal scaling policies across 13 diverse workload regimes
> on ContinuumBench (121,134 requests). Real-time telemetry is recorded on
> every LLM synthesis call and multi-stage cascade evaluation.

## 1. Executive Status & Best Policy to Date

- **Best Program ID**: `ff98dab4-f4d3-4dcc-9ff1-0dc75c3b78a7` (Iteration 7)
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Primary Fitness $J$**: **1098.6640**
- **Deadline Misses**: **0** (InferLine: 44, Fixed: 0)
- **Worker-Seconds**: **23,038.0** (**17.43% savings** vs Fixed Capacity; InferLine: 14,261.0 / 48.9%)
- **Churn Deltas**: **1332** (InferLine: 855, KEDA: 1,710)
- **Tail Safety (P99)**: **7.00s** (InferLine: 6.0s, SLA Deadline: 10.0s)

### Benchmark Baseline Comparison Matrix

| Controller / Policy | Type | Worker-Seconds | Cost Savings vs Fixed | Deadline Misses | Churn Deltas | Max P99 Latency |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fixed Capacity** | Static Peak | 27,900.0 | 0.0% | 0 | 205 | 5.0s |
| **InferLine Tuner** | Reactive Envelope | 14,261.0 | 48.9% | 44 | 855 | 6.0s |
| **Kubernetes HPA** | Reactive Util | 23,940.0 | 14.2% | 72 | 606 | 13.0s |
| **KEDA** | Reactive Concurrency | 19,850.0 | 28.9% | 128 | 1710 | 9.5s |
| **Conformal Seed Baseline** | Conformal ACI | 16,675.0 | 40.2% | 824 | 4628 | 7.0s |
| **⭐ Best Evolved Policy** | **Conformal Evolved** | **23,038.0** | **17.43%** | **0** | **1332** | **7.00s** |

---

## 2. LLM Call & Synthesis Telemetry

- **Total LLM Calls**: 7 (Successful: 7 | Rejected/Error: 0)
- **Total Token Budget Consumed**: 102,518 tokens (57,124 prompt + 7,324 completion/thinking)
- **Model**: `gemini-2.5-flash` via Google AI Studio (`temperature: 0.7`, `max_tokens: 8192`)

---

## 3. Discovered Algorithms Summary Table

| Iter | Program ID | Branch Origin | Fitness $J$ | Misses | Worker-Sec | Savings | Deltas | Max P99 | Regimes | Status vs InferLine |
|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | `b67f1403` | Island 0 | **914.56** | 183 | 21,590.0 | 22.6% | 1412 | 7.00s | 13/13 | Evaluated |
| 2 | `7b6b03c6` | Island 1 | **239.11** | 596 | 18,389.0 | 34.1% | 6789 | 16.00s | 13/13 | Evaluated |
| 3 | `f34a0900` | Island 2 | **663.40** | 400 | 20,572.0 | 26.3% | 2136 | 7.00s | 13/13 | Evaluated |
| 4 | `bdbfd30e` | Island 0 | **914.56** | 183 | 21,590.0 | 22.6% | 1412 | 7.00s | 13/13 | Evaluated |
| 5 | `461f8990` | Island 1 | **84.84** | 746 | 17,973.0 | 35.6% | 6891 | 16.00s | 13/13 | Evaluated |
| 6 | `96af09dd` | Island 2 | **758.82** | 343 | 19,211.0 | 31.1% | 1422 | 7.00s | 13/13 | Evaluated |
| 7 | `ff98dab4` | Island 0 | **1098.66** | 0 | 23,038.0 | 17.4% | 1332 | 7.00s | 13/13 | ✅ Beats Misses |

---

## 4. Chronological Iteration Breakdown & Code Innovations

### Iteration 1: Program `b67f1403-57f2-4454-99cd-5a95fce14d37`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `e37b53e2-6638-4ad8-959f-acb1756faae2`
- **LLM Call Telemetry**: 6051 prompt tokens, 1125 completion tokens (total: 12195) | Latency: 301.62s
- **Composite Fitness $J$**: **914.5600**
- **13-Regime Benchmark Performance**: 183 misses, 21,590.0 worker-s (22.62% savings), 1412 deltas, Max P99: 7.00s
- **Innovation Rationale**: Increased the safety margin and accelerated queue draining to proactively reduce deadline misses, and implemented an asymmetric scale-down with a cooldown period to minimize flapping and prevent premature worker termination.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,30 +142,44 @@
 
     # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
     # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
+    # Add safety margin to handle Poisson arrival variance without SLA misses.
+    SAFETY_MARGIN = 1.25 # Increased from 1.20 for better miss reduction
     demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.4 # Decreased from 0.5 for faster queue draining
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # This is the desired worker count before applying cooldown or urgency overrides.
+    desired_workers = demand_workers + drain_workers - state.booting_workers
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
+    # ── Term 4: Asymmetric Scale-Down & Cooldown for Flapping ──────────────
+    # Introduce a cooldown period for scaling down to prevent flapping (KEDA flapping)
+    # and premature worker termination (HPA drain drop).
+    SCALE_DOWN_COOLDOWN_S = 10.0
+
+    # Initialize effective_target with desired_workers
+    effective_target = desired_workers
+
+    # If we are trying to scale down and are within the cooldown period,
+    # prevent scaling down and hold current capacity.
+    if desired_workers < state.active_workers and state.time_since_last_scale_s < SCALE_DOWN_COOLDOWN_S:
+        effective_target = state.active_workers # Hold current active workers
+
+    # ── Term 5: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
     # immediately clamp to max workers to prevent a deadline miss cascade.
     SLA_RESCUE_MARGIN_S = 3.0
     time_remaining = state.sla_deadline_s - state.oldest_task_age_s
     if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+        effective_target = max_workers # Override any previous calculation to ensure safety.
 
-    # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
+    # ── Term 6: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
     k_t = int(max(1, min(max_workers, effective_target)))
     return k_t
```

### Iteration 2: Program `7b6b03c6-90b2-4af0-b676-3df8146975ad`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `e37b53e2-6638-4ad8-959f-acb1756faae2`
- **LLM Call Telemetry**: 6031 prompt tokens, 1497 completion tokens (total: 15760) | Latency: 335.28s
- **Composite Fitness $J$**: **239.1120**
- **13-Regime Benchmark Performance**: 596 misses, 18,389.0 worker-s (34.09% savings), 6789 deltas, Max P99: 16.00s
- **Innovation Rationale**: Introduced proactive scaling by incorporating `p_fast_velocity` and `ingress_acceleration` to anticipate complexity surges before queues form. Modulated core demand with `mean_set_size` for ambiguity and enhanced queue draining with `cloud_queue_velocity` for improved responsiveness.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -140,32 +140,53 @@
     mu = state.worker_capacity_rps       # 16.0 RPS/worker
     max_workers = 18                     # 6 nodes × 3 workers/node (cluster capacity)
 
-    # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
-    # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
+    # Define common constants for tuning
     SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    DRAIN_WINDOW_S = 0.5
+    SLA_RESCUE_MARGIN_S = 3.0
+    ACCEL_PREEMPT_FACTOR = 0.5 # Factor to convert ingress_acceleration (RPS/s^2) to RPS equivalent for proactive scaling
 
-    # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
-    # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
-    # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
-    queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
+    # ── Core Demand Calculation (adjusted for ambiguity) ─────────────────────
+    # Adjust offered_cloud_rps by mean_set_size: higher mean_set_size implies more complex work per request.
+    # This non-linearly (multiplicatively) increases the effective demand.
+    # mean_set_size >= 1.0, so this only increases or maintains demand.
+    adjusted_offered_cloud_rps = state.offered_cloud_rps * SAFETY_MARGIN * state.mean_set_size
+    demand_workers = math.ceil(adjusted_offered_cloud_rps / mu)
+
+    # ── Preemptive Scaling for Surging Complexity and Ingress Acceleration ──
+    preemptive_surge_workers = 0
+
+    # Proactively scale up if complexity is surging (p_fast decreasing).
+    # The term ingress_rps * (-p_fast_velocity) estimates the additional RPS load due to complexity shift.
+    if state.p_fast_velocity < 0:
+        p_fast_preempt_rps = state.ingress_rps * (-state.p_fast_velocity)
+        preemptive_surge_workers += math.ceil(p_fast_preempt_rps / mu)
+
+    # Proactively scale up if ingress RPS is accelerating.
+    # ingress_acceleration is d^2(lambda)/dt^2. Convert to an RPS estimate for a lookahead period.
+    if state.ingress_acceleration > 0:
+        acceleration_preempt_rps = state.ingress_acceleration * ACCEL_PREEMPT_FACTOR
+        preemptive_surge_workers += math.ceil(acceleration_preempt_rps / mu)
+
+    # ── Queue Drain Budget (adjusted for queue velocity) ─────────────────────
+    # Add extra workers to drain backlog Q_t and anticipate immediate growth from Q_velocity.
+    # Only consider positive velocity to avoid prematurely reducing workers when queue is shrinking.
+    anticipated_queue_increase_rps = max(0.0, state.cloud_queue_velocity * DRAIN_WINDOW_S)
+    queue_drain_rps = (state.cloud_queue_depth + anticipated_queue_increase_rps) / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
-    # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # ── Calculate Effective Target (combining all terms) ────────────────────
+    # Sum base demand, preemptive surge, and queue draining, then subtract in-flight workers.
+    effective_target = demand_workers + preemptive_surge_workers + drain_workers - state.booting_workers
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
+    # ── Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
     # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
     time_remaining = state.sla_deadline_s - state.oldest_task_age_s
     if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
         effective_target = max_workers
 
-    # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
+    # ── Final Clamp to Feasible Integer Range ───────────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
     k_t = int(max(1, min(max_workers, effective_target)))
     return k_t
```

### Iteration 3: Program `f34a0900-5b09-41b4-97dd-ebe37b3bebcc`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `e37b53e2-6638-4ad8-959f-acb1756faae2`
- **LLM Call Telemetry**: 6106 prompt tokens, 774 completion tokens (total: 12309) | Latency: 315.27s
- **Composite Fitness $J$**: **663.3960**
- **13-Regime Benchmark Performance**: 400 misses, 20,572.0 worker-s (26.27% savings), 2136 deltas, Max P99: 7.00s
- **Innovation Rationale**: The current policy suffers from high deadline misses (824 vs InferLine's 44) and poor churn stability (4628 deltas vs InferLine's 855). This update integrates `state.mean_set_size` to provide proactive safety headroom for complex tasks and adds hysteresis using `state.time_since_last_scale_s` to stabilize scale-down decisions, aligning with the goal of semantic complexity-awareness and improved stability.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,9 +142,12 @@
 
     # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
     # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
-    demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
+    # Add safety margin to handle Poisson arrival variance and augment with
+    # conformal headroom proportional to mean_set_size for semantic complexity.
+    BASE_SAFETY_FACTOR = 1.15 # Baseline safety for typical loads
+    CONFORMAL_MEAN_SET_SIZE_WEIGHT = 0.75 # Amplifies safety margin based on task complexity
+    dynamic_safety_factor = BASE_SAFETY_FACTOR + max(0.0, (state.mean_set_size - 1.0) * CONFORMAL_MEAN_SET_SIZE_WEIGHT)
+    demand_workers = math.ceil((state.offered_cloud_rps * dynamic_safety_factor) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
@@ -156,6 +159,12 @@
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
     effective_target = demand_workers + drain_workers - state.booting_workers
+
+    # ── Term X: Hysteresis for Scale-Down Stability ──────────────────────────
+    # Prevents rapid scaling down to improve churn stability, unless urgency guard triggers.
+    COOLDOWN_FOR_SCALE_DOWN_S = 8.0 # Cooldown period (in seconds) before allowing scale-down
+    if effective_target < state.active_workers and state.time_since_last_scale_s < COOLDOWN_FOR_SCALE_DOWN_S:
+        effective_target = state.active_workers
 
     # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 4: Program `bdbfd30e-e8c7-4dbf-bd7b-5f58d2d06a61`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `e37b53e2-6638-4ad8-959f-acb1756faae2`
- **LLM Call Telemetry**: 9912 prompt tokens, 1226 completion tokens (total: 13490) | Latency: 289.58s
- **Composite Fitness $J$**: **914.5600**
- **13-Regime Benchmark Performance**: 183 misses, 21,590.0 worker-s (22.62% savings), 1412 deltas, Max P99: 7.00s
- **Innovation Rationale**: The previous attempt (Program 1) showed significant improvements in deadline misses and churn stability by adjusting safety margins, queue drain windows, and introducing an asymmetric scale-down cooldown. Reapplying these proven changes will likely restore the higher fitness.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -142,30 +142,44 @@
 
     # ── Term 1: Demand-Forward Provisioning ──────────────────────────────────
     # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
-    # Add 20% safety margin to handle Poisson arrival variance without SLA misses.
-    SAFETY_MARGIN = 1.20
+    # Add safety margin to handle Poisson arrival variance without SLA misses.
+    SAFETY_MARGIN = 1.25 # Increased from 1.20 for better miss reduction
     demand_workers = math.ceil((state.offered_cloud_rps * SAFETY_MARGIN) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 0.4 # Decreased from 0.5 for faster queue draining
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
     # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
     # Workers already booting will contribute capacity shortly; avoid double-counting.
-    effective_target = demand_workers + drain_workers - state.booting_workers
+    # This is the desired worker count before applying cooldown or urgency overrides.
+    desired_workers = demand_workers + drain_workers - state.booting_workers
 
-    # ── Term 4: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
+    # ── Term 4: Asymmetric Scale-Down & Cooldown for Flapping ──────────────
+    # Introduce a cooldown period for scaling down to prevent flapping (KEDA flapping)
+    # and premature worker termination (HPA drain drop).
+    SCALE_DOWN_COOLDOWN_S = 10.0
+
+    # Initialize effective_target with desired_workers
+    effective_target = desired_workers
+
+    # If we are trying to scale down and are within the cooldown period,
+    # prevent scaling down and hold current capacity.
+    if desired_workers < state.active_workers and state.time_since_last_scale_s < SCALE_DOWN_COOLDOWN_S:
+        effective_target = state.active_workers # Hold current active workers
+
+    # ── Term 5: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
     # immediately clamp to max workers to prevent a deadline miss cascade.
     SLA_RESCUE_MARGIN_S = 3.0
     time_remaining = state.sla_deadline_s - state.oldest_task_age_s
     if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
-        effective_target = max_workers
+        effective_target = max_workers # Override any previous calculation to ensure safety.
 
-    # ── Term 5: Final Clamp to Feasible Integer Range ────────────────────────
+    # ── Term 6: Final Clamp to Feasible Integer Range ────────────────────────
     # k_t must always be a valid integer in [1, max_workers].
     k_t = int(max(1, min(max_workers, effective_target)))
     return k_t
```

### Iteration 5: Program `461f8990-bd98-455a-aa3d-fadee181b0ed`
- **Branch Origin**: **Island 1: Continuous Complexity Dynamic Radical**
- **Parent Program**: `7b6b03c6-90b2-4af0-b676-3df8146975ad`
- **LLM Call Telemetry**: 7773 prompt tokens, 1226 completion tokens (total: 15172) | Latency: 329.75s
- **Composite Fitness $J$**: **84.8440**
- **13-Regime Benchmark Performance**: 746 misses, 17,973.0 worker-s (35.58% savings), 6891 deltas, Max P99: 16.00s
- **Innovation Rationale**: This modification introduces a continuous dynamic factor (`complexity_dynamic_rps`) that scales capacity up when complexity surges (`p_fast_velocity < 0`) and allows for smooth capacity reduction when complexity decreases (`p_fast_velocity > 0`), preemptively adjusting to complexity shifts before queues accumulate. It refactors demand calculation by aggregating all RPS terms before converting to workers, improving continuity.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -150,34 +150,36 @@
     # Adjust offered_cloud_rps by mean_set_size: higher mean_set_size implies more complex work per request.
     # This non-linearly (multiplicatively) increases the effective demand.
     # mean_set_size >= 1.0, so this only increases or maintains demand.
-    adjusted_offered_cloud_rps = state.offered_cloud_rps * SAFETY_MARGIN * state.mean_set_size
-    demand_workers = math.ceil(adjusted_offered_cloud_rps / mu)
+    base_demand_rps = state.offered_cloud_rps * SAFETY_MARGIN * state.mean_set_size
 
-    # ── Preemptive Scaling for Surging Complexity and Ingress Acceleration ──
-    preemptive_surge_workers = 0
+    # ── Continuous Complexity Dynamics Factor ───────────────────────────────
+    # Represents the rate of increase or decrease of complexity.
+    # Positive when complexity surges (p_fast_velocity < 0), adding demand.
+    # Negative when complexity relaxes (p_fast_velocity > 0), reducing demand.
+    complexity_dynamic_rps = state.ingress_rps * (-state.p_fast_velocity)
 
-    # Proactively scale up if complexity is surging (p_fast decreasing).
-    # The term ingress_rps * (-p_fast_velocity) estimates the additional RPS load due to complexity shift.
-    if state.p_fast_velocity < 0:
-        p_fast_preempt_rps = state.ingress_rps * (-state.p_fast_velocity)
-        preemptive_surge_workers += math.ceil(p_fast_preempt_rps / mu)
-
+    # ── Preemptive Scaling for Ingress Acceleration ─────────────────────────
     # Proactively scale up if ingress RPS is accelerating.
     # ingress_acceleration is d^2(lambda)/dt^2. Convert to an RPS estimate for a lookahead period.
+    acceleration_preempt_rps = 0.0
     if state.ingress_acceleration > 0:
         acceleration_preempt_rps = state.ingress_acceleration * ACCEL_PREEMPT_FACTOR
-        preemptive_surge_workers += math.ceil(acceleration_preempt_rps / mu)
 
     # ── Queue Drain Budget (adjusted for queue velocity) ─────────────────────
-    # Add extra workers to drain backlog Q_t and anticipate immediate growth from Q_velocity.
+    # Add extra throughput required to drain backlog Q_t and anticipate immediate growth from Q_velocity.
     # Only consider positive velocity to avoid prematurely reducing workers when queue is shrinking.
     anticipated_queue_increase_rps = max(0.0, state.cloud_queue_velocity * DRAIN_WINDOW_S)
     queue_drain_rps = (state.cloud_queue_depth + anticipated_queue_increase_rps) / DRAIN_WINDOW_S
-    drain_workers = math.ceil(queue_drain_rps / mu)
 
-    # ── Calculate Effective Target (combining all terms) ────────────────────
-    # Sum base demand, preemptive surge, and queue draining, then subtract in-flight workers.
-    effective_target = demand_workers + preemptive_surge_workers + drain_workers - state.booting_workers
+    # ── Aggregate all RPS demands ───────────────────────────────────────────
+    total_effective_rps = base_demand_rps + complexity_dynamic_rps + acceleration_preempt_rps + queue_drain_rps
+
+    # ── Calculate Raw Target Workers (before booting offset and clamping) ──
+    raw_target_workers = math.ceil(total_effective_rps / mu)
+
+    # ── Term 3: Subtract In-Flight Booting Workers ───────────────────────────
+    # Workers already booting will contribute capacity shortly; avoid double-counting.
+    effective_target = raw_target_workers - state.booting_workers
 
     # ── Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
```

### Iteration 6: Program `96af09dd-2683-44fe-858e-73119772c79d`
- **Branch Origin**: **Island 2: InferLine-Conformal Hybrid Radical**
- **Parent Program**: `f34a0900-5b09-41b4-97dd-ebe37b3bebcc`
- **LLM Call Telemetry**: 7196 prompt tokens, 480 completion tokens (total: 12822) | Latency: 311.31s
- **Composite Fitness $J$**: **758.8180**
- **13-Regime Benchmark Performance**: 343 misses, 19,211.0 worker-s (31.14% savings), 1422 deltas, Max P99: 7.00s
- **Innovation Rationale**: To align with InferLine's cost efficiency and churn stability while leveraging semantic awareness, I've adjusted the safety factors, increased the queue drain window, and extended the scale-down cooldown. These changes aim to reduce worker-seconds and scaling deltas, addressing the current policy's higher resource consumption and churn compared to InferLine.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -144,15 +144,15 @@
     # offered_cloud_rps = ingress_rps * (1 - p_fast) is the causal cloud demand.
     # Add safety margin to handle Poisson arrival variance and augment with
     # conformal headroom proportional to mean_set_size for semantic complexity.
-    BASE_SAFETY_FACTOR = 1.15 # Baseline safety for typical loads
-    CONFORMAL_MEAN_SET_SIZE_WEIGHT = 0.75 # Amplifies safety margin based on task complexity
+    BASE_SAFETY_FACTOR = 1.10 # Reduced baseline safety to lower worker-seconds and improve cost savings
+    CONFORMAL_MEAN_SET_SIZE_WEIGHT = 0.25 # Reduced amplification of safety margin for more conservative scaling and better churn
     dynamic_safety_factor = BASE_SAFETY_FACTOR + max(0.0, (state.mean_set_size - 1.0) * CONFORMAL_MEAN_SET_SIZE_WEIGHT)
     demand_workers = math.ceil((state.offered_cloud_rps * dynamic_safety_factor) / mu)
 
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.5
+    DRAIN_WINDOW_S = 1.0 # Increased drain window for less aggressive queue clearing, reducing cost and churn
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
@@ -162,7 +162,7 @@
 
     # ── Term X: Hysteresis for Scale-Down Stability ──────────────────────────
     # Prevents rapid scaling down to improve churn stability, unless urgency guard triggers.
-    COOLDOWN_FOR_SCALE_DOWN_S = 8.0 # Cooldown period (in seconds) before allowing scale-down
+    COOLDOWN_FOR_SCALE_DOWN_S = 12.0 # Increased cooldown to further reduce scaling deltas and improve churn stability
     if effective_target < state.active_workers and state.time_since_last_scale_s < COOLDOWN_FOR_SCALE_DOWN_S:
         effective_target = state.active_workers
```

### Iteration 7: Program `ff98dab4-f4d3-4dcc-9ff1-0dc75c3b78a7`
- **Branch Origin**: **Island 0: Core Conformal Branch**
- **Parent Program**: `bdbfd30e-e8c7-4dbf-bd7b-5f58d2d06a61`
- **LLM Call Telemetry**: 14055 prompt tokens, 996 completion tokens (total: 20770) | Latency: 313.8s
- **Composite Fitness $J$**: **1098.6640**
- **13-Regime Benchmark Performance**: 0 misses, 23,038.0 worker-s (17.43% savings), 1332 deltas, Max P99: 7.00s
- **Innovation Rationale**: To minimize deadline misses (highest priority), I will make the urgency guard more proactive by increasing its activation margin and make queue draining more aggressive. These changes prioritize miss reduction, even if they moderately increase worker-seconds or scaling deltas.

#### Code Mutation Applied:
```diff
--- parent_policy.py
+++ evolved_policy.py
@@ -149,7 +149,7 @@
     # ── Term 2: Queue Drain Budget ───────────────────────────────────────────
     # Extra workers needed to drain backlog Q_t within DRAIN_WINDOW_S seconds.
     # drain_rps = Q / DRAIN_WINDOW_S is the additional throughput required.
-    DRAIN_WINDOW_S = 0.4 # Decreased from 0.5 for faster queue draining
+    DRAIN_WINDOW_S = 0.3 # Further decreased from 0.4 for more aggressive queue draining to reduce misses
     queue_drain_rps = state.cloud_queue_depth / DRAIN_WINDOW_S
     drain_workers = math.ceil(queue_drain_rps / mu)
 
@@ -161,7 +161,7 @@
     # ── Term 4: Asymmetric Scale-Down & Cooldown for Flapping ──────────────
     # Introduce a cooldown period for scaling down to prevent flapping (KEDA flapping)
     # and premature worker termination (HPA drain drop).
-    SCALE_DOWN_COOLDOWN_S = 10.0
+    SCALE_DOWN_COOLDOWN_S = 10.0 # Maintain current cooldown to prevent excessive flapping
 
     # Initialize effective_target with desired_workers
     effective_target = desired_workers
@@ -174,7 +174,7 @@
     # ── Term 5: Urgency Guard (Head-of-Line SLA Rescue) ─────────────────────
     # If the oldest queued task is within SLA_RESCUE_MARGIN_S of the deadline,
     # immediately clamp to max workers to prevent a deadline miss cascade.
-    SLA_RESCUE_MARGIN_S = 3.0
+    SLA_RESCUE_MARGIN_S = 5.0 # Increased from 3.0 for more proactive deadline miss prevention
     time_remaining = state.sla_deadline_s - state.oldest_task_age_s
     if time_remaining < SLA_RESCUE_MARGIN_S and state.cloud_queue_depth > 0:
         effective_target = max_workers # Override any previous calculation to ensure safety.
```

