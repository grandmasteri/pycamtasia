"""Tests for Project.apply_to_all_groups and Project.mute_all_groups."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

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
# Project.apply_to_all_groups
# ---------------------------------------------------------------------------

class TestApplyToAllGroups:
    def test_returns_zero_for_empty_project(self, empty_project: Project) -> None:
        applied_count: int = empty_project.apply_to_all_groups(lambda g: None)
        assert applied_count == 0

    def test_returns_group_count(self, complex_project: Project) -> None:
        expected_count: int = complex_project.group_count
        applied_count: int = complex_project.apply_to_all_groups(lambda g: None)
        assert applied_count == expected_count

    def test_operation_called_on_each_group(self, complex_project: Project) -> None:
        visited_group_ids: list[int] = []
        complex_project.apply_to_all_groups(lambda g: visited_group_ids.append(g.id))
        expected_ids = [group.id for _, group in complex_project.all_groups]
        assert visited_group_ids == expected_ids

    def test_operation_receives_group_instances(self, complex_project: Project) -> None:
        received_types: list[type] = []
        complex_project.apply_to_all_groups(lambda g: received_types.append(type(g)))
        assert all(t is Group for t in received_types)

    def test_return_type_is_int(self, complex_project: Project) -> None:
        result = complex_project.apply_to_all_groups(lambda g: None)
        assert isinstance(result, int)


# ---------------------------------------------------------------------------
# Project.mute_all_groups
# ---------------------------------------------------------------------------

class TestMuteAllGroups:
    def test_returns_zero_for_empty_project(self, empty_project: Project) -> None:
        muted_count: int = empty_project.mute_all_groups()
        assert muted_count == 0

    def test_returns_group_count(self, complex_project: Project) -> None:
        expected_count: int = complex_project.group_count
        muted_count: int = complex_project.mute_all_groups()
        assert muted_count == expected_count

    def test_all_groups_muted_after_call(self, complex_project: Project) -> None:
        complex_project.mute_all_groups()
        for _track, group in complex_project.all_groups:
            assert group.is_muted is True

    def test_return_type_is_int(self, complex_project: Project) -> None:
        result = complex_project.mute_all_groups()
        assert isinstance(result, int)

    def test_idempotent(self, complex_project: Project) -> None:
        first_count: int = complex_project.mute_all_groups()
        second_count: int = complex_project.mute_all_groups()
        assert first_count == second_count
        for _track, group in complex_project.all_groups:
            assert group.is_muted is True
