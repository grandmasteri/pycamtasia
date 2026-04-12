from __future__ import annotations

from fractions import Fraction

import pytest

from camtasia.timeline.clips import (
    EDIT_RATE,
    AMFile,
    BaseClip,
    Callout,
    Group,
    GroupTrack,
    IMFile,
    ScreenIMFile,
    ScreenVMFile,
    StitchedMedia,
    VMFile,
    clip_from_dict,
)


# ------------------------------------------------------------------
# Helpers: realistic clip dicts based on the Camtasia format spec
# ------------------------------------------------------------------

def _base_clip_dict(**overrides) -> dict:
    base = {
        "id": 14,
        "_type": "AMFile",
        "src": 3,
        "start": 0,
        "duration": 106051680000,
        "mediaStart": 0,
        "mediaDuration": 113484000000,
        "scalar": 1,
    }
    base.update(overrides)
    return base


def _amfile_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="AMFile",
        channelNumber="0,1",
        attributes={"ident": "voiceover", "gain": 0.8, "mixToMono": False, "loudnessNormalization": True},
    )
    d.update(overrides)
    return d


def _imfile_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="IMFile",
        id=33,
        src=6,
        start=5092080000,
        duration=26248320000,
        mediaDuration=1,
        parameters={
            "translation0": {"type": "double", "defaultValue": 10.0, "interp": "eioe"},
            "translation1": {"type": "double", "defaultValue": 20.0, "interp": "eioe"},
            "scale0": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
            "scale1": {"type": "double", "defaultValue": 0.75, "interp": "eioe"},
        },
    )
    d.update(overrides)
    return d


def _screen_vmfile_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="ScreenVMFile",
        id=50,
        src=2,
        scalar="51/101",
        parameters={
            "cursorScale": {"type": "double", "defaultValue": 5.0, "interp": "linr"},
            "cursorOpacity": {"type": "double", "defaultValue": 0.8, "interp": "linr"},
        },
    )
    d.update(overrides)
    return d


def _callout_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="Callout",
        id=60,
        **{"def": {
            "kind": "remix",
            "shape": "text",
            "style": "basic",
            "text": "Hello World",
            "width": 934.5,
            "height": 253.9,
            "horizontal-alignment": "center",
        }},
    )
    d.update(overrides)
    return d


def _group_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="Group",
        id=70,
        tracks=[
            {
                "trackIndex": 0,
                "medias": [_base_clip_dict(_type="IMFile", id=71)],
                "parameters": {},
            },
            {
                "trackIndex": 1,
                "medias": [_base_clip_dict(_type="AMFile", id=72)],
                "parameters": {},
            },
        ],
        attributes={"ident": "Group 1", "widthAttr": 1900.0, "heightAttr": 1060.0},
    )
    d.update(overrides)
    return d


def _stitched_dict(**overrides) -> dict:
    d = _base_clip_dict(
        _type="StitchedMedia",
        id=80,
        medias=[
            _base_clip_dict(_type="AMFile", id=81, start=0, duration=50000000),
            _base_clip_dict(_type="AMFile", id=82, start=50000000, duration=60000000),
        ],
        attributes={"gain": 0.9},
    )
    d.update(overrides)
    return d


# ------------------------------------------------------------------
# clip_from_dict factory dispatch
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    "type_str, expected_class",
    [
        ("AMFile", AMFile),
        ("VMFile", VMFile),
        ("IMFile", IMFile),
        ("ScreenVMFile", ScreenVMFile),
        ("ScreenIMFile", ScreenIMFile),
        ("StitchedMedia", StitchedMedia),
        ("Group", Group),
        ("Callout", Callout),
    ],
    ids=["AMFile", "VMFile", "IMFile", "ScreenVMFile", "ScreenIMFile", "StitchedMedia", "Group", "Callout"],
)
def test_clip_from_dict_dispatches_correct_type(type_str: str, expected_class: type) -> None:
    data = _base_clip_dict(_type=type_str)
    actual_clip = clip_from_dict(data)
    assert type(actual_clip) is expected_class


def test_clip_from_dict_unknown_type_falls_back_to_base() -> None:
    data = _base_clip_dict(_type="UnknownClipType")
    actual_clip = clip_from_dict(data)
    assert type(actual_clip) is BaseClip


def test_clip_from_dict_missing_type_falls_back_to_base() -> None:
    data = {"id": 1, "start": 0, "duration": 100, "mediaStart": 0, "mediaDuration": 100}
    actual_clip = clip_from_dict(data)
    assert type(actual_clip) is BaseClip


# ------------------------------------------------------------------
# BaseClip properties
# ------------------------------------------------------------------

def test_baseclip_core_properties() -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    assert clip.id == 14
    assert clip.clip_type == "AMFile"
    assert clip.start == 0
    assert clip.duration == 106051680000
    assert clip.media_start == 0
    assert clip.media_duration == 113484000000
    assert clip.source_id == 3


def test_baseclip_scalar_parses_string_fraction() -> None:
    data = _base_clip_dict(scalar="51/101")
    clip = BaseClip(data)
    actual_scalar = clip.scalar
    assert actual_scalar == Fraction(51, 101)


def test_baseclip_scalar_parses_int() -> None:
    data = _base_clip_dict(scalar=1)
    clip = BaseClip(data)
    actual_scalar = clip.scalar
    assert actual_scalar == Fraction(1)


def test_baseclip_set_speed_mutates_dict() -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.set_speed(2.0)
    expected_scalar = str(Fraction(1, 2))
    assert data["scalar"] == expected_scalar


def test_baseclip_start_seconds() -> None:
    data = _base_clip_dict(start=EDIT_RATE * 5)
    clip = BaseClip(data)
    assert clip.start_seconds == 5.0


def test_baseclip_duration_seconds() -> None:
    data = _base_clip_dict(duration=EDIT_RATE * 10)
    clip = BaseClip(data)
    assert clip.duration_seconds == 10.0


@pytest.mark.parametrize(
    "input_seconds, expected_ticks",
    [
        (0.0, 0),
        (1.0, EDIT_RATE),
        (5.5, round(5.5 * EDIT_RATE)),
    ],
    ids=["zero", "one-second", "fractional"],
)
def test_set_start_seconds(input_seconds: float, expected_ticks: int) -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.start_seconds = input_seconds
    actual_start = clip.start
    assert actual_start == expected_ticks


@pytest.mark.parametrize(
    "input_seconds, expected_ticks",
    [
        (0.0, 0),
        (1.0, EDIT_RATE),
        (3.25, round(3.25 * EDIT_RATE)),
    ],
    ids=["zero", "one-second", "fractional"],
)
def test_set_duration_seconds(input_seconds: float, expected_ticks: int) -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.duration_seconds = input_seconds
    actual_duration = clip.duration
    assert actual_duration == expected_ticks


@pytest.mark.parametrize("input_seconds", [0.0, 1.0, 7.33], ids=["zero", "one", "fractional"])
def test_start_seconds_roundtrip(input_seconds: float) -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.start_seconds = input_seconds
    actual_seconds = clip.start_seconds
    assert actual_seconds == pytest.approx(input_seconds)


@pytest.mark.parametrize("input_seconds", [0.0, 1.0, 4.87], ids=["zero", "one", "fractional"])
def test_duration_seconds_roundtrip(input_seconds: float) -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.duration_seconds = input_seconds
    actual_seconds = clip.duration_seconds
    assert actual_seconds == pytest.approx(input_seconds)


def test_baseclip_media_start_parses_string_fraction() -> None:
    data = _base_clip_dict(mediaStart="100/3")
    clip = BaseClip(data)
    assert clip.media_start == Fraction(100, 3)


def test_baseclip_effects_defaults_empty() -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    assert clip.effects == []


def test_baseclip_parameters_defaults_empty() -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    assert clip.parameters == {}


def test_baseclip_source_id_none_when_absent() -> None:
    data = _base_clip_dict()
    del data["src"]
    clip = BaseClip(data)
    assert clip.source_id is None


# ------------------------------------------------------------------
# Dict mutation passthrough
# ------------------------------------------------------------------

def test_baseclip_start_setter_mutates_dict() -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.start = 999
    assert data["start"] == 999


def test_baseclip_duration_setter_mutates_dict() -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.duration = 888
    assert data["duration"] == 888


# ------------------------------------------------------------------
# AMFile
# ------------------------------------------------------------------

def test_amfile_channel_number() -> None:
    clip = AMFile(_amfile_dict())
    assert clip.channel_number == "0,1"


def test_amfile_gain() -> None:
    clip = AMFile(_amfile_dict())
    assert clip.gain == 0.8


def test_amfile_loudness_normalization() -> None:
    clip = AMFile(_amfile_dict())
    assert clip.loudness_normalization is True


def test_amfile_gain_setter_mutates_dict() -> None:
    data = _amfile_dict()
    clip = AMFile(data)
    clip.gain = 1.5
    assert data["attributes"]["gain"] == 1.5


def test_amfile_channel_number_default() -> None:
    data = _base_clip_dict(_type="AMFile")
    clip = AMFile(data)
    assert clip.channel_number == "0"


def test_amfile_gain_default() -> None:
    data = _base_clip_dict(_type="AMFile")
    clip = AMFile(data)
    assert clip.gain == 1.0


def test_amfile_loudness_normalization_default() -> None:
    data = _base_clip_dict(_type="AMFile")
    clip = AMFile(data)
    assert clip.loudness_normalization is False


# ------------------------------------------------------------------
# IMFile
# ------------------------------------------------------------------

def test_imfile_translation() -> None:
    clip = IMFile(_imfile_dict())
    assert clip.translation == (10.0, 20.0)


def test_imfile_scale() -> None:
    clip = IMFile(_imfile_dict())
    assert clip.scale == (0.75, 0.75)


def test_imfile_translation_setter_mutates_dict() -> None:
    data = _imfile_dict()
    clip = IMFile(data)
    clip.translation = (50.0, 60.0)
    assert data["parameters"]["translation0"]["defaultValue"] == 50.0
    assert data["parameters"]["translation1"]["defaultValue"] == 60.0


def test_imfile_scale_default_when_absent() -> None:
    data = _base_clip_dict(_type="IMFile")
    clip = IMFile(data)
    assert clip.scale == (1.0, 1.0)


def test_imfile_translation_default_when_absent() -> None:
    data = _base_clip_dict(_type="IMFile")
    clip = IMFile(data)
    assert clip.translation == (0.0, 0.0)


# ------------------------------------------------------------------
# ScreenVMFile
# ------------------------------------------------------------------

def test_screen_vmfile_cursor_scale() -> None:
    clip = ScreenVMFile(_screen_vmfile_dict())
    assert clip.cursor_scale == 5.0


def test_screen_vmfile_cursor_opacity() -> None:
    clip = ScreenVMFile(_screen_vmfile_dict())
    assert clip.cursor_opacity == 0.8


def test_screen_vmfile_cursor_scale_setter_mutates_dict() -> None:
    data = _screen_vmfile_dict()
    clip = ScreenVMFile(data)
    clip.cursor_scale = 3.0
    assert data["parameters"]["cursorScale"]["defaultValue"] == 3.0


def test_screen_vmfile_cursor_scale_default() -> None:
    data = _base_clip_dict(_type="ScreenVMFile")
    clip = ScreenVMFile(data)
    assert clip.cursor_scale == 1.0


def test_screen_vmfile_cursor_opacity_default() -> None:
    data = _base_clip_dict(_type="ScreenVMFile")
    clip = ScreenVMFile(data)
    assert clip.cursor_opacity == 1.0


# ------------------------------------------------------------------
# StitchedMedia
# ------------------------------------------------------------------

def test_stitched_nested_clips_returns_typed_clips() -> None:
    clip = StitchedMedia(_stitched_dict())
    actual_clips = clip.nested_clips
    assert [type(c) for c in actual_clips] == [AMFile, AMFile]
    assert actual_clips[0].id == 81
    assert actual_clips[1].id == 82


def test_stitched_volume() -> None:
    clip = StitchedMedia(_stitched_dict())
    assert clip.volume == 0.9


def test_stitched_nested_clips_empty_when_no_medias() -> None:
    data = _base_clip_dict(_type="StitchedMedia")
    clip = StitchedMedia(data)
    assert clip.nested_clips == []


# ------------------------------------------------------------------
# Group
# ------------------------------------------------------------------

def test_group_tracks_returns_group_track_objects() -> None:
    clip = Group(_group_dict())
    actual_tracks = clip.tracks
    assert [type(t) for t in actual_tracks] == [GroupTrack, GroupTrack]


def test_group_track_clips_are_typed() -> None:
    clip = Group(_group_dict())
    track0_clips = clip.tracks[0].clips
    assert type(track0_clips[0]) is IMFile

    track1_clips = clip.tracks[1].clips
    assert type(track1_clips[0]) is AMFile


def test_group_track_index() -> None:
    clip = Group(_group_dict())
    assert clip.tracks[0].track_index == 0
    assert clip.tracks[1].track_index == 1


def test_group_attributes() -> None:
    clip = Group(_group_dict())
    assert clip.ident == "Group 1"
    assert clip.width == 1900.0
    assert clip.height == 1060.0


def test_group_tracks_empty_when_no_tracks() -> None:
    data = _base_clip_dict(_type="Group")
    clip = Group(data)
    assert clip.tracks == []


# ------------------------------------------------------------------
# Callout
# ------------------------------------------------------------------

def test_callout_text() -> None:
    clip = Callout(_callout_dict())
    assert clip.text == "Hello World"


def test_callout_text_setter_mutates_dict() -> None:
    data = _callout_dict()
    clip = Callout(data)
    clip.text = "Updated"
    assert data["def"]["text"] == "Updated"


def test_callout_kind_shape_style() -> None:
    clip = Callout(_callout_dict())
    assert clip.kind == "remix"
    assert clip.shape == "text"
    assert clip.style == "basic"


def test_callout_dimensions() -> None:
    clip = Callout(_callout_dict())
    assert clip.width == 934.5
    assert clip.height == 253.9


def test_callout_text_default_when_no_def() -> None:
    data = _base_clip_dict(_type="Callout")
    clip = Callout(data)
    assert clip.text == ""


class TestClipReprShowsSeconds:
    def test_clip_repr_shows_seconds(self):
        data = _base_clip_dict(start=705_600_000, duration=705_600_000 * 2)
        clip = BaseClip(data)
        r = repr(clip)
        assert "1.00s" in r
        assert "2.00s" in r
        assert "start=" in r
        assert "duration=" in r
