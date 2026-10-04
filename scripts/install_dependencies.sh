#!/usr/bin/env bash
# ==============================================================================
# scripts/install_dependencies.sh
#
# Role:
#   Full dependency installation and environment setup script for fresh
#   Codespace or remote compute instances.
#
# Actions:
#   1. Creates/verifies Python virtual environment (.venv)
#   2. Installs pip requirements from requirements.txt
#   3. Clones external repositories into clones/ (ContinuumBench, eclypse, openevolve)
#   4. Applies repo patches (telemetry logging, in-flight auto-rotation)
#   5. Synchronizes continuum_ext controllers and workloads into ContinuumBench
#   6. Installs cloned packages in editable mode
#   7. Verifies end-to-end import sanity
#
# Usage:
#   bash scripts/install_dependencies.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "======================================================================"
echo " EDGECOMPUTE: Codespace & Dependency Setup"
echo " Workspace: ${WORKSPACE_ROOT}"
echo "======================================================================"

cd "${WORKSPACE_ROOT}"

# ── 1. Virtual Environment Setup ─────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "[1/6] Creating Python 3 virtual environment in .venv..."
    pip install virtualenv
    virtualenv .venv --python=python3.12
else
    echo "[1/6] Using existing virtual environment in .venv."
fi

VENV_PYTHON="${WORKSPACE_ROOT}/.venv/bin/python"
VENV_PIP="${WORKSPACE_ROOT}/.venv/bin/pip"

echo "[2/6] Upgrading pip, setuptools, wheel..."
"${VENV_PIP}" install --upgrade pip setuptools wheel

# ── 2. Install Standard Dependencies ─────────────────────────────────────────
echo "[3/6] Installing packages from requirements.txt..."
"${VENV_PIP}" install -r requirements.txt

# ── 3. Clone External Repositories (if not present) ──────────────────────────
mkdir -p "${WORKSPACE_ROOT}/clones"
mkdir -p "${WORKSPACE_ROOT}/patches"

echo "[4/6] Checking external repositories in clones/..."

# (a) eclypse
if [ ! -d "${WORKSPACE_ROOT}/clones/eclypse/.git" ]; then
    echo "  -> Cloning eclypse..."
    git clone https://github.com/eclypse-org/eclypse.git "${WORKSPACE_ROOT}/clones/eclypse"
else
    echo "  -> eclypse already present."
fi

# (b) ContinuumBench
if [ ! -d "${WORKSPACE_ROOT}/clones/ContinuumBench/.git" ]; then
    echo "  -> Cloning ContinuumBench..."
    git clone https://github.com/lilanpei/ContinuumBench.git "${WORKSPACE_ROOT}/clones/ContinuumBench"
else
    echo "  -> ContinuumBench already present."
fi

# (c) OpenEvolve
if [ ! -d "${WORKSPACE_ROOT}/clones/openevolve/.git" ]; then
    echo "  -> Cloning OpenEvolve..."
    git clone https://github.com/algorithmicsuperintelligence/openevolve.git "${WORKSPACE_ROOT}/clones/openevolve"
else
    echo "  -> OpenEvolve already present."
fi

# ── 4. Apply Patches & Synchronize Extension Files ───────────────────────────
echo "[5/6] Applying integration patches and extensions..."

# Apply ContinuumBench patch if present
if [ -f "${WORKSPACE_ROOT}/patches/continuum_bench.patch" ]; then
    echo "  -> Applying ContinuumBench workload patch..."
    (cd "${WORKSPACE_ROOT}/clones/ContinuumBench" && git apply "${WORKSPACE_ROOT}/patches/continuum_bench.patch" 2>/dev/null || true)
fi

# Sync conformal controllers and workloads into ContinuumBench
mkdir -p "${WORKSPACE_ROOT}/clones/ContinuumBench/src/continuum_bench/controllers/"
mkdir -p "${WORKSPACE_ROOT}/clones/ContinuumBench/src/continuum_bench/workload/"

cp -fv "${WORKSPACE_ROOT}/src/continuum_ext/controllers/conformal_controllers.py" \
      "${WORKSPACE_ROOT}/clones/ContinuumBench/src/continuum_bench/controllers/"
cp -fv "${WORKSPACE_ROOT}/src/continuum_ext/controllers/extensions_local.py" \
      "${WORKSPACE_ROOT}/clones/ContinuumBench/src/continuum_bench/controllers/"
cp -fv "${WORKSPACE_ROOT}/src/continuum_ext/workload/conformal_workloads.py" \
      "${WORKSPACE_ROOT}/clones/ContinuumBench/src/continuum_bench/workload/"

# Apply OpenEvolve patch (logging hooks + in-flight auto-rotation)
if [ -f "${WORKSPACE_ROOT}/patches/openevolve_telemetry_and_autorotate.patch" ]; then
    echo "  -> Applying OpenEvolve telemetry and auto-rotation patch..."
    (cd "${WORKSPACE_ROOT}/clones/openevolve" && git apply "${WORKSPACE_ROOT}/patches/openevolve_telemetry_and_autorotate.patch" 2>/dev/null || true)
fi

# ── 5. Install Cloned Frameworks in Editable Mode ────────────────────────────
echo "[6/6] Installing cloned frameworks in editable mode..."
"${VENV_PIP}" install -e "${WORKSPACE_ROOT}/clones/eclypse"
"${VENV_PIP}" install -e "${WORKSPACE_ROOT}/clones/ContinuumBench"
"${VENV_PIP}" install -e "${WORKSPACE_ROOT}/clones/openevolve"

# ── 6. Sanity Verification ───────────────────────────────────────────────────
echo "Verifying environment integrity..."
"${VENV_PYTHON}" -c "
import openevolve
import continuum_bench
import eclypse
from continuum_bench.controllers.extensions import build_extension_controller
from continuum_bench.workload import build_stream
import scipy
import pydantic
import openai
print('✓ All core frameworks imported successfully.')
print('✓ ContinuumBench extension hooks and workload generators verified.')
print('✓ Python environment is ready for evolutionary policy search.')
"

echo "======================================================================"
echo " SETUP COMPLETE!"
echo " Next steps on Codespaces:"
echo "   1. Create .env.backup with your Gemini API keys"
echo "   2. Run: ./.venv/bin/python scripts/rotate_api_key.py --auto-find-working"
echo "   3. Launch: ./.venv/bin/python scripts/run_unattended.py --iterations 200"
echo "======================================================================"
