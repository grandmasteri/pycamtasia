"""Tests for the Right Angle Lower Third title template."""
from __future__ import annotations

from typing import Any

from camtasia.timing import seconds_to_ticks
from camtasia.timeline.track import Track
from camtasia.timeline.clips.group import Group


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
