#!/usr/bin/env bash
# ==============================================================================
# scripts/init_codespace_v6.sh — Codespace Initializer for v6
# ==============================================================================
# Role:
#   Initializes a clean GitHub Codespace environment using the authoritative,
#   battle-tested setup from scripts/install_dependencies.sh, followed by
#   API status check and background launch instructions.
#
# Usage:
#   bash scripts/init_codespace_v6.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================================================"
echo " INITIALIZING ENVIRONMENT FOR OPENEVOLVE"
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
echo " CODESPACE INITIALIZATION COMPLETE!"
echo "========================================================================"
