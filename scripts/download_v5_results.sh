#!/usr/bin/env bash
# ==============================================================================
# scripts/download_v5_results.sh — Export and Download Evolution v5 Results Bundle
# ==============================================================================
# Role:
#   Packages the Top 30 discovered policies, discovery logs, token and code churn
#   summaries, leaderboard CSV & Markdown, and the final evolved policy into a tiny
#   compressed tarball (evolution_v5_results_bundle.tar.gz, ~2MB).
#   Provides copy-paste download commands for local transfer from GitHub Codespaces.
#
# Usage:
#   bash scripts/download_v5_results.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${WORKSPACE_ROOT}/.venv/bin/python"
TARBALL_PATH="${WORKSPACE_ROOT}/evolution_v5_results_bundle.tar.gz"

cd "${WORKSPACE_ROOT}"

echo "========================================================================"
echo " PACKAGING EVOLUTION v5 REALISM-AWARE RESULTS"
echo " Workspace: ${WORKSPACE_ROOT}"
echo " Python:    ${PYTHON_BIN}"
echo "========================================================================"

# 1. Ensure logs are synchronized first
if [ -f "${WORKSPACE_ROOT}/scratch/log_discovery_v5.py" ]; then
    echo "[1/3] Synchronizing discovery logs, token tracking, and code churn..."
    "${PYTHON_BIN}" "${WORKSPACE_ROOT}/scratch/log_discovery_v5.py" || true
fi

# 2. Run export script to extract top 30 policies and build tarball
echo "[2/3] Extracting top 30 policies and building bundle..."
"${PYTHON_BIN}" "${WORKSPACE_ROOT}/scripts/export_top_variants.py" --top 30 --version 5 --clean-sim-logs

# 3. Verify bundle existence and print download instructions
if [ -f "${TARBALL_PATH}" ]; then
    TAR_SIZE=$(du -h "${TARBALL_PATH}" | cut -f1)
    SHA256=$(sha256sum "${TARBALL_PATH}" | cut -d' ' -f1)
    
    echo "========================================================================"
    echo " BUNDLE READY FOR DOWNLOAD!"
    echo " File:    ${TARBALL_PATH}"
    echo " Size:    ${TAR_SIZE}"
    echo " SHA256:  ${SHA256}"
    echo "========================================================================"
    echo ""
    echo "DOWNLOAD INSTRUCTIONS FROM GITHUB CODESPACES:"
    echo "------------------------------------------------------------------------"
    echo "Option 1 (VS Code UI - Recommended):"
    echo "  In the VS Code File Explorer panel on the left, right-click:"
    echo "  -> 'evolution_v5_results_bundle.tar.gz'"
    echo "  -> Select 'Download...'"
    echo ""
    echo "Option 2 (GitHub CLI from your local terminal):"
    echo "  gh codespace cp -e remote:/workspaces/edgecompute/evolution_v5_results_bundle.tar.gz ."
    echo ""
    echo "Option 3 (Quick Local HTTP Server inside Codespace):"
    echo "  ./.venv/bin/python -m http.server 8088"
    echo "  (Open the forwarded port in your browser and download directly)"
    echo "========================================================================"
else
    echo "ERROR: Failed to generate ${TARBALL_PATH}." >&2
    exit 1
fi
