---
name: scientific-repo-refactor
description: "Systematically refactor scientific and ML codebases without regressions, context exhaustion, or broken import paths. Enforces root-module execution, strictly confined local virtual environments, minimal-diff staged migrations, zero silent fallbacks, context sanitization, and verification gates."
---

# Scientific Repository Refactor

A rigorous, zero-regression protocol for refactoring scientific, ML, and systems codebases. This skill codifies lessons learned from large-scale multi-stage repository reorganizations, preventing LLM context exhaustion, import breakage, workspace confinement violations, and documentation poisoning.

---

## Core Mandates

1. **Virtual Environment Confinement**: Never create symlinks pointing outside the workspace (e.g. to sibling directories). All virtual environments must be strictly local and self-contained at `./.venv`.
2. **Root-Module Execution Mandate**: Never inject paths dynamically (`sys.path.insert`, `sys.path.append`). Execute all tools and evaluation scripts via `./.venv/bin/python -m <package>.<module>` anchored from the repository root.
3. **Advisor-First Confirmation Gating**: Never execute unilateral restructuring or delete files without explicit user consent. Present proposals in structured tables and await user confirmation.
4. **Minimal-Diff Staged Migration**: Never refactor an entire codebase in a single sprawling diff. Limit atomic migration batches to $\le 15$ lines of changes per commit using `git mv` metadata moves and temporary contract shims.
5. **Zero Silent Fallbacks**: Never implement fallback ternary expressions (e.g., `Path("new") if Path("new").is_dir() else Path("old")`). Canonical paths must bind unconditionally and fail fast with explicit exceptions.
6. **Documentation Hygiene & Sanitization**: Intermediate notes, exploratory audits, and superseded logs poison downstream LLM context. Delete fabricated notes and archive superseded documents to `.archive/docs/`.

---

## Step-by-Step Refactoring Workflow

### Step 1: Preflight Hygiene & Environment Audit
- Verify that `./.venv` exists and its interpreter (`./.venv/bin/python`) is strictly confined within the workspace root.
- Execute the automated hygiene scanner:
  ```bash
  ./.venv/bin/python .agents/skills/scientific-repo-refactor/scripts/audit_refactor_hygiene.py
  ```
- **Done when:** The hygiene audit confirms zero out-of-bounds symlinks, zero dynamic `sys.path` tampering, and zero unresolved legacy dependencies.

### Step 2: Codebase Inventory & Advisor-First Confirmation Gating
- Catalog all candidate scripts, configurations, and artifacts into a structured classification table:
  - **Active / Canonical**: Core pipeline scripts to be preserved and relocated.
  - **Dead / Superseded**: Obsolete experiments to be archived.
  - **Tests**: Ad-hoc test scripts to be consolidated into `tests/`.
- Present the classification table and proposed destination paths to the user.
- Detail trade-offs, potential import disruptions, and verification plans.
- **Done when:** The user explicitly approves the proposed restructuring plan.

### Step 3: Archive Dead Code & Consolidate Tests
- Move superseded experiments, exploratory scripts, and legacy scratchpads to `.archive/` using `git mv`.
- Consolidate all standalone test scripts into `tests/` following standard pytest conventions (`test_*.py`).
- Run `./.venv/bin/pytest tests/` to establish the baseline test pass rate.
- **Done when:** Dead files are safely moved to `.archive/`, all tests are under `tests/`, and pytest passes cleanly.

### Step 4: Minimal-Diff Staged Migration
Follow the detailed protocol in [Minimal-Diff Migration Protocol](file://references/minimal-diff-migration.md):
1. **Preserve Script Basenames**: Keep existing filenames (e.g., `download_datasets.py`) to preserve runbooks and developer muscle memory.
2. **Git Metadata Directory Move**: Rename directories using `git mv <legacy_dir> <canonical_dir>` (0 lines of code churn).
3. **Deploy Typed Contract Shims**: In `contracts/`, create temporary re-export shims so legacy import paths forward directly to canonical contracts:
   ```python
   # contracts/legacy.py
   from contracts.canonical import *  # noqa: F401, F403
   ```
4. **Surgical Consumer Updates**: Update consumer imports in small, atomic batches ($\le 15$ lines per commit). Commit after each verified module update.
- **Done when:** All downstream scripts reference canonical package paths, and intermediate tests continue to pass.

### Step 5: Eliminate Silent Fallbacks & Deprecation Cleanup
Review anti-patterns in [Refactoring Anti-Patterns & Pitfalls](file://references/refactoring-anti-patterns.md):
- Search the codebase for ternary path fallbacks:
  ```bash
  grep -rn "if.*is_dir().*else" .
  ```
- Replace any ternary fallback with strict, fail-fast canonical binding:
  ```python
  CANONICAL_DIR = Path("canonical_name")
  if not CANONICAL_DIR.is_dir():
      raise FileNotFoundError(f"Missing required directory: {CANONICAL_DIR.resolve()}")
  ```
- Remove temporary contract shims and transitional directory symlinks once all consumers are updated.
- Update `.gitignore` to ensure new runtime output directories are ignored.
- **Done when:** Zero silent fallback patterns exist in active code and transitional symlinks/shims are removed.

### Step 6: Documentation Sanitization & Context Hygiene
- Audit the repository root and `docs/` for intermediate notes, adversarial scrutiny files, and superseded draft logs.
- Remove completely obsolete or hallucinated scrutiny documents.
- Archive superseded historical milestone logs into `.archive/docs/`.
- Ensure module `README.md` files accurately describe the new canonical directory layout and module execution patterns.
- **Done when:** Only authoritative Single Sources of Truth (SSOT) remain in active documentation directories.

### Step 7: End-to-End Verification Gate
- Run the full verification suite in sequence:
  1. Unit tests: `./.venv/bin/pytest tests/`
  2. Core pipeline module tests: `./.venv/bin/python -m <module>.<entrypoint> --help`
  3. Figure and report generation scripts.
  4. End-to-end smoke simulations across all seeds.
  5. Final hygiene audit:
     ```bash
     ./.venv/bin/python .agents/skills/scientific-repo-refactor/scripts/audit_refactor_hygiene.py
     ```
- Review `git status` and `git diff` to ensure zero unintended changes or leftover untracked artifacts.
- **Done when:** All verification gates pass cleanly and changes are committed to git.

---

## Key References & Tools

- [Refactoring Anti-Patterns & Pitfalls](file://references/refactoring-anti-patterns.md): In-depth examination of silent fallbacks, out-of-bounds venvs, path tampering, and documentation poisoning.
- [Minimal-Diff Migration Protocol](file://references/minimal-diff-migration.md): Staged execution flow, contract shims, and output manifest handling.
- [Hygiene Audit Script](file://scripts/audit_refactor_hygiene.py): Standalone CLI validator for workspace confinement, `sys.path`, and silent fallbacks.
