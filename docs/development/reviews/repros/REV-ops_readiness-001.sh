#!/usr/bin/env bash
# REV-ops_readiness-001: Tests CI workflow is failing on main
# Repro: list the last 3 test workflow runs and observe all are 'failure'
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Last 3 Tests workflow runs ==="
gh run list --workflow=tests.yml --limit 3

echo ""
echo "Expected: at least one 'success' status"
echo "Actual: all 3 runs show 'failure'"
echo ""
echo "Root cause: CI runs pytest with --cov but without --cov-fail-under=100."
echo "The coverage.run.omit in pyproject.toml excludes cli.py, frame_stamp.py,"
echo "effects.py, track_media.py, trec_probe.py — but CI still fails."
echo "Investigate the actual failure logs with:"
echo "  gh run view <run-id> --log-failed"
