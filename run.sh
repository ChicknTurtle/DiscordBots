#!/bin/sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
"$VENV_PYTHON" "$SCRIPT_DIR/main.py"