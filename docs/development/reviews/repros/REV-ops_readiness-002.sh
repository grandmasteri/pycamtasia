#!/usr/bin/env bash
# REV-ops_readiness-002: CI does not enforce --cov-fail-under=100
# The pyproject.toml declares fail_under = 100 under [tool.coverage.report],
# but the CI workflow runs:
#   pytest tests/ --cov=camtasia --cov-report=xml --cov-report=term-missing
# without --cov-fail-under=100 or --cov-report=term (which triggers the check).
#
# The fail_under setting in pyproject.toml only takes effect when pytest-cov
# generates a report that triggers the coverage.report module. The CI command
# uses --cov-report=xml and --cov-report=term-missing but does NOT include
# a bare --cov-report=term or explicit --cov-fail-under flag.
#
# Actually, pytest-cov DOES read [tool.coverage.report].fail_under when
# --cov-report=term-missing is used. So the gate should work.
# The real question is: why are the CI runs failing?

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== CI pytest command ==="
grep 'pytest' .github/workflows/tests.yml

echo ""
echo "=== pyproject.toml coverage config ==="
grep -A3 'coverage.report' pyproject.toml

echo ""
echo "Note: --cov-report=term-missing does trigger fail_under from pyproject.toml."
echo "The CI failures may be from actual test failures, not coverage."
