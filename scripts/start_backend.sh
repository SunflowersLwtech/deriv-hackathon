#!/usr/bin/env bash

set -euo pipefail

ENV_NAME="${TRADEIQ_CONDA_ENV:-tradeiq}"
HOST="${TRADEIQ_HOST:-127.0.0.1}"
PORT="${TRADEIQ_PORT:-8000}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda not found in PATH."
  exit 1
fi

# Initialize conda for this non-interactive shell.
if conda shell.bash hook >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
else
  CONDA_BASE="$(conda info --base)"
  # shellcheck source=/dev/null
  source "${CONDA_BASE}/etc/profile.d/conda.sh"
fi

conda activate "${ENV_NAME}"

if [[ "${CONDA_DEFAULT_ENV:-}" != "${ENV_NAME}" ]]; then
  echo "Error: failed to activate conda env '${ENV_NAME}'. Current: '${CONDA_DEFAULT_ENV:-none}'"
  exit 1
fi

echo "Conda env active: ${CONDA_DEFAULT_ENV}"
echo "Python: $(command -v python)"

cd "${BACKEND_DIR}"

python manage.py runserver "${HOST}:${PORT}"
