"""Tests for timeline search and filter operations."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.timeline import Timeline
from camtasia.timing import EDIT_RATE, seconds_to_ticks


def _make_clip(clip_id: int, clip_type: str, start_seconds: float, duration_seconds: float) -> dict[str, Any]:
    start = seconds_to_ticks(start_seconds)
    duration = seconds_to_ticks(duration_seconds)
    return {
        "_type": clip_type, "id": clip_id,
        "start": start, "duration": duration,
        "mediaStart": 0, "mediaDuration": duration, "scalar": 1,
        "src": clip_id, "metadata": {}, "animationTracks": {},
        "parameters": {}, "effects": [],
    }


def _timeline_data() -> dict[str, Any]:
    """Build a timeline with 3 tracks and mixed clip types.

    Track 0: AMFile at 0-2s, AMFile at 5-8s
    Track 1: IMFile at 1-4s, VMFile at 6-9s
    Track 2: IMFile at 10-12s
    """
    tracks = [
        {"trackIndex": 0, "medias": [
            _make_clip(1, "AMFile", 0, 2),
            _make_clip(2, "AMFile", 5, 3),
        ], "parameters": {}},
        {"trackIndex": 1, "medias": [
            _make_clip(3, "IMFile", 1, 3),
            _make_clip(4, "VMFile", 6, 3),
        ], "parameters": {}},
        {"trackIndex": 2, "medias": [
            _make_clip(5, "IMFile", 10, 2),
        ], "parameters": {}},
    ]
    attrs = [
        {"ident": f"Track {i}", "audioMuted": False, "videoHidden": False,
         "magnetic": False, "metadata": {"IsLocked": "False"}}
        for i in range(3)
    ]
    return {
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": attrs,
        "parameters": {},
    }


@pytest.fixture
def tl() -> Timeline:
    return Timeline(_timeline_data())


class TestClipsInRange:
    def test_clips_in_range_finds_overlapping(self, tl: Timeline):
        # Range 1-3s should overlap: AMFile@0-2s (track0), IMFile@1-4s (track1)
        results = tl.clips_in_range(1, 3)
        ids = {clip.id for _, clip in results}
        assert ids == {1, 3}

    def test_clips_in_range_excludes_non_overlapping(self, tl: Timeline):
        # Range 1-3s should NOT include clips at 5-8s, 6-9s, 10-12s
        results = tl.clips_in_range(1, 3)
        ids = {clip.id for _, clip in results}
        assert 2 not in ids
        assert 4 not in ids
        assert 5 not in ids

    def test_clips_in_range_empty(self, tl: Timeline):
        # Range 12-15s has no clips
        assert tl.clips_in_range(12, 15) == []


class TestClipsOfType:
    def test_clips_of_type_amfile(self, tl: Timeline):
        results = tl.clips_of_type("AMFile")
        ids = {clip.id for _, clip in results}
        assert ids == {1, 2}
        assert all(clip.clip_type == "AMFile" for _, clip in results)

    def test_clips_of_type_imfile(self, tl: Timeline):
        results = tl.clips_of_type("IMFile")
        ids = {clip.id for _, clip in results}
        assert ids == {3, 5}
        assert all(clip.clip_type == "IMFile" for _, clip in results)

    def test_clips_of_type_none_found(self, tl: Timeline):
        assert tl.clips_of_type("Callout") == []


class TestConvenienceProperties:
    def test_audio_clips_property(self, tl: Timeline):
        results = tl.audio_clips
        ids = {clip.id for _, clip in results}
        assert ids == {1, 2}
        assert all(clip.clip_type == "AMFile" for _, clip in results)

    def test_image_clips_property(self, tl: Timeline):
        results = tl.image_clips
        ids = {clip.id for _, clip in results}
        assert ids == {3, 5}
        assert all(clip.clip_type == "IMFile" for _, clip in results)

    def test_video_clips_property(self, tl: Timeline):
        results = tl.video_clips
        assert len(results) == 1
        assert results[0][1].clip_type == "VMFile"
        assert results[0][1].id == 4
