"""Tests for Media proxy and reverse functionality."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.media_bin import Media, MediaBin, MediaType
from camtasia.library.library import Library


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


class TestCreateProxy:
    def test_sets_proxy_path(self):
        media = Media(_make_media_entry())
        media.create_proxy(Path("/tmp/proxy.mp4"))
        assert media._data["metadata"]["proxyPath"] == "/tmp/proxy.mp4"

    def test_preserves_existing_metadata(self):
        entry = _make_media_entry(metadata={"timeAdded": "20250101T000000"})
        media = Media(entry)
        media.create_proxy(Path("/proxy.mov"))
        assert media._data["metadata"]["timeAdded"] == "20250101T000000"
        assert media._data["metadata"]["proxyPath"] == "/proxy.mov"

    def test_overwrites_previous_proxy(self):
        media = Media(_make_media_entry())
        media.create_proxy(Path("/first.mp4"))
        media.create_proxy(Path("/second.mp4"))
        assert media._data["metadata"]["proxyPath"] == "/second.mp4"

    def test_creates_metadata_dict_when_absent(self):
        entry = _make_media_entry()
        assert "metadata" not in entry
        media = Media(entry)
        media.create_proxy(Path("/proxy.mp4"))
        assert "metadata" in media._data


class TestDeleteProxy:
    def test_removes_proxy_path(self):
        entry = _make_media_entry(metadata={"proxyPath": "/tmp/proxy.mp4"})
        media = Media(entry)
        media.delete_proxy()
        assert "proxyPath" not in media._data["metadata"]

    def test_noop_when_no_proxy(self):
        entry = _make_media_entry(metadata={"timeAdded": "20250101T000000"})
        media = Media(entry)
        media.delete_proxy()
        assert media._data["metadata"] == {"timeAdded": "20250101T000000"}

    def test_noop_when_no_metadata(self):
        media = Media(_make_media_entry())
        media.delete_proxy()  # should not raise

    def test_create_then_delete_roundtrip(self):
        media = Media(_make_media_entry())
        media.create_proxy(Path("/proxy.mp4"))
        assert media._data["metadata"]["proxyPath"] == "/proxy.mp4"
        media.delete_proxy()
        assert "proxyPath" not in media._data["metadata"]


class TestReverse:
    def test_sets_reversed_flag(self):
        media = Media(_make_media_entry())
        media.reverse()
        assert media._data["metadata"]["reversed"] is True

    def test_adds_reversed_variant_to_source_tracks(self):
        media = Media(_make_media_entry(src="./clip.mov"))
        media.reverse()
        variants = media._data["sourceTracks"][0]["variants"]
        assert variants == [{"type": "reversed", "src": "./clip.mov"}]

    def test_idempotent_no_duplicate_variants(self):
        media = Media(_make_media_entry())
        media.reverse()
        media.reverse()
        variants = media._data["sourceTracks"][0]["variants"]
        assert len(variants) == 1

    def test_preserves_existing_metadata(self):
        entry = _make_media_entry(metadata={"timeAdded": "20250101T000000"})
        media = Media(entry)
        media.reverse()
        assert media._data["metadata"]["timeAdded"] == "20250101T000000"
        assert media._data["metadata"]["reversed"] is True


class TestAddToLibrary:
    def test_bridge_creates_library_asset(self):
        entry = _make_media_entry(media_id=5, src="./media/intro.mov")
        data = [entry]
        media_bin = MediaBin(data, Path("/fake"))
        lib = Library("test")
        media = media_bin[5]
        asset = media_bin.add_to_library(media, lib)
        assert asset.name == "intro"
        assert asset.kind == "clip"
        assert len(lib) == 1

    def test_bridge_asset_payload_is_deep_copy(self):
        entry = _make_media_entry(media_id=1)
        media_bin = MediaBin([entry], Path("/fake"))
        lib = Library("test")
        media = media_bin[1]
        asset = media_bin.add_to_library(media, lib)
        # Mutating the asset payload should not affect the original
        asset.payload["extra"] = True
        assert "extra" not in entry
