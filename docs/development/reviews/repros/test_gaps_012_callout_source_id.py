"""REV-test_gaps-012: Callout.source_id raises TypeError but is not tested.

callout.py line 103 raises TypeError('Callout clips do not have a source ID').
No test verifies this behavior.
"""
import pytest

from camtasia.timeline.clips.callout import Callout


def test_callout_source_id_raises_type_error():
    """Accessing source_id on a Callout should raise TypeError."""
    data = {
        "_type": "Callout",
        "id": 1,
        "start": 0,
        "duration": 705600000,
        "mediaStart": 0,
        "mediaDuration": 705600000,
        "scalar": 1,
        "effects": [],
        "parameters": {},
        "attributes": {"style": {"data": ""}},
    }
    clip = Callout(data)
    with pytest.raises(TypeError, match="Callout clips do not have a source ID"):
        _ = clip.source_id
