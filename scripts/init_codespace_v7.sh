#!/usr/bin/env bash
# ==============================================================================
# scripts/init_codespace_v7.sh — Complete Fresh Codespace Initializer for v7
# ==============================================================================
# Role:
#   Sets up a clean GitHub Codespace or Linux compute instance for running
#   the OpenEvolve v7 Realism-Aware evolutionary autoscaler synthesis.
#
# Directives:
#   1. Creates/verifies dedicated workspace venv at ./.venv (Python >= 3.10).
#   2. Installs core dependencies and editable workspace clones (eclypse, ContinuumBench, openevolve).
#   3. Checks .env and validates Gemini API key status via rotate_api_key.py.
#   4. Makes all scripts executable.
#   5. Verifies end-to-end module imports before launch.
#
# Usage:
#   bash scripts/init_codespace_v7.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${WORKSPACE_ROOT}/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
PIP_BIN="${VENV_DIR}/bin/pip"

cd "${WORKSPACE_ROOT}"

echo "========================================================================"
echo " INITIALIZING CODESPACE ENVIRONMENT FOR EVOLUTION v7"
echo " Workspace: ${WORKSPACE_ROOT}"
echo "========================================================================"

# 1. Verify Host Python Version (Requires Python >= 3.10)
HOST_PYTHON=""
if command -v python3.12 &>/dev/null; then
    HOST_PYTHON="python3.12"
elif command -v python3.11 &>/dev/null; then
    HOST_PYTHON="python3.11"
elif command -v python3.10 &>/dev/null; then
    HOST_PYTHON="python3.10"
elif command -v python3 &>/dev/null; then
    HOST_PYTHON="python3"
else
    echo "ERROR: python3 not found. Please install Python 3.10+." >&2
    exit 1
fi

echo "[1/6] Using host Python: $(${HOST_PYTHON} --version)"

# 2. Create or Verify Virtual Environment at ./.venv
if [ ! -d "${VENV_DIR}" ] || [ ! -x "${PYTHON_BIN}" ]; then
    echo "[2/6] Creating workspace virtual environment at ./.venv..."
    ${HOST_PYTHON} -m venv "${VENV_DIR}"
else
    echo "[2/6] Existing virtual environment detected at ./.venv."
fi

# 3. Upgrade pip and setuptools
echo "[3/6] Upgrading pip and build tools..."
"${PIP_BIN}" install --upgrade pip setuptools wheel --quiet

# 4. Install Base Requirements
echo "[4/6] Installing core scientific and LLM libraries..."
"${PIP_BIN}" install --quiet \
    numpy \
    pandas \
    scipy \
    pyyaml \
    pydantic \
    openai \
    matplotlib \
    pytest

# 5. Install Cloned Submodules in Editable Mode
echo "[5/6] Linking cloned frameworks (eclypse, ContinuumBench, openevolve)..."
if [ -d "${WORKSPACE_ROOT}/clones/eclypse" ]; then
    "${PIP_BIN}" install -e "${WORKSPACE_ROOT}/clones/eclypse" --no-deps --quiet
fi

if [ -d "${WORKSPACE_ROOT}/clones/ContinuumBench" ]; then
    "${PIP_BIN}" install -e "${WORKSPACE_ROOT}/clones/ContinuumBench" --no-deps --quiet
fi

if [ -d "${WORKSPACE_ROOT}/clones/openevolve" ]; then
    "${PIP_BIN}" install -e "${WORKSPACE_ROOT}/clones/openevolve" --quiet
fi

# Link local workspace package if setup.py or pyproject.toml exists
if [ -f "${WORKSPACE_ROOT}/setup.py" ] || [ -f "${WORKSPACE_ROOT}/pyproject.toml" ]; then
    "${PIP_BIN}" install -e "${WORKSPACE_ROOT}" --no-deps --quiet || true
fi

# 6. Make All Scripts Executable
chmod +x "${WORKSPACE_ROOT}/scripts/"*.sh "${WORKSPACE_ROOT}/scripts/"*.py 2>/dev/null || true

# 7. Verification of Core Imports
echo "[6/6] Verifying environment and framework contracts..."
"${PYTHON_BIN}" -c "
import continuum_bench
import eclypse
import openevolve
import pydantic
import yaml
import numpy
import pandas
print('  -> All core modules successfully imported into .venv!')
"

# 8. Check API Key Status
echo ""
echo "========================================================================"
echo " API KEY HEALTH CHECK"
echo "========================================================================"
if [ -f "${WORKSPACE_ROOT}/.env" ]; then
    "${PYTHON_BIN}" "${WORKSPACE_ROOT}/scripts/rotate_api_key.py" --status || true
else
    echo "WARNING: .env file not found."
    echo "Create .env with: echo 'GEMINI_API_KEY=your_key_here' > .env"
fi

echo ""
echo "========================================================================"
echo " CODESPACE INITIALIZATION COMPLETE!"
echo "========================================================================"
echo "To launch the unattended v7 evolutionary search in the background:"
echo ""
echo "  nohup ./.venv/bin/python scripts/run_unattended_v7.py --reset --iterations 100 > evaluation_run_v7.log 2>&1 &"
echo ""
echo "To monitor real-time progress and token consumption:"
echo "  tail -f evaluation_run_v7.log"
echo "  cat docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V7.md"
echo "========================================================================"
