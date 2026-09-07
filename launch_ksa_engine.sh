#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
if ! python -c "import pygame" >/dev/null 2>&1; then
	python -m pip install -r requirements-dev.txt
fi
exec python -m ksa_engine --editor
