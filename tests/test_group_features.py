"""Tests for Group introspection features: all_internal_clips, internal_clip_types,
has_audio, has_video, internal_duration_seconds, find_internal_clips_by_type.
"""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import BaseClip, Group, GroupTrack
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


# ── all_internal_clips ──────────────────────────────────────────────


class TestAllInternalClips:
    """Group.all_internal_clips returns a flat list of all clips."""

    def test_returns_all_clips_across_tracks(self, video_audio_group: Group) -> None:
        all_clips: list[BaseClip] = video_audio_group.all_internal_clips
        assert len(all_clips) == 2

    def test_returns_correct_types(self, video_audio_group: Group) -> None:
        clip_types: list[str] = [c.clip_type for c in video_audio_group.all_internal_clips]
        assert clip_types == ['VMFile', 'AMFile']

    def test_empty_group_returns_empty_list(self, empty_group: Group) -> None:
        assert empty_group.all_internal_clips == []

    def test_multi_type_group_count(self, multi_type_group: Group) -> None:
        assert len(multi_type_group.all_internal_clips) == 3

    def test_returns_base_clip_instances(self, video_audio_group: Group) -> None:
        for clip in video_audio_group.all_internal_clips:
            assert isinstance(clip, BaseClip)


# ── internal_clip_types ─────────────────────────────────────────────


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
        assert isinstance(result, set)


# ── has_audio ───────────────────────────────────────────────────────


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


# ── has_video ───────────────────────────────────────────────────────


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


# ── internal_duration_seconds ───────────────────────────────────────


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

    def test_returns_float(self, video_only_group: Group) -> None:
        assert isinstance(video_only_group.internal_duration_seconds, float)


# ── find_internal_clips_by_type ─────────────────────────────────────


class TestFindInternalClipsByType:
    """Group.find_internal_clips_by_type filters by clip type."""

    def test_find_by_string(self, multi_type_group: Group) -> None:
        video_clips: list[BaseClip] = multi_type_group.find_internal_clips_by_type('VMFile')
        assert len(video_clips) == 1
        assert all(c.clip_type == 'VMFile' for c in video_clips)

    def test_find_by_clip_type_enum(self, multi_type_group: Group) -> None:
        audio_clips: list[BaseClip] = multi_type_group.find_internal_clips_by_type(ClipType.AUDIO)
        assert len(audio_clips) == 1

    def test_no_matches_returns_empty(self, video_only_group: Group) -> None:
        assert video_only_group.find_internal_clips_by_type('AMFile') == []

    def test_empty_group_returns_empty(self, empty_group: Group) -> None:
        assert empty_group.find_internal_clips_by_type('VMFile') == []

    def test_multiple_matches(self, video_only_group: Group) -> None:
        video_clips: list[BaseClip] = video_only_group.find_internal_clips_by_type('VMFile')
        assert len(video_clips) == 2

    def test_find_image_clips(self, multi_type_group: Group) -> None:
        image_clips: list[BaseClip] = multi_type_group.find_internal_clips_by_type(ClipType.IMAGE)
        assert len(image_clips) == 1
        assert image_clips[0].clip_type == 'IMFile'


class TestGroupDescribe:
    def test_group_describe(self):
        """Group clips should have a working describe() method."""
        group = _make_group([[
            _clip_data(1, 'VMFile', 0, 100),
            _clip_data(2, 'AMFile', 0, 100),
        ]])
        actual_description: str = group.describe()
        assert 'Group' in actual_description

    def test_group_to_dict(self):
        """Group clips should have a working to_dict() method."""
        from camtasia.timeline.clips.group import Group
        group = _make_group([[_clip_data(1, 'VMFile', 0, 100)]])
        actual_dict: dict = group.to_dict()
        assert actual_dict['type'] == 'Group'
        assert actual_dict['id'] == group.id


class TestGroupTrackOperations:
    def test_group_track_len(self):
        from camtasia.timeline.clips.group import GroupTrack
        track_data = {'trackIndex': 0, 'medias': [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
            {'id': 2, '_type': 'AMFile', 'start': 100, 'duration': 200},
        ], 'transitions': [], 'parameters': {}, 'ident': '',
           'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False}
        gt = GroupTrack(track_data)
        assert len(gt) == 2

    def test_group_track_iter(self):
        from camtasia.timeline.clips.group import GroupTrack
        track_data = {'trackIndex': 0, 'medias': [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100},
        ], 'transitions': [], 'parameters': {}, 'ident': '',
           'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False}
        gt = GroupTrack(track_data)
        clips = list(gt)
        assert len(clips) == 1
        assert clips[0].id == 1

    def test_group_track_repr(self):
        from camtasia.timeline.clips.group import GroupTrack
        track_data = {'trackIndex': 0, 'medias': [], 'transitions': [], 'parameters': {}, 'ident': '',
           'audioMuted': False, 'videoHidden': False, 'magnetic': False, 'matte': 0, 'solo': False}
        gt = GroupTrack(track_data)
        assert 'GroupTrack' in repr(gt)


class TestGroupEdgeCases:
    def test_empty_group_clip_count(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[]])
        assert group.clip_count == 0

    def test_empty_group_all_internal_clips(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[]])
        assert group.all_internal_clips == []

    def test_empty_group_internal_duration(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[]])
        assert group.internal_duration_seconds == 0.0

    def test_group_find_internal_clips_no_match(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[_clip_data(1, 'VMFile', 0, 100)]])
        assert group.find_internal_clips_by_type('AMFile') == []

    def test_group_has_audio_false(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[_clip_data(1, 'VMFile', 0, 100)]])
        assert group.has_audio is False

    def test_group_has_video_false(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[_clip_data(1, 'AMFile', 0, 100)]])
        assert group.has_video is False

    def test_group_rename_and_check(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[_clip_data(1, 'VMFile', 0, 100)]])
        group.rename('My Group')
        assert group.ident == 'My Group'

    def test_group_set_dimensions_and_check(self):
        from camtasia.timeline.clips.group import Group
        group = _make_group([[_clip_data(1, 'VMFile', 0, 100)]])
        group.set_dimensions(1920.0, 1080.0)
        assert group.width == 1920.0
        assert group.height == 1080.0

    def test_group_no_tracks_internal_duration(self):
        from camtasia.timeline.clips.group import Group
        group = Group({
            '_type': 'Group', 'id': 1, 'start': 0, 'duration': 100,
            'mediaDuration': 100, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'attributes': {'ident': ''},
        })
        assert group.internal_duration_seconds == 0.0

    def test_group_clear_all_then_clip_count(self):
        group = _make_group([[_clip_data(1, 'VMFile', 0, 100), _clip_data(2, 'AMFile', 50, 100)]])
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
