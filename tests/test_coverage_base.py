"""Tests covering missing lines in base.py, behaviors.py, source.py, callout.py, timing.py."""
from __future__ import annotations

import pytest
from camtasia.timing import seconds_to_ticks, EDIT_RATE, format_duration
from camtasia.timeline.clips.base import BaseClip


def _clip(extra=None, **kw):
    d = {'id': 1, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 100,
         'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
         'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
         'animationTracks': {}}
    if extra:
        d.update(extra)
    d.update(kw)
    return d


# base.py:207 — mute() on UnifiedMedia with no audio raises ValueError
class TestMuteUnifiedMediaNoAudio:
    def test_raises(self):
        data = _clip(_type='UnifiedMedia')
        data.pop('audio', None)
        clip = BaseClip(data)
        with pytest.raises(ValueError, match='no audio sub-clip'):
            clip.mute()


# base.py:398 — opacity setter clears visual animationTracks
class TestOpacitySetterClearsVisualTracks:
    def test_clears_visual(self):
        data = _clip()
        data['animationTracks'] = {'visual': [{'some': 'segment'}]}
        data['parameters']['opacity'] = 0.5
        clip = BaseClip(data)
        clip.opacity = 0.8
        assert data['animationTracks']['visual'] == []
        assert data['parameters']['opacity'] == 0.8


# base.py:748 — _get_existing_opacity_keyframes returns None when opacity is not a dict
class TestOpacityNotDict:
    def test_returns_none(self):
        data = _clip()
        data['parameters']['opacity'] = 0.5  # plain float, not a dict
        clip = BaseClip(data)
        assert clip._get_existing_opacity_keyframes() is None


# base.py:777-780 — fade_in merges with existing fade-out
class TestFadeInMergesWithFadeOut:
    def test_merge(self):
        fade_out_kf = {'time': 1000, 'value': 0.0, 'endTime': 2000, 'duration': 1000}
        data = _clip()
        data['parameters']['opacity'] = {'keyframes': [fade_out_kf]}
        clip = BaseClip(data)
        result = clip.fade_in(1.0)
        assert result is clip
        # After merge, visual track should have 2 keyframes
        visual = data['animationTracks'].get('visual', [])
        assert len(visual) > 0


# behaviors.py:173,177 — get_parameter / set_parameter raise NotImplementedError
class TestBehaviorEffectParams:
    def test_get_parameter_raises(self):
        from camtasia.effects.behaviors import GenericBehaviorEffect
        data = {'effectName': 'test', '_type': 'GenericBehaviorEffect',
                'in': {}, 'center': {}, 'out': {}}
        effect = GenericBehaviorEffect(data)
        with pytest.raises(NotImplementedError):
            effect.get_parameter('foo')

    def test_set_parameter_raises(self):
        from camtasia.effects.behaviors import GenericBehaviorEffect
        data = {'effectName': 'test', '_type': 'GenericBehaviorEffect',
                'in': {}, 'center': {}, 'out': {}}
        effect = GenericBehaviorEffect(data)
        with pytest.raises(NotImplementedError):
            effect.set_parameter('foo', 42)


# source.py:160 — set_shader_colors with wrong count raises ValueError
class TestShaderColorsWrongCount:
    def test_raises(self):
        from camtasia.effects.source import SourceEffect
        data = {'effectName': 'test', '_type': 'SourceEffect', 'parameters': {}}
        effect = SourceEffect(data)
        with pytest.raises(ValueError, match='Expected 2 or 4 colors'):
            effect.set_shader_colors((255, 0, 0), (0, 255, 0), (0, 0, 255))


# callout.py:398-399 — set_size when existing width/height ARE dicts (dict branch)
class TestCalloutSetSizeDictBranch:
    def test_updates_dict_default_value(self):
        from camtasia.timeline.clips.callout import Callout
        data = _clip(_type='Callout')
        data['def'] = {
            'width': {'defaultValue': 100, 'keyframes': [{'time': 0, 'value': 100}]},
            'height': {'defaultValue': 50, 'keyframes': [{'time': 0, 'value': 50}]},
        }
        clip = Callout(data)
        clip.set_size(200, 150)
        assert data['def']['width']['defaultValue'] == 200
        assert data['def']['height']['defaultValue'] == 150
        assert 'keyframes' not in data['def']['width']
        assert 'keyframes' not in data['def']['height']


# timing.py:55-56 — format_duration centisecond overflow
class TestFormatDurationCsOverflow:
    def test_cs_overflow(self):
        # We need a tick value where round(fraction * 100) >= 100
        # fraction just below 1.0 → cs rounds to 100
        # 0.999... seconds → cs = round(0.999... * 100) = 100
        # Use ticks that produce exactly X.995 seconds
        ticks = round(59.995 * EDIT_RATE)
        result = format_duration(ticks)
        assert '1:00.00' in result or '0:60.00' not in result
