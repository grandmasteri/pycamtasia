"""Tests that property setters propagate timing fields to compound clip children."""
from __future__ import annotations

from fractions import Fraction

from camtasia.timeline.clips import StitchedMedia, UnifiedMedia
from camtasia.timeline.clips.base import BaseClip
from camtasia.timing import seconds_to_ticks

EDIT_RATE = 705_600_000


# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------

def _unified_media_data(start=0, duration=705600000, media_duration=705600000):
    return {
        '_type': 'UnifiedMedia', 'id': 1, 'start': start,
        'duration': duration, 'mediaDuration': media_duration,
        'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
        'metadata': {}, 'animationTracks': {},
        'video': {'_type': 'VMFile', 'id': 2, 'src': 1, 'start': start,
                  'duration': duration, 'mediaDuration': media_duration,
                  'mediaStart': 0, 'scalar': 1, 'trackNumber': 0,
                  'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
        'audio': {'_type': 'AMFile', 'id': 3, 'src': 1, 'start': start,
                  'duration': duration, 'mediaDuration': media_duration,
                  'mediaStart': 0, 'scalar': 1, 'trackNumber': 0, 'channelNumber': 0,
                  'parameters': {}, 'effects': [], 'metadata': {},
                  'animationTracks': {}, 'attributes': {'gain': 1.0}},
    }


def _stitched_media_data(start=0, duration=705600000, media_duration=705600000):
    def _segment(id_, type_='VMFile'):
        return {
            '_type': type_, 'id': id_, 'src': 1, 'start': start,
            'duration': duration, 'mediaDuration': media_duration,
            'mediaStart': 0, 'scalar': 1, 'trackNumber': 0,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
    return {
        '_type': 'StitchedMedia', 'id': 10, 'start': start,
        'duration': duration, 'mediaDuration': media_duration,
        'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
        'metadata': {}, 'animationTracks': {},
        'medias': [_segment(11), _segment(12, 'AMFile')],
    }


def _children_unified(data):
    return [data['video'], data['audio']]


def _children_stitched(data):
    return data['medias']


# ---------------------------------------------------------------------------
# UnifiedMedia propagation
# ---------------------------------------------------------------------------

class TestUnifiedMediaPropagation:

    def test_start_propagates(self):
        data = _unified_media_data()
        clip = UnifiedMedia(data)
        clip.start = EDIT_RATE * 5
        for child in _children_unified(data):
            assert child['start'] == EDIT_RATE * 5

    def test_duration_propagates(self):
        data = _unified_media_data()
        clip = UnifiedMedia(data)
        clip.duration = EDIT_RATE * 3
        for child in _children_unified(data):
            assert child['duration'] == EDIT_RATE * 3
            assert child['mediaDuration'] == data['mediaDuration']
            assert child['scalar'] == data.get('scalar', 1)

    def test_scalar_propagates(self):
        data = _unified_media_data()
        clip = UnifiedMedia(data)
        clip.scalar = Fraction(1, 2)
        for child in _children_unified(data):
            assert child['scalar'] == data['scalar']
            assert child['mediaDuration'] == data['mediaDuration']

    def test_media_duration_propagates(self):
        data = _unified_media_data()
        clip = UnifiedMedia(data)
        clip.media_duration = EDIT_RATE * 7
        for child in _children_unified(data):
            assert child['mediaDuration'] == EDIT_RATE * 7

    def test_set_speed_propagates(self):
        data = _unified_media_data()
        clip = UnifiedMedia(data)
        clip.set_speed(2.0)
        for child in _children_unified(data):
            assert child['scalar'] == data['scalar']
            assert child['mediaDuration'] == data['mediaDuration']
            assert child['mediaStart'] == data.get('mediaStart', 0)
            assert child['metadata']['clipSpeedAttribute'] == data['metadata']['clipSpeedAttribute']

    def test_set_time_range_propagates(self):
        data = _unified_media_data()
        clip = UnifiedMedia(data)
        clip.set_time_range(2.0, 3.0)
        for child in _children_unified(data):
            assert child['start'] == data['start']
            assert child['duration'] == data['duration']
            assert child['mediaDuration'] == data['mediaDuration']
            assert child['scalar'] == data.get('scalar', 1)


# ---------------------------------------------------------------------------
# StitchedMedia propagation
# ---------------------------------------------------------------------------

class TestStitchedMediaPropagation:

    def test_start_propagates(self):
        data = _stitched_media_data()
        clip = StitchedMedia(data)
        clip.start = EDIT_RATE * 5
        for child in _children_stitched(data):
            assert child['start'] == data['start']

    def test_duration_propagates(self):
        data = _stitched_media_data()
        clip = StitchedMedia(data)
        clip.duration = EDIT_RATE * 3
        for child in _children_stitched(data):
            assert child['duration'] == data['duration']
            assert child['mediaDuration'] == data['mediaDuration']
            assert child['scalar'] == data.get('scalar', 1)

    def test_scalar_propagates(self):
        data = _stitched_media_data()
        clip = StitchedMedia(data)
        clip.scalar = Fraction(1, 2)
        for child in _children_stitched(data):
            assert child['scalar'] == data['scalar']
            assert child['mediaDuration'] == data['mediaDuration']

    def test_media_duration_propagates(self):
        data = _stitched_media_data()
        clip = StitchedMedia(data)
        clip.media_duration = EDIT_RATE * 7
        for child in _children_stitched(data):
            assert child['mediaDuration'] == data['mediaDuration']

    def test_set_speed_propagates(self):
        data = _stitched_media_data()
        clip = StitchedMedia(data)
        clip.set_speed(2.0)
        for child in _children_stitched(data):
            assert child['scalar'] == data['scalar']
            assert child['mediaDuration'] == data['mediaDuration']
            assert child['metadata']['clipSpeedAttribute'] == data['metadata']['clipSpeedAttribute']

    def test_set_time_range_propagates(self):
        data = _stitched_media_data()
        clip = StitchedMedia(data)
        clip.set_time_range(2.0, 3.0)
        for child in _children_stitched(data):
            assert child['start'] == data['start']
            assert child['duration'] == data['duration']
            assert child['mediaDuration'] == data['mediaDuration']
            assert child['scalar'] == data.get('scalar', 1)


class TestStitchedMediaSetStartSeconds:
    """set_start_seconds propagates start to StitchedMedia children."""

    def test_propagates_start(self):
        data = _stitched_media_data()
        clip = BaseClip(data)
        clip.set_start_seconds(2.0)
        expected_start = seconds_to_ticks(2.0)
        for inner in data['medias']:
            assert inner['start'] == expected_start


class TestStitchedMediaSetDurationSeconds:
    """set_duration_seconds propagates to StitchedMedia children."""

    def test_propagates_duration_and_scalar(self):
        data = _stitched_media_data()
        clip = BaseClip(data)
        clip.set_duration_seconds(3.0)
        expected_dur = seconds_to_ticks(3.0)
        for inner in data['medias']:
            assert inner['duration'] == expected_dur
            assert inner['scalar'] == data.get('scalar', 1)
