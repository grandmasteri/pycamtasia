"""Tests for LutEffect advanced blending/preset properties and save_lut_preset."""
from __future__ import annotations

import pytest

from camtasia.effects.base import effect_from_dict
from camtasia.effects.visual import LutEffect
from camtasia.timeline.clips.base import BaseClip
from camtasia.timing import EDIT_RATE, seconds_to_ticks
from camtasia.types import EffectName, LutPreset


def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _make_lut_data(**overrides) -> dict:
    """Build a minimal LutEffect dict with all parameters."""
    params = {
        "lutSource": "Tasteful.cube",
        "lut_intensity": 0.8,
        "channel": 0,
        "shadowRampStart": 0.0,
        "shadowRampEnd": 0.1,
        "highlightRampStart": 0.9,
        "highlightRampEnd": 1.0,
        "rangePreset": "default",
        "easeInTime": 0,
        "easeOutTime": 0,
    }
    params.update(overrides)
    return {
        "effectName": "LutEffect",
        "bypassed": False,
        "category": "categoryVisualEffects",
        "parameters": {k: _param(v) if isinstance(v, (int, float)) else v for k, v in params.items()},
    }


def _make_clip_with_lut(**lut_overrides) -> BaseClip:
    """Build a BaseClip with a LutEffect attached."""
    clip_data: dict = {
        "_type": "VMFile",
        "id": 1,
        "start": 0,
        "duration": seconds_to_ticks(10.0),
        "effects": [_make_lut_data(**lut_overrides)],
        "parameters": {},
        "metadata": {},
    }
    return BaseClip(clip_data)


class TestLutEffectDispatch:
    def test_effect_from_dict_returns_lut_effect(self):
        data = _make_lut_data()
        actual = effect_from_dict(data)
        assert type(actual) is LutEffect

    def test_name(self):
        lut = LutEffect(_make_lut_data())
        assert lut.name == "LutEffect"


class TestLutEffectExistingProperties:
    def test_lut_source_get_set(self):
        lut = LutEffect(_make_lut_data())
        assert lut.lut_source == "Tasteful.cube"
        lut.lut_source = "Warm.cube"
        assert lut.lut_source == "Warm.cube"

    def test_intensity_get_set(self):
        lut = LutEffect(_make_lut_data())
        assert lut.intensity == 0.8
        lut.intensity = 0.5
        assert lut.intensity == 0.5


class TestLutEffectRampProperties:
    def test_shadow_ramp_start(self):
        lut = LutEffect(_make_lut_data(shadowRampStart=0.1))
        assert lut.shadow_ramp_start == 0.1
        lut.shadow_ramp_start = 0.25
        assert lut.shadow_ramp_start == 0.25

    def test_shadow_ramp_end(self):
        lut = LutEffect(_make_lut_data(shadowRampEnd=0.2))
        assert lut.shadow_ramp_end == 0.2
        lut.shadow_ramp_end = 0.35
        assert lut.shadow_ramp_end == 0.35

    def test_highlight_ramp_start(self):
        lut = LutEffect(_make_lut_data(highlightRampStart=0.7))
        assert lut.highlight_ramp_start == 0.7
        lut.highlight_ramp_start = 0.8
        assert lut.highlight_ramp_start == 0.8

    def test_highlight_ramp_end(self):
        lut = LutEffect(_make_lut_data(highlightRampEnd=0.95))
        assert lut.highlight_ramp_end == 0.95
        lut.highlight_ramp_end = 1.0
        assert lut.highlight_ramp_end == 1.0


class TestLutEffectChannel:
    @pytest.mark.parametrize(
        ("raw_value", "expected_str"),
        [(0, "all"), (1, "red"), (2, "green"), (3, "blue")],
    )
    def test_channel_int_to_str(self, raw_value, expected_str):
        lut = LutEffect(_make_lut_data(channel=raw_value))
        assert lut.channel == expected_str

    @pytest.mark.parametrize(
        ("set_str", "expected_raw"),
        [("all", 0), ("red", 1), ("green", 2), ("blue", 3)],
    )
    def test_channel_set_by_str(self, set_str, expected_raw):
        lut = LutEffect(_make_lut_data())
        lut.channel = set_str
        assert lut.get_parameter("channel") == expected_raw

    def test_channel_set_by_int(self):
        lut = LutEffect(_make_lut_data())
        lut.channel = 2
        assert lut.get_parameter("channel") == 2
        assert lut.channel == "green"

    def test_channel_unknown_int_defaults_to_all(self):
        lut = LutEffect(_make_lut_data(channel=99))
        assert lut.channel == "all"

    def test_channel_str_already_stored(self):
        """If the parameter is stored as a string, return it directly."""
        data = _make_lut_data()
        data["parameters"]["channel"] = "red"
        lut = LutEffect(data)
        assert lut.channel == "red"


class TestLutEffectRangePreset:
    def test_get_set(self):
        lut = LutEffect(_make_lut_data(rangePreset="default"))
        assert lut.range_preset == "default"
        lut.range_preset = "shadows"
        assert lut.range_preset == "shadows"


class TestLutEffectEase:
    def test_ease_in_seconds_roundtrip(self):
        lut = LutEffect(_make_lut_data(easeInTime=0))
        lut.ease_in_seconds = 2.0
        assert lut.get_parameter("easeInTime") == seconds_to_ticks(2.0)
        assert abs(lut.ease_in_seconds - 2.0) < 1e-6

    def test_ease_out_seconds_roundtrip(self):
        lut = LutEffect(_make_lut_data(easeOutTime=0))
        lut.ease_out_seconds = 1.5
        assert lut.get_parameter("easeOutTime") == seconds_to_ticks(1.5)
        assert abs(lut.ease_out_seconds - 1.5) < 1e-6

    def test_ease_zero(self):
        lut = LutEffect(_make_lut_data(easeInTime=0, easeOutTime=0))
        assert lut.ease_in_seconds == 0.0
        assert lut.ease_out_seconds == 0.0


class TestLutPresetEnum:
    def test_values(self):
        assert LutPreset.BLACK_AND_WHITE == "Black and White.cube"
        assert LutPreset.VINTAGE == "Vintage.cube"
        assert LutPreset.WARM == "Warm.cube"
        assert LutPreset.COOL == "Cool.cube"
        assert LutPreset.HIGH_CONTRAST == "High Contrast.cube"

    def test_is_str(self):
        assert isinstance(LutPreset.WARM, str)

    def test_usable_as_lut_source(self):
        lut = LutEffect(_make_lut_data())
        lut.lut_source = LutPreset.VINTAGE.value
        assert lut.lut_source == "Vintage.cube"


class TestSaveLutPreset:
    def test_saves_params_to_metadata(self):
        clip = _make_clip_with_lut()
        clip.save_lut_preset("my_look")
        presets = clip.metadata["lutPresets"]
        assert "my_look" in presets
        saved = presets["my_look"]
        assert saved["lut_intensity"]["defaultValue"] == 0.8
        assert saved["lutSource"] == "Tasteful.cube"

    def test_multiple_presets(self):
        clip = _make_clip_with_lut()
        clip.save_lut_preset("look_a")
        # Modify the effect
        lut = LutEffect(clip._data["effects"][0])
        lut.intensity = 0.3
        clip.save_lut_preset("look_b")
        presets = clip.metadata["lutPresets"]
        assert presets["look_a"]["lut_intensity"]["defaultValue"] == 0.8
        assert presets["look_b"]["lut_intensity"]["defaultValue"] == 0.3

    def test_raises_without_lut_effect(self):
        clip_data: dict = {
            "_type": "VMFile",
            "id": 2,
            "start": 0,
            "duration": 1000,
            "effects": [],
            "parameters": {},
            "metadata": {},
        }
        clip = BaseClip(clip_data)
        with pytest.raises(ValueError, match="No LutEffect found"):
            clip.save_lut_preset("nope")

    def test_preset_via_add_lut_effect(self):
        """save_lut_preset works with a LUT added via add_lut_effect."""
        clip_data: dict = {
            "_type": "VMFile",
            "id": 3,
            "start": 0,
            "duration": seconds_to_ticks(5.0),
            "effects": [],
            "parameters": {},
            "metadata": {},
        }
        clip = BaseClip(clip_data)
        clip.add_lut_effect(intensity=0.6)
        clip.save_lut_preset("from_api")
        saved = clip.metadata["lutPresets"]["from_api"]
        assert saved["lut_intensity"] == 0.6
        assert saved["channel"] == 0
