#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.9 or newer was not found. Install Python and try again." >&2
    exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_BIN" -m venv .venv
fi

echo "Installing dependencies from requirements.txt..."
# shellcheck disable=SC1091
. ".venv/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo
echo "Installation complete."
echo "Start the app with: ./VideOCRplus.sh"
