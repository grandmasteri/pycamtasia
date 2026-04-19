"""Tests for BaseClip.clone() and BaseClip.matches_any_type()."""
from __future__ import annotations

from camtasia.timeline.clips import BaseClip, clip_from_dict
from camtasia.types import ClipType


def _make_clip(clip_type: str = 'VMFile', clip_id: int = 42) -> BaseClip:
    return clip_from_dict({
        '_type': clip_type,
        'id': clip_id,
        'start': 0,
        'duration': 705_600_000,
        'mediaStart': 0,
        'mediaDuration': 705_600_000,
        'effects': [{'effectName': 'Glow', 'bypassed': False, 'category': '', 'parameters': {}}],
    })


# ── clone ────────────────────────────────────────────────────────────

class TestClone:
    def test_clone_returns_base_clip(self):
        clip = _make_clip()
        cloned = clip.clone()
        assert isinstance(cloned, BaseClip)

    def test_clone_has_sentinel_id(self):
        clip = _make_clip()
        cloned = clip.clone()
        assert cloned.id == -1

    def test_clone_preserves_type(self):
        clip = _make_clip('AMFile')
        cloned = clip.clone()
        assert cloned.clip_type == 'AMFile'

    def test_clone_preserves_timing(self):
        clip = _make_clip()
        cloned = clip.clone()
        assert cloned.start == clip.start
        assert cloned.duration == clip.duration

    def test_clone_deep_copies_effects(self):
        clip = _make_clip()
        cloned = clip.clone()
        assert cloned.effect_names == clip.effect_names
        # Mutating clone's effects must not affect original
        cloned._data['effects'].clear()
        assert len(clip.effect_names) == 1

    def test_clone_is_independent(self):
        clip = _make_clip()
        cloned = clip.clone()
        cloned.start = 999
        assert clip.start == 0


# ── matches_any_type ─────────────────────────────────────────────────

class TestMatchesAnyType:
    def test_matches_single_string(self):
        clip = _make_clip('VMFile')
        assert clip.matches_any_type('VMFile')

    def test_matches_single_enum(self):
        clip = _make_clip('AMFile')
        assert clip.matches_any_type(ClipType.AUDIO)

    def test_matches_among_several(self):
        clip = _make_clip('IMFile')
        assert clip.matches_any_type(ClipType.AUDIO, ClipType.IMAGE, ClipType.VIDEO)

    def test_no_match_returns_false(self):
        clip = _make_clip('VMFile')
        assert not clip.matches_any_type(ClipType.AUDIO, ClipType.IMAGE)

    def test_empty_args_returns_false(self):
        clip = _make_clip()
        assert not clip.matches_any_type()
