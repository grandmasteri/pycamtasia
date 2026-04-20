"""Tests that property setters propagate timing fields to compound clip children."""
from __future__ import annotations

from fractions import Fraction

from camtasia.timeline.clips import StitchedMedia, UnifiedMedia
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

    def test_start_does_not_propagate(self):
        data = _stitched_media_data()
        orig_starts = [c['start'] for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.start = EDIT_RATE * 5
        for child, orig in zip(_children_stitched(data), orig_starts):
            assert child['start'] == orig

    def test_duration_propagates_proportionally(self):
        data = _stitched_media_data()
        old_durations = [c['duration'] for c in _children_stitched(data)]
        old_total = data['duration']
        clip = StitchedMedia(data)
        clip.duration = EDIT_RATE * 3
        ratio = Fraction(EDIT_RATE * 3) / Fraction(old_total)
        for child, od in zip(_children_stitched(data), old_durations):
            assert child['duration'] == round(Fraction(od) * ratio)

    def test_scalar_propagates_proportionally(self):
        data = _stitched_media_data()
        old_durations = [c['duration'] for c in _children_stitched(data)]
        old_scalar = Fraction(str(data.get('scalar', 1)))
        clip = StitchedMedia(data)
        clip.scalar = Fraction(1, 2)
        new_scalar = Fraction(1, 2)
        ratio = new_scalar / old_scalar
        for child, od in zip(_children_stitched(data), old_durations):
            assert child['duration'] == round(Fraction(od) * ratio)

    def test_media_duration_does_not_propagate(self):
        data = _stitched_media_data()
        orig = [c['mediaDuration'] for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.media_duration = EDIT_RATE * 7
        for child, omd in zip(_children_stitched(data), orig):
            assert child['mediaDuration'] == omd

    def test_set_speed_propagates(self):
        data = _stitched_media_data()
        orig_mds = [c['mediaDuration'] for c in _children_stitched(data)]
        clip = StitchedMedia(data)
        clip.set_speed(2.0)
        for child, orig_md in zip(_children_stitched(data), orig_mds):
            assert child['scalar'] == data['scalar']
            # Children keep their own mediaDuration, duration is recalculated
            assert child['mediaDuration'] == orig_md
            scalar = Fraction(str(child['scalar']))
            expected_dur = Fraction(str(orig_md)) * scalar
            assert Fraction(str(child['duration'])) == expected_dur
            assert child['metadata']['clipSpeedAttribute'] == data['metadata']['clipSpeedAttribute']

    def test_set_time_range_propagates_duration_proportionally(self):
        data = _stitched_media_data()
        old_durations = [c['duration'] for c in _children_stitched(data)]
        old_total = data['duration']
        clip = StitchedMedia(data)
        new_dur = seconds_to_ticks(3.0)
        clip.set_time_range(2.0, 3.0)
        ratio = Fraction(new_dur) / Fraction(old_total)
        for child, od in zip(_children_stitched(data), old_durations):
            assert child['duration'] == round(Fraction(od) * ratio)


# -- set_time_range and set_duration_seconds mediaStart propagation --

def _unified_media_with_media_start(media_start=0):
    return {
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0,
        'duration': EDIT_RATE, 'mediaDuration': EDIT_RATE,
        'mediaStart': media_start, 'scalar': 1,
        'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        'video': {
            '_type': 'VMFile', 'id': 2, 'src': 1, 'start': 0,
            'duration': EDIT_RATE, 'mediaDuration': EDIT_RATE,
            'mediaStart': 0, 'scalar': 1, 'trackNumber': 0,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        },
        'audio': {
            '_type': 'AMFile', 'id': 3, 'src': 1, 'start': 0,
            'duration': EDIT_RATE, 'mediaDuration': EDIT_RATE,
            'mediaStart': 0, 'scalar': 1, 'trackNumber': 0, 'channelNumber': 0,
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {}, 'attributes': {'gain': 1.0},
        },
    }


class TestSetTimeRangeMediaStartPropagation:
    def test_propagates_mediaStart_to_children(self):
        data = _unified_media_with_media_start(media_start=EDIT_RATE * 5)
        clip = UnifiedMedia(data)
        clip.set_time_range(2.0, 3.0)
        for key in ('video', 'audio'):
            assert data[key]['mediaStart'] == EDIT_RATE * 5


class TestSetDurationSecondsMediaStartPropagation:
    def test_propagates_mediaStart_to_children(self):
        data = _unified_media_with_media_start(media_start=EDIT_RATE * 3)
        clip = UnifiedMedia(data)
        clip.set_duration_seconds(4.0)
        for key in ('video', 'audio'):
            assert data[key]['mediaStart'] == EDIT_RATE * 3


class TestUnifiedMediaDurationSetterPropagatesMediaStart:
    def test_duration_setter_propagates_media_start(self):
        data = _unified_media_with_media_start(media_start=EDIT_RATE * 3)
        clip = UnifiedMedia(data)
        clip.duration = EDIT_RATE * 2
        for key in ('video', 'audio'):
            assert data[key]['mediaStart'] == EDIT_RATE * 3


class TestUnifiedMediaScalarSetterPropagatesMediaStart:
    def test_scalar_setter_propagates_media_start(self):
        from fractions import Fraction
        data = _unified_media_with_media_start(media_start=EDIT_RATE * 4)
        clip = UnifiedMedia(data)
        clip.scalar = Fraction(1, 2)
        for key in ('video', 'audio'):
            assert data[key]['mediaStart'] == EDIT_RATE * 4


class TestUnifiedMediaDurationPropertySetterPropagatesMediaStart:
    def test_media_duration_setter_does_not_overwrite_media_start(self):
        data = _unified_media_with_media_start(media_start=EDIT_RATE * 2)
        clip = UnifiedMedia(data)
        clip.media_duration = EDIT_RATE * 5
        for key in ('video', 'audio'):
            # Bug 2 fix: media_duration setter must NOT overwrite sub-clip mediaStart
            assert data[key]['mediaStart'] == 0


# ------------------------------------------------------------------
# Bug 3 & 4: duration/scalar setter — IMFile override on UnifiedMedia image sub-clips
# ------------------------------------------------------------------

def _unified_media_with_image_video():
    """UnifiedMedia with an IMFile video sub-clip (image)."""
    return {
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0,
        'duration': EDIT_RATE * 5, 'mediaDuration': 1,
        'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
        'metadata': {}, 'animationTracks': {},
        'video': {'_type': 'IMFile', 'id': 2, 'src': 1, 'start': 0,
                  'duration': EDIT_RATE * 5, 'mediaDuration': 1,
                  'mediaStart': 0, 'scalar': 1, 'trackNumber': 0,
                  'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
        'audio': None,
    }


class TestDurationSetterIMFileOverrideOnUnifiedMedia:
    def test_duration_setter_keeps_image_sub_clip_media_duration_1(self):
        """Bug 3: duration setter must keep mediaDuration=1 for IMFile sub-clips."""
        data = _unified_media_with_image_video()
        clip = UnifiedMedia(data)
        clip.duration = EDIT_RATE * 10
        assert data['video']['mediaDuration'] == 1

    def test_scalar_setter_keeps_image_sub_clip_media_duration_1(self):
        """Bug 4: scalar setter must keep mediaDuration=1 for IMFile sub-clips."""
        data = _unified_media_with_image_video()
        clip = UnifiedMedia(data)
        clip.scalar = Fraction(1, 2)
        assert data['video']['mediaDuration'] == 1
