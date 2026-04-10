"""Tests to increase coverage for timeline clip modules.

Covers missing lines in:
- callout.py (setters, colors, behavior, convenience methods)
- image.py (setters, helpers, crop, geometry)
- screen_recording.py (transforms, cursor effects, ScreenIMFile)
- audio.py (channel_number setter, loudness_normalization setter)
- group.py (GroupTrack repr, parameters)
- base.py (gain, mute, metadata, animations, effects helpers, repr, fade, opacity)
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from camtasia.timeline.clips import EDIT_RATE
from camtasia.timeline.clips.audio import AMFile
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.clips.callout import Callout
from camtasia.timeline.clips.group import Group, GroupTrack
from camtasia.timeline.clips.image import IMFile
from camtasia.timeline.clips.screen_recording import ScreenIMFile, ScreenVMFile


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _base(**kw) -> dict:
    d = {
        "id": 1, "_type": "AMFile", "src": 1,
        "start": 0, "duration": EDIT_RATE * 10,
        "mediaStart": 0, "mediaDuration": EDIT_RATE * 10, "scalar": 1,
    }
    d.update(kw)
    return d


# ==================================================================
# Callout — missing: setters, fill/stroke color, set_font, set_colors,
#   resize, add_behavior, tail_position, corner_radius, horizontal_alignment
# ==================================================================

class TestCalloutSetters:
    def test_text_setter_creates_def_if_absent(self):
        data = _base(_type="Callout")
        clip = Callout(data)
        clip.text = "new"
        assert data["def"]["text"] == "new"

    def test_style_setter(self):
        data = _base(_type="Callout", **{"def": {"style": "basic"}})
        clip = Callout(data)
        clip.style = "fancy"
        assert data["def"]["style"] == "fancy"

    def test_width_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.width = 500.0
        assert data["def"]["width"] == 500.0

    def test_height_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.height = 300.0
        assert data["def"]["height"] == 300.0

    def test_horizontal_alignment_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.horizontal_alignment = "left"
        assert data["def"]["horizontal-alignment"] == "left"


class TestCalloutColors:
    def test_fill_color_reads_defaults(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.fill_color == (0.0, 0.0, 0.0, 1.0)

    def test_fill_color_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.fill_color = (0.1, 0.2, 0.3, 0.4)
        assert data["def"]["fill-color-red"] == 0.1
        assert data["def"]["fill-color-opacity"] == 0.4

    def test_stroke_color_reads_defaults(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.stroke_color == (0.0, 0.0, 0.0, 1.0)

    def test_stroke_color_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.stroke_color = (0.5, 0.6, 0.7, 0.8)
        assert data["def"]["stroke-color-blue"] == 0.7

    def test_corner_radius_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.corner_radius == 0.0

    def test_corner_radius_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.corner_radius = 12.0
        assert data["def"]["corner-radius"] == 12.0

    def test_tail_position_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.tail_position == (0.0, 0.0)

    def test_tail_position_setter(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.tail_position = (10.0, 20.0)
        assert data["def"]["tail-x"] == 10.0
        assert data["def"]["tail-y"] == 20.0


class TestCalloutConvenience:
    def test_set_font(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        actual_result = clip.set_font("Arial", "Bold", 48.0)
        assert actual_result is clip
        assert data["def"]["font"]["name"] == "Arial"
        assert data["def"]["font"]["weight"] == "Bold"
        assert data["def"]["font"]["size"] == 48.0

    def test_set_colors_fill_only(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        actual_result = clip.set_colors(fill=(1.0, 0.0, 0.0, 1.0))
        assert actual_result is clip
        assert data["def"]["fill-color-red"] == 1.0

    def test_set_colors_stroke_only(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.set_colors(stroke=(0.0, 1.0, 0.0, 0.5))
        assert data["def"]["stroke-color-green"] == 1.0

    def test_set_colors_font_color(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        clip.set_colors(font_color=(0.1, 0.2, 0.3))
        assert data["def"]["font"]["color-red"] == 0.1
        assert data["def"]["font"]["color-green"] == 0.2
        assert data["def"]["font"]["color-blue"] == 0.3

    def test_resize(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        actual_result = clip.resize(800.0, 600.0)
        assert actual_result is clip
        assert clip.width == 800.0
        assert clip.height == 600.0

    def test_add_behavior(self):
        data = _base(_type="Callout", **{"def": {}})
        clip = Callout(data)
        actual_effect = clip.add_behavior("Reveal", "reveal", "none")
        assert actual_effect is not None
        assert data["effects"][0]["_type"] == "GenericBehaviorEffect"
        assert data["effects"][0]["metadata"]["presetName"] == "Reveal"
        assert data["effects"][0]["out"]["attributes"]["name"] == "none"

    def test_font_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.font == {}

    def test_kind_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.kind == ""

    def test_shape_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.shape == ""

    def test_style_default(self):
        clip = Callout(_base(_type="Callout"))
        assert clip.style == ""


# ==================================================================
# IMFile — missing: _set_param_value (new key), scale setter,
#   geometry_crop, move_to, scale_to, scale_to_xy, crop
# ==================================================================

class TestIMFile:
    def test_set_param_value_creates_new_param(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        clip.translation = (100.0, 200.0)
        assert data["parameters"]["translation0"]["defaultValue"] == 100.0
        assert data["parameters"]["translation0"]["type"] == "double"

    def test_scale_setter(self):
        data = _base(_type="IMFile", parameters={
            "scale0": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
        })
        clip = IMFile(data)
        clip.scale = (2.0, 3.0)
        assert data["parameters"]["scale0"]["defaultValue"] == 2.0
        assert data["parameters"]["scale1"]["defaultValue"] == 3.0

    def test_geometry_crop_with_params(self):
        data = _base(_type="IMFile", parameters={
            "geometryCrop0": {"type": "double", "defaultValue": 0.1, "interp": "eioe"},
            "geometryCrop1": {"type": "double", "defaultValue": 0.2, "interp": "eioe"},
            "geometryCrop2": {"type": "double", "defaultValue": 0.3, "interp": "eioe"},
            "geometryCrop3": {"type": "double", "defaultValue": 0.4, "interp": "eioe"},
        })
        clip = IMFile(data)
        actual_crop = clip.geometry_crop
        assert actual_crop == {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}

    def test_geometry_crop_empty_when_absent(self):
        clip = IMFile(_base(_type="IMFile"))
        assert clip.geometry_crop == {}

    def test_move_to(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.move_to(50.0, 75.0)
        assert actual_result is clip
        assert clip.translation == (50.0, 75.0)

    def test_scale_to(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.scale_to(2.0)
        assert actual_result is clip
        assert clip.scale == (2.0, 2.0)

    def test_scale_to_xy(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.scale_to_xy(1.5, 2.5)
        assert actual_result is clip
        assert clip.scale == (1.5, 2.5)

    def test_crop(self):
        data = _base(_type="IMFile")
        clip = IMFile(data)
        actual_result = clip.crop(left=0.1, top=0.2, right=0.3, bottom=0.4)
        assert actual_result is clip
        actual_crop = clip.geometry_crop
        assert actual_crop == {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}

    def test_get_param_value_raw_numeric(self):
        """When parameter is a plain number, not a dict."""
        data = _base(_type="IMFile", parameters={"translation0": 42.0})
        clip = IMFile(data)
        assert clip.translation == (42.0, 0.0)


# ==================================================================
# ScreenVMFile — missing: translation, scale, cursor setters,
#   cursor_track_level, smooth_cursor, cursor effects
# ==================================================================

class TestScreenVMFile:
    def _make(self, **kw):
        params = {
            "translation0": {"type": "double", "defaultValue": 2.0, "interp": "eioe"},
            "translation1": {"type": "double", "defaultValue": -4.0, "interp": "eioe"},
            "scale0": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
            "cursorScale": {"type": "double", "defaultValue": 5.0, "interp": "linr"},
            "cursorOpacity": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
            "cursorTrackLevel": {"type": "double", "defaultValue": 0.5, "interp": "linr"},
            "smoothCursorAcrossEditDuration": 0,
        }
        params.update(kw)
        return ScreenVMFile(_base(_type="ScreenVMFile", parameters=params))

    def test_translation(self):
        clip = self._make()
        assert clip.translation == (2.0, -4.0)

    def test_translation_setter(self):
        data = _base(_type="ScreenVMFile", parameters={})
        clip = ScreenVMFile(data)
        clip.translation = (10.0, 20.0)
        assert data["parameters"]["translation0"]["defaultValue"] == 10.0

    def test_scale(self):
        clip = self._make()
        assert clip.scale == (0.75, 0.75)

    def test_scale_setter(self):
        data = _base(_type="ScreenVMFile", parameters={
            "scale0": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 1.0, "interp": "eioe"},
        })
        clip = ScreenVMFile(data)
        clip.scale = (0.5, 0.5)
        assert data["parameters"]["scale0"]["defaultValue"] == 0.5

    def test_cursor_opacity_setter(self):
        data = _base(_type="ScreenVMFile", parameters={
            "cursorOpacity": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
        })
        clip = ScreenVMFile(data)
        clip.cursor_opacity = 0.5
        assert data["parameters"]["cursorOpacity"]["defaultValue"] == 0.5

    def test_cursor_track_level(self):
        clip = self._make()
        assert clip.cursor_track_level == 0.5

    def test_smooth_cursor_across_edit_duration(self):
        clip = self._make()
        assert clip.smooth_cursor_across_edit_duration == 0

    def test_cursor_motion_blur_intensity_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorMotionBlur", "parameters": {
                "intensity": {"type": "double", "defaultValue": 1.0, "interp": "linr"},
            }},
        ])
        clip = ScreenVMFile(data)
        assert clip.cursor_motion_blur_intensity == 1.0

    def test_cursor_motion_blur_intensity_no_effect(self):
        clip = ScreenVMFile(_base(_type="ScreenVMFile"))
        assert clip.cursor_motion_blur_intensity == 0.0

    def test_cursor_shadow_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorShadow", "parameters": {
                "angle": {"type": "double", "defaultValue": 3.9, "interp": "linr"},
                "offset": 7.0,
            }},
        ])
        clip = ScreenVMFile(data)
        actual_shadow = clip.cursor_shadow
        assert actual_shadow["angle"] == 3.9
        assert actual_shadow["offset"] == 7.0

    def test_cursor_shadow_no_effect(self):
        clip = ScreenVMFile(_base(_type="ScreenVMFile"))
        assert clip.cursor_shadow == {}

    def test_cursor_physics_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorPhysics", "parameters": {
                "intensity": {"type": "double", "defaultValue": 1.5, "interp": "linr"},
                "tilt": {"type": "double", "defaultValue": 2.5, "interp": "linr"},
            }},
        ])
        clip = ScreenVMFile(data)
        actual_physics = clip.cursor_physics
        assert actual_physics["intensity"] == 1.5
        assert actual_physics["tilt"] == 2.5

    def test_cursor_physics_no_effect(self):
        clip = ScreenVMFile(_base(_type="ScreenVMFile"))
        assert clip.cursor_physics == {}

    def test_left_click_scaling_with_effect(self):
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "LeftClickScaling", "parameters": {
                "scale": {"type": "double", "defaultValue": 3.5, "interp": "linr"},
                "speed": 7.5,
            }},
        ])
        clip = ScreenVMFile(data)
        actual_click = clip.left_click_scaling
        assert actual_click["scale"] == 3.5
        assert actual_click["speed"] == 7.5

    def test_left_click_scaling_no_effect(self):
        clip = ScreenVMFile(_base(_type="ScreenVMFile"))
        assert clip.left_click_scaling == {}

    def test_get_param_value_raw_numeric(self):
        data = _base(_type="ScreenVMFile", parameters={"cursorScale": 3.0})
        clip = ScreenVMFile(data)
        assert clip.cursor_scale == 3.0

    def test_set_param_value_creates_new(self):
        data = _base(_type="ScreenVMFile", parameters={})
        clip = ScreenVMFile(data)
        clip.cursor_scale = 4.0
        assert data["parameters"]["cursorScale"]["defaultValue"] == 4.0
        assert data["parameters"]["cursorScale"]["interp"] == "linr"


# ==================================================================
# ScreenIMFile
# ==================================================================

class TestScreenIMFile:
    def test_cursor_image_path(self):
        data = _base(_type="ScreenIMFile", parameters={
            "cursorImagePath": "2b7b6af1/2",
        })
        clip = ScreenIMFile(data)
        assert clip.cursor_image_path == "2b7b6af1/2"

    def test_cursor_image_path_none(self):
        clip = ScreenIMFile(_base(_type="ScreenIMFile"))
        assert clip.cursor_image_path is None

    def test_cursor_location_keyframes(self):
        data = _base(_type="ScreenIMFile", parameters={
            "cursorLocation": {
                "type": "point",
                "keyframes": [
                    {"time": 0, "endTime": 100, "value": [10, 20, 0], "duration": 0},
                    {"time": 100, "endTime": 200, "value": [30, 40, 0], "duration": 0},
                ],
            },
        })
        clip = ScreenIMFile(data)
        actual_kf = clip.cursor_location_keyframes
        assert actual_kf[0]["value"] == [10, 20, 0]
        assert actual_kf[1]["value"] == [30, 40, 0]

    def test_cursor_location_keyframes_empty(self):
        clip = ScreenIMFile(_base(_type="ScreenIMFile"))
        assert clip.cursor_location_keyframes == []


# ==================================================================
# AMFile — missing: channel_number setter, loudness_normalization setter
# ==================================================================

class TestAMFileMissing:
    def test_channel_number_setter(self):
        data = _base(_type="AMFile")
        clip = AMFile(data)
        clip.channel_number = "0,1"
        assert data["channelNumber"] == "0,1"

    def test_loudness_normalization_setter(self):
        data = _base(_type="AMFile")
        clip = AMFile(data)
        clip.loudness_normalization = True
        assert data["attributes"]["loudnessNormalization"] is True


# ==================================================================
# Group — missing: GroupTrack repr, GroupTrack parameters
# ==================================================================

class TestGroupMissing:
    def test_group_track_repr(self):
        track_data = {"trackIndex": 2, "medias": [_base(), _base(id=2)], "parameters": {}}
        track = GroupTrack(track_data)
        actual_repr = repr(track)
        assert actual_repr == "GroupTrack(index=2, clips=2)"

    def test_group_track_parameters(self):
        track_data = {"trackIndex": 0, "medias": [], "parameters": {"volume": 0.5}}
        track = GroupTrack(track_data)
        assert track.parameters == {"volume": 0.5}


# ==================================================================
# BaseClip — missing: gain setter, mute, metadata, animation_tracks,
#   visual_animations, repr, media_start setter, media_duration setter,
#   scalar setter, fade_in, fade_out, fade, set_opacity, clear_animations,
#   add_effect, add_drop_shadow, add_glow, add_round_corners, remove_effects,
#   add_glow_timed
# ==================================================================

class TestBaseClipGainAndMute:
    def test_gain_default(self):
        clip = BaseClip(_base())
        assert clip.gain == 1.0

    def test_gain_setter(self):
        data = _base()
        clip = BaseClip(data)
        clip.gain = 0.5
        assert data["attributes"]["gain"] == 0.5

    def test_mute(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.mute()
        assert actual_result is clip
        assert clip.gain == 0.0


class TestBaseClipMetadata:
    def test_metadata_default(self):
        clip = BaseClip(_base())
        assert clip.metadata == {}

    def test_metadata_present(self):
        data = _base(metadata={"key": "val"})
        clip = BaseClip(data)
        assert clip.metadata == {"key": "val"}

    def test_animation_tracks_default(self):
        clip = BaseClip(_base())
        assert clip.animation_tracks == {}

    def test_visual_animations_default(self):
        clip = BaseClip(_base())
        assert clip.visual_animations == []

    def test_visual_animations_present(self):
        data = _base(animationTracks={"visual": [{"track": "opacity"}]})
        clip = BaseClip(data)
        assert clip.visual_animations == [{"track": "opacity"}]


class TestBaseClipRepr:
    def test_repr(self):
        data = _base(start=EDIT_RATE * 2, duration=EDIT_RATE * 5)
        clip = BaseClip(data)
        actual_repr = repr(clip)
        assert "BaseClip" in actual_repr
        assert "2.00s" in actual_repr
        assert "5.00s" in actual_repr


class TestBaseClipSetters:
    def test_media_start_setter(self):
        data = _base()
        clip = BaseClip(data)
        clip.media_start = 999
        assert data["mediaStart"] == 999

    def test_media_duration_setter(self):
        data = _base()
        clip = BaseClip(data)
        clip.media_duration = 888
        assert data["mediaDuration"] == 888

    def test_scalar_setter_from_fraction(self):
        data = _base()
        clip = BaseClip(data)
        clip.scalar = Fraction(1, 2)
        assert data["scalar"] == "1/2"

    def test_media_duration_string_fraction(self):
        data = _base(mediaDuration="100/3")
        clip = BaseClip(data)
        assert clip.media_duration == Fraction(100, 3)


class TestBaseClipFade:
    def test_fade_in(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.fade_in(1.0)
        assert actual_result is clip
        assert "opacity" in data["parameters"]
        assert data["parameters"]["opacity"]["keyframes"][0]["value"] == 0.0

    def test_fade_out(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.fade_out(1.0)
        assert actual_result is clip
        assert "opacity" in data["parameters"]
        kf = data["parameters"]["opacity"]["keyframes"]
        assert kf[0]["value"] == 1.0
        assert kf[-1]["value"] == 0.0

    def test_fade_both(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.fade(fade_in_seconds=0.5, fade_out_seconds=0.5)
        assert actual_result is clip
        visual = data["animationTracks"]["visual"]
        # 3 segments for fade-in + hold + fade-out
        assert isinstance(visual, list)

    def test_fade_out_only(self):
        data = _base()
        clip = BaseClip(data)
        clip.fade(fade_out_seconds=1.0)
        kf = data["parameters"]["opacity"]["keyframes"]
        assert kf[0]["value"] == 1.0
        assert kf[-1]["value"] == 0.0

    def test_fade_no_op(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.fade()
        assert actual_result is clip
        assert "opacity" not in data.get("parameters", {})

    def test_set_opacity(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.set_opacity(0.5)
        assert actual_result is clip
        assert data["parameters"]["opacity"]["keyframes"][0]["value"] == 0.5

    def test_clear_animations(self):
        data = _base(animationTracks={"visual": [{"track": "opacity"}]})
        clip = BaseClip(data)
        actual_result = clip.clear_animations()
        assert actual_result is clip
        assert data["animationTracks"]["visual"] == []


class TestBaseClipEffects:
    def test_add_effect(self):
        data = _base()
        clip = BaseClip(data)
        effect_data = {"effectName": "TestEffect", "bypassed": False}
        actual_effect = clip.add_effect(effect_data)
        assert actual_effect is not None
        assert data["effects"][0]["effectName"] == "TestEffect"

    def test_add_drop_shadow(self):
        data = _base()
        clip = BaseClip(data)
        actual_effect = clip.add_drop_shadow(offset=10, blur=20, opacity=0.3, angle=5.0, color=(0.1, 0.2, 0.3))
        assert actual_effect is not None
        effect_dict = data["effects"][0]
        assert effect_dict["effectName"] == "DropShadow"
        assert effect_dict["parameters"]["offset"]["defaultValue"] == 10

    def test_add_glow(self):
        data = _base()
        clip = BaseClip(data)
        actual_effect = clip.add_glow(radius=50.0, intensity=0.5)
        assert actual_effect is not None
        assert data["effects"][0]["effectName"] == "Glow"
        assert data["effects"][0]["parameters"]["radius"]["defaultValue"] == 50.0

    def test_add_round_corners(self):
        data = _base()
        clip = BaseClip(data)
        actual_effect = clip.add_round_corners(radius=20.0)
        assert actual_effect is not None
        assert data["effects"][0]["effectName"] == "RoundCorners"
        assert data["effects"][0]["parameters"]["radius"]["defaultValue"] == 20.0

    def test_remove_effects(self):
        data = _base(effects=[{"effectName": "Glow"}])
        clip = BaseClip(data)
        actual_result = clip.remove_effects()
        assert actual_result is clip
        assert data["effects"] == []

    def test_add_glow_timed(self):
        data = _base()
        clip = BaseClip(data)
        actual_glow = clip.add_glow_timed(
            start_seconds=1.0, duration_seconds=2.0,
            radius=40.0, intensity=0.4,
            fade_in_seconds=0.3, fade_out_seconds=0.5,
        )
        assert actual_glow is not None
        effect_dict = data["effects"][0]
        assert effect_dict["effectName"] == "Glow"
        assert effect_dict["parameters"]["radius"]["defaultValue"] == 40.0
        assert effect_dict["leftEdgeMods"][0]["type"] == "fadeIn"
        assert effect_dict["rightEdgeMods"][0]["type"] == "fadeOut"


class TestBaseClipRemoveOpacityTracks:
    def test_remove_opacity_tracks_no_visual(self):
        """_remove_opacity_tracks is a no-op when no animationTracks exist."""
        data = _base()
        clip = BaseClip(data)
        clip._remove_opacity_tracks()  # should not raise

    def test_remove_opacity_tracks_filters(self):
        data = _base(animationTracks={"visual": [
            {"track": "opacity", "endTime": 100},
            {"track": "position", "endTime": 200},
        ]})
        clip = BaseClip(data)
        clip._remove_opacity_tracks()
        assert data["animationTracks"]["visual"] == [{"track": "position", "endTime": 200}]


class TestCalloutHorizontalAlignmentGetter:
    def test_horizontal_alignment_from_def(self):
        data = _base(_type="Callout", **{"def": {"horizontal-alignment": "right"}})
        clip = Callout(data)
        assert clip.horizontal_alignment == "right"


class TestScreenVMFileEffectParamRawValue:
    def test_get_effect_param_raw_numeric(self):
        """Cover _get_effect_param when param is a raw number, not a dict."""
        data = _base(_type="ScreenVMFile", parameters={}, effects=[
            {"effectName": "CursorMotionBlur", "parameters": {"intensity": 0.75}},
        ])
        clip = ScreenVMFile(data)
        assert clip.cursor_motion_blur_intensity == 0.75
