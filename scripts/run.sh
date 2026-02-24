#!/usr/bin/env bash
# AgentFlow Framework - Run Script
set -euo pipefail

HOST=${AGENTFLOW_HOST:-0.0.0.0}
PORT=${AGENTFLOW_PORT:-8000}
WORKERS=${AGENTFLOW_WORKERS:-1}
RELOAD=${AGENTFLOW_RELOAD:-true}

echo "======================================"
echo "  AgentFlow Framework"
echo "  Starting API server..."
echo "======================================"
echo "  Host:    $HOST"
echo "  Port:    $PORT"
echo "  Reload:  $RELOAD"
echo "======================================"

# Activate venv if exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Check .env exists
if [ ! -f ".env" ]; then
  echo "WARNING: .env file not found. Run scripts/setup.sh first."
fi

# Run the FastAPI app
if [ "$RELOAD" = "true" ]; then
  uvicorn agentflow.api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload \
    --log-level info
else
  uvicorn agentflow.api.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level info
fi
