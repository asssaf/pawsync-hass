#!/usr/bin/env bash
set -euo pipefail

echo "==> Updating package lists..."
sudo apt-get update

echo "==> Installing Python 3, pip, and venv..."
sudo apt-get install -y python3 python3-pip python3-venv

echo "==> Setting up virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

echo "==> Upgrading pip inside virtual environment..."
.venv/bin/pip install --upgrade pip

echo "==> Installing development requirements..."
.venv/bin/pip install -r requirements-dev.txt

echo "==> Dev setup completed successfully!"
echo "==> To activate the environment, run: source .venv/bin/activate"
