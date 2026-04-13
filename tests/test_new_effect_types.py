from __future__ import annotations

from camtasia.timeline.clips import BaseClip


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


class TestAddLutEffect:
    def test_add_lut_effect_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_lut_effect()
        effect = data["effects"][0]
        assert effect["effectName"] == "LutEffect"
        assert effect["bypassed"] is False
        assert effect["category"] == "categoryVisualEffects"
        assert effect["parameters"]["lut_intensity"] == 1.0
        assert effect["parameters"]["channel"] == 0
        assert result is clip

    def test_add_lut_effect_custom_intensity(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_lut_effect(intensity=0.6)
        assert data["effects"][0]["parameters"]["lut_intensity"] == 0.6


class TestAddEmphasize:
    def test_add_emphasize_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_emphasize()
        effect = data["effects"][0]
        assert effect["effectName"] == "Emphasize"
        assert effect["bypassed"] is False
        assert effect["category"] == "categoryAudioEffects"
        assert effect["parameters"]["emphasizeAmount"] == 0.5
        assert result is clip

    def test_add_emphasize_custom_amount(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_emphasize(amount=0.8)
        assert data["effects"][0]["parameters"]["emphasizeAmount"] == 0.8


class TestAddMediaMatte:
    def test_add_media_matte_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_media_matte()
        effect = data["effects"][0]
        assert effect["effectName"] == "MediaMatte"
        assert effect["bypassed"] is False
        assert effect["category"] == "categoryVisualEffects"
        assert effect["parameters"]["intensity"] == 1.0
        assert effect["parameters"]["matteMode"] == 1
        assert effect["parameters"]["trackDepth"] == 10002
        assert result is clip

    def test_add_media_matte_custom_values(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_media_matte(intensity=0.7, matte_mode=2, track_depth=10005)
        params = data["effects"][0]["parameters"]
        assert params["intensity"] == 0.7
        assert params["matteMode"] == 2
        assert params["trackDepth"] == 10005


class TestAddBlendMode:
    def test_add_blend_mode(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_blend_mode(mode='multiply')
        effect = data["effects"][0]
        assert effect["effectName"] == "BlendModeEffect"
        assert effect["bypassed"] is False
        assert effect["category"] == "categoryVisualEffects"
        assert effect["parameters"]["blendMode"] == "multiply"
        assert result is clip


class TestAddFadeEffect:
    def test_add_fade_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_fade_effect(opacity=0.5)
        effect = data["effects"][0]
        assert effect["effectName"] == "fade"
        assert effect["bypassed"] is False
        assert effect["category"] == "categoryVisualEffects"
        assert effect["parameters"]["opacity"] == 0.5
        assert result is clip


class TestPlaceholderMediaLoads:
    def test_placeholder_media_loads(self):
        from camtasia.timeline.clips import clip_from_dict
        data = {
            "id": 99,
            "_type": "PlaceholderMedia",
            "src": 1,
            "start": 0,
            "duration": 705600000,
            "mediaStart": 0,
            "mediaDuration": 705600000,
            "scalar": 1,
        }
        clip = clip_from_dict(data)
        assert isinstance(clip, BaseClip)
        assert clip.clip_type == "PlaceholderMedia"
        assert clip.id == 99