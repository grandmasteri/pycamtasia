"""Tests for the title preset API."""
from __future__ import annotations

from typing import Any

from camtasia.timing import EDIT_RATE
from camtasia.timeline.track import Track


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


class TestAddTitleCenteredPreset:
    def test_add_title_centered_preset(self):
        track = _make_track()
        clip = track.add_title("Hello", 0, 5)

        assert clip.text == "Hello"
        assert clip.font["name"] == "Montserrat"
        assert clip.font["weight"] == "Regular"
        assert clip.font["size"] == 64.0
        assert clip.font["color-red"] == 1.0
        assert clip.font["color-green"] == 1.0
        assert clip.font["color-blue"] == 1.0
        assert clip.definition["horizontal-alignment"] == "center"
        assert clip.definition["vertical-alignment"] == "center"
        assert clip.definition["width"] == 934.5
        assert clip.definition["height"] == 253.9
        assert clip.definition["resize-behavior"] == "resizeText"
        assert clip._data["parameters"]["translation0"] == -416.6
        assert clip._data["parameters"]["translation1"] == -274.8


class TestCalloutPosition:
    def test_callout_position(self):
        track = _make_track()
        clip = track.add_callout("test", 0, 3)
        clip.position(100.5, -200.3)

        assert clip._data["parameters"]["translation0"] == 100.5
        assert clip._data["parameters"]["translation1"] == -200.3


class TestCalloutSetAlignment:
    def test_callout_set_alignment(self):
        track = _make_track()
        clip = track.add_callout("test", 0, 3)
        clip.set_alignment("left", "top")

        assert clip.definition["horizontal-alignment"] == "left"
        assert clip.definition["vertical-alignment"] == "top"


class TestCalloutSetSize:
    def test_callout_set_size(self):
        track = _make_track()
        clip = track.add_callout("test", 0, 3)
        clip.set_size(500.0, 200.0)

        assert clip.definition["width"] == 500.0
        assert clip.definition["height"] == 200.0
        assert clip.definition["resize-behavior"] == "resizeText"
