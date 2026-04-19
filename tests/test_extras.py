"""Tests for camtasia.extras module — media_markers utility."""
from __future__ import annotations

from unittest.mock import MagicMock

from camtasia.extras import media_markers
from camtasia.timeline.marker import Marker


class TestMediaMarkers:
    """Tests for the media_markers generator."""

    def test_yields_marker_media_track_tuples(self):
        marker = Marker(name="m1", time=100)
        media = MagicMock()
        media.markers = [marker]
        track = MagicMock()
        track.medias = [media]
        project = MagicMock()
        project.timeline.tracks = [track]

        actual_result = list(media_markers(project))
        assert actual_result == [(marker, media, track)]

    def test_empty_project(self):
        project = MagicMock()
        project.timeline.tracks = []
        assert list(media_markers(project)) == []

    def test_media_with_no_markers(self):
        media = MagicMock()
        media.markers = []
        track = MagicMock()
        track.medias = [media]
        project = MagicMock()
        project.timeline.tracks = [track]

        assert list(media_markers(project)) == []
