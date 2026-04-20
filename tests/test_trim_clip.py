"""Tests for Track.trim_clip()."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


class TestTrimClip:
    def test_trim_start(self):
        track = _make_track()
        clip = track.add_callout("Hello", 1.0, 10.0)
        orig_start = seconds_to_ticks(1.0)
        orig_dur = seconds_to_ticks(10.0)

        track.trim_clip(clip.id, trim_start_seconds=2.0)

        m = track._data['medias'][0]
        assert m['start'] == orig_start + seconds_to_ticks(2.0)
        assert m['duration'] == orig_dur - seconds_to_ticks(2.0)
        assert m['mediaStart'] == seconds_to_ticks(2.0)

    def test_trim_end(self):
        track = _make_track()
        clip = track.add_callout("Hello", 1.0, 10.0)
        orig_start = seconds_to_ticks(1.0)
        orig_dur = seconds_to_ticks(10.0)

        track.trim_clip(clip.id, trim_end_seconds=3.0)

        m = track._data['medias'][0]
        assert m['start'] == orig_start
        assert m['duration'] == orig_dur - seconds_to_ticks(3.0)

    def test_trim_both(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0.0, 10.0)

        track.trim_clip(clip.id, trim_start_seconds=2.0, trim_end_seconds=3.0)

        m = track._data['medias'][0]
        assert m['start'] == seconds_to_ticks(2.0)
        assert m['duration'] == seconds_to_ticks(10.0) - seconds_to_ticks(2.0) - seconds_to_ticks(3.0)
        assert m['mediaStart'] == seconds_to_ticks(2.0)

    def test_trim_too_much_raises(self):
        track = _make_track()
        clip = track.add_callout("Hello", 0.0, 5.0)

        with pytest.raises(ValueError, match="zero or negative duration"):
            track.trim_clip(clip.id, trim_start_seconds=3.0, trim_end_seconds=3.0)

    def test_trim_nonexistent_raises(self):
        track = _make_track()

        with pytest.raises(KeyError, match="No clip with id=999"):
            track.trim_clip(999, trim_start_seconds=1.0)


class TestTrimClipUnifiedMediaEffects:
    """Bug 11: trim_clip should adjust effects on UnifiedMedia sub-clips."""

    def _make_unified_clip(self, track: Track) -> int:
        """Add a UnifiedMedia clip with effects on sub-clips."""
        clip_data: dict[str, Any] = {
            "id": 100,
            "_type": "UnifiedMedia",
            "start": 0,
            "duration": seconds_to_ticks(10.0),
            "mediaStart": 0,
            "mediaDuration": seconds_to_ticks(10.0),
            "scalar": 1,
            "video": {
                "id": 101,
                "_type": "VMFile",
                "start": 0,
                "duration": seconds_to_ticks(10.0),
                "mediaStart": 0,
                "mediaDuration": seconds_to_ticks(10.0),
                "scalar": 1,
                "effects": [
                    {"start": 0, "duration": seconds_to_ticks(3.0), "name": "early"},
                    {"start": seconds_to_ticks(7.0), "duration": seconds_to_ticks(3.0), "name": "late"},
                ],
            },
        }
        track._data.setdefault("medias", []).append(clip_data)
        return 100

    def test_trim_start_adjusts_sub_clip_effects(self):
        track = _make_track()
        clip_id = self._make_unified_clip(track)

        track.trim_clip(clip_id, trim_start_seconds=2.0)

        video = track._data["medias"][0]["video"]
        effects = video["effects"]
        # "early" effect: was start=0, dur=3s. After trim 2s from start:
        # trimmed by 2s -> start=0, dur=1s
        assert effects[0]["start"] == 0
        assert effects[0]["duration"] == seconds_to_ticks(1.0)

    def test_trim_end_adjusts_sub_clip_effects(self):
        track = _make_track()
        clip_id = self._make_unified_clip(track)

        track.trim_clip(clip_id, trim_end_seconds=2.0)

        video = track._data["medias"][0]["video"]
        effects = video["effects"]
        # "late" effect: was start=7s, dur=3s. New clip dur=8s.
        # Effect end=10s > 8s, so trimmed to dur=1s
        late = next(e for e in effects if e.get("name") == "late")
        assert late["duration"] == seconds_to_ticks(1.0)
