"""Tests for the legacy camtasia/operations.py — add_media_to_track and remove_media."""
from __future__ import annotations

import importlib.util
import pathlib
from unittest.mock import MagicMock

import pytest

# Load the legacy operations.py directly (it coexists with the operations/ package)
_legacy_path = pathlib.Path(__file__).parent.parent / "src" / "camtasia" / "operations.py"
_spec = importlib.util.spec_from_file_location("camtasia._operations_legacy", str(_legacy_path))
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)

add_media_to_track = _legacy.add_media_to_track
remove_media = _legacy.remove_media


class TestAddMediaToTrack:
    """Tests for add_media_to_track function."""

    def test_adds_media_to_specified_track(self):
        media_obj = MagicMock()
        track = MagicMock()
        proj = MagicMock()
        proj.timeline.tracks.__getitem__ = MagicMock(return_value=track)
        proj.media_bin.__getitem__ = MagicMock(return_value=media_obj)

        add_media_to_track(proj, 0, "media-1", start=100, duration=200, effects=["fx"])
        track.add_media.assert_called_once_with(media_obj, 100, 200, ["fx"])


class TestRemoveMedia:
    """Tests for remove_media function."""

    def test_removes_media_with_no_track_references(self):
        track = MagicMock()
        track.medias = []
        project = MagicMock()
        project.timeline.tracks = [track]

        remove_media(project, "media-1")
        project.media_bin.__delitem__.assert_called_once_with("media-1")

    def test_raises_when_track_references_exist_and_clear_false(self):
        track_media = MagicMock()
        track_media.source = "media-1"
        track_media.id = "tm-1"
        track = MagicMock()
        track.medias = [track_media]
        project = MagicMock()
        project.timeline.tracks = [track]

        with pytest.raises(ValueError, match="references exist on tracks"):
            remove_media(project, "media-1", clear_tracks=False)

    def test_clears_track_references_when_clear_tracks_true(self):
        track_media = MagicMock()
        track_media.source = "media-1"
        track_media.id = "tm-1"
        medias_mock = MagicMock()
        medias_mock.__iter__ = MagicMock(return_value=iter([track_media]))
        track = MagicMock()
        track.medias = medias_mock
        project = MagicMock()
        project.timeline.tracks = [track]

        remove_media(project, "media-1", clear_tracks=True)
        medias_mock.__delitem__.assert_called_once_with("tm-1")
        project.media_bin.__delitem__.assert_called_once_with("media-1")
