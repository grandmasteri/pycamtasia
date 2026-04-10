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

        actual_visual = clip.visual_animations
        actual_track = actual_visual[0]
        assert actual_track["track"] == "opacity"
        expected_keyframes = [
            {"time": 0, "value": "0", "interp": "linr"},
            {"time": seconds_to_ticks(1.0), "value": "1", "interp": "linr"},
        ]
        assert actual_track["keyframes"] == expected_keyframes

    def test_returns_self_for_chaining(self):
        clip = IMFile(_clip_data())
        actual_result = clip.fade_in(0.5)
        assert actual_result is clip


class TestFadeOut:
    def test_creates_opacity_keyframes_one_to_zero_at_end(self):
        clip_duration = EDIT_RATE * 10
        clip = IMFile(_clip_data(duration=clip_duration, media_duration=clip_duration))
        clip.fade_out(2.0)

        actual_track = clip.visual_animations[0]
        assert actual_track["track"] == "opacity"
        expected_keyframes = [
            {"time": clip_duration - seconds_to_ticks(2.0), "value": "1", "interp": "linr"},
            {"time": clip_duration, "value": "0", "interp": "linr"},
        ]
        assert actual_track["keyframes"] == expected_keyframes

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.fade_out(0.5) is clip


class TestFade:
    def test_both_fade_in_and_out(self):
        dur = EDIT_RATE * 10
        clip = IMFile(_clip_data(duration=dur, media_duration=dur))
        clip.fade(fade_in_seconds=1.0, fade_out_seconds=1.0)

        actual_track = clip.visual_animations[0]
        actual_kf = actual_track["keyframes"]
        # First keyframe: opacity 0 at time 0
        assert actual_kf[0] == {"time": 0, "value": "0", "interp": "linr"}
        # Second: opacity 1 at fade-in end
        assert actual_kf[1] == {"time": seconds_to_ticks(1.0), "value": "1", "interp": "linr"}
        # Hold at 1 until fade-out start
        assert actual_kf[2] == {"time": dur - seconds_to_ticks(1.0), "value": "1", "interp": "linr"}
        # Final: opacity 0 at clip end
        assert actual_kf[3] == {"time": dur, "value": "0", "interp": "linr"}

    def test_replaces_existing_opacity_animations(self):
        clip = IMFile(_clip_data(duration=EDIT_RATE * 10, media_duration=EDIT_RATE * 10))
        clip.fade_in(0.5)
        clip.fade(fade_in_seconds=1.0)

        actual_opacity_tracks = [
            t for t in clip.visual_animations if t["track"] == "opacity"
        ]
        # fade() should have removed the old one and added a new one
        assert actual_opacity_tracks == [clip.visual_animations[0]]

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.fade(fade_in_seconds=0.5) is clip


class TestSetOpacity:
    @pytest.mark.parametrize("opacity_value", [0.0, 0.5, 1.0])
    def test_single_keyframe_at_given_value(self, opacity_value: float):
        clip = IMFile(_clip_data())
        clip.set_opacity(opacity_value)

        actual_track = clip.visual_animations[0]
        assert actual_track["track"] == "opacity"
        expected_keyframes = [
            {"time": 0, "value": str(opacity_value), "interp": "linr"},
        ]
        assert actual_track["keyframes"] == expected_keyframes

    def test_clears_previous_opacity(self):
        clip = IMFile(_clip_data())
        clip.fade_in(1.0)
        clip.set_opacity(0.7)

        actual_opacity_tracks = [
            t for t in clip.visual_animations if t["track"] == "opacity"
        ]
        # Only the set_opacity track should remain
        assert actual_opacity_tracks[0]["keyframes"] == [
            {"time": 0, "value": "0.7", "interp": "linr"},
        ]

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.set_opacity(0.5) is clip


class TestClearAnimations:
    def test_empties_visual_animations(self):
        clip = IMFile(_clip_data())
        clip.fade_in(1.0)
        clip.clear_animations()
        assert clip.visual_animations == []

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.clear_animations() is clip


# ===================================================================
# Effect tests
# ===================================================================


class TestAddDropShadow:
    def test_correct_effect_structure(self):
        clip = IMFile(_clip_data())
        actual_effect = clip.add_drop_shadow(offset=15.0, blur=25.0, opacity=0.2, angle=315.0, color=(0, 0, 0))

        assert isinstance(actual_effect, DropShadow)
        assert actual_effect.name == "DropShadow"
        assert actual_effect.get_parameter("offset") == 15.0
        assert actual_effect.get_parameter("blur") == 25.0
        assert actual_effect.get_parameter("opacity") == 0.2
        assert actual_effect.get_parameter("angle") == 315.0
        assert actual_effect.get_parameter("color-red") == 0
        assert actual_effect.get_parameter("color-green") == 0
        assert actual_effect.get_parameter("color-blue") == 0

    def test_appended_to_effects_list(self):
        clip = IMFile(_clip_data())
        clip.add_drop_shadow()
        assert clip.effects[0]["effectName"] == "DropShadow"


class TestAddGlow:
    def test_correct_effect_structure(self):
        clip = IMFile(_clip_data())
        actual_effect = clip.add_glow(radius=20.0, intensity=0.8)

        assert isinstance(actual_effect, Glow)
        assert actual_effect.name == "Glow"
        assert actual_effect.get_parameter("radius") == 20.0
        assert actual_effect.get_parameter("intensity") == 0.8


class TestAddRoundCorners:
    def test_correct_effect_structure(self):
        clip = IMFile(_clip_data())
        actual_effect = clip.add_round_corners(radius=16.0)

        assert isinstance(actual_effect, RoundCorners)
        assert actual_effect.name == "RoundCorners"
        assert actual_effect.get_parameter("radius") == 16.0
        assert actual_effect.get_parameter("top-left") == 1.0
        assert actual_effect.get_parameter("top-right") == 1.0
        assert actual_effect.get_parameter("bottom-left") == 1.0
        assert actual_effect.get_parameter("bottom-right") == 1.0


class TestRemoveEffects:
    def test_clears_all_effects(self):
        clip = IMFile(_clip_data())
        clip.add_glow()
        clip.add_drop_shadow()
        clip.remove_effects()
        assert clip.effects == []

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.remove_effects() is clip


class TestMethodChaining:
    def test_chain_multiple_operations(self):
        clip = IMFile(_clip_data(duration=EDIT_RATE * 10, media_duration=EDIT_RATE * 10))
        actual_result = (
            clip
            .fade_in(0.5)
            .fade_out(0.5)
            .set_opacity(0.8)
            .clear_animations()
        )
        assert actual_result is clip
        assert clip.visual_animations == []


# ===================================================================
# IMFile transform tests
# ===================================================================


class TestMoveTo:
    def test_sets_translation_parameters(self):
        clip = IMFile(_clip_data())
        clip.move_to(100.0, -50.0)

        assert clip.translation == (100.0, -50.0)

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.move_to(0, 0) is clip


class TestScaleTo:
    def test_sets_uniform_scale(self):
        clip = IMFile(_clip_data())
        clip.scale_to(0.5)

        assert clip.scale == (0.5, 0.5)

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.scale_to(1.0) is clip


class TestScaleToXY:
    def test_sets_nonuniform_scale(self):
        clip = IMFile(_clip_data())
        clip.scale_to_xy(2.0, 0.5)

        assert clip.scale == (2.0, 0.5)


class TestCrop:
    def test_sets_geometry_crop_values(self):
        clip = IMFile(_clip_data())
        clip.crop(left=0.1, top=0.2, right=0.3, bottom=0.4)

        actual_params = clip.parameters
        assert actual_params["geometryCrop0"]["defaultValue"] == 0.1
        assert actual_params["geometryCrop1"]["defaultValue"] == 0.2
        assert actual_params["geometryCrop2"]["defaultValue"] == 0.3
        assert actual_params["geometryCrop3"]["defaultValue"] == 0.4

    def test_returns_self(self):
        clip = IMFile(_clip_data())
        assert clip.crop(left=0.1) is clip


# ===================================================================
# Track-level tests
# ===================================================================


class TestTrackAddImage:
    def test_creates_imfile_clip(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        actual_clip = track.add_image(source_id=42, start_seconds=1.0, duration_seconds=5.0)

        assert isinstance(actual_clip, IMFile)
        assert actual_clip.clip_type == "IMFile"
        assert actual_clip.source_id == 42
        assert actual_clip.start == seconds_to_ticks(1.0)
        assert actual_clip.duration == seconds_to_ticks(5.0)


class TestTrackAddAudio:
    def test_creates_amfile_clip(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        actual_clip = track.add_audio(source_id=10, start_seconds=0.0, duration_seconds=30.0)

        assert isinstance(actual_clip, AMFile)
        assert actual_clip.clip_type == "AMFile"
        assert actual_clip.source_id == 10
        assert actual_clip.start == 0
        assert actual_clip.duration == seconds_to_ticks(30.0)


class TestTrackAddCallout:
    def test_creates_callout_with_text_and_font(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        actual_clip = track.add_callout(
            "Hello World",
            start_seconds=2.0,
            duration_seconds=3.0,
            font_name="Helvetica",
            font_weight="Bold",
            font_size=128.0,
        )

        assert isinstance(actual_clip, Callout)
        assert actual_clip.text == "Hello World"
        assert actual_clip.font["name"] == "Helvetica"
        assert actual_clip.font["weight"] == "Bold"
        assert actual_clip.font["size"] == 128.0
        assert actual_clip.start == seconds_to_ticks(2.0)
        assert actual_clip.duration == seconds_to_ticks(3.0)


class TestTrackAddFadeThroughBlack:
    def test_creates_transition_between_clips(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        clip_a = track.add_image(source_id=1, start_seconds=0.0, duration_seconds=5.0)
        clip_b = track.add_image(source_id=2, start_seconds=5.0, duration_seconds=5.0)

        actual_transition = track.add_fade_through_black(clip_a, clip_b, duration_seconds=0.5)

        assert actual_transition.name == "FadeThroughBlack"
        assert actual_transition.left_media_id == clip_a.id
        assert actual_transition.right_media_id == clip_b.id
        assert actual_transition.duration == seconds_to_ticks(0.5)


class TestTrackAddImageSequence:
    def test_creates_multiple_images_back_to_back(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        actual_clips = track.add_image_sequence(
            source_ids=[10, 20, 30],
            start_seconds=0.0,
            duration_per_image_seconds=5.0,
        )

        assert [c.source_id for c in actual_clips] == [10, 20, 30]
        assert actual_clips[0].start == 0
        assert actual_clips[1].start == seconds_to_ticks(5.0)
        assert actual_clips[2].start == seconds_to_ticks(10.0)

    def test_adds_transitions_when_requested(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        actual_clips = track.add_image_sequence(
            source_ids=[10, 20, 30],
            start_seconds=0.0,
            duration_per_image_seconds=5.0,
            transition_seconds=0.5,
        )

        actual_transitions = list(track.transitions)
        assert actual_transitions[0].left_media_id == actual_clips[0].id
        assert actual_transitions[0].right_media_id == actual_clips[1].id
        assert actual_transitions[1].left_media_id == actual_clips[1].id
        assert actual_transitions[1].right_media_id == actual_clips[2].id

    def test_no_transitions_when_zero_seconds(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        track.add_image_sequence(
            source_ids=[10, 20],
            start_seconds=0.0,
            duration_per_image_seconds=5.0,
            transition_seconds=0.0,
        )
        assert list(track.transitions) == []


class TestTrackEndTimeSeconds:
    def test_returns_end_of_last_clip(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        track.add_image(source_id=1, start_seconds=0.0, duration_seconds=5.0)
        track.add_image(source_id=2, start_seconds=5.0, duration_seconds=10.0)

        actual_end = track.end_time_seconds()
        assert actual_end == pytest.approx(15.0)

    def test_empty_track_returns_zero(self):
        attrs, data = _track_data()
        track = Track(attrs, data)
        assert track.end_time_seconds() == 0.0


# ===================================================================
# Timeline-level tests
# ===================================================================


class TestTimelineTotalDuration:
    def test_seconds_from_clips(self):
        tl_data = _timeline_data(num_tracks=1)
        tl = Timeline(tl_data)
        track = list(tl.tracks)[0]
        track.add_image(source_id=1, start_seconds=0.0, duration_seconds=10.0)
        track.add_image(source_id=2, start_seconds=10.0, duration_seconds=5.0)

        assert tl.total_duration_seconds() == pytest.approx(15.0)

    def test_ticks_from_clips(self):
        tl_data = _timeline_data(num_tracks=1)
        tl = Timeline(tl_data)
        track = list(tl.tracks)[0]
        track.add_image(source_id=1, start_seconds=0.0, duration_seconds=10.0)

        assert tl.total_duration_ticks() == seconds_to_ticks(10.0)

    def test_empty_timeline_returns_zero(self):
        tl = Timeline(_timeline_data(num_tracks=1))
        assert tl.total_duration_seconds() == 0.0
        assert tl.total_duration_ticks() == 0


class TestGetOrCreateTrack:
    def test_creates_new_track_when_not_found(self):
        tl = Timeline(_timeline_data(num_tracks=0))
        actual_track = tl.get_or_create_track("Slides")

        assert actual_track.name == "Slides"
        assert tl.track_count == 1

    def test_returns_existing_track(self):
        tl_data = _timeline_data(num_tracks=1)
        tl_data["trackAttributes"][0]["ident"] = "Audio"
        tl = Timeline(tl_data)

        actual_track = tl.get_or_create_track("Audio")
        assert actual_track.name == "Audio"
        assert tl.track_count == 1  # no new track created

    def test_does_not_duplicate(self):
        tl = Timeline(_timeline_data(num_tracks=0))
        tl.get_or_create_track("MyTrack")
        tl.get_or_create_track("MyTrack")
        assert tl.track_count == 1


class TestAllClips:
    def test_returns_flat_list_across_tracks(self):
        tl_data = _timeline_data(num_tracks=2)
        tl = Timeline(tl_data)
        tracks = list(tl.tracks)
        tracks[0].add_image(source_id=1, start_seconds=0.0, duration_seconds=5.0)
        tracks[1].add_image(source_id=2, start_seconds=0.0, duration_seconds=3.0)

        actual_clips = tl.all_clips()
        assert [c.source_id for c in actual_clips] == [1, 2]

    def test_empty_timeline(self):
        tl = Timeline(_timeline_data(num_tracks=1))
        assert tl.all_clips() == []


class TestAddMarker:
    def test_creates_marker_at_correct_time(self):
        tl = Timeline(_timeline_data())
        actual_marker = tl.add_marker("Chapter 1", time_seconds=5.0)

        assert actual_marker.name == "Chapter 1"
        assert actual_marker.time == seconds_to_ticks(5.0)


# ===================================================================
# Project-level tests
# ===================================================================


class TestProjectImportMedia:
    """Tests for Project.import_media type detection.

    These require a real project on disk, so we use the conftest fixture.
    """

    @pytest.mark.parametrize(
        "suffix, expected_type_name",
        [
            (".png", "Image"),
            (".wav", "Audio"),
            (".mp4", "Video"),
            (".jpg", "Image"),
            (".m4a", "Audio"),
            (".mov", "Video"),
        ],
    )
    def test_extension_type_mapping(self, suffix, expected_type_name, tmp_path, project):
        """Verify import_media detects the correct MediaType from extension."""
        test_file = tmp_path / f"test_file{suffix}"
        test_file.write_bytes(b"\x00" * 16)

        actual_media = project.import_media(test_file)
        from camtasia.media_bin import MediaType
        expected_type = MediaType[expected_type_name]
        assert actual_media.type == expected_type

    def test_unknown_extension_raises(self, tmp_path, project):
        test_file = tmp_path / "test_file.xyz"
        test_file.write_bytes(b"\x00")
        with pytest.raises(ValueError, match="Cannot determine media type"):
            project.import_media(test_file)


class TestProjectFindMedia:
    def test_find_by_name_returns_match(self, tmp_path, project):
        test_file = tmp_path / "my_image.png"
        test_file.write_bytes(b"\x00" * 16)
        project.import_media(test_file)

        actual_media = project.find_media_by_name("my_image")
        assert actual_media is not None
        assert actual_media.identity == "my_image"

    def test_find_by_name_returns_none_when_missing(self, project):
        assert project.find_media_by_name("nonexistent") is None

    def test_find_by_suffix(self, tmp_path, project):
        png_file = tmp_path / "slide.png"
        png_file.write_bytes(b"\x00" * 16)
        wav_file = tmp_path / "audio.wav"
        wav_file.write_bytes(b"\x00" * 16)
        project.import_media(png_file)
        project.import_media(wav_file)

        actual_pngs = project.find_media_by_suffix(".png")
        actual_names = [m.identity for m in actual_pngs]
        assert "slide" in actual_names

        actual_wavs = project.find_media_by_suffix(".wav")
        actual_wav_names = [m.identity for m in actual_wavs]
        assert "audio" in actual_wav_names


class TestProjectTotalDuration:
    def test_delegates_to_timeline(self, project):
        # Empty project should have zero duration
        assert project.total_duration_seconds() == 0.0


# ===================================================================
# Advanced tests
# ===================================================================


class TestAddGlowTimed:
    def test_time_bounded_glow_with_edge_mods(self):
        clip = IMFile(_clip_data(duration=EDIT_RATE * 20))
        actual_effect = clip.add_glow_timed(
            start_seconds=2.0,
            duration_seconds=5.0,
            radius=35.0,
            intensity=0.35,
            fade_in_seconds=0.4,
            fade_out_seconds=1.0,
        )

        assert isinstance(actual_effect, Glow)
        assert actual_effect.name == "Glow"
        assert actual_effect.start == seconds_to_ticks(2.0)
        assert actual_effect.duration == seconds_to_ticks(5.0)
        assert actual_effect.get_parameter("radius") == 35.0
        assert actual_effect.get_parameter("intensity") == 0.35

        expected_left = [{"type": "fadeIn", "duration": seconds_to_ticks(0.4)}]
        expected_right = [{"type": "fadeOut", "duration": seconds_to_ticks(1.0)}]
        assert actual_effect.left_edge_mods == expected_left
        assert actual_effect.right_edge_mods == expected_right


class TestCalloutSetFont:
    def test_updates_font_properties(self):
        callout = Callout(_callout_data())
        actual_result = callout.set_font("Helvetica", "Bold", 128.0)

        assert actual_result is callout
        assert callout.font["name"] == "Helvetica"
        assert callout.font["weight"] == "Bold"
        assert callout.font["size"] == 128.0


class TestCalloutSetColors:
    def test_sets_fill_color(self):
        callout = Callout(_callout_data())
        callout.set_colors(fill=(1.0, 0.0, 0.0, 0.5))

        assert callout.fill_color == (1.0, 0.0, 0.0, 0.5)

    def test_sets_stroke_color(self):
        callout = Callout(_callout_data())
        callout.set_colors(stroke=(0.0, 1.0, 0.0, 1.0))

        assert callout.stroke_color == (0.0, 1.0, 0.0, 1.0)

    def test_sets_font_color(self):
        callout = Callout(_callout_data())
        callout.set_colors(font_color=(0.5, 0.5, 0.5))

        assert callout.font["color-red"] == 0.5
        assert callout.font["color-green"] == 0.5
        assert callout.font["color-blue"] == 0.5

    def test_returns_self(self):
        callout = Callout(_callout_data())
        assert callout.set_colors(fill=(1, 1, 1, 1)) is callout


class TestCalloutResize:
    def test_sets_dimensions(self):
        callout = Callout(_callout_data())
        actual_result = callout.resize(800.0, 600.0)

        assert actual_result is callout
        assert callout.width == 800.0
        assert callout.height == 600.0


class TestCalloutAddBehavior:
    def test_creates_generic_behavior_effect(self):
        callout = Callout(_callout_data(duration=EDIT_RATE * 5))
        actual_effect = callout.add_behavior(
            preset="Reveal",
            entrance_name="reveal",
            exit_name="none",
        )

        assert isinstance(actual_effect, GenericBehaviorEffect)
        assert actual_effect.effect_name == "GenericBehaviorEffect"
        assert actual_effect.preset_name == "Reveal"
        assert actual_effect.entrance.name == "reveal"
        assert actual_effect.exit.name == "none"
        assert actual_effect.center.name == "none"
        assert actual_effect.duration == EDIT_RATE * 5

    def test_appended_to_effects_list(self):
        callout = Callout(_callout_data())
        callout.add_behavior()
        assert callout.effects[0]["_type"] == "GenericBehaviorEffect"

    def test_entrance_attributes_structure(self):
        callout = Callout(_callout_data())
        actual_effect = callout.add_behavior(entrance_name="reveal")

        actual_in_attrs = actual_effect.entrance
        assert actual_in_attrs.character_order == 0
        assert actual_in_attrs.offset_between_characters == 17640000
        assert actual_in_attrs.suggested_duration_per_character == 35280000
        assert actual_in_attrs.overlap_proportion == "1/2"
