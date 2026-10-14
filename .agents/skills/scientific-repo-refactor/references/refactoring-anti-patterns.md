# Refactoring Anti-Patterns & Pitfalls

This reference catalogues the critical failure modes encountered during scientific codebase reorganizations and prescribes concrete preventive rules.

---

## 1. The Silent Fallback Anti-Pattern (`if ... else Path("old")`)

### The Trap
When renaming a core directory (e.g., `gate2/` $\to$ `profiling/`), developers or agents often introduce ternary checks:
```python
# ANTI-PATTERN: Silent fallback masks errors and keeps legacy names alive
PROFILING_DIR = Path("profiling") if Path("profiling").is_dir() else Path("gate2")
```
### Why It Fails
1. **Defeats the Refactoring**: The old name remains active in the code, defeating the goal of intentional renaming.
2. **Masks Upstream Failures**: If `profiling/` is missing due to a bad mount, accidental deletion, or clone failure, the script silently runs against stale legacy artifacts instead of failing fast.
3. **Prolongs Deprecation Debt**: Other developers and agents continue referencing the legacy fallback.

### The Correct Pattern
Bind strictly and unconditionally to the canonical semantic path:
```python
# CORRECT: Fail fast and explicitly
PROFILING_DIR = Path("profiling")
if not PROFILING_DIR.is_dir():
    raise FileNotFoundError(f"Required profiling directory not found at: {PROFILING_DIR.resolve()}")
```

---

## 2. Out-of-Bounds Virtualenv Symlinking

### The Trap
When `.venv` is missing in the workspace, an agent discovers a virtualenv in a sibling or parent directory (e.g., `~/edgecompute/.venv`) and creates a symlink:
```bash
# ANTI-PATTERN: Reaching outside workspace boundaries
ln -s /home/vaibo/edgecompute/.venv /home/vaibo/auto-edgecompute/.venv
```
### Why It Fails
1. **Violates Workspace Confinement**: Agents are strictly forbidden from reading or linking outside the user's workspace directory.
2. **Breaks Portability & Reproducibility**: The repository ceases to be self-contained; cloning on a new machine or Codespace will fail because the hardcoded external path does not exist.
3. **Hidden Mutation Risk**: Actions in one workspace can mutate dependencies or state in an unrelated workspace.

### The Correct Pattern
Always build a genuine, self-contained virtual environment inside the workspace root:
```bash
# CORRECT: Self-contained workspace virtualenv
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -e clones/<local_pkg>
```
Verify that `sys.executable` and `sys.prefix` are strictly rooted in the current workspace.

---

## 3. Dynamic `sys.path` Tampering

### The Trap
Injecting directories into `sys.path` to force imports when running scripts directly:
```python
# ANTI-PATTERN: Ad-hoc path injection
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```
### Why It Fails
1. **Breaks Module Semantics**: Different scripts end up with different import resolutions depending on invocation order.
2. **Masks Circular or Broken Packages**: Masks packaging issues and prevents standard tools (pytest, linters, IDEs) from resolving symbols.
3. **Violates Root Module Invariance**: Makes scripts non-reproducible when packaged or run from containers.

### The Correct Pattern
Enforce root-level module execution across the entire workspace:
```bash
# CORRECT: Run as module from repository root
./.venv/bin/python -m package.module
```
Use clean, absolute package imports anchored from root: `from package.subpackage import function`.

---

## 4. Context Exhaustion via Massive Diffs

### The Trap
Simultaneously renaming directories, updating script basenames, and modifying every call site across 40 files in a single prompt.
### Why It Fails
1. Produces massive git diffs (>1,000 lines), exhausting LLM context limits and generating truncated tool calls.
2. High probability of syntax errors, broken imports, and undetected regressions.
3. Code review becomes impossible for the user.

### The Correct Pattern
Use the **Minimal-Diff Staged Migration**:
1. Stage 1: Git metadata directory moves (`git mv`) — **0 lines of code changed**.
2. Stage 2: Backward-compatibility forwarding shims (`from contracts.canonical import *`) — **$\le 4$ lines**.
3. Stage 3: Surgical consumer import updates in small, atomic batches ($\le 15$ lines per commit).
4. Stage 4: Run full verification gate after each atomic stage.

---

## 5. Documentation Poisoning & Hallucinated Contexts

### The Trap
Leaving intermediate notes, adversarial audits of superseded drafts, or speculative prompt experiments (e.g., hallucinated Reinforcement Learning specs, old temperature distortion notes) in active markdown files.
### Why It Fails
1. Downstream LLMs read these files during context expansion and hallucinate incorrect architectures.
2. Contradicts canonical paper claims and introduces bias into evaluation narratives.
3. Reviewers and collaborators find contradictory specifications.

### The Correct Pattern
1. **Delete** outright fabricated or irrelevant markdown files.
2. **Archive** superseded milestone logs and pre-fix audit notes into `.archive/docs/` or `.archive/legacy_scrutiny/`.
3. Keep only active, verified **Single Sources of Truth (SSOT)** in `docs/` and sanitize module `README.md` files to match the current codebase.
