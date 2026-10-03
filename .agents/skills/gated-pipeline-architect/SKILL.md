---
name: gated-pipeline-architect
description: Design and implement robust gated statistical data pipelines. Enforces config-driven architectures, runtime type validation, zero hardcoding between pipeline gates, and mandatory tool grounding to prevent hallucinating or reinventing existing libraries.
metadata:
  origin: custom
---

# Gated Pipeline Architect

This skill guides the design, auditing, and implementation of sequential, gated statistical pipelines where each section enforces a statistical or data-quality gate before downstream stages can proceed.

## Core Mandates

1. **Tool Grounding First**: Never hallucinate APIs or write custom implementations of existing libraries (e.g., OpenEvolve, SciPy, Great Expectations). Ground yourself on actual packages before writing code.
2. **Zero Hardcoded Coupling**: No downstream gate may hardcode intermediate JSON or assume static upstream results. The primary dataset is the single source of truth.
3. **Config-Driven Operations**: All thresholds, tolerances, alpha levels, and file paths must live in external configuration files (YAML/JSON), not in code.
4. **Runtime Type Validation**: All configurations and gate verdict outputs must be validated through strict typed schemas (e.g., Pydantic or TypedDict).

## Workflow

### Step 1 - Tool Grounding & Anti-Reinvention Audit
Before drafting or modifying code:
- Search the environment for designated packages (e.g., `python -c "import <tool>"`).
- If an existing tool or framework (e.g., OpenEvolve, SciPy, Statsmodels) is mentioned or applicable, verify its real API signatures and documentation rather than inventing wrapper functions or rolling custom implementations.
- Refer to `references/tool-grounding.md` for the exact grounding protocol.
- **Done when:** The tool's installation status is confirmed, real imports are verified, and no mock or invented substitute module exists.

### Step 2 - Externalize Gate Configuration
Define all thresholds and parameters in an external YAML or JSON file:
- Isolate dataset paths, target feature names, test selections (e.g., Kolmogorov-Smirnov, Shapiro-Wilk, Student-t), significance thresholds ($\alpha$), and tolerance limits.
- Never write hardcoded magic numbers into gate logic.
- **Done when:** A valid configuration file (e.g., `pipeline_config.yaml`) exists and fully describes all gate parameters.

### Step 3 - Define Typed Schemas & Runtime Contracts
Define Pydantic or dataclass models for:
- `GateConfig`: Validates and parses the configuration file.
- `GateResult`: The structured, immutable output of every gate (`gate_name`, `passed: bool`, `p_value`, `test_statistic`, `metrics`, `details`, `timestamp`).
- `PipelineRunState`: Accumulates dynamic results across gates.
- Refer to `references/contracts-and-type-validation.md` for schema templates.
- **Done when:** Configuration and gate verdicts parse cleanly through type validators with zero runtime schema errors.

### Step 4 - Implement Dynamic Statistical Gates (Anti-Leakage)
Implement each gate as an independent, deterministic callable:
- Each gate takes the primary dataset + typed configuration + optional previous gate verdicts.
- The gate dynamically calculates statistics directly from data; it never expects or hardcodes static test statistics or canned mock JSON.
- If a gate fails, it immediately emits `passed=False` with error details and activates the designated policy (halt, warn, or branch).
- **Done when:** Downstream gates consume dynamic typed `GateResult` objects and execute properly regardless of variation in upstream results.

### Step 5 - Audit & Verification
Run automated tests covering:
1. **Config Validation**: Malformed thresholds or missing fields raise validation errors at startup.
2. **Dynamic Behavior**: Altering data distribution correctly trips statistical gates without code changes.
3. **Anti-Hardcoding Scan**: Grep the codebase for hardcoded magic numbers, fixed p-values, or baked-in test responses.
- **Done when:** All tests pass, static scans reveal zero hardcoded values, and schema validation holds on both passing and failing runs.

## Anti-Patterns

- **Hallucinating / Mocking Libraries**: Writing a synthetic `openevolve.py` or fake statistical function instead of using verified packages.
- **Hardcoding Gate Verdicts**: Writing `if result["p_val"] < 0.05` where `0.05` is hardcoded in code rather than loaded from configuration.
- **Coupling via Side-Effects**: Having Gate 2 read an undocumented, mutated global variable or disk file left by Gate 1.
- **Untyped Dictionaries**: Passing arbitrary untyped `dict` payloads between gates instead of validated schemas.

## Companion References

- `references/tool-grounding.md`: Anti-hallucination and tool discovery checklist.
- `references/contracts-and-type-validation.md`: Pydantic schema models, configuration patterns, and anti-leakage checklist.
