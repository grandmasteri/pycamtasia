"""Tests for the Right Angle Lower Third title template."""
from __future__ import annotations

import copy
from typing import Any
from unittest.mock import patch

from camtasia.templates import lower_third
from camtasia.timeline.clips.group import Group
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


def _make_track() -> Track:
    attrs: dict[str, Any] = {"ident": "Track 1"}
    data: dict[str, Any] = {"trackIndex": 0, "medias": []}
    return Track(attrs, data)


def _get_title_clip(group_data: dict) -> dict:
    """Title is on tracks[0].medias[0].tracks[1].medias[0]."""
    return group_data["tracks"][0]["medias"][0]["tracks"][1]["medias"][0]


def _get_subtitle_clip(group_data: dict) -> dict:
    """Subtitle is on tracks[0].medias[0].tracks[0].medias[0]."""
    return group_data["tracks"][0]["medias"][0]["tracks"][0]["medias"][0]


def _get_line_clip(group_data: dict) -> dict:
    """Accent line is on tracks[2].medias[0]."""
    return group_data["tracks"][2]["medias"][0]


class TestAddLowerThirdCreatesGroup:
    def test_add_lower_third_creates_group(self):
        track = _make_track()
        clip = track.add_lower_third("Name", "Description", 5.0, 10.0)

        assert isinstance(clip, Group)
        assert clip.ident == "Right Angle Lower Third"
        assert [m["_type"] for m in track._data["medias"]] == ["Group"]
        # Outer group has 3 tracks: Text group, Shape, Line
        assert [t["medias"][0]["_type"] for t in clip._data["tracks"]] == ["Group", "Callout", "Callout"]


class TestLowerThirdTitleText:
    def test_lower_third_title_text(self):
        track = _make_track()
        clip = track.add_lower_third("Jane Doe", "Some subtitle", 0, 10)

        title_clip = _get_title_clip(clip._data)
        assert title_clip["def"]["text"] == "Jane Doe"
        # textAttributes rangeEnd should match title length
        for kf in title_clip["def"]["textAttributes"]["keyframes"]:
            for attr in kf["value"]:
                assert attr["rangeEnd"] == len("Jane Doe")


class TestLowerThirdSubtitleText:
    def test_lower_third_subtitle_text(self):
        track = _make_track()
        clip = track.add_lower_third("Name", "My custom subtitle", 0, 10)

        subtitle_clip = _get_subtitle_clip(clip._data)
        assert subtitle_clip["def"]["text"] == "My custom subtitle"
        for kf in subtitle_clip["def"]["textAttributes"]["keyframes"]:
            for attr in kf["value"]:
                assert attr["rangeEnd"] == len("My custom subtitle")


class TestLowerThirdCustomColors:
    def test_lower_third_custom_colors(self):
        track = _make_track()
        clip = track.add_lower_third(
            "Name", "Sub", 0, 10,
            title_color=(255, 0, 0, 255),
            accent_color=(1.0, 0.0, 0.0),
        )

        # Check title fgColor override
        title_clip = _get_title_clip(clip._data)
        for kf in title_clip["def"]["textAttributes"]["keyframes"]:
            for attr in kf["value"]:
                if attr["name"] == "fgColor":
                    assert attr["value"] == "(255,0,0,255)"

        # Check accent line fill color override
        line_clip = _get_line_clip(clip._data)
        assert line_clip["def"]["fill-color-red"]["defaultValue"] == 1.0
        assert line_clip["def"]["fill-color-green"]["defaultValue"] == 0.0
        assert line_clip["def"]["fill-color-blue"]["defaultValue"] == 0.0
        # Keyframes should also be updated
        for kf in line_clip["def"]["fill-color-red"]["keyframes"]:
            assert kf["value"] == 1.0
        for kf in line_clip["def"]["fill-color-green"]["keyframes"]:
            assert kf["value"] == 0.0
        for kf in line_clip["def"]["fill-color-blue"]["keyframes"]:
            assert kf["value"] == 0.0


class TestLowerThirdPositionAndDuration:
    def test_lower_third_position_and_duration(self):
        track = _make_track()
        clip = track.add_lower_third("Name", "Sub", 5.0, 8.0)

        expected_start = seconds_to_ticks(5.0)
        expected_duration = seconds_to_ticks(8.0)

        assert clip.start == expected_start
        assert clip.duration == expected_duration
        assert clip._data["mediaDuration"] == float(expected_duration)

        # IDs should be fresh sequential (starting from 1 on empty track)
        outer_id = clip._data["id"]
        text_group = clip._data["tracks"][0]["medias"][0]
        assert text_group["id"] == outer_id + 1
        subtitle = text_group["tracks"][0]["medias"][0]
        assert subtitle["id"] == outer_id + 2
        title = text_group["tracks"][1]["medias"][0]
        assert title["id"] == outer_id + 3
        shape = clip._data["tracks"][1]["medias"][0]
        assert shape["id"] == outer_id + 4
        line = clip._data["tracks"][2]["medias"][0]
        assert line["id"] == outer_id + 5


class TestLowerThirdFontWeight:
    def test_font_weight_custom(self):
        track = _make_track()
        clip = track.add_lower_third("Name", "Sub", 0, 10, font_weight=700)

        title_clip = _get_title_clip(clip._data)
        for kf in title_clip["def"]["textAttributes"]["keyframes"]:
            for attr in kf["value"]:
                if attr["name"] == "fontWeight":
                    actual_weight = attr["value"]
                    expected_weight = 700
                    assert actual_weight == expected_weight

    def test_font_weight_default(self):
        track = _make_track()
        clip = track.add_lower_third("Name", "Sub", 0, 10)

        title_clip = _get_title_clip(clip._data)
        for kf in title_clip["def"]["textAttributes"]["keyframes"]:
            for attr in kf["value"]:
                if attr["name"] == "fontWeight":
                    actual_weight = attr["value"]
                    expected_weight = 900
                    assert actual_weight == expected_weight


class TestLowerThirdScale:
    def test_scale_sets_parameters(self):
        track = _make_track()
        clip = track.add_lower_third("Name", "Sub", 0, 10, scale=0.923)

        actual_scale0 = clip._data["parameters"]["scale0"]
        actual_scale1 = clip._data["parameters"]["scale1"]
        assert isinstance(actual_scale0, dict)
        assert actual_scale0["defaultValue"] == 0.923
        assert actual_scale0["type"] == "double"
        assert isinstance(actual_scale1, dict)
        assert actual_scale1["defaultValue"] == 0.923

    def test_scale_none_no_params(self):
        track = _make_track()
        clip = track.add_lower_third("Name", "Sub", 0, 10)

        assert "scale0" not in clip._data.get("parameters", {})
        assert "scale1" not in clip._data.get("parameters", {})


class TestLowerThirdTemplateIdent:
    def test_template_ident_sets_attribute(self):
        track = _make_track()
        expected_ident = "Custom Lower Third"
        clip = track.add_lower_third(
            "Name", "Sub", 0, 10, template_ident=expected_ident,
        )

        actual_ident = clip._data["attributes"]["ident"]
        assert actual_ident == expected_ident


class TestLowerThirdScaleOverrideWithDictParam:
    """Cover track.py line 862: scale override when existing param is a dict."""

    def test_scale_updates_existing_dict_param(self):
        original = lower_third.LOWER_THIRD_TEMPLATE
        patched = copy.deepcopy(original)
        patched['parameters']['scale0'] = {'type': 'double', 'defaultValue': 1.0, 'interp': 'eioe'}
        patched['parameters']['scale1'] = {'type': 'double', 'defaultValue': 1.0, 'interp': 'eioe'}
        with patch.object(lower_third, 'LOWER_THIRD_TEMPLATE', patched):
            track = _make_track()
            clip = track.add_lower_third("Name", "Sub", 0, 10, scale=0.5)
        actual = clip._data['parameters']
        assert actual['scale0']['defaultValue'] == 0.5
        assert actual['scale1']['defaultValue'] == 0.5


# ── Bug 11: add_lower_third scales line clip keyframed animation timing ──


class TestLowerThirdLineClipKeyframeScaling:
    """Line clip (track index 2) keyframes must be scaled proportionally
    to the requested duration."""

    ORIGINAL_LINE_DUR = 7220640000  # original line clip duration from template

    def _get_line_keyframe_times(self, group_data: dict) -> list[int]:
        """Collect all 'time' values from def keyframes on the line clip."""
        line_clip = _get_line_clip(group_data)
        times = []
        for _key, val in line_clip.get('def', {}).items():
            if isinstance(val, dict) and 'keyframes' in val:
                for kf in val['keyframes']:
                    if 'time' in kf:
                        times.append(kf['time'])
        return times

    def _get_line_animation_end_times(self, group_data: dict) -> list[int]:
        """Collect all 'endTime' values from animationTracks on the line clip."""
        line_clip = _get_line_clip(group_data)
        end_times = []
        for track_kfs in line_clip.get('animationTracks', {}).values():
            for kf in track_kfs:
                if 'endTime' in kf:
                    end_times.append(kf['endTime'])
        return end_times

    def test_line_def_keyframes_scaled(self):
        track = _make_track()
        dur_seconds = 10.0
        clip = track.add_lower_third("Name", "Sub", 0, dur_seconds)
        dur_ticks = seconds_to_ticks(dur_seconds)
        line_scale = dur_ticks / self.ORIGINAL_LINE_DUR

        times = self._get_line_keyframe_times(clip._data)
        # All non-zero times should be scaled from the original template values
        original_times = [0, 352800000, 705600000, 6773760000]
        expected_nonzero = [int(t * line_scale) for t in original_times if t > 0]
        actual_nonzero = [t for t in times if t > 0]
        # Each expected time should appear at least once (multiple def keys share same times)
        for exp in expected_nonzero:
            assert exp in actual_nonzero, f"Expected scaled time {exp} not found in {actual_nonzero}"

    def test_line_animation_tracks_scaled(self):
        track = _make_track()
        dur_seconds = 10.0
        clip = track.add_lower_third("Name", "Sub", 0, dur_seconds)
        dur_ticks = seconds_to_ticks(dur_seconds)
        line_scale = dur_ticks / self.ORIGINAL_LINE_DUR

        end_times = self._get_line_animation_end_times(clip._data)
        original_end_times = [352800000, 705600000, 1411200000, 7197120000]
        expected = [int(t * line_scale) for t in original_end_times]
        assert sorted(end_times) == sorted(expected)

    def test_line_keyframes_match_at_original_duration(self):
        """When duration matches the original template, keyframes should be unchanged."""
        track = _make_track()
        # Use the original template duration in seconds
        dur_seconds = self.ORIGINAL_LINE_DUR / seconds_to_ticks(1.0)
        clip = track.add_lower_third("Name", "Sub", 0, dur_seconds)

        line_clip = _get_line_clip(clip._data)
        # Check that a known def keyframe time is preserved
        width_kfs = line_clip['def']['width']['keyframes']
        times = [kf['time'] for kf in width_kfs]
        assert 352800000 in times
        assert 705600000 in times
