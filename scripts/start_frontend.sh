#!/usr/bin/env bash
# ─── TradeIQ Frontend (Development Mode) ──────────────────
# Starts Next.js dev server with hot reload.
# Requires: Node.js 20+, npm, frontend/.env.local configured.
#
# Usage:
#   chmod +x scripts/start_frontend.sh
#   ./scripts/start_frontend.sh
# ───────────────────────────────────────────────────────────

set -euo pipefail

HOST="${TRADEIQ_FRONTEND_HOST:-localhost}"
PORT="${TRADEIQ_FRONTEND_PORT:-3000}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm not found in PATH."
  exit 1
fi

echo "Node: $(command -v node)"
echo "NPM: $(command -v npm)"

cd "${FRONTEND_DIR}"

if [[ ! -d node_modules ]]; then
  echo "Installing frontend dependencies..."
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
fi

npm run dev -- --hostname "${HOST}" --port "${PORT}"
