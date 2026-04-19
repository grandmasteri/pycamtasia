"""Tests that property setters propagate timing fields to compound clip children."""
from __future__ import annotations

from fractions import Fraction

from camtasia.timeline.clips import StitchedMedia, UnifiedMedia

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

    def test_start_does_not_propagate(self):
        data = _stitched_media_data()
        orig_starts = [c['start'] for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.start = EDIT_RATE * 5
        for child, orig in zip(_children_stitched(data), orig_starts):
            assert child['start'] == orig

    def test_duration_does_not_propagate(self):
        data = _stitched_media_data()
        orig = [(c['duration'], c['mediaDuration'], c['scalar']) for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.duration = EDIT_RATE * 3
        for child, (od, omd, osc) in zip(_children_stitched(data), orig):
            assert child['duration'] == od
            assert child['mediaDuration'] == omd
            assert child['scalar'] == osc

    def test_scalar_does_not_propagate(self):
        data = _stitched_media_data()
        orig = [(c['scalar'], c['mediaDuration']) for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.scalar = Fraction(1, 2)
        for child, (osc, omd) in zip(_children_stitched(data), orig):
            assert child['scalar'] == osc
            assert child['mediaDuration'] == omd

    def test_media_duration_does_not_propagate(self):
        data = _stitched_media_data()
        orig = [c['mediaDuration'] for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.media_duration = EDIT_RATE * 7
        for child, omd in zip(_children_stitched(data), orig):
            assert child['mediaDuration'] == omd

    def test_set_speed_propagates(self):
        data = _stitched_media_data()
        clip = StitchedMedia(data)
        clip.set_speed(2.0)
        for child in _children_stitched(data):
            assert child['scalar'] == data['scalar']
            assert child['mediaDuration'] == data['mediaDuration']
            assert child['metadata']['clipSpeedAttribute'] == data['metadata']['clipSpeedAttribute']

    def test_set_time_range_does_not_propagate(self):
        data = _stitched_media_data()
        orig = [(c['start'], c['duration'], c['mediaDuration'], c['scalar']) for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.set_time_range(2.0, 3.0)
        for child, (os, od, omd, osc) in zip(_children_stitched(data), orig):
            assert child['start'] == os
            assert child['duration'] == od
            assert child['mediaDuration'] == omd
            assert child['scalar'] == osc
