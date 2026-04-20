"""Tests for camtasia.timeline.clips.stitched — StitchedMedia clip type."""
from __future__ import annotations

from fractions import Fraction

import pytest

from camtasia.timeline.clips import AMFile, BaseClip, StitchedMedia, clip_from_dict
from camtasia.timeline.clips.base import EDIT_RATE
from camtasia.timing import seconds_to_ticks

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _base_clip_dict(**overrides) -> dict:
    base = {
        "id": 14,
        "_type": "AMFile",
        "src": 3,
        "start": 0,
        "duration": 106051680000,
        "mediaStart": 0,
        "mediaDuration": 113484000000,
        "scalar": 1,
    }
    base.update(overrides)
    return base


def _stitched_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="StitchedMedia",
        id=80,
        medias=[
            _base_clip_dict(_type="AMFile", id=81, start=0, duration=50000000),
            _base_clip_dict(_type="AMFile", id=82, start=50000000, duration=60000000),
        ],
        attributes={"gain": 0.9},
    )
    d.update(overrides)
    return d


_S5 = seconds_to_ticks(5.0)


# ------------------------------------------------------------------
# StitchedMedia basic properties
# ------------------------------------------------------------------

def test_stitched_nested_clips_returns_typed_clips() -> None:
    clip = StitchedMedia(_stitched_dict())
    actual_clips = clip.nested_clips
    assert [type(c) for c in actual_clips] == [AMFile, AMFile]
    assert actual_clips[0].id == 81
    assert actual_clips[1].id == 82


def test_stitched_volume() -> None:
    clip = StitchedMedia(_stitched_dict())
    assert clip.gain == 0.9


def test_stitched_nested_clips_empty_when_no_medias() -> None:
    data = _base_clip_dict(_type="StitchedMedia")
    clip = StitchedMedia(data)
    assert clip.nested_clips == []


def test_stitched_attributes():
    clip = StitchedMedia(_stitched_dict())
    assert isinstance(clip.attributes, dict)


# ------------------------------------------------------------------
# StitchedMedia: set_source raises
# ------------------------------------------------------------------

class TestStitchedSetSource:
    def test_set_source_raises(self):
        s = StitchedMedia({
            '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': _S5,
            'mediaDuration': _S5, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'medias': [],
        })
        with pytest.raises(TypeError, match='do not have a top-level source'):
            s.set_source(1)


# ------------------------------------------------------------------
# StitchedMedia: min_media_start
# ------------------------------------------------------------------

def test_stitched_min_media_start():
    clip = clip_from_dict({'_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'mediaStart': 0, 'mediaDuration': 100, 'minMediaStart': 42})
    assert clip.min_media_start == 42
    clip2 = clip_from_dict({'_type': 'StitchedMedia', 'id': 2, 'start': 0, 'duration': 100,
                            'mediaStart': 0, 'mediaDuration': 100})
    assert clip2.min_media_start == 0


# ------------------------------------------------------------------
# StitchedMedia: is_stitched, is_audio, is_video
# ------------------------------------------------------------------

def test_is_stitched():
    clip = clip_from_dict({'_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'mediaStart': 0, 'mediaDuration': 100})
    assert clip.is_stitched is True
    assert clip.is_placeholder is False


def test_base_clip_is_audio_stitched_media():
    clip = BaseClip({
        '_type': 'StitchedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'medias': [{'_type': 'AMFile'}],
    })
    assert clip.is_audio is True


def test_base_clip_is_video_stitched_media():
    clip = BaseClip({
        '_type': 'StitchedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'medias': [{'_type': 'VMFile'}],
    })
    assert clip.is_video is True


# ------------------------------------------------------------------
# StitchedMedia improvements
# ------------------------------------------------------------------

class TestStitchedMediaImprovements:
    def _make_stitched(self) -> StitchedMedia:
        return StitchedMedia({
            'id': 1, '_type': 'StitchedMedia', 'start': 0, 'duration': 200,
            'mediaStart': 0, 'mediaDuration': 200, 'scalar': 1,
            'medias': [
                {'id': 10, '_type': 'ScreenVMFile', 'start': 0, 'duration': 100,
                 'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1},
                {'id': 11, '_type': 'ScreenVMFile', 'start': 100, 'duration': 100,
                 'mediaStart': 100, 'mediaDuration': 100, 'scalar': 1},
            ],
        })

    def test_segment_count(self):
        assert self._make_stitched().segment_count == 2

    def test_segment_count_empty(self):
        assert StitchedMedia({
            'id': 1, '_type': 'StitchedMedia', 'start': 0, 'duration': 0,
            'mediaStart': 0, 'mediaDuration': 0, 'scalar': 1,
        }).segment_count == 0

    def test_clear_segments(self):
        actual_clip = self._make_stitched()
        actual_clip.clear_segments()
        assert actual_clip.segment_count == 0
        assert actual_clip._data['medias'] == []


def _make_stitched_for_speed(segments: list[tuple[int, int, int]]) -> BaseClip:
    """Build a StitchedMedia clip with inner segments (start, duration, mediaDuration)."""
    medias = []
    for start, dur, md in segments:
        medias.append({
            '_type': 'VMFile', 'id': len(medias) + 100,
            'start': start, 'duration': dur, 'mediaDuration': md,
            'scalar': 1, 'metadata': {},
        })
    total_dur = sum(d for _, d, _ in segments)
    return BaseClip({
        '_type': 'StitchedMedia', 'id': 1, 'start': 0,
        'duration': total_dur, 'mediaDuration': total_dur, 'scalar': 1,
        'medias': medias, 'metadata': {}, 'parameters': {},
        'effects': [], 'animationTracks': {},
    })


class TestSetSpeedStitchedMediaLayout:
    def test_inner_starts_sequential_after_speed_change(self):
        clip = _make_stitched_for_speed([
            (0, EDIT_RATE, EDIT_RATE),
            (EDIT_RATE, EDIT_RATE, EDIT_RATE),
        ])
        clip.set_speed(2.0)
        inners = clip._data['medias']
        assert inners[0]['start'] == 0
        expected_dur = int(Fraction(EDIT_RATE) * Fraction(1, 2))
        assert inners[1]['start'] == expected_dur

    def test_no_gaps_or_overlaps_after_speed_change(self):
        clip = _make_stitched_for_speed([
            (0, EDIT_RATE, EDIT_RATE),
            (EDIT_RATE, EDIT_RATE * 2, EDIT_RATE * 2),
            (EDIT_RATE * 3, EDIT_RATE, EDIT_RATE),
        ])
        clip.set_speed(0.5)
        inners = clip._data['medias']
        for i in range(len(inners) - 1):
            end = inners[i]['start'] + int(Fraction(str(inners[i]['duration'])))
            assert end == inners[i + 1]['start']

    def test_single_segment_start_stays_zero(self):
        clip = _make_stitched_for_speed([(0, EDIT_RATE, EDIT_RATE)])
        clip.set_speed(3.0)
        assert clip._data['medias'][0]['start'] == 0


class TestClearSegmentsResetsScalarAndMediaStart:
    """clear_segments must reset scalar to 1 and mediaStart to 0."""

    def test_clear_segments_resets_scalar(self):
        data = {
            '_type': 'StitchedMedia', 'id': 1, 'start': 0,
            'duration': 1000, 'mediaDuration': 2000,
            'scalar': '1/2', 'mediaStart': 500,
            'medias': [{'_type': 'VMFile', 'id': 10, 'start': 0,
                        'duration': 1000, 'mediaDuration': 2000, 'scalar': '1/2'}],
            'metadata': {}, 'parameters': {}, 'effects': [], 'animationTracks': {},
        }
        clip = StitchedMedia(data)
        clip.clear_segments()
        assert data['scalar'] == 1
        assert data['mediaStart'] == 0
        assert data['duration'] == 0
        assert data['mediaDuration'] == 0
        assert data['medias'] == []
