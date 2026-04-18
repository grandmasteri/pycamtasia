"""Tests for uncovered lines in unified.py — TypeError-raising overrides."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.unified import UnifiedMedia


@pytest.fixture
def um():
    return UnifiedMedia({
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
        'video': {'_type': 'VMFile', 'id': 2, 'src': 1, 'start': 0, 'duration': 100,
                  'attributes': {}, 'parameters': {}, 'effects': []},
        'audio': {'_type': 'AMFile', 'id': 3, 'src': 1, 'start': 0, 'duration': 100,
                  'attributes': {}, 'parameters': {}, 'effects': []},
    })


def test_add_effect_raises(um):
    """Line 71."""
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_effect({'effectName': 'Glow'})


def test_add_drop_shadow_raises(um):
    """Line 74."""
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_drop_shadow()


def test_add_round_corners_raises(um):
    """Line 85."""
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_round_corners()


def test_add_glow_raises(um):
    """Line 88."""
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_glow()


def test_add_glow_timed_raises(um):
    """Line 91."""
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_glow_timed()


def test_copy_effects_from_raises(um):
    """Line 102."""
    with pytest.raises(TypeError, match='Effects must be added'):
        um.copy_effects_from(um)


def test_set_source_raises(um):
    """Line 105 (set_source on UnifiedMedia)."""
    with pytest.raises(TypeError, match='Cannot set_source'):
        um.set_source(42)
