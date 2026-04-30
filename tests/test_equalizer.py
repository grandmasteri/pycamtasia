"""Tests for the Equalizer audio effect and BaseClip.add_equalizer."""
from __future__ import annotations

from camtasia.effects.audio import Equalizer
from camtasia.effects.base import effect_from_dict


def _param(value, type_: str = "double", interp: str = "linr") -> dict:
    return {"type": type_, "defaultValue": value, "interp": interp}


def _equalizer_dict(bands: list[tuple[float, float]] | None = None) -> dict:
    bands = bands or [(100.0, 3.0), (1000.0, -2.0)]
    params = {}
    for i, (freq, gain) in enumerate(bands):
        params[f'band-{i}-frequency'] = _param(freq)
        params[f'band-{i}-gain-db'] = _param(gain)
    return {
        "effectName": "Equalizer",
        "bypassed": False,
        "category": "categoryAudioEffects",
        "parameters": params,
    }


class TestEqualizerEffect:
    def test_dispatch(self):
        data = {"effectName": "Equalizer", "parameters": {}}
        assert type(effect_from_dict(data)) is Equalizer

    def test_bands_read(self):
        eq = Equalizer(_equalizer_dict())
        assert eq.bands == [
            {'frequency': 100.0, 'gain_db': 3.0},
            {'frequency': 1000.0, 'gain_db': -2.0},
        ]

    def test_bands_setter(self):
        data = _equalizer_dict()
        eq = Equalizer(data)
        eq.bands = [{'frequency': 500.0, 'gain_db': 0.0}]
        assert eq.bands[0] == {'frequency': 500.0, 'gain_db': 0.0}

    def test_empty_bands(self):
        data = {"effectName": "Equalizer", "bypassed": False, "category": "", "parameters": {}}
        eq = Equalizer(data)
        assert eq.bands == []


class TestBaseClipAddEqualizer:
    def _make_clip(self) -> dict:
        return {
            '_type': 'AMFile', 'id': 1, 'start': 0,
            'duration': 705600000, 'effects': [],
        }

    def test_adds_effect(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(self._make_clip())
        effect = clip.add_equalizer([(200.0, 1.5), (4000.0, -3.0)])
        assert isinstance(effect, Equalizer)
        assert clip.effect_count == 1

    def test_bands_match(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(self._make_clip())
        clip.add_equalizer([(200.0, 1.5)])
        eq = Equalizer(clip.effects[0])
        assert eq.bands == [{'frequency': 200.0, 'gain_db': 1.5}]

    def test_effect_category(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip(self._make_clip())
        clip.add_equalizer([(100.0, 0.0)])
        assert clip.effects[0]['category'] == 'categoryAudioEffects'
