"""Tests for Project.all_groups, Project.group_count,
Project.screen_recording_groups, and Timeline.groups.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.project import Project, load_project
from camtasia.timeline.clips.group import Group
from camtasia.timeline.track import Track

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'
FIXTURES = Path(__file__).parent / 'fixtures'


# Module-level list to prevent TemporaryDirectory from being GC'd during test
_TEMP_DIRS: list = []

def _isolated_project():
    """Load template into an isolated temp copy (safe for parallel execution)."""
    import shutil, tempfile
    from camtasia.project import load_project
    td = tempfile.TemporaryDirectory()
    _TEMP_DIRS.append(td)  # prevent premature GC
    dst = Path(td.name) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)

@pytest.fixture
def empty_project() -> Project:
    return _isolated_project()


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

    def test_empty_project_returns_empty_list(self, empty_project: Project) -> None:
        assert empty_project.all_groups == []

    def test_all_groups_is_subset_of_all_clips(self, complex_project: Project) -> None:
        all_clip_set = set(clip.id for _, clip in complex_project.all_clips)
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

    def test_empty_project_returns_zero(self, empty_project: Project) -> None:
        assert empty_project.group_count == 0

    def test_returns_int(self, complex_project: Project) -> None:
        assert complex_project.group_count == len(complex_project.all_groups)


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
        all_group_ids = set(group.id for _, group in complex_project.all_groups)
        for _, group in complex_project.screen_recording_groups:
            assert group.id in all_group_ids

    def test_empty_project_returns_empty_list(self, empty_project: Project) -> None:
        assert empty_project.screen_recording_groups == []

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

    def test_empty_project_returns_empty_list(self, empty_project: Project) -> None:
        assert empty_project.timeline.groups == []

    def test_count_matches_project_group_count(self, complex_project: Project) -> None:
        assert len(complex_project.timeline.groups) == complex_project.group_count

    def test_same_groups_as_project_all_groups(self, complex_project: Project) -> None:
        timeline_group_ids = set(g.id for g in complex_project.timeline.groups)
        project_group_ids = set(g.id for _, g in complex_project.all_groups)
        assert timeline_group_ids == project_group_ids
