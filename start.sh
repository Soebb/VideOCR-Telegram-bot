#!/usr/bin/env bash
# Install the system libraries required by PaddleOCR's bundled OpenCV,
# install the Python dependencies, and start the Telegram bot.
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

# apt requires root. Use sudo when available (for local/non-root environments).
if [[ "$(id -u)" -eq 0 ]]; then
    SUDO=()
elif command -v sudo >/dev/null 2>&1; then
    SUDO=(sudo)
else
    echo "ERROR: Installing libGL requires root privileges (or sudo)." >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "[setup] Installing system libraries required by PaddleOCR/OpenCV..."
"${SUDO[@]}" apt-get update
"${SUDO[@]}" apt-get install -y --no-install-recommends libgl1 libglib2.0-0
"${SUDO[@]}" rm -rf /var/lib/apt/lists/*

echo "[setup] Installing Python requirements..."
python -m pip install -r requirements.txt

echo "[start] Launching Telegram bot..."
exec python bot.py
