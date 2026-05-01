#!/usr/bin/env bash
# REV-api_docs-002: operations.media_ops referenced in decision matrix but
# has no automodule directive — its public functions are undocumented.

cd "$(dirname "$0")/../../../.."

echo "=== media_ops referenced in decision matrix ==="
grep 'media_ops' docs/api/operations.rst

echo ""
echo "=== But no automodule directive ==="
grep 'automodule.*media_ops' docs/api/operations.rst || echo "MISSING: no automodule for media_ops"

echo ""
echo "=== Public functions in media_ops ==="
python3 -c "
import ast
with open('src/camtasia/operations/media_ops.py') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
        print(f'  {node.name} (line {node.lineno})')
"
