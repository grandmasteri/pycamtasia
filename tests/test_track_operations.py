"""Tests for track operations, attributes, protocols, and clip helpers."""
from __future__ import annotations

from typing import Any
import warnings

import pytest

from camtasia.timeline.clips import AMFile, Callout, IMFile, VMFile
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.track import (
    _VALID_CLIP_TYPES,
    Track,
    _PerMediaMarkers,
)
from camtasia.timing import EDIT_RATE, seconds_to_ticks


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
        clip = next(iter(t.clips))
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


# track.py:1182,1184,1186 — add_image_sequence validation errors
class TestAddImageSequenceValidation:
    def test_transition_ge_duration_raises(self):
        t = _track()
        with pytest.raises(ValueError, match=r'transition_seconds.*must be less than'):
            t.add_image_sequence([1, 2], 0, duration_per_image_seconds=5.0, transition_seconds=5.0)

    def test_negative_transition_raises(self):
        t = _track()
        with pytest.raises(ValueError, match='transition_seconds must be non-negative'):
            t.add_image_sequence([1, 2], 0, duration_per_image_seconds=5.0, transition_seconds=-1.0)


# track.py:1231,1233,1238 — add_freeze_frame validation errors
class TestAddFreezeFrameValidation:
    def test_no_source_id_raises(self):
        t = _track()
        clip = t.add_clip('Callout', None, 0, seconds_to_ticks(10.0))
        with pytest.raises(ValueError, match='source_clip has no source ID'):
            t.add_freeze_frame(clip, at_seconds=5.0, freeze_duration_seconds=2.0)

    def test_before_clip_start_raises(self):
        t = _track()
        clip = t.add_clip('VMFile', 1, seconds_to_ticks(5.0), seconds_to_ticks(10.0))
        with pytest.raises(ValueError, match=r'at_seconds.*is before source_clip start'):
            t.add_freeze_frame(clip, at_seconds=3.0, freeze_duration_seconds=2.0)

    def test_past_clip_end_raises(self):
        t = _track()
        clip = t.add_clip('VMFile', 1, seconds_to_ticks(5.0), seconds_to_ticks(10.0))
        with pytest.raises(ValueError, match=r'at_seconds.*is past the end'):
            t.add_freeze_frame(clip, at_seconds=16.0, freeze_duration_seconds=2.0)


# track.py:2406 — _max_clip_id recursion into StitchedMedia sub-clips
class TestMaxClipIdWithStitchedSubClips:
    def test_next_clip_id_accounts_for_stitched_sub_clips(self):
        """Ensure _next_clip_id finds IDs inside StitchedMedia.medias."""
        stitched = _media(10, 0, seconds_to_ticks(10.0), _type='StitchedMedia')
        stitched['medias'] = [
            {'id': 50, '_type': 'VMFile', 'src': 1, 'start': 0,
             'duration': seconds_to_ticks(5.0), 'mediaStart': 0,
             'mediaDuration': seconds_to_ticks(5.0), 'scalar': 1},
        ]
        t = _track(medias=[stitched])
        # _next_clip_id should be > 50 (the sub-clip ID)
        next_id = t._next_clip_id()
        assert next_id > 50


# ── Merged from test_track_coverage.py ───────────────────────────────


def _coverage_track(
    index: int = 0,
    name: str = "Test",
    medias: list[dict] | None = None,
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
        "transitions": [],
        "parameters": {},
    }
    return Track(attrs, data)


class TestTrackAttributeFlags:
    def test_audio_muted_getter_and_setter(self):
        track = _coverage_track()
        assert track.audio_muted is False
        track.audio_muted = True
        assert track.audio_muted is True

    def test_video_hidden_getter_and_setter(self):
        track = _coverage_track()
        assert track.video_hidden is False
        track.video_hidden = True
        assert track.video_hidden is True

    def test_magnetic_getter_and_setter(self):
        track = _coverage_track()
        assert track.magnetic is False
        track.magnetic = True
        assert track.magnetic is True

    def test_solo_getter_and_setter(self):
        track = _coverage_track()
        assert track.solo is False
        track.solo = True
        assert track.solo is True

    def test_is_locked_getter_and_setter(self):
        track = _coverage_track()
        assert track.is_locked is False
        track.is_locked = True
        assert track.is_locked is True


class TestTrackClipIteration:
    def test_medias_alias_returns_same_as_clips(self):
        track = _coverage_track()
        track.add_clip("IMFile", 1, 0, EDIT_RATE)
        actual_via_clips = [c.id for c in track.clips]
        actual_via_medias = [c.id for c in track.medias]
        assert actual_via_clips == actual_via_medias


class TestTrackAddVideo:
    def test_add_video_returns_vmfile(self):
        track = _coverage_track()
        actual_clip = track.add_video(source_id=10, start_seconds=1.0, duration_seconds=5.0)
        assert isinstance(actual_clip, VMFile)
        assert actual_clip.start == seconds_to_ticks(1.0)
        assert actual_clip.duration == seconds_to_ticks(5.0)


class TestTrackAddAudio:
    def test_add_audio_returns_amfile(self):
        track = _coverage_track()
        actual_clip = track.add_audio(source_id=20, start_seconds=0.0, duration_seconds=3.0)
        assert isinstance(actual_clip, AMFile)
        assert actual_clip.start == 0
        assert actual_clip.duration == seconds_to_ticks(3.0)


class TestTrackAddCallout:
    def test_add_callout_returns_callout(self):
        track = _coverage_track()
        actual_clip = track.add_callout(
            text="Hello World",
            start_seconds=2.0,
            duration_seconds=4.0,
        )
        assert isinstance(actual_clip, Callout)
        assert actual_clip.start == seconds_to_ticks(2.0)
        assert actual_clip.duration == seconds_to_ticks(4.0)


class TestTrackTransitions:
    def test_add_transition(self):
        track = _coverage_track()
        clip_a = track.add_image(1, 0.0, 5.0)
        clip_b = track.add_image(2, 5.0, 5.0)
        actual_transition = track.add_transition("FadeThroughBlack", clip_a, clip_b, 0.5)
        assert actual_transition.name == "FadeThroughBlack"
        assert actual_transition.left_media_id == clip_a.id
        assert actual_transition.right_media_id == clip_b.id

    def test_add_fade_through_black(self):
        track = _coverage_track()
        clip_a = track.add_image(1, 0.0, 5.0)
        clip_b = track.add_image(2, 5.0, 5.0)
        actual_transition = track.add_fade_through_black(clip_a, clip_b, 1.0)
        assert actual_transition.name == "FadeThroughBlack"
        assert actual_transition.duration == seconds_to_ticks(1.0)


class TestTrackImageSequence:
    def test_creates_clips_without_transitions(self):
        track = _coverage_track()
        actual_clips = track.add_image_sequence([1, 2, 3], start_seconds=0.0, duration_per_image_seconds=2.0)
        assert all(isinstance(c, IMFile) for c in actual_clips)
        actual_starts = [c.start for c in actual_clips]
        assert actual_starts == [seconds_to_ticks(0.0), seconds_to_ticks(2.0), seconds_to_ticks(4.0)]

    def test_creates_clips_with_transitions(self):
        track = _coverage_track()
        actual_clips = track.add_image_sequence(
            [1, 2, 3], start_seconds=0.0,
            duration_per_image_seconds=2.0, transition_seconds=0.5,
        )
        assert [type(c).__name__ for c in actual_clips] == ['IMFile', 'IMFile', 'IMFile']
        actual_transitions = list(track.transitions)
        assert [t.name for t in actual_transitions] == ["FadeThroughBlack", "FadeThroughBlack"]


class TestTrackEndTime:
    def test_empty_track_returns_zero(self):
        track = _coverage_track()
        assert track.end_time_seconds() == 0.0

    def test_returns_max_clip_end(self):
        track = _coverage_track()
        track.add_image(1, 0.0, 5.0)
        track.add_image(2, 5.0, 3.0)
        assert track.end_time_seconds() == pytest.approx(8.0)


class TestTrackRemoveClip:
    def test_remove_clip_by_id(self):
        track = _coverage_track()
        clip = track.add_image(1, 0.0, 5.0)
        track.remove_clip(clip.id)
        assert list(track.clips) == []

    def test_remove_nonexistent_clip_raises(self):
        track = _coverage_track()
        with pytest.raises(KeyError, match="No clip with id=999"):
            track.remove_clip(999)


class TestTrackMarkers:
    def test_track_markers_property(self):
        track = _coverage_track()
        assert list(track.markers) == []


class TestTrackRepr:
    def test_repr(self):
        track = _coverage_track(index=2, name="My Track")
        assert repr(track) == "Track(name='My Track', index=2)"


class TestPerMediaMarkers:
    def test_iterates_markers_with_adjusted_times(self):
        media_data = {
            "start": 1000,
            "mediaStart": 500,
            "parameters": {
                "toc": {
                    "keyframes": [
                        {"time": 600, "value": "Marker A"},
                        {"time": 800, "value": "Marker B"},
                    ]
                }
            },
        }
        markers = _PerMediaMarkers(media_data)
        actual_markers = list(markers)
        assert [(m.name, m.time) for m in actual_markers] == [
            ("Marker A", 1000 + (600 - 500)),
            ("Marker B", 1000 + (800 - 500)),
        ]

    def test_len(self):
        media_data = {
            "parameters": {
                "toc": {
                    "keyframes": [{"time": 0, "value": "M1"}]
                }
            }
        }
        markers = list(_PerMediaMarkers(media_data))
        assert [m.name for m in markers] == ["M1"]

    def test_empty_markers(self):
        assert list(_PerMediaMarkers({})) == []


class TestClipAccessorMarkers:
    def test_clip_has_per_media_markers(self):
        """Clips yielded by track.clips should have markers attached."""
        attrs = {"ident": "T", "audioMuted": False, "videoHidden": False,
                 "magnetic": False, "metadata": {"IsLocked": "False"}}
        data = {
            "trackIndex": 0,
            "medias": [{
                "_type": "IMFile", "id": 1, "start": 0, "duration": EDIT_RATE,
                "mediaStart": 0, "mediaDuration": EDIT_RATE, "scalar": 1,
                "src": 1, "metadata": {}, "animationTracks": {}, "effects": [],
                "parameters": {
                    "toc": {"keyframes": [{"time": 100, "value": "Mark"}]}
                },
            }],
            "transitions": [],
        }
        track = Track(attrs, data)
        actual_clip = next(iter(track.clips))
        actual_markers = list(actual_clip.markers)
        assert actual_markers[0].name == "Mark"


class TestTitlePresetUnknown:
    def test_unknown_preset_raises(self):
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        data = {'trackIndex': 0, 'medias': []}
        track = Track(attrs, data)
        with pytest.raises(ValueError, match='Unknown title preset'):
            track.add_title('Hello', 0, 5, preset='nonexistent')


class TestSetSegmentSpeedsMissingClip:
    def test_missing_clip_raises(self):
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        data = {'trackIndex': 0, 'medias': []}
        track = Track(attrs, data)
        with pytest.raises(KeyError, match='No clip with id=999'):
            track.set_segment_speeds(999, [(30, 1.0)])


class TestSplitClipMissingClip:
    def test_missing_clip_raises(self):
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        data = {'trackIndex': 0, 'medias': []}
        track = Track(attrs, data)
        with pytest.raises(KeyError, match='No clip with id=999'):
            track.split_clip(999, 5.0)


class TestSplitClipOutOfRange:
    def test_split_before_clip_raises(self):
        clip = {
            'id': 1, '_type': 'VMFile', 'src': 1, 'trackNumber': 0,
            'start': seconds_to_ticks(10.0), 'duration': seconds_to_ticks(10.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(10.0),
            'scalar': 1, 'metadata': {}, 'parameters': {}, 'effects': [],
            'animationTracks': {},
        }
        attrs = {'ident': 'test', 'audioMuted': False, 'videoHidden': False}
        data = {'trackIndex': 0, 'medias': [clip]}
        track = Track(attrs, data)
        with pytest.raises(ValueError, match='outside clip range'):
            track.split_clip(1, 5.0)


# ── Merged from test_feature_gaps_3_6.py ─────────────────────────────


class TestTrackRemoveAllClips:
    def test_remove_all_clips_returns_count(self, project):
        track = project.timeline.tracks[0]
        track.add_video(1, 0, 5)
        track.add_video(1, 5, 5)
        track.add_audio(1, 10, 5)
        assert track.remove_all_clips() == 3

    def test_remove_all_clips_empties_track(self, project):
        track = project.timeline.tracks[0]
        track.add_video(1, 0, 5)
        track.add_video(1, 5, 5)
        track.remove_all_clips()
        assert len(track) == 0
        assert track.is_empty

    def test_remove_all_clips_clears_transitions(self, project):
        track = project.timeline.tracks[0]
        c1 = track.add_video(1, 0, 5)
        c2 = track.add_video(1, 5, 5)
        track.transitions.add('FadeThroughBlack', c1.id, c2.id, 100_000)
        track.remove_all_clips()
        assert len(track.transitions) == 0

    def test_remove_all_clips_on_empty_returns_zero(self, project):
        track = project.timeline.tracks[0]
        assert track.remove_all_clips() == 0

    def test_remove_all_clips_preserves_track_identity(self, project):
        track = project.timeline.tracks[0]
        track.name = 'MyTrack'
        track.add_video(1, 0, 5)
        track.remove_all_clips()
        assert track.name == 'MyTrack'
        assert track.index == project.timeline.tracks[0].index


class TestTrackClearWithGroupTransitions:
    def test_clear_removes_group_internal_transitions(self):
        """clear() removes transitions from Group clips' internal tracks."""
        group_media = {
            'id': 1, '_type': 'Group', 'start': 0, 'duration': 100,
            'tracks': [
                {'trackIndex': 0, 'medias': [{'id': 10, '_type': 'VMFile', 'start': 0, 'duration': 50}],
                 'transitions': [{'name': 'Fade', 'duration': 10, 'leftMedia': 10, 'rightMedia': 11}]},
            ],
        }
        data = {'trackIndex': 0, 'medias': [group_media], 'transitions': []}
        track = Track({'ident': 'test'}, data)
        track.clear()
        assert data['medias'] == []


# ── Merged from test_track_protocols.py ──────────────────────────────


def _proto_track(medias=None, index=0):
    data = {"trackIndex": index, "medias": medias or []}
    attrs = {"ident": f"Track-{index}"}
    return Track(attrs, data)


def _proto_track_with_clips(n=2, index=0):
    medias = [
        {"id": i + 1, "_type": "IMFile", "src": 10 + i, "trackNumber": 0,
         "start": i * 1000, "duration": 1000, "mediaStart": 0,
         "mediaDuration": 1, "scalar": 1, "metadata": {},
         "animationTracks": {}, "parameters": {}, "effects": []}
        for i in range(n)
    ]
    return _proto_track(medias=medias, index=index)


class TestTrackEqHash:
    def test_same_data_object_is_equal(self):
        data = {"trackIndex": 0, "medias": []}
        t1 = Track({"ident": "A"}, data)
        t2 = Track({"ident": "B"}, data)
        assert t1 == t2

    def test_same_index_different_data_is_equal(self):
        t1 = _proto_track(index=3)
        t2 = _proto_track(index=3)
        assert t1 == t2

    def test_different_index_not_equal(self):
        t1 = _proto_track(index=0)
        t2 = _proto_track(index=1)
        assert t1 != t2

    def test_not_equal_to_non_track(self):
        t = _proto_track()
        assert t != "not a track"

    def test_hash_same_index(self):
        t1 = _proto_track(index=5)
        t2 = _proto_track(index=5)
        assert hash(t1) == hash(t2)

    def test_usable_in_set(self):
        t1 = _proto_track(index=0)
        t2 = _proto_track(index=0)
        assert {t1, t2} == {t1}


class TestTrackLen:
    def test_empty_track(self):
        t = _proto_track()
        assert len(t) == 0

    def test_track_with_clips(self):
        t = _proto_track_with_clips(3)
        assert len(t) == 3
        assert [c.id for c in t.clips] == [1, 2, 3]

    def test_no_medias_key(self):
        data = {"trackIndex": 0}
        t = Track({"ident": "X"}, data)
        assert len(t) == 0


class TestClipCount:
    def test_matches_len(self):
        t = _proto_track_with_clips(4)
        assert t.clip_count == len(t) == 4

    def test_empty(self):
        t = _proto_track()
        assert t.clip_count == 0


class TestFindClip:
    def test_found(self):
        t = _proto_track_with_clips(3)
        clip = t.find_clip(2)
        assert clip is not None
        assert clip.id == 2

    def test_not_found(self):
        t = _proto_track_with_clips(3)
        assert t.find_clip(999) is None


class TestAddClipValidation:
    def test_invalid_type_raises(self):
        t = _proto_track()
        with pytest.raises(ValueError, match="Unknown clip type 'Bogus'"):
            t.add_clip("Bogus", 1, 0, 1000)

    @pytest.mark.parametrize("clip_type", sorted(_VALID_CLIP_TYPES))
    def test_valid_types_accepted(self, clip_type):
        t = _proto_track()
        source_id = None if clip_type in ("Callout", "Group") else 1
        clip = t.add_clip(clip_type, source_id, 0, 1000)
        assert clip is not None


class TestTrackIter:
    def test_track_iter(self):
        t = _proto_track_with_clips(3)
        clips = list(t)
        assert [c.id for c in clips] == [1, 2, 3]


class TestTrackContains:
    def test_track_contains_by_id(self):
        t = _proto_track_with_clips(2)
        assert 1 in t

    def test_track_contains_by_clip(self):
        t = _proto_track_with_clips(2)
        clip = next(iter(t.clips))
        assert clip in t

    def test_track_not_contains(self):
        t = _proto_track_with_clips(2)
        assert 999 not in t

    def test_track_contains_non_clip_returns_false(self):
        t = _proto_track_with_clips(2)
        assert ("not a clip" in t) is False


class TestExtendClipTrimsEffects:
    """Bug 14: extend_clip should trim effects when shortening a clip."""

    def test_shorten_trims_effects_past_new_duration(self):
        from camtasia.timing import seconds_to_ticks
        attrs: dict[str, Any] = {"ident": "Track 1"}
        data: dict[str, Any] = {"trackIndex": 0, "medias": []}
        track = Track(attrs, data)
        clip = track.add_callout("A", 0, 10.0)
        m = track._data["medias"][0]
        m["effects"] = [
            {"start": 0, "duration": seconds_to_ticks(3.0), "name": "early"},
            {"start": seconds_to_ticks(8.0), "duration": seconds_to_ticks(2.0), "name": "late"},
        ]

        track.extend_clip(clip.id, extend_seconds=-4.0)  # new duration = 6s

        effects = m["effects"]
        early = [e for e in effects if e.get("name") == "early"]
        assert len(early) == 1, "Effect within new duration should be kept"
        late = [e for e in effects if e.get("name") == "late"]
        assert len(late) == 0, "Effect past new duration should be removed"


# Bug 15: add_image_sequence uses integer tick arithmetic to avoid drift

class TestImageSequenceNoDrift:
    def test_no_floating_point_drift_over_many_images(self):
        from camtasia.timing import seconds_to_ticks
        attrs: dict[str, Any] = {"ident": "Track 1"}
        data: dict[str, Any] = {"trackIndex": 0, "medias": [], "transitions": []}
        track = Track(attrs, data)

        # Use values that cause float drift: 1/3 second transitions
        clips = track.add_image_sequence(
            list(range(1, 21)),  # 20 images
            start_seconds=0.0,
            duration_per_image_seconds=3.0,
            transition_seconds=1.0,
        )
        # Each image after the first should start at (3-1)*i ticks from start
        duration_ticks = seconds_to_ticks(3.0)
        transition_ticks = seconds_to_ticks(1.0)
        for i, clip in enumerate(clips):
            expected = i * (duration_ticks - transition_ticks)
            assert clip.start == expected, (
                f"Clip {i}: expected start {expected}, got {clip.start} (drift detected)"
            )


# -- Bug: add_image_sequence must use integer ticks to avoid cumulative drift --

def test_add_image_sequence_no_cumulative_drift() -> None:
    """add_image_sequence should not accumulate floating-point drift across many images."""
    track = _track()
    # Use a duration that doesn't convert cleanly to avoid drift
    clips = track.add_image_sequence(
        list(range(1, 21)),  # 20 images
        start_seconds=0.0,
        duration_per_image_seconds=3.0,
    )
    duration_ticks = seconds_to_ticks(3.0)
    for i, clip in enumerate(clips):
        expected = i * duration_ticks
        assert clip.start == expected, (
            f"Clip {i}: expected start {expected}, got {clip.start} (drift detected)"
        )
