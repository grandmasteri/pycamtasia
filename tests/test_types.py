"""Tests for camtasia.types enums."""
from camtasia.types import ClipType, EffectName, BlendMode


class TestClipTypeValues:
    """Verify all ClipType enum values match the actual _type strings."""

    def test_clip_type_values(self):
        expected = {
            'AUDIO': 'AMFile',
            'VIDEO': 'VMFile',
            'IMAGE': 'IMFile',
            'SCREEN_VIDEO': 'ScreenVMFile',
            'SCREEN_IMAGE': 'ScreenIMFile',
            'CALLOUT': 'Callout',
            'GROUP': 'Group',
            'UNIFIED_MEDIA': 'UnifiedMedia',
            'STITCHED_MEDIA': 'StitchedMedia',
            'PLACEHOLDER': 'PlaceholderMedia',
        }
        for name, value in expected.items():
            assert ClipType[name].value == value


class TestEffectNameValues:
    """Verify all EffectName enum values match effectName strings."""

    def test_effect_name_values(self):
        expected = {
            'DROP_SHADOW': 'DropShadow',
            'ROUND_CORNERS': 'RoundCorners',
            'GLOW': 'Glow',
            'MOTION_BLUR': 'MotionBlur',
            'MASK': 'Mask',
            'BLUR_REGION': 'BlurRegion',
            'COLOR_ADJUSTMENT': 'ColorAdjustment',
            'BORDER': 'Border',
            'COLORIZE': 'Colorize',
            'SPOTLIGHT': 'Spotlight',
            'LUT_EFFECT': 'LutEffect',
            'EMPHASIZE': 'Emphasize',
            'MEDIA_MATTE': 'MediaMatte',
            'BLEND_MODE': 'BlendModeEffect',
        }
        for name, value in expected.items():
            assert EffectName[name].value == value


class TestBlendModeValues:
    """Verify BlendMode int values."""

    def test_blend_mode_values(self):
        assert BlendMode.NORMAL == 16
        assert BlendMode.MULTIPLY == 3


class TestStrEnumComparison:
    """Verify str enum behavior — ClipType members compare equal to plain strings."""

    def test_str_enum_comparison(self):
        assert ClipType.AUDIO == 'AMFile'
        assert ClipType.VIDEO == 'VMFile'
        assert ClipType.CALLOUT == 'Callout'
