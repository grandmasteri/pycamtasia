"""Tests for camtasia.operations.diff."""

from __future__ import annotations

from pathlib import Path

from camtasia.operations.diff import ProjectDiff, diff_projects
from camtasia.project import load_project
from camtasia.timing import seconds_to_ticks

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'



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

def _load_empty():
    return _isolated_project()


def test_identical_projects_no_changes():
    a, b = _load_empty(), _load_empty()
    result = diff_projects(a, b)
    assert not result.has_changes
    assert result.tracks_added == []
    assert result.tracks_removed == []
    assert result.clips_added == []
    assert result.clips_removed == []
    assert result.media_added == []
    assert result.media_removed == []
    assert result.settings_changed == {}


def test_track_added():
    a, b = _load_empty(), _load_empty()
    b.timeline.get_or_create_track('New')
    result = diff_projects(a, b)
    assert len(result.tracks_added) >= 1
    assert result.tracks_removed == []


def test_track_removed():
    a, b = _load_empty(), _load_empty()
    a.timeline.get_or_create_track('Extra')
    result = diff_projects(a, b)
    assert len(result.tracks_removed) >= 1
    assert result.tracks_added == []


def test_clip_added():
    a, b = _load_empty(), _load_empty()
    track_a = a.timeline.get_or_create_track('T')
    track_b = b.timeline.get_or_create_track('T')
    track_b.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
    result = diff_projects(a, b)
    assert len(result.clips_added) == 1
    assert result.clips_removed == []


def test_clip_removed():
    a, b = _load_empty(), _load_empty()
    track_a = a.timeline.get_or_create_track('T')
    track_b = b.timeline.get_or_create_track('T')
    track_a.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
    result = diff_projects(a, b)
    assert len(result.clips_removed) == 1
    assert result.clips_added == []


def test_media_added():
    a, b = _load_empty(), _load_empty()
    wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
    b.import_media(wav)
    result = diff_projects(a, b)
    assert len(result.media_added) >= 1
    assert result.media_removed == []


def test_settings_changed():
    a, b = _load_empty(), _load_empty()
    b.width = 3840
    b.height = 2160
    result = diff_projects(a, b)
    assert 'width' in result.settings_changed
    assert 'height' in result.settings_changed
    assert result.settings_changed['width'] == (a.width, 3840)
    assert result.settings_changed['height'] == (a.height, 2160)


def test_has_changes_true():
    a, b = _load_empty(), _load_empty()
    b.width = 1280
    result = diff_projects(a, b)
    assert result.has_changes is True


def test_has_changes_false():
    result = ProjectDiff()
    assert result.has_changes is False


def test_summary_no_changes():
    result = ProjectDiff()
    assert result.summary() == 'No changes'


def test_summary_with_changes():
    a, b = _load_empty(), _load_empty()
    b.width = 3840
    b.timeline.get_or_create_track('New')
    result = diff_projects(a, b)
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
