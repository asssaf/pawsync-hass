#!/usr/bin/env bash
set -euo pipefail

# Project development environment setup script using Mise.
# Sourced by entrypoint.sh on container startup when AGY_STARTUP_HOOK is configured.

echo "========================================="
echo "Running project developer tool setup..."
echo "========================================="

HOST_CACHE_DIR="/home/user/host-cache"
export MISE_DATA_DIR="${HOST_CACHE_DIR}/mise"
export MISE_CACHE_DIR="${HOST_CACHE_DIR}/mise/cache"
export PATH="${HOST_CACHE_DIR}/mise/bin:$PATH"

# 1. Bootstrap Mise if not present
if ! command -v mise &> /dev/null; then
    echo "Mise not found in host-cache. Bootstrapping Mise..."
    mkdir -p "${HOST_CACHE_DIR}/mise/bin"
    MISE_INSTALL_PATH="${HOST_CACHE_DIR}/mise/bin/mise" sh -c "$(curl -fsSL https://mise.run)"
fi
mise trust ~/work/mise.toml

# 2. Install tools declared in mise.toml
if [ -f "/home/user/work/mise.toml" ]; then
    echo "Installing project tools from mise.toml..."
    (cd /home/user/work && mise install)
else
    echo "No mise.toml configuration found in project workspace."
fi

# 3. Export environment variables for the current shell session
eval "$(mise env -s bash)"

# Avoid warning about hardlinks if cache and target are on different filesystems
export UV_LINK_MODE=copy

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

echo "========================================="
echo "Developer tool setup complete!"
echo "========================================="
