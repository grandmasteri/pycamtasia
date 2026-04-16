"""Comprehensive tests for the pycamtasia L2 convenience API."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timing import EDIT_RATE, seconds_to_ticks, ticks_to_seconds
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.clips.image import IMFile
from camtasia.timeline.clips.callout import Callout
from camtasia.timeline.clips import clip_from_dict, AMFile
from camtasia.timeline.track import Track
from camtasia.timeline.timeline import Timeline
from camtasia.effects.base import Effect
from camtasia.effects.visual import DropShadow, Glow, RoundCorners
from camtasia.effects.behaviors import GenericBehaviorEffect


# ---------------------------------------------------------------------------
# Helpers — minimal data builders
# ---------------------------------------------------------------------------

def _clip_data(
    *,
    clip_type: str = "IMFile",
    clip_id: int = 1,
    start: int = 0,
    duration: int = EDIT_RATE * 5,
    media_start: int = 0,
    media_duration: int | None = None,
    src: int = 100,
) -> dict[str, Any]:
    """Build a minimal clip dict."""
    return {
        "_type": clip_type,
        "id": clip_id,
        "start": start,
        "duration": duration,
        "mediaStart": media_start,
        "mediaDuration": media_duration if media_duration is not None else duration,
        "scalar": 1,
        "src": src,
        "metadata": {},
        "animationTracks": {},
        "parameters": {},
        "effects": [],
    }


def _callout_data(
    *,
    clip_id: int = 1,
    duration: int = EDIT_RATE * 5,
    text: str = "Hello",
) -> dict[str, Any]:
    """Build a minimal Callout clip dict."""
    data = _clip_data(clip_type="Callout", clip_id=clip_id, duration=duration)
    data.pop("src")
    data["def"] = {
        "kind": "remix",
        "shape": "text",
        "style": "basic",
        "text": text,
        "height": 250.0,
        "width": 400.0,
        "font": {"name": "Arial", "weight": "Normal", "size": 96.0},
    }
    return data


def _track_data(index: int = 0) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (attributes, track_data) for a Track."""
    attrs = {"ident": f"Track {index}", "audioMuted": False, "videoHidden": False,
             "magnetic": False, "metadata": {"IsLocked": "False"}}
    data = {"trackIndex": index, "medias": [], "transitions": []}
    return attrs, data


def _timeline_data(num_tracks: int = 1) -> dict[str, Any]:
    """Build a minimal timeline dict."""
    tracks = []
    attrs = []
    for i in range(num_tracks):
        a, d = _track_data(i)
        tracks.append(d)
        attrs.append(a)
    return {
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": attrs,
        "parameters": {},
    }


# ===================================================================
# Clip-level animation tests
# ===================================================================


class TestFadeIn:

    def test_creates_opacity_keyframes_zero_to_one(self):
        clip = IMFile(_clip_data(duration=EDIT_RATE * 10))
        clip.fade_in(1.0)
        actual_opacity = clip._data["parameters"]["opacity"]
        assert actual_opacity["type"] == "double"
        actual_kfs = actual_opacity["keyframes"]
        assert [kf["value"] for kf in actual_kfs] == [1.0]
        actual_visual = clip._data["animationTracks"]["visual"]
        assert [v["duration"] > 0 for v in actual_visual] == [True]

    def test_returns_self_for_chaining(self):
        clip = IMFile(_clip_data())
        assert clip.fade_in(0.5) is clip


class TestFadeOut:
    def test_creates_opacity_keyframes_one_to_zero_at_end(self):
        dur = EDIT_RATE * 10
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade_out(2.0)
        actual_kfs = clip._data["parameters"]["opacity"]["keyframes"]
        assert [kf["value"] for kf in actual_kfs] == [0.0]

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.fade_out(0.5) is clip


class TestFade:
    def test_both_fade_in_and_out(self):
        dur = EDIT_RATE * 10
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade(fade_in_seconds=1.0, fade_out_seconds=1.0)
        actual_kfs = clip._data["parameters"]["opacity"]["keyframes"]
        assert [kf["value"] for kf in actual_kfs] == [1.0, 0.0]
        # v10: 2 visual segments — fade-in, fade-out
        visual = clip._data["animationTracks"]["visual"]
        fade_in_ticks = seconds_to_ticks(1.0)
        fade_out_ticks = seconds_to_ticks(1.0)
        assert visual == [
            {"endTime": fade_in_ticks, "duration": fade_in_ticks},
            {"endTime": dur, "duration": fade_out_ticks},
        ]

    def test_replaces_existing_opacity_animations(self):
        clip = IMFile(_clip_data(duration=EDIT_RATE * 10, media_duration=EDIT_RATE * 10))
        clip.fade_in(0.5)
        clip.fade(fade_in_seconds=1.0)
        actual_kfs = clip._data["parameters"]["opacity"]["keyframes"]
        assert [kf["value"] for kf in actual_kfs] == [1.0]

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.fade(fade_in_seconds=0.5) is clip


class TestSetOpacity:
    @pytest.mark.parametrize("opacity", [0.0, 0.5, 1.0])
    def test_sets_plain_scalar(self, project, opacity):
        track = project.timeline.add_track("T")
        clip = track.add_clip("VMFile", 1, 0, 705600000)
        clip.set_opacity(opacity)
        assert clip._data["parameters"]["opacity"] == opacity

    def test_returns_self(self, project):
        track = project.timeline.add_track("T")
        clip = track.add_clip("VMFile", 1, 0, 705600000)
        assert clip.set_opacity(0.5) is clip

class TestClearAnimations:
    def test_empties_visual_animations(self):
        clip = IMFile(_clip_data())
        clip.fade_in(1.0)
        clip.clear_animations()
        assert clip._data["animationTracks"]["visual"] == []

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.clear_animations() is clip


# ===================================================================
# Clip-level animation tests


# ===================================================================
# Clip metadata defaults
# ===================================================================


class TestClipMetadataDefaults:
    """Tests for default metadata fields set by add_clip() and add_image()."""

    @pytest.fixture()
    def track(self) -> Track:
        attrs, data = _track_data()
        return Track(attrs, data)

    def test_add_clip_has_default_metadata_fields(self, track: Track):
        clip = track.add_clip('IMFile', 1, 0, EDIT_RATE * 5)
        meta = clip.metadata
        assert meta['audiateLinkedSession'] == ''
        assert meta['clipSpeedAttribute'] == {'type': 'bool', 'value': False}
        assert meta['colorAttribute'] == {'type': 'color', 'value': [0, 0, 0, 0]}
        assert meta['effectApplied'] == 'none'

    def test_custom_metadata_merges_and_overrides_defaults(self, track: Track):
        clip = track.add_clip(
            'IMFile', 1, 0, EDIT_RATE * 5,
            metadata={'effectApplied': 'blur', 'custom_key': 42},
        )
        meta = clip.metadata
        # overridden
        assert meta['effectApplied'] == 'blur'
        # custom addition
        assert meta['custom_key'] == 42
        # defaults still present
        assert meta['audiateLinkedSession'] == ''
        assert meta['clipSpeedAttribute'] == {'type': 'bool', 'value': False}

    def test_add_image_includes_trimStartSum(self, track: Track):
        clip = track.add_image(1, 0.0, 5.0)
        assert clip._data['trimStartSum'] == 0
