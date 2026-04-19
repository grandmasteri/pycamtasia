"""Tests for Track.split_all_clips_at()."""
from __future__ import annotations

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track(*medias) -> tuple[Track, dict]:
    """Build a Track with the given media dicts."""
    attrs: dict = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
    data: dict = {'trackIndex': 0, 'medias': list(medias), 'transitions': []}
    return Track(attrs, data), data


def _clip(clip_id: int, start_s: float, dur_s: float) -> dict:
    """Return a minimal VMFile clip dict."""
    return {
        'id': clip_id,
        '_type': 'VMFile',
        'src': 1,
        'trackNumber': 0,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'metadata': {},
        'parameters': {},
        'effects': [],
        'animationTracks': {},
    }


class TestSplitAllClipsAt:
    """Tests for Track.split_all_clips_at()."""

    def test_splits_single_spanning_clip(self) -> None:
        """A single clip spanning the time point is split into two."""
        track, data = _make_track(_clip(1, 0.0, 10.0))
        split_count: int = track.split_all_clips_at(5.0)
        assert split_count == 1
        assert len(data['medias']) == 2
        # Left half ends at 5s, right half starts at 5s
        starts = sorted(m['start'] for m in data['medias'])
        assert starts[0] == seconds_to_ticks(0.0)
        assert starts[1] == seconds_to_ticks(5.0)

    def test_splits_multiple_overlapping_clips(self) -> None:
        """Two clips that both span the time point are both split."""
        track, data = _make_track(
            _clip(1, 0.0, 10.0),
            _clip(2, 2.0, 10.0),
        )
        split_count: int = track.split_all_clips_at(5.0)
        assert split_count == 2
        assert len(data['medias']) == 4
        # All four pieces should be VMFile clips
        assert all(m['_type'] == 'VMFile' for m in data['medias'])

    def test_returns_zero_when_no_clips_span_time(self) -> None:
        """No clips at the time point means nothing is split."""
        track, data = _make_track(_clip(1, 0.0, 3.0))
        split_count: int = track.split_all_clips_at(5.0)
        assert split_count == 0
        assert len(data['medias']) == 1

    def test_returns_zero_on_empty_track(self) -> None:
        """An empty track returns zero."""
        track, _ = _make_track()
        assert track.split_all_clips_at(5.0) == 0

    def test_skips_clip_at_exact_start_boundary(self) -> None:
        """A clip whose start equals the split point is not spanning it."""
        track, data = _make_track(_clip(1, 5.0, 5.0))
        split_count: int = track.split_all_clips_at(5.0)
        # clips_at uses start <= t < start+duration, so t==start IS spanning.
        # But split_clip raises ValueError when split_point == orig_start.
        assert split_count == 0
        assert len(data['medias']) == 1

    def test_skips_clip_at_exact_end_boundary(self) -> None:
        """A clip whose end equals the split point is not spanning."""
        track, data = _make_track(_clip(1, 0.0, 5.0))
        split_count: int = track.split_all_clips_at(5.0)
        assert split_count == 0
        assert len(data['medias']) == 1

    def test_only_spanning_clips_are_split(self) -> None:
        """Non-spanning clips on the same track are left untouched."""
        track, data = _make_track(
            _clip(1, 0.0, 10.0),   # spans 5.0
            _clip(2, 20.0, 5.0),   # does NOT span 5.0
        )
        split_count: int = track.split_all_clips_at(5.0)
        assert split_count == 1
        assert len(data['medias']) == 3

    def test_split_durations_are_preserved(self) -> None:
        """The sum of left+right durations equals the original."""
        original_duration: int = seconds_to_ticks(10.0)
        track, data = _make_track(_clip(1, 0.0, 10.0))
        track.split_all_clips_at(5.0)
        total: int = sum(m['duration'] for m in data['medias'])
        assert total == original_duration

