"""Tests for fade_in/fade_out animation collision fix.

When fade_in() and fade_out() are called sequentially, they must produce
a single unified opacity animation (3 visual segments: fade-in, hold,
fade-out) instead of two separate tracks that Camtasia rejects.
"""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timing import EDIT_RATE, seconds_to_ticks
from camtasia.timeline.clips.image import IMFile


def _clip_data(
    *,
    duration: int = EDIT_RATE * 5,
    media_duration: int | None = None,
) -> dict[str, Any]:
    return {
        "_type": "IMFile",
        "id": 1,
        "start": 0,
        "duration": duration,
        "mediaStart": 0,
        "mediaDuration": media_duration if media_duration is not None else duration,
        "scalar": 1,
        "src": 100,
        "metadata": {},
        "animationTracks": {},
        "parameters": {},
        "effects": [],
    }


class TestFadeInThenFadeOut:
    """fade_in() followed by fade_out() must produce a single visual track."""

    @pytest.mark.parametrize(
        "fade_in_secs, fade_out_secs",
        [
            (0.5, 0.5),
            (1.0, 2.0),
            (0.25, 0.75),
        ],
        ids=["equal", "asymmetric", "short-in-long-out"],
    )
    def test_creates_single_visual_track_with_three_segments(
        self, fade_in_secs: float, fade_out_secs: float
    ):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_in(fade_in_secs)
        clip.fade_out(fade_out_secs)

        actual_segments = clip._data["animationTracks"]["visual"]
        fade_in_ticks = seconds_to_ticks(fade_in_secs)
        fade_out_ticks = seconds_to_ticks(fade_out_secs)

        expected_segments = [
            {"endTime": fade_in_ticks, "duration": fade_in_ticks},
            {"endTime": dur - fade_out_ticks, "duration": dur - fade_out_ticks - fade_in_ticks},
            {"endTime": dur, "duration": fade_out_ticks},
        ]
        assert actual_segments == expected_segments

    def test_keyframes_span_full_animation(self):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_in(0.5)
        clip.fade_out(0.5)

        actual_keyframes = clip._data["parameters"]["opacity"]["keyframes"]
        assert actual_keyframes[0]["value"] == 0.0
        assert actual_keyframes[1]["value"] == 1.0
        assert actual_keyframes[-2]["value"] == 1.0
        assert actual_keyframes[-1]["value"] == 0.0


class TestFadeOutThenFadeIn:
    """fade_out() followed by fade_in() must also produce a single visual track."""

    @pytest.mark.parametrize(
        "fade_in_secs, fade_out_secs",
        [
            (0.5, 0.5),
            (1.0, 2.0),
            (0.25, 0.75),
        ],
        ids=["equal", "asymmetric", "short-in-long-out"],
    )
    def test_creates_single_visual_track_with_three_segments(
        self, fade_in_secs: float, fade_out_secs: float
    ):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_out(fade_out_secs)
        clip.fade_in(fade_in_secs)

        actual_segments = clip._data["animationTracks"]["visual"]
        fade_in_ticks = seconds_to_ticks(fade_in_secs)
        fade_out_ticks = seconds_to_ticks(fade_out_secs)

        expected_segments = [
            {"endTime": fade_in_ticks, "duration": fade_in_ticks},
            {"endTime": dur - fade_out_ticks, "duration": dur - fade_out_ticks - fade_in_ticks},
            {"endTime": dur, "duration": fade_out_ticks},
        ]
        assert actual_segments == expected_segments

    def test_keyframes_span_full_animation(self):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_out(0.5)
        clip.fade_in(0.5)

        actual_keyframes = clip._data["parameters"]["opacity"]["keyframes"]
        assert actual_keyframes[0]["value"] == 0.0
        assert actual_keyframes[1]["value"] == 1.0
        assert actual_keyframes[-2]["value"] == 1.0
        assert actual_keyframes[-1]["value"] == 0.0


class TestFadeInOnly:
    """fade_in() alone must still produce a single segment."""

    @pytest.mark.parametrize("fade_secs", [0.25, 0.5, 1.0], ids=["quarter", "half", "one"])
    def test_creates_single_segment(self, fade_secs: float):
        clip = IMFile(_clip_data())
        clip.fade_in(fade_secs)

        actual_segments = clip._data["animationTracks"]["visual"]
        expected_ticks = seconds_to_ticks(fade_secs)
        expected_segments = [{"endTime": expected_ticks, "duration": expected_ticks}]
        assert actual_segments == expected_segments

    def test_keyframes_zero_to_one(self):
        clip = IMFile(_clip_data())
        clip.fade_in(0.5)

        actual_keyframes = clip._data["parameters"]["opacity"]["keyframes"]
        assert actual_keyframes[0]["value"] == 0.0
        assert actual_keyframes[-1]["value"] == 1.0


class TestFadeOutOnly:
    """fade_out() alone must still produce a single segment."""

    @pytest.mark.parametrize("fade_secs", [0.25, 0.5, 1.0], ids=["quarter", "half", "one"])
    def test_creates_single_segment(self, fade_secs: float):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_out(fade_secs)

        actual_segments = clip._data["animationTracks"]["visual"]
        expected_ticks = seconds_to_ticks(fade_secs)
        expected_segments = [{"endTime": dur, "duration": expected_ticks}]
        assert actual_segments == expected_segments

    def test_keyframes_one_to_zero(self):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_out(0.5)

        actual_keyframes = clip._data["parameters"]["opacity"]["keyframes"]
        assert actual_keyframes[0]["value"] == 1.0
        assert actual_keyframes[-1]["value"] == 0.0


class TestFadeMethodRegression:
    """The existing fade() method must continue to work correctly."""

    @pytest.mark.parametrize(
        "fade_in_secs, fade_out_secs",
        [
            (0.5, 0.5),
            (1.0, 0.0),
            (0.0, 1.0),
            (1.0, 2.0),
        ],
        ids=["both-equal", "in-only", "out-only", "asymmetric"],
    )
    def test_fade_produces_correct_visual_segments(
        self, fade_in_secs: float, fade_out_secs: float
    ):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade(fade_in_seconds=fade_in_secs, fade_out_seconds=fade_out_secs)

        actual_segments = clip._data["animationTracks"]["visual"]

        if fade_in_secs > 0 and fade_out_secs > 0:
            fade_in_ticks = seconds_to_ticks(fade_in_secs)
            fade_out_ticks = seconds_to_ticks(fade_out_secs)
            expected_segments = [
                {"endTime": fade_in_ticks, "duration": fade_in_ticks},
                {"endTime": dur - fade_out_ticks, "duration": dur - fade_out_ticks - fade_in_ticks},
                {"endTime": dur, "duration": fade_out_ticks},
            ]
            assert actual_segments == expected_segments
        elif fade_in_secs > 0:
            expected_ticks = seconds_to_ticks(fade_in_secs)
            expected_segments = [{"endTime": expected_ticks, "duration": expected_ticks}]
            assert actual_segments == expected_segments
        elif fade_out_secs > 0:
            expected_ticks = seconds_to_ticks(fade_out_secs)
            expected_segments = [{"endTime": dur, "duration": expected_ticks}]
            assert actual_segments == expected_segments

    def test_fade_replaces_prior_animations(self):
        dur = EDIT_RATE * 5
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_in(0.5)
        clip.fade_out(0.5)
        clip.fade(fade_in_seconds=1.0, fade_out_seconds=1.0)

        actual_segments = clip._data["animationTracks"]["visual"]
        fade_ticks = seconds_to_ticks(1.0)
        expected_segments = [
            {"endTime": fade_ticks, "duration": fade_ticks},
            {"endTime": dur - fade_ticks, "duration": dur - fade_ticks - fade_ticks},
            {"endTime": dur, "duration": fade_ticks},
        ]
        assert actual_segments == expected_segments
