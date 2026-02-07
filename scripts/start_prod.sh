#!/usr/bin/env bash
# ─── TradeIQ Production Start (No Docker) ─────────────────
# Starts both backend and frontend in production mode.
# Requires: conda env 'tradeiq', npm, .env configured.
#
# Usage:
#   chmod +x scripts/start_prod.sh
#   ./scripts/start_prod.sh
# ───────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
ENV_NAME="${TRADEIQ_CONDA_ENV:-tradeiq}"

BACKEND_HOST="${TRADEIQ_HOST:-0.0.0.0}"
BACKEND_PORT="${TRADEIQ_PORT:-8000}"
FRONTEND_HOST="${TRADEIQ_FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${TRADEIQ_FRONTEND_PORT:-3000}"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo -e "${CYAN}  TradeIQ Production Deployment${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"

# ── Check .env ──
if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
  echo -e "${RED}Error: .env file not found. Copy from .env.example:${NC}"
  echo -e "  cp .env.example .env"
  exit 1
fi

# ── Init conda ──
if ! command -v conda >/dev/null 2>&1; then
  echo -e "${RED}Error: conda not found${NC}"; exit 1
fi

if conda shell.bash hook >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
else
  CONDA_BASE="$(conda info --base)"
  source "${CONDA_BASE}/etc/profile.d/conda.sh"
fi

conda activate "${ENV_NAME}"
echo -e "${GREEN}✓ Conda env: ${CONDA_DEFAULT_ENV}${NC}"

# ── Backend: migrate + collect static ──
echo -e "\n${CYAN}[1/3] Preparing backend...${NC}"
cd "${BACKEND_DIR}"

python manage.py migrate --noinput 2>/dev/null || true
python manage.py collectstatic --noinput 2>/dev/null || true

echo -e "${GREEN}✓ Backend ready${NC}"

# ── Frontend: build ──
echo -e "\n${CYAN}[2/3] Building frontend...${NC}"
cd "${FRONTEND_DIR}"

if [[ ! -d node_modules ]]; then
  npm ci
fi

# Set standalone output for production
NEXT_OUTPUT=standalone npm run build
echo -e "${GREEN}✓ Frontend built${NC}"

# ── Start both services ──
echo -e "\n${CYAN}[3/3] Starting services...${NC}"

# Trap to kill both on exit
cleanup() {
  echo -e "\n${CYAN}Shutting down...${NC}"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  echo -e "${GREEN}✓ All services stopped${NC}"
}
trap cleanup EXIT INT TERM

# Start backend (daphne for ASGI + WebSocket)
cd "${BACKEND_DIR}"
daphne -b "${BACKEND_HOST}" -p "${BACKEND_PORT}" tradeiq.asgi:application &
BACKEND_PID=$!

# Start frontend (Next.js production)
cd "${FRONTEND_DIR}"
npm run start -- --hostname "${FRONTEND_HOST}" --port "${FRONTEND_PORT}" &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  TradeIQ is running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "  Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo -e "  Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo -e "  API:      http://${BACKEND_HOST}:${BACKEND_PORT}/api/"
echo -e "  Pipeline: http://${FRONTEND_HOST}:${FRONTEND_PORT}/pipeline"
echo -e ""
echo -e "  Press Ctrl+C to stop all services."
echo ""

# Wait for either to exit
wait -n $BACKEND_PID $FRONTEND_PID
