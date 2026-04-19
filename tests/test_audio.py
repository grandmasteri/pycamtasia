"""Tests for camtasia.timeline.clips.audio — AMFile clip type."""
from __future__ import annotations

from camtasia.timeline.clips import AMFile
from camtasia.timing import EDIT_RATE


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _base_clip_dict(**overrides) -> dict:
    base = {
        "id": 14,
        "_type": "AMFile",
        "src": 3,
        "start": 0,
        "duration": 106051680000,
        "mediaStart": 0,
        "mediaDuration": 113484000000,
        "scalar": 1,
    }
    base.update(overrides)
    return base


def _amfile_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="AMFile",
        channelNumber="0,1",
        attributes={"ident": "voiceover", "gain": 0.8, "mixToMono": False, "loudnessNormalization": True},
    )
    d.update(overrides)
    return d


def _base(**kw) -> dict:
    d = {
        "id": 1, "_type": "AMFile", "src": 1,
        "start": 0, "duration": EDIT_RATE * 10,
        "mediaStart": 0, "mediaDuration": EDIT_RATE * 10, "scalar": 1,
    }
    d.update(kw)
    return d


# ------------------------------------------------------------------
# AMFile properties
# ------------------------------------------------------------------

def test_amfile_properties() -> None:
    clip = AMFile(_amfile_dict())
    assert clip.channel_number == "0,1"
    assert clip.gain == 0.8
    assert clip.loudness_normalization is True


def test_amfile_gain_setter_mutates_dict() -> None:
    data = _amfile_dict()
    clip = AMFile(data)
    clip.gain = 1.5
    assert data["attributes"]["gain"] == 1.5


def test_amfile_defaults() -> None:
    data = _base_clip_dict(_type="AMFile")
    clip = AMFile(data)
    assert clip.channel_number == "0"
    assert clip.gain == 1.0
    assert clip.loudness_normalization is False


# ------------------------------------------------------------------
# AMFile: channel_number setter, loudness_normalization setter
# ------------------------------------------------------------------

class TestAMFileMissing:
    def test_channel_number_setter(self):
        data = _base(_type="AMFile")
        clip = AMFile(data)
        clip.channel_number = "0,1"
        assert data["channelNumber"] == "0,1"

    def test_loudness_normalization_setter(self):
        data = _base(_type="AMFile")
        clip = AMFile(data)
        clip.loudness_normalization = True
        assert data["attributes"]["loudnessNormalization"] is True


# ------------------------------------------------------------------
# is_silent for AMFile
# ------------------------------------------------------------------

def test_non_unified_silent_when_gain_zero():
    clip = AMFile(_amfile_dict(attributes={'ident': '', 'gain': 0.0, 'mixToMono': False, 'loudnessNormalization': False}))
    assert clip.is_silent is True
