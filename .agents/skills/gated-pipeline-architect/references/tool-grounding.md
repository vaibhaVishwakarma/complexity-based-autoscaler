# Tool Grounding and Anti-Reinvention Protocol

When building statistical validation gates, evolutionary loops, or data pipelines, agents often suffer from two major failure modes:
1. **Reinventing the Wheel**: Reimplementing complex statistical algorithms or evolutionary mechanics from scratch when robust libraries already exist.
2. **Hallucination / Mocking**: Inventing non-existent APIs, methods, or CLI commands for tools (e.g. `openevolve`, `great_expectations`, `statsmodels`).

## 1. Grounding Workflow

Before writing any custom algorithmic module or wrapper:

1. **Environment Probe**:
   Check if the specified tool or library is installed:
   ```bash
   python -c "import <tool_name>; print(<tool_name>.__file__)"
   pip show <tool_name>
   ```

2. **Package & API Discovery**:
   - Inspect actual exports: `python -c "import <tool_name>; print(dir(<tool_name>))"`
   - Check CLI commands: `<tool_name> --help` or `which <tool_name>`
   - If not installed, ask or check whether it should be installed from PyPI/source rather than mocked in code.

3. **Anti-Hallucination Rules**:
   - **Never mock or synthesize a substitute library** (e.g., creating a file named `openevolve.py` with dummy classes) without explicit instruction from the user.
   - If a library like OpenEvolve is required, import and configure the actual package; if it is unavailable in the environment, report the missing dependency immediately.
   - For statistical tests (e.g. Kolmogorov-Smirnov, t-tests, Mann-Whitney, chi-square), always prefer standard library implementations (`scipy.stats`, `statsmodels`) over handwritten mathematical approximations.

4. **External Knowledge Verification**:
   If uncertain of an API signature or parameter names, use web search or inspect local docstrings (`help(module.function)` or inspect module source) before writing code that calls it.
