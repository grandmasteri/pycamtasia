"""Tests for PlaceholderMedia.replace_with."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.placeholder import PlaceholderMedia


def _make_placeholder(start: int = 0, duration: int = 705600000) -> PlaceholderMedia:
    return PlaceholderMedia({
        '_type': 'PlaceholderMedia',
        'id': 10,
        'start': start,
        'duration': duration,
        'mediaDuration': duration,
        'scalar': 1,
        'metadata': {'placeHolderTitle': 'TBD'},
    })


class TestReplaceWithRipple:
    def test_adopts_new_duration(self):
        ph = _make_placeholder(duration=1000)
        ph.replace_with({'_type': 'VMFile', 'duration': 5000}, mode='ripple')
        assert ph.duration == 5000

    def test_changes_type(self):
        ph = _make_placeholder()
        ph.replace_with({'_type': 'AMFile', 'duration': 100})
        assert ph.clip_type == 'AMFile'

    def test_sets_src(self):
        ph = _make_placeholder()
        ph.replace_with({'_type': 'VMFile', 'duration': 100, 'src': 42})
        assert ph._data['src'] == 42


class TestReplaceWithClipSpeed:
    def test_keeps_duration_sets_scalar(self):
        ph = _make_placeholder(duration=1000)
        ph.replace_with({'_type': 'VMFile', 'duration': 2000}, mode='clip_speed')
        assert ph.duration == 1000
        assert ph._data['mediaDuration'] == 2000
        assert ph._data['scalar'] == '1/2'

    def test_scalar_one_when_same_duration(self):
        ph = _make_placeholder(duration=1000)
        ph.replace_with({'_type': 'VMFile', 'duration': 1000}, mode='clip_speed')
        assert ph._data['scalar'] == 1


class TestReplaceWithFromEnd:
    def test_aligns_end(self):
        ph = _make_placeholder(start=100, duration=500)
        old_end = 100 + 500
        ph.replace_with({'_type': 'VMFile', 'duration': 300}, mode='from_end')
        assert ph.start + ph.duration == old_end
        assert ph.duration == 300
        assert ph.start == old_end - 300


class TestReplaceWithFromStart:
    def test_keeps_start_and_duration(self):
        ph = _make_placeholder(start=200, duration=1000)
        ph.replace_with({'_type': 'IMFile', 'duration': 5000}, mode='from_start')
        assert ph.start == 200
        assert ph.duration == 1000


class TestReplaceWithInvalidMode:
    def test_raises_on_bad_mode(self):
        ph = _make_placeholder()
        with pytest.raises(ValueError, match="mode must be one of"):
            ph.replace_with({'_type': 'VMFile', 'duration': 100}, mode='invalid')
