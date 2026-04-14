"""Tests for camtasia.types enums."""
from camtasia.types import ClipType, EffectName, BlendMode, MaskShape, CalloutShape, TransitionType, CalloutKind


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


class TestMaskShapeEnumValues:
    """Verify MaskShape int values."""

    def test_mask_shape_enum_values(self):
        assert MaskShape.RECTANGLE == 0
        assert MaskShape.ELLIPSE == 1
        assert isinstance(MaskShape.RECTANGLE, int)


class TestCalloutShapeEnumValues:
    """Verify CalloutShape string values."""

    def test_callout_shape_enum_values(self):
        expected = {
            'RECTANGLE': 'rectangle',
            'ROUNDED_RECTANGLE': 'roundedRectangle',
            'ELLIPSE': 'ellipse',
            'TRIANGLE': 'triangle',
            'ARROW': 'arrow',
            'DIAMOND': 'diamond',
            'STAR': 'star',
        }
        for name, value in expected.items():
            assert CalloutShape[name].value == value
        # str enum comparison
        assert CalloutShape.RECTANGLE == 'rectangle'


class TestCalloutShapeSetter:
    def test_set_shape_with_enum(self):
        from camtasia.timeline.clips.callout import Callout
        from camtasia.types import CalloutShape
        data = {'_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100, 'def': {'shape': 'rectangle'}}
        c = Callout(data)
        c.shape = CalloutShape.ELLIPSE
        assert data['def']['shape'] == 'ellipse'

    def test_set_shape_with_string(self):
        from camtasia.timeline.clips.callout import Callout
        data = {'_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100, 'def': {'shape': 'rectangle'}}
        c = Callout(data)
        c.shape = 'triangle'
        assert data['def']['shape'] == 'triangle'


class TestNewTransitionTypes:
    """Verify the three new transition type enum values."""

    def test_new_transition_types(self):
        assert TransitionType.GLITCH3.value == 'Glitch3'
        assert TransitionType.PAINT_ARCS.value == 'PaintArcs'
        assert TransitionType.SPHERICAL_SPIN.value == 'SphericalSpin'
        # str enum comparison
        assert TransitionType.GLITCH3 == 'Glitch3'
        assert TransitionType.PAINT_ARCS == 'PaintArcs'
        assert TransitionType.SPHERICAL_SPIN == 'SphericalSpin'


class TestCalloutKindValues:
    """Verify CalloutKind enum values."""

    def test_callout_kind_values(self):
        assert CalloutKind.REMIX.value == 'remix'
        assert CalloutKind.WIN_BLUR.value == 'TypeWinBlur'
        # str enum comparison
        assert CalloutKind.REMIX == 'remix'
        assert CalloutKind.WIN_BLUR == 'TypeWinBlur'
