#!/usr/bin/env bash
# ==============================================================================
# scripts/download_v7_results.sh — Export and Download Evolution v7 Results Bundle
# ==============================================================================
# Role:
#   1. Remote Mode (executed inside Codespace):
#      - Synchronizes docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V7.md with latest token usage.
#      - Exports Top 30 discovered policies with full provenance into output/top30_variants_v7/.
#      - Packages everything into a lightweight compressed tarball:
#        evolution_v7_results_bundle.tar.gz (< 2MB).
#      - Cleans up disposable temporary simulation logs to save disk space.
#      - Displays copy-paste download commands for local retrieval.
#
#   2. Local Pull Mode (executed from local terminal):
#      - Downloads evolution_v7_results_bundle.tar.gz directly from active Codespace
#        via GitHub CLI (`gh codespace cp`) into the local `temp/` folder.
#      - Automatically extracts to `temp/v7_bundle_inspect/` for instant inspection.
#
# Usage:
#   # In Codespace (package & prepare bundle):
#   bash scripts/download_v7_results.sh
#
#   # From Local Machine (pull bundle from Codespace):
#   bash scripts/download_v7_results.sh --pull
#   bash scripts/download_v7_results.sh --pull <codespace-name>
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARBALL_NAME="evolution_v7_results_bundle.tar.gz"
TARBALL_PATH="${WORKSPACE_ROOT}/${TARBALL_NAME}"

# Locate Python binary (workspace virtual environment first)
if [ -x "${WORKSPACE_ROOT}/.venv/bin/python" ]; then
    PYTHON_BIN="${WORKSPACE_ROOT}/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
else
    PYTHON_BIN="python"
fi

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL PULL MODE (triggered with --pull or -p)
# ─────────────────────────────────────────────────────────────────────────────
if [ "${1:-}" = "--pull" ] || [ "${1:-}" = "-p" ]; then
    CODESPACE_ARG="${2:-}"
    LOCAL_DEST="${WORKSPACE_ROOT}/temp"
    mkdir -p "${LOCAL_DEST}"

    echo "========================================================================"
    echo " DOWNLOADING EVOLUTION v7 RESULTS FROM GITHUB CODESPACE"
    echo " Destination: ${LOCAL_DEST}"
    echo "========================================================================"

    if ! command -v gh &>/dev/null; then
        echo "ERROR: GitHub CLI ('gh') is not installed. Install it or use VS Code UI download." >&2
        exit 1
    fi

    # Determine target codespace
    if [ -z "${CODESPACE_ARG}" ]; then
        echo "Detecting active Codespace..."
        ACTIVE_CS=$(gh codespace list --json name,state --jq '.[] | select(.state=="Available") | .name' | head -n 1 || true)
        if [ -z "${ACTIVE_CS}" ]; then
            ACTIVE_CS=$(gh codespace list --json name --jq '.[0].name' || true)
        fi
        if [ -z "${ACTIVE_CS}" ]; then
            echo "ERROR: No active Codespace found. Specify codespace name:" >&2
            echo "  bash scripts/download_v7_results.sh --pull <codespace-name>" >&2
            exit 1
        fi
        CODESPACE_ARG="${ACTIVE_CS}"
    fi

    echo "Connecting to Codespace: ${CODESPACE_ARG}..."

    # Ensure remote bundle is packaged first
    echo "[1/3] Triggering packaging inside remote Codespace..."
    gh codespace ssh -c "${CODESPACE_ARG}" -- "cd /workspaces/edgecompute && bash scripts/download_v7_results.sh" || {
        echo "Notice: Remote execution returned non-zero; attempting direct file transfer..."
    }

    # Copy bundle to local temp/
    echo "[2/3] Transferring ${TARBALL_NAME} to local temp/ directory..."
    gh codespace cp -c "${CODESPACE_ARG}" -e "remote:/workspaces/edgecompute/${TARBALL_NAME}" "${LOCAL_DEST}/${TARBALL_NAME}"

    # Also copy live discovery log
    echo "[3/3] Transferring live EVOLVED_ALGORITHMS_DISCOVERY_LOG_V7.md..."
    gh codespace cp -c "${CODESPACE_ARG}" -e "remote:/workspaces/edgecompute/docs/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V7.md" "${LOCAL_DEST}/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V7.md" || true

    # Extract to inspection folder
    INSPECT_DIR="${LOCAL_DEST}/v7_bundle_inspect"
    mkdir -p "${INSPECT_DIR}"
    tar -zxf "${LOCAL_DEST}/${TARBALL_NAME}" -C "${INSPECT_DIR}" || true

    echo "========================================================================"
    echo " DOWNLOAD COMPLETE!"
    echo " Archive:     ${LOCAL_DEST}/${TARBALL_NAME}"
    echo " Dashboard:   ${LOCAL_DEST}/EVOLVED_ALGORITHMS_DISCOVERY_LOG_V7.md"
    echo " Inspected:   ${INSPECT_DIR}/"
    echo "========================================================================"
    echo ""
    echo "To run full local evaluation of the raw output data across all Step 8.5 baselines:"
    echo "  ./.venv/bin/python scripts/evaluate_v7_raw_results.py --candidate output/evolved_policy_v7.py"
    echo "========================================================================"
    exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# REMOTE PACKAGING MODE (executed inside Codespace)
# ─────────────────────────────────────────────────────────────────────────────
cd "${WORKSPACE_ROOT}"

echo "========================================================================"
echo " PACKAGING EVOLUTION v7 REALISM-AWARE RESULTS"
echo " Workspace: ${WORKSPACE_ROOT}"
echo " Python:    ${PYTHON_BIN}"
echo "========================================================================"

# 1. Update discovery dashboard with latest token consumption and candidate rankings
echo "[1/3] Synchronizing discovery dashboard and token usage..."
"${PYTHON_BIN}" "${WORKSPACE_ROOT}/scripts/run_evolution_v7.py" --update-dashboard || true

# 2. Extract Top 30 policies, generate leaderboard CSV/MD, and create bundle
echo "[2/3] Extracting Top 30 policies and building ${TARBALL_NAME}..."
"${PYTHON_BIN}" "${WORKSPACE_ROOT}/scripts/export_top_variants.py" --top 30 --version 6 --clean-sim-logs

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
    echo "Option 1 (VS Code UI - Recommended & Fastest):"
    echo "  In the VS Code File Explorer panel on the left:"
    echo "  1. Right-click '${TARBALL_NAME}'"
    echo "  2. Select 'Download...'"
    echo "  3. Save to your local machine (e.g., inside temp/)"
    echo ""
    echo "Option 2 (One-line pull from your local terminal):"
    echo "  bash scripts/download_v7_results.sh --pull"
    echo ""
    echo "Option 3 (GitHub CLI direct copy from local terminal):"
    echo "  gh codespace cp -e remote:/workspaces/edgecompute/${TARBALL_NAME} ./temp/"
    echo ""
    echo "Option 4 (Local HTTP Server inside Codespace):"
    echo "  ${PYTHON_BIN} -m http.server 8088"
    echo "  (Open the forwarded port 8088 in your browser and download directly)"
    echo "========================================================================"
else
    echo "ERROR: Failed to generate ${TARBALL_PATH}." >&2
    exit 1
fi
