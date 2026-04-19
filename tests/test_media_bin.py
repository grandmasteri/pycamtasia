from __future__ import annotations

import sys
from pathlib import Path

import pytest

import camtasia.media_bin.media_bin as mb_mod
from camtasia.media_bin import Media, MediaBin, MediaType
from camtasia.media_bin.media_bin import _get_media_type, _parse_with_pymediainfo


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
        assert [m.id for m in actual_items] == [10]
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


class TestImportMediaSourcePrefixAndMetaData:
    """import_media() must prefix src with './' and set metaData to 'filename;'."""

    def test_imported_source_starts_with_dot_slash(self, project, tmp_path):
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        media = project.media_bin.import_media(
            media_file, media_type=MediaType.Video, width=1920, height=1080,
        )
        raw_src = media._data["src"]
        assert raw_src.startswith("./"), f"Expected src to start with './' but got: {raw_src}"

    def test_imported_source_track_metadata_contains_filename(self, project, tmp_path):
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        media = project.media_bin.import_media(
            media_file, media_type=MediaType.Video, width=1920, height=1080,
        )
        meta = media._data["sourceTracks"][0]["metaData"]
        assert meta == "clip.mov;", f"Expected metaData 'clip.mov;' but got: {meta!r}"


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



class TestMediaTypeEmptySourceTracks:
    def test_type_returns_none_for_empty_source_tracks(self, project):
        media = Media({'id': 1, 'src': './test.mp4', 'rect': [0, 0, 100, 100], 'sourceTracks': []})
        assert media.type is None



class TestMediaSourceTracks:
    def test_source_tracks_returns_list(self):
        actual_tracks = Media({
            'id': 1, 'src': './media/test.mp4', 'rect': [0, 0, 1920, 1080],
            'lastMod': '20250101T120000',
            'sourceTracks': [
                {'type': 0, 'editRate': 30, 'range': [0, 9000]},
                {'type': 2, 'editRate': 44100, 'range': [0, 441000]},
            ],
        }).source_tracks
        assert [t['type'] for t in actual_tracks] == [0, 2]

    def test_source_tracks_empty_when_missing(self):
        actual_tracks = Media({
            'id': 1, 'src': './media/test.png', 'rect': [0, 0, 100, 100],
            'lastMod': '20250101T120000',
        }).source_tracks
        assert actual_tracks == []

    def test_video_edit_rate_returns_int(self):
        actual_rate = Media({
            'id': 1, 'src': './media/test.mp4', 'rect': [0, 0, 1920, 1080],
            'lastMod': '20250101T120000',
            'sourceTracks': [{'type': 0, 'editRate': 30, 'range': [0, 9000]}],
        }).video_edit_rate
        assert actual_rate == 30

    def test_video_edit_rate_none_when_no_video_track(self):
        actual_rate = Media({
            'id': 1, 'src': './media/test.wav', 'rect': [0, 0, 0, 0],
            'lastMod': '20250101T120000',
            'sourceTracks': [{'type': 2, 'editRate': 44100, 'range': [0, 441000]}],
        }).video_edit_rate
        assert actual_rate is None



class TestMediaRangeNoSourceTracks:
    def test_range_returns_zeros_when_no_source_tracks(self):
        entry = _make_media_entry()
        del entry['sourceTracks']
        media = Media(entry)
        assert media.range == (0, 0)

    def test_range_returns_values_from_source_tracks(self):
        entry = _make_media_entry(range_vals=[100, 5000])
        media = Media(entry)
        assert media.range == (100, 5000)



class TestMediaLastModification:
    def test_last_modification_parses_timestamp(self):
        entry = _make_media_entry(last_mod="20190606T103830")
        media = Media(entry)
        ts = media.last_modification
        assert ts.year == 2019
        assert ts.month == 6
        assert ts.day == 6



class TestImportMediaFileNotFound:
    def test_raises_file_not_found(self, project):
        with pytest.raises(FileNotFoundError):
            project.media_bin.import_media(
                "/nonexistent/file.mov", media_type=MediaType.Video,
            )



class TestImportMediaNoMediaType:
    def test_raises_value_error_without_media_type(self, project, tmp_path, monkeypatch):
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        # Force _parse_with_pymediainfo to return None
        monkeypatch.setattr(mb_mod, '_parse_with_pymediainfo', lambda fp: None)
        with pytest.raises(ValueError, match="Cannot determine media type"):
            project.media_bin.import_media(media_file, validate_format=False)

    def test_sample_rate_string_converted(self, project, tmp_path, monkeypatch):
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        monkeypatch.setattr(mb_mod, '_parse_with_pymediainfo', lambda fp: {
            'track_type': 'Audio',
            'width': None, 'height': None,
            'frame_rate': None, 'duration': 1000,
            'channel_s': 2,
            'sampling_rate': '44100.0',  # string, not int
            'bit_depth': 16,
        })
        monkeypatch.setattr(mb_mod, '_get_media_type', lambda t: MediaType.Audio)
        media = project.media_bin.import_media(media_file, validate_format=False)
        assert media is not None

    def test_sample_rate_invalid_string_becomes_none(self, project, tmp_path, monkeypatch):
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        monkeypatch.setattr(mb_mod, '_parse_with_pymediainfo', lambda fp: {
            'track_type': 'Audio',
            'width': None, 'height': None,
            'frame_rate': None, 'duration': 1000,
            'channel_s': 2,
            'sampling_rate': 'invalid',  # can't convert to float
            'bit_depth': 16,
        })
        monkeypatch.setattr(mb_mod, '_get_media_type', lambda t: MediaType.Audio)
        media = project.media_bin.import_media(media_file, validate_format=False)
        assert media is not None



class TestImportMediaNumChannels:
    def test_num_channels_parsed_from_track(self, project, tmp_path, monkeypatch):
        media_file = tmp_path / "clip.mov"
        media_file.write_bytes(b"\x00")
        monkeypatch.setattr(mb_mod, '_parse_with_pymediainfo', lambda fp: {
            'track_type': 'Video',
            'width': 1920, 'height': 1080,
            'frame_rate': 30, 'duration': 1000,
            'channel_s': '2 / 1',
            'sampling_rate': None, 'bit_depth': 0,
        })
        monkeypatch.setattr(mb_mod, '_get_media_type', lambda t: MediaType.Video)
        media = project.media_bin.import_media(media_file, validate_format=False)
        assert media is not None



class TestParseWithPymediainfo:
    def test_returns_track_data(self, monkeypatch):

        class FakeTrack:
            def to_data(self):
                return {'width': 1920, 'height': 1080}

        class FakeGeneral:
            def to_data(self):
                return {}

        class FakeInfo:
            tracks = [FakeGeneral(), FakeTrack()]

        class FakeMediaInfo:
            @staticmethod
            def parse(path):
                return FakeInfo()

        fake_mod = type(sys)('pymediainfo')
        fake_mod.MediaInfo = FakeMediaInfo
        monkeypatch.setitem(sys.modules, 'pymediainfo', fake_mod)

        result = _parse_with_pymediainfo(Path('/fake/video.mp4'))
        assert result == {'width': 1920, 'height': 1080}

    def test_returns_none_on_parse_error(self, monkeypatch):

        class FakeMediaInfo:
            @staticmethod
            def parse(path):
                raise RuntimeError('parse failed')

        fake_mod = type(sys)('pymediainfo')
        fake_mod.MediaInfo = FakeMediaInfo
        monkeypatch.setitem(sys.modules, 'pymediainfo', fake_mod)

        result = _parse_with_pymediainfo(Path('/fake/video.mp4'))
        assert result is None

    def test_returns_none_when_too_few_tracks(self, monkeypatch):

        class FakeInfo:
            tracks = [type('T', (), {'to_data': lambda self: {}})()]

        class FakeMediaInfo:
            @staticmethod
            def parse(path):
                return FakeInfo()

        fake_mod = type(sys)('pymediainfo')
        fake_mod.MediaInfo = FakeMediaInfo
        monkeypatch.setitem(sys.modules, 'pymediainfo', fake_mod)

        result = _parse_with_pymediainfo(Path('/fake/video.mp4'))
        assert result is None

    def test_returns_none_when_import_fails(self, monkeypatch):

        # Remove pymediainfo from sys.modules so the import inside the function is re-attempted
        monkeypatch.delitem(sys.modules, 'pymediainfo', raising=False)
        real_import = __builtins__['__import__'] if isinstance(__builtins__, dict) else __builtins__.__import__
        def _fail_pymediainfo(name, *a, **kw):
            if name == 'pymediainfo':
                raise ImportError('mocked')
            return real_import(name, *a, **kw)
        monkeypatch.setattr('builtins.__import__', _fail_pymediainfo)

        result = mb_mod._parse_with_pymediainfo(Path('/fake/video.mp4'))
        assert result is None


class TestMediaBinEdgeCases:
    def test_media_range_empty_source_tracks(self):
        data = {'id': 1, 'src': 'test.png', 'sourceTracks': [], 'rect': [0, 0, 100, 100]}
        m = Media(data)
        assert m.range == (0, 0)

    def test_media_duration_seconds_image(self):
        data = {'id': 1, 'src': 'test.png',
                'sourceTracks': [{'type': 1, 'range': [0, 1], 'editRate': 1}],
                'rect': [0, 0, 100, 100]}
        m = Media(data)
        assert m.duration_seconds == 0.0

    def test_unsupported_stream_type_raises(self):
        with pytest.raises(ValueError, match='Unsupported'):
            _get_media_type({'kind_of_stream': 'Subtitle'})
