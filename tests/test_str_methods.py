"""Tests for Track.__str__ and BaseClip.__str__."""
from __future__ import annotations

from camtasia.timeline.clips import BaseClip, EDIT_RATE
from camtasia.timeline.track import Track


def _clip(**overrides) -> BaseClip:
    data: dict = {
        "id": 1,
        "_type": "VMFile",
        "src": 3,
        "start": 0,
        "duration": int(10 * EDIT_RATE),
        "mediaStart": 0,
        "mediaDuration": int(10 * EDIT_RATE),
        "scalar": 1,
    }
    data.update(overrides)
    return BaseClip(data)


def _track(name: str = "Track 1", medias: list | None = None) -> Track:
    attrs = {"ident": name}
    data = {"trackIndex": 0, "medias": medias or []}
    return Track(attrs, data)


class TestBaseClipStr:
    def test_basic(self) -> None:
        clip = _clip()
        assert str(clip) == "VMFile(id=1, 10.0s)"

    def test_audio_type(self) -> None:
        clip = _clip(_type="AMFile", id=42, duration=int(5.5 * EDIT_RATE))
        assert str(clip) == "AMFile(id=42, 5.5s)"

    def test_short_duration(self) -> None:
        clip = _clip(duration=int(0.3 * EDIT_RATE))
        assert str(clip) == "VMFile(id=1, 0.3s)"

    def test_zero_duration(self) -> None:
        clip = _clip(duration=0)
        assert str(clip) == "VMFile(id=1, 0.0s)"

    def test_str_differs_from_repr(self) -> None:
        clip = _clip()
        assert str(clip) != repr(clip)


class TestTrackStr:
    def test_empty_track(self) -> None:
        track = _track("Narration")
        assert str(track) == "Narration (0 clips, 0.0s)"

    def test_with_clips(self) -> None:
        medias = [
            {"id": 1, "_type": "VMFile", "start": 0, "duration": int(5 * EDIT_RATE)},
            {"id": 2, "_type": "VMFile", "start": int(5 * EDIT_RATE), "duration": int(3 * EDIT_RATE)},
        ]
        track = _track("Video", medias)
        assert str(track) == "Video (2 clips, 8.0s)"

    def test_single_clip(self) -> None:
        medias = [{"id": 1, "_type": "AMFile", "start": 0, "duration": int(12.5 * EDIT_RATE)}]
        track = _track("Audio", medias)
        assert str(track) == "Audio (1 clips, 12.5s)"

    def test_str_differs_from_repr(self) -> None:
        track = _track("My Track")
        assert str(track) != repr(track)
