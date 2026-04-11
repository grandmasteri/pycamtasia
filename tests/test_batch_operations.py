"""Tests for camtasia.operations.batch."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from camtasia.operations.batch import (
    apply_to_all_tracks,
    apply_to_clips,
    apply_to_track,
    fade_all,
    move_all,
    scale_all,
    set_opacity_all,
)


def _make_clip(x: float = 0.0, y: float = 0.0) -> MagicMock:
    clip = MagicMock()
    clip.translation = (x, y)
    return clip


def _make_track(n: int) -> MagicMock:
    track = MagicMock()
    track.clips = [_make_clip() for _ in range(n)]
    return track


def _make_timeline(track_sizes: list[int]) -> MagicMock:
    tl = MagicMock()
    tl.tracks = [_make_track(n) for n in track_sizes]
    return tl


class TestApplyToClips:
    def test_calls_fn(self):
        clips = [_make_clip() for _ in range(3)]
        fn = MagicMock()
        apply_to_clips(clips, fn)
        assert fn.call_count == 3
        for clip in clips:
            fn.assert_any_call(clip)

    def test_returns_count(self):
        clips = [_make_clip() for _ in range(5)]
        assert apply_to_clips(clips, lambda c: None) == 5


class TestApplyToTrack:
    def test_processes_all_clips(self):
        track = _make_track(4)
        fn = MagicMock()
        result = apply_to_track(track, fn)
        assert result == 4
        assert fn.call_count == 4


class TestApplyToAllTracks:
    def test_processes_all_tracks(self):
        tl = _make_timeline([2, 3])
        fn = MagicMock()
        result = apply_to_all_tracks(tl, fn)
        assert result == 5
        assert fn.call_count == 5


class TestSetOpacityAll:
    def test_sets_opacity(self):
        clips = [_make_clip() for _ in range(3)]
        result = set_opacity_all(clips, 0.5)
        assert result == 3
        for clip in clips:
            clip.set_opacity.assert_called_once_with(0.5)


class TestFadeAll:
    def test_applies_fade(self):
        clips = [_make_clip() for _ in range(2)]
        result = fade_all(clips, fade_in=0.3, fade_out=0.7)
        assert result == 2
        for clip in clips:
            clip.fade.assert_called_once_with(0.3, 0.7)


class TestScaleAll:
    def test_sets_scale(self):
        clips = [_make_clip() for _ in range(2)]
        result = scale_all(clips, 1.5)
        assert result == 2
        for clip in clips:
            clip.scale_to.assert_called_once_with(1.5)


class TestMoveAll:
    def test_offsets_clips(self):
        clips = [_make_clip(10.0, 20.0), _make_clip(5.0, 15.0)]
        result = move_all(clips, dx=3.0, dy=-2.0)
        assert result == 2
        clips[0].move_to.assert_called_once_with(13.0, 18.0)
        clips[1].move_to.assert_called_once_with(8.0, 13.0)


class TestEmpty:
    def test_apply_to_empty(self):
        assert apply_to_clips([], MagicMock()) == 0
