"""Tests for camtasia.operations.diff."""

from __future__ import annotations

from pathlib import Path

from camtasia.operations.diff import ProjectDiff, diff_projects
from camtasia.project import load_project
from camtasia.timing import seconds_to_ticks


def _load_copy(project):
    """Load a second independent instance from the same tmp_path copy."""
    return load_project(project.file_path)


def test_identical_projects_no_changes(project):
    b = _load_copy(project)
    result = diff_projects(project, b)
    assert not result.has_changes
    assert result.tracks_added == []
    assert result.tracks_removed == []
    assert result.clips_added == []
    assert result.clips_removed == []
    assert result.media_added == []
    assert result.media_removed == []
    assert result.settings_changed == {}


def test_track_added(project):
    b = _load_copy(project)
    b.timeline.get_or_create_track('New')
    result = diff_projects(project, b)
    assert len(result.tracks_added) == 1
    assert result.tracks_removed == []


def test_track_removed(project):
    b = _load_copy(project)
    project.timeline.get_or_create_track('Extra')
    result = diff_projects(project, b)
    assert len(result.tracks_removed) == 1
    assert result.tracks_added == []


def test_clip_added(project):
    b = _load_copy(project)
    project.timeline.get_or_create_track('T')
    track_b = b.timeline.get_or_create_track('T')
    track_b.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
    result = diff_projects(project, b)
    assert len(result.clips_added) == 1
    assert result.clips_removed == []


def test_clip_removed(project):
    b = _load_copy(project)
    track_a = project.timeline.get_or_create_track('T')
    b.timeline.get_or_create_track('T')
    track_a.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
    result = diff_projects(project, b)
    assert len(result.clips_removed) == 1
    assert result.clips_added == []


def test_media_added(project):
    b = _load_copy(project)
    wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
    b.import_media(wav)
    result = diff_projects(project, b)
    assert len(result.media_added) == 1
    assert result.media_removed == []


def test_settings_changed(project):
    b = _load_copy(project)
    b.width = 3840
    b.height = 2160
    result = diff_projects(project, b)
    assert 'width' in result.settings_changed
    assert 'height' in result.settings_changed
    assert result.settings_changed['width'] == (project.width, 3840)
    assert result.settings_changed['height'] == (project.height, 2160)


def test_has_changes_true(project):
    b = _load_copy(project)
    b.width = 1280
    result = diff_projects(project, b)
    assert result.has_changes is True


def test_has_changes_false():
    result = ProjectDiff()
    assert result.has_changes is False


def test_summary_no_changes():
    result = ProjectDiff()
    assert result.summary() == 'No changes'


def test_summary_with_changes(project):
    b = _load_copy(project)
    b.width = 3840
    b.timeline.get_or_create_track('New')
    result = diff_projects(project, b)
    text = result.summary()
    assert 'width' in text
    assert 'Tracks added' in text


class TestSummaryAllFields:
    def test_summary_shows_all_change_types(self):
        diff = ProjectDiff(
            tracks_added=[3],
            tracks_removed=[0],
            clips_added=[(1, 10), (2, 20)],
            clips_removed=[(1, 5)],
            media_added=[100],
            media_removed=[50, 51],
            settings_changed={'width': (1920, 3840)},
        )
        actual_summary = diff.summary()
        assert 'Tracks added' in actual_summary
        assert 'Tracks removed' in actual_summary
        assert 'Clips added: 2' in actual_summary
        assert 'Clips removed: 1' in actual_summary
        assert 'Media added: 1' in actual_summary
        assert 'Media removed: 2' in actual_summary
        assert 'width: 1920 -> 3840' in actual_summary
