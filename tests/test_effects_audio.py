"""Tests for audio effect wrappers."""
from __future__ import annotations

import pytest

from camtasia.effects.audio import AudioCompression, ClipSpeedAudio, NoiseRemoval, Pitch
from camtasia.effects.base import effect_from_dict


def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


# ------------------------------------------------------------------
# Helpers: realistic effect dicts
# ------------------------------------------------------------------

def _noise_removal_dict() -> dict:
    return {
        "effectName": "VSTEffect-DFN3NoiseRemoval",
        "bypassed": False,
        "category": "categoryAudioEffects",
        "parameters": {
            "Amount": _param(0.8),
            "Bypass": _param(0.0),
            "Sensitivity": _param(0.5),
            "Reduction": _param(0.7),
        },
    }


def _audio_compression_dict() -> dict:
    return {
        "effectName": "AudioCompression",
        "bypassed": False,
        "category": "categoryAudioEffects",
        "parameters": {
            "ratio": _param(4.0),
            "threshold": _param(-20.0),
            "gain": _param(3.0),
            "volumeVariation": _param(0.5),
        },
    }


def _pitch_dict() -> dict:
    return {
        "effectName": "Pitch",
        "bypassed": False,
        "category": "categoryAudioEffects",
        "parameters": {
            "pitch": _param(2.0),
            "easeIn": _param(0.1),
            "easeOut": _param(0.2),
        },
    }


def _clip_speed_audio_dict() -> dict:
    return {
        "effectName": "ClipSpeedAudio",
        "bypassed": False,
        "category": "categoryAudioEffects",
        "parameters": {
            "speed": _param(1.5),
            "duration": _param(30000.0),
        },
    }


# ------------------------------------------------------------------
# effect_from_dict dispatch
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("effect_name", "expected_class"),
    [
        ("VSTEffect-DFN3NoiseRemoval", NoiseRemoval),
        ("AudioCompression", AudioCompression),
        ("Pitch", Pitch),
        ("ClipSpeedAudio", ClipSpeedAudio),
    ],
    ids=["NoiseRemoval", "AudioCompression", "Pitch", "ClipSpeedAudio"],
)
def test_effect_from_dict_dispatches_audio_effects(effect_name: str, expected_class: type) -> None:
    data = {"effectName": effect_name, "parameters": {}}
    assert type(effect_from_dict(data)) is expected_class


# ------------------------------------------------------------------
# NoiseRemoval
# ------------------------------------------------------------------

class TestNoiseRemoval:
    def test_amount(self) -> None:
        effect = NoiseRemoval(_noise_removal_dict())
        assert effect.amount == 0.8

    def test_amount_setter(self) -> None:
        data = _noise_removal_dict()
        effect = NoiseRemoval(data)
        effect.amount = 0.5
        assert data["parameters"]["Amount"]["defaultValue"] == 0.5

    def test_bypass(self) -> None:
        effect = NoiseRemoval(_noise_removal_dict())
        assert effect.bypass == 0.0

    def test_sensitivity(self) -> None:
        effect = NoiseRemoval(_noise_removal_dict())
        assert effect.sensitivity == 0.5

    def test_sensitivity_setter(self) -> None:
        data = _noise_removal_dict()
        effect = NoiseRemoval(data)
        effect.sensitivity = 0.9
        assert data["parameters"]["Sensitivity"]["defaultValue"] == 0.9

    def test_reduction(self) -> None:
        effect = NoiseRemoval(_noise_removal_dict())
        assert effect.reduction == 0.7

    def test_reduction_setter(self) -> None:
        data = _noise_removal_dict()
        effect = NoiseRemoval(data)
        effect.reduction = 0.3
        assert data["parameters"]["Reduction"]["defaultValue"] == 0.3


# ------------------------------------------------------------------
# AudioCompression
# ------------------------------------------------------------------

class TestAudioCompression:
    def test_ratio(self) -> None:
        effect = AudioCompression(_audio_compression_dict())
        assert effect.ratio == 4.0

    def test_threshold(self) -> None:
        effect = AudioCompression(_audio_compression_dict())
        assert effect.threshold == -20.0

    def test_gain(self) -> None:
        effect = AudioCompression(_audio_compression_dict())
        assert effect.gain == 3.0

    def test_volume_variation(self) -> None:
        effect = AudioCompression(_audio_compression_dict())
        assert effect.volume_variation == 0.5

    def test_setters_mutate_dict(self) -> None:
        data = _audio_compression_dict()
        effect = AudioCompression(data)
        effect.ratio = 8.0
        effect.threshold = -10.0
        effect.gain = 6.0
        effect.volume_variation = 1.0
        assert data["parameters"]["ratio"]["defaultValue"] == 8.0
        assert data["parameters"]["threshold"]["defaultValue"] == -10.0
        assert data["parameters"]["gain"]["defaultValue"] == 6.0
        assert data["parameters"]["volumeVariation"]["defaultValue"] == 1.0


# ------------------------------------------------------------------
# Pitch
# ------------------------------------------------------------------

class TestPitch:
    def test_pitch(self) -> None:
        effect = Pitch(_pitch_dict())
        assert effect.pitch == 2.0

    def test_ease_in(self) -> None:
        effect = Pitch(_pitch_dict())
        assert effect.ease_in == 0.1

    def test_ease_out(self) -> None:
        effect = Pitch(_pitch_dict())
        assert effect.ease_out == 0.2

    def test_setters_mutate_dict(self) -> None:
        data = _pitch_dict()
        effect = Pitch(data)
        effect.pitch = -3.0
        effect.ease_in = 0.5
        effect.ease_out = 0.8
        assert data["parameters"]["pitch"]["defaultValue"] == -3.0
        assert data["parameters"]["easeIn"]["defaultValue"] == 0.5
        assert data["parameters"]["easeOut"]["defaultValue"] == 0.8


# ------------------------------------------------------------------
# ClipSpeedAudio
# ------------------------------------------------------------------

class TestClipSpeedAudio:
    def test_speed(self) -> None:
        effect = ClipSpeedAudio(_clip_speed_audio_dict())
        assert effect.speed == 1.5

    def test_effect_duration(self) -> None:
        effect = ClipSpeedAudio(_clip_speed_audio_dict())
        assert effect.effect_duration == 30000.0

    def test_setters_mutate_dict(self) -> None:
        data = _clip_speed_audio_dict()
        effect = ClipSpeedAudio(data)
        effect.speed = 2.0
        effect.effect_duration = 60000.0
        assert data["parameters"]["speed"]["defaultValue"] == 2.0
        assert data["parameters"]["duration"]["defaultValue"] == 60000.0
