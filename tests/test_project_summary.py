"""Tests for Project.summary() and Timeline.duration_seconds property."""
from __future__ import annotations


def test_summary_contains_project_name(project):
    text = project.summary()
    assert f'Project: {project.file_path.name}' in text


def test_summary_contains_dimensions(project):
    text = project.summary()
    assert f'Canvas: {project.width}x{project.height}' in text


def test_summary_contains_track_info(project):
    text = project.summary()
    assert f'Tracks: {project.timeline.track_count}' in text
    # Each track should appear as an indented line
    for track in project.timeline.tracks:
        assert f'Track {track.index}' in text


def test_timeline_duration_seconds_property(project):
    tl = project.timeline
    assert tl.duration_seconds == tl.total_duration_seconds()


class TestSummaryWithClips:
    def test_summary_shows_clip_types(self, project):
        track = project.timeline.add_track('Test')
        track.add_clip('AMFile', 1, 0, 705600000)
        actual_summary = project.summary()
        assert 'AMFile' in actual_summary
        assert 'clips' in actual_summary
