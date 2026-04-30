"""Tests for Media zoom_metadata property."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.media_bin import Media


def _make_media_entry(
    media_id: int = 1,
    src: str = "./media/clip.mov",
    rect: list[int] | None = None,
    media_type: int = 0,
    range_vals: list[int] | None = None,
    last_mod: str = "20190606T103830",
    metadata: dict | None = None,
) -> dict:
    entry: dict = {
        "id": media_id,
        "src": src,
        "rect": rect or [0, 0, 1920, 1080],
        "lastMod": last_mod,
        "sourceTracks": [
            {
                "range": range_vals or [0, 5000],
                "type": media_type,
                "editRate": 1000,
                "trackRect": rect or [0, 0, 1920, 1080],
                "sampleRate": 0,
                "bitDepth": 0,
                "numChannels": 0,
            }
        ],
    }
    if metadata is not None:
        entry["metadata"] = metadata
    return entry


class TestZoomMetadataGetter:
    def test_returns_empty_strings_when_no_metadata(self):
        media = Media(_make_media_entry())
        assert media.zoom_metadata == {
            "meeting_id": "",
            "host": "",
            "topic": "",
            "date": "",
        }

    def test_returns_empty_strings_when_no_zoom_key(self):
        entry = _make_media_entry(metadata={"timeAdded": "20250101T000000"})
        media = Media(entry)
        assert media.zoom_metadata == {
            "meeting_id": "",
            "host": "",
            "topic": "",
            "date": "",
        }

    def test_returns_stored_values(self):
        zoom = {"meeting_id": "123", "host": "alice", "topic": "Demo", "date": "2025-01-01"}
        entry = _make_media_entry(metadata={"zoom": zoom})
        media = Media(entry)
        assert media.zoom_metadata == zoom

    def test_returns_partial_values_with_defaults(self):
        entry = _make_media_entry(metadata={"zoom": {"meeting_id": "456"}})
        media = Media(entry)
        expected = {"meeting_id": "456", "host": "", "topic": "", "date": ""}
        assert media.zoom_metadata == expected

    def test_getter_does_not_mutate_underlying_data(self):
        entry = _make_media_entry(metadata={"zoom": {"meeting_id": "789"}})
        media = Media(entry)
        result = media.zoom_metadata
        result["host"] = "modified"
        assert media._data["metadata"]["zoom"].get("host") is None


class TestZoomMetadataSetter:
    def test_sets_all_fields(self):
        media = Media(_make_media_entry())
        zoom = {"meeting_id": "100", "host": "bob", "topic": "Review", "date": "2025-06-15"}
        media.zoom_metadata = zoom
        assert media._data["metadata"]["zoom"] == zoom

    def test_creates_metadata_dict_when_absent(self):
        entry = _make_media_entry()
        assert "metadata" not in entry
        media = Media(entry)
        media.zoom_metadata = {"meeting_id": "1"}
        assert "zoom" in media._data["metadata"]

    def test_preserves_existing_metadata(self):
        entry = _make_media_entry(metadata={"timeAdded": "20250101T000000"})
        media = Media(entry)
        media.zoom_metadata = {"meeting_id": "2", "host": "carol", "topic": "Sync", "date": "2025-03-01"}
        assert media._data["metadata"]["timeAdded"] == "20250101T000000"

    def test_overwrites_previous_zoom(self):
        media = Media(_make_media_entry())
        media.zoom_metadata = {"meeting_id": "first", "host": "", "topic": "", "date": ""}
        media.zoom_metadata = {"meeting_id": "second", "host": "x", "topic": "y", "date": "z"}
        assert media.zoom_metadata["meeting_id"] == "second"

    def test_missing_keys_default_to_empty_string(self):
        media = Media(_make_media_entry())
        media.zoom_metadata = {"topic": "Only topic"}
        assert media.zoom_metadata == {
            "meeting_id": "",
            "host": "",
            "topic": "Only topic",
            "date": "",
        }

    def test_roundtrip_set_then_get(self):
        media = Media(_make_media_entry())
        zoom = {"meeting_id": "999", "host": "dave", "topic": "Launch", "date": "2025-12-31"}
        media.zoom_metadata = zoom
        assert media.zoom_metadata == zoom
