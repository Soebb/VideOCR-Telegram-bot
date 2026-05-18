#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    echo "Virtual environment not found. Running install.sh first..."
    sh "./install.sh"
fi

export PYTHONUTF8=1
exec ".venv/bin/python" "./cli.py" "$@"
