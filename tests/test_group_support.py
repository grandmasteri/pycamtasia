"""Tests for Group manipulation support: add_clip, add_internal_track, ungroup, group_clips, clip_count."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import BaseClip, Group, GroupTrack, clip_from_dict
from camtasia.timeline.track import Track
from camtasia.timing import EDIT_RATE, seconds_to_ticks


@pytest.fixture
def track() -> Track:
    """A bare Track with two simple clips for grouping tests."""
    attrs = {'ident': 'Track 1'}
    data = {
        'trackIndex': 0,
        'medias': [
            {
                '_type': 'VMFile',
                'id': 1,
                'src': 10,
                'start': seconds_to_ticks(0.0),
                'duration': seconds_to_ticks(5.0),
                'mediaStart': 0,
                'mediaDuration': seconds_to_ticks(5.0),
                'scalar': 1,
                'parameters': {},
                'effects': [],
                'metadata': {},
                'animationTracks': {},
            },
            {
                '_type': 'AMFile',
                'id': 2,
                'src': 11,
                'start': seconds_to_ticks(5.0),
                'duration': seconds_to_ticks(3.0),
                'mediaStart': 0,
                'mediaDuration': seconds_to_ticks(3.0),
                'scalar': 1,
                'parameters': {},
                'effects': [],
                'metadata': {},
                'animationTracks': {},
            },
        ],
        'transitions': [],
    }
    return Track(attrs, data)


@pytest.fixture
def group() -> Group:
    """A Group clip with one internal track containing two clips."""
    group_data = {
        '_type': 'Group',
        'id': 100,
        'start': seconds_to_ticks(10.0),
        'duration': seconds_to_ticks(8.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(8.0),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
        'attributes': {'ident': 'TestGroup'},
        'tracks': [
            {
                'trackIndex': 0,
                'medias': [
                    {
                        '_type': 'VMFile',
                        'id': 10,
                        'src': 5,
                        'start': 0,
                        'duration': seconds_to_ticks(4.0),
                        'mediaStart': 0,
                        'mediaDuration': seconds_to_ticks(4.0),
                        'scalar': 1,
                        'parameters': {},
                        'effects': [],
                        'metadata': {},
                        'animationTracks': {},
                    },
                    {
                        '_type': 'AMFile',
                        'id': 11,
                        'src': 6,
                        'start': seconds_to_ticks(4.0),
                        'duration': seconds_to_ticks(4.0),
                        'mediaStart': 0,
                        'mediaDuration': seconds_to_ticks(4.0),
                        'scalar': 1,
                        'parameters': {},
                        'effects': [],
                        'metadata': {},
                        'animationTracks': {},
                    },
                ],
                'transitions': [],
            },
        ],
    }
    return Group(group_data)


class TestGroupTrackAddClip:
    """GroupTrack.add_clip() creates a clip inside the internal track."""

    def test_add_clip_returns_base_clip(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
        clip: BaseClip = group_track.add_clip(
            'IMFile', source_id=99,
            start_ticks=0, duration_ticks=seconds_to_ticks(2.0),
            next_id=100,
        )
        assert isinstance(clip, BaseClip)

    def test_add_clip_increments_id(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
        with pytest.warns(UserWarning, match='auto-generated locally-unique ID'):
            clip: BaseClip = group_track.add_clip(
                'IMFile', source_id=99,
                start_ticks=0, duration_ticks=seconds_to_ticks(2.0),
            )
        assert clip.id == 12  # max existing is 11

    def test_add_clip_increases_track_length(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
        original_count: int = len(group_track)
        group_track.add_clip(
            'IMFile', source_id=99,
            start_ticks=0, duration_ticks=seconds_to_ticks(2.0),
            next_id=100,
        )
        assert len(group_track) == original_count + 1

    def test_add_clip_without_source_id(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
        clip: BaseClip = group_track.add_clip(
            'Callout', source_id=None,
            start_ticks=0, duration_ticks=seconds_to_ticks(1.0),
            next_id=100,
        )
        assert 'src' not in clip._data

    def test_add_clip_with_extra_fields(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
        clip: BaseClip = group_track.add_clip(
            'VMFile', source_id=7,
            start_ticks=0, duration_ticks=seconds_to_ticks(1.0),
            next_id=100,
            trackNumber=1,
        )
        assert clip._data['trackNumber'] == 1


class TestGroupAddInternalTrack:
    """Group.add_internal_track() appends a new empty track."""

    def test_add_internal_track_returns_group_track(self, group: Group) -> None:
        new_track: GroupTrack = group.add_internal_track()
        assert isinstance(new_track, GroupTrack)

    def test_add_internal_track_increases_count(self, group: Group) -> None:
        original_count: int = len(group.tracks)
        group.add_internal_track()
        assert len(group.tracks) == original_count + 1

    def test_new_track_has_correct_index(self, group: Group) -> None:
        new_track: GroupTrack = group.add_internal_track()
        assert new_track.track_index == 1

    def test_new_track_is_empty(self, group: Group) -> None:
        new_track: GroupTrack = group.add_internal_track()
        assert len(new_track) == 0


class TestGroupUngroup:
    """Group.ungroup() extracts clips with timeline-absolute positions."""

    def test_ungroup_returns_all_clips(self, group: Group) -> None:
        extracted_clips: list[BaseClip] = group.ungroup()
        assert len(extracted_clips) == 2

    def test_ungroup_adjusts_start_times(self, group: Group) -> None:
        group_start: int = group.start
        extracted_clips: list[BaseClip] = group.ungroup()
        first_clip: BaseClip = extracted_clips[0]
        # First internal clip had start=0, should now be group_start
        assert first_clip.start == group_start

    def test_ungroup_second_clip_timing(self, group: Group) -> None:
        group_start: int = group.start
        extracted_clips: list[BaseClip] = group.ungroup()
        second_clip: BaseClip = extracted_clips[1]
        expected_start: int = group_start + seconds_to_ticks(4.0)
        assert second_clip.start == expected_start

    def test_ungroup_preserves_clip_types(self, group: Group) -> None:
        extracted_clips: list[BaseClip] = group.ungroup()
        clip_types: list[str] = [c.clip_type for c in extracted_clips]
        assert clip_types == ['VMFile', 'AMFile']


class TestTrackGroupClips:
    """Track.group_clips() removes clips and creates a Group."""

    def test_group_clips_returns_group(self, track: Track) -> None:
        result: Group = track.group_clips([1, 2])
        assert isinstance(result, Group)

    def test_group_clips_removes_originals(self, track: Track) -> None:
        track.group_clips([1, 2])
        # Only the new Group should remain
        remaining_types: list[str] = [c.clip_type for c in track.clips]
        assert remaining_types == ['Group']

    def test_group_clips_has_internal_clips(self, track: Track) -> None:
        result: Group = track.group_clips([1, 2])
        internal_clip_count: int = sum(len(t) for t in result.tracks)
        assert internal_clip_count == 2

    def test_group_clips_raises_on_missing_ids(self, track: Track) -> None:
        with pytest.raises(KeyError, match='Clips not found'):
            track.group_clips([999, 888])

    def test_group_clips_position_at_earliest(self, track: Track) -> None:
        result: Group = track.group_clips([1, 2])
        # Clip 1 starts at 0.0s, so group should start at 0.0s
        assert result.start == seconds_to_ticks(0.0)

    def test_group_clips_duration_spans_all(self, track: Track) -> None:
        result: Group = track.group_clips([1, 2])
        # Clip 1: 0-5s, Clip 2: 5-8s → total 8s
        assert result.duration == seconds_to_ticks(8.0)


class TestGroupClipCount:
    """Group.clip_count property returns total clips across all tracks."""

    def test_clip_count_single_track(self, group: Group) -> None:
        assert group.clip_count == 2

    def test_clip_count_after_add(self, group: Group) -> None:
        group.tracks[0].add_clip(
            'IMFile', source_id=99,
            start_ticks=0, duration_ticks=seconds_to_ticks(1.0),
            next_id=100,
        )
        assert group.clip_count == 3

    def test_clip_count_multiple_tracks(self, group: Group) -> None:
        new_track: GroupTrack = group.add_internal_track()
        new_track.add_clip(
            'AMFile', source_id=20,
            start_ticks=0, duration_ticks=seconds_to_ticks(2.0),
            next_id=100,
        )
        assert group.clip_count == 3


class TestGroupClipsPreservesTiming:
    """Verify timing integrity through group/ungroup round-trip."""

    def test_round_trip_preserves_relative_offsets(self, track: Track) -> None:
        """Grouping then ungrouping should yield the original absolute start times."""
        original_clip_1_start: int = seconds_to_ticks(0.0)
        original_clip_2_start: int = seconds_to_ticks(5.0)

        grouped: Group = track.group_clips([1, 2])
        extracted_clips: list[BaseClip] = grouped.ungroup()

        assert extracted_clips[0].start == original_clip_1_start
        assert extracted_clips[1].start == original_clip_2_start

    def test_internal_clips_are_group_relative(self, track: Track) -> None:
        """After grouping, internal clip starts should be relative to group start."""
        grouped: Group = track.group_clips([1, 2])
        internal_clips: list[BaseClip] = grouped.tracks[0].clips
        # Group starts at 0.0s, so first clip should be at 0 relative
        assert internal_clips[0].start == 0
        # Second clip was at 5.0s absolute, group at 0.0s → relative 5.0s
        assert internal_clips[1].start == seconds_to_ticks(5.0)


# ── from test_coverage_phase4: group.py tests ──

import warnings


def test_group_track_transitions_raises():
    gt = GroupTrack({'medias': []})
    with pytest.raises(AttributeError, match='do not support transitions'):
        gt.transitions


def test_group_set_source_raises():
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 100,
        'tracks': [],
    })
    with pytest.raises(TypeError, match='do not have a source'):
        g.set_source(1)


def test_set_internal_segment_speeds_warns_over_8():
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 10000,
        'tracks': [{'medias': [{'_type': 'ScreenVMFile', 'id': 10, 'start': 0, 'duration': 10000,
                                 'src': 1, 'mediaStart': 0, 'mediaDuration': 10000,
                                 'attributes': {'ident': ''}, 'trackNumber': 0}]}],
    })
    segments = [(i * 0.1, (i + 1) * 0.1, 0.1) for i in range(9)]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        g.set_internal_segment_speeds(segments)
        warns = [x for x in w if '>8' in str(x.message)]
        assert len(warns) >= 1


def test_set_internal_segment_speeds_canvas_aspect_mismatch():
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 10000,
        'attributes': {'widthAttr': 1920, 'heightAttr': 1080},
        'tracks': [{'medias': [{'_type': 'ScreenVMFile', 'id': 10, 'start': 0, 'duration': 10000,
                                 'src': 1, 'mediaStart': 0, 'mediaDuration': 10000,
                                 'attributes': {'ident': ''}, 'trackNumber': 0}]}],
    })
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        g.set_internal_segment_speeds(
            [(0, 5.0, 5.0)],
            canvas_width=800,
            canvas_height=800,
            source_width=1920,
            source_height=1080,
        )
        warns = [x for x in w if 'aspect ratio' in str(x.message)]
        assert len(warns) >= 1


def test_set_internal_segment_speeds_source_bin_resolve():
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 10000,
        'tracks': [{'medias': [{'_type': 'ScreenVMFile', 'id': 10, 'start': 0, 'duration': 10000,
                                 'src': 42, 'mediaStart': 0, 'mediaDuration': 10000,
                                 'attributes': {'ident': ''}, 'trackNumber': 0}]}],
    })
    source_bin = [
        {'id': 42, 'sourceTracks': [{'trackRect': [0, 0, 3840, 2160]}]},
    ]
    g.set_internal_segment_speeds(
        [(0, 5.0, 5.0)],
        canvas_width=1920,
        canvas_height=1080,
        source_bin=source_bin,
    )


def test_group_trim_to_group_duration():
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 500,
        'tracks': [{'medias': [
            {'_type': 'VMFile', 'id': 10, 'start': 0, 'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1},
            {'_type': 'IMFile', 'id': 11, 'start': 0, 'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000},
        ]}],
    })
    g.sync_internal_durations()
    assert g._data['tracks'][0]['medias'][0]['duration'] == 500
    assert g._data['tracks'][0]['medias'][1]['mediaDuration'] == 1


# ── from test_ci_coverage_gaps: group.py set_internal_segment_speeds ──

def _group_with_unified_media():
    return {
        'id': 1, '_type': 'Group',
        'start': 0, 'duration': seconds_to_ticks(100),
        'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100),
        'scalar': 1, 'metadata': {}, 'parameters': {}, 'effects': [],
        'attributes': {'ident': ''}, 'animationTracks': {},
        'tracks': [
            {'medias': [{'id': 10, '_type': 'VMFile', 'src': 1,
                         'start': 0, 'duration': seconds_to_ticks(100),
                         'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100),
                         'scalar': 1}]},
            {'medias': [{'id': 11, '_type': 'UnifiedMedia',
                         'video': {'src': 2, 'attributes': {'ident': 'rec'},
                                   'parameters': {}, 'effects': []},
                         'start': 0, 'duration': seconds_to_ticks(100),
                         'mediaStart': 0, 'mediaDuration': seconds_to_ticks(100)}]},
        ],
    }


class TestGroupSetInternalSegmentSpeeds:
    def test_creates_screenvm_clips(self):
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50), (50, 100, 25)])
        media_track = data['tracks'][1]
        assert [m['_type'] for m in media_track['medias']] == ['ScreenVMFile', 'ScreenVMFile']

    def test_updates_group_duration(self):
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 30), (50, 100, 20)])
        assert data['duration'] == seconds_to_ticks(50)

    def test_extends_vmfile_on_other_tracks(self):
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50), (50, 100, 50)])
        vmfile = data['tracks'][0]['medias'][0]
        assert vmfile['duration'] == seconds_to_ticks(100)

    def test_no_unified_media_raises(self):
        data = {
            'id': 1, '_type': 'Group',
            'start': 0, 'duration': 100, 'mediaStart': 0,
            'mediaDuration': 100, 'scalar': 1,
            'tracks': [{'medias': [{'id': 10, '_type': 'AMFile'}]}],
        }
        group = Group(data)
        with pytest.raises(ValueError, match='No internal track'):
            group.set_internal_segment_speeds([(0, 50, 50)])

    def test_stitched_media_template(self):
        data = _group_with_unified_media()
        data['tracks'][1]['medias'] = [{'id': 11, '_type': 'StitchedMedia',
                                         'src': 2, 'attributes': {'ident': 'rec'}}]
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50)])
        assert data['tracks'][1]['medias'][0]['_type'] == 'ScreenVMFile'

    def test_scalar_is_string_when_not_one(self):
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 100, 50)])
        clip = data['tracks'][1]['medias'][0]
        assert isinstance(clip['scalar'], str)

    def test_scalar_is_int_one_for_normal_speed(self):
        data = _group_with_unified_media()
        group = Group(data)
        group.set_internal_segment_speeds([(0, 50, 50)])
        clip = data['tracks'][1]['medias'][0]
        assert clip['scalar'] == 1
