from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.media_bin import Media, MediaBin, MediaType


def _make_media_entry(
    media_id: int = 1,
    src: str = "./media/clip.mov",
    rect: list[int] | None = None,
    media_type: int = 0,
    range_vals: list[int] | None = None,
    last_mod: str = "20190606T103830",
) -> dict:
    return {
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


class TestMediaBinEmpty:
    def test_empty_bin_has_zero_length(self):
        media_bin = MediaBin([], Path("/fake"))
        assert list(media_bin) == []

    def test_empty_bin_iteration_yields_nothing(self):
        media_bin = MediaBin([], Path("/fake"))
        assert list(media_bin) == []

    def test_empty_bin_next_id_returns_one(self):
        media_bin = MediaBin([], Path("/fake"))
        assert media_bin.next_id() == 1


class TestMediaBinAccess:
    def test_iteration_yields_media_objects(self):
        entry_a = _make_media_entry(media_id=1, src="./a.mov")
        entry_b = _make_media_entry(media_id=2, src="./b.mov")
        media_bin = MediaBin([entry_a, entry_b], Path("/fake"))
        actual_items = list(media_bin)
        assert all(isinstance(m, Media) for m in actual_items)
        actual_sources = [str(m.source) for m in actual_items]
        assert actual_sources == ["a.mov", "b.mov"]

    def test_getitem_by_id(self):
        entry = _make_media_entry(media_id=42, src="./clip.mov")
        media_bin = MediaBin([entry], Path("/fake"))
        actual_media = media_bin[42]
        assert actual_media.id == 42
        assert str(actual_media.source) == "clip.mov"

    def test_getitem_missing_id_raises_key_error(self):
        media_bin = MediaBin([_make_media_entry(media_id=1)], Path("/fake"))
        with pytest.raises(KeyError, match="No media with id 999"):
            media_bin[999]

    def test_delitem_removes_entry(self):
        entry = _make_media_entry(media_id=5)
        data = [entry]
        media_bin = MediaBin(data, Path("/fake"))
        del media_bin[5]
        assert list(media_bin) == []

    def test_delitem_missing_id_raises_key_error(self):
        media_bin = MediaBin([_make_media_entry(media_id=1)], Path("/fake"))
        with pytest.raises(KeyError, match="No media with id 999"):
            del media_bin[999]


class TestMediaBinMutation:
    def test_next_id_returns_max_plus_one(self):
        entries = [
            _make_media_entry(media_id=3),
            _make_media_entry(media_id=7),
            _make_media_entry(media_id=5),
        ]
        media_bin = MediaBin(entries, Path("/fake"))
        assert media_bin.next_id() == 8

    def test_add_media_entry_appends_and_returns_media(self):
        data: list[dict] = []
        media_bin = MediaBin(data, Path("/fake"))
        new_entry = _make_media_entry(media_id=10, src="./new.mov")
        actual_media = media_bin.add_media_entry(new_entry)
        assert isinstance(actual_media, Media)
        assert actual_media.id == 10
        assert str(actual_media.source) == "new.mov"
        actual_items = list(media_bin)
        assert len(actual_items) == 1
        assert actual_items[0].id == 10
        assert str(actual_items[0].source) == "new.mov"


class TestMediaProperties:
    def test_source(self):
        entry = _make_media_entry(src="./recordings/clip.trec")
        media = Media(entry)
        assert media.source == Path("./recordings/clip.trec")

    def test_identity(self):
        entry = _make_media_entry(src="./recordings/my_video.mov")
        media = Media(entry)
        assert media.identity == "my_video"

    def test_type_video(self):
        entry = _make_media_entry(media_type=MediaType.Video.value)
        media = Media(entry)
        assert media.type == MediaType.Video

    def test_type_image(self):
        entry = _make_media_entry(media_type=MediaType.Image.value)
        media = Media(entry)
        assert media.type == MediaType.Image

    def test_type_audio(self):
        entry = _make_media_entry(media_type=MediaType.Audio.value)
        media = Media(entry)
        assert media.type == MediaType.Audio

    def test_rect(self):
        entry = _make_media_entry(rect=[0, 0, 5120, 2880])
        media = Media(entry)
        assert media.rect == (0, 0, 5120, 2880)

    def test_dimensions(self):
        entry = _make_media_entry(rect=[0, 0, 1280, 720])
        media = Media(entry)
        assert media.dimensions == (1280, 720)


class TestMediaTypeEnum:
    @pytest.mark.parametrize(
        ("member", "expected_value"),
        [
            (MediaType.Video, 0),
            (MediaType.Image, 1),
            (MediaType.Audio, 2),
        ],
    )
    def test_enum_values(self, member: MediaType, expected_value: int):
        assert member.value == expected_value
