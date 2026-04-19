"""Tests for Project.diff() method."""

from __future__ import annotations

from pathlib import Path

from camtasia.project import load_project
from camtasia.timing import seconds_to_ticks


def _load_copy(project):
    """Load a second independent instance from the same tmp_path copy."""
    return load_project(project.file_path)


def test_diff_identical_projects_returns_empty(project):
    b = _load_copy(project)
    assert project.diff(b) == {}


def test_diff_title_changed(project):
    b = _load_copy(project)
    b.title = 'Other'
    result = project.diff(b)
    assert result['title'] == (project.title, 'Other')


def test_diff_resolution_changed(project):
    b = _load_copy(project)
    b.width = 3840
    b.height = 2160
    result = project.diff(b)
    assert result['resolution'] == ('1920x1080', '3840x2160')


def test_diff_resolution_width_only(project):
    b = _load_copy(project)
    b.width = 1280
    result = project.diff(b)
    assert 'resolution' in result


def test_diff_track_count_changed(project):
    b = _load_copy(project)
    b.timeline.get_or_create_track('Extra')
    result = project.diff(b)
    assert result['track_count'] == (project.track_count, b.track_count)


def test_diff_clip_count_changed(project):
    b = _load_copy(project)
    track = b.timeline.get_or_create_track('T')
    track.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
    result = project.diff(b)
    assert result['clip_count'] == (project.clip_count, b.clip_count)


def test_diff_media_count_changed(project):
    b = _load_copy(project)
    wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
    b.import_media(wav)
    result = project.diff(b)
    assert 'media_count' in result


def test_diff_multiple_differences(project):
    b = _load_copy(project)
    b.title = 'Changed'
    b.width = 3840
    b.height = 2160
    result = project.diff(b)
    assert 'title' in result
    assert 'resolution' in result


def test_diff_no_false_positives_on_same_values(project):
    b = _load_copy(project)
    b.title = project.title
    b.width = project.width
    b.height = project.height
    assert project.diff(b) == {}
