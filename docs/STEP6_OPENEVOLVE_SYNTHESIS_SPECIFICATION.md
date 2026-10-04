# Step 6 & 7 Specification: OpenEvolve Evolutionary Policy Synthesis & Cascade Evaluation Architecture

**Document Role**: Authoritative technical specification and execution blueprint for simulation-in-the-loop evolutionary synthesis of the Conformal Autoscaler using OpenEvolve.  
**Roadmap Milestones**: Step 6 (Evaluator & Fitness Engine) and Step 7 (Evolutionary Policy Search) of the [Unified Strategy](file:///home/vaibo/edgecompute/docs/CONFORMAL_AUTOSCALER_STRATEGY.md#12-chronological-execution-roadmap-and-verification-checklist).  
**Upstream Provenance**: Baseline empirical data from [`docs/STEP5_NON_CONFORMAL_BASELINES_REPORT.md`](file:///home/vaibo/edgecompute/docs/STEP5_NON_CONFORMAL_BASELINES_REPORT.md) & [`output/suite_baselines_runs/suite_baselines_summary.csv`](file:///home/vaibo/edgecompute/output/suite_baselines_runs/suite_baselines_summary.csv).  
**Testbed Infrastructure**: ContinuumBench / Eclypse discrete-event engine (`clones/ContinuumBench/`).  
**Evolution Framework**: OpenEvolve (`clones/openevolve/`, installed in `./.venv`).  
**Governance Compliance**: Adheres strictly to [`AGENTS.md`](file:///home/vaibo/edgecompute/AGENTS.md) Rules #1, #2, #3, #4, #5, and #6.

---

## 1. Executive Summary & Synthesis Objective

The goal of this phase is to evolve a **Pareto-optimal Conformal Autoscaling Control Law** that simultaneously resolves the four catastrophic failure modes identified during the Step 5 baseline benchmark:
1. **The Over-Provisioning Penalty** (Fixed Capacity: 27,900.0 worker-seconds, 0% savings).
2. **The Scale-to-Zero Drain Drop** (Kubernetes HPA: 72 deadline misses in `suite1_zero_terminal`).
3. **Semantic Drift Blindness** (InferLine Tuner: 23 deadline misses during Suite 2 complexity shocks).
4. **Queue Reaction Flapping & Thrashing** (KEDA Queue: 205 deadline misses, 1,710 scaling deltas).

```
                      THE OPENEVOLVE SYNTHESIS CYCLE
                      
  ┌────────────────────────────────────────────────────────┐
  │                 LLM MUTATION OPERATOR                  │
  │  • Receives current seed code + System Message         │
  │  • Generates git-style diffs modifying formulas        │
  │  • Ingests execution artifacts from prior failures     │
  └───────────────────────────┬────────────────────────────┘
                              │ Proposed Candidate Policy
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │         STATIC AST & SIGNATURE VALIDATION GATE         │
  │  • Checks TelemetricState access (0.001s)              │
  │  • Blocks hallucinated variables or unauthorized libs  │
  └───────────────────────────┬────────────────────────────┘
                              │ Syntactically Verified
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │        CASCADE SIMULATION-IN-THE-LOOP EVALUATOR        │
  │  • Stage 1 (0.05s): Runtime Sanity & Exception Gate    │
  │  • Stage 2 (2.0s):  Multi-Stress Micro-Tranche         │
  │  • Stage 3 (20.0s): Full 13-Regime Authoritative Run   │
  └───────────────────────────┬────────────────────────────┘
                              │ EvaluationResult(metrics, artifacts)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │      MAP-ELITES ARCHIVE & ASYMMETRIC ISLAND MODEL      │
  │  • 3D Grid: Cost Savings × Churn Stability × Tail Latency
  │  • Island 0 (Core) ──[One-Way Migration]──> Island 1   │
  └────────────────────────────────────────────────────────┘
```

---

## 2. Telemetry State Contract & Anti-Hallucination Guardrails

To prevent the LLM from inventing non-existent features while ensuring it has access to all causal signals necessary for breakthrough performance, all candidate policies operate against a strictly typed `TelemetricState` dataclass.

### 2.1 The 4-Tier Telemetric State Schema (`TelemetricState`)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TelemetricState:
    """
    Authoritative, immutable telemetric observation contract delivered
    to the autoscaler at timestep t. Every attribute is causally observable
    at time t with zero lookahead or oracle leakage.
    """
    # ─── TIER 1: EDGE SEMANTIC TRIAGE TELEMETRY ────────────────────────
    p_fast: float
        """Empirical acceptance ratio: fraction of frames handled locally (|C(x)| = 1)."""
    p_fast_velocity: float
        """Rate of change: dp_fast/dt over a 3-epoch sliding window."""
    mean_set_size: float
        """Mean RAPS prediction set size E[|C(x)|]. RAPS calibrated at alpha=0.10, q_hat=0.79914."""
        
    # ─── TIER 2: CONTINUUM TRAFFIC DYNAMICS ────────────────────────────
    ingress_rps: float
        """Arriving Poisson sensor request rate lambda(t) at IoT sensor ingress."""
    ingress_acceleration: float
        """Second derivative d^2(lambda)/dt^2 indicating sudden ramp/burst onset."""
    offered_cloud_rps: float
        """Causal multiplicative demand: lambda_cloud(t) = ingress_rps * (1 - p_fast)."""
        
    # ─── TIER 3: CLUSTER QUEUE BACKLOG & AGING ────────────────────────
    cloud_queue_depth: int
        """Current unserviced task backlog Q_t waiting at the CloudRefine ingress queue."""
    cloud_queue_velocity: float
        """Rate of backlog change: dQ/dt differentiating transient bursts from growing queues."""
    oldest_task_age_s: float
        """Age of head-of-line queued task, measuring proximity to the 15.0s SLA deadline."""
        
    # ─── TIER 4: WORKER FLEET & ACTUATION STATE ────────────────────────
    active_workers: int
        """Currently active, healthy CloudRefine GPU workers (k_t in [1, 18])."""
    booting_workers: int
        """Workers currently spinning up subject to the 1.0s container startup delay."""
    time_since_last_scale_s: float
        """Elapsed seconds since the last scaling action (cooldown / drain tracking)."""
        
    # ─── HARDWARE & CONTRACT CONSTANTS ────────────────────────────────
    worker_capacity_rps: float = 16.0
        """Profiled Tesla T4 service rate (mu): 0.0625s per inference."""
    sla_deadline_s: float = 15.0
        """End-to-end SLA latency budget: D = 15.0 seconds."""
```

### 2.2 The 4-Tier Guardrail Enforcement Pipeline

1. **Explicit Typed Signature Contract**:
   Candidate policies must conform to:
   ```python
   # EVOLVE-BLOCK-START
   def compute_target_workers(state: TelemetricState) -> int:
       ...
   # EVOLVE-BLOCK-END
   ```
2. **Pre-Execution Static AST Inspection**:
   Before a simulation process is spawned, the evaluator parses the code's Abstract Syntax Tree (AST):
   ```python
   import ast

   VALID_ATTRIBUTES = set(TelemetricState.__dataclass_fields__.keys())

   def validate_ast(code_str: str) -> list[str]:
       tree = ast.parse(code_str)
       errors = []
       for node in ast.walk(tree):
           # Block unauthorized imports
           if isinstance(node, (ast.Import, ast.ImportFrom)):
               errors.append(f"Unauthorized import detected: {ast.dump(node)}")
           # Block hallucinated state variables
           if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
               if node.value.id == "state" and node.attr not in VALID_ATTRIBUTES:
                   errors.append(f"Invalid feature access: state.{node.attr}")
       return errors
   ```
   If an invalid variable is attempted (e.g. `state.gpu_temp`), the AST checker aborts in **0.001 seconds**, preventing simulation crashes.
3. **Runtime Execution Sandboxing**:
   Candidate functions execute in an isolated namespace containing only standard mathematical primitives (`min`, `max`, `abs`, `round`, `math`, `np`).
4. **Artifact Feedback Loop**:
   If an AST check or runtime exception occurs, the exact traceback and error context are written to `EvaluationResult(artifacts={"error_message": ...})`. OpenEvolve automatically injects this feedback into the prompt for the next generation, forcing the LLM to self-correct.

---

## 3. Decoupling: Capacity Sizing vs. Node Placement

Adhering strictly to **AGENTS.md Rule #2 (Decoupled Linkage)**, the autoscaler does **not** decide which physical or virtual node is powered down.
- **Autoscaler Responsibility (The Sizer)**: Determines the optimal target worker capacity $k_t \in [1, 18]$ to guarantee SLA compliance while minimizing cost.
- **Substrate Scheduler Responsibility (The Placer)**: The ContinuumBench placement engine (`clones/ContinuumBench/src/continuum_bench/controllers/autoscaling_baselines.py`) handles:
  - Worker bin-packing across the 6 Cloud GPU nodes (`Cloud_0` to `Cloud_5`).
  - Worker container termination and node consolidation.
  - VM power-down when a host becomes completely empty.

---

## 4. The 3-Stage Cascade Evaluator: Preventing Surrogate Bias

A fundamental hazard in evolutionary coding is **Surrogate Evaluation Bias**: if an early smoke filter ranks candidates on an easy, flat workload, it promotes dumb over-provisioners and prunes sophisticated adaptive algorithms.

To prevent this, our cascade evaluator enforces a strict distinction:
- **Stages 1 & 2 are strictly Go / No-Go Validity Gates.**
- **Stage 3 is the ONLY stage that ranks candidates in the MAP-Elites database.**

```
Stage 1: Pure Validity Gate (~0.05s)
  │  • Tests AST, division-by-zero, bounds [1, 18]
  │  • Metric: stage1_passed in {0.0, 1.0} (Threshold = 0.5)
  ▼ Passed
Stage 2: Multi-Stress Micro-Tranche (~2.0s)
  │  • 10-epoch Flat slice (checks downscaling capability)
  │  • 10-epoch Shock slice (checks p_fast collapse reaction)
  │  • 10-epoch Zero-Terminal slice (checks drain guard)
  │  • Permissive Threshold: Completion >= 90%, Queue < 50
  ▼ Passed
Stage 3: Authoritative 13-Regime Benchmark (~20.0s)
  │  • Full 121,134 requests across all 13 regimes
  │  • Computes Fitness J and MAP-Elites feature coordinates
  ▼
Archive & Population Update
```

### 4.1 Stage 1: Pure Validity Gate (~0.05s)
- **Objective**: Verify that code executes without Python exceptions under extreme boundary conditions.
- **Execution**: Evaluates `compute_target_workers(state)` on synthetic boundary states:
  - Zero Fast-Path: `state.p_fast = 0.0`
  - Max Ingress: `state.ingress_rps = 200.0`
  - Zero Ingress: `state.ingress_rps = 0.0, state.cloud_queue_depth = 0`
- **Pass Criteria**: Returns an integer $k \in [1, 18]$ with zero crashes. Output metric: `stage1_passed = 1.0`. Threshold: `0.5`.

### 4.2 Stage 2: Multi-Stress Micro-Tranche (~2.0s)
- **Objective**: Verify that the policy does not catastrophically collapse when subjected to contrasting dynamics.
- **Execution**: Runs a 30-epoch condensed simulation episode containing three 10-epoch slices:
  1. *Flat traffic*: Verifies the policy does not permanently clamp to 18 workers.
  2. *Complexity shock ($p_{\text{fast}} \downarrow 0.20$)*: Verifies the policy detects semantic drift and scales up before queues explode.
  3. *Zero-terminal drop ($\lambda \to 0$)*: Verifies the policy does not prematurely kill workers while tasks are in flight.
- **Pass Criteria**: Must complete $\ge 90\%$ of requests and maintain mean queue wait $< 1.0$s.
- **Permissive Safety Net**: Deliberately avoids fine-grained ranking to ensure innovative, non-traditional strategies pass through to Stage 3.

### 4.3 Stage 3: Authoritative 13-Regime Benchmark (~20.0s)
- **Objective**: Authoritative Pareto-optimal performance evaluation across the continuum.
- **Execution**: Runs full simulation episodes across all 13 calibrated regimes (121,134 requests).
- **Primary Fitness Metric ($J$)**:
  $$J = - \left( 1.0 \cdot \text{Deadline\_Misses} + 0.20 \cdot \frac{\text{Worker\_Seconds}}{100} + 0.05 \cdot \text{Scaling\_Deltas} \right) + 0.01 \cdot \text{Completed\_Requests}$$
  - SLA violations (deadline misses $> 15.0$s) are penalized with weight $1.0$.
  - Cloud worker-seconds are penalized with weight $0.20 / 100$.
  - Actuation flapping (scaling deltas) is penalized with weight $0.05$.
  - Successful throughput provides a positive reward with weight $0.01$.

---

## 5. Asymmetric Island Topology: Directed One-Way Gene Flow

To explore high-risk, creative policy mutations without risking corruption of the mathematically sound conformal baseline, we implement an **Asymmetric Source-Sink Island Topology** using OpenEvolve's `PopulationStrategy.migrate` hook.

```
  ┌────────────────────────────────────────────────────────┐
  │         ISLAND 0: Core Conformal Branch (Source)       │
  │  • Strict Adaptive Conformal Inference (ACI)           │
  │  • Asymmetric scale-down with statistical certainty   │
  │  • Receives ZERO migrations from Island 1              │
  └───────────────────────────┬────────────────────────────┘
                              │
                              │  ONE-WAY MIGRATION
                              │  (Core breakthroughs flow down)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │      ISLAND 1: Experimental Radical Branch (Sink)      │
  │  • Non-linear momentum, learned preemption heuristics  │
  │  • High exploration temperature                        │
  │  • NEVER sends programs back to Island 0               │
  └────────────────────────────────────────────────────────┘
```

### 5.1 Python Implementation of Directed Migration
```python
from openevolve.population import PopulationStrategy, MigrationMove, PopulationSnapshot

def directed_source_sink_migration(snapshot: PopulationSnapshot) -> list[MigrationMove]:
    """
    Enforces asymmetric gene flow:
    - Island 0 (Core) -> Island 1 (Experimental): ALLOWED
    - Island 1 (Experimental) -> Island 0 (Core): FORBIDDEN
    """
    moves = []
    # Identify the elite program on Island 0
    island_0_pids = list(snapshot.islands[0])
    if island_0_pids:
        best_p0_id = max(
            island_0_pids,
            key=lambda pid: snapshot.programs[pid].metrics.get("combined_score", float("-inf"))
        )
        # Migrate a copy of the Core elite into the Experimental Island
        moves.append(MigrationMove(program_id=best_p0_id, target_island=1))
        
    # Island 0 receives NO incoming moves, preserving mathematical purity
    return moves

custom_population_strategy = PopulationStrategy(
    migrate=directed_source_sink_migration
)
```

---

## 6. MAP-Elites Quality-Diversity Feature Dimensions

To ensure that the population maintains a diverse archive of candidate policies across the Pareto frontier, OpenEvolve maps surviving programs into a 3-dimensional feature grid:

```yaml
database:
  feature_dimensions:
    - "cost_savings"      # Continuous: percentage worker-seconds saved vs Fixed (27,900s)
    - "churn_stability"   # Continuous: 2000.0 - scaling_deltas
    - "tail_safety"       # Continuous: 15.0 - p99_latency
  feature_bins:
    cost_savings: 10
    churn_stability: 10
    tail_safety: 10
```
This guarantees that ultra-conservative (zero-miss) policies, ultra-low-cost policies, and hyper-stable (zero-churn) policies are preserved simultaneously, enabling cross-over between distinct policy phenotypes.

---

## 7. Concrete File Structure & Implementation Roadmap

Execution proceeds by creating the following modular files in the repository:

| File Path | Component Role | Key Contents |
| :--- | :--- | :--- |
| `src/continuum_ext/evolution/seed_policy.py` | Initial Seed Program | Typed `TelemetricState` dataclass + baseline multiplicative conformal policy bounded by `# EVOLVE-BLOCK-START/END`. |
| `src/continuum_ext/evolution/openevolve_evaluator.py` | Multi-Stage Evaluator | Implements `evaluate_stage1` (sanity), `evaluate_stage2` (triad stress), and `evaluate_stage3` (full 13 regimes) returning `EvaluationResult`. |
| `src/continuum_ext/evolution/population_policy.py` | Migration Strategy | Implements `directed_source_sink_migration` hook for asymmetric gene flow. |
| `configs/evolution/openevolve_config.yaml` | Framework Configuration | OpenEvolve YAML setting models (`gemini-2.5-pro` / `flash`), cascade thresholds (`[0.5, -50.0]`), timeouts, and MAP-Elites bins. |
| `scratch/run_evolution.py` | Execution Launcher | Orchestrates OpenEvolve evolutionary search in `./.venv` with logging and checkpointing. |

---

*Specification verified against OpenEvolve v0.4.0 source code and ContinuumBench runtime contracts in strict compliance with AGENTS.md.*
