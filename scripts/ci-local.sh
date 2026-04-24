#!/usr/bin/env bash
# Run the full CI pipeline locally: ruff + mypy + tests with coverage.
# Usage: ./scripts/ci-local.sh
set -euo pipefail

echo "=== ruff ==="
ruff check src/ tests/

echo "=== mypy ==="
mypy src/camtasia/

echo "=== tests + coverage ==="
python -m pytest tests/ -n0 --cov=camtasia --cov-report=term-missing -q

echo "=== ALL PASSED ==="
