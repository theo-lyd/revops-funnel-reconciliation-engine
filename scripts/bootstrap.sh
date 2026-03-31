#!/usr/bin/env bash
set -euo pipefail

python -m pip install -r requirements/base.txt -r requirements/dev.txt
pre-commit install
mkdir -p data/warehouse logs

echo "Bootstrap complete."
