# Pipeline Contracts, Config Files, and Type Validation

This reference specifies how to decouple sequential statistical gates and prevent downstream leakage or hardcoding.

## 1. Principles of Gated Pipelines

- **Primary Dataset Integrity**: The dataset remains the immutable ground truth. Gates read the dataset or subsets, but do not mutate raw underlying inputs unpredictably.
- **Zero Result Hardcoding**: No downstream gate should contain hardcoded assumptions about upstream results (e.g. `prev_gate_p_val = 0.032` or static JSON files).
- **Explicit Gate Verdicts**: Every gate outputs a typed verdict schema (`GateResult`). Downstream gates consume this verdict dynamically.
- **Fail-Fast / Circuit-Breaker**: If a gate fails its statistical criteria, the pipeline halts immediately or branches into a designated diagnostic path.

## 2. Configuration Pattern (YAML / JSON)

Never hardcode thresholds, column names, sample sizes, or p-value cutoffs in Python code. Place them in a configuration file:

```yaml
# pipeline_config.yaml
dataset:
  path: "data/primary_dataset.parquet"
  id_column: "sample_id"

gates:
  - name: "normality_check"
    gate_type: "statistical"
    test: "shapiro_wilk"
    columns: ["feature_a", "feature_b"]
    alpha_threshold: 0.05
    on_failure: "halt"

  - name: "distribution_drift"
    gate_type: "statistical"
    test: "kolmogorov_smirnov"
    reference_split: "baseline"
    target_split: "candidate"
    significance_level: 0.01
    max_drift_ks_stat: 0.15
    on_failure: "halt"

  - name: "metric_stability"
    gate_type: "variance_threshold"
    metric: "f1_score"
    min_value: 0.85
    max_variance: 0.02
    on_failure: "warn"
```

## 3. Pydantic Runtime Type Validation

Use Pydantic (or dataclasses with runtime type checks) to enforce strict contracts for configs and gate outputs:

```python
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class GateConfig(BaseModel):
    name: str = Field(..., min_length=1)
    gate_type: Literal["statistical", "schema", "variance_threshold"]
    alpha_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    on_failure: Literal["halt", "warn", "skip"] = "halt"
    parameters: Dict[str, Any] = Field(default_factory=dict)


class GateResult(BaseModel):
    gate_name: str
    passed: bool
    test_statistic: Optional[float] = None
    p_value: Optional[float] = None
    threshold: Optional[float] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None


class PipelineRunState(BaseModel):
    run_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    gate_results: List[GateResult] = Field(default_factory=list)
    status: Literal["running", "passed", "failed"] = "running"

    def record_gate(self, result: GateResult) -> bool:
        self.gate_results.append(result)
        if not result.passed:
            self.status = "failed"
            return False
        return True
```

## 4. Anti-Leakage Checklist

1. [ ] Are test statistics computed dynamically on the primary dataset?
2. [ ] Are p-value cutoffs, confidence levels, and tolerance margins read strictly from `GateConfig`?
3. [ ] Does Gate $N$ receive Gate $N-1$'s output strictly as a validated `GateResult` object, rather than looking at raw local variables or static JSON fixtures?
4. [ ] Does the pipeline raise an explicit `GateFailureException` or halt when a required statistical gate fails?
