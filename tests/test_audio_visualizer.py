"""Tests for AudioVisualizer effect and AMFile.add_audio_visualizer."""
from __future__ import annotations

import pytest

from camtasia.effects.audio_visualizer import AudioVisualizer
from camtasia.effects.base import effect_from_dict
from camtasia.timeline.clips.audio import AMFile


def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _visualizer_dict(
    *,
    vis_type: str = "bars",
    color: tuple[float, float, float, float] = (1, 1, 1, 1),
    height: float = 100.0,
    sensitivity: float = 0.7,
) -> dict:
    return {
        "effectName": "AudioVisualizer",
        "bypassed": False,
        "category": "categoryAudioEffects",
        "parameters": {
            "type": vis_type,
            "color-red": color[0],
            "color-green": color[1],
            "color-blue": color[2],
            "color-alpha": color[3],
            "height": height,
            "sensitivity": sensitivity,
        },
    }


def _amfile_data() -> dict:
    """Minimal AMFile clip dict."""
    return {
        "_type": "AMFile",
        "id": 42,
        "start": 0,
        "duration": 705600000,
        "mediaStart": 0,
        "mediaDuration": 705600000,
        "scalar": "1",
        "src": 1,
        "trackNumber": 0,
        "attributes": {"ident": "narration"},
    }


# ------------------------------------------------------------------
# effect_from_dict dispatch
# ------------------------------------------------------------------

class TestEffectDispatch:
    def test_dispatches_to_audio_visualizer(self) -> None:
        data = {"effectName": "AudioVisualizer", "parameters": {}}
        assert type(effect_from_dict(data)) is AudioVisualizer


# ------------------------------------------------------------------
# AudioVisualizer properties
# ------------------------------------------------------------------

class TestAudioVisualizerProperties:
    def test_type_default(self) -> None:
        effect = AudioVisualizer(_visualizer_dict())
        assert effect.type == "bars"

    def test_type_setter(self) -> None:
        data = _visualizer_dict()
        effect = AudioVisualizer(data)
        effect.type = "wave"
        assert data["parameters"]["type"] == "wave"

    def test_type_setter_rejects_invalid(self) -> None:
        effect = AudioVisualizer(_visualizer_dict())
        with pytest.raises(ValueError, match="Invalid visualizer type"):
            effect.type = "invalid"

    def test_color_default(self) -> None:
        effect = AudioVisualizer(_visualizer_dict())
        assert effect.color == (1.0, 1.0, 1.0, 1.0)

    def test_color_setter(self) -> None:
        data = _visualizer_dict()
        effect = AudioVisualizer(data)
        effect.color = (0.5, 0.2, 0.8, 0.9)
        assert data["parameters"]["color-red"] == 0.5
        assert data["parameters"]["color-green"] == 0.2
        assert data["parameters"]["color-blue"] == 0.8
        assert data["parameters"]["color-alpha"] == 0.9

    def test_height_default(self) -> None:
        effect = AudioVisualizer(_visualizer_dict())
        assert effect.height == 100.0

    def test_height_setter(self) -> None:
        data = _visualizer_dict()
        effect = AudioVisualizer(data)
        effect.height = 200.0
        assert data["parameters"]["height"] == 200.0

    def test_sensitivity_default(self) -> None:
        effect = AudioVisualizer(_visualizer_dict())
        assert effect.sensitivity == 0.7

    def test_sensitivity_setter(self) -> None:
        data = _visualizer_dict()
        effect = AudioVisualizer(data)
        effect.sensitivity = 0.3
        assert data["parameters"]["sensitivity"] == 0.3


# ------------------------------------------------------------------
# AudioVisualizer with animated (dict) parameters
# ------------------------------------------------------------------

class TestAudioVisualizerAnimatedParams:
    def test_reads_animated_height(self) -> None:
        data = _visualizer_dict()
        data["parameters"]["height"] = _param(150.0)
        effect = AudioVisualizer(data)
        assert effect.height == 150.0

    def test_sets_animated_height(self) -> None:
        data = _visualizer_dict()
        data["parameters"]["height"] = _param(150.0)
        effect = AudioVisualizer(data)
        effect.height = 250.0
        assert data["parameters"]["height"]["defaultValue"] == 250.0


# ------------------------------------------------------------------
# All valid types
# ------------------------------------------------------------------

class TestAudioVisualizerTypes:
    @pytest.mark.parametrize("vis_type", sorted(AudioVisualizer.VALID_TYPES))
    def test_valid_types_accepted(self, vis_type: str) -> None:
        data = _visualizer_dict(vis_type=vis_type)
        effect = AudioVisualizer(data)
        assert effect.type == vis_type

    @pytest.mark.parametrize("vis_type", sorted(AudioVisualizer.VALID_TYPES))
    def test_setter_accepts_all_valid_types(self, vis_type: str) -> None:
        effect = AudioVisualizer(_visualizer_dict())
        effect.type = vis_type
        assert effect.type == vis_type


# ------------------------------------------------------------------
# AMFile.add_audio_visualizer convenience method
# ------------------------------------------------------------------

class TestAMFileAddAudioVisualizer:
    def test_returns_audio_visualizer(self) -> None:
        clip = AMFile(_amfile_data())
        result = clip.add_audio_visualizer()
        assert isinstance(result, AudioVisualizer)

    def test_default_parameters(self) -> None:
        clip = AMFile(_amfile_data())
        viz = clip.add_audio_visualizer()
        assert viz.type == "bars"
        assert viz.color == (1.0, 1.0, 1.0, 1.0)
        assert viz.height == 100.0
        assert viz.sensitivity == 0.7

    def test_custom_parameters(self) -> None:
        clip = AMFile(_amfile_data())
        viz = clip.add_audio_visualizer(
            type="spectrum",
            color=(0.2, 0.4, 0.6, 0.8),
            height=50.0,
            sensitivity=0.9,
        )
        assert viz.type == "spectrum"
        assert viz.color == (0.2, 0.4, 0.6, 0.8)
        assert viz.height == 50.0
        assert viz.sensitivity == 0.9

    def test_appends_to_effects_list(self) -> None:
        clip = AMFile(_amfile_data())
        clip.add_audio_visualizer()
        effects = clip._data["effects"]
        assert len(effects) == 1
        assert effects[0]["effectName"] == "AudioVisualizer"

    def test_rejects_invalid_type(self) -> None:
        clip = AMFile(_amfile_data())
        with pytest.raises(ValueError, match="Invalid visualizer type"):
            clip.add_audio_visualizer(type="invalid")

    def test_effect_category(self) -> None:
        clip = AMFile(_amfile_data())
        viz = clip.add_audio_visualizer()
        assert viz.category == "categoryAudioEffects"

    def test_effect_not_bypassed(self) -> None:
        clip = AMFile(_amfile_data())
        viz = clip.add_audio_visualizer()
        assert viz.bypassed is False
