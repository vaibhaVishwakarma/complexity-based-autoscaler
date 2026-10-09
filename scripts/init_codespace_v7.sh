#!/usr/bin/env bash
# ==============================================================================
# scripts/init_codespace_v7.sh — Codespace Initializer for v7
# ==============================================================================
# Role:
#   Initializes a clean GitHub Codespace environment using the authoritative,
#   battle-tested setup from scripts/install_dependencies.sh, followed by
#   v7 API status check and background launch instructions.
#
# Usage:
#   bash scripts/init_codespace_v7.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================================================"
echo " INITIALIZING ENVIRONMENT FOR OPENEVOLVE v7"
echo " Running authoritative environment setup: scripts/install_dependencies.sh"
echo "========================================================================"

bash "${SCRIPT_DIR}/install_dependencies.sh"

echo ""
echo "========================================================================"
echo " API KEY HEALTH CHECK"
echo "========================================================================"
if [ -f "${WORKSPACE_ROOT}/.env" ]; then
    "${WORKSPACE_ROOT}/.venv/bin/python" "${WORKSPACE_ROOT}/scripts/rotate_api_key.py" --status || true
else
    echo "WARNING: .env file not found."
    echo "Create .env with: echo 'GEMINI_API_KEY=your_key_here' > .env"
fi

echo ""
echo "========================================================================"
echo " OPENEVOLVE v7 SETUP COMPLETE!"
echo "========================================================================"
echo "To launch the unattended v7 evolutionary search in the background:"
echo ""
echo "  nohup ./.venv/bin/python scripts/run_unattended_v7.py --reset --iterations 50 > evaluation_run_v7.log 2>&1 &"
echo ""
echo "To monitor real-time progress and token consumption:"
echo "  tail -f evaluation_run_v7.log"
echo "  cat docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V7.md"
echo "========================================================================"
