"""Tests for add_media_to_track and remove_media."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from camtasia.operations import add_media_to_track, remove_media


class TestAddMediaToTrack:
    """Tests for add_media_to_track function."""

    def test_adds_media_to_specified_track(self):
        track = MagicMock()
        proj = MagicMock()
        proj.timeline.tracks.__getitem__ = MagicMock(return_value=track)
        media = MagicMock()
        media.range = (0, 200)
        media.type.value = 0  # Video
        proj.media_bin.__getitem__ = MagicMock(return_value=media)

        add_media_to_track(proj, 0, 42, start=100, duration=200)
        track.add_clip.assert_called_once_with("VMFile", 42, 100, 200, effects=[])

    def test_defaults_duration_from_media_range(self):
        track = MagicMock()
        proj = MagicMock()
        proj.timeline.tracks.__getitem__ = MagicMock(return_value=track)
        media = MagicMock()
        media.range = (10, 310)
        media.type.value = 2  # Audio
        proj.media_bin.__getitem__ = MagicMock(return_value=media)

        add_media_to_track(proj, 0, 42, start=0)
        track.add_clip.assert_called_once_with("AMFile", 42, 0, 300, effects=[])


class TestRemoveMedia:
    """Tests for remove_media function."""

    def test_removes_media_with_no_track_references(self):
        track = MagicMock()
        track.medias = []
        project = MagicMock()
        project.timeline.tracks = [track]

        remove_media(project, 42)
        project.media_bin.__delitem__.assert_called_once_with(42)

    def test_raises_when_track_references_exist_and_clear_false(self):
        clip = MagicMock()
        clip.source_id = 42
        clip.id = 1
        track = MagicMock()
        track.medias = [clip]
        project = MagicMock()
        project.timeline.tracks = [track]

        with pytest.raises(ValueError, match="references exist on tracks"):
            remove_media(project, 42, clear_tracks=False)

    def test_clears_track_references_when_clear_tracks_true(self):
        clip = MagicMock()
        clip.source_id = 42
        clip.id = 1
        track = MagicMock()
        track.medias = [clip]
        project = MagicMock()
        project.timeline.tracks = [track]

        remove_media(project, 42, clear_tracks=True)
        track.remove_clip.assert_called_once_with(1)
        project.media_bin.__delitem__.assert_called_once_with(42)


class TestAddMediaToTrackUnknownType:
    """Line 48: unknown media type raises ValueError."""

    def test_raises_on_unknown_media_type(self):
        track = MagicMock()
        proj = MagicMock()
        proj.timeline.tracks.__getitem__ = MagicMock(return_value=track)
        media = MagicMock()
        media.range = (0, 200)
        # Unknown type value
        media.type.value = 999  # not in _MEDIA_TYPE_TO_CLIP
        proj.media_bin.__getitem__ = MagicMock(return_value=media)

        with pytest.raises(ValueError, match="Unknown media type"):
            add_media_to_track(proj, 0, 42, start=100, duration=200)
