#!/usr/bin/env bash
# Repro for REV-packaging-004: sdist includes ~10MB of test fixtures
# Run from project root: bash docs/development/reviews/repros/REV-packaging-004.sh

set -euo pipefail

echo "=== REV-packaging-004: sdist fixture bloat ==="
echo ""

echo "1. Fixture sizes on disk:"
ls -lh tests/fixtures/
echo ""

echo "2. Total fixture size:"
du -sh tests/fixtures/
echo ""

echo "3. Fixtures in sdist:"
tar tzf dist/pycamtasia-*.tar.gz | grep fixtures
echo ""

echo "4. sdist total size:"
ls -lh dist/pycamtasia-*.tar.gz
echo ""

echo "RESULT: Large binary fixtures (especially empty.wav at 5MB) are included"
echo "in the sdist, bloating the PyPI upload unnecessarily."
