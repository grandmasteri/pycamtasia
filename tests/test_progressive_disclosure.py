"""Tests for Project.add_progressive_disclosure()."""
from __future__ import annotations

from camtasia.timing import seconds_to_ticks


class TestProgressiveDisclosure:

    def test_creates_tracks_and_clips(self, project):
        clips = project.add_progressive_disclosure(
            [(10, 3.0), (20, 5.0)],
            start_seconds=1.0,
        )

        assert [(c.start, c.duration) for c in clips] == [
            (seconds_to_ticks(1.0), seconds_to_ticks(3.0)),
            (seconds_to_ticks(1.0), seconds_to_ticks(5.0)),
        ]
        track_names = [t.name for t in project.timeline.tracks]
        assert 'Prog-0' in track_names
        assert 'Prog-1' in track_names

    def test_fade_in_applied(self, project):
        clips = project.add_progressive_disclosure(
            [(10, 2.0)],
            start_seconds=0.0,
            fade_in=0.3,
        )

        opacity = clips[0]._data['parameters']['opacity']
        assert opacity['keyframes'][0]['value'] == 1.0
        assert opacity['keyframes'][0]['duration'] == seconds_to_ticks(0.3)

    def test_custom_prefix(self, project):
        project.add_progressive_disclosure(
            [(10, 1.0)],
            start_seconds=0.0,
            track_prefix='Layer',
        )

        track_names = [t.name for t in project.timeline.tracks]
        assert 'Layer-0' in track_names

    def test_empty_list(self, project):
        assert project.add_progressive_disclosure([], start_seconds=0.0) == []

    def test_correct_source_ids(self, project):
        clips = project.add_progressive_disclosure(
            [(10, 1.0), (20, 1.0)],
            start_seconds=0.0,
        )

        assert clips[0].source_id == 10
        assert clips[1].source_id == 20
