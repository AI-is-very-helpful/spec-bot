#!/bin/bash
# Run Azure Functions with venv activated

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv (for development tools, etc.)
source .venv/bin/activate

# Run Azure Functions
# Note: Azure Functions Core Tools uses system Python
# Use venv for development tools (pytest, mypy, etc.)
exec func start
