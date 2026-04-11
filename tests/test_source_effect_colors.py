from __future__ import annotations
"""Tests for SourceEffect flat-scalar color handling and set_shader_colors."""
from camtasia.effects.source import SourceEffect
from camtasia.effects.visual import _color_rgba, _set_color_rgba


def _flat_source_effect():
    """SourceEffect with flat scalar parameters (real Camtasia format)."""
    return {
        "effectName": "SourceEffect",
        "parameters": {
            "Color0-red": 0.137, "Color0-green": 0.184,
            "Color0-blue": 0.243, "Color0-alpha": 1.0,
            "Color1-red": 0.0, "Color1-green": 0.5,
            "Color1-blue": 1.0, "Color1-alpha": 1.0,
            "Color2-red": 0.2, "Color2-green": 0.3,
            "Color2-blue": 0.4, "Color2-alpha": 0.8,
            "Color3-red": 0.9, "Color3-green": 0.8,
            "Color3-blue": 0.7, "Color3-alpha": 0.6,
            "MidPointX": 0.5, "MidPointY": 0.5,
            "Speed": 5.0,
            "sourceFileType": "tscshadervid",
        },
    }


def test_get_color_flat_scalars():
    effect = SourceEffect(_flat_source_effect())
    assert effect.color0 == (0.137, 0.184, 0.243, 1.0)
    assert effect.color3 == (0.9, 0.8, 0.7, 0.6)


def test_set_color_flat_scalars():
    effect = SourceEffect(_flat_source_effect())
    effect.color0 = (0.1, 0.2, 0.3, 0.4)
    assert effect.color0 == (0.1, 0.2, 0.3, 0.4)
    # Verify stays flat
    assert effect.parameters["Color0-red"] == 0.1


def test_set_shader_colors():
    effect = SourceEffect(_flat_source_effect())
    effect.set_shader_colors((255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 128, 128))
    assert effect.color0 == (1.0, 0.0, 0.0, 1.0)
    assert effect.color1 == (0.0, 1.0, 0.0, 1.0)
    assert effect.color2 == (0.0, 0.0, 1.0, 1.0)
    r, g, b, a = effect.color3
    assert abs(r - 128 / 255) < 1e-9
    assert a == 1.0


def test_set_color_rgba_flat_scalars():
    params = {"color-red": 0.1, "color-green": 0.2,
              "color-blue": 0.3, "color-alpha": 1.0}
    _set_color_rgba(params, "color", (0.5, 0.6, 0.7, 0.8))
    assert params["color-red"] == 0.5
    assert _color_rgba(params, "color") == (0.5, 0.6, 0.7, 0.8)


def test_source_effect_on_vmfile():
    from camtasia.timeline.clips.video import VMFile
    data = {"_type": "VMFile", "id": 1, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100,
            "sourceEffect": {"effectName": "SourceEffect", "parameters": {}}}
    clip = VMFile(data)
    assert clip.source_effect is not None
    assert clip.source_effect["effectName"] == "SourceEffect"


def test_source_effect_none_when_absent():
    from camtasia.timeline.clips.video import VMFile
    data = {"_type": "VMFile", "id": 1, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100}
    assert VMFile(data).source_effect is None
