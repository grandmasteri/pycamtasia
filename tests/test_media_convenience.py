"""Tests for MediaBin convenience methods and Media.__repr__."""
from camtasia.media_bin.media_bin import Media, MediaBin, MediaType
from pathlib import Path


def _make_media(media_id, media_type_val, src="./media/test.mp4"):
    return {
        "id": media_id,
        "src": src,
        "rect": [0, 0, 1920, 1080],
        "lastMod": "20190606T103830",
        "sourceTracks": [{"range": [0, 1000], "type": media_type_val, "editRate": 1000,
                          "trackRect": [0, 0, 1920, 1080], "sampleRate": 0,
                          "bitDepth": 0, "numChannels": 0}],
    }


def _make_bin(entries):
    return MediaBin(entries, Path("/tmp"))


class TestFindByType:
    def test_find_by_type_returns_matching(self):
        entries = [
            _make_media(1, 0),  # Video
            _make_media(2, 2, "./media/song.mp3"),  # Audio
            _make_media(3, 0),  # Video
        ]
        mb = _make_bin(entries)
        result = mb.find_by_type(MediaType.Video)
        assert {m.id for m in result} == {1, 3}
        assert all(m.type == MediaType.Video for m in result)

    def test_find_by_type_empty(self):
        entries = [_make_media(1, 0)]
        mb = _make_bin(entries)
        assert mb.find_by_type(MediaType.Audio) == []


class TestAudioFilesProperty:
    def test_audio_files_property(self):
        entries = [
            _make_media(1, 2, "./media/a.wav"),
            _make_media(2, 0),
            _make_media(3, 2, "./media/b.wav"),
        ]
        mb = _make_bin(entries)
        assert {m.id for m in mb.audio_files} == {1, 3}
        assert all(m.type == MediaType.Audio for m in mb.audio_files)


class TestVideoFilesProperty:
    def test_video_files_property(self):
        entries = [
            _make_media(1, 0),
            _make_media(2, 1, "./media/pic.png"),
            _make_media(3, 0),
        ]
        mb = _make_bin(entries)
        assert {m.id for m in mb.video_files} == {1, 3}
        assert all(m.type == MediaType.Video for m in mb.video_files)


class TestImageFilesProperty:
    def test_image_files_property(self):
        entries = [
            _make_media(1, 1, "./media/a.png"),
            _make_media(2, 1, "./media/b.jpg"),
            _make_media(3, 0),
        ]
        mb = _make_bin(entries)
        assert {m.id for m in mb.image_files} == {1, 2}
        assert all(m.type == MediaType.Image for m in mb.image_files)


class TestMediaRepr:
    def test_media_repr(self):
        data = _make_media(42, 0, "./media/clip.mp4")
        m = Media(data)
        assert repr(m) == "Media(id=42, identity='clip', type=Video)"
