"""Tests for behavior preset templates."""
import pytest

from camtasia.templates.behavior_presets import get_behavior_preset


REQUIRED_FIELDS = {'_type', 'effectName', 'bypassed', 'start', 'duration', 'in', 'center', 'out'}


@pytest.mark.parametrize("preset_name, in_name, out_name, meta_key", [
    ('reveal', 'reveal', 'reveal', None),
    ('sliding', 'sliding', 'sliding', None),
    ('fade', 'fadeIn', None, 'Fade'),
    ('flyIn', 'flyIn', None, 'FlyIn'),
    ('popUp', 'hinge', None, 'PopUp'),
], ids=['reveal', 'sliding', 'fade', 'flyIn', 'popUp'])
def test_preset_structure(preset_name, in_name, out_name, meta_key):
    effect = get_behavior_preset(preset_name, 30 * 60 * 5880000)
    assert REQUIRED_FIELDS <= set(effect.keys())
    assert effect['_type'] == 'GenericBehaviorEffect'
    assert effect['effectName'] == preset_name
    assert 'metadata' in effect
    assert effect['in']['attributes']['name'] == in_name
    if out_name is not None:
        assert effect['out']['attributes']['name'] == out_name
    if meta_key is not None:
        assert effect['metadata']['presetName'] == meta_key


def test_unknown_preset_raises():
    with pytest.raises(ValueError, match="Unknown behavior preset 'Bogus'"):
        get_behavior_preset('Bogus', 1000)


@pytest.mark.parametrize("preset_name", ['reveal', 'sliding', 'fade'])
def test_preset_duration_calculated(preset_name):
    clip_dur = 30 * 60 * 5880000
    effect = get_behavior_preset(preset_name, clip_dur)
    assert effect['duration'] == clip_dur
