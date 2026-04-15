"""Tests for camtasia.types enums."""
from camtasia.types import (
    ClipType, EffectName, BlendMode, MaskShape, CalloutShape,
    TransitionType, CalloutKind, BehaviorInnerName, BehaviorPreset,
    InterpolationType, _RGBADict,
)


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
            'COLOR_ADJUSTMENT': 'ColorAdjustment',
            'SPOTLIGHT': 'Spotlight',
            'LUT_EFFECT': 'LutEffect',
            'EMPHASIZE': 'Emphasize',
            'MEDIA_MATTE': 'MediaMatte',
            'BLEND_MODE': 'BlendModeEffect',
            'SOURCE_EFFECT': 'SourceEffect',
            'CURSOR_MOTION_BLUR': 'CursorMotionBlur',
            'CURSOR_SHADOW': 'CursorShadow',
            'CURSOR_PHYSICS': 'CursorPhysics',
            'LEFT_CLICK_SCALING': 'LeftClickScaling',
            'VST_NOISE_REMOVAL': 'VSTEffect-DFN3NoiseRemoval',
        }
        for name, value in expected.items():
            assert EffectName[name].value == value

    def test_effect_name_count(self):
        assert len(EffectName) == 17


class TestTransitionTypeValues:
    """Verify TransitionType only contains schema-valid values."""

    def test_transition_type_values(self):
        expected = {
            'CARD_FLIP': 'CardFlip',
            'FADE': 'Fade',
            'FADE_THROUGH_BLACK': 'FadeThroughBlack',
            'GLITCH3': 'Glitch3',
            'LINEAR_BLUR': 'LinearBlur',
            'PAINT_ARCS': 'PaintArcs',
            'SLIDE_LEFT': 'SlideLeft',
            'SLIDE_RIGHT': 'SlideRight',
            'SPHERICAL_SPIN': 'SphericalSpin',
            'STRETCH': 'Stretch',
        }
        for name, value in expected.items():
            assert TransitionType[name].value == value

    def test_transition_type_count(self):
        assert len(TransitionType) == 10

    def test_fabricated_values_removed(self):
        removed = [
            'DISSOLVE', 'FADE_TO_WHITE', 'SLIDE_UP', 'SLIDE_DOWN',
            'WIPE_LEFT', 'WIPE_RIGHT', 'WIPE_UP', 'WIPE_DOWN', 'GLITCH',
        ]
        for name in removed:
            assert name not in TransitionType.__members__

    def test_str_enum_comparison(self):
        assert TransitionType.GLITCH3 == 'Glitch3'
        assert TransitionType.PAINT_ARCS == 'PaintArcs'
        assert TransitionType.SPHERICAL_SPIN == 'SphericalSpin'


class TestBehaviorPresetValues:
    """Verify BehaviorPreset uses lowercase values matching schema."""

    def test_behavior_preset_values(self):
        expected = {
            'REVEAL': 'reveal',
            'SLIDING': 'sliding',
            'FADE': 'fade',
            'FLY_IN': 'flyIn',
            'POP_UP': 'popUp',
            'PULSATING': 'pulsating',
            'SHIFTING': 'shifting',
        }
        for name, value in expected.items():
            assert BehaviorPreset[name].value == value

    def test_behavior_preset_count(self):
        assert len(BehaviorPreset) == 7

    def test_str_enum_comparison(self):
        assert BehaviorPreset.REVEAL == 'reveal'
        assert BehaviorPreset.PULSATING == 'pulsating'


class TestBehaviorInnerNameValues:
    """Verify BehaviorInnerName enum values match inner name strings from TechSmith samples."""

    def test_behavior_inner_name_values(self):
        expected = {
            'FADE_IN': 'fadeIn',
            'REVEAL': 'reveal',
            'SLIDING': 'sliding',
            'FLY_IN': 'flyIn',
            'GROW': 'grow',
            'HINGE': 'hinge',
            'FADE_OUT': 'fadeOut',
            'FLY_OUT': 'flyOut',
            'SHRINK': 'shrink',
            'SHIFTING': 'shifting',
            'NONE': 'none',
            'TREMBLE': 'tremble',
            'PULSATE': 'pulsate',
        }
        for name, value in expected.items():
            assert BehaviorInnerName[name].value == value

    def test_behavior_inner_name_count(self):
        assert len(BehaviorInnerName) == 13

    def test_str_enum_comparison(self):
        assert BehaviorInnerName.FADE_IN == 'fadeIn'
        assert BehaviorInnerName.NONE == 'none'
        assert BehaviorInnerName.PULSATE == 'pulsate'


class TestInterpolationTypeValues:
    """Verify InterpolationType has correct members."""

    def test_interpolation_type_values(self):
        expected = {
            'LINEAR': 'linr',
            'EASE_IN_OUT_ELASTIC': 'eioe',
            'SPRING': 'sprg',
            'BOUNCE': 'bnce',
        }
        for name, value in expected.items():
            assert InterpolationType[name].value == value

    def test_hold_removed(self):
        assert 'HOLD' not in InterpolationType.__members__

    def test_interpolation_type_count(self):
        assert len(InterpolationType) == 4


class TestRGBADictRenamed:
    """Verify RGBA TypedDict was renamed to _RGBADict."""

    def test_rgba_dict_is_typed_dict(self):
        assert hasattr(_RGBADict, '__annotations__')
        assert 'red' in _RGBADict.__annotations__
        assert 'green' in _RGBADict.__annotations__
        assert 'blue' in _RGBADict.__annotations__

    def test_no_public_rgba_in_types(self):
        import camtasia.types as t
        assert not hasattr(t, 'RGBA') or t.RGBA is t._RGBADict


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
            'EMPTY': '',
            'TEXT': 'text',
            'TEXT_RECTANGLE': 'text-rectangle',
            'TEXT_ARROW2': 'text-arrow2',
            'ARROW': 'arrow',
            'SHAPE_RECTANGLE': 'shape-rectangle',
            'SHAPE_ELLIPSE': 'shape-ellipse',
            'SHAPE_TRIANGLE': 'shape-triangle',
        }
        for name, value in expected.items():
            assert CalloutShape[name].value == value
        # str enum comparison
        assert CalloutShape.SHAPE_RECTANGLE == 'shape-rectangle'


class TestCalloutShapeSetter:
    def test_set_shape_with_enum(self):
        from camtasia.timeline.clips.callout import Callout
        from camtasia.types import CalloutShape
        data = {'_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100, 'def': {'shape': 'rectangle'}}
        c = Callout(data)
        c.shape = CalloutShape.SHAPE_ELLIPSE
        assert data['def']['shape'] == 'shape-ellipse'

    def test_set_shape_with_string(self):
        from camtasia.timeline.clips.callout import Callout
        data = {'_type': 'Callout', 'id': 1, 'start': 0, 'duration': 100, 'def': {'shape': 'rectangle'}}
        c = Callout(data)
        c.shape = 'triangle'
        assert data['def']['shape'] == 'triangle'


class TestCalloutKindValues:
    """Verify CalloutKind enum values."""

    def test_callout_kind_values(self):
        assert CalloutKind.REMIX.value == 'remix'
        assert CalloutKind.WIN_BLUR.value == 'TypeWinBlur'
        # str enum comparison
        assert CalloutKind.REMIX == 'remix'
        assert CalloutKind.WIN_BLUR == 'TypeWinBlur'
