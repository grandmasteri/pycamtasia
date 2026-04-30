"""Tests for BaseClip.add_emphasize builder method."""
from __future__ import annotations

import pytest

from camtasia.effects.visual import Emphasize
from camtasia.timeline.clips import EDIT_RATE, BaseClip
from camtasia.timing import seconds_to_ticks


def _make_clip(**overrides) -> BaseClip:
    data: dict = {
        '_type': 'AMFile',
        'id': 1,
        'start': 0,
        'duration': EDIT_RATE * 10,
        'mediaDuration': EDIT_RATE * 10,
        'mediaStart': 0,
        'scalar': 1,
        'effects': [],
        **overrides,
    }
    return BaseClip(data)


class TestAddEmphasize:
    """Tests for the add_emphasize builder method."""

    def test_defaults(self):
        clip = _make_clip()
        eff = clip.add_emphasize()
        assert isinstance(eff, Emphasize)
        assert eff.amount == 0.5
        assert eff.ramp_position == 2.0  # 'inside' maps to 2
        assert eff.ramp_in_ticks == 0
        assert eff.ramp_out_ticks == 0

    def test_effect_appended_to_clip(self):
        clip = _make_clip()
        clip.add_emphasize()
        assert len(clip.effects) == 1
        assert clip.effects[0]['effectName'] == 'Emphasize'

    @pytest.mark.parametrize(
        ("position_str", "expected_value"),
        [
            ('outside', 0),
            ('span', 1),
            ('inside', 2),
        ],
    )
    def test_ramp_position_values(self, position_str, expected_value):
        clip = _make_clip()
        eff = clip.add_emphasize(ramp_position=position_str)
        assert eff.ramp_position == float(expected_value)
        assert clip.effects[0]['parameters']['emphasizeRampPosition'] == expected_value

    def test_ramp_in_out_seconds_converted_to_ticks(self):
        clip = _make_clip()
        eff = clip.add_emphasize(ramp_in_seconds=1.5, ramp_out_seconds=2.0)
        assert eff.ramp_in_ticks == seconds_to_ticks(1.5)
        assert eff.ramp_out_ticks == seconds_to_ticks(2.0)

    def test_intensity_maps_to_amount(self):
        clip = _make_clip()
        eff = clip.add_emphasize(intensity=0.8)
        assert eff.amount == 0.8
        assert clip.effects[0]['parameters']['emphasizeAmount'] == 0.8

    def test_invalid_ramp_position_raises(self):
        clip = _make_clip()
        with pytest.raises(ValueError, match="ramp_position must be"):
            clip.add_emphasize(ramp_position='invalid')

    def test_serialized_parameter_names(self):
        clip = _make_clip()
        clip.add_emphasize(
            ramp_position='span',
            ramp_in_seconds=0.5,
            ramp_out_seconds=1.0,
            intensity=0.7,
        )
        params = clip.effects[0]['parameters']
        assert set(params.keys()) == {
            'emphasizeAmount',
            'emphasizeRampPosition',
            'emphasizeRampInTime',
            'emphasizeRampOutTime',
        }
        assert params['emphasizeAmount'] == 0.7
        assert params['emphasizeRampPosition'] == 1
        assert params['emphasizeRampInTime'] == seconds_to_ticks(0.5)
        assert params['emphasizeRampOutTime'] == seconds_to_ticks(1.0)

    def test_effect_category_is_audio(self):
        clip = _make_clip()
        clip.add_emphasize()
        assert clip.effects[0]['category'] == 'categoryAudioEffects'

    def test_multiple_emphasize_effects(self):
        clip = _make_clip()
        eff1 = clip.add_emphasize(intensity=0.3)
        eff2 = clip.add_emphasize(intensity=0.9)
        assert len(clip.effects) == 2
        assert eff1.amount == 0.3
        assert eff2.amount == 0.9
