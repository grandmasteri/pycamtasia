"""Tests for camtasia.timeline.clips.placeholder — PlaceholderMedia clip type."""
from __future__ import annotations

import ast
import inspect

import pytest

from camtasia.timeline.clips import clip_from_dict, placeholder
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
                           'attributes': {'widthAttr': 1920.0, 'heightAttr': 1080.0}})
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



def test_no_sys_import() -> None:
    """placeholder.py should not import sys."""
    source = inspect.getsource(placeholder)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != 'sys', 'sys should not be imported in placeholder.py'
        if isinstance(node, ast.ImportFrom) and node.module == 'sys':
            raise AssertionError('sys should not be imported in placeholder.py')


class TestPlaceholderWidthHeightUsesAttrKeys:
    """width/height must read widthAttr/heightAttr, not width/height."""

    def test_reads_widthAttr(self):
        clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 10, 'start': 0, 'duration': 100,
                               'attributes': {'widthAttr': 1280.0, 'heightAttr': 720.0}})
        assert clip.width == 1280.0
        assert clip.height == 720.0

    def test_old_keys_ignored(self):
        """Old 'width'/'height' keys should NOT be read."""
        clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 11, 'start': 0, 'duration': 100,
                               'attributes': {'width': 1920.0, 'height': 1080.0}})
        assert clip.width == 0.0
        assert clip.height == 0.0
