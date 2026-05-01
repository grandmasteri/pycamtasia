"""Tests for camtasia.effects.behaviors — typed properties and preset factory."""
from __future__ import annotations

import pytest

from camtasia.effects.behaviors import BehaviorPhase, GenericBehaviorEffect

# ------------------------------------------------------------------
# BehaviorPhase: center-phase loop properties
# ------------------------------------------------------------------

class TestBehaviorPhaseLoopProperties:
    """Cover seconds_per_loop, number_of_loops, delay_between_loops."""

    def test_seconds_per_loop_numeric(self):
        data = {"attributes": {"secondsPerLoop": 2.5}, "parameters": {}}
        assert BehaviorPhase(data).seconds_per_loop == 2.5

    def test_seconds_per_loop_string_fraction(self):
        data = {"attributes": {"secondsPerLoop": "4/5"}, "parameters": {}}
        assert BehaviorPhase(data).seconds_per_loop == 0.8

    def test_seconds_per_loop_missing_defaults_zero(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).seconds_per_loop == 0.0

    def test_seconds_per_loop_setter(self):
        data = {"attributes": {}, "parameters": {}}
        p = BehaviorPhase(data)
        p.seconds_per_loop = 3.0
        assert data["attributes"]["secondsPerLoop"] == 3.0

    def test_number_of_loops_getter(self):
        data = {"attributes": {"numberOfLoops": -1}, "parameters": {}}
        assert BehaviorPhase(data).number_of_loops == -1

    def test_number_of_loops_missing_defaults_zero(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).number_of_loops == 0

    def test_number_of_loops_setter(self):
        data = {"attributes": {}, "parameters": {}}
        p = BehaviorPhase(data)
        p.number_of_loops = 5
        assert data["attributes"]["numberOfLoops"] == 5

    def test_delay_between_loops_getter(self):
        data = {"attributes": {"delayBetweenLoops": 1.5}, "parameters": {}}
        assert BehaviorPhase(data).delay_between_loops == 1.5

    def test_delay_between_loops_missing_defaults_zero(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).delay_between_loops == 0.0

    def test_delay_between_loops_setter(self):
        data = {"attributes": {}, "parameters": {}}
        p = BehaviorPhase(data)
        p.delay_between_loops = 0.25
        assert data["attributes"]["delayBetweenLoops"] == 0.25


# ------------------------------------------------------------------
# BehaviorPhase: animation parameter accessors (dict and scalar paths)
# ------------------------------------------------------------------

class TestBehaviorPhaseAnimationParameters:
    """Cover opacity, jump, rotation, scale, shift — both dict and scalar branches."""

    # --- opacity ---

    def test_opacity_from_dict(self):
        data = {"attributes": {}, "parameters": {"opacity": {"defaultValue": 0.8}}}
        assert BehaviorPhase(data).opacity == 0.8

    def test_opacity_from_scalar(self):
        data = {"attributes": {}, "parameters": {"opacity": 0.5}}
        assert BehaviorPhase(data).opacity == 0.5

    def test_opacity_missing(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).opacity == 1.0

    def test_opacity_setter_into_dict(self):
        param = {"defaultValue": 0.8}
        data = {"attributes": {}, "parameters": {"opacity": param}}
        BehaviorPhase(data).opacity = 0.3
        assert param["defaultValue"] == 0.3

    def test_opacity_setter_into_scalar(self):
        data = {"attributes": {}, "parameters": {}}
        BehaviorPhase(data).opacity = 0.7
        assert data["parameters"]["opacity"] == 0.7

    # --- jump ---

    def test_jump_from_dict(self):
        data = {"attributes": {}, "parameters": {"jump": {"defaultValue": 5.0}}}
        assert BehaviorPhase(data).jump == 5.0

    def test_jump_from_scalar(self):
        data = {"attributes": {}, "parameters": {"jump": 2.0}}
        assert BehaviorPhase(data).jump == 2.0

    def test_jump_missing(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).jump == 0.0

    def test_jump_setter_into_dict(self):
        param = {"defaultValue": 1.0}
        data = {"attributes": {}, "parameters": {"jump": param}}
        BehaviorPhase(data).jump = 10.0
        assert param["defaultValue"] == 10.0

    def test_jump_setter_into_scalar(self):
        data = {"attributes": {}, "parameters": {}}
        BehaviorPhase(data).jump = 4.0
        assert data["parameters"]["jump"] == 4.0

    # --- rotation ---

    def test_rotation_from_dict(self):
        data = {"attributes": {}, "parameters": {"rotation": {"defaultValue": 0.035}}}
        assert BehaviorPhase(data).rotation == 0.035

    def test_rotation_from_scalar(self):
        data = {"attributes": {}, "parameters": {"rotation": 1.5}}
        assert BehaviorPhase(data).rotation == 1.5

    def test_rotation_missing(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).rotation == 0.0

    def test_rotation_setter_into_dict(self):
        param = {"defaultValue": 0.0}
        data = {"attributes": {}, "parameters": {"rotation": param}}
        BehaviorPhase(data).rotation = 0.5
        assert param["defaultValue"] == 0.5

    def test_rotation_setter_into_scalar(self):
        data = {"attributes": {}, "parameters": {}}
        BehaviorPhase(data).rotation = 0.1
        assert data["parameters"]["rotation"] == 0.1

    # --- scale ---

    def test_scale_from_dict(self):
        data = {"attributes": {}, "parameters": {"scale": {"defaultValue": 1.15}}}
        assert BehaviorPhase(data).scale == 1.15

    def test_scale_from_scalar(self):
        data = {"attributes": {}, "parameters": {"scale": 2.0}}
        assert BehaviorPhase(data).scale == 2.0

    def test_scale_missing(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).scale == 1.0

    def test_scale_setter_into_dict(self):
        param = {"defaultValue": 1.0}
        data = {"attributes": {}, "parameters": {"scale": param}}
        BehaviorPhase(data).scale = 1.5
        assert param["defaultValue"] == 1.5

    def test_scale_setter_into_scalar(self):
        data = {"attributes": {}, "parameters": {}}
        BehaviorPhase(data).scale = 0.5
        assert data["parameters"]["scale"] == 0.5

    # --- shift ---

    def test_shift_from_dict(self):
        data = {
            "attributes": {},
            "parameters": {
                "horizontal": {"defaultValue": 6.0},
                "vertical": {"defaultValue": 2.0},
            },
        }
        assert BehaviorPhase(data).shift == (6.0, 2.0)

    def test_shift_from_scalar(self):
        data = {"attributes": {}, "parameters": {"horizontal": 3.0, "vertical": 1.0}}
        assert BehaviorPhase(data).shift == (3.0, 1.0)

    def test_shift_missing(self):
        data = {"attributes": {}, "parameters": {}}
        assert BehaviorPhase(data).shift == (0.0, 0.0)

    def test_shift_setter_into_dict(self):
        h_param = {"defaultValue": 0.0}
        v_param = {"defaultValue": 0.0}
        data = {"attributes": {}, "parameters": {"horizontal": h_param, "vertical": v_param}}
        BehaviorPhase(data).shift = (5.0, 3.0)
        assert h_param["defaultValue"] == 5.0
        assert v_param["defaultValue"] == 3.0

    def test_shift_setter_into_scalar(self):
        data = {"attributes": {}, "parameters": {}}
        BehaviorPhase(data).shift = (7.0, 4.0)
        assert data["parameters"]["horizontal"] == 7.0
        assert data["parameters"]["vertical"] == 4.0


# ------------------------------------------------------------------
# GenericBehaviorEffect.from_preset
# ------------------------------------------------------------------

_ALL_PRESETS = [
    "flyIn", "flyOut", "emphasize", "jiggle", "reveal",
    "fade", "popUp", "sliding", "pulsating", "shifting",
]


class TestFromPreset:
    """Cover the from_preset classmethod for all 10 presets."""

    @pytest.mark.parametrize("preset_name", _ALL_PRESETS)
    def test_from_preset_returns_effect(self, preset_name: str):
        effect = GenericBehaviorEffect.from_preset(preset_name)
        assert effect.effect_name == preset_name
        assert isinstance(effect, GenericBehaviorEffect)
        assert effect.duration is not None

    def test_from_preset_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown behavior preset"):
            GenericBehaviorEffect.from_preset("nonexistent")
