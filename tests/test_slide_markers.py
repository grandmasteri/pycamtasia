"""Tests for camtasia.operations.slide_markers."""
from __future__ import annotations

import pytest

from camtasia.operations.slide_markers import mark_slides_from_presentation
from camtasia.timing import EDIT_RATE


class TestMarkSlidesTimeline:
    def test_empty_slides(self, project):
        count = mark_slides_from_presentation(project, [])
        assert count == 0
        assert list(project.timeline.markers) == []

    def test_single_slide(self, project):
        slides = [{'time_seconds': 1.0, 'title': 'Slide 1'}]
        count = mark_slides_from_presentation(project, slides)
        assert count == 1
        markers = list(project.timeline.markers)
        assert len(markers) == 1
        assert markers[0].name == 'Slide 1'
        assert markers[0].time == pytest.approx(1.0 * EDIT_RATE, abs=1)

    def test_multiple_slides(self, project):
        slides = [
            {'time_seconds': 0.0, 'title': 'Intro'},
            {'time_seconds': 5.0, 'title': 'Body'},
            {'time_seconds': 10.0, 'title': 'Conclusion'},
        ]
        count = mark_slides_from_presentation(project, slides)
        assert count == 3
        names = [m.name for m in project.timeline.markers]
        assert names == ['Intro', 'Body', 'Conclusion']

    def test_returns_count(self, project):
        slides = [
            {'time_seconds': 0.0, 'title': 'A'},
            {'time_seconds': 1.0, 'title': 'B'},
        ]
        assert mark_slides_from_presentation(project, slides) == 2


class TestMarkSlidesTrack:
    def test_nonexistent_track_raises(self, project):
        with pytest.raises(KeyError, match='No track named'):
            mark_slides_from_presentation(
                project,
                [{'time_seconds': 0.0, 'title': 'X'}],
                track_name='nonexistent',
            )

    def test_markers_on_named_track(self, project):
        # The default project has at least one track; get its name
        track = list(project.timeline.tracks)[0]
        track_name = track.name
        slides = [{'time_seconds': 2.0, 'title': 'Track Slide'}]
        count = mark_slides_from_presentation(project, slides, track_name=track_name)
        assert count == 1
        markers = list(track.markers)
        assert len(markers) == 1
        assert markers[0].name == 'Track Slide'

    def test_timeline_markers_unchanged_when_track_specified(self, project):
        track = list(project.timeline.tracks)[0]
        slides = [{'time_seconds': 0.0, 'title': 'On Track'}]
        mark_slides_from_presentation(project, slides, track_name=track.name)
        assert list(project.timeline.markers) == []
