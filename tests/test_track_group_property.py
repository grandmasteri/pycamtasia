"""Tests for Track.set_group_property and Track.get_nested_subgroup."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.group import Group
from camtasia.timeline.track import Track


def _make_track(medias=None):
    """Build a minimal Track with optional clips."""
    data = {
        'trackIndex': 0,
        'medias': medias or [],
        'parameters': {},
        'transitions': [],
    }
    attrs = {'ident': 'Track 1'}
    return Track(attrs, data)


def _make_group(group_id, ident='', tracks=None, **extra):
    """Build a minimal Group clip dict."""
    return {
        'id': group_id,
        '_type': 'Group',
        'start': 0,
        'duration': 1000,
        'mediaStart': 0,
        'mediaDuration': 1000,
        'scalar': 1,
        'attributes': {'ident': ident, 'widthAttr': 1920.0, 'heightAttr': 1080.0},
        'parameters': {'scale0': {'type': 'double', 'defaultValue': 1.0, 'interp': 'eioe'}},
        'effects': [],
        'metadata': {'effectApplied': 'none'},
        'animationTracks': {},
        'tracks': tracks or [],
        **extra,
    }


def _make_inner_track(medias=None, index=0):
    """Build a minimal internal Group track dict."""
    return {
        'trackIndex': index,
        'medias': medias or [],
        'parameters': {},
        'ident': '',
        'audioMuted': False,
        'videoHidden': False,
        'magnetic': False,
        'matte': 0,
        'solo': False,
    }


class TestSetGroupProperty:
    def test_sets_top_level_key(self):
        group = _make_group(10)
        track = _make_track(medias=[group])
        track.set_group_property(10, 'scalar', 2)
        assert group['scalar'] == 2

    def test_sets_nested_key(self):
        group = _make_group(10)
        track = _make_track(medias=[group])
        track.set_group_property(10, 'attributes.ident', 'MyGroup')
        assert group['attributes']['ident'] == 'MyGroup'

    def test_sets_deeply_nested_key(self):
        group = _make_group(10)
        track = _make_track(medias=[group])
        track.set_group_property(10, 'parameters.scale0.defaultValue', 2.5)
        assert group['parameters']['scale0']['defaultValue'] == 2.5

    def test_raises_on_missing_clip(self):
        track = _make_track()
        with pytest.raises(KeyError, match='No clip with id=99'):
            track.set_group_property(99, 'scalar', 1)

    def test_raises_on_non_group_clip(self):
        clip = {
            'id': 10, '_type': 'VMFile', 'start': 0, 'duration': 1000,
            'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        track = _make_track(medias=[clip])
        with pytest.raises(TypeError, match='not a Group'):
            track.set_group_property(10, 'scalar', 1)

    def test_raises_on_missing_intermediate_path(self):
        group = _make_group(10)
        track = _make_track(medias=[group])
        with pytest.raises(KeyError, match="Path segment 'nonexistent'"):
            track.set_group_property(10, 'nonexistent.key', 'val')

    def test_sets_metadata_key(self):
        group = _make_group(10)
        track = _make_track(medias=[group])
        track.set_group_property(10, 'metadata.effectApplied', 'blur')
        assert group['metadata']['effectApplied'] == 'blur'


class TestGetNestedSubgroup:
    def test_finds_direct_subgroup(self):
        inner_group = _make_group(20, ident='SubA')
        outer_group = _make_group(10, tracks=[_make_inner_track(medias=[inner_group])])
        track = _make_track(medias=[outer_group])
        result = track.get_nested_subgroup(10, 'SubA')
        assert result is not None
        assert isinstance(result, Group)
        assert result.ident == 'SubA'

    def test_finds_deeply_nested_subgroup(self):
        deep = _make_group(30, ident='Deep')
        mid = _make_group(20, ident='Mid', tracks=[_make_inner_track(medias=[deep])])
        outer = _make_group(10, tracks=[_make_inner_track(medias=[mid])])
        track = _make_track(medias=[outer])
        result = track.get_nested_subgroup(10, 'Deep')
        assert result is not None
        assert result.ident == 'Deep'

    def test_returns_none_when_not_found(self):
        inner = _make_group(20, ident='Other')
        outer = _make_group(10, tracks=[_make_inner_track(medias=[inner])])
        track = _make_track(medias=[outer])
        assert track.get_nested_subgroup(10, 'Missing') is None

    def test_raises_on_missing_clip(self):
        track = _make_track()
        with pytest.raises(KeyError, match='No clip with id=99'):
            track.get_nested_subgroup(99, 'X')

    def test_raises_on_non_group_clip(self):
        clip = {
            'id': 10, '_type': 'VMFile', 'start': 0, 'duration': 1000,
            'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        track = _make_track(medias=[clip])
        with pytest.raises(TypeError, match='not a Group'):
            track.get_nested_subgroup(10, 'X')

    def test_returns_none_for_empty_group(self):
        outer = _make_group(10)
        track = _make_track(medias=[outer])
        assert track.get_nested_subgroup(10, 'Anything') is None
