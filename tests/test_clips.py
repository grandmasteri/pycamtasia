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
    assert data["scalar"] == "1/2"


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
    assert clip.cursor_scale == 5.0


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
    assert clip.gain == 0.9  # gain is in attributes, volume is in parameters


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


class TestSetTimeRange:
    def test_set_time_range(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        clip.set_time_range(2.0, 5.0)
        assert clip.start == EDIT_RATE * 2
        assert clip.duration == EDIT_RATE * 5

    def test_set_time_range_chaining(self):
        data = _base_clip_dict()
        clip = BaseClip(data)
        result = clip.set_time_range(1.0, 3.0)
        assert result is clip


def test_stitched_attributes():
    clip = StitchedMedia(_stitched_dict())
    assert isinstance(clip.attributes, dict)


# ------------------------------------------------------------------
# BaseClip: mute, opacity, fade (from base.py coverage)
# ------------------------------------------------------------------

def _coverage_clip(extra=None, **kw):
    d = {'id': 1, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 100,
         'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
         'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
         'animationTracks': {}}
    if extra:
        d.update(extra)
    d.update(kw)
    return d


class TestMuteUnifiedMediaNoAudio:
    def test_raises(self):
        data = _coverage_clip(_type='UnifiedMedia')
        data.pop('audio', None)
        clip = BaseClip(data)
        with pytest.raises(ValueError, match='no audio sub-clip'):
            clip.mute()


class TestOpacitySetterClearsVisualTracks:
    def test_clears_visual(self):
        data = _coverage_clip()
        data['animationTracks'] = {'visual': [{'some': 'segment'}]}
        data['parameters']['opacity'] = 0.5
        clip = BaseClip(data)
        clip.opacity = 0.8
        assert data['animationTracks']['visual'] == []
        assert data['parameters']['opacity'] == 0.8


class TestOpacityNotDict:
    def test_returns_none(self):
        data = _coverage_clip()
        data['parameters']['opacity'] = 0.5
        clip = BaseClip(data)
        assert clip._get_existing_opacity_keyframes() is None


class TestFadeInMergesWithFadeOut:
    def test_merge(self):
        fade_out_kf = {'time': 1000, 'value': 0.0, 'endTime': 2000, 'duration': 1000}
        data = _coverage_clip()
        data['parameters']['opacity'] = {'keyframes': [fade_out_kf]}
        clip = BaseClip(data)
        result = clip.fade_in(1.0)
        assert result is clip
        visual = data['animationTracks'].get('visual', [])
        assert len(visual) == 2
        assert 'endTime' in visual[0]


# ------------------------------------------------------------------
# Callout: set_size dict branch (from base.py coverage)
# ------------------------------------------------------------------

class TestCalloutSetSizeDictBranch:
    def test_updates_dict_default_value(self):
        data = _coverage_clip(_type='Callout')
        data['def'] = {
            'width': {'defaultValue': 100, 'keyframes': [{'time': 0, 'value': 100}]},
            'height': {'defaultValue': 50, 'keyframes': [{'time': 0, 'value': 50}]},
        }
        clip = Callout(data)
        clip.set_size(200, 150)
        assert data['def']['width']['defaultValue'] == 200
        assert data['def']['height']['defaultValue'] == 150
        assert 'keyframes' not in data['def']['width']
        assert 'keyframes' not in data['def']['height']


# ------------------------------------------------------------------
# UnifiedMedia: effect blocking (from unified.py coverage)
# ------------------------------------------------------------------

@pytest.fixture
def um():
    from camtasia.timeline.clips.unified import UnifiedMedia
    return UnifiedMedia({
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
        'video': {'_type': 'VMFile', 'id': 2, 'src': 1, 'start': 0, 'duration': 100,
                  'attributes': {}, 'parameters': {}, 'effects': []},
        'audio': {'_type': 'AMFile', 'id': 3, 'src': 1, 'start': 0, 'duration': 100,
                  'attributes': {}, 'parameters': {}, 'effects': []},
    })


def test_um_add_effect_raises(um):
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_effect({'effectName': 'Glow'})


def test_um_add_drop_shadow_raises(um):
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_drop_shadow()


def test_um_add_round_corners_raises(um):
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_round_corners()


def test_um_add_glow_raises(um):
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_glow()


def test_um_add_glow_timed_raises(um):
    with pytest.raises(TypeError, match='Effects must be added'):
        um.add_glow_timed()


def test_um_copy_effects_from_raises(um):
    with pytest.raises(TypeError, match='Effects must be added'):
        um.copy_effects_from(um)


def test_um_set_source_raises(um):
    with pytest.raises(TypeError, match='Cannot set_source'):
        um.set_source(42)


# ------------------------------------------------------------------
# Clip coverage: unified, group, callout, speed, placeholder, stitched
# ------------------------------------------------------------------

from camtasia.timing import seconds_to_ticks
from camtasia.timeline.track import Track

_S1 = seconds_to_ticks(1.0)
_S5 = seconds_to_ticks(5.0)
_S10 = seconds_to_ticks(10.0)


def _um_data():
    return {
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': _S10,
        'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'video': {
            '_type': 'ScreenVMFile', 'id': 2, 'src': 5, 'start': 0,
            'duration': _S10, 'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'attributes': {'ident': 'rec'},
            'trackNumber': 0,
        },
        'audio': {
            '_type': 'AMFile', 'id': 3, 'src': 5, 'start': 0,
            'duration': _S10, 'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'attributes': {'gain': 1.0},
        },
    }


def _cov_group_data(inner=None, duration=None):
    dur = duration or _S10
    return {
        '_type': 'Group', 'id': 100, 'start': _S1, 'duration': dur,
        'mediaDuration': dur, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'attributes': {'ident': 'grp', 'widthAttr': 1920, 'heightAttr': 1080},
        'tracks': [{'trackIndex': 0, 'medias': inner or [], 'transitions': []}],
    }


def _cov_callout_data(**overrides):
    d = {
        '_type': 'Callout', 'id': 400, 'start': 0, 'duration': _S5,
        'mediaDuration': _S5, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'def': {
            'text': 'Hello', 'kind': 'remix', 'shape': 'text', 'style': 'basic',
            'font': {'name': 'Arial', 'weight': 'Regular', 'size': 24.0},
            'width': 200, 'height': 100,
            'textAttributes': {
                'type': 'textAttributeList',
                'keyframes': [{
                    'endTime': 0,
                    'time': 0,
                    'duration': 0,
                    'value': [
                        {'name': 'fontName', 'value': 'Arial', 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'string'},
                        {'name': 'fontWeight', 'value': 400, 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'int'},
                        {'name': 'fontSize', 'value': 24, 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'double'},
                        {'name': 'fgColor', 'value': '(0,0,0,255)', 'rangeEnd': 5, 'rangeStart': 0, 'valueType': 'color'},
                    ]
                }]
            },
        },
    }
    d.update(overrides)
    return d


class TestUnifiedMediaEffectBlocking:
    def test_add_effect(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_effect({})

    def test_add_drop_shadow(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_drop_shadow()

    def test_add_round_corners(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_round_corners()

    def test_add_glow(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_glow()

    def test_add_glow_timed(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.add_glow_timed()

    def test_copy_effects_from(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.copy_effects_from(um)

    def test_set_source(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError):
            um.set_source(1)


class TestGroupSyncInternalDurations:
    def test_sync_with_fractional_scalar(self):
        inner = {
            '_type': 'VMFile', 'id': 10, 'src': 1,
            'start': 0, 'duration': _S10 * 2,
            'mediaDuration': _S10 * 2, 'mediaStart': 0, 'scalar': '1/2',
            'parameters': {}, 'effects': [],
        }
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.sync_internal_durations()
        assert inner['duration'] == _S10
        expected_md = int(Fraction(_S10) / Fraction(1, 2))
        assert inner['mediaDuration'] == expected_md

    def test_sync_propagates_to_unified(self):
        import copy
        inner = copy.deepcopy(_um_data())
        inner['duration'] = _S10 * 3
        inner['mediaDuration'] = _S10 * 3
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.sync_internal_durations()
        assert inner['duration'] == _S10


class TestGroupUngroup:
    def test_ungroup_adjusts_start_and_propagates(self):
        import copy
        inner_um = copy.deepcopy(_um_data())
        inner_um['start'] = 0
        data = _cov_group_data([inner_um])
        data['start'] = _S5
        g = Group(data)
        clips = g.ungroup()
        assert len(clips) >= 1
        assert clips[0].start == _S5


class TestGroupSetInternalSegmentSpeedsCanvasWidthOnly:
    def test_canvas_width_only(self):
        import copy
        inner = copy.deepcopy(_um_data())
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            canvas_width=1920,
        )
        clip = data['tracks'][0]['medias'][0]
        assert clip['parameters']['scale0']['defaultValue'] == 1.0

    def test_canvas_height_only(self):
        import copy
        inner = copy.deepcopy(_um_data())
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            canvas_height=1080,
        )
        clip = data['tracks'][0]['medias'][0]
        assert clip['parameters']['scale1']['defaultValue'] == 1.0

    def test_source_bin_lookup_miss(self):
        import copy
        inner = copy.deepcopy(_um_data())
        data = _cov_group_data([inner], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            source_bin=[{'id': 999, 'sourceTracks': []}],
            canvas_width=1920,
            canvas_height=1080,
        )
        medias = data['tracks'][0]['medias']
        assert len(medias) == 1
        assert medias[0]['_type'] in ('UnifiedMedia', 'ScreenVMFile', 'VMFile')

    def test_no_internal_track_raises(self):
        data = _cov_group_data()
        data['tracks'][0]['medias'] = []
        g = Group(data)
        with pytest.raises(ValueError, match='No internal track'):
            g.set_internal_segment_speeds(segments=[(0.0, 1.0, 1.0)])

    def test_stitched_media_template(self):
        stitched = {
            '_type': 'StitchedMedia', 'id': 50, 'start': 0, 'duration': _S10,
            'mediaDuration': _S10, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'trackNumber': 0,
            'attributes': {'ident': 'stitch'},
            'medias': [{'_type': 'ScreenVMFile', 'id': 51, 'src': 5}],
        }
        data = _cov_group_data([stitched], duration=_S10)
        g = Group(data)
        g.set_internal_segment_speeds(segments=[(0.0, 5.0, 5.0)])
        assert data['tracks'][0]['medias'][0]['_type'] == 'ScreenVMFile'


class TestCalloutSetFontWithIntWeight:
    def test_set_font_int_weight_updates_keyframes(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_font('Montserrat', weight=700, size=48)
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fontName'] == 'Montserrat'
        assert attrs['fontWeight'] == 700
        assert attrs['fontSize'] == 48

    def test_set_font_string_weight(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_font('Roboto', weight='Bold', size=36)
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fontWeight'] == 700


class TestCalloutSetColorsWithFgColor:
    def test_set_colors_updates_fgcolor_in_keyframes(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_colors(font_color=(0.0, 1.0, 0.0))
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fgColor'] == '(0,255,0,255)'

    def test_set_colors_with_alpha(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.set_colors(font_color=(1.0, 0.0, 0.0, 0.5))
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert '128' in attrs['fgColor'] or '127' in attrs['fgColor']


class TestCalloutDefinitionProperty:
    def test_definition_returns_def_dict(self):
        d = _cov_callout_data()
        c = Callout(d)
        defn = c.definition
        assert defn['text'] == 'Hello'

    def test_definition_empty_when_no_def(self):
        d = _cov_callout_data()
        del d['def']
        c = Callout(d)
        assert c.definition == {}


class TestAdjustScalar:
    def test_adjust_scalar_modifies_clip(self):
        from camtasia.operations.speed import _adjust_scalar
        clip = {'scalar': '1/2', 'metadata': {}}
        _adjust_scalar(clip, Fraction(2))
        assert Fraction(clip['scalar']) == Fraction(1)

    def test_adjust_scalar_unity(self):
        from camtasia.operations.speed import _adjust_scalar
        clip = {'scalar': 1}
        _adjust_scalar(clip, Fraction(3, 2))
        assert Fraction(clip['scalar']) == Fraction(3, 2)


class TestMarkSpeedChangedExclusions:
    def test_imfile_excluded(self):
        from camtasia.operations.speed import rescale_project
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0,
                    'medias': [
                        {'_type': 'IMFile', 'id': 1, 'start': 0, 'duration': _S5,
                         'mediaDuration': 1, 'mediaStart': 0, 'scalar': 1,
                         'parameters': {}, 'effects': [], 'metadata': {}},
                    ],
                    'transitions': [],
                }]}}]},
                'parameters': {},
            },
        }
        rescale_project(data, Fraction(2))
        clip = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert clip.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is not True

    def test_callout_excluded(self):
        from camtasia.operations.speed import rescale_project
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0,
                    'medias': [
                        {'_type': 'Callout', 'id': 1, 'start': 0, 'duration': _S5,
                         'mediaDuration': _S5, 'mediaStart': 0, 'scalar': 1,
                         'parameters': {}, 'effects': [], 'metadata': {},
                         'def': {}},
                    ],
                    'transitions': [],
                }]}}]},
                'parameters': {},
            },
        }
        rescale_project(data, Fraction(2))
        clip = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert clip.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is not True

    def test_mark_speed_recurses_into_unified_children(self):
        from camtasia.operations.speed import rescale_project
        um = _um_data()
        um['metadata'] = {}
        um['video']['metadata'] = {}
        um['audio']['metadata'] = {}
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0, 'medias': [um], 'transitions': [],
                }]}}]},
                'parameters': {},
            },
        }
        rescale_project(data, Fraction(2))
        vid = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['video']
        assert vid.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is True

    def test_mark_speed_recurses_into_group_tracks(self):
        from camtasia.operations.speed import rescale_project
        inner_vm = {
            '_type': 'VMFile', 'id': 10, 'src': 1,
            'start': 0, 'duration': _S5, 'mediaDuration': _S5,
            'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
            'metadata': {},
        }
        group = _cov_group_data([inner_vm], duration=_S5)
        group['metadata'] = {}
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0, 'medias': [group], 'transitions': [],
                }]}}]},
                'parameters': {},
            },
        }
        rescale_project(data, Fraction(2))
        inner = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['tracks'][0]['medias'][0]
        assert inner.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is True

    def test_mark_speed_recurses_into_stitched_medias(self):
        from camtasia.operations.speed import rescale_project
        stitched = {
            '_type': 'StitchedMedia', 'id': 20, 'start': 0, 'duration': _S5,
            'mediaDuration': _S5, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'medias': [{
                '_type': 'VMFile', 'id': 21, 'src': 1,
                'start': 0, 'duration': _S5, 'mediaDuration': _S5,
                'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
                'metadata': {},
            }],
        }
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0, 'medias': [stitched], 'transitions': [],
                }]}}]},
                'parameters': {},
            },
        }
        rescale_project(data, Fraction(2))
        inner = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['medias'][0]
        assert inner.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is True


class TestOverlapFixWithUnified:
    def test_overlap_fix_propagates_to_unified(self):
        import copy
        from camtasia.operations.speed import rescale_project
        um1 = _um_data()
        um1['id'] = 1
        um1['start'] = 0
        um1['duration'] = _S5 + 2
        um2 = copy.deepcopy(_um_data())
        um2['id'] = 4
        um2['video']['id'] = 5
        um2['audio']['id'] = 6
        um2['start'] = _S5
        um2['duration'] = _S5
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0, 'medias': [um1, um2], 'transitions': [],
                }]}}]},
                'parameters': {},
            },
        }
        rescale_project(data, Fraction(1))
        medias = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias']
        a_end = medias[0]['start'] + medias[0]['duration']
        b_start = medias[1]['start']
        assert a_end <= b_start


class TestPlaceholderSetSource:
    def test_set_source_raises(self):
        from camtasia.timeline.clips.placeholder import PlaceholderMedia
        p = PlaceholderMedia({
            '_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': _S5,
            'mediaDuration': 1, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [],
        })
        with pytest.raises(TypeError, match='Cannot set_source'):
            p.set_source(1)


class TestStitchedSetSource:
    def test_set_source_raises(self):
        s = StitchedMedia({
            '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': _S5,
            'mediaDuration': _S5, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'medias': [],
        })
        with pytest.raises(TypeError, match='do not have a top-level source'):
            s.set_source(1)


class TestCalloutSetSourceRaises:
    def test_set_source_raises_type_error(self):
        c = Callout(_cov_callout_data())
        with pytest.raises(TypeError, match='Callout clips do not have a source ID'):
            c.set_source(1)


class TestCalloutTextSetterUpdatesRanges:
    def test_text_setter_updates_keyframe_ranges(self):
        d = _cov_callout_data()
        c = Callout(d)
        c.text = 'New longer text'
        for kf in d['def']['textAttributes']['keyframes']:
            for attr in kf['value']:
                assert attr['rangeEnd'] == len('New longer text')
                assert attr['rangeStart'] == 0


class TestCalloutDimensionSettersWithDictValues:
    def test_width_setter_with_dict_value(self):
        d = _cov_callout_data()
        d['def']['width'] = {'defaultValue': 200, 'keyframes': [{'time': 0, 'value': 200}]}
        c = Callout(d)
        c.width = 300
        assert d['def']['width']['defaultValue'] == 300
        assert 'keyframes' not in d['def']['width']

    def test_height_setter_with_dict_value(self):
        d = _cov_callout_data()
        d['def']['height'] = {'defaultValue': 100, 'keyframes': [{'time': 0, 'value': 100}]}
        c = Callout(d)
        c.height = 200
        assert d['def']['height']['defaultValue'] == 200
        assert 'keyframes' not in d['def']['height']

    def test_corner_radius_setter_with_dict_value(self):
        d = _cov_callout_data()
        d['def']['corner-radius'] = {'defaultValue': 5, 'keyframes': [{'time': 0, 'value': 5}]}
        c = Callout(d)
        c.corner_radius = 10
        assert d['def']['corner-radius']['defaultValue'] == 10
        assert 'keyframes' not in d['def']['corner-radius']


class TestUnifiedMediaDuplicateEffectsTo:
    def test_duplicate_effects_to_raises(self):
        from camtasia.timeline.clips.unified import UnifiedMedia
        um = UnifiedMedia(_um_data())
        with pytest.raises(TypeError, match='Cannot duplicate effects from UnifiedMedia'):
            um.duplicate_effects_to(um)


# =========================================================================
# Tests migrated from test_convenience.py
# =========================================================================

def _make_track(medias=None, name='T'):
    """Build a minimal Track from raw dicts."""
    data = {'trackIndex': 0, 'medias': medias or []}
    attrs = {'ident': name}
    return Track(attrs, data)




# ---------------------------------------------------------------------------
# BaseClip.describe
# ---------------------------------------------------------------------------

def test_clip_describe():
    from camtasia.timeline.clips import clip_from_dict
    data = {
        'id': 42,
        '_type': 'VMFile',
        'start': seconds_to_ticks(1.0),
        'duration': seconds_to_ticks(4.0),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(4.0),
        'scalar': 1,
        'effects': [{'effectName': 'Glow'}, {'effectName': 'DropShadow'}],
        'parameters': {},
        'metadata': {},
        'animationTracks': {},
    }
    clip = clip_from_dict(data)
    desc = clip.describe()
    assert 'VMFile (id=42)' in desc
    assert '1.00s' in desc
    assert '5.00s' in desc
    assert '4.00s' in desc
    assert 'Effects: Glow, DropShadow' in desc




# ---------------------------------------------------------------------------
# Clip type-check properties
# ---------------------------------------------------------------------------

@pytest.mark.parametrize('type_str, prop, expected', [
    ('AMFile', 'is_audio', True),
    ('VMFile', 'is_video', True),
    ('ScreenVMFile', 'is_video', True),
    ('IMFile', 'is_image', True),
    ('Group', 'is_group', True),
    ('Callout', 'is_callout', True),
    ('AMFile', 'is_video', False),
    ('VMFile', 'is_audio', False),
    ('IMFile', 'is_callout', False),
])
def test_clip_type_properties(type_str, prop, expected):
    from camtasia.timeline.clips import clip_from_dict
    data = {'_type': type_str, 'id': 1, 'start': 0, 'duration': 100,
            'mediaSource': {}, 'parameters': {}, 'effects': [],
            'metadata': {}, 'animationTracks': {}}
    clip = clip_from_dict(data)
    assert getattr(clip, prop) is expected




# ---------------------------------------------------------------------------
# BaseClip.end_seconds
# ---------------------------------------------------------------------------

def test_end_seconds():
    from camtasia.timing import EDIT_RATE
    from camtasia.timeline.clips.base import BaseClip
    start = EDIT_RATE * 2   # 2 seconds
    dur = EDIT_RATE * 3     # 3 seconds
    clip = BaseClip({'_type': 'AMFile', 'id': 1, 'start': start,
                     'duration': dur, 'metadata': {},
                     'animationTracks': {}})
    assert clip.end_seconds == pytest.approx(5.0)



# ---------------------------------------------------------------------------
# BaseClip.time_range
# ---------------------------------------------------------------------------

def test_time_range():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import seconds_to_ticks
    data = {
        '_type': 'AMFile', 'id': 1,
        'start': seconds_to_ticks(2.0),
        'duration': seconds_to_ticks(3.0),
        'parameters': {}, 'effects': [],
        'metadata': {}, 'animationTracks': {},
    }
    clip = clip_from_dict(data)
    assert clip.time_range[0] == pytest.approx(2.0)
    assert clip.time_range[1] == pytest.approx(5.0)




# ---------------------------------------------------------------------------
# BaseClip.to_dict
# ---------------------------------------------------------------------------

def test_clip_to_dict():
    from camtasia.timeline.clips.base import BaseClip
    start = seconds_to_ticks(1.0)
    dur = seconds_to_ticks(2.0)
    clip = BaseClip({
        'id': 42, '_type': 'VMFile', 'start': start, 'duration': dur,
        'src': 7, 'effects': [{'effectName': 'Blur'}],
    })
    d = clip.to_dict()
    assert d['id'] == 42
    assert d['type'] == 'VMFile'
    assert d['start_seconds'] == pytest.approx(1.0)
    assert d['duration_seconds'] == pytest.approx(2.0)
    assert d['end_seconds'] == pytest.approx(3.0)
    assert d['source_id'] == 7
    assert d['effects'] == ['Blur']

    # Without source_id or effects
    clip2 = BaseClip({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': start})
    d2 = clip2.to_dict()
    assert 'source_id' not in d2
    assert 'effects' not in d2




# ---------------------------------------------------------------------------
# BaseClip.is_at
# ---------------------------------------------------------------------------

def test_clip_is_at():
    from camtasia.timeline.clips.base import BaseClip
    start = seconds_to_ticks(2.0)
    dur = seconds_to_ticks(3.0)
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': start, 'duration': dur})
    assert clip.is_at(2.0) is True
    assert clip.is_at(3.5) is True
    assert clip.is_at(4.99) is True
    assert clip.is_at(5.0) is False
    assert clip.is_at(1.0) is False




# ---------------------------------------------------------------------------
# StitchedMedia.min_media_start
# ---------------------------------------------------------------------------

def test_stitched_min_media_start():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'mediaStart': 0, 'mediaDuration': 100, 'minMediaStart': 42})
    assert clip.min_media_start == 42
    # default when key absent
    clip2 = clip_from_dict({'_type': 'StitchedMedia', 'id': 2, 'start': 0, 'duration': 100,
                            'mediaStart': 0, 'mediaDuration': 100})
    assert clip2.min_media_start == 0




# ---------------------------------------------------------------------------
# PlaceholderMedia.subtitle
# ---------------------------------------------------------------------------

def test_placeholder_subtitle():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'metadata': {'placeHolderSubTitle': 'hello'}})
    assert clip.subtitle == 'hello'
    clip.subtitle = 'world'
    assert clip.subtitle == 'world'
    # default when absent
    clip2 = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 2, 'start': 0, 'duration': 100})
    assert clip2.subtitle == ''




# ---------------------------------------------------------------------------
# PlaceholderMedia.width / height
# ---------------------------------------------------------------------------

def test_placeholder_width_height():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'attributes': {'width': 1920.0, 'height': 1080.0}})
    assert clip.width == 1920.0
    assert clip.height == 1080.0
    # defaults
    clip2 = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 2, 'start': 0, 'duration': 100})
    assert clip2.width == 0.0
    assert clip2.height == 0.0




# ---------------------------------------------------------------------------
# BaseClip.is_stitched / is_placeholder
# ---------------------------------------------------------------------------

def test_is_stitched():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
                           'mediaStart': 0, 'mediaDuration': 100})
    assert clip.is_stitched is True
    assert clip.is_placeholder is False


def test_is_placeholder():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.is_placeholder is True
    assert clip.is_stitched is False




# ---------------------------------------------------------------------------
# BaseClip.opacity
# ---------------------------------------------------------------------------

def test_clip_opacity_get_set():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.opacity == 1.0  # default
    clip.opacity = 0.5
    assert clip.opacity == 0.5
    # keyframe-style dict
    clip2 = clip_from_dict({'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 100,
                            'parameters': {'opacity': {'type': 'float', 'defaultValue': 0.75, 'keyframes': []}}})
    assert clip2.opacity == 0.75


def test_clip_opacity_validation():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100})
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        clip.opacity = 1.5
    with pytest.raises(ValueError, match='opacity must be 0.0-1.0'):
        clip.opacity = -0.1




# ---------------------------------------------------------------------------
# BaseClip.volume
# ---------------------------------------------------------------------------

def test_clip_volume_get_set():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.volume == 1.0  # default
    clip.volume = 2.0
    assert clip.volume == 2.0
    # keyframe-style dict
    clip2 = clip_from_dict({'_type': 'AMFile', 'id': 2, 'start': 0, 'duration': 100,
                            'parameters': {'volume': {'type': 'float', 'defaultValue': 0.5, 'keyframes': []}}})
    assert clip2.volume == 0.5


def test_clip_volume_validation():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100})
    with pytest.raises(ValueError, match='volume must be >= 0.0'):
        clip.volume = -0.5




# ---------------------------------------------------------------------------
# Project.set_canvas_size
# ---------------------------------------------------------------------------

def test_set_canvas_size():
    from camtasia.project import Project
    from pathlib import Path
    from unittest.mock import patch
    proj = Project.__new__(Project)
    proj._data = {
        'sourceBin': [],
        'timeline': {
            'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
            'trackAttributes': [],
        },
        'editRate': 30,
    }
    proj._file_path = Path('/tmp/fake.tscproj')
    proj._encoding = 'utf-8'
    proj.set_canvas_size(3840, 2160)
    assert proj.width == 3840
    assert proj.height == 2160




# ---------------------------------------------------------------------------
# BaseClip.set_opacity_fade
# ---------------------------------------------------------------------------

def test_set_opacity_fade():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import seconds_to_ticks
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 9000})
    result = clip.set_opacity_fade(1.0, 0.0, 3.0)
    assert result is clip  # returns self
    params = clip._data['parameters']['opacity']
    assert params['defaultValue'] == 1.0
    assert len(params['keyframes']) == 1
    assert params['keyframes'][0]['value'] == 0.0  # target value
    # without duration_seconds — uses clip duration
    clip2 = clip_from_dict({'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 9000})
    clip2.set_opacity_fade(0.5, 1.0)
    assert clip2._data['parameters']['opacity']['defaultValue'] == 0.5




# ---------------------------------------------------------------------------
# BaseClip.set_volume_fade
# ---------------------------------------------------------------------------

def test_set_volume_fade():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 9000})
    result = clip.set_volume_fade(1.0, 0.0, 3.0)
    assert result is clip
    params = clip._data['parameters']['volume']
    assert params['defaultValue'] == 1.0
    assert len(params['keyframes']) == 1
    assert params['keyframes'][0]['value'] == 0.0  # target value




# ---------------------------------------------------------------------------
# BaseClip.set_position_keyframes
# ---------------------------------------------------------------------------

def test_set_position_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_position_keyframes([(0.0, 100, 200), (2.0, 300, 400)])
    assert result is clip  # fluent return
    params = clip._data['parameters']
    assert params['translation0']['defaultValue'] == 300
    assert params['translation1']['defaultValue'] == 400
    assert len(params['translation0']['keyframes']) == 2
    assert len(params['translation1']['keyframes']) == 2
    kf_x = params['translation0']['keyframes'][1]
    assert kf_x['value'] == 300
    assert kf_x['time'] == t(2.0)
    kf_y = params['translation1']['keyframes'][1]
    assert kf_y['value'] == 400




# ---------------------------------------------------------------------------
# BaseClip.set_scale_keyframes
# ---------------------------------------------------------------------------

def test_set_scale_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_scale_keyframes([(0.0, 1.0), (3.0, 2.5)])
    assert result is clip
    params = clip._data['parameters']
    assert params['scale0']['defaultValue'] == 2.5
    assert params['scale1']['defaultValue'] == 2.5
    assert len(params['scale0']['keyframes']) == 2
    kf = params['scale0']['keyframes'][1]
    assert kf['value'] == 2.5
    assert kf['time'] == t(3.0)
    # scale0 and scale1 should have independent lists
    params['scale0']['keyframes'].append({'extra': True})
    assert len(params['scale1']['keyframes']) == 2




# ---------------------------------------------------------------------------
# BaseClip.set_rotation_keyframes
# ---------------------------------------------------------------------------

def test_set_rotation_keyframes():
    import math
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_rotation_keyframes([(0.0, 0), (2.0, 90), (5.0, 180)])
    assert result is clip  # fluent
    params = clip._data['parameters']
    rot = params['rotation2']
    assert rot['type'] == 'double'
    assert rot['defaultValue'] == pytest.approx(math.radians(180))
    assert len(rot['keyframes']) == 3
    assert rot['keyframes'][1]['value'] == pytest.approx(math.radians(90))
    assert rot['keyframes'][1]['time'] == t(2.0)
    assert rot['keyframes'][2]['value'] == pytest.approx(math.radians(180))




# ---------------------------------------------------------------------------
# BaseClip.set_crop_keyframes
# ---------------------------------------------------------------------------

def test_set_crop_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    result = clip.set_crop_keyframes([
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (3.0, 0.1, 0.2, 0.3, 0.4),
    ])
    assert result is clip  # fluent
    params = clip._data['parameters']
    for i, name in enumerate(['geometryCrop0', 'geometryCrop1', 'geometryCrop2', 'geometryCrop3']):
        assert name in params
        assert params[name]['type'] == 'double'
        assert len(params[name]['keyframes']) == 2
        assert params[name]['keyframes'][0]['value'] == 0.0
    # Check second keyframe values: left=0.1, top=0.2, right=0.3, bottom=0.4
    assert params['geometryCrop0']['keyframes'][1]['value'] == pytest.approx(0.1)
    assert params['geometryCrop1']['keyframes'][1]['value'] == pytest.approx(0.2)
    assert params['geometryCrop2']['keyframes'][1]['value'] == pytest.approx(0.3)
    assert params['geometryCrop3']['keyframes'][1]['value'] == pytest.approx(0.4)
    assert params['geometryCrop0']['keyframes'][1]['time'] == t(3.0)




# ---------------------------------------------------------------------------
# BaseClip.animate
# ---------------------------------------------------------------------------

def test_animate_fade_in():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0), 'mediaDuration': seconds_to_ticks(10.0)})
    result = clip.animate(fade_in=2.0)
    assert result is clip
    # _add_opacity_track writes to both parameters.opacity and animationTracks.visual
    assert 'opacity' in clip._data.get('parameters', {})
    assert 'animationTracks' in clip._data


def test_animate_scale():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(scale_from=0.5, scale_to=1.5)
    params = clip._data['parameters']
    assert params['scale0']['keyframes'][0]['value'] == 0.5
    assert params['scale0']['keyframes'][1]['value'] == 1.5
    assert params['scale0']['keyframes'][1]['time'] == seconds_to_ticks(10.0)


def test_animate_move():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(move_from=(0, 0), move_to=(100, 200))
    params = clip._data['parameters']
    assert params['translation0']['keyframes'][0]['value'] == 0
    assert params['translation0']['keyframes'][1]['value'] == 100
    assert params['translation1']['keyframes'][1]['value'] == 200
    assert params['translation0']['keyframes'][1]['time'] == seconds_to_ticks(10.0)


def test_animate_combined():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(fade_in=1.0, scale_from=0.0, scale_to=1.0, move_from=(0, 0), move_to=(50, 50))
    params = clip._data['parameters']
    # fade
    assert params['opacity']['keyframes'][0]['value'] == 1.0  # fade-in target (defaultValue is 0.0)
    assert len(params["opacity"]["keyframes"]) >= 1
    # scale
    assert params['scale0']['keyframes'][0]['value'] == 0.0
    assert params['scale0']['keyframes'][1]['value'] == 1.0
    # position
    assert params['translation0']['keyframes'][1]['value'] == 50
    assert params['translation1']['keyframes'][1]['value'] == 50


def test_animate_chaining():
    from camtasia.timeline.clips import clip_from_dict
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    result = clip.animate(fade_in=1.0).animate(scale_from=1.0, scale_to=2.0)
    assert result is clip
    params = clip._data['parameters']
    assert 'opacity' in params
    assert 'scale0' in params


def test_animate_fade_out():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import seconds_to_ticks
    data = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(5.0), 'mediaDuration': seconds_to_ticks(5.0), 'parameters': {}}
    clip = clip_from_dict(data)
    clip.animate(fade_out=1.0)
    # fade() writes to animationTracks
    assert 'animationTracks' in data or 'opacity' in data.get('parameters', {})




# ---------------------------------------------------------------------------
# BaseClip.speed / set_speed
# ---------------------------------------------------------------------------

def test_clip_speed_get_set():
    media = {'id': 1, 'start': 0, 'duration': 100}
    t = _make_track([media])
    clip = list(t.clips)[0]
    assert clip.speed == 1  # default
    result = clip.set_speed(2.0)
    assert clip.speed == 2.0
    assert result is clip  # fluent return


def test_clip_speed_validation():
    media = {'id': 1, 'start': 0, 'duration': 100}
    t = _make_track([media])
    clip = list(t.clips)[0]
    with pytest.raises(ValueError):
        clip.set_speed(0)
    with pytest.raises(ValueError):
        clip.set_speed(-1)




# ---------------------------------------------------------------------------
# BaseClip.effect_names
# ---------------------------------------------------------------------------

def test_clip_effect_names():
    medias = [
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100, 'effects': [
            {'effectName': 'Blur'},
            {'effectName': 'Glow'},
        ]},
        {'id': 2, 'start': 100, 'duration': 100},
    ]
    track = _make_track(medias)
    clips = list(track.clips)
    assert clips[0].effect_names == ['Blur', 'Glow']
    assert clips[1].effect_names == []




# ---------------------------------------------------------------------------
# BaseClip.is_visible / Track.visible_clips / Project.has_audio / has_video
# ---------------------------------------------------------------------------

def test_is_visible():
    audio = _make_track([{'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100}])
    video = _make_track([{'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100}])
    assert list(audio.clips)[0].is_visible is False
    assert list(video.clips)[0].is_visible is True


def test_visible_clips():
    medias = [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100},
        {'id': 3, '_type': 'IMFile', 'start': 200, 'duration': 100},
    ]
    track = _make_track(medias)
    visible = track.visible_clips
    assert len(visible) == 2
    assert all(c.is_visible for c in visible)


def test_new_callout_shapes():
    from camtasia.types import CalloutShape
    assert CalloutShape.SHAPE_ELLIPSE.value == 'shape-ellipse'
    assert CalloutShape.SHAPE_TRIANGLE.value == 'shape-triangle'
    assert CalloutShape.TEXT.value == 'text'
    assert CalloutShape.TEXT_RECTANGLE.value == 'text-rectangle'
    assert CalloutShape.SHAPE_RECTANGLE.value == 'shape-rectangle'




# ---------------------------------------------------------------------------
# Track.clip_at_index
# ---------------------------------------------------------------------------

def test_clip_at_index():
    medias = [
        {'id': 2, '_type': 'AMFile', 'start': 200, 'duration': 100},
        {'id': 1, '_type': 'VMFile', 'start': 50, 'duration': 100},
        {'id': 3, '_type': 'IMFile', 'start': 500, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    first_clip = track.clip_at_index(0)
    assert first_clip.id == 1  # start=50 is earliest
    second_clip = track.clip_at_index(1)
    assert second_clip.id == 2  # start=200
    third_clip = track.clip_at_index(2)
    assert third_clip.id == 3  # start=500


def test_clip_at_index_out_of_range():
    track = _make_track(medias=[
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
    ])
    with pytest.raises(IndexError, match='clip index 5 out of range'):
        track.clip_at_index(5)
    with pytest.raises(IndexError, match='clip index -1 out of range'):
        track.clip_at_index(-1)




# ---------------------------------------------------------------------------
# BaseClip.source_id
# ---------------------------------------------------------------------------

def test_source_id_replaces_source_path():
    from camtasia.timeline.clips import clip_from_dict
    clip_with_src = clip_from_dict({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'src': '/media/video.mp4',
    })
    assert clip_with_src.source_id == '/media/video.mp4'

    clip_without_src = clip_from_dict({
        'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 100,
    })
    assert clip_without_src.source_id is None




# ---------------------------------------------------------------------------
# BaseClip.media_start_seconds
# ---------------------------------------------------------------------------

def test_media_start_seconds():
    from camtasia.timeline.clips import clip_from_dict
    from camtasia.timing import EDIT_RATE
    media_start_ticks: int = EDIT_RATE * 5  # exactly 5 seconds
    clip = clip_from_dict({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'mediaStart': media_start_ticks,
    })
    assert clip.media_start_seconds == pytest.approx(5.0)




# ---------------------------------------------------------------------------
# clip_before / clip_after / overlaps_with / distance_to
# ---------------------------------------------------------------------------

def test_clip_before():
    """clip_before returns the last clip ending before the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(3), 'duration': seconds_to_ticks(1)},
    ])
    clip = track.clip_before(3.0)
    assert clip is not None
    assert clip.id == 1


def test_clip_before_none():
    """clip_before returns None when no clip ends before the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)},
    ])
    assert track.clip_before(1.0) is None


def test_clip_after():
    """clip_after returns the first clip starting after the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)},
    ])
    clip = track.clip_after(3.0)
    assert clip is not None
    assert clip.id == 2


def test_clip_after_none():
    """clip_after returns None when no clip starts after the given time."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(1)},
    ])
    assert track.clip_after(5.0) is None


def test_overlaps_with_true():
    """overlaps_with returns True for overlapping clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(2), 'duration': seconds_to_ticks(2)})
    assert clip_a.overlaps_with(clip_b) is True


def test_overlaps_with_false():
    """overlaps_with returns False for non-overlapping clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(3), 'duration': seconds_to_ticks(1)})
    assert clip_a.overlaps_with(clip_b) is False


def test_distance_to_gap():
    """distance_to returns positive seconds for a gap between clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)})
    assert clip_a.distance_to(clip_b) == pytest.approx(3.0)


def test_distance_to_overlap():
    """distance_to returns negative seconds for overlapping clips."""
    from camtasia.timeline.clips import BaseClip
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(2), 'duration': seconds_to_ticks(2)})
    assert clip_a.distance_to(clip_b) == pytest.approx(-1.0)




# ---------------------------------------------------------------------------
# Project.duration_formatted
# ---------------------------------------------------------------------------

def test_duration_formatted():
    """duration_formatted returns MM:SS string."""
    from unittest.mock import PropertyMock, patch
    from camtasia.project import Project

    with patch.object(Project, 'duration_seconds', new_callable=PropertyMock, return_value=125.7):
        proj = object.__new__(Project)
        assert proj.duration_formatted == '2:05'




# ---------------------------------------------------------------------------
# Track.clip_count_by_type
# ---------------------------------------------------------------------------

def test_clip_count_by_type():
    medias = [
        {'id': 1, 'start': 0, 'duration': 100, '_type': 'VMFile'},
        {'id': 2, 'start': 100, 'duration': 100, '_type': 'VMFile'},
        {'id': 3, 'start': 200, 'duration': 100, '_type': 'Callout'},
    ]
    track = _make_track(medias=medias)
    counts: dict[str, int] = track.clip_count_by_type
    assert counts['VMFile'] == 2
    assert counts['Callout'] == 1
    assert len(counts) == 2




# ---------------------------------------------------------------------------
# BaseClip.has_keyframes
# ---------------------------------------------------------------------------

def test_has_keyframes_true():
    media = {
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {
            'opacity': {
                'type': 'double',
                'defaultValue': 1.0,
                'keyframes': [{'time': 0, 'value': 1.0}],
            },
        },
    }
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    assert clip.has_keyframes is True


def test_has_keyframes_false():
    media = {
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {
            'opacity': 0.5,
        },
    }
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    assert clip.has_keyframes is False




# ---------------------------------------------------------------------------
# BaseClip.keyframe_count
# ---------------------------------------------------------------------------

def test_keyframe_count():
    media: dict[str, Any] = {
        'id': 1,
        'start': 0,
        'duration': 300,
        'parameters': {
            'scale': {
                'keyframes': [{'time': 0, 'value': 1.0}, {'time': 100, 'value': 2.0}],
            },
            'opacity': {
                'keyframes': [{'time': 0, 'value': 1.0}],
            },
            'volume': 0.8,  # not a keyframed parameter
        },
    }
    track = _make_track(medias=[media])
    clip = list(track.clips)[0]
    assert clip.keyframe_count == 3




# ---------------------------------------------------------------------------
# BaseClip.is_at_origin
# ---------------------------------------------------------------------------

def test_is_at_origin():
    at_zero: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100}
    not_zero: dict[str, Any] = {'id': 2, 'start': 500, 'duration': 100}
    track = _make_track(medias=[at_zero, not_zero])
    clips = list(track.clips)
    assert clips[0].is_at_origin is True
    assert clips[1].is_at_origin is False




# ---------------------------------------------------------------------------
# BaseClip.copy_timing_from
# ---------------------------------------------------------------------------

def test_copy_timing_from():
    from camtasia.timeline.clips.base import BaseClip
    source = BaseClip({'id': 1, '_type': 'VMFile', 'start': 1000, 'duration': 5000})
    target = BaseClip({'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100})
    result = target.copy_timing_from(source)
    assert target.start == 1000
    assert target.duration == 5000
    assert result is target  # returns self for chaining




# ---------------------------------------------------------------------------
# BaseClip.matches_type
# ---------------------------------------------------------------------------

def test_matches_type():
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.types import ClipType
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100})
    assert clip.matches_type('VMFile') is True
    assert clip.matches_type(ClipType.VIDEO) is True
    assert clip.matches_type('AMFile') is False
    assert clip.matches_type(ClipType.AUDIO) is False




# ---------------------------------------------------------------------------
# BaseClip.snap_to_seconds
# ---------------------------------------------------------------------------

def test_snap_to_seconds():
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timing import seconds_to_ticks
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2.0)})
    result = clip.snap_to_seconds(5.0)
    assert clip.start == seconds_to_ticks(5.0)
    assert result is clip  # returns self for chaining




# ---------------------------------------------------------------------------
# BaseClip.is_longer_than
# ---------------------------------------------------------------------------

def test_is_longer_than():
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timing import seconds_to_ticks
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3.0)})
    assert clip.is_longer_than(2.0) is True
    assert clip.is_longer_than(3.0) is False
    assert clip.is_longer_than(4.0) is False




# ---------------------------------------------------------------------------
# BaseClip.is_shorter_than
# ---------------------------------------------------------------------------

def test_is_shorter_than():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2.0)})
    assert clip.is_shorter_than(3.0) is True
    assert clip.is_shorter_than(2.0) is False
    assert clip.is_shorter_than(1.0) is False




# ---------------------------------------------------------------------------
# BaseClip.set_source
# ---------------------------------------------------------------------------

def test_set_source():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, 'src': 10, '_type': 'AMFile', 'start': 0, 'duration': 100})
    result = clip.set_source(42)
    assert clip.source_id == 42
    assert result is clip  # fluent return




# ---------------------------------------------------------------------------
# BaseClip.set_metadata / get_metadata
# ---------------------------------------------------------------------------

def test_set_get_metadata():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100})
    # get_metadata returns default when key missing
    assert clip.get_metadata('author') is None
    assert clip.get_metadata('author', 'unknown') == 'unknown'
    # set_metadata returns self (fluent) and stores value
    result = clip.set_metadata('author', 'Alice')
    assert result is clip
    assert clip.get_metadata('author') == 'Alice'
    # metadata property reflects the change
    assert clip.metadata == {'author': 'Alice'}




# ---------------------------------------------------------------------------
# Track.clip_ids_sorted
# ---------------------------------------------------------------------------

def test_clip_ids_sorted():
    track = _make_track([
        {'id': 3, 'start': 300, 'duration': 100},
        {'id': 1, 'start': 100, 'duration': 100},
        {'id': 2, 'start': 200, 'duration': 100},
    ])
    assert track.clip_ids_sorted == [1, 2, 3]
    # Original clip_ids preserves insertion order
    assert track.clip_ids == [3, 1, 2]




# ---------------------------------------------------------------------------
# BaseClip.is_muted
# ---------------------------------------------------------------------------

def test_clip_is_muted():
    media = {'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 0.0}}
    track = _make_track(medias=[media])
    muted_clip = list(track.clips)[0]
    assert muted_clip.is_muted is True

    audible_media = {'id': 2, 'start': 200, 'duration': 100, 'attributes': {'gain': 0.75}}
    audible_track = _make_track(medias=[audible_media])
    audible_clip = list(audible_track.clips)[0]
    assert audible_clip.is_muted is False




# ---------------------------------------------------------------------------
# Track.muted_clips
# ---------------------------------------------------------------------------

def test_muted_clips():
    medias = [
        {'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 0.0}},
        {'id': 2, 'start': 200, 'duration': 100, 'attributes': {'gain': 1.0}},
        {'id': 3, 'start': 400, 'duration': 100, 'attributes': {'gain': 0.0}},
    ]
    track = _make_track(medias=medias)
    muted = track.muted_clips
    assert len(muted) == 2
    muted_ids: list[int] = [clip.id for clip in muted]
    assert muted_ids == [1, 3]




# ---------------------------------------------------------------------------
# BaseClip.set_start_seconds
# ---------------------------------------------------------------------------

def test_set_start_seconds_updates_data():
    """set_start_seconds writes the correct tick value to _data['start']."""
    from camtasia.timeline.clips.base import BaseClip
    clip_data: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100, 'type': 'VMFile', 'parameters': {}, 'effects': [], 'attributes': {'ident': ''}}
    clip: BaseClip = BaseClip(clip_data)
    result = clip.set_start_seconds(2.0)
    assert clip._data['start'] == seconds_to_ticks(2.0)
    assert result is clip  # returns self for chaining




# ---------------------------------------------------------------------------
# BaseClip.set_duration_seconds
# ---------------------------------------------------------------------------

def test_set_duration_seconds_updates_data():
    """set_duration_seconds writes the correct tick value to _data['duration']."""
    from camtasia.timeline.clips.base import BaseClip
    clip_data: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100, 'type': 'VMFile', 'parameters': {}, 'effects': [], 'attributes': {'ident': ''}}
    clip: BaseClip = BaseClip(clip_data)
    result = clip.set_duration_seconds(5.0)
    assert clip._data['duration'] == seconds_to_ticks(5.0)
    assert result is clip  # returns self for chaining




# ---------------------------------------------------------------------------
# BaseClip.is_effect_applied
# ---------------------------------------------------------------------------

def test_is_effect_applied_true():
    """is_effect_applied returns True when the effect is present."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'DropShadow'}],
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied('DropShadow') is True


def test_is_effect_applied_false():
    """is_effect_applied returns False when the effect is absent."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'Glow'}],
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied('DropShadow') is False


def test_is_effect_applied_no_effects():
    """is_effect_applied returns False when clip has no effects list."""
    clip_data: dict = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied('DropShadow') is False


def test_is_effect_applied_with_enum():
    """is_effect_applied works with EffectName enum values."""
    from camtasia.types import EffectName
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'DropShadow'}],
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    assert clip.is_effect_applied(EffectName.DROP_SHADOW) is True




# ---------------------------------------------------------------------------
# BaseClip.clear_metadata
# ---------------------------------------------------------------------------

def test_clear_metadata_removes_all():
    """clear_metadata empties the metadata dict."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'metadata': {'presetName': 'Intro', 'author': 'Test'},
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    result = clip.clear_metadata()
    assert clip.metadata == {}
    assert clip_data['metadata'] == {}


def test_clear_metadata_returns_self():
    """clear_metadata returns self for chaining."""
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'metadata': {'key': 'value'},
    }
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    returned: BaseClip = clip.clear_metadata()
    assert returned is clip


def test_clear_metadata_on_empty():
    """clear_metadata works when metadata is already empty or absent."""
    clip_data: dict = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100}
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip(clip_data)
    clip.clear_metadata()
    assert clip_data['metadata'] == {}



# ── is_silent for UnifiedMedia ──────────────────────────────────────


class TestIsSilentUnifiedMedia:
    def test_unified_media_silent_when_gain_zero(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip({
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'audio': {'attributes': {'gain': 0.0}},
        })
        assert clip.is_silent is True

    def test_unified_media_not_silent_when_gain_nonzero(self):
        from camtasia.timeline.clips.base import BaseClip
        clip = BaseClip({
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'audio': {'attributes': {'gain': 0.8}},
        })
        assert clip.is_silent is False

    def test_non_unified_silent_when_gain_zero(self):
        clip = AMFile(_amfile_dict(attributes={'ident': '', 'gain': 0.0, 'mixToMono': False, 'loudnessNormalization': False}))
        assert clip.is_silent is True


# ── add_lut_effect, add_media_matte, add_motion_blur, add_emphasize ─


class TestEffectAddMethods:
    def _clip(self):
        return VMFile(_base_clip_dict(effects=[]))

    def test_add_lut_effect(self):
        clip = self._clip()
        result = clip.add_lut_effect(intensity=0.5)
        assert result is clip
        eff = clip._data['effects'][-1]
        assert eff['effectName'] == 'LutEffect'
        assert eff['parameters']['lut_intensity'] == 0.5

    def test_add_media_matte(self):
        clip = self._clip()
        result = clip.add_media_matte(intensity=0.7, matte_mode=2)
        assert result is clip
        eff = clip._data['effects'][-1]
        assert eff['effectName'] == 'MediaMatte'
        assert eff['parameters']['matteMode'] == 2

    def test_add_motion_blur(self):
        clip = self._clip()
        result = clip.add_motion_blur(intensity=0.9)
        assert result is clip
        eff = clip._data['effects'][-1]
        assert eff['effectName'] == 'MotionBlur'

    def test_add_emphasize(self):
        clip = self._clip()
        result = clip.add_emphasize(amount=0.3)
        assert result is clip
        eff = clip._data['effects'][-1]
        assert eff['effectName'] == 'Emphasize'
        assert eff['parameters']['emphasizeAmount'] == 0.3

    def test_add_blend_mode(self):
        clip = self._clip()
        result = clip.add_blend_mode(mode=3, intensity=0.8)
        assert result is clip
        eff = clip._data['effects'][-1]
        assert eff['effectName'] == 'BlendModeEffect'
        assert eff['parameters']['mode'] == 3


# ── is_longer_than / apply_if ───────────────────────────────────────


class TestClipPredicates:
    def test_is_longer_than(self):
        clip = AMFile(_amfile_dict())
        assert clip.is_longer_than(0.0) is True

    def test_apply_if_true(self):
        clip = AMFile(_amfile_dict())
        called = []
        clip.apply_if(lambda c: True, lambda c: called.append(c))
        assert len(called) == 1

    def test_apply_if_false(self):
        clip = AMFile(_amfile_dict())
        called = []
        clip.apply_if(lambda c: False, lambda c: called.append(c))
        assert len(called) == 0


class TestRemoveEffectByName:
    def test_removes_matching_effects(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0, 5.0)
        clip._data['effects'] = [
            {'effectName': 'Glow', 'parameters': {}},
            {'effectName': 'Border', 'parameters': {}},
            {'effectName': 'Glow', 'parameters': {}},
        ]
        actual_removed = clip.remove_effect_by_name('Glow')
        assert actual_removed == 2
        assert len(clip._data['effects']) == 1
        assert clip._data['effects'][0]['effectName'] == 'Border'


class TestDuplicateEffectsTo:
    def test_copies_effects_to_target(self, project):
        track = project.timeline.tracks[0]
        source = track.add_video(0, 0, 5.0)
        target = track.add_video(0, 5.0, 5.0)
        source._data['effects'] = [{'effectName': 'Glow', 'parameters': {}}]
        source.duplicate_effects_to(target)
        assert len(target._data.get('effects', [])) == 1
        assert target._data['effects'][0]['effectName'] == 'Glow'


class TestResetTransforms:
    def test_resets_position_scale_rotation(self, project):
        track = project.timeline.tracks[0]
        clip = track.add_video(0, 0, 5.0)
        clip.move_to(100, 200)
        clip.scale_to(2.0)
        clip.rotation = 45.0
        actual_result = clip.reset_transforms()
        assert actual_result is clip
        assert clip.translation == (0, 0)
        assert clip.scale == (1.0, 1.0)
        assert clip.rotation == 0.0
