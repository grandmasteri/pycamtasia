#!/bin/bash
# Verification gauntlet for a fix branch.
#
# Usage: scripts/verify-fix-branch.sh [--skip-integration]
#
# Runs all quality gates. Returns 0 if all pass, 1 if any fail.
# Fix agents must run this before marking a ROADMAP entry resolved.

set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

SKIP_INTEGRATION=0
if [ "${1:-}" = "--skip-integration" ]; then
    SKIP_INTEGRATION=1
fi

failed=0
check() {
    local name="$1"; shift
    echo -n "  [$name] "
    if "$@" >/tmp/gauntlet_$$.log 2>&1; then
        echo "PASS"
    else
        echo "FAIL"
        echo "--- output ---"
        tail -20 /tmp/gauntlet_$$.log
        echo "---"
        failed=1
    fi
    rm -f /tmp/gauntlet_$$.log
}

echo "=== verification gauntlet ==="
check "ruff" ruff check src/ tests/
check "mypy" python -m mypy src/camtasia
check "unit tests" python -m pytest --tb=line --timeout=15 -q
check "sphinx" bash -c 'cd docs && sphinx-build -b html -q . _build/html'

if [ "$SKIP_INTEGRATION" = "0" ]; then
    echo "  [integration] running (~65 min)..."
    if python -m pytest tests/test_integration_*.py tests/test_camtasia_integration.py -m integration -o "addopts=" --timeout=180 -q >/tmp/gauntlet_integ_$$.log 2>&1; then
        echo "  [integration] PASS"
    else
        echo "  [integration] FAIL"
        tail -20 /tmp/gauntlet_integ_$$.log
        failed=1
    fi
    rm -f /tmp/gauntlet_integ_$$.log
else
    echo "  [integration] SKIPPED (--skip-integration)"
fi

if [ "$failed" = "0" ]; then
    echo ""
    echo "=== ALL CHECKS PASSED ==="
    exit 0
else
    echo ""
    echo "=== GAUNTLET FAILED ==="
    exit 1
fi
