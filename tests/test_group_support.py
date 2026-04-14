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
        )
        assert isinstance(clip, BaseClip)

    def test_add_clip_increments_id(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
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
        )
        assert len(group_track) == original_count + 1

    def test_add_clip_without_source_id(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
        clip: BaseClip = group_track.add_clip(
            'Callout', source_id=None,
            start_ticks=0, duration_ticks=seconds_to_ticks(1.0),
        )
        assert 'src' not in clip._data

    def test_add_clip_with_extra_fields(self, group: Group) -> None:
        group_track: GroupTrack = group.tracks[0]
        clip: BaseClip = group_track.add_clip(
            'VMFile', source_id=7,
            start_ticks=0, duration_ticks=seconds_to_ticks(1.0),
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
        )
        assert group.clip_count == 3

    def test_clip_count_multiple_tracks(self, group: Group) -> None:
        new_track: GroupTrack = group.add_internal_track()
        new_track.add_clip(
            'AMFile', source_id=20,
            start_ticks=0, duration_ticks=seconds_to_ticks(2.0),
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
