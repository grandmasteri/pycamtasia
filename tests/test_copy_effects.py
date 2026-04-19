"""Tests for BaseClip.copy_effects_from()."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.base import BaseClip


def _make_clip(**overrides) -> BaseClip:
    data = {
        'id': overrides.pop('id', 1),
        '_type': 'VMFile',
        'start': 0,
        'duration': 100,
        'mediaStart': 0,
        'mediaDuration': 100,
        **overrides,
    }
    return BaseClip(data)


class TestCopyEffectsFrom:
    def test_copy_effects_from_copies_all(self):
        source = _make_clip(id=1, effects=[
            {'effectName': 'Glow', 'parameters': {'radius': 10}},
            {'effectName': 'DropShadow', 'parameters': {'offset': 5}},
        ])
        target = _make_clip(id=2)

        target.copy_effects_from(source)

        assert [e['effectName'] for e in target.effects] == ['Glow', 'DropShadow']

    def test_copy_effects_from_appends(self):
        source = _make_clip(id=1, effects=[
            {'effectName': 'Glow', 'parameters': {'radius': 10}},
        ])
        target = _make_clip(id=2, effects=[
            {'effectName': 'Border', 'parameters': {'width': 4}},
        ])

        target.copy_effects_from(source)

        assert [e['effectName'] for e in target.effects] == ['Border', 'Glow']

    def test_copy_effects_from_deep_copies(self):
        source = _make_clip(id=1, effects=[
            {'effectName': 'Glow', 'parameters': {'radius': 10}},
        ])
        target = _make_clip(id=2)

        target.copy_effects_from(source)

        # Mutating the copy should not affect the source
        target.effects[0]['parameters']['radius'] = 999
        assert source.effects[0]['parameters']['radius'] == 10

    def test_copy_effects_from_chaining(self):
        source = _make_clip(id=1, effects=[
            {'effectName': 'Glow', 'parameters': {'radius': 10}},
        ])
        target = _make_clip(id=2)

        result = target.copy_effects_from(source)

        assert result is target
