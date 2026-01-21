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

# Ensure common package manager paths are available (Homebrew varies by arch).
export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"

machine="$(uname -m)"
if [[ "${machine}" == "arm64" ]]; then
  # If running under Rosetta, uv will install an x86_64 Python, which can force
  # building packages from source (e.g. llvmlite) and require extra toolchains.
  if [[ "$(sysctl -n sysctl.proc_translated 2>/dev/null || echo 0)" == "1" ]]; then
    echo "Detected Rosetta translation on Apple Silicon." >&2
    echo "Please re-run in a native arm64 shell so uv installs arm64 Python and can use prebuilt wheels:" >&2
    echo "  arch -arm64 zsh -lc './install_mac.sh'" >&2
    echo "" >&2
    echo "If you're using Terminal.app: Get Info on Terminal and uncheck 'Open using Rosetta'." >&2
    exit 1
  fi
fi

echo "Installing Python 3.12 via uv..."
if [[ "${machine}" == "arm64" ]]; then
  # Force native Apple Silicon Python to avoid unnecessary source builds.
  uv python install cpython-3.12-macos-aarch64-none
else
  uv python install 3.12
fi

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment..."
  uv venv
fi

echo "Installing Python dependencies..."
# If llvmlite has to build from source (common on Intel macOS or mismatched arch),
# it expects a `cmake` executable to be available on PATH. Disabling build isolation
# for llvmlite lets it see tools installed into the project environment (including
# the PyPI `cmake` package), avoiding "cmake not found" build failures.
uv sync --python .venv --no-build-isolation-package llvmlite

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
