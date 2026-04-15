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


# ------------------------------------------------------------------
# ColorAdjustment
# ------------------------------------------------------------------

class TestAddColorAdjustment:
    def test_add_color_adjustment_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_color_adjustment()
        effect = data["effects"][0]
        assert effect["effectName"] == "ColorAdjustment"
        assert effect["bypassed"] is False
        assert effect["category"] == "categoryVisualEffects"
        assert effect["parameters"]["brightness"] == 0.0
        assert effect["parameters"]["contrast"] == 0.0
        assert effect["parameters"]["saturation"] == 1.0
        assert effect["parameters"]["channel"] == 0

    def test_add_color_adjustment_custom_values(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_color_adjustment(brightness=0.5, contrast=-0.3, saturation=2.0)
        params = data["effects"][0]["parameters"]
        assert params["brightness"] == 0.5
        assert params["contrast"] == -0.3
        assert params["saturation"] == 2.0

    def test_add_color_adjustment_chaining(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_color_adjustment()
        assert result is clip


# ------------------------------------------------------------------
# Border
# ------------------------------------------------------------------

class TestAddBorder:
    def test_add_border_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_border()
        effect = data["effects"][0]
        assert effect["effectName"] == "Border"
        assert effect["bypassed"] is False
        assert effect["parameters"]["width"] == 4.0
        assert effect["parameters"]["color-red"] == 1.0
        assert effect["parameters"]["color-green"] == 1.0
        assert effect["parameters"]["color-blue"] == 1.0
        assert effect["parameters"]["color-alpha"] == 1.0
        assert effect["parameters"]["corner-radius"] == 0.0

    def test_add_border_custom_color(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_border(width=8.0, color=(0.2, 0.4, 0.6, 0.8), corner_radius=5.0)
        params = data["effects"][0]["parameters"]
        assert params["width"] == 8.0
        assert params["color-red"] == 0.2
        assert params["color-green"] == 0.4
        assert params["color-blue"] == 0.6
        assert params["color-alpha"] == 0.8
        assert params["corner-radius"] == 5.0

    def test_add_border_chaining(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_border()
        assert result is clip


# ------------------------------------------------------------------
# Colorize
# ------------------------------------------------------------------

class TestAddColorize:
    def test_add_colorize_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_colorize()
        effect = data["effects"][0]
        assert effect["effectName"] == "Colorize"
        assert effect["bypassed"] is False
        assert effect["parameters"]["color-red"] == 0.5
        assert effect["parameters"]["color-green"] == 0.5
        assert effect["parameters"]["color-blue"] == 0.5
        assert effect["parameters"]["intensity"] == 0.5

    def test_add_colorize_custom_values(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_colorize(color=(0.1, 0.9, 0.3), intensity=0.8)
        params = data["effects"][0]["parameters"]
        assert params["color-red"] == 0.1
        assert params["color-green"] == 0.9
        assert params["color-blue"] == 0.3
        assert params["intensity"] == 0.8


# ------------------------------------------------------------------
# Spotlight
# ------------------------------------------------------------------

class TestAddSpotlight:
    def test_add_spotlight_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_spotlight()
        effect = data["effects"][0]
        assert effect["effectName"] == "Spotlight"
        assert effect["bypassed"] is False
        assert effect["parameters"]["brightness"] == 0.5
        assert effect["parameters"]["concentration"] == 0.5
        assert effect["parameters"]["opacity"] == 0.35

    def test_add_spotlight_custom_values(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_spotlight(brightness=0.8, concentration=0.3, opacity=0.5)
        params = data["effects"][0]["parameters"]
        assert params["brightness"] == 0.8
        assert params["concentration"] == 0.3
        assert params["opacity"] == 0.5


class TestAddMotionBlur:
    def test_add_motion_blur_creates_effect(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.add_motion_blur()
        effect = data["effects"][0]
        assert effect["effectName"] == "MotionBlur"
        assert effect["bypassed"] is False
        assert effect["parameters"]["intensity"] == 1.0
        assert result is clip

    def test_add_motion_blur_custom_intensity(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.add_motion_blur(intensity=0.6)
        assert data["effects"][0]["parameters"]["intensity"] == 0.6


class TestEffectRepr:
    def test_effect_repr(self):
        from camtasia.effects.base import Effect
        data = {"effectName": "Glow", "bypassed": False, "category": "", "parameters": {}}
        effect = Effect(data)
        assert repr(effect) == "Effect(name='Glow')"


class TestDropShadowEnabled:
    def test_enabled_getter(self):
        from camtasia.effects.visual import DropShadow
        data = {'effectName': 'DropShadow', 'parameters': {'enabled': 1}}
        ds = DropShadow(data)
        assert ds.enabled == 1

    def test_enabled_setter(self):
        from camtasia.effects.visual import DropShadow
        data = {'effectName': 'DropShadow', 'parameters': {'enabled': 1}}
        ds = DropShadow(data)
        ds.enabled = 0
        assert ds.enabled == 0
