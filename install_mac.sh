#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

if [[ ! -f "pyproject.toml" ]]; then
  echo "Run this script from the repo root (missing pyproject.toml)." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

export PATH="${HOME}/.local/bin:${PATH}"

echo "Installing Python 3.12 via uv..."
uv python install 3.12

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment..."
  uv venv
fi

echo "Installing Python dependencies..."
uv pip install -r requirements.txt --python .venv

if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing ffmpeg via Homebrew..."
    brew install ffmpeg
  else
    echo ""
    echo "ffmpeg not found."
    echo "Install from https://ffmpeg.org/download.html or install Homebrew first:"
    echo "  https://brew.sh"
  fi
fi

echo ""
echo "Install complete. To start:"
echo "  uv run main.py"
