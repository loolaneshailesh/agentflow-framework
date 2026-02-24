#!/usr/bin/env bash
# AgentFlow Framework - Setup Script
set -euo pipefail

echo "======================================"
echo "  AgentFlow Framework - Setup"
echo "======================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

REQUIRED_MINOR=10
ACTUAL_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$ACTUAL_MINOR" -lt "$REQUIRED_MINOR" ]; then
  echo "ERROR: Python 3.10+ required"
  exit 1
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy .env if not exists
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo ">>> .env file created from .env.example"
  echo ">>> IMPORTANT: Edit .env and add your API key!"
  echo ">>> The framework will auto-detect your LLM provider."
fi

echo ""
echo "======================================"
echo "  Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env and set your API key (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)"
echo "  2. Run: source .venv/bin/activate"
echo "  3. Start server: bash scripts/run.sh"
echo "  4. Open browser: http://localhost:8000"
echo "  5. Run demo: python demos/finance_ap_demo.py"
echo ""
