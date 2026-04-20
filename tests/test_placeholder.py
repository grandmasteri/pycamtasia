"""Tests for camtasia.timeline.clips.placeholder — PlaceholderMedia clip type."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import clip_from_dict
from camtasia.timeline.clips.placeholder import PlaceholderMedia
from camtasia.timing import seconds_to_ticks

_S5 = seconds_to_ticks(5.0)


# ------------------------------------------------------------------
# PlaceholderMedia: set_source raises
# ------------------------------------------------------------------

class TestPlaceholderSetSource:
    def test_set_source_raises(self):
        p = PlaceholderMedia({
            '_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': _S5,
            'mediaDuration': 1, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [],
        })
        with pytest.raises(TypeError, match='Cannot set_source'):
            p.set_source(1)


# ------------------------------------------------------------------
# PlaceholderMedia: subtitle
# ------------------------------------------------------------------

def test_placeholder_subtitle():
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'metadata': {'placeHolderSubTitle': 'hello'}})
    assert clip.subtitle == 'hello'
    clip.subtitle = 'world'
    assert clip.subtitle == 'world'
    clip2 = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 2, 'start': 0, 'duration': 100})
    assert clip2.subtitle == ''


# ------------------------------------------------------------------
# PlaceholderMedia: width / height
# ------------------------------------------------------------------

def test_placeholder_width_height():
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'attributes': {'width': 1920.0, 'height': 1080.0}})
    assert clip.width == 1920.0
    assert clip.height == 1080.0
    clip2 = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 2, 'start': 0, 'duration': 100})
    assert clip2.width == 0.0
    assert clip2.height == 0.0


# ------------------------------------------------------------------
# PlaceholderMedia: is_placeholder
# ------------------------------------------------------------------

def test_is_placeholder():
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.is_placeholder is True
    assert clip.is_stitched is False


def test_placeholder_subtitle_null_returns_empty_string():
    """Bug 2: subtitle should return '' when placeHolderSubTitle is None."""
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 3, 'start': 0, 'duration': 100,
                           'metadata': {'placeHolderSubTitle': None}})
    assert clip.subtitle == ''
