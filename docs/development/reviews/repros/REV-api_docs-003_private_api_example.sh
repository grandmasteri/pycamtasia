#!/usr/bin/env bash
# REV-api_docs-003: operations.rst example uses project._data (private attribute)
# and has missing import (uses camtasia.load_project without importing camtasia)

cd "$(dirname "$0")/../../../.."

echo "=== Private API usage in example ==="
grep -n '_data' docs/api/operations.rst

echo ""
echo "=== Missing import — uses camtasia.load_project without 'import camtasia' ==="
# The example imports from camtasia.operations.speed but uses camtasia.load_project
grep -A8 'code-block:: python' docs/api/operations.rst | head -20
