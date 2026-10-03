# Conformal Autoscaler — Full System Architecture

---

## 1 · The Real System Being Simulated

This is the actual edge–cloud split inference pipeline. ContinuumBench simulates it as a discrete-time Eclypse service graph.

```
┌──────────────────────────────── EDGE NODE (IoT / MEC tier) ──────────────────────────────────┐
│                                                                                                │
│   Camera / IoT Source                                                                          │
│   ─────────────────                                                                            │
│   λ(t) requests/epoch  ──►  EdgePreprocess          EdgeInference (TinyViT ResNet-152)        │
│   [CameraSource]             [0.45 s/req]      ──►  [0.60 s/req, conformal scorer]           │
│                                                                                                │
│                                                         │              │                       │
│                                                    fp(t) fraction  (1−fp(t)) fraction          │
│                                                    HIGH confidence  LOW confidence             │
│                                                    [FAST PATH ✓]   [SLOW PATH →]              │
│                                                         │              │                       │
│                                                         ▼              ▼                       │
└──────────────────────────────── EDGE ───────────────── Sink  ←────── │ ────────────────────┘
                                                         ▲              │
                                                         │              │  WAN link
                                                         │              ▼
┌──────────────────────────────── CLOUD (GPU tier — T4) ────────────────────────────────────────┐
│                                                                                                │
│          CloudRefine Worker Pool  (0–N active workers, each 1.8 s/req)                        │
│          ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                   │
│          │ w_0 ✓  │  │ w_1 ✓  │  │ w_2 ✓  │  │ w_3 ✗  │  │ w_4 ✗  │  ...              │
│          │ ACTIVE │  │ ACTIVE │  │ ACTIVE │  │INACTIVE│  │INACTIVE│                         │
│          └────┬───┘  └────┬───┘  └────┬───┘  └─────────┘  └─────────┘                   │
│               └───────────┴───────────┘                                                       │
│                           │  refined results                                                   │
└───────────────────────────┼───────────────────────────────────────────────────────────────────┘
                            └────────────────────────────────────────────► Sink
```

> [!IMPORTANT]
> **The autoscaler controls ONLY the CloudRefine worker pool** — the number of active workers `N`.  
> `CameraSource`, `EdgePreprocess`, `EdgeInference`, and `Sink` are **fixed** — no scaling decisions apply to them.  
> The fast-path / slow-path **split ratio `fp(t)`** is determined entirely by `EdgeInference`'s conformal scorer — the autoscaler **observes** it but does not set it.

---

## 2 · ContinuumBench Simulation Layer

How the real system above is implemented as a discrete-time simulation inside Eclypse:

```
┌──────────────────────────── CONTINUUM BENCH SIMULATION LOOP (1 epoch = 1 s) ──────────────────┐
│                                                                                                  │
│  EPOCH t                                                                                         │
│  ────────                                                                                        │
│                                                                                                  │
│  1. WorkloadGenerator.sample_2d(t)                                                               │
│       └─► (λ_t, fp_t)  ← Suite 1/2 parametric OR Suite 3 Azure trace + overlay                 │
│                                                                                                  │
│  2. CameraSource injects λ_t Poisson arrivals into EdgePreprocess queue                          │
│                                                                                                  │
│  3. SkeletonService._step_transform() runs for each stage:                                       │
│       EdgePreprocess   → drains buffer at processing_time=0.45 s                                │
│       EdgeInference    → drains buffer at processing_time=0.60 s                                │
│                           TRIAGE: fp_t fraction → Sink (fast path)                              │
│                                   (1−fp_t) fraction → CloudRefine queue (slow path)             │
│                                                                                                  │
│  4. Each ACTIVE CloudRefine worker drains from the shared pool queue                             │
│       processing_time = mean_ms(batch_size) / 1000  ← from Gate 2 contract surface             │
│       (workers share queue round-robin; inactive workers consume ε resources only)              │
│                                                                                                  │
│  5. Sink records latency, SLO hits/misses (deadline_s = 12.0 s)                                │
│                                                                                                  │
│  6. WorkerPoolManager.snapshots() → ControllerState                                             │
│       state.queue_depths["CloudRefine"] = current backlog item count                            │
│       state.worker_pools["CloudRefine"] = WorkerPoolSnapshot(active, inactive, ready...)        │
│       state.metadata["fast_path_fraction"] = fp_t          ← ONLY conformal controller uses   │
│       state.metadata["mean_set_size"]      = set_size_t    ← ONLY conformal controller uses   │
│                                                                                                  │
│  7. Controller.step(state) → ControllerAction                                                   │
│       scale = [ScaleAction("CloudRefine", desired_N)]                                           │
│       placement = {worker_id → node_id}  ← Eclypse placement                                   │
│                                                                                                  │
│  8. WorkerPoolManager.set_active_workers("CloudRefine", desired_N)                              │
│       Workers w_0 … w_{N-1}: ACTIVE  (full resource allocation)                                │
│       Workers w_N … w_max:   INACTIVE (ε resource allocation, no queue drain)                  │
│                                                                                                  │
│  REPEAT for epoch t+1                                                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3 · Fast Path vs Slow Path — Data Flow Detail

```
                    λ(t) total requests arrive
                            │
                            ▼
                    ┌───────────────┐
                    │ EdgeInference │   processing_time = 0.60 s/req
                    │  Conformal    │   scores each request with
                    │  Scorer       │   TinyViT ResNet-152 ONNX
                    └──────┬────────┘
                           │
              ┌────────────┴─────────────┐
              │                          │
   FAST PATH  │  fp(t) fraction          │  SLOW PATH  (1 − fp(t)) fraction
   ──────────►│  High-confidence pred    │  Low-confidence / large set
              │  Set size ≤ threshold    │  Set size > threshold
              │  q_hat = 0.7991          │  q_hat = 0.7991
              ▼                          ▼
          ┌───────┐              ┌──────────────────┐
          │ Sink  │              │ CloudRefine Queue │
          │(done) │              │ (backlog grows if │
          └───────┘              │  workers < demand)│
                                 └────────┬─────────┘
                                          │
                              ┌───────────┴──────────────┐
                              │  Active CloudRefine       │
                              │  Workers w_0 … w_{N-1}   │
                              │  Each: 1.8 s/req          │
                              │  T4 GPU, batch_size=8     │
                              │  Capacity: 77.92 RPS/node │
                              └───────────┬──────────────┘
                                          ▼
                                       Sink
```

**Key insight:** `fp(t)` is the only signal that reveals whether the CloudRefine pool is about to be overloaded. **When `fp` drops, more requests take the slow path** — the GPU queue grows. The autoscaler must act *before* the queue grows.

---

## 4 · What Each Controller Actually Sees

This is the core differentiator between the 6 competitors:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  state.queue_depths["CloudRefine"]  ← ALL controllers see this (queue backlog)          │
│  state.worker_pools["CloudRefine"]  ← ALL controllers see this (active/inactive counts) │
│  state.epoch, state.time_s          ← ALL controllers see this                          │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  state.metadata["fast_path_fraction"]  fp(t)   ← ONLY ConformalAutoscaler uses this    │
│  state.metadata["mean_set_size"]       C̄(t)    ← ONLY ConformalAutoscaler uses this    │
│  state.metadata["effective_alpha"]     α̂(t)    ← ONLY ConformalAutoscaler uses this    │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

| Controller | Sees queue? | Sees fp(t)? | Sees C̄(t)? | Decision signal |
|---|---|---|---|---|
| **FixedCapacity** | ✗ (ignores) | ✗ | ✗ | none — static peak |
| **HPA** | ✓ (utilisation proxy) | ✗ | ✗ | `queue / active / target_util` |
| **KEDA** | ✓ (trigger) | ✗ | ✗ | `ceil(queue / target_per_worker)` |
| **InferLine** | ✓ (multi-scale EMA) | ✗ | ✗ | `max(EMA_fast, mid, slow) × 1.15` |
| **ComplexityBlind** | ✓ (single EMA) | ✗ (logs only) | ✗ | `λ_forecast × (1 − 0.50_assumed)` |
| **ConformalAutoscaler** | ✓ | ✓ **proactive** | ✓ **headroom** | `λ_slow = λ × (1 − fp(t))` |

> [!NOTE]
> `state.metadata` is populated by the scenario runner each epoch. For **non-conformal baselines**, the fp fields are still present in `metadata` — they just **never read them**. This is verified by the `ComplexityBlindPredictiveController` which explicitly logs `actual_fp_from_metadata` in its diagnostics without using it in any decision path.

---

## 5 · Autoscaler Scope — What Is and Isn't Controlled

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        OUT OF AUTOSCALER SCOPE                               │
│                                                                              │
│  CameraSource ──► EdgePreprocess ──► EdgeInference                           │
│  [fixed]            [fixed]            [fixed + fp(t) scorer]               │
│                                                                              │
│  These stages are always-on singletons. Their processing_time values         │
│  come from the Gate 1 calibration config (or YAML scenario defaults).        │
│  The autoscaler never emits ScaleAction for these stages.                    │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                         IN AUTOSCALER SCOPE ← ONLY THIS                     │
│                                                                              │
│   CloudRefine Worker Pool                                                    │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │ Controller decides: how many of w_0 … w_max are ACTIVE each epoch   │  │
│   │ Range: [min_workers=1, max_workers=N_max from YAML]                  │  │
│   │                                                                      │  │
│   │ Placement: which Eclypse node each active worker is assigned to      │  │
│   │ (best_fit heuristic, or MILP solver if configured)                   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│   Sink — always on, out of scope                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 6 · Gate Contracts in the Simulation Loop

```
          Gate 1 Contract                     Gate 2 Contract
          ───────────────                     ───────────────
  gate1/configs/calibration_config.json   gate2/output-gpu-t4/
                                          triton_service_profiles.json
          │                                       │
          │  q_hat = 0.7991                       │  by_batch_size → p50_ms, p95_ms
          │  alpha = 0.10                         │  capacity(b=8, τ=40ms) = 77.92 RPS/node
          │  fast_path_fraction = 0.50            │
          ▼                                       ▼
  contracts/gate1.py                      contracts/gate2.py
  Gate1CalibrationConfig                  Gate2HardwareProfile
  load_gate1_config()                     load_gate2_profiles()
                                          compute_service_capacity_rps()
          │                                       │
          │                                       │
          ▼                                       ▼
  ┌─────────────────────────────────────────────────────────┐
  │              SIMULATION EPOCH                           │
  │                                                         │
  │  EdgeInference triage: fp(t) computed from              │
  │  conformal scorer using q_hat from Gate 1 ─────────────►│──► state.metadata["fp"]
  │                                                         │
  │  CloudRefineWorker processing_time = mean_ms(b) / 1000  │
  │  loaded from Gate 2 surface (NOT hardcoded) ────────────►│──► SkeletonService
  │                                                         │
  │  ConformalAutoscalerController:                         │
  │    _q_hat loaded from Gate 1 ───────────────────────────►│──► headroom decisions
  │    _capacity_rps loaded from Gate 2 ────────────────────►│──► worker sizing
  └─────────────────────────────────────────────────────────┘
```

---

## 7 · Infrastructure Simulation (Eclypse Layer)

```
ECLYPSE INFRASTRUCTURE GRAPH
(build_extended_continuum → InfraBundle)

  IoT Layer          Edge Layer          Cloud Layer
  ─────────          ──────────          ───────────
  ┌─────────┐        ┌──────────┐        ┌──────────────────────┐
  │ iot_0   │───────►│ edge_0   │───────►│ cloud_0  (T4 GPU)    │
  │ iot_1   │        │ edge_1   │        │ cloud_1  (T4 GPU)    │
  │   ...   │        │   ...    │        │   ...                │
  └─────────┘        └──────────┘        └──────────────────────┘
  
  Each node has: cpu, ram, storage, placement_layers
  
  SERVICE → NODE PLACEMENT (per epoch, if replan triggered):
  
  CameraSource    → iot layer node        (fixed by resource profile)
  EdgePreprocess  → edge layer node       (fixed by resource profile)
  EdgeInference   → edge layer node       (fixed by resource profile)
  Sink            → any layer             (fixed by resource profile)
  CloudRefine_w_i → cloud layer node      ← PLACED BY AUTOSCALER
                                            (best_fit or MILP)
  
  Inactive workers: resource requirements → ε (near-zero)
  so they don't consume node capacity and placement is trivial.
```

---

## 8 · ConformalAutoscaler Decision Flow (Per Epoch)

```
EPOCH t ──────────────────────────────────────────────────────────────────────

  state.metadata["fast_path_fraction"] = fp_t       (e.g. 0.20 — alarm)
  state.metadata["mean_set_size"]      = C̄_t        (e.g. 2.8 — ambiguous)
  state.queue_depths["CloudRefine"]    = Q_t         (e.g. 35 items)
  state.worker_pools["CloudRefine"].active_workers = N_t   (e.g. 5)

  ① Compute λ_slow(t):
       λ_hat   = Q_t × (capacity_rps / N_t)    = 35 × (77.92/5) = 545 RPS
       λ_slow  = λ_hat × (1 − fp_t)            = 545 × 0.80     = 436 RPS

  ② EMA smoothing:
       ema_λ_slow = α × λ_slow + (1−α) × prev_ema

  ③ Compute headroom:
       margin = 1.20 (base)
       if fp_t < 0.35:  margin += (0.35 − fp_t)  = +0.15  → margin = 1.35
       if C̄_t > 1.0:   margin += 0.10 × (C̄_t − 1.0) = +0.18 → margin = 1.53

  ④ Desired workers:
       desired = ceil(ema_λ_slow × margin / capacity_rps)
               = ceil(436 × 1.53 / 77.92) ≈ 9 workers

  ⑤ Action:
       fp_t = 0.20 < fp_preempt_threshold = 0.35
       → PROACTIVE PREEMPTION: scale to 9, BYPASS cooldown
       
       ScaleAction("CloudRefine", active_workers=9)

  ⑥ If instead fp_t = 0.65, C̄_t = 1.1, Q_t = 1 for 3 consecutive epochs:
       → FAST SCALE-DOWN: recovery_counter ≥ 3, in_recovery() = True
       ScaleAction("CloudRefine", active_workers=max(min_workers, desired))

EPOCH t+1 ────────────────────────────────────────────────────────────────────
```

---

## 9 · Baseline Comparison — How Non-Conformal Controllers React to fp Drop

```
SCENARIO: fp drops from 0.65 → 0.20 at epoch 60 (Suite 2-A: SteadyShock)
Volume λ constant at 50 RPS throughout. CloudRefine queue starts empty.

EPOCH:    59     60     61     62     63     64     65
fp:      0.65   0.20   0.20   0.20   0.20   0.20   0.20
λ_slow:   17.5   40     40     40     40     40     40
Queue:     0     0     12     28     45     60     71   ← GROWS (workers too few)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FixedCapacity        │ N=25 always. Queue never grows. 100% cost. ✓ SLO    │
│ HPA                  │ Queue=12@ep61 → scale from 5→7. Reacts at ep61.     │
│                      │ Queue grows for 2 epochs before correction.          │
│ KEDA                 │ Queue trigger fires at ep61. scale 5→ceil(12/10)=2  │
│                      │ — UNDER-provisions! Doesn't account for complexity. │
│ InferLine            │ EMA_fast(queue) rising → scales at ep62-63.         │
│                      │ 15-epoch stabilisation means slow to respond.        │
│ ComplexityBlind      │ assumes fp=0.50, ignores actual fp=0.20.            │
│                      │ Computes λ_slow with WRONG fp → under-provisions.   │
│                      │ fp field is in metadata but never read.             │
│                                                                             │
│ ConformalAutoscaler  │ fp=0.20 < 0.35 threshold detected at epoch 60.     │
│                      │ PROACTIVE: scales BEFORE queue grows.               │
│                      │ Queue stays near 0. SLO maintained.                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

> [!TIP]
> This 2–4 epoch reaction lag is the **central claim of the paper**: conformal set-size telemetry is an earlier warning signal than queue depth. By the time the queue has grown enough for reactive controllers to act, SLO violations have already accumulated.
