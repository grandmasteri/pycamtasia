"""Tests for Timeline.total_duration_formatted and Timeline.summary."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.timeline import Timeline
from camtasia.timing import EDIT_RATE


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


def _add_clip(data: dict, track_idx: int, clip_id: int, start_sec: float, dur_sec: float,
              clip_type: str = "IMFile") -> None:
    start = int(start_sec * EDIT_RATE)
    dur = int(dur_sec * EDIT_RATE)
    data["sceneTrack"]["scenes"][0]["csml"]["tracks"][track_idx]["medias"].append({
        "_type": clip_type, "id": clip_id, "start": start, "duration": dur,
        "mediaStart": 0, "mediaDuration": dur, "scalar": 1,
        "src": clip_id, "metadata": {}, "animationTracks": {}, "parameters": {}, "effects": [],
    })


class TestTotalDurationFormatted:
    @pytest.mark.parametrize(("dur_seconds", "expected"), [
        (0, "0:00"),
        (45, "0:45"),
        (125, "2:05"),
        (3661, "1:01:01"),
        (3600, "1:00:00"),
        (60, "1:00"),
    ], ids=["empty", "seconds-only", "minutes-and-seconds", "hours", "exact-hour", "exact-minute"])
    def test_total_duration_formatted(self, dur_seconds, expected):
        data = _timeline_data()
        if dur_seconds:
            _add_clip(data, 0, 1, 0, dur_seconds)
        tl = Timeline(data)
        assert tl.total_duration_formatted == expected


class TestSummary:
    def test_empty_timeline(self):
        tl = Timeline(_timeline_data())
        result = tl.summary()
        assert "Timeline: 0:00" in result
        assert "Tracks: 1" in result
        assert "Total clips: 0" in result
        assert "Clip density: 0.00" in result
        assert "Groups" not in result

    def test_with_clips(self):
        data = _timeline_data(2)
        _add_clip(data, 0, 1, 0, 10)
        _add_clip(data, 1, 2, 0, 5)
        tl = Timeline(data)
        result = tl.summary()
        assert "Timeline: 0:10" in result
        assert "Tracks: 2" in result
        assert "Total clips: 2" in result

    def test_with_groups(self):
        data = _timeline_data()
        # Add a Group clip
        _add_clip(data, 0, 1, 0, 10, clip_type="Group")
        # Groups need nested tracks structure
        media = data["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        media["tracks"] = [{"trackIndex": 0, "medias": []}]
        tl = Timeline(data)
        result = tl.summary()
        assert "Groups: 1" in result

    def test_summary_line_count_no_groups(self):
        tl = Timeline(_timeline_data())
        lines = tl.summary().split("\n")
        assert len(lines) == 4

    def test_summary_line_count_with_groups(self):
        data = _timeline_data()
        _add_clip(data, 0, 1, 0, 10, clip_type="Group")
        media = data["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        media["tracks"] = [{"trackIndex": 0, "medias": []}]
        tl = Timeline(data)
        lines = tl.summary().split("\n")
        assert len(lines) == 5
