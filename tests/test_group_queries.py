"""Tests for Project.all_groups, Project.group_count,
Project.screen_recording_groups, and Timeline.groups.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.project import Project, load_project
from camtasia.timeline.clips.group import Group
from camtasia.timeline.track import Track

FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.fixture
def complex_project() -> Project:
    return load_project(FIXTURES / 'techsmith_complex_asset.tscproj')


# ---------------------------------------------------------------------------
# Project.all_groups
# ---------------------------------------------------------------------------

class TestAllGroups:
    def test_returns_list_of_track_group_tuples(self, complex_project: Project) -> None:
        all_groups = complex_project.all_groups
        assert isinstance(all_groups, list)
        for track, group in all_groups:
            assert isinstance(track, Track)
            assert isinstance(group, Group)

    def test_empty_project_returns_empty_list(self, project) -> None:
        assert project.all_groups == []

    def test_all_groups_is_subset_of_all_clips(self, complex_project: Project) -> None:
        all_clip_set = {clip.id for _, clip in complex_project.all_clips}
        for _, group in complex_project.all_groups:
            assert group.id in all_clip_set

    def test_no_non_group_clips_included(self, complex_project: Project) -> None:
        for _, clip in complex_project.all_groups:
            assert isinstance(clip, Group)


# ---------------------------------------------------------------------------
# Project.group_count
# ---------------------------------------------------------------------------

class TestGroupCount:
    def test_matches_len_of_all_groups(self, complex_project: Project) -> None:
        assert complex_project.group_count == len(complex_project.all_groups)

    def test_empty_project_returns_zero(self, project) -> None:
        assert project.group_count == 0


# ---------------------------------------------------------------------------
# Project.screen_recording_groups
# ---------------------------------------------------------------------------

class TestScreenRecordingGroups:
    def test_returns_list_of_track_group_tuples(self, complex_project: Project) -> None:
        screen_recording_groups = complex_project.screen_recording_groups
        assert isinstance(screen_recording_groups, list)
        for track, group in screen_recording_groups:
            assert isinstance(track, Track)
            assert isinstance(group, Group)

    def test_all_returned_groups_are_screen_recordings(self, complex_project: Project) -> None:
        for _, group in complex_project.screen_recording_groups:
            assert group.is_screen_recording is True

    def test_is_subset_of_all_groups(self, complex_project: Project) -> None:
        all_group_ids = {group.id for _, group in complex_project.all_groups}
        for _, group in complex_project.screen_recording_groups:
            assert group.id in all_group_ids

    def test_empty_project_returns_empty_list(self, project) -> None:
        assert project.screen_recording_groups == []

    def test_count_le_group_count(self, complex_project: Project) -> None:
        assert len(complex_project.screen_recording_groups) <= complex_project.group_count


# ---------------------------------------------------------------------------
# Timeline.groups
# ---------------------------------------------------------------------------

class TestTimelineGroups:
    def test_returns_list_of_groups(self, complex_project: Project) -> None:
        timeline_groups = complex_project.timeline.groups
        assert isinstance(timeline_groups, list)
        for group in timeline_groups:
            assert isinstance(group, Group)

    def test_empty_project_returns_empty_list(self, project) -> None:
        assert project.timeline.groups == []

    def test_count_matches_project_group_count(self, complex_project: Project) -> None:
        assert len(complex_project.timeline.groups) == complex_project.group_count

    def test_same_groups_as_project_all_groups(self, complex_project: Project) -> None:
        timeline_group_ids = {g.id for g in complex_project.timeline.groups}
        project_group_ids = {g.id for _, g in complex_project.all_groups}
        assert timeline_group_ids == project_group_ids


# ---------------------------------------------------------------------------
# Bug 3: set_internal_segment_speeds scalar must not truncate to integer
# ---------------------------------------------------------------------------

class TestSetInternalSegmentSpeedsScalar:
    def test_non_integer_scalar_preserved_as_fraction(self) -> None:
        """When total_tl / total_src is not an integer, scalar must be a string fraction."""
        from fractions import Fraction

        from camtasia.timeline.clips.group import Group
        from camtasia.timing import seconds_to_ticks

        dur_ticks = seconds_to_ticks(10.0)
        group_data: dict = {
            '_type': 'Group', 'id': 1,
            'start': 0, 'duration': dur_ticks,
            'mediaStart': 0, 'mediaDuration': dur_ticks,
            'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {},
            'attributes': {'ident': '', 'widthAttr': 1920.0, 'heightAttr': 1080.0},
            'tracks': [
                {'trackIndex': 0, 'medias': [{
                    'id': 10, '_type': 'UnifiedMedia',
                    'video': {
                        'id': 11, '_type': 'ScreenVMFile', 'src': 42,
                        'trackNumber': 0, 'attributes': {'ident': ''},
                        'parameters': {}, 'effects': [],
                        'start': 0, 'duration': dur_ticks,
                        'mediaStart': 0, 'mediaDuration': dur_ticks,
                        'scalar': 1, 'animationTracks': {},
                    },
                    'effects': [],
                    'start': 0, 'duration': dur_ticks,
                    'mediaStart': 0, 'mediaDuration': dur_ticks,
                    'scalar': 1,
                }]},
                {'trackIndex': 1, 'medias': [{
                    'id': 20, '_type': 'AMFile', 'src': 42,
                    'trackNumber': 1, 'attributes': {'ident': ''},
                    'parameters': {}, 'effects': [],
                    'start': 0, 'duration': dur_ticks,
                    'mediaStart': 0, 'mediaDuration': dur_ticks,
                    'scalar': 1, 'animationTracks': {},
                }]},
            ],
        }
        group = Group(group_data)
        # 3s source at 2x speed = 6s timeline, 7s source at 1x = 7s timeline
        # total_tl = 13s, total_src = 10s, ratio = 13/10 (not integer)
        group.set_internal_segment_speeds(
            [(0.0, 3.0, 6.0), (3.0, 10.0, 7.0)],
            next_id=100,
        )
        # Check the AMFile on track 1 got a fractional scalar
        am = group_data['tracks'][1]['medias'][0]
        scalar_val = Fraction(str(am['scalar']))
        assert scalar_val == Fraction(13, 10)


# ---------------------------------------------------------------------------
# Bug 4: internal_media_src must check StitchedMedia children
# ---------------------------------------------------------------------------

class TestInternalMediaSrcStitchedMedia:
    def test_finds_src_in_stitched_screen_vm_file(self) -> None:
        from camtasia.timeline.clips.group import Group

        group_data: dict = {
            '_type': 'Group', 'id': 1,
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100,
            'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {},
            'attributes': {'ident': ''},
            'tracks': [{'trackIndex': 0, 'medias': [{
                'id': 10, '_type': 'StitchedMedia',
                'start': 0, 'duration': 100,
                'medias': [
                    {'id': 11, '_type': 'ScreenVMFile', 'src': 99, 'start': 0, 'duration': 50},
                    {'id': 12, '_type': 'ScreenVMFile', 'src': 99, 'start': 50, 'duration': 50},
                ],
            }]}],
        }
        group = Group(group_data)
        assert group.internal_media_src == 99

    def test_finds_src_in_stitched_unified_media(self) -> None:
        from camtasia.timeline.clips.group import Group

        group_data: dict = {
            '_type': 'Group', 'id': 1,
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100,
            'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {},
            'attributes': {'ident': ''},
            'tracks': [{'trackIndex': 0, 'medias': [{
                'id': 10, '_type': 'StitchedMedia',
                'start': 0, 'duration': 100,
                'medias': [{
                    'id': 11, '_type': 'UnifiedMedia',
                    'video': {'_type': 'ScreenVMFile', 'src': 77},
                    'start': 0, 'duration': 100,
                }],
            }]}],
        }
        group = Group(group_data)
        assert group.internal_media_src == 77
