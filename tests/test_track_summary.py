"""Tests for Track.summary()."""
from __future__ import annotations

from typing import Any

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _track(
    index: int = 0,
    name: str = "Test",
    medias: list[dict] | None = None,
    transitions: list[dict] | None = None,
) -> Track:
    attrs: dict[str, Any] = {
        "ident": name,
        "audioMuted": False,
        "videoHidden": False,
        "magnetic": False,
        "solo": False,
        "metadata": {"IsLocked": "False"},
    }
    data: dict[str, Any] = {
        "trackIndex": index,
        "medias": medias or [],
        "transitions": transitions or [],
        "parameters": {},
    }
    return Track(attrs, data)


def _media(id: int, type: str, start: int, duration: int) -> dict[str, Any]:
    return {
        "id": id,
        "_type": type,
        "src": 1,
        "start": start,
        "duration": duration,
        "mediaStart": 0,
        "mediaDuration": duration,
        "scalar": 1,
        "metadata": {},
        "animationTracks": {},
        "parameters": {},
        "effects": [],
        "trackNumber": 0,
        "attributes": {"ident": ""},
    }


class TestTrackSummary:
    def test_empty_track(self):
        track = _track(name="Empty")
        result = track.summary()
        assert result == "Track: Empty\nClips: 0\nDuration: 0.00s"

    def test_single_clip(self):
        dur = seconds_to_ticks(5.0)
        track = _track(name="V1", medias=[_media(1, "VMFile", 0, dur)])
        result = track.summary()
        lines = result.split("\n")
        assert lines[0] == "Track: V1"
        assert lines[1] == "Clips: 1"
        assert lines[2] == "Duration: 5.00s"
        assert "Types: VMFile" in result

    def test_multiple_clip_types_sorted(self):
        dur = seconds_to_ticks(2.0)
        track = _track(
            name="Mixed",
            medias=[
                _media(1, "VMFile", 0, dur),
                _media(2, "AMFile", dur, dur),
            ],
        )
        result = track.summary()
        assert "Types: AMFile, VMFile" in result

    def test_transitions_shown_when_present(self):
        dur = seconds_to_ticks(3.0)
        track = _track(
            name="Trans",
            medias=[
                _media(1, "VMFile", 0, dur),
                _media(2, "VMFile", dur, dur),
            ],
            transitions=[
                {"leftMedia": 1, "rightMedia": 2, "duration": seconds_to_ticks(0.5)},
            ],
        )
        result = track.summary()
        assert "Transitions: 1" in result

    def test_transitions_hidden_when_absent(self):
        dur = seconds_to_ticks(3.0)
        track = _track(name="NoTrans", medias=[_media(1, "VMFile", 0, dur)])
        result = track.summary()
        assert "Transitions" not in result

    def test_gaps_shown_when_present(self):
        dur = seconds_to_ticks(2.0)
        gap = seconds_to_ticks(1.0)
        track = _track(
            name="Gappy",
            medias=[
                _media(1, "VMFile", 0, dur),
                _media(2, "VMFile", dur + gap, dur),
            ],
        )
        result = track.summary()
        assert "Gaps: 1 (1.00s total)" in result

    def test_gaps_hidden_when_absent(self):
        dur = seconds_to_ticks(2.0)
        track = _track(
            name="NoGap",
            medias=[
                _media(1, "VMFile", 0, dur),
                _media(2, "VMFile", dur, dur),
            ],
        )
        result = track.summary()
        assert "Gaps" not in result

    def test_clip_types_hidden_when_empty(self):
        track = _track(name="Empty")
        result = track.summary()
        assert "Types" not in result

    def test_returns_string(self):
        track = _track()
        assert isinstance(track.summary(), str)
