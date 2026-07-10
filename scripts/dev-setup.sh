#!/usr/bin/env bash
set -euo pipefail

# Avoid warning about hardlinks if cache and target are on different filesystems
export UV_LINK_MODE=copy

# Check if uv is installed
if ! command -v uv &> /dev/null && [ ! -f "$HOME/.local/bin/uv" ]; then
    echo "==> Installing uv (modern Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Ensure uv is in PATH for this script session
if [ -f "$HOME/.local/bin/uv" ]; then
    export PATH="$HOME/.local/bin:$PATH"
fi

if [ -d ".venv" ]; then
    # Check the Python version of the existing virtual environment
    VENV_PYTHON_VERSION=$(".venv/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "")
    if [ "$VENV_PYTHON_VERSION" != "3.14" ]; then
        echo "==> Existing .venv has Python $VENV_PYTHON_VERSION. Re-creating with Python 3.14..."
        uv venv --python 3.14 --clear .venv
    else
        echo "==> Virtual environment (.venv) already exists with Python 3.14."
    fi
else
    echo "==> Creating virtual environment (.venv) with Python 3.14..."
    uv venv --python 3.14 .venv
fi

echo "==> Installing development requirements..."
uv pip install -r requirements-dev.txt

echo "==> Dev setup completed successfully!"
echo "==> To activate the environment, run: source .venv/bin/activate"
