#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
ROOT_DIR="$(dirname "$DIR")"
VENV_DIR="$ROOT_DIR/.venv"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    VENV_PYTHON="$VENV_DIR/Scripts/python"
else
    VENV_PYTHON="$VENV_DIR/bin/python"
fi

if [ ! -x "$VENV_PYTHON" ]; then
    if ! command -v python3 > /dev/null 2>&1; then
        echo "Error: python3 is required but not installed." >&2
        exit 1
    fi
    if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        echo "Error: Python 3.10 or higher is required." >&2
        exit 1
    fi
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Upgrading pip..."
"$VENV_PYTHON" -m pip install --upgrade pip

if [ -f "$ROOT_DIR/pyproject.toml" ]; then
    echo "Installing project and dev requirements from pyproject.toml..."
    # Install the project in editable mode with dev dependencies
    (cd "$ROOT_DIR" && "$VENV_PYTHON" -m pip install -e ".[dev]")
else
    echo "No pyproject.toml found."
fi

echo "Virtual environment is ready. To activate, run:"
echo "source .venv/bin/activate"
