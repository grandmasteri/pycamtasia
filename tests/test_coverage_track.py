"""Tests covering missing lines in track.py."""
from __future__ import annotations

from fractions import Fraction

import pytest
from camtasia.timing import seconds_to_ticks
from camtasia.timeline.track import Track, _propagate_start_to_unified
from camtasia.timeline.clips.base import BaseClip


def _track(medias=None, transitions=None, attrs=None):
    data = {'trackIndex': 0, 'medias': medias or [], 'transitions': transitions or []}
    return Track(attrs or {'ident': 'T'}, data, _all_tracks=[data])


def _media(id, start, dur, _type='VMFile', src=0, scalar=1, **kw):
    d = {'id': id, '_type': _type, 'src': src, 'start': start, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': scalar,
         'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
         'animationTracks': {}}
    d.update(kw)
    return d


# track.py:849 — add_lower_third scale override when param is not a dict
class TestAddLowerThirdScaleNotDict:
    def test_scale_plain_value(self):
        t = _track()
        clip = t.add_lower_third('Title', 'Sub', start_seconds=0, duration_seconds=5, scale=2.0)
        assert clip is not None
        # scale0/scale1 should be set as dicts
        params = clip._data.get('parameters', {})
        assert isinstance(params.get('scale0'), dict)
        assert params['scale0']['defaultValue'] == 2.0


# track.py:1224 — add_freeze_frame with zero scalar raises
class TestFreezeFrameZeroScalar:
    def test_raises(self):
        m = _media(1, 0, seconds_to_ticks(10), scalar=0)
        t = _track([m])
        source_clip = BaseClip(m)
        with pytest.raises(ValueError, match='zero scalar'):
            t.add_freeze_frame(source_clip, at_seconds=5.0, freeze_duration_seconds=2.0)


# track.py:1263 — extend_clip with zero scalar
class TestExtendClipZeroScalar:
    def test_zero_scalar_sets_media_duration(self):
        m = _media(1, 0, 1000, scalar=0)
        t = _track([m])
        t.extend_clip(1, extend_seconds=1.0)
        assert m['mediaDuration'] == m['duration']


# track.py:1265 — extend_clip IMFile guard
class TestExtendClipIMFile:
    def test_imfile_media_duration_1(self):
        m = _media(1, 0, 1000, _type='IMFile')
        t = _track([m])
        t.extend_clip(1, extend_seconds=1.0)
        assert m['mediaDuration'] == 1


# track.py:1267-1272 — extend_clip UnifiedMedia propagation
class TestExtendClipUnifiedMedia:
    def test_propagates_to_sub_clips(self):
        m = _media(1, 0, seconds_to_ticks(10), _type='UnifiedMedia')
        m['video'] = {'id': 10, '_type': 'VMFile', 'start': 0, 'duration': m['duration'],
                      'mediaDuration': m['mediaDuration'], 'mediaStart': 0, 'scalar': 1}
        m['audio'] = {'id': 11, '_type': 'AMFile', 'start': 0, 'duration': m['duration'],
                      'mediaDuration': m['mediaDuration'], 'mediaStart': 0, 'scalar': 1}
        t = _track([m])
        t.extend_clip(1, extend_seconds=2.0)
        assert m['video']['duration'] == m['duration']
        assert m['audio']['duration'] == m['duration']


# track.py:1727 — trim_clip IMFile guard and UnifiedMedia propagation
class TestTrimClipIMFileAndUnifiedMedia:
    def test_imfile_media_duration_set_to_1(self):
        m = _media(1, 0, seconds_to_ticks(10), _type='IMFile')
        t = _track([m])
        t.trim_clip(1, trim_end_seconds=2.0)
        assert m['mediaDuration'] == 1

    def test_unified_media_propagates_to_sub_clips(self):
        m = _media(1, 0, seconds_to_ticks(10), _type='UnifiedMedia')
        m['video'] = {'id': 10, '_type': 'VMFile', 'start': 0, 'duration': m['duration'],
                      'mediaDuration': m['mediaDuration'], 'mediaStart': 0, 'scalar': 1}
        m['audio'] = {'id': 11, '_type': 'AMFile', 'start': 0, 'duration': m['duration'],
                      'mediaDuration': m['mediaDuration'], 'mediaStart': 0, 'scalar': 1}
        t = _track([m])
        t.trim_clip(1, trim_end_seconds=2.0)
        expected_dur = m['duration']
        assert m['video']['duration'] == expected_dur
        assert m['audio']['duration'] == expected_dur
        assert m['video']['mediaStart'] == m['mediaStart']


# track.py:1955-1971 — merge_adjacent validations
class TestMergeAdjacentValidations:
    def test_not_adjacent(self):
        a = _media(1, 0, 100, src=1)
        b = _media(2, 200, 100, src=1)  # gap between
        t = _track([a, b])
        with pytest.raises(ValueError, match='not adjacent'):
            t.merge_adjacent_clips(1, 2)

    def test_different_sources(self):
        a = _media(1, 0, 100, src=1)
        b = _media(2, 100, 100, src=2)
        t = _track([a, b])
        with pytest.raises(ValueError, match='different sources'):
            t.merge_adjacent_clips(1, 2)

    def test_different_types(self):
        a = _media(1, 0, 100, src=1, _type='VMFile')
        b = _media(2, 100, 100, src=1, _type='AMFile')
        b['channelNumber'] = '0'
        t = _track([a, b])
        with pytest.raises(ValueError, match='different types'):
            t.merge_adjacent_clips(1, 2)

    def test_different_track_numbers(self):
        a = _media(1, 0, 100, src=1, trackNumber=0)
        b = _media(2, 100, 100, src=1, trackNumber=1)
        t = _track([a, b])
        with pytest.raises(ValueError, match='different source tracks'):
            t.merge_adjacent_clips(1, 2)

    def test_different_scalars(self):
        a = _media(1, 0, 100, src=1, scalar=1)
        b = _media(2, 100, 100, src=1, scalar='1/2')
        t = _track([a, b])
        with pytest.raises(ValueError, match='different scalars'):
            t.merge_adjacent_clips(1, 2)

    def test_not_contiguous_in_source(self):
        a = _media(1, 0, 100, src=1, mediaStart=0, mediaDuration=100)
        b = _media(2, 100, 100, src=1, mediaStart=200, mediaDuration=100)  # gap in source
        t = _track([a, b])
        with pytest.raises(ValueError, match='not contiguous'):
            t.merge_adjacent_clips(1, 2)

    def test_swap_order(self):
        """When b comes before a in timeline, they should be swapped."""
        a = _media(1, 0, 100, src=1, mediaStart=0, mediaDuration=100)
        b = _media(2, 100, 100, src=1, mediaStart=100, mediaDuration=100)
        t = _track([a, b])
        # Pass in reverse order — should swap internally
        result = t.merge_adjacent_clips(2, 1)
        assert result.duration == 200


# track.py:2208-2209 — insert_gap shifts transitions
class TestInsertGapShiftsTransitions:
    def test_transitions_shifted(self):
        m1 = _media(1, 0, 100)
        m2 = _media(2, 100, 100)
        trans = {'start': 100, 'duration': 10, 'leftMedia': 1, 'rightMedia': 2}
        t = _track([m1, m2], [trans])
        t.insert_gap(at_seconds=0.0, gap_duration_seconds=1.0)
        gap_ticks = seconds_to_ticks(1.0)
        assert trans['start'] == 100 + gap_ticks


# track.py:2270-2271,2280 — scale_all_durations IMFile guard and transition scaling
class TestScaleAllDurationsIMFile:
    def test_imfile_gets_media_duration_1(self):
        m = _media(1, 0, 1000, _type='IMFile')
        trans = {'duration': 100}
        t = _track([m], [trans])
        t.scale_all_durations(2.0)
        assert m['mediaDuration'] == 1
        assert m['scalar'] == 1
        assert trans['duration'] == 200


# track.py:2273-2278 — scale_all_durations UnifiedMedia propagation
class TestScaleAllDurationsUnifiedMedia:
    def test_propagates_to_sub_clips(self):
        m = _media(1, 0, 1000, _type='UnifiedMedia')
        m['video'] = {'id': 10, '_type': 'VMFile', 'start': 0, 'duration': 1000,
                      'mediaDuration': 1000, 'mediaStart': 0, 'scalar': 1}
        m['audio'] = {'id': 11, '_type': 'AMFile', 'start': 0, 'duration': 1000,
                      'mediaDuration': 1000, 'mediaStart': 0, 'scalar': 1}
        t = _track([m])
        t.scale_all_durations(2.0)
        assert m['video']['duration'] == m['duration']
        assert m['audio']['duration'] == m['duration']


# track.py:2353,2355 — marker filtering (before start, beyond end)
class TestMarkerFiltering:
    def test_markers_outside_range_filtered(self):
        m = _media(1, 0, 1000)
        m['mediaStart'] = 100
        m['mediaDuration'] = 500
        m['parameters']['toc'] = {'keyframes': [
            {'time': 50, 'value': 'before'},   # media_offset = 50 - 100 = -50 < 0
            {'time': 200, 'value': 'inside'},   # media_offset = 200 - 100 = 100, < 500
            {'time': 700, 'value': 'beyond'},   # media_offset = 700 - 100 = 600, >= 500
        ]}
        t = _track([m])
        # Access markers through the Track's clips iterator which attaches _PerMediaMarkers
        clip = list(t.clips)[0]
        markers = list(clip.markers)
        names = [mk.name for mk in markers]
        assert 'before' not in names
        assert 'beyond' not in names
        assert 'inside' in names


# track.py:1865,1867-1872 — split_clip IMFile and UnifiedMedia (left half)
class TestSplitClipIMFileAndUnifiedMedia:
    def test_imfile_split(self):
        m = _media(1, 0, seconds_to_ticks(10), _type='IMFile')
        t = _track([m])
        left, right = t.split_clip(1, split_at_seconds=5.0)
        assert left._data['mediaDuration'] == 1
        assert right._data['mediaDuration'] == 1

    def test_unified_media_split(self):
        m = _media(1, 0, seconds_to_ticks(10), _type='UnifiedMedia')
        m['video'] = {'id': 10, '_type': 'VMFile', 'start': 0, 'duration': m['duration'],
                      'mediaDuration': m['mediaDuration'], 'mediaStart': 0, 'scalar': 1}
        m['audio'] = {'id': 11, '_type': 'AMFile', 'start': 0, 'duration': m['duration'],
                      'mediaDuration': m['mediaDuration'], 'mediaStart': 0, 'scalar': 1}
        t = _track([m])
        left, right = t.split_clip(1, split_at_seconds=5.0)
        # Left half sub-clips should be propagated
        assert left._data['video']['duration'] == left._data['duration']
        # Right half sub-clips should be propagated
        assert right._data['video']['duration'] == right._data['duration']
        assert right._data['audio']['start'] == right._data['start']


# track.py:1977 — merge_adjacent_clips IMFile guard
class TestMergeAdjacentIMFile:
    def test_imfile_merge(self):
        a = _media(1, 0, 100, _type='IMFile', src=1, mediaStart=0, mediaDuration=1)
        b = _media(2, 100, 100, _type='IMFile', src=1, mediaStart=1, mediaDuration=1)
        t = _track([a, b])
        result = t.merge_adjacent_clips(1, 2)
        assert result._data['mediaDuration'] == 1


# track.py:394 — add_clip with None source_id for media file type
class TestAddClipNoneSourceId:
    def test_warns_and_uses_src_0(self):
        import warnings
        t = _track()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            clip = t.add_clip('VMFile', None, 0, 100)
            assert any('source_id is None' in str(warning.message) for warning in w)
            assert clip._data['src'] == 0


# track.py:402 — add_clip with id=-1 sentinel
class TestAddClipIdSentinel:
    def test_reassigns_id(self):
        t = _track()
        # Clone produces id=-1; simulate by passing id=-1 in kwargs
        clip = t.add_clip('VMFile', 0, 0, 100, id=-1)
        assert clip.id != -1
