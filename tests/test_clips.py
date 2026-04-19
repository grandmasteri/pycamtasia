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
