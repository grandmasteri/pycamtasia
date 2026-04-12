"""Tests for behavior preset templates."""
import pytest

from camtasia.templates.behavior_presets import get_behavior_preset


REQUIRED_FIELDS = {'_type', 'effectName', 'bypassed', 'start', 'duration', 'in', 'center', 'out'}


def test_reveal_preset_structure():
    effect = get_behavior_preset('Reveal', 30 * 60 * 5880000)
    assert REQUIRED_FIELDS <= set(effect.keys())
    assert effect['_type'] == 'GenericBehaviorEffect'
    assert effect['effectName'] == 'reveal'
    assert 'metadata' in effect
    assert effect['in']['attributes']['name'] == 'reveal'
    assert effect['out']['attributes']['name'] == 'reveal'


def test_sliding_preset_structure():
    effect = get_behavior_preset('Sliding', 30 * 60 * 5880000)
    assert REQUIRED_FIELDS <= set(effect.keys())
    assert effect['_type'] == 'GenericBehaviorEffect'
    assert effect['effectName'] == 'sliding'
    assert 'metadata' in effect
    assert effect['in']['attributes']['name'] == 'sliding'
    assert effect['out']['attributes']['name'] == 'sliding'


def test_unknown_preset_raises():
    with pytest.raises(ValueError, match="Unknown behavior preset 'Bogus'"):
        get_behavior_preset('Bogus', 1000)


def test_preset_duration_calculated():
    clip_dur = 30 * 60 * 5880000
    reveal = get_behavior_preset('Reveal', clip_dur)
    assert reveal['duration'] == clip_dur - reveal['start']

    sliding = get_behavior_preset('Sliding', clip_dur)
    assert sliding['duration'] == clip_dur - sliding['start']
