"""REV-test_gaps-005: history.py 'Malformed patch operation' error path not tested.

Line 199 raises ValueError for a malformed patch operation (missing 'op' key),
but no test triggers this specific path. Only 'Malformed history file' (line 211)
is tested.
"""
import json
import pytest

from camtasia.history import History


def test_malformed_patch_operation_raises(tmp_path):
    """A history entry with a patch missing the 'op' key should raise ValueError."""
    history_file = tmp_path / "history.json"
    # Write a history file with a malformed patch (missing 'op')
    history_data = [
        {
            "description": "bad patch",
            "forward": [{"path": "/foo"}],  # missing 'op' key
            "reverse": [{"op": "remove", "path": "/foo"}],
        }
    ]
    history_file.write_text(json.dumps(history_data))
    with pytest.raises(ValueError, match="Malformed patch operation"):
        History.load(history_file)
