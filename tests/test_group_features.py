"""Tests for Group introspection features: all_internal_clips, internal_clip_types,
has_audio, has_video, internal_duration_seconds, find_internal_clips_by_type.
"""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from camtasia.timeline.clips import AMFile, BaseClip, Group, GroupTrack, IMFile
from camtasia.timing import seconds_to_ticks
from camtasia.types import ClipType


def _make_group(tracks_data: list[list[dict]]) -> Group:
    """Build a Group from a list of track media lists."""
    tracks = []
    for track_index, medias in enumerate(tracks_data):
        tracks.append({
            'trackIndex': track_index,
            'medias': medias,
            'transitions': [],
        })
    return Group({
        '_type': 'Group',
        'id': 1,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(10.0),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
        'attributes': {'ident': 'TestGroup'},
        'tracks': tracks,
    })


def _clip_data(clip_type: str, clip_id: int, start_s: float, dur_s: float, src: int = 1) -> dict:
    """Build minimal clip data dict."""
    return {
        '_type': clip_type,
        'id': clip_id,
        'src': src,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
    }


@pytest.fixture
def video_audio_group() -> Group:
    """Group with one video clip and one audio clip on separate tracks."""
    return _make_group([
        [_clip_data('VMFile', 10, 0.0, 5.0)],
        [_clip_data('AMFile', 11, 0.0, 3.0)],
    ])


@pytest.fixture
def video_only_group() -> Group:
    """Group with only video clips."""
    return _make_group([
        [_clip_data('VMFile', 10, 0.0, 4.0), _clip_data('VMFile', 11, 4.0, 2.0)],
    ])


@pytest.fixture
def empty_group() -> Group:
    """Group with no internal tracks."""
    return _make_group([[]])


@pytest.fixture
def multi_type_group() -> Group:
    """Group with video, audio, and image clips."""
    return _make_group([
        [_clip_data('VMFile', 10, 0.0, 5.0), _clip_data('IMFile', 11, 5.0, 2.0)],
        [_clip_data('AMFile', 12, 0.0, 7.0)],
    ])


class TestAllInternalClips:
    """Group.all_internal_clips returns a flat list of all clips."""

    def test_returns_all_clips_across_tracks(self, video_audio_group: Group) -> None:
        all_clips: list[BaseClip] = video_audio_group.all_internal_clips
        assert [c.clip_type for c in all_clips] == ['VMFile', 'AMFile']

    def test_empty_group_returns_empty_list(self, empty_group: Group) -> None:
        assert empty_group.all_internal_clips == []

    def test_multi_type_group_count(self, multi_type_group: Group) -> None:
        assert [c.clip_type for c in multi_type_group.all_internal_clips] == ['VMFile', 'IMFile', 'AMFile']


class TestInternalClipTypes:
    """Group.internal_clip_types returns unique clip type strings."""

    def test_single_type(self, video_only_group: Group) -> None:
        assert video_only_group.internal_clip_types == {'VMFile'}

    def test_multiple_types(self, multi_type_group: Group) -> None:
        assert multi_type_group.internal_clip_types == {'VMFile', 'IMFile', 'AMFile'}

    def test_empty_group(self, empty_group: Group) -> None:
        assert empty_group.internal_clip_types == set()

    def test_returns_set(self, video_audio_group: Group) -> None:
        result: set[str] = video_audio_group.internal_clip_types
        assert result == {'VMFile', 'AMFile'}


class TestHasAudio:
    """Group.has_audio detects audio clips."""

    def test_true_when_audio_present(self, video_audio_group: Group) -> None:
        assert video_audio_group.has_audio is True

    def test_false_when_no_audio(self, video_only_group: Group) -> None:
        assert video_only_group.has_audio is False

    def test_false_for_empty_group(self, empty_group: Group) -> None:
        assert empty_group.has_audio is False

    def test_true_with_multi_type(self, multi_type_group: Group) -> None:
        assert multi_type_group.has_audio is True


class TestHasVideo:
    """Group.has_video detects video clips."""

    def test_true_when_video_present(self, video_audio_group: Group) -> None:
        assert video_audio_group.has_video is True

    def test_true_for_video_only(self, video_only_group: Group) -> None:
        assert video_only_group.has_video is True

    def test_false_for_empty_group(self, empty_group: Group) -> None:
        assert empty_group.has_video is False

    def test_audio_only_group_has_no_video(self) -> None:
        audio_only: Group = _make_group([
            [_clip_data('AMFile', 10, 0.0, 3.0)],
        ])
        assert audio_only.has_video is False


class TestInternalDurationSeconds:
    """Group.internal_duration_seconds computes max end across all tracks."""

    def test_single_track_duration(self, video_only_group: Group) -> None:
        # Two clips: 0-4s and 4-6s → max end = 6s
        assert video_only_group.internal_duration_seconds == pytest.approx(6.0)

    def test_multi_track_takes_longest(self, video_audio_group: Group) -> None:
        # Track 0: 0-5s, Track 1: 0-3s → max end = 5s
        assert video_audio_group.internal_duration_seconds == pytest.approx(5.0)

    def test_empty_group_returns_zero(self, empty_group: Group) -> None:
        assert empty_group.internal_duration_seconds == 0.0

    def test_multi_type_group_duration(self, multi_type_group: Group) -> None:
        # Track 0: 0-5s + 5-7s = 7s, Track 1: 0-7s = 7s → max end = 7s
        assert multi_type_group.internal_duration_seconds == pytest.approx(7.0)


class TestFindInternalClipsByType:
    """Group.find_internal_clips_by_type filters by clip type."""

    def test_find_by_string(self, multi_type_group: Group) -> None:
        video_clips: list[BaseClip] = multi_type_group.find_internal_clips_by_type('VMFile')
        assert [c.clip_type for c in video_clips] == ['VMFile']

    def test_find_by_clip_type_enum(self, multi_type_group: Group) -> None:
        audio_clips: list[BaseClip] = multi_type_group.find_internal_clips_by_type(ClipType.AUDIO)
        assert [c.clip_type for c in audio_clips] == ['AMFile']

    def test_no_matches_returns_empty(self, video_only_group: Group) -> None:
        assert video_only_group.find_internal_clips_by_type('AMFile') == []

    def test_empty_group_returns_empty(self, empty_group: Group) -> None:
        assert empty_group.find_internal_clips_by_type('VMFile') == []

    def test_multiple_matches(self, video_only_group: Group) -> None:
        video_clips: list[BaseClip] = video_only_group.find_internal_clips_by_type('VMFile')
        assert [c.clip_type for c in video_clips] == ['VMFile', 'VMFile']

    def test_find_image_clips(self, multi_type_group: Group) -> None:
        image_clips: list[BaseClip] = multi_type_group.find_internal_clips_by_type(ClipType.IMAGE)
        assert [c.clip_type for c in image_clips] == ['IMFile']


class TestGroupDescribe:
    def test_group_to_dict(self):
        """Group clips should have a working to_dict() method."""
        group = _make_group([[_clip_data('VMFile', 1, 0, 100)]])
        actual_dict: dict = group.to_dict()
        assert actual_dict['type'] == 'Group'
        assert actual_dict['id'] == 1


class TestGroupTrackOperations:
    def test_group_track_len(self):
        track_data = {'trackIndex': 0, 'medias': [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
            {'id': 2, '_type': 'AMFile', 'start': 100, 'duration': 200},
        ], 'transitions': [], 'parameters': {}, 'ident': '',
           'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False}
        gt = GroupTrack(track_data)
        assert [c.id for c in gt] == [1, 2]

    def test_group_track_iter(self):
        track_data = {'trackIndex': 0, 'medias': [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
        ], 'transitions': [], 'parameters': {}, 'ident': '',
           'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False}
        gt = GroupTrack(track_data)
        clips = list(gt)
        assert [c.id for c in clips] == [1]

    def test_group_track_repr(self):
        track_data = {'trackIndex': 0, 'medias': [], 'transitions': [], 'parameters': {}, 'ident': '',
           'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False}
        gt = GroupTrack(track_data)
        assert 'GroupTrack' in repr(gt)


class TestGroupEdgeCases:
    def test_empty_group_clip_count(self):
        group = _make_group([[]])
        assert group.clip_count == 0

    def test_group_set_dimensions_and_check(self):
        group = _make_group([[_clip_data('VMFile', 1, 0, 100)]])
        group.set_dimensions(1920.0, 1080.0)
        assert group.width == 1920.0
        assert group.height == 1080.0

    def test_group_no_tracks_internal_duration(self):
        group = Group({
            '_type': 'Group', 'id': 1, 'start': 0, 'duration': 100,
            'mediaDuration': 100, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'attributes': {'ident': ''},
        })
        assert group.internal_duration_seconds == 0.0

    def test_group_clear_all_then_clip_count(self):
        group = _make_group([[_clip_data('VMFile', 1, 0, 100), _clip_data('AMFile', 2, 50, 100)]])
        group.clear_all_internal_clips()
        assert group.clip_count == 0

    def test_group_add_internal_track_then_add_clip(self):
        group = _make_group([[]])
        new_track = group.add_internal_track()
        new_track.add_clip('IMFile', 5, 0, 705600000, next_id=100)
        assert group.clip_count == 1

    def test_group_ungroup_empty(self):
        group = _make_group([[]])
        extracted = group.ungroup()
        assert extracted == []


# ==================================================================
# Group basic properties (from test_clips.py)
# ==================================================================


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


def _group_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="Group",
        id=70,
        tracks=[
            {
                "trackIndex": 0,
                "medias": [_base_clip_dict(_type="IMFile", id=71)],
                "parameters": {},
            },
            {
                "trackIndex": 1,
                "medias": [_base_clip_dict(_type="AMFile", id=72)],
                "parameters": {},
            },
        ],
        attributes={"ident": "Group 1", "widthAttr": 1900.0, "heightAttr": 1060.0},
    )
    d.update(overrides)
    return d


_S1 = seconds_to_ticks(1.0)
_S5 = seconds_to_ticks(5.0)
_S10 = seconds_to_ticks(10.0)


def _um_data():
    return {
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': _S10,
        'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'video': {
            '_type': 'ScreenVMFile', 'id': 2, 'src': 5, 'start': 0,
            'duration': _S10, 'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'attributes': {'ident': 'rec'},
            'trackNumber': 0,
        },
        'audio': {
            '_type': 'AMFile', 'id': 3, 'src': 5, 'start': 0,
            'duration': _S10, 'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'attributes': {'gain': 1.0},
        },
    }


def _cov_group_data(inner=None, duration=None):
    dur = duration or _S10
    return {
        '_type': 'Group', 'id': 100, 'start': _S1, 'duration': dur,
        'mediaDuration': dur, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'attributes': {'ident': 'grp', 'widthAttr': 1920, 'heightAttr': 1080},
        'tracks': [{'trackIndex': 0, 'medias': inner or [], 'transitions': []}],
    }


def test_group_tracks_returns_group_track_objects() -> None:
    clip = Group(_group_dict())
    actual_tracks = clip.tracks
    assert [type(t) for t in actual_tracks] == [GroupTrack, GroupTrack]


def test_group_track_clips_are_typed() -> None:
    clip = Group(_group_dict())
    track0_clips = clip.tracks[0].clips
    assert type(track0_clips[0]) is IMFile

    track1_clips = clip.tracks[1].clips
    assert type(track1_clips[0]) is AMFile


def test_group_track_index() -> None:
    clip = Group(_group_dict())
    assert clip.tracks[0].track_index == 0
    assert clip.tracks[1].track_index == 1


def test_group_attributes() -> None:
    clip = Group(_group_dict())
    assert clip.ident == "Group 1"
    assert clip.width == 1900.0
    assert clip.height == 1060.0


def test_group_tracks_empty_when_no_tracks() -> None:
    data = _base_clip_dict(_type="Group")
    clip = Group(data)
    assert clip.tracks == []


class TestGroupSyncInternalDurations:
    def test_sync_with_fractional_scalar(self):
        inner = {
            '_type': 'VMFile', 'id': 10, 'src': 1,
            'start': 0, 'duration': _S10 * 2,
            'mediaDuration': _S10 * 2, 'mediaStart': 0, 'scalar': '1/2',
            'parameters': {}, 'effects': [],
        }
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.sync_internal_durations()
        assert inner['duration'] == _S10
        expected_md = int(Fraction(_S10) / Fraction(1, 2))
        assert inner['mediaDuration'] == expected_md

    def test_sync_propagates_to_unified(self):
        inner = copy.deepcopy(_um_data())
        inner['duration'] = _S10 * 3
        inner['mediaDuration'] = _S10 * 3
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.sync_internal_durations()
        assert inner['duration'] == _S10


class TestGroupUngroup:
    def test_ungroup_adjusts_start_and_propagates(self):
        inner_um = copy.deepcopy(_um_data())
        inner_um['start'] = 0
        data = _cov_group_data([inner_um])
        data['start'] = _S5
        g = Group(data)
        clips = g.ungroup()
        assert clips[0].start == _S5


class TestGroupSetInternalSegmentSpeedsCanvasWidthOnly:
    def test_canvas_width_only(self):
        inner = copy.deepcopy(_um_data())
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            canvas_width=1920,
        )
        clip = data['tracks'][0]['medias'][0]
        assert clip['parameters']['scale0']['defaultValue'] == 1.0

    def test_canvas_height_only(self):
        inner = copy.deepcopy(_um_data())
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            canvas_height=1080,
        )
        clip = data['tracks'][0]['medias'][0]
        assert clip['parameters']['scale1']['defaultValue'] == 1.0

    def test_source_bin_lookup_miss(self):
        inner = copy.deepcopy(_um_data())
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            source_bin=[{'id': 999, 'sourceTracks': []}],
            canvas_width=1920,
            canvas_height=1080,
        )
        medias = data['tracks'][0]['medias']
        assert medias[0]['_type'] in ('UnifiedMedia', 'ScreenVMFile', 'VMFile')

    def test_no_internal_track_raises(self):
        data = _cov_group_data()
        data['tracks'][0]['medias'] = []
        g = Group(data)
        with pytest.raises(ValueError, match='No internal track'):
            g.set_internal_segment_speeds(segments=[(0.0, 1.0, 1.0)])

    def test_stitched_media_template(self):
        stitched = {
            '_type': 'StitchedMedia', 'id': 50, 'start': 0, 'duration': _S10,
            'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'trackNumber': 0,
            'attributes': {'ident': 'stitch'},
            'medias': [{'_type': 'ScreenVMFile', 'id': 51, 'src': 5}],
        }
        data = _cov_group_data([stitched], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(segments=[(0.0, 5.0, 5.0)])
        assert data['tracks'][0]['medias'][0]['_type'] == 'ScreenVMFile'


def _make_group_for_sync(group_dur: int, clips: list[dict]) -> Group:
    """Build a Group with one internal track containing the given clip dicts."""
    return Group({
        '_type': 'Group', 'id': 1, 'start': 0,
        'duration': group_dur, 'mediaDuration': group_dur, 'scalar': 1,
        'parameters': {}, 'effects': [], 'metadata': {},
        'animationTracks': {}, 'attributes': {'ident': ''},
        'tracks': [{'trackIndex': 0, 'medias': clips}],
    })


class TestSyncInternalDurationsStartOffset:
    """sync_internal_durations must account for clip start offset."""

    def test_clip_with_start_offset_trimmed_correctly(self):
        group = _make_group_for_sync(100, [
            {'_type': 'VMFile', 'id': 10, 'start': 60, 'duration': 80,
             'mediaDuration': 80, 'scalar': 1},
        ])
        group.sync_internal_durations()
        assert group._data['tracks'][0]['medias'][0]['duration'] == 40

    def test_clip_starting_past_group_end_gets_zero_duration(self):
        group = _make_group_for_sync(50, [
            {'_type': 'VMFile', 'id': 10, 'start': 60, 'duration': 40,
             'mediaDuration': 40, 'scalar': 1},
        ])
        group.sync_internal_durations()
        assert group._data['tracks'][0]['medias'][0]['duration'] == 0

    def test_multiple_clips_with_offsets(self):
        group = _make_group_for_sync(100, [
            {'_type': 'VMFile', 'id': 10, 'start': 0, 'duration': 100,
             'mediaDuration': 100, 'scalar': 1},
            {'_type': 'VMFile', 'id': 11, 'start': 50, 'duration': 80,
             'mediaDuration': 80, 'scalar': 1},
        ])
        group.sync_internal_durations()
        clips_after = group._data['tracks'][0]['medias']
        assert clips_after[0]['duration'] == 100
        assert clips_after[1]['duration'] == 50


class TestSetInternalSegmentSpeedsResetsMediaStart:
    """Bug 6: set_internal_segment_speeds must reset mediaStart=0 on other-track clips."""

    def test_amfile_mediastart_reset_to_zero(self):
        """AMFile on non-video track should have mediaStart=0 after speed change."""
        data = {
            '_type': 'Group', 'id': 1, 'start': 0,
            'duration': seconds_to_ticks(100.0),
            'mediaStart': seconds_to_ticks(10.0),
            'mediaDuration': seconds_to_ticks(100.0),
            'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {}, 'attributes': {'ident': ''},
            'tracks': [
                {'medias': [{
                    'id': 10, '_type': 'AMFile', 'src': 1,
                    'start': 0, 'duration': seconds_to_ticks(100.0),
                    'mediaStart': seconds_to_ticks(10.0),
                    'mediaDuration': seconds_to_ticks(100.0),
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {}, 'animationTracks': {},
                }]},
                {'medias': [{
                    'id': 11, '_type': 'UnifiedMedia',
                    'video': {
                        'src': 1,
                        'attributes': {'ident': ''},
                        'parameters': {},
                        'effects': [],
                    },
                    'start': 0, 'duration': seconds_to_ticks(100.0),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100.0),
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {}, 'animationTracks': {},
                }]},
            ],
        }
        g = Group(data)
        g.set_internal_segment_speeds([(0, 50, 50.0), (50, 100, 50.0)])
        am_clip = data['tracks'][0]['medias'][0]
        assert am_clip['mediaStart'] == 0


class TestMergeInternalTracksSnapshot:
    """Bug 7: merge_internal_tracks should snapshot self.tracks once."""

    def test_single_track_returns_immediately(self):
        """A group with one track should return it without mutation."""
        g = _make_group([[_clip_data('VMFile', 10, 0.0, 5.0)]])
        result = g.merge_internal_tracks()
        assert len(result.clips) == 1

    def test_merge_preserves_all_clips(self):
        """Merging 3 tracks should collect all clips into track 0."""
        g = _make_group([
            [_clip_data('VMFile', 10, 0.0, 5.0)],
            [_clip_data('AMFile', 20, 0.0, 5.0)],
            [_clip_data('IMFile', 30, 0.0, 5.0)],
        ])
        result = g.merge_internal_tracks()
        assert len(result.clips) == 3
        assert len(g.tracks) == 1


# ==== Bugs 7-10: StitchedMedia handling + Group properties ====

def _make_group_bug7_10(tracks: list[dict]) -> Group:
    return Group({
        '_type': 'Group',
        'id': 1,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(10.0),
        'scalar': 1,
        'attributes': {'ident': 'test', 'widthAttr': 1920.0, 'heightAttr': 1080.0},
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
        'tracks': tracks,
    })


class TestSyncInternalDurationsStitchedMedia:
    """Bug 7: sync_internal_durations should trim StitchedMedia nested segments."""

    def test_trims_segments_past_new_duration(self) -> None:
        seg1_dur = seconds_to_ticks(4.0)
        seg2_dur = seconds_to_ticks(4.0)
        seg3_dur = seconds_to_ticks(4.0)
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'StitchedMedia',
                'id': 10,
                'start': 0,
                'duration': seg1_dur + seg2_dur + seg3_dur,
                'mediaStart': 0,
                'mediaDuration': seg1_dur + seg2_dur + seg3_dur,
                'scalar': 1,
                'parameters': {},
                'effects': [],
                'metadata': {},
                'animationTracks': {},
                'medias': [
                    {'_type': 'ScreenVMFile', 'id': 11, 'start': 0, 'duration': seg1_dur, 'src': 2},
                    {'_type': 'ScreenVMFile', 'id': 12, 'start': seg1_dur, 'duration': seg2_dur, 'src': 2},
                    {'_type': 'ScreenVMFile', 'id': 13, 'start': seg1_dur + seg2_dur, 'duration': seg3_dur, 'src': 2},
                ],
            }],
        }])
        # Reduce group duration so third segment is past the end
        group._data['duration'] = seconds_to_ticks(6.0)
        group.sync_internal_durations()

        stitched = group._data['tracks'][0]['medias'][0]
        segments = stitched['medias']
        # Third segment started at 8s, group is now 6s → dropped
        assert len(segments) == 2
        # Second segment: starts at 4s, dur 4s → end 8s > 6s → trimmed to 2s
        assert segments[1]['duration'] == seconds_to_ticks(2.0)

    def test_drops_segment_starting_at_new_end(self) -> None:
        dur5 = seconds_to_ticks(5.0)
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'StitchedMedia',
                'id': 10,
                'start': 0,
                'duration': dur5 * 2,
                'mediaStart': 0,
                'mediaDuration': dur5 * 2,
                'scalar': 1,
                'parameters': {},
                'effects': [],
                'metadata': {},
                'animationTracks': {},
                'medias': [
                    {'_type': 'ScreenVMFile', 'id': 11, 'start': 0, 'duration': dur5, 'src': 2},
                    {'_type': 'ScreenVMFile', 'id': 12, 'start': dur5, 'duration': dur5, 'src': 2},
                ],
            }],
        }])
        group._data['duration'] = dur5
        group.sync_internal_durations()

        segments = group._data['tracks'][0]['medias'][0]['medias']
        assert len(segments) == 1
        assert segments[0]['id'] == 11


class TestIsScreenRecordingStitchedMedia:
    """Bug 8: is_screen_recording should check StitchedMedia children."""

    def test_stitched_with_screen_vm_file(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'StitchedMedia',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'medias': [
                    {'_type': 'ScreenVMFile', 'id': 11, 'start': 0, 'duration': seconds_to_ticks(5.0), 'src': 2},
                ],
            }],
        }])
        assert group.is_screen_recording is True

    def test_stitched_with_unified_screen_vm(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'StitchedMedia',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'medias': [
                    {
                        '_type': 'UnifiedMedia',
                        'id': 11,
                        'video': {'_type': 'ScreenVMFile', 'id': 12, 'src': 2},
                        'start': 0,
                        'duration': seconds_to_ticks(5.0),
                    },
                ],
            }],
        }])
        assert group.is_screen_recording is True

    def test_stitched_with_plain_vm_file(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'StitchedMedia',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'medias': [
                    {'_type': 'VMFile', 'id': 11, 'start': 0, 'duration': seconds_to_ticks(5.0), 'src': 2},
                ],
            }],
        }])
        assert group.is_screen_recording is False


class TestInternalMediaSrcScreenOnly:
    """Bug 9: internal_media_src should only return ScreenVMFile sources."""

    def test_camera_unified_media_returns_none(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'UnifiedMedia',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'video': {'_type': 'VMFile', 'id': 11, 'src': 42},
                'audio': {'_type': 'AMFile', 'id': 12, 'src': 42},
            }],
        }])
        assert group.internal_media_src is None

    def test_screen_unified_media_returns_src(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'UnifiedMedia',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'video': {'_type': 'ScreenVMFile', 'id': 11, 'src': 42},
                'audio': {'_type': 'AMFile', 'id': 12, 'src': 42},
            }],
        }])
        assert group.internal_media_src == 42

    def test_bare_screen_vm_file_returns_src(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'ScreenVMFile',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'src': 99,
            }],
        }])
        assert group.internal_media_src == 99


class TestHasAudioUnifiedMedia:
    """Bug 10: has_audio should use has_audio property for UnifiedMedia."""

    def test_unified_media_with_audio_returns_true(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'UnifiedMedia',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'mediaStart': 0,
                'mediaDuration': seconds_to_ticks(5.0),
                'scalar': 1,
                'video': {
                    '_type': 'ScreenVMFile', 'id': 11, 'src': 2,
                    'start': 0, 'duration': seconds_to_ticks(5.0),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
                    'scalar': 1,
                },
                'audio': {
                    '_type': 'AMFile', 'id': 12, 'src': 2,
                    'start': 0, 'duration': seconds_to_ticks(5.0),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
                    'scalar': 1,
                },
                'effects': [],
            }],
        }])
        assert group.has_audio is True

    def test_unified_media_without_audio_returns_false(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'UnifiedMedia',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'mediaStart': 0,
                'mediaDuration': seconds_to_ticks(5.0),
                'scalar': 1,
                'video': {
                    '_type': 'ScreenVMFile', 'id': 11, 'src': 2,
                    'start': 0, 'duration': seconds_to_ticks(5.0),
                    'mediaStart': 0, 'mediaDuration': seconds_to_ticks(5.0),
                    'scalar': 1,
                },
                'effects': [],
            }],
        }])
        assert group.has_audio is False

    def test_amfile_still_detected(self) -> None:
        group = _make_group_bug7_10([{
            'trackIndex': 0,
            'medias': [{
                '_type': 'AMFile',
                'id': 10,
                'start': 0,
                'duration': seconds_to_ticks(5.0),
                'mediaStart': 0,
                'mediaDuration': seconds_to_ticks(5.0),
                'scalar': 1,
                'src': 2,
                'parameters': {},
                'effects': [],
                'metadata': {},
                'animationTracks': {},
            }],
        }])
        assert group.has_audio is True
