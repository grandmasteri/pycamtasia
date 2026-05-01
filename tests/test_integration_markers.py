"""Integration tests for markers and captions — opened in Camtasia."""
from __future__ import annotations

from camtasia import seconds_to_ticks
from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


class TestTimelineMarkers:
    """Timeline-level markers (project.timeline.markers)."""

    def test_add_single_marker(self, project):
        project.timeline.markers.add('Intro', seconds_to_ticks(1.0))
        open_in_camtasia(project)

    def test_add_and_remove_marker(self, project):
        t = seconds_to_ticks(5.0)
        project.timeline.markers.add('ToRemove', t)
        project.timeline.markers.add('ToKeep', seconds_to_ticks(10.0))
        project.timeline.markers.remove_at(t)
        open_in_camtasia(project)

    def test_marker_rename(self, project):
        project.timeline.markers.add('OldLabel', seconds_to_ticks(3.0))
        project.timeline.markers._inner.rename('OldLabel', 'NewLabel')
        open_in_camtasia(project)

    def test_marker_at_time_zero(self, project):
        project.timeline.markers.add('Start', 0)
        open_in_camtasia(project)

    def test_marker_at_end_of_timeline(self, project):
        # Place a callout to give the timeline duration, then marker at end
        track = project.timeline.get_or_create_track('Content')
        track.add_callout('placeholder', 0.0, 60.0)
        end_ticks = seconds_to_ticks(60.0)
        project.timeline.markers.add('End', end_ticks)
        open_in_camtasia(project)

    def test_many_markers(self, project):
        for i in range(55):
            project.timeline.markers.add(f'M{i:03d}', seconds_to_ticks(i * 0.5))
        open_in_camtasia(project)


class TestMediaMarkers:
    """Per-track (media) markers via track.markers."""

    def test_media_marker_on_track(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.add_callout('clip', 0.0, 10.0)
        track.markers.add('CuePoint', seconds_to_ticks(2.5))
        open_in_camtasia(project)

    def test_media_marker_position_within_clip(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.add_callout('clip', 5.0, 20.0)
        # Marker inside the clip's time range
        track.markers.add('Mid', seconds_to_ticks(15.0))
        open_in_camtasia(project)


class TestCaptions:
    """Captions via project.add_caption and timeline.add_caption."""

    def test_basic_caption(self, project):
        project.add_caption('Hello world', 0.0, 3.0)
        open_in_camtasia(project)

    def test_caption_with_styling(self, project):
        project.add_caption(
            'Styled text',
            1.0,
            4.0,
            font_size=48.0,
            font_color=(1.0, 0.0, 0.0),
        )
        open_in_camtasia(project)

    def test_multiple_captions_in_sequence(self, project):
        project.add_caption('First', 0.0, 2.0)
        project.add_caption('Second', 2.0, 2.0)
        project.add_caption('Third', 4.0, 2.0)
        open_in_camtasia(project)

    def test_captions_on_different_tracks(self, project):
        project.add_caption('Track A', 0.0, 3.0, track_name='Subs-A')
        project.add_caption('Track B', 0.0, 3.0, track_name='Subs-B')
        open_in_camtasia(project)


class TestChapterMarkers:
    """Batch chapter markers via project.add_chapter_markers."""

    def test_add_chapter_markers_batch(self, project):
        chapters = [
            (0.0, 'Introduction'),
            (10.0, 'Setup'),
            (25.0, 'Demo'),
            (45.0, 'Conclusion'),
        ]
        project.add_chapter_markers(chapters)
        open_in_camtasia(project)


class TestMarkerCaptionCombination:
    """Markers and captions coexisting on the same timeline."""

    def test_markers_and_captions_together(self, project):
        project.timeline.markers.add('Chapter1', seconds_to_ticks(0.0))
        project.timeline.markers.add('Chapter2', seconds_to_ticks(5.0))
        project.add_caption('Welcome', 0.0, 3.0)
        project.add_caption('Next section', 5.0, 3.0)
        open_in_camtasia(project)
