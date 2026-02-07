#!/bin/bash
# TradeIQ Environment Setup Script
# Creates conda environment and installs dependencies

set -e  # Exit on error

echo "=========================================="
echo "TradeIQ Environment Setup"
echo "=========================================="

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    echo "Please install conda first: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Environment name
ENV_NAME="tradeiq"

# Check if environment already exists
if conda env list | grep -q "^${ENV_NAME} "; then
    echo "⚠️  Environment '${ENV_NAME}' already exists"
    read -p "Do you want to remove it and create a new one? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda env remove -n ${ENV_NAME} -y
    else
        echo "Using existing environment..."
        conda activate ${ENV_NAME}
        echo "✅ Environment activated"
        exit 0
    fi
fi

# Create conda environment from environment.yml
echo ""
echo "📦 Creating conda environment '${ENV_NAME}'..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
conda env create -f "${SCRIPT_DIR}/environment.yml"

# Activate environment
echo ""
echo "🔌 Activating environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ${ENV_NAME}

# Verify Python version
PYTHON_VERSION=$(python --version)
echo "✅ Python version: ${PYTHON_VERSION}"

# Verify Django installation
if python -c "import django; print(django.get_version())" 2>/dev/null; then
    DJANGO_VERSION=$(python -c "import django; print(django.get_version())")
    echo "✅ Django version: ${DJANGO_VERSION}"
else
    echo "❌ Error: Django not installed correctly"
    exit 1
fi

# Verify other key packages
echo ""
echo "🔍 Verifying key packages..."
python -c "import rest_framework; print('✅ DRF installed')" || echo "❌ DRF not found"
python -c "import channels; print('✅ Channels installed')" || echo "❌ Channels not found"
python -c "import openai; print('✅ OpenAI SDK installed')" || echo "❌ OpenAI SDK not found"
python -c "import atproto; print('✅ atproto installed')" || echo "❌ atproto not found"
python -c "import psycopg2; print('✅ psycopg2 installed')" || echo "❌ psycopg2 not found"

# Verify Django can load
echo ""
echo "🔍 Verifying Django configuration..."
if python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradeiq.settings'); import django; django.setup(); print('✅ Django settings loaded')" 2>/dev/null; then
    echo "✅ Django configuration OK"
else
    echo "⚠️  Django settings check skipped (run from backend/ directory)"
fi

echo ""
echo "=========================================="
echo "✅ Environment setup complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  conda activate ${ENV_NAME}"
echo ""
echo "To deactivate, run:"
echo "  conda deactivate"
echo ""
