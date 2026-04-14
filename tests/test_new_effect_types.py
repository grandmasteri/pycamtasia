from __future__ import annotations

from camtasia.timeline.clips import BaseClip
from camtasia.timeline.transitions import TransitionList


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
        assert effect["metadata"]["presetName"] == "Media Matte Luminasity"
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
    def test_add_blend_mode_defaults(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_blend_mode()
        effect = data["effects"][0]
        assert effect["effectName"] == "BlendModeEffect"
        assert effect["parameters"]["mode"] == 16
        assert effect["parameters"]["intensity"] == 1.0
        assert effect["parameters"]["invert"] == 0
        assert effect["parameters"]["channel"] == 0
        assert result is clip

    def test_add_blend_mode_multiply(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_blend_mode(mode=3, intensity=0.8)
        params = data["effects"][0]["parameters"]
        assert params["mode"] == 3
        assert params["intensity"] == 0.8


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


class TestNewTransitionTypes:
    def _make_list(self) -> TransitionList:
        return TransitionList({"transitions": []})

    def test_add_card_flip(self):
        tl = self._make_list()
        t = tl.add_card_flip(1, 2, duration_seconds=0.5)
        assert t.name == "CardFlip"
        assert t.left_media_id == 1
        assert t.right_media_id == 2

    def test_add_glitch(self):
        tl = self._make_list()
        t = tl.add_glitch(1, 2, duration_seconds=0.5)
        assert t.name == "Glitch"

    def test_add_linear_blur(self):
        tl = self._make_list()
        t = tl.add_linear_blur(1, 2, duration_seconds=0.5)
        assert t.name == "LinearBlur"

    def test_add_stretch(self):
        tl = self._make_list()
        t = tl.add_stretch(1, 2, duration_seconds=0.5)
        assert t.name == "Stretch"


class TestDropShadowEnabledParam:
    def test_drop_shadow_enabled_param(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_drop_shadow(enabled=0)
        assert data["effects"][0]["parameters"]["enabled"] == 0

        data2 = _base_clip_dict()
        clip2 = BaseClip(data2)
        clip2.add_drop_shadow()
        assert data2["effects"][0]["parameters"]["enabled"] == 1


class TestEffectMetadataProperty:
    def test_effect_metadata_property(self):
        from camtasia.effects.base import Effect

        # Effect with metadata
        e = Effect({"effectName": "X", "parameters": {}, "metadata": {"presetName": "foo"}})
        assert e.metadata == {"presetName": "foo"}

        # Effect without metadata
        e2 = Effect({"effectName": "Y", "parameters": {}})
        assert e2.metadata == {}


class TestAddLutEffectMetadata:
    def test_add_lut_effect_with_preset_name(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_lut_effect(preset_name="Warm")
        assert data["effects"][0]["metadata"] == {"presetName": "Warm"}

    def test_add_lut_effect_without_preset_name(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_lut_effect()
        assert data["effects"][0]["metadata"] == {}
