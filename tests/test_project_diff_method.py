"""Tests for Project.diff() method."""

from __future__ import annotations

from pathlib import Path

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


def test_diff_identical_projects_returns_empty():
    a, b = _load_empty(), _load_empty()
    assert a.diff(b) == {}


def test_diff_title_changed():
    a, b = _load_empty(), _load_empty()
    b.title = 'Other'
    result = a.diff(b)
    assert result['title'] == (a.title, 'Other')


def test_diff_resolution_changed():
    a, b = _load_empty(), _load_empty()
    b.width = 3840
    b.height = 2160
    result = a.diff(b)
    assert result['resolution'] == ('1920x1080', '3840x2160')


def test_diff_resolution_width_only():
    a, b = _load_empty(), _load_empty()
    b.width = 1280
    result = a.diff(b)
    assert 'resolution' in result


def test_diff_track_count_changed():
    a, b = _load_empty(), _load_empty()
    b.timeline.get_or_create_track('Extra')
    result = a.diff(b)
    assert result['track_count'] == (a.track_count, b.track_count)


def test_diff_clip_count_changed():
    a, b = _load_empty(), _load_empty()
    track = b.timeline.get_or_create_track('T')
    track.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
    result = a.diff(b)
    assert result['clip_count'] == (a.clip_count, b.clip_count)


def test_diff_media_count_changed():
    a, b = _load_empty(), _load_empty()
    wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
    b.import_media(wav)
    result = a.diff(b)
    assert 'media_count' in result


def test_diff_multiple_differences():
    a, b = _load_empty(), _load_empty()
    b.title = 'Changed'
    b.width = 3840
    b.height = 2160
    result = a.diff(b)
    assert 'title' in result
    assert 'resolution' in result


def test_diff_no_false_positives_on_same_values():
    a, b = _load_empty(), _load_empty()
    b.title = a.title
    b.width = a.width
    b.height = a.height
    assert a.diff(b) == {}
