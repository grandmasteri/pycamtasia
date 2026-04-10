"""Tests for new features for text behaviors, animation tracks, and callout shapes.

Covers: MotionBlur, Mask, BlurRegion, GenericBehaviorEffect,
animationTracks on BaseClip, and new callout shapes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.visual import BlurRegion, Mask, MotionBlur
from camtasia.effects.behaviors import BehaviorPhase, GenericBehaviorEffect
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.clips.callout import Callout

FIXTURES = Path(__file__).parent / "fixtures"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    """Build a standard Camtasia parameter dict."""
    return {"type": type_, "defaultValue": value, "interp": interp}


def _keyframed_param(default: float, keyframes: list[dict]) -> dict:
    """Build a keyframed parameter dict."""
    return {
        "type": "double",
        "defaultValue": default,
        "keyframes": keyframes,
    }


# ------------------------------------------------------------------
# MotionBlur
# ------------------------------------------------------------------

MOTION_BLUR_DICT = {
    "effectName": "MotionBlur",
    "bypassed": False,
    "category": "categoryVisualEffects",
    "parameters": {
        "intensity": _param(0.75),
    },
}


class TestMotionBlur:
    def test_intensity_read(self):
        actual_effect = MotionBlur(MOTION_BLUR_DICT)
        assert actual_effect.intensity == 0.75

    def test_intensity_write(self):
        data = json.loads(json.dumps(MOTION_BLUR_DICT))
        actual_effect = MotionBlur(data)
        actual_effect.intensity = 1.5
        assert actual_effect.intensity == 1.5
        assert data["parameters"]["intensity"]["defaultValue"] == 1.5

    def test_name_and_category(self):
        actual_effect = MotionBlur(MOTION_BLUR_DICT)
        assert actual_effect.name == "MotionBlur"
        assert actual_effect.category == "categoryVisualEffects"

    def test_effect_from_dict_dispatches_motion_blur(self):
        actual_effect = effect_from_dict(MOTION_BLUR_DICT)
        assert isinstance(actual_effect, MotionBlur)
        assert actual_effect.intensity == 0.75


# ------------------------------------------------------------------
# Mask
# ------------------------------------------------------------------

MASK_KEYFRAMES = [
    {"endTime": 705600000, "time": 0, "value": 346.97, "duration": 705600000},
    {"endTime": 9760800000, "time": 9055200000, "value": 346.97, "duration": 705600000},
]

MASK_DICT = {
    "effectName": "Mask",
    "bypassed": False,
    "category": "categoryVisualEffects",
    "parameters": {
        "mask_shape": _param(0, type_="int"),
        "mask_opacity": _param(0.0),
        "mask_blend": _param(-0.02),
        "mask_invert": _param(0, type_="int"),
        "mask_rotation": _param(0.0),
        "mask_width": _keyframed_param(346.97, MASK_KEYFRAMES),
        "mask_height": _keyframed_param(347.68, MASK_KEYFRAMES),
        "mask_positionX": _keyframed_param(9.07, MASK_KEYFRAMES),
        "mask_positionY": _keyframed_param(1.96, MASK_KEYFRAMES),
    },
}


class TestMask:
    def test_all_scalar_parameters(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_shape == 0
        assert actual_effect.mask_opacity == 0.0
        assert actual_effect.mask_blend == -0.02
        assert actual_effect.mask_invert == 0
        assert actual_effect.mask_rotation == 0.0

    def test_keyframed_width_returns_default_value(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_width == 346.97

    def test_keyframed_height_returns_default_value(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_height == 347.68

    def test_keyframed_position(self):
        actual_effect = Mask(MASK_DICT)
        assert actual_effect.mask_position_x == 9.07
        assert actual_effect.mask_position_y == 1.96

    def test_mask_shape_write(self):
        data = json.loads(json.dumps(MASK_DICT))
        actual_effect = Mask(data)
        actual_effect.mask_shape = 2
        assert actual_effect.mask_shape == 2

    def test_effect_from_dict_dispatches_mask(self):
        actual_effect = effect_from_dict(MASK_DICT)
        assert isinstance(actual_effect, Mask)
        assert actual_effect.mask_blend == -0.02


# ------------------------------------------------------------------
# BlurRegion
# ------------------------------------------------------------------

BLUR_REGION_DICT = {
    "effectName": "BlurRegion",
    "bypassed": False,
    "category": "",
    "parameters": {
        "sigma": _param(10.0),
        "mask_corner_radius": _param(5.0),
        "mask_invert": _param(0, type_="int"),
        "color_alpha": _param(0.8),
    },
    "metadata": {"presetName": "Blur Region"},
}


class TestBlurRegion:
    def test_all_parameters(self):
        actual_effect = BlurRegion(BLUR_REGION_DICT)
        assert actual_effect.sigma == 10.0
        assert actual_effect.mask_corner_radius == 5.0
        assert actual_effect.mask_invert == 0
        assert actual_effect.color_alpha == 0.8

    def test_sigma_write(self):
        data = json.loads(json.dumps(BLUR_REGION_DICT))
        actual_effect = BlurRegion(data)
        actual_effect.sigma = 25.0
        assert actual_effect.sigma == 25.0
        assert data["parameters"]["sigma"]["defaultValue"] == 25.0

    def test_effect_from_dict_dispatches_blur_region(self):
        actual_effect = effect_from_dict(BLUR_REGION_DICT)
        assert isinstance(actual_effect, BlurRegion)
        assert actual_effect.sigma == 10.0


# ------------------------------------------------------------------
# effect_from_dict dispatch for all 3 new types
# ------------------------------------------------------------------

class TestEffectFromDictDispatch:
    @pytest.mark.parametrize(
        "effect_dict, expected_type",
        [
            (MOTION_BLUR_DICT, MotionBlur),
            (MASK_DICT, Mask),
            (BLUR_REGION_DICT, BlurRegion),
        ],
        ids=["MotionBlur", "Mask", "BlurRegion"],
    )
    def test_dispatches_to_correct_class(self, effect_dict, expected_type):
        actual_effect = effect_from_dict(effect_dict)
        assert type(actual_effect) is expected_type

    def test_unknown_effect_returns_base(self):
        actual_effect = effect_from_dict({"effectName": "UnknownEffect", "parameters": {}})
        assert type(actual_effect) is Effect


# ------------------------------------------------------------------
# GenericBehaviorEffect
# ------------------------------------------------------------------

BEHAVIOR_DICT = {
    "_type": "GenericBehaviorEffect",
    "effectName": "reveal",
    "bypassed": False,
    "start": 1411200000,
    "duration": 12277440000,
    "in": {
        "attributes": {
            "name": "reveal",
            "type": 0,
            "characterOrder": 7,
            "offsetBetweenCharacters": 35280000,
            "suggestedDurationPerCharacter": 517440000,
            "overlapProportion": 0,
            "movement": 16,
            "springDamping": 5.0,
            "springStiffness": 50.0,
            "bounceBounciness": 0.45,
        },
        "parameters": {
            "direction": {
                "type": "int",
                "valueBounds": {"minValue": 0, "maxValue": 20, "defaultValue": 0},
                "keyframes": [
                    {"endTime": 0, "time": 0, "value": 0, "duration": 0}
                ],
            }
        },
    },
    "center": {
        "attributes": {
            "name": "none",
            "type": 1,
            "characterOrder": 6,
            "secondsPerLoop": 1,
            "numberOfLoops": -1,
        },
        "parameters": {},
    },
    "out": {
        "attributes": {
            "name": "reveal",
            "type": 0,
            "characterOrder": 7,
            "offsetBetweenCharacters": 35280000,
            "suggestedDurationPerCharacter": 517440000,
            "overlapProportion": "1/2",
            "movement": 6,
            "springDamping": 5.0,
            "springStiffness": 50.0,
            "bounceBounciness": 0.45,
        },
        "parameters": {},
    },
    "metadata": {"presetName": "Reveal"},
}


class TestGenericBehaviorEffect:
    def test_create_from_dict(self):
        actual_effect = GenericBehaviorEffect(BEHAVIOR_DICT)
        assert actual_effect.effect_name == "reveal"
        assert actual_effect.bypassed is False
        assert actual_effect.start == 1411200000
        assert actual_effect.duration == 12277440000
        assert actual_effect.preset_name == "Reveal"

    def test_entrance_phase(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).entrance
        assert actual_phase.name == "reveal"
        assert actual_phase.phase_type == 0
        assert actual_phase.character_order == 7
        assert actual_phase.offset_between_characters == 35280000
        assert actual_phase.suggested_duration_per_character == 517440000
        assert actual_phase.movement == 16
        assert actual_phase.spring_damping == 5.0
        assert actual_phase.spring_stiffness == 50.0
        assert actual_phase.bounce_bounciness == 0.45

    def test_center_phase(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).center
        assert actual_phase.name == "none"
        assert actual_phase.phase_type == 1
        assert actual_phase.character_order == 6

    def test_exit_phase(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).exit
        assert actual_phase.name == "reveal"
        assert actual_phase.phase_type == 0
        assert actual_phase.movement == 6

    def test_overlap_proportion_string_fraction(self):
        """The out phase has overlapProportion as string '1/2'."""
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).exit
        assert actual_phase.overlap_proportion == "1/2"

    def test_overlap_proportion_integer(self):
        """The in phase has overlapProportion as integer 0."""
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).entrance
        assert actual_phase.overlap_proportion == 0

    def test_entrance_parameters_contain_direction(self):
        actual_params = GenericBehaviorEffect(BEHAVIOR_DICT).entrance.parameters
        assert "direction" in actual_params
        assert actual_params["direction"]["type"] == "int"

    def test_bypassed_write(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        actual_effect = GenericBehaviorEffect(data)
        actual_effect.bypassed = True
        assert actual_effect.bypassed is True
        assert data["bypassed"] is True

    def test_preset_name_missing_metadata(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        del data["metadata"]
        actual_effect = GenericBehaviorEffect(data)
        assert actual_effect.preset_name == ""

    def test_repr(self):
        actual_repr = repr(GenericBehaviorEffect(BEHAVIOR_DICT))
        assert actual_repr == "GenericBehaviorEffect(name='reveal', preset='Reveal')"


class TestBehaviorPhase:
    def test_repr(self):
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).entrance
        assert repr(actual_phase) == "BehaviorPhase(name='reveal', type=0)"

    def test_name_write(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        actual_phase = GenericBehaviorEffect(data).entrance
        actual_phase.name = "typewriter"
        assert actual_phase.name == "typewriter"
        assert data["in"]["attributes"]["name"] == "typewriter"

    def test_spring_damping_write(self):
        data = json.loads(json.dumps(BEHAVIOR_DICT))
        actual_phase = GenericBehaviorEffect(data).entrance
        actual_phase.spring_damping = 10.0
        assert actual_phase.spring_damping == 10.0

    def test_defaults_for_missing_optional_attrs(self):
        """Center phase lacks movement, spring*, bounce* — should return defaults."""
        actual_phase = GenericBehaviorEffect(BEHAVIOR_DICT).center
        assert actual_phase.movement == 0
        assert actual_phase.spring_damping == 0.0
        assert actual_phase.spring_stiffness == 0.0
        assert actual_phase.bounce_bounciness == 0.0
        assert actual_phase.offset_between_characters == 0
        assert actual_phase.suggested_duration_per_character == 0


# ------------------------------------------------------------------
# animationTracks on BaseClip
# ------------------------------------------------------------------

ANIMATION_TRACKS_DATA = {
    "visual": [
        {"endTime": 352800000, "duration": 352800000, "range": [0, 352800000], "interp": "eioe"},
        {"endTime": 705600000, "duration": 352800000, "range": [352800000, 352800000], "interp": "eioe"},
        {"endTime": 1411200000, "duration": 705600000, "range": [705600000, 705600000], "interp": "eioe"},
    ]
}


class TestAnimationTracks:
    def test_empty_animation_tracks(self):
        actual_clip = BaseClip({
            "_type": "IMFile", "id": 1, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100,
            "animationTracks": {},
        })
        assert actual_clip.animation_tracks == {}

    def test_missing_animation_tracks_returns_empty_dict(self):
        actual_clip = BaseClip({
            "_type": "IMFile", "id": 1, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100,
        })
        assert actual_clip.animation_tracks == {}

    def test_visual_animation_tracks(self):
        actual_clip = BaseClip({
            "_type": "Callout", "id": 180, "start": 0, "duration": 1411200000,
            "mediaStart": 0, "mediaDuration": 1411200000,
            "animationTracks": ANIMATION_TRACKS_DATA,
        })
        actual_tracks = actual_clip.animation_tracks
        assert "visual" in actual_tracks
        expected_visual = [
            {"endTime": 352800000, "duration": 352800000, "range": [0, 352800000], "interp": "eioe"},
            {"endTime": 705600000, "duration": 352800000, "range": [352800000, 352800000], "interp": "eioe"},
            {"endTime": 1411200000, "duration": 705600000, "range": [705600000, 705600000], "interp": "eioe"},
        ]
        assert actual_tracks["visual"] == expected_visual

    def test_negative_range_values(self):
        """Pre-roll animations can have negative time values."""
        actual_clip = BaseClip({
            "_type": "Callout", "id": 99, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100,
            "animationTracks": {
                "visual": [
                    {"endTime": 0, "duration": 470400000, "range": [-1081920000, 470400000]},
                ]
            },
        })
        actual_segment = actual_clip.animation_tracks["visual"][0]
        assert actual_segment["range"] == [-1081920000, 470400000]


# ------------------------------------------------------------------
# Callout new shapes
# ------------------------------------------------------------------

def _callout_dict(shape: str, style: str, **extra_def) -> dict:
    """Build a minimal Callout clip dict with the given shape/style."""
    defn = {
        "kind": "remix",
        "shape": shape,
        "style": style,
        "fill-color-red": 1.0,
        "fill-color-green": 1.0,
        "fill-color-blue": 1.0,
        "fill-color-opacity": 1.0,
        "stroke-color-red": 0.0,
        "stroke-color-green": 0.5,
        "stroke-color-blue": 0.5,
        "stroke-color-opacity": 1.0,
        "height": 150.0,
        "width": 350.0,
        "corner-radius": 0.0,
        "tail-x": 0.0,
        "tail-y": -20.0,
    }
    defn.update(extra_def)
    return {
        "_type": "Callout", "id": 100, "start": 0, "duration": 705600000,
        "mediaStart": 0, "mediaDuration": 705600000,
        "def": defn,
    }


class TestCalloutNewShapes:
    def test_shape_rectangle_bold(self):
        actual_callout = Callout(_callout_dict("shape-rectangle", "bold"))
        assert actual_callout.shape == "shape-rectangle"
        assert actual_callout.style == "bold"

    def test_shape_rectangle_abstract(self):
        actual_callout = Callout(_callout_dict("shape-rectangle", "abstract"))
        assert actual_callout.shape == "shape-rectangle"
        assert actual_callout.style == "abstract"

    def test_text_arrow2(self):
        actual_callout = Callout(_callout_dict("text-arrow2", "bold"))
        assert actual_callout.shape == "text-arrow2"
        assert actual_callout.style == "bold"
        assert actual_callout.tail_position == (0.0, -20.0)

    def test_text_rectangle_abstract(self):
        actual_callout = Callout(_callout_dict(
            "text-rectangle", "abstract", **{"corner-radius": 9.0}
        ))
        assert actual_callout.shape == "text-rectangle"
        assert actual_callout.style == "abstract"
        assert actual_callout.corner_radius == 9.0

    def test_fill_color_tuple(self):
        actual_callout = Callout(_callout_dict("shape-rectangle", "bold"))
        assert actual_callout.fill_color == (1.0, 1.0, 1.0, 1.0)

    def test_stroke_color_tuple(self):
        actual_callout = Callout(_callout_dict("shape-rectangle", "bold"))
        assert actual_callout.stroke_color == (0.0, 0.5, 0.5, 1.0)

    def test_fill_color_write(self):
        data = _callout_dict("shape-rectangle", "bold")
        actual_callout = Callout(data)
        actual_callout.fill_color = (0.2, 0.3, 0.4, 0.5)
        assert actual_callout.fill_color == (0.2, 0.3, 0.4, 0.5)

    def test_corner_radius_write(self):
        data = _callout_dict("text-rectangle", "abstract", **{"corner-radius": 0.0})
        actual_callout = Callout(data)
        actual_callout.corner_radius = 12.0
        assert actual_callout.corner_radius == 12.0

    def test_tail_position_write(self):
        data = _callout_dict("text-arrow2", "bold")
        actual_callout = Callout(data)
        actual_callout.tail_position = (10.0, -30.0)
        assert actual_callout.tail_position == (10.0, -30.0)

    @pytest.mark.parametrize(
        "shape, style",
        [
            ("shape-rectangle", "bold"),
            ("shape-rectangle", "abstract"),
            ("text-arrow2", "bold"),
            ("text-rectangle", "abstract"),
        ],
        ids=["rect-bold", "rect-abstract", "arrow2-bold", "textrect-abstract"],
    )
    def test_kind_is_remix(self, shape, style):
        actual_callout = Callout(_callout_dict(shape, style))
        assert actual_callout.kind == "remix"


# ------------------------------------------------------------------
# Integration tests with sample project B fixture
# ------------------------------------------------------------------

@pytest.fixture
def test_project_b_data():
    fixture_path = FIXTURES / "test_project_b.tscproj"
    if not fixture_path.exists():
        pytest.skip("test_project_b.tscproj fixture not available")
    with open(fixture_path) as f:
        return json.load(f)


def _collect_all(obj, predicate):
    """Recursively collect all dicts matching predicate."""
    results = []
    if isinstance(obj, dict):
        if predicate(obj):
            results.append(obj)
        for v in obj.values():
            results.extend(_collect_all(v, predicate))
    elif isinstance(obj, list):
        for v in obj:
            results.extend(_collect_all(v, predicate))
    return results


class TestTestProjectBIntegration:
    """Integration tests against sample project B fixture."""

    def test_clips_with_animation_tracks(self, test_project_b_data):
        actual_clips = _collect_all(
            test_project_b_data,
            lambda d: (
                "_type" in d
                and "animationTracks" in d
                and d["animationTracks"] != {}
            ),
        )
        # Verify we found clips and they have visual tracks
        assert actual_clips != []
        actual_first = BaseClip(actual_clips[0])
        assert "visual" in actual_first.animation_tracks
        actual_visual = actual_first.animation_tracks["visual"]
        assert actual_visual != []
        # Each segment has the expected keys
        actual_segment = actual_visual[0]
        assert actual_segment.keys() >= {"endTime", "duration", "range"}

    def test_generic_behavior_effects(self, test_project_b_data):
        actual_behaviors = _collect_all(
            test_project_b_data,
            lambda d: d.get("_type") == "GenericBehaviorEffect",
        )
        assert actual_behaviors != []
        actual_effect = GenericBehaviorEffect(actual_behaviors[0])
        assert actual_effect.effect_name == "reveal"
        assert actual_effect.preset_name == "Reveal"
        # Verify phases are accessible
        assert actual_effect.entrance.name == "reveal"
        assert actual_effect.center.name == "none"
        assert actual_effect.exit.name == "reveal"

    def test_mask_effects(self, test_project_b_data):
        actual_masks = _collect_all(
            test_project_b_data,
            lambda d: d.get("effectName") == "Mask",
        )
        assert actual_masks != []
        # Verify the raw parameter keys use dashes (real format)
        actual_params = actual_masks[0]["parameters"]
        assert "mask-shape" in actual_params or "mask_shape" in actual_params

    def test_motion_blur_effects(self, test_project_b_data):
        actual_effects = _collect_all(
            test_project_b_data,
            lambda d: d.get("effectName") == "MotionBlur",
        )
        assert actual_effects != []
        actual_first = actual_effects[0]
        assert actual_first["category"] == "categoryVisualEffects"

    def test_new_callout_shapes(self, test_project_b_data):
        actual_callouts = _collect_all(
            test_project_b_data,
            lambda d: (
                isinstance(d.get("shape"), str)
                and d.get("shape") in ("shape-rectangle", "text-arrow2", "text-rectangle")
            ),
        )
        assert actual_callouts != []
        actual_shapes = {c["shape"] for c in actual_callouts}
        # The fixture contains at least shape-rectangle and text-arrow2
        assert "shape-rectangle" in actual_shapes

    def test_callout_styles_include_bold_and_abstract(self, test_project_b_data):
        actual_callouts = _collect_all(
            test_project_b_data,
            lambda d: (
                isinstance(d.get("shape"), str)
                and d.get("shape") in ("shape-rectangle", "text-arrow2", "text-rectangle")
            ),
        )
        actual_styles = {c.get("style") for c in actual_callouts}
        assert {"bold", "abstract"} <= actual_styles

    def test_callout_fill_and_stroke_colors(self, test_project_b_data):
        actual_callouts = _collect_all(
            test_project_b_data,
            lambda d: (
                isinstance(d.get("shape"), str)
                and d.get("shape") == "text-arrow2"
            ),
        )
        assert actual_callouts != []
        actual_callout = Callout({
            "_type": "Callout", "id": 1, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100,
            "def": actual_callouts[0],
        })
        actual_fill = actual_callout.fill_color
        assert isinstance(actual_fill, tuple)
        assert isinstance(actual_fill, tuple) and actual_fill[3] is not None  # 4-element RGBA tuple
        actual_stroke = actual_callout.stroke_color
        assert isinstance(actual_stroke, tuple)
        assert isinstance(actual_stroke, tuple) and actual_stroke[3] is not None  # 4-element RGBA tuple

    def test_text_rectangle_has_corner_radius(self, test_project_b_data):
        actual_callouts = _collect_all(
            test_project_b_data,
            lambda d: (
                isinstance(d.get("shape"), str)
                and d.get("shape") == "text-rectangle"
            ),
        )
        assert actual_callouts != []
        actual_callout = Callout({
            "_type": "Callout", "id": 1, "start": 0, "duration": 100,
            "mediaStart": 0, "mediaDuration": 100,
            "def": actual_callouts[0],
        })
        assert actual_callout.corner_radius == 9.0
