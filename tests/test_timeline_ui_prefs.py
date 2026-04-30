"""Tests for Timeline UI preference properties and library asset insertion."""
from __future__ import annotations

import pytest

from camtasia.library.library import LibraryAsset
from camtasia.timeline.timeline import Timeline
from camtasia.timing import seconds_to_ticks


def _make_timeline_data(**extra) -> dict:
    data = {
        "id": 1,
        "sceneTrack": {
            "scenes": [{"csml": {"tracks": []}}]
        },
        "trackAttributes": [],
    }
    data.update(extra)
    return data


# ---------------------------------------------------------------------------
# detached property + detach/reattach
# ---------------------------------------------------------------------------

class TestDetached:
    def test_default_is_false(self):
        tl = Timeline(_make_timeline_data())
        assert tl.detached is False

    def test_set_true(self):
        tl = Timeline(_make_timeline_data())
        tl.detached = True
        assert tl.detached is True

    def test_detach_method(self):
        tl = Timeline(_make_timeline_data())
        tl.detach()
        assert tl.detached is True

    def test_reattach_method(self):
        tl = Timeline(_make_timeline_data())
        tl.detach()
        tl.reattach()
        assert tl.detached is False

    def test_stored_in_docprefs(self):
        tl = Timeline(_make_timeline_data())
        tl.detached = True
        assert tl._data['docPrefs']['DocPrefTimelineDetached'] is True


# ---------------------------------------------------------------------------
# playback_rate property
# ---------------------------------------------------------------------------

class TestPlaybackRate:
    def test_default_is_one(self):
        tl = Timeline(_make_timeline_data())
        assert tl.playback_rate == 1

    @pytest.mark.parametrize("rate", [1, 2, 4, 8])
    def test_valid_rates(self, rate):
        tl = Timeline(_make_timeline_data())
        tl.playback_rate = rate
        assert tl.playback_rate == rate

    def test_invalid_rate_raises(self):
        tl = Timeline(_make_timeline_data())
        with pytest.raises(ValueError, match="Playback rate must be one of"):
            tl.playback_rate = 3

    def test_stored_in_docprefs(self):
        tl = Timeline(_make_timeline_data())
        tl.playback_rate = 4
        assert tl._data['docPrefs']['DocPrefPlaybackRate'] == 4


# ---------------------------------------------------------------------------
# scroll_offset property
# ---------------------------------------------------------------------------

class TestScrollOffset:
    def test_default_is_zero(self):
        tl = Timeline(_make_timeline_data())
        assert tl.scroll_offset == 0.0

    def test_set_and_get(self):
        tl = Timeline(_make_timeline_data())
        tl.scroll_offset = 123.5
        assert tl.scroll_offset == 123.5

    def test_stored_in_docprefs(self):
        tl = Timeline(_make_timeline_data())
        tl.scroll_offset = 42.0
        assert tl._data['docPrefs']['DocPrefHorizontalScrollBarValue'] == 42.0


# ---------------------------------------------------------------------------
# add_library_asset
# ---------------------------------------------------------------------------

class TestAddLibraryAsset:
    def test_inserts_on_new_track(self):
        tl = Timeline(_make_timeline_data())
        asset = LibraryAsset(name="intro", kind="clip", payload={
            "id": 100, "_type": "IMFile", "start": 0, "duration": 1000,
        })
        tl.add_library_asset(asset, "Assets", 2.0)
        track = tl.find_track_by_name("Assets")
        assert track is not None
        clips = list(track.clips)
        assert len(clips) == 1
        assert clips[0].start == seconds_to_ticks(2.0)

    def test_remaps_clip_ids(self):
        tl = Timeline(_make_timeline_data())
        asset = LibraryAsset(name="clip", kind="clip", payload={
            "id": 1, "_type": "AMFile", "start": 0, "duration": 500,
        })
        tl.add_library_asset(asset, "Track1", 0.0)
        clips = list(tl.find_track_by_name("Track1").clips)
        # ID should be remapped to avoid collision with timeline id=1
        assert clips[0].id != 1

    def test_does_not_mutate_original_payload(self):
        tl = Timeline(_make_timeline_data())
        original_payload = {"id": 50, "_type": "IMFile", "start": 0, "duration": 100}
        asset = LibraryAsset(name="img", kind="clip", payload=original_payload)
        tl.add_library_asset(asset, "Track1", 5.0)
        assert original_payload["start"] == 0
        assert original_payload["id"] == 50
