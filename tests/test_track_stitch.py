"""Tests for join_clips validation, unstitch_clip, stitch_adjacent, and extend_clip ripple."""
from __future__ import annotations

import pytest

from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track(medias: list[dict] | None = None) -> Track:
    return Track(
        attributes={'ident': 'test'},
        data={'trackIndex': 0, 'medias': medias or [], 'transitions': []},
    )


def _clip(clip_id: int, start_seconds: float, duration_seconds: float, **kw) -> dict:
    d = {
        'id': clip_id,
        '_type': kw.get('_type', 'AMFile'),
        'src': kw.get('src', 1),
        'start': seconds_to_ticks(start_seconds),
        'duration': seconds_to_ticks(duration_seconds),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(duration_seconds),
        'scalar': 1,
        'metadata': {},
        'animationTracks': {},
        'parameters': {},
        'effects': [],
    }
    d.update(kw)
    return d


class TestJoinClipsValidation:
    """join_clips must validate same-source and adjacency."""

    def test_different_sources_raises(self):
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 2.0, 3.0, src=20),
        ])
        with pytest.raises(ValueError, match='same source'):
            track.join_clips([1, 2])

    def test_non_adjacent_raises(self):
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 5.0, 3.0, src=10),  # gap between 2s and 5s
        ])
        with pytest.raises(ValueError, match='adjacent'):
            track.join_clips([1, 2])

    def test_adjacent_same_source_succeeds(self):
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 2.0, 3.0, src=10),
        ])
        result = track.join_clips([1, 2])
        assert result.clip_type == 'StitchedMedia'
        assert result.duration == seconds_to_ticks(5.0)

    def test_three_clips_middle_gap_raises(self):
        track = _make_track([
            _clip(1, 0.0, 2.0, src=5),
            _clip(2, 2.0, 1.0, src=5),
            _clip(3, 4.0, 1.0, src=5),  # gap at 3s-4s
        ])
        with pytest.raises(ValueError, match='adjacent'):
            track.join_clips([1, 2, 3])


class TestUnstitchClip:
    """unstitch_clip dissolves a StitchedMedia back into segments."""

    def _make_stitched_track(self):
        """Create a track with a StitchedMedia containing 2 segments."""
        inner = [
            _clip(81, 0.0, 2.0, src=5),
            _clip(82, 2.0, 3.0, src=5),
        ]
        stitched = {
            'id': 80,
            '_type': 'StitchedMedia',
            'start': seconds_to_ticks(1.0),
            'duration': seconds_to_ticks(5.0),
            'mediaStart': 0,
            'mediaDuration': seconds_to_ticks(5.0),
            'scalar': 1,
            'medias': inner,
            'parameters': {},
            'effects': [],
            'metadata': {},
            'animationTracks': {},
            'attributes': {'ident': ''},
        }
        return _make_track([stitched])

    def test_unstitch_produces_segments(self):
        track = self._make_stitched_track()
        clips = track.unstitch_clip(80)
        assert len(clips) == 2
        # Original stitched clip should be gone
        ids = [m['id'] for m in track._data['medias']]
        assert 80 not in ids

    def test_unstitch_positions_segments_correctly(self):
        track = self._make_stitched_track()
        clips = track.unstitch_clip(80)
        starts = sorted(c.start for c in clips)
        # Parent starts at 1s; inner segments at 0s and 2s relative
        assert starts[0] == seconds_to_ticks(1.0)
        assert starts[1] == seconds_to_ticks(3.0)

    def test_unstitch_non_stitched_raises(self):
        track = _make_track([_clip(1, 0.0, 2.0)])
        with pytest.raises(TypeError, match='not StitchedMedia'):
            track.unstitch_clip(1)

    def test_unstitch_missing_clip_raises(self):
        track = _make_track([])
        with pytest.raises(KeyError, match='No clip with id=999'):
            track.unstitch_clip(999)


class TestStitchAdjacent:
    """stitch_adjacent is a convenience wrapper around join_clips."""

    def test_stitch_adjacent_succeeds(self):
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 2.0, 3.0, src=10),
        ])
        result = track.stitch_adjacent([1, 2])
        assert result.clip_type == 'StitchedMedia'

    def test_stitch_adjacent_validates_source(self):
        track = _make_track([
            _clip(1, 0.0, 2.0, src=10),
            _clip(2, 2.0, 3.0, src=20),
        ])
        with pytest.raises(ValueError, match='same source'):
            track.stitch_adjacent([1, 2])


class TestExtendClipRipple:
    """extend_clip with ripple=True pushes following clips."""

    def test_ripple_true_pushes_following(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
            _clip(3, 5.0, 1.0),
        ])
        track.extend_clip(1, extend_seconds=1.0, ripple=True)
        medias = track._data['medias']
        assert medias[0]['duration'] == seconds_to_ticks(3.0)
        assert medias[1]['start'] == seconds_to_ticks(3.0)
        assert medias[2]['start'] == seconds_to_ticks(6.0)

    def test_ripple_false_does_not_push(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ])
        track.extend_clip(1, extend_seconds=1.0, ripple=False)
        assert track._data['medias'][0]['duration'] == seconds_to_ticks(3.0)
        # Clip 2 should NOT have moved
        assert track._data['medias'][1]['start'] == seconds_to_ticks(2.0)

    def test_ripple_default_false(self):
        track = _make_track([
            _clip(1, 0.0, 2.0),
            _clip(2, 2.0, 3.0),
        ])
        track.extend_clip(1, extend_seconds=1.0)
        # Default ripple=False — clip 2 stays
        assert track._data['medias'][1]['start'] == seconds_to_ticks(2.0)
