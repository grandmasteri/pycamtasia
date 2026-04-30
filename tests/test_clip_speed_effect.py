"""Tests for BaseClip.apply_clip_speed_effect."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.clips import BaseClip, clip_from_dict
from camtasia.timing import seconds_to_ticks


def _clip(duration_s: float = 10.0, **kw: Any) -> BaseClip:
    d: dict[str, Any] = {
        'id': 1,
        '_type': 'VMFile',
        'src': 1,
        'start': 0,
        'duration': seconds_to_ticks(duration_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(duration_s),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'animationTracks': {},
    }
    d.update(kw)
    return clip_from_dict(d)


class TestApplyClipSpeedEffect:
    def test_adds_clip_speed_effect(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(2.0)
        assert c.is_effect_applied('ClipSpeed')

    def test_effect_has_correct_speed_param(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(1.5)
        effect = next(e for e in c.effects if e['effectName'] == 'ClipSpeed')
        assert effect['parameters']['speed'] == 1.5

    def test_does_not_duplicate_on_second_call(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(2.0)
        c.apply_clip_speed_effect(3.0)
        count = sum(1 for e in c.effects if e.get('effectName') == 'ClipSpeed')
        assert count == 1

    def test_preserves_original_speed_on_duplicate(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(2.0)
        c.apply_clip_speed_effect(3.0)
        effect = next(e for e in c.effects if e['effectName'] == 'ClipSpeed')
        assert effect['parameters']['speed'] == 2.0

    def test_with_explicit_duration(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(2.0, duration=seconds_to_ticks(5.0))
        effect = next(e for e in c.effects if e['effectName'] == 'ClipSpeed')
        assert effect['duration'] == seconds_to_ticks(5.0)

    def test_without_duration_has_no_duration_key(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(2.0)
        effect = next(e for e in c.effects if e['effectName'] == 'ClipSpeed')
        assert 'duration' not in effect

    def test_effect_not_bypassed(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(1.0)
        effect = next(e for e in c.effects if e['effectName'] == 'ClipSpeed')
        assert effect['bypassed'] is False

    def test_returns_self(self) -> None:
        c = _clip()
        assert c.apply_clip_speed_effect(2.0) is c

    def test_coexists_with_other_effects(self) -> None:
        c = _clip()
        c.add_glow()
        c.apply_clip_speed_effect(2.0)
        assert c.is_effect_applied('ClipSpeed')
        assert c.is_effect_applied('Glow')
        assert c.effect_count == 2

    def test_removable_by_name(self) -> None:
        c = _clip()
        c.apply_clip_speed_effect(2.0)
        removed = c.remove_effect_by_name('ClipSpeed')
        assert removed == 1
        assert not c.is_effect_applied('ClipSpeed')
