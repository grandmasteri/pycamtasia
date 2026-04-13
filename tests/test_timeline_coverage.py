"""Tests for camtasia.timeline.timeline — track management and L2 methods."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.timeline import Timeline
from camtasia.timeline.track import Track
from camtasia.timeline.marker import Marker
from camtasia.timing import EDIT_RATE, seconds_to_ticks


def _timeline_data(num_tracks: int = 1) -> dict[str, Any]:
    tracks = []
    attrs = []
    for i in range(num_tracks):
        tracks.append({"trackIndex": i, "medias": [], "parameters": {}})
        attrs.append({"ident": f"Track {i}", "audioMuted": False, "videoHidden": False,
                       "magnetic": False, "metadata": {"IsLocked": "False"}})
    return {
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": attrs,
        "parameters": {},
    }


class TestTimelineTotalDuration:
    def test_empty_timeline_returns_zero(self):
        tl = Timeline(_timeline_data())
        assert tl.total_duration_ticks == 0
        assert tl.total_duration_seconds() == 0.0

    def test_duration_from_clips(self):
        data = _timeline_data()
        clip_end = EDIT_RATE * 5
        data["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"] = [
            {"_type": "IMFile", "id": 1, "start": 0, "duration": clip_end,
             "mediaStart": 0, "mediaDuration": clip_end, "scalar": 1,
             "src": 1, "metadata": {}, "animationTracks": {}, "parameters": {}, "effects": []},
        ]
        tl = Timeline(data)
        assert tl.total_duration_ticks == clip_end
        assert tl.total_duration_seconds() == pytest.approx(5.0)


class TestTimelineGetOrCreateTrack:
    def test_returns_existing_track_by_name(self):
        tl = Timeline(_timeline_data(2))
        actual_track = tl.get_or_create_track("Track 0")
        assert actual_track.name == "Track 0"

    def test_creates_new_track_when_not_found(self):
        tl = Timeline(_timeline_data())
        actual_track = tl.get_or_create_track("New Track")
        assert actual_track.name == "New Track"
        assert tl.track_count == 2


class TestTimelineAllClips:
    def test_empty_timeline_returns_empty(self):
        tl = Timeline(_timeline_data())
        assert tl.all_clips() == []

    def test_collects_clips_across_tracks(self):
        data = _timeline_data(2)
        clip_a = {"_type": "IMFile", "id": 1, "start": 0, "duration": EDIT_RATE,
                  "mediaStart": 0, "mediaDuration": EDIT_RATE, "scalar": 1,
                  "src": 1, "metadata": {}, "animationTracks": {}, "parameters": {}, "effects": []}
        clip_b = {"_type": "IMFile", "id": 2, "start": 0, "duration": EDIT_RATE,
                  "mediaStart": 0, "mediaDuration": EDIT_RATE, "scalar": 1,
                  "src": 2, "metadata": {}, "animationTracks": {}, "parameters": {}, "effects": []}
        data["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"] = [clip_a]
        data["sceneTrack"]["scenes"][0]["csml"]["tracks"][1]["medias"] = [clip_b]
        tl = Timeline(data)
        actual_ids = [c.id for c in tl.all_clips()]
        assert actual_ids == [1, 2]


class TestTimelineAddMarker:
    def test_add_marker_returns_marker(self):
        tl = Timeline(_timeline_data())
        actual_marker = tl.add_marker("Chapter 1", 2.5)
        assert actual_marker.name == "Chapter 1"
        assert actual_marker.time == seconds_to_ticks(2.5)


class TestTimelineRemoveTrack:
    def test_remove_track_reduces_count(self):
        tl = Timeline(_timeline_data(3))
        assert tl.track_count == 3
        tl.remove_track(1)
        assert tl.track_count == 2

    def test_remove_track_renumbers(self):
        tl = Timeline(_timeline_data(3))
        tl.remove_track(0)
        actual_indices = [t.index for t in tl.tracks]
        assert actual_indices == [0, 1]

    def test_remove_nonexistent_track_raises(self):
        tl = Timeline(_timeline_data())
        with pytest.raises(KeyError, match="No track with index=99"):
            tl.remove_track(99)
