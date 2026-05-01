#!/usr/bin/env bash
# REV-api_docs-001: MediaBin methods missing from rendered API docs
# The automodule directive targets camtasia.media_bin (the package __init__.py)
# which only re-exports class names, not the full module for autodoc.
# Result: most MediaBin methods (import_folder, find_by_type, delete_unused,
# sorted, etc.) are invisible in the rendered HTML.

cd "$(dirname "$0")/../../../.."

echo "=== Checking rendered HTML for MediaBin methods ==="
for method in import_folder find_by_type delete_unused sorted import_many next_id add_media_entry; do
    count=$(grep -c "$method" docs/_build/html/api/media_bin.html 2>/dev/null || echo 0)
    echo "  $method: $count occurrences (expected >0)"
done

echo ""
echo "=== Root cause: automodule targets package, not submodule ==="
grep 'automodule' docs/api/media_bin.rst
echo "Should be: .. automodule:: camtasia.media_bin.media_bin"
