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



# This automatically creates and/or sources the .venv directory thanks to python.uv_venv_auto settings in mise.toml

echo "==> Installing development requirements..."
mise run setup

echo "==> Dev setup completed successfully!"
echo "==> To activate the environment, run: source .venv/bin/activate"

echo "========================================="
echo "Developer tool setup complete!"
echo "========================================="
