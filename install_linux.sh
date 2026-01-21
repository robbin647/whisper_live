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
  echo "Installing ffmpeg..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y ffmpeg
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y ffmpeg
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm ffmpeg
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y ffmpeg
  else
    echo "No supported package manager found. Installing bundled ffmpeg..."
    mkdir -p "${HOME}/.local/bin"
    curl -L -o /tmp/ffmpeg-6.1-linux-64.zip \
      https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v6.1/ffmpeg-6.1-linux-64.zip
    unzip -o -d "${HOME}/.local/bin" /tmp/ffmpeg-6.1-linux-64.zip
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
fi

echo ""
echo "Install complete. To start:"
echo "  uv run main.py"
