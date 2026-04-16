"""Tests for Group mutation methods: remove_internal_clip, clear_all_internal_clips,
set_dimensions, rename.
"""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import Group
from camtasia.timing import seconds_to_ticks


def _clip_data(clip_type: str, clip_id: int, start_s: float, dur_s: float) -> dict:
    """Build minimal clip data dict."""
    return {
        '_type': clip_type,
        'id': clip_id,
        'src': 1,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
    }


def _make_group(tracks_data: list[list[dict]], *, transitions: list[list[dict]] | None = None) -> Group:
    """Build a Group from track media lists with optional per-track transitions."""
    tracks = []
    for track_index, medias in enumerate(tracks_data):
        track_transitions = transitions[track_index] if transitions else []
        tracks.append({
            'trackIndex': track_index,
            'medias': medias,
            'transitions': track_transitions,
        })
    return Group({
        '_type': 'Group',
        'id': 1,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(10.0),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
        'attributes': {'ident': 'TestGroup', 'widthAttr': 1920.0, 'heightAttr': 1080.0},
        'tracks': tracks,
    })


# ── remove_internal_clip ────────────────────────────────────────────


class TestRemoveInternalClip:
    """Group.remove_internal_clip removes a clip by ID with transition cascade."""

    def test_removes_clip_from_single_track(self) -> None:
        group: Group = _make_group([
            [_clip_data('VMFile', 10, 0.0, 5.0), _clip_data('VMFile', 11, 5.0, 3.0)],
        ])
        group.remove_internal_clip(10)
        remaining_ids: list[int] = [c.id for c in group.all_internal_clips]
        assert remaining_ids == [11]

    def test_removes_clip_from_correct_track(self) -> None:
        group: Group = _make_group([
            [_clip_data('VMFile', 10, 0.0, 5.0)],
            [_clip_data('AMFile', 20, 0.0, 3.0)],
        ])
        group.remove_internal_clip(20)
        assert len(group.all_internal_clips) == 1
        assert group.all_internal_clips[0].id == 10

    def test_raises_key_error_for_missing_id(self) -> None:
        group: Group = _make_group([[_clip_data('VMFile', 10, 0.0, 5.0)]])
        with pytest.raises(KeyError, match='No internal clip with id=999'):
            group.remove_internal_clip(999)

    def test_raises_key_error_on_empty_group(self) -> None:
        group: Group = _make_group([])
        with pytest.raises(KeyError):
            group.remove_internal_clip(1)


# ── clear_all_internal_clips ────────────────────────────────────────


class TestClearAllInternalClips:
    """Group.clear_all_internal_clips empties all tracks and returns count."""

    def test_returns_total_removed_count(self) -> None:
        group: Group = _make_group([
            [_clip_data('VMFile', 10, 0.0, 5.0)],
            [_clip_data('AMFile', 20, 0.0, 3.0), _clip_data('AMFile', 21, 3.0, 2.0)],
        ])
        removed_count: int = group.clear_all_internal_clips()
        assert removed_count == 3

    def test_all_tracks_empty_after_clear(self) -> None:
        group: Group = _make_group([
            [_clip_data('VMFile', 10, 0.0, 5.0)],
            [_clip_data('AMFile', 20, 0.0, 3.0)],
        ])
        group.clear_all_internal_clips()
        assert group.all_internal_clips == []

    def test_returns_zero_for_empty_group(self) -> None:
        group: Group = _make_group([])
        assert group.clear_all_internal_clips() == 0

    def test_returns_zero_for_tracks_with_no_clips(self) -> None:
        group: Group = _make_group([[]])
        assert group.clear_all_internal_clips() == 0


# ── set_dimensions ──────────────────────────────────────────────────


class TestSetDimensions:
    """Group.set_dimensions updates widthAttr and heightAttr."""

    def test_sets_width_and_height(self) -> None:
        group: Group = _make_group([[]])
        group.set_dimensions(3840.0, 2160.0)
        assert group.width == 3840.0
        assert group.height == 2160.0

    def test_returns_self_for_chaining(self) -> None:
        group: Group = _make_group([[]])
        result = group.set_dimensions(1280.0, 720.0)
        assert result is group

    def test_overwrites_existing_dimensions(self) -> None:
        group: Group = _make_group([[]])
        assert group.width == 1920.0
        group.set_dimensions(800.0, 600.0)
        assert group.width == 800.0
        assert group.height == 600.0

    def test_creates_attributes_if_missing(self) -> None:
        group: Group = Group({
            '_type': 'Group',
            'id': 1,
            'start': 0,
            'duration': 100,
            'mediaStart': 0,
            'mediaDuration': 100,
            'scalar': 1,
            'parameters': {},
            'effects': [],
            'metadata': {},
            'animationTracks': {},
            'tracks': [],
        })
        group.set_dimensions(640.0, 480.0)
        assert group.width == 640.0
        assert group.height == 480.0


# ── rename ──────────────────────────────────────────────────────────


class TestRename:
    """Group.rename updates the ident attribute."""

    def test_sets_new_name(self) -> None:
        group: Group = _make_group([[]])
        group.rename('NewGroupName')
        assert group.ident == 'NewGroupName'

    def test_returns_self_for_chaining(self) -> None:
        group: Group = _make_group([[]])
        result = group.rename('Chained')
        assert result is group

    def test_overwrites_existing_name(self) -> None:
        group: Group = _make_group([[]])
        assert group.ident == 'TestGroup'
        group.rename('Renamed')
        assert group.ident == 'Renamed'

    def test_creates_attributes_if_missing(self) -> None:
        group: Group = Group({
            '_type': 'Group',
            'id': 1,
            'start': 0,
            'duration': 100,
            'mediaStart': 0,
            'mediaDuration': 100,
            'scalar': 1,
            'parameters': {},
            'effects': [],
            'metadata': {},
            'animationTracks': {},
            'tracks': [],
        })
        group.rename('FromScratch')
        assert group.ident == 'FromScratch'

    def test_fluent_chain_with_set_dimensions(self) -> None:
        group: Group = _make_group([[]])
        group.rename('Sized').set_dimensions(1280.0, 720.0)
        assert group.ident == 'Sized'
        assert group.width == 1280.0
