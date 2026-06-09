#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$DIR")"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip

if [ -f "$ROOT_DIR/pyproject.toml" ]; then
    echo "Installing project and dev requirements from pyproject.toml..."
    # Install the project in editable mode with dev dependencies
    pip install -e "$ROOT_DIR[dev]"
else
    echo "No pyproject.toml found."
fi

echo "Virtual environment is ready. To activate, run:"
echo "source .venv/bin/activate"
