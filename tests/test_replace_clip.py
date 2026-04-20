"""Tests for Track.replace_clip() and BaseClip.clone()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": [], "transitions": []}
    return Track(attrs, data)


class TestReplaceClip:
    def test_replace_clip_preserves_position(self):
        track = _make_track()
        original = track.add_callout("A", 0, 5)
        start = original.start

        new_data = {"_type": "Callout", "duration": 10, "start": 999,
                    "mediaStart": 0, "mediaDuration": 10}
        result = track.replace_clip(original.id, new_data)

        assert result.start == start

    def test_replace_clip_new_id(self):
        track = _make_track()
        original = track.add_callout("A", 0, 5)
        old_id = original.id

        new_data = {"_type": "Callout", "duration": 10,
                    "mediaStart": 0, "mediaDuration": 10}
        result = track.replace_clip(old_id, new_data)

        assert result.id != old_id

    def test_replace_clip_cascades_transitions(self):
        track = _make_track()
        c1 = track.add_callout("A", 0, 5)
        c2 = track.add_callout("B", 5, 5)
        track.add_fade_through_black(c1, c2, 0.5)

        new_data = {"_type": "Callout", "duration": 5,
                    "mediaStart": 0, "mediaDuration": 5}
        track.replace_clip(c1.id, new_data)

        assert track._data.get("transitions", []) == []

    def test_replace_clip_nonexistent_raises(self):
        track = _make_track()
        with pytest.raises(KeyError, match="No clip with id=999"):
            track.replace_clip(999, {"_type": "Callout"})


class TestClone:
    def test_clone_returns_deep_copy(self):
        track = _make_track()
        clip = track.add_callout("A", 0, 5)
        clip._data["effects"] = [{"effectName": "Glow"}]

        cloned = clip.clone()

        cloned._data["effects"][0]["effectName"] = "Shadow"
        assert clip._data["effects"][0]["effectName"] == "Glow"

    def test_clone_has_sentinel_id(self):
        track = _make_track()
        clip = track.add_callout("A", 0, 5)
        assert "id" in clip._data

        cloned = clip.clone()

        assert cloned.id == -1


# ------------------------------------------------------------------
# Bug 15: replace_clip remaps nested IDs
# ------------------------------------------------------------------

class TestReplaceClipRemapsNestedIds:
    def test_remaps_group_internal_clip_ids(self):
        track = _make_track()
        original = track.add_callout("A", 0, 5)
        old_id = original.id

        # Build a Group-like replacement with nested tracks
        group_data: dict[str, Any] = {
            "_type": "Group",
            "duration": 5000,
            "mediaStart": 0,
            "mediaDuration": 5000,
            "scalar": 1,
            "tracks": [{
                "trackIndex": 0,
                "medias": [{"id": 999, "_type": "VMFile", "start": 0, "duration": 5000}],
            }],
            "attributes": {},
            "parameters": {},
            "effects": [],
            "metadata": {},
            "animationTracks": {},
        }
        result = track.replace_clip(old_id, group_data)
        inner_id = result._data['tracks'][0]['medias'][0]['id']
        # Nested ID should be remapped, not the original 999
        assert inner_id != 999
