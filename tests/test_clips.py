"""Tests for camtasia.timeline.clips.base — BaseClip and clip_from_dict factory."""
from __future__ import annotations

from fractions import Fraction
import math
from pathlib import Path
from typing import Any
from unittest.mock import PropertyMock, patch
import warnings

import pytest

from camtasia.effects.base import Effect
from camtasia.project import Project
from camtasia.timeline.clips import (
    EDIT_RATE,
    AMFile,
    BaseClip,
    Callout,
    Group,
    IMFile,
    ScreenIMFile,
    ScreenVMFile,
    StitchedMedia,
    VMFile,
    clip_from_dict,
)
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks
from camtasia.types import CalloutShape, ClipType, EffectName

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


def _make_track(medias=None, name='T'):
    """Build a minimal Track from raw dicts."""
    data = {'trackIndex': 0, 'medias': medias or []}
    attrs = {'ident': name}
    return Track(attrs, data)


def _base(**kw) -> dict:
    d = {
        "id": 1, "_type": "AMFile", "src": 1,
        "start": 0, "duration": EDIT_RATE * 10,
        "mediaStart": 0, "mediaDuration": EDIT_RATE * 10, "scalar": 1,
    }
    d.update(kw)
    return d


def _coverage_clip(extra=None, **kw):
    d = {'id': 1, '_type': 'VMFile', 'src': 0, 'start': 0, 'duration': 100,
         'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
         'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
         'animationTracks': {}}
    if extra:
        d.update(extra)
    d.update(kw)
    return d


# ------------------------------------------------------------------
# clip_from_dict factory dispatch
# ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("type_str", "expected_class"),
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
    assert clip.scalar == Fraction(51, 101)


def test_baseclip_scalar_parses_int() -> None:
    data = _base_clip_dict(scalar=1)
    clip = BaseClip(data)
    assert clip.scalar == Fraction(1)


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
    ("input_seconds", "expected_ticks"),
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
    assert clip.start == expected_ticks


@pytest.mark.parametrize(
    ("input_seconds", "expected_ticks"),
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
    assert clip.duration == expected_ticks


@pytest.mark.parametrize("input_seconds", [0.0, 1.0, 7.33], ids=["zero", "one", "fractional"])
def test_start_seconds_roundtrip(input_seconds: float) -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.start_seconds = input_seconds
    assert clip.start_seconds == pytest.approx(input_seconds)


@pytest.mark.parametrize("input_seconds", [0.0, 1.0, 4.87], ids=["zero", "one", "fractional"])
def test_duration_seconds_roundtrip(input_seconds: float) -> None:
    data = _base_clip_dict()
    clip = BaseClip(data)
    clip.duration_seconds = input_seconds
    assert clip.duration_seconds == pytest.approx(input_seconds)


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
        assert 'endTime' in visual[0]


class TestOpacityEmptyKeyframes:
    def test_empty_keyframes_returns_none(self):
        data = {
            'id': 1, '_type': 'VMFile', 'src': 0,
            'start': 0, 'duration': 100, 'mediaStart': 0,
            'parameters': {'opacity': {'keyframes': []}},
        }
        clip = BaseClip(data)
        assert clip._get_existing_opacity_keyframes() is None


# ------------------------------------------------------------------
# BaseClip.describe
# ------------------------------------------------------------------

def test_clip_describe():
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


# ------------------------------------------------------------------
# Clip type-check properties
# ------------------------------------------------------------------

@pytest.mark.parametrize(("type_str", "prop", "expected"), [
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
    data = {'_type': type_str, 'id': 1, 'start': 0, 'duration': 100,
            'mediaSource': {}, 'parameters': {}, 'effects': [],
            'metadata': {}, 'animationTracks': {}}
    clip = clip_from_dict(data)
    assert getattr(clip, prop) is expected


# ------------------------------------------------------------------
# BaseClip.end_seconds
# ------------------------------------------------------------------

def test_end_seconds():
    start = EDIT_RATE * 2
    dur = EDIT_RATE * 3
    clip = BaseClip({'_type': 'AMFile', 'id': 1, 'start': start,
                     'duration': dur, 'metadata': {},
                     'animationTracks': {}})
    assert clip.end_seconds == pytest.approx(5.0)


# ------------------------------------------------------------------
# BaseClip.time_range
# ------------------------------------------------------------------

def test_time_range():
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


# ------------------------------------------------------------------
# BaseClip.to_dict
# ------------------------------------------------------------------

def test_clip_to_dict():
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

    clip2 = BaseClip({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': start})
    d2 = clip2.to_dict()
    assert 'source_id' not in d2
    assert 'effects' not in d2


# ------------------------------------------------------------------
# BaseClip.is_at
# ------------------------------------------------------------------

def test_clip_is_at():
    start = seconds_to_ticks(2.0)
    dur = seconds_to_ticks(3.0)
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': start, 'duration': dur})
    assert clip.is_at(2.0) is True
    assert clip.is_at(3.5) is True
    assert clip.is_at(4.99) is True
    assert clip.is_at(5.0) is False
    assert clip.is_at(1.0) is False


# ------------------------------------------------------------------
# BaseClip.opacity
# ------------------------------------------------------------------

def test_clip_opacity_get_set():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.opacity == 1.0
    clip.opacity = 0.5
    assert clip.opacity == 0.5
    clip2 = clip_from_dict({'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 100,
                            'parameters': {'opacity': {'type': 'float', 'defaultValue': 0.75, 'keyframes': []}}})
    assert clip2.opacity == 0.75


def test_clip_opacity_validation():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100})
    with pytest.raises(ValueError, match=r'opacity must be 0\.0-1\.0'):
        clip.opacity = 1.5
    with pytest.raises(ValueError, match=r'opacity must be 0\.0-1\.0'):
        clip.opacity = -0.1


# ------------------------------------------------------------------
# BaseClip.volume
# ------------------------------------------------------------------

def test_clip_volume_get_set():
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100})
    assert clip.volume == 1.0
    clip.volume = 2.0
    assert clip.volume == 2.0
    clip2 = clip_from_dict({'_type': 'AMFile', 'id': 2, 'start': 0, 'duration': 100,
                            'parameters': {'volume': {'type': 'float', 'defaultValue': 0.5, 'keyframes': []}}})
    assert clip2.volume == 0.5


def test_clip_volume_validation():
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100})
    with pytest.raises(ValueError, match=r'volume must be >= 0\.0'):
        clip.volume = -0.5


# ------------------------------------------------------------------
# Project.set_canvas_size
# ------------------------------------------------------------------

def test_set_canvas_size():
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


# ------------------------------------------------------------------
# BaseClip.set_opacity_fade
# ------------------------------------------------------------------

def test_set_opacity_fade():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 9000})
    result = clip.set_opacity_fade(1.0, 0.0, 3.0)
    assert result is clip
    params = clip._data['parameters']['opacity']
    assert params['defaultValue'] == 1.0
    assert params['keyframes'][0]['value'] == 0.0
    clip2 = clip_from_dict({'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 9000})
    clip2.set_opacity_fade(0.5, 1.0)
    assert clip2._data['parameters']['opacity']['defaultValue'] == 0.5


# ------------------------------------------------------------------
# BaseClip.set_volume_fade
# ------------------------------------------------------------------

def test_set_volume_fade():
    clip = clip_from_dict({'_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 9000})
    result = clip.set_volume_fade(1.0, 0.0, 3.0)
    assert result is clip
    params = clip._data['parameters']['volume']
    assert params['defaultValue'] == 1.0
    assert params['keyframes'][0]['value'] == 0.0


# ------------------------------------------------------------------
# BaseClip.set_position_keyframes
# ------------------------------------------------------------------

def test_set_position_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    result = clip.set_position_keyframes([(0.0, 100, 200), (2.0, 300, 400)])
    assert result is clip
    params = clip._data['parameters']
    assert params['translation0']['defaultValue'] == 300
    assert params['translation1']['defaultValue'] == 400
    kf_x = params['translation0']['keyframes'][1]
    assert kf_x['value'] == 300
    assert kf_x['time'] == t(2.0)
    kf_y = params['translation1']['keyframes'][1]
    assert kf_y['value'] == 400


def test_set_position_keyframes_creates_animation_tracks_visual():
    """set_position_keyframes must also populate animationTracks.visual to match real Camtasia projects."""
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.set_position_keyframes([(0.0, 100, 200), (2.0, 300, 400)])
    visual = clip._data['animationTracks']['visual']
    # 2 keyframe times → 2 visual segments (deduplicated across x/y parallel params)
    assert len(visual) == 2
    assert visual[0]['time'] == 0 if 'time' in visual[0] else visual[0]['range'][0] == 0
    # Each segment has endTime/duration/range/interp
    for seg in visual:
        assert 'endTime' in seg
        assert 'duration' in seg
        assert 'range' in seg


def test_set_scale_keyframes_creates_animation_tracks_visual():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.set_scale_keyframes([(0.0, 1.0), (1.5, 2.0)])
    visual = clip._data['animationTracks']['visual']
    assert len(visual) == 2


def test_set_rotation_keyframes_creates_animation_tracks_visual():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.set_rotation_keyframes([(0.0, 0.0), (1.0, 90.0)])
    visual = clip._data['animationTracks']['visual']
    assert len(visual) == 2


def test_set_crop_keyframes_creates_animation_tracks_visual():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.set_crop_keyframes([(0.0, 0.0, 0.0, 0.0, 0.0), (1.0, 0.1, 0.1, 0.1, 0.1)])
    visual = clip._data['animationTracks']['visual']
    # 4 crop params but deduped to 2 unique times
    assert len(visual) == 2


def test_add_keyframe_visual_param_creates_animation_tracks_visual():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.add_keyframe('translation0', 1.0, 50.0, duration_seconds=0.5)
    visual = clip._data['animationTracks']['visual']
    assert len(visual) == 1


def test_add_keyframe_non_visual_param_does_not_create_animation_tracks():
    """Non-visual params (e.g., volume) should NOT create animationTracks.visual entries."""
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.add_keyframe('volume', 1.0, 0.5)
    visual = clip._data.get('animationTracks', {}).get('visual', [])
    assert len(visual) == 0


# ------------------------------------------------------------------
# BaseClip.set_scale_keyframes
# ------------------------------------------------------------------

def test_set_scale_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    result = clip.set_scale_keyframes([(0.0, 1.0), (3.0, 2.5)])
    assert result is clip
    params = clip._data['parameters']
    assert params['scale0']['defaultValue'] == 2.5
    assert params['scale1']['defaultValue'] == 2.5
    kf = params['scale0']['keyframes'][1]
    assert kf['value'] == 2.5
    assert kf['time'] == t(3.0)
    params['scale0']['keyframes'].append({'extra': True})
    assert [kf['value'] for kf in params['scale1']['keyframes']] == [1.0, 2.5]


# ------------------------------------------------------------------
# BaseClip.set_rotation_keyframes
# ------------------------------------------------------------------

def test_set_rotation_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    result = clip.set_rotation_keyframes([(0.0, 0), (2.0, 90), (5.0, 180)])
    assert result is clip
    params = clip._data['parameters']
    rot = params['rotation2']
    assert rot['type'] == 'double'
    assert rot['defaultValue'] == pytest.approx(math.radians(180))
    assert rot['keyframes'][1]['value'] == pytest.approx(math.radians(90))
    assert rot['keyframes'][1]['time'] == t(2.0)
    assert rot['keyframes'][2]['value'] == pytest.approx(math.radians(180))


# ------------------------------------------------------------------
# BaseClip.set_crop_keyframes
# ------------------------------------------------------------------

def test_set_crop_keyframes():
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    result = clip.set_crop_keyframes([
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (3.0, 0.1, 0.2, 0.3, 0.4),
    ])
    assert result is clip
    params = clip._data['parameters']
    for name in ['geometryCrop0', 'geometryCrop1', 'geometryCrop2', 'geometryCrop3']:
        assert name in params
        assert params[name]['type'] == 'double'
        assert params[name]['keyframes'][0]['value'] == 0.0
    assert params['geometryCrop0']['keyframes'][1]['value'] == pytest.approx(0.1)
    assert params['geometryCrop1']['keyframes'][1]['value'] == pytest.approx(0.2)
    assert params['geometryCrop2']['keyframes'][1]['value'] == pytest.approx(0.3)
    assert params['geometryCrop3']['keyframes'][1]['value'] == pytest.approx(0.4)
    assert params['geometryCrop0']['keyframes'][1]['time'] == t(3.0)


# ------------------------------------------------------------------
# BaseClip.animate
# ------------------------------------------------------------------

def test_animate_fade_in():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0), 'mediaDuration': seconds_to_ticks(10.0)})
    result = clip.animate(fade_in=2.0)
    assert result is clip
    assert 'opacity' in clip._data.get('parameters', {})
    assert 'animationTracks' in clip._data


def test_animate_scale():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(scale_from=0.5, scale_to=1.5)
    params = clip._data['parameters']
    assert params['scale0']['keyframes'][0]['value'] == 0.5
    assert params['scale0']['keyframes'][1]['value'] == 1.5
    assert params['scale0']['keyframes'][1]['time'] == seconds_to_ticks(10.0)


def test_animate_move():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(move_from=(0, 0), move_to=(100, 200))
    params = clip._data['parameters']
    assert params['translation0']['keyframes'][0]['value'] == 0
    assert params['translation0']['keyframes'][1]['value'] == 100
    assert params['translation1']['keyframes'][1]['value'] == 200
    assert params['translation0']['keyframes'][1]['time'] == seconds_to_ticks(10.0)


def test_animate_combined():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    clip.animate(fade_in=1.0, scale_from=0.0, scale_to=1.0, move_from=(0, 0), move_to=(50, 50))
    params = clip._data['parameters']
    assert params['opacity']['keyframes'][0]['value'] == 1.0
    assert params['scale0']['keyframes'][0]['value'] == 0.0
    assert params['scale0']['keyframes'][1]['value'] == 1.0
    assert params['translation0']['keyframes'][1]['value'] == 50
    assert params['translation1']['keyframes'][1]['value'] == 50


def test_animate_chaining():
    clip = clip_from_dict({'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(10.0)})
    result = clip.animate(fade_in=1.0).animate(scale_from=1.0, scale_to=2.0)
    assert result is clip
    params = clip._data['parameters']
    assert 'opacity' in params
    assert 'scale0' in params


def test_animate_fade_out():
    data = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': seconds_to_ticks(5.0), 'mediaDuration': seconds_to_ticks(5.0), 'parameters': {}}
    clip = clip_from_dict(data)
    clip.animate(fade_out=1.0)
    assert 'animationTracks' in data or 'opacity' in data.get('parameters', {})


# ------------------------------------------------------------------
# BaseClip.speed / set_speed
# ------------------------------------------------------------------

def test_clip_speed_get_set():
    media = {'id': 1, 'start': 0, 'duration': 100}
    t = _make_track([media])
    clip = next(iter(t.clips))
    assert clip.speed == 1
    result = clip.set_speed(2.0)
    assert clip.speed == 2.0
    assert result is clip


def test_clip_speed_validation():
    media = {'id': 1, 'start': 0, 'duration': 100}
    t = _make_track([media])
    clip = next(iter(t.clips))
    with pytest.raises(ValueError):
        clip.set_speed(0)
    with pytest.raises(ValueError):
        clip.set_speed(-1)


# ------------------------------------------------------------------
# BaseClip.effect_names
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# BaseClip.is_visible / Track.visible_clips
# ------------------------------------------------------------------

def test_is_visible():
    audio = _make_track([{'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100}])
    video = _make_track([{'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100}])
    assert next(iter(audio.clips)).is_visible is False
    assert next(iter(video.clips)).is_visible is True


def test_visible_clips():
    medias = [
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
        {'id': 2, '_type': 'VMFile', 'start': 100, 'duration': 100},
        {'id': 3, '_type': 'IMFile', 'start': 200, 'duration': 100},
    ]
    track = _make_track(medias)
    visible = track.visible_clips
    assert [c.clip_type for c in visible] == ['VMFile', 'IMFile']


def test_new_callout_shapes():
    assert CalloutShape.SHAPE_ELLIPSE.value == 'shape-ellipse'
    assert CalloutShape.SHAPE_TRIANGLE.value == 'shape-triangle'
    assert CalloutShape.TEXT.value == 'text'
    assert CalloutShape.TEXT_RECTANGLE.value == 'text-rectangle'
    assert CalloutShape.SHAPE_RECTANGLE.value == 'shape-rectangle'


# ------------------------------------------------------------------
# Track.clip_at_index
# ------------------------------------------------------------------

def test_clip_at_index():
    medias = [
        {'id': 2, '_type': 'AMFile', 'start': 200, 'duration': 100},
        {'id': 1, '_type': 'VMFile', 'start': 50, 'duration': 100},
        {'id': 3, '_type': 'IMFile', 'start': 500, 'duration': 100},
    ]
    track = _make_track(medias=medias)
    assert track.clip_at_index(0).id == 1
    assert track.clip_at_index(1).id == 2
    assert track.clip_at_index(2).id == 3


def test_clip_at_index_out_of_range():
    track = _make_track(medias=[
        {'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100},
    ])
    with pytest.raises(IndexError, match='clip index 5 out of range'):
        track.clip_at_index(5)
    with pytest.raises(IndexError, match='clip index -1 out of range'):
        track.clip_at_index(-1)


# ------------------------------------------------------------------
# BaseClip.source_id
# ------------------------------------------------------------------

def test_source_id_replaces_source_path():
    clip_with_src = clip_from_dict({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'src': '/media/video.mp4',
    })
    assert clip_with_src.source_id == '/media/video.mp4'

    clip_without_src = clip_from_dict({
        'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 100,
    })
    assert clip_without_src.source_id is None


# ------------------------------------------------------------------
# BaseClip.media_start_seconds
# ------------------------------------------------------------------

def test_media_start_seconds():
    media_start_ticks: int = EDIT_RATE * 5
    clip = clip_from_dict({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'mediaStart': media_start_ticks,
    })
    assert clip.media_start_seconds == pytest.approx(5.0)


# ------------------------------------------------------------------
# clip_before / clip_after / overlaps_with / distance_to
# ------------------------------------------------------------------

def test_clip_before():
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(3), 'duration': seconds_to_ticks(1)},
    ])
    clip = track.clip_before(3.0)
    assert clip is not None
    assert clip.id == 1


def test_clip_before_none():
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)},
    ])
    assert track.clip_before(1.0) is None


def test_clip_after():
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)},
    ])
    clip = track.clip_after(3.0)
    assert clip is not None
    assert clip.id == 2


def test_clip_after_none():
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(1)},
    ])
    assert track.clip_after(5.0) is None


def test_clip_after_includes_clip_at_exact_time():
    """clip_after uses >= (at-or-after); a clip starting exactly at the query time is returned."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': seconds_to_ticks(5.0), 'duration': seconds_to_ticks(1)},
    ])
    clip = track.clip_after(5.0)
    assert clip is not None
    assert clip.id == 1


def test_clip_strictly_after_excludes_clip_at_exact_time():
    """clip_strictly_after uses > (strictly after); a clip at the query time is NOT returned."""
    track = _make_track([
        {'id': 1, '_type': 'VMFile', 'start': seconds_to_ticks(5.0), 'duration': seconds_to_ticks(1)},
        {'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(10.0), 'duration': seconds_to_ticks(1)},
    ])
    assert track.clip_strictly_after(5.0).id == 2
    assert track.clip_strictly_after(10.0) is None


def test_overlaps_with_true():
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(2), 'duration': seconds_to_ticks(2)})
    assert clip_a.overlaps_with(clip_b) is True


def test_overlaps_with_false():
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(3), 'duration': seconds_to_ticks(1)})
    assert clip_a.overlaps_with(clip_b) is False


def test_distance_to_gap():
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(5), 'duration': seconds_to_ticks(1)})
    assert clip_a.distance_to(clip_b) == pytest.approx(3.0)


def test_distance_to_overlap():
    clip_a = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3)})
    clip_b = BaseClip({'id': 2, '_type': 'VMFile', 'start': seconds_to_ticks(2), 'duration': seconds_to_ticks(2)})
    assert clip_a.distance_to(clip_b) == pytest.approx(-1.0)


# ------------------------------------------------------------------
# Project.duration_formatted
# ------------------------------------------------------------------

def test_duration_formatted():
    with patch.object(Project, 'duration_seconds', new_callable=PropertyMock, return_value=125.7):
        proj = object.__new__(Project)
        assert proj.duration_formatted == '2:05'


# ------------------------------------------------------------------
# Track.clip_count_by_type
# ------------------------------------------------------------------

def test_clip_count_by_type():
    medias = [
        {'id': 1, 'start': 0, 'duration': 100, '_type': 'VMFile'},
        {'id': 2, 'start': 100, 'duration': 100, '_type': 'VMFile'},
        {'id': 3, 'start': 200, 'duration': 100, '_type': 'Callout'},
    ]
    track = _make_track(medias=medias)
    counts: dict[str, int] = track.clip_count_by_type
    assert counts == {'VMFile': 2, 'Callout': 1}


# ------------------------------------------------------------------
# BaseClip.has_keyframes
# ------------------------------------------------------------------

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
    clip = next(iter(track.clips))
    assert clip.has_keyframes is True


def test_has_keyframes_false():
    media = {
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {
            'opacity': 0.5,
        },
    }
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    assert clip.has_keyframes is False


# ------------------------------------------------------------------
# BaseClip.keyframe_count
# ------------------------------------------------------------------

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
            'volume': 0.8,
        },
    }
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    assert clip.keyframe_count == 3


# ------------------------------------------------------------------
# BaseClip.is_at_origin
# ------------------------------------------------------------------

def test_is_at_origin():
    at_zero: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100}
    not_zero: dict[str, Any] = {'id': 2, 'start': 500, 'duration': 100}
    track = _make_track(medias=[at_zero, not_zero])
    clips = list(track.clips)
    assert clips[0].is_at_origin is True
    assert clips[1].is_at_origin is False


# ------------------------------------------------------------------
# BaseClip.copy_timing_from
# ------------------------------------------------------------------

def test_copy_timing_from():
    source = BaseClip({'id': 1, '_type': 'VMFile', 'start': 1000, 'duration': 5000})
    target = BaseClip({'id': 2, '_type': 'VMFile', 'start': 0, 'duration': 100})
    result = target.copy_timing_from(source)
    assert target.start == 1000
    assert target.duration == 5000
    assert result is target


# ------------------------------------------------------------------
# BaseClip.matches_type
# ------------------------------------------------------------------

def test_matches_type():
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100})
    assert clip.matches_type('VMFile') is True
    assert clip.matches_type(ClipType.VIDEO) is True
    assert clip.matches_type('AMFile') is False
    assert clip.matches_type(ClipType.AUDIO) is False


# ------------------------------------------------------------------
# BaseClip.snap_to_seconds
# ------------------------------------------------------------------

def test_snap_to_seconds():
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2.0)})
    result = clip.snap_to_seconds(5.0)
    assert clip.start == seconds_to_ticks(5.0)
    assert result is clip


# ------------------------------------------------------------------
# BaseClip.is_longer_than / is_shorter_than
# ------------------------------------------------------------------

def test_is_longer_than():
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(3.0)})
    assert clip.is_longer_than(2.0) is True
    assert clip.is_longer_than(3.0) is False
    assert clip.is_longer_than(4.0) is False


def test_is_shorter_than():
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': seconds_to_ticks(2.0)})
    assert clip.is_shorter_than(3.0) is True
    assert clip.is_shorter_than(2.0) is False
    assert clip.is_shorter_than(1.0) is False


# ------------------------------------------------------------------
# BaseClip.set_source
# ------------------------------------------------------------------

def test_set_source():
    clip = BaseClip({'id': 1, 'src': 10, '_type': 'AMFile', 'start': 0, 'duration': 100})
    result = clip.set_source(42)
    assert clip.source_id == 42
    assert result is clip


# ------------------------------------------------------------------
# BaseClip.set_metadata / get_metadata
# ------------------------------------------------------------------

def test_set_get_metadata():
    clip = BaseClip({'id': 1, '_type': 'AMFile', 'start': 0, 'duration': 100})
    assert clip.get_metadata('author') is None
    assert clip.get_metadata('author', 'unknown') == 'unknown'
    result = clip.set_metadata('author', 'Alice')
    assert result is clip
    assert clip.get_metadata('author') == 'Alice'
    assert clip.metadata == {'author': 'Alice'}


# ------------------------------------------------------------------
# Track.clip_ids_sorted
# ------------------------------------------------------------------

def test_clip_ids_sorted():
    track = _make_track([
        {'id': 3, 'start': 300, 'duration': 100},
        {'id': 1, 'start': 100, 'duration': 100},
        {'id': 2, 'start': 200, 'duration': 100},
    ])
    assert track.clip_ids_sorted == [1, 2, 3]
    assert track.clip_ids == [3, 1, 2]


# ------------------------------------------------------------------
# BaseClip.is_muted / Track.muted_clips
# ------------------------------------------------------------------

def test_clip_is_muted():
    media = {'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 0.0}}
    track = _make_track(medias=[media])
    muted_clip = next(iter(track.clips))
    assert muted_clip.is_muted is True

    audible_media = {'id': 2, 'start': 200, 'duration': 100, 'attributes': {'gain': 0.75}}
    audible_track = _make_track(medias=[audible_media])
    audible_clip = next(iter(audible_track.clips))
    assert audible_clip.is_muted is False


def test_muted_clips():
    medias = [
        {'id': 1, 'start': 0, 'duration': 100, 'attributes': {'gain': 0.0}},
        {'id': 2, 'start': 200, 'duration': 100, 'attributes': {'gain': 1.0}},
        {'id': 3, 'start': 400, 'duration': 100, 'attributes': {'gain': 0.0}},
    ]
    track = _make_track(medias=medias)
    muted = track.muted_clips
    muted_ids: list[int] = [clip.id for clip in muted]
    assert muted_ids == [1, 3]


# ------------------------------------------------------------------
# BaseClip.set_start_seconds / set_duration_seconds
# ------------------------------------------------------------------

def test_set_start_seconds_updates_data():
    clip_data: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100, 'type': 'VMFile', 'parameters': {}, 'effects': [], 'attributes': {'ident': ''}}
    clip: BaseClip = BaseClip(clip_data)
    result = clip.set_start_seconds(2.0)
    assert clip._data['start'] == seconds_to_ticks(2.0)
    assert result is clip


def test_set_duration_seconds_updates_data():
    clip_data: dict[str, Any] = {'id': 1, 'start': 0, 'duration': 100, 'type': 'VMFile', 'parameters': {}, 'effects': [], 'attributes': {'ident': ''}}
    clip: BaseClip = BaseClip(clip_data)
    result = clip.set_duration_seconds(5.0)
    assert clip._data['duration'] == seconds_to_ticks(5.0)
    assert result is clip


# ------------------------------------------------------------------
# BaseClip.is_effect_applied
# ------------------------------------------------------------------

def test_is_effect_applied_true():
    clip = BaseClip({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'DropShadow'}],
    })
    assert clip.is_effect_applied('DropShadow') is True


def test_is_effect_applied_false():
    clip = BaseClip({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'Glow'}],
    })
    assert clip.is_effect_applied('DropShadow') is False


def test_is_effect_applied_no_effects():
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100})
    assert clip.is_effect_applied('DropShadow') is False


def test_is_effect_applied_with_enum():
    clip = BaseClip({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'effects': [{'effectName': 'DropShadow'}],
    })
    assert clip.is_effect_applied(EffectName.DROP_SHADOW) is True


# ------------------------------------------------------------------
# BaseClip.clear_metadata
# ------------------------------------------------------------------

def test_clear_metadata_removes_all():
    clip_data: dict = {
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'metadata': {'presetName': 'Intro', 'author': 'Test'},
    }
    clip = BaseClip(clip_data)
    clip.clear_metadata()
    assert clip.metadata == {}
    assert clip_data['metadata'] == {}


def test_clear_metadata_returns_self():
    clip = BaseClip({
        'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100,
        'metadata': {'key': 'value'},
    })
    assert clip.clear_metadata() is clip


def test_clear_metadata_on_empty():
    clip = BaseClip({'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 100})
    clip.clear_metadata()
    assert clip._data['metadata'] == {}


# ------------------------------------------------------------------
# Effect add methods (LUT, MediaMatte, MotionBlur, Emphasize, BlendMode)
# ------------------------------------------------------------------

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
        result = clip.add_emphasize(intensity=0.3)
        assert isinstance(result, Effect)
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


# ------------------------------------------------------------------
# apply_if
# ------------------------------------------------------------------

class TestClipPredicates:
    def test_apply_if_true(self):
        clip = AMFile(_base_clip_dict(
            _type="AMFile",
            channelNumber="0,1",
            attributes={"ident": "voiceover", "gain": 0.8, "mixToMono": False, "loudnessNormalization": True},
        ))
        called = []
        clip.apply_if(lambda c: True, lambda c: called.append(c))
        assert called[0] is clip

    def test_apply_if_false(self):
        clip = AMFile(_base_clip_dict(
            _type="AMFile",
            channelNumber="0,1",
            attributes={"ident": "voiceover", "gain": 0.8, "mixToMono": False, "loudnessNormalization": True},
        ))
        called = []
        clip.apply_if(lambda c: False, lambda c: called.append(c))
        assert called == []


# ------------------------------------------------------------------
# remove_effect_by_name / duplicate_effects_to / reset_transforms
# ------------------------------------------------------------------

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
        assert clip._data['effects'] == [{'effectName': 'Border', 'parameters': {}}]


class TestDuplicateEffectsTo:
    def test_copies_effects_to_target(self, project):
        track = project.timeline.tracks[0]
        source = track.add_video(0, 0, 5.0)
        target = track.add_video(0, 5.0, 5.0)
        source._data['effects'] = [{'effectName': 'Glow', 'parameters': {}}]
        source.duplicate_effects_to(target)
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


# ------------------------------------------------------------------
# BaseClip: gain, mute, metadata, animations, repr, setters
# ------------------------------------------------------------------

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

    def test_unmute_restores_gain(self):
        data = _base()
        clip = BaseClip(data)
        clip.mute()
        assert clip.gain == 0.0
        actual_result = clip.unmute()
        assert actual_result is clip
        assert clip.gain == 1.0

    def test_unmute_group(self):
        data = {**_base(), '_type': 'Group', 'tracks': []}
        clip = BaseClip(data)
        clip.mute()
        assert data['parameters']['volume'] == 0.0
        clip.unmute()
        assert data['parameters']['volume'] == 1.0

    def test_unmute_unified_media(self):
        data = {
            **_base(), '_type': 'UnifiedMedia',
            'audio': {'_type': 'AMFile', 'attributes': {}},
        }
        clip = BaseClip(data)
        clip.mute()
        assert data['audio']['attributes']['gain'] == 0.0
        clip.unmute()
        assert data['audio']['attributes']['gain'] == 1.0

    def test_unmute_unified_media_no_audio_raises(self):
        data = {**_base(), '_type': 'UnifiedMedia'}
        clip = BaseClip(data)
        with pytest.raises(ValueError, match='no audio'):
            clip.unmute()


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


class TestBaseClipReprCoverage:
    def test_repr(self):
        data = _base(start=EDIT_RATE * 2, duration=EDIT_RATE * 5)
        clip = BaseClip(data)
        actual_repr = repr(clip)
        assert "BaseClip" in actual_repr
        assert "2.00s" in actual_repr
        assert "5.00s" in actual_repr


class TestBaseClipSettersCoverage:
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


# ------------------------------------------------------------------
# BaseClip: fade, opacity, effects coverage
# ------------------------------------------------------------------

class TestBaseClipFadeCoverage:
    def test_fade_in(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.fade_in(1.0)
        assert actual_result is clip
        assert "opacity" in data["parameters"]
        assert data["parameters"]["opacity"]["keyframes"][0]["value"] == 1.0

    def test_fade_out(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.fade_out(1.0)
        assert actual_result is clip
        assert "opacity" in data["parameters"]
        kf = data["parameters"]["opacity"]["keyframes"]
        assert [k["value"] for k in kf] == [0.0]

    def test_fade_both(self):
        data = _base()
        clip = BaseClip(data)
        actual_result = clip.fade(fade_in_seconds=0.5, fade_out_seconds=0.5)
        assert actual_result is clip
        visual = data["animationTracks"]["visual"]
        assert isinstance(visual, list)

    def test_fade_out_only(self):
        data = _base()
        clip = BaseClip(data)
        clip.fade(fade_out_seconds=1.0)
        kf = data["parameters"]["opacity"]["keyframes"]
        assert [k["value"] for k in kf] == [0.0]

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
        assert data["parameters"]["opacity"] == 0.5

    def test_clear_animations(self):
        data = _base(animationTracks={"visual": [{"track": "opacity"}]})
        clip = BaseClip(data)
        actual_result = clip.clear_animations()
        assert actual_result is clip
        assert data["animationTracks"] == {}


class TestBaseClipEffectsCoverage:
    def test_add_effect(self):
        data = _base()
        clip = BaseClip(data)
        effect_data = {"effectName": "TestEffect", "bypassed": False}
        actual_effect = clip.add_effect(effect_data)
        assert actual_effect.name == "TestEffect"
        assert data["effects"][0]["effectName"] == "TestEffect"

    def test_add_drop_shadow(self):
        data = _base()
        clip = BaseClip(data)
        actual_effect = clip.add_drop_shadow(offset=10, blur=20, opacity=0.3, angle=5.0, color=(0.1, 0.2, 0.3))
        assert actual_effect.name == "DropShadow"
        effect_dict = data["effects"][0]
        assert effect_dict["effectName"] == "DropShadow"
        assert effect_dict["parameters"]["offset"] == 10

    def test_add_glow(self):
        data = _base()
        clip = BaseClip(data)
        actual_effect = clip.add_glow(radius=50.0, intensity=0.5)
        assert actual_effect.name == "Glow"
        assert data["effects"][0]["effectName"] == "Glow"
        assert data["effects"][0]["parameters"]["radius"] == 50.0

    def test_add_round_corners(self):
        data = _base()
        clip = BaseClip(data)
        actual_effect = clip.add_round_corners(radius=20.0)
        assert actual_effect.name == "RoundCorners"
        assert data["effects"][0]["effectName"] == "RoundCorners"
        assert data["effects"][0]["parameters"]["radius"] == 20.0

    def test_remove_effects(self):
        data = _base(effects=[{"effectName": "Glow"}])
        clip = BaseClip(data)
        actual_result = clip.remove_all_effects()
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
        assert actual_glow.name == "Glow"
        effect_dict = data["effects"][0]
        assert effect_dict["effectName"] == "Glow"
        assert effect_dict["parameters"]["radius"]["defaultValue"] == 40.0
        assert effect_dict['leftEdgeMods'][0]['group'] == 'Video'
        assert effect_dict['rightEdgeMods'][0]['group'] == 'Video'


# ------------------------------------------------------------------
# Standalone base.py coverage
# ------------------------------------------------------------------

def test_base_clip_opacity_setter_dict():
    clip = BaseClip({
        '_type': 'VMFile',
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {'opacity': {'type': 'double', 'defaultValue': 1.0, 'keyframes': []}},
        'animationTracks': {'visual': [{'key': 'val'}]},
    })
    clip.opacity = 0.5
    assert clip._data['parameters']['opacity']['defaultValue'] == 0.5
    assert 'keyframes' not in clip._data['parameters']['opacity']
    assert clip._data['animationTracks']['visual'] == []


def test_base_clip_volume_setter_dict():
    clip = BaseClip({
        '_type': 'VMFile',
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {'volume': {'type': 'double', 'defaultValue': 1.0, 'keyframes': []}},
    })
    clip.volume = 0.5
    assert clip._data['parameters']['volume']['defaultValue'] == 0.5


def test_base_clip_set_opacity_method_dict():
    clip = BaseClip({
        '_type': 'VMFile',
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {'opacity': {'type': 'double', 'defaultValue': 1.0, 'keyframes': []}},
        'animationTracks': {'visual': [{'key': 'val'}]},
    })
    clip.set_opacity(0.3)
    assert clip._data['parameters']['opacity']['defaultValue'] == 0.3
    assert clip._data['animationTracks']['visual'] == []


def test_base_clip_source_path_deprecation():
    clip = BaseClip({
        '_type': 'VMFile',
        'id': 1, 'start': 0, 'duration': 100,
        'src': 42,
    })
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        result = clip.source_path
        assert result == 42
        assert 'deprecated' in str(w[0].message).lower()


# ------------------------------------------------------------------
# Bug fix: is_silent checks parameters.volume for UnifiedMedia
# ------------------------------------------------------------------

class TestIsSilentUnifiedMedia:
    def test_silent_when_audio_gain_zero(self):
        clip = BaseClip({
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'audio': {'_type': 'AMFile', 'attributes': {'gain': 0.0}},
        })
        assert clip.is_silent is True

    def test_silent_when_volume_zero_scalar(self):
        clip = BaseClip({
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'audio': {'_type': 'AMFile', 'attributes': {'gain': 1.0}},
            'parameters': {'volume': 0.0},
        })
        assert clip.is_silent is True

    def test_silent_when_volume_zero_dict(self):
        clip = BaseClip({
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'audio': {'_type': 'AMFile', 'attributes': {'gain': 1.0}},
            'parameters': {'volume': {'type': 'double', 'defaultValue': 0.0}},
        })
        assert clip.is_silent is True

    def test_not_silent_when_both_nonzero(self):
        clip = BaseClip({
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'audio': {'_type': 'AMFile', 'attributes': {'gain': 0.8}},
            'parameters': {'volume': 0.5},
        })
        assert clip.is_silent is False

    def test_not_silent_defaults(self):
        clip = BaseClip({
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
        })
        assert clip.is_silent is False


class TestMediaStartSecondsPrecision:
    """media_start_seconds must not truncate fractional ticks."""

    def test_fractional_media_start_preserved(self):
        clip = BaseClip({
            '_type': 'VMFile', 'id': 1, 'start': 0,
            'duration': EDIT_RATE, 'mediaDuration': EDIT_RATE,
            'mediaStart': '705600001/2', 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {},
        })
        expected = float(Fraction(705600001, 2)) / EDIT_RATE
        assert clip.media_start_seconds == expected

    def test_integer_media_start_unchanged(self):
        clip = BaseClip({
            '_type': 'VMFile', 'id': 1, 'start': 0,
            'duration': EDIT_RATE, 'mediaDuration': EDIT_RATE,
            'mediaStart': EDIT_RATE, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'animationTracks': {},
        })
        assert abs(clip.media_start_seconds - 1.0) < 1e-12


class TestClearAllKeyframesAnimationTracks:
    """clear_all_keyframes must also clear animationTracks."""

    def test_animation_tracks_cleared(self):
        clip = BaseClip({
            '_type': 'VMFile', 'id': 1, 'start': 0,
            'duration': EDIT_RATE, 'mediaDuration': EDIT_RATE, 'scalar': 1,
            'parameters': {
                'opacity': {
                    'type': 'double', 'defaultValue': 1.0,
                    'keyframes': [{'time': 0, 'value': 0.0, 'endTime': 100, 'duration': 100}],
                },
            },
            'effects': [], 'metadata': {},
            'animationTracks': {'visual': [{'endTime': 100, 'duration': 100}]},
        })
        clip.clear_all_keyframes()
        assert 'keyframes' not in clip._data['parameters']['opacity']
        assert clip._data['animationTracks'] == {}


class TestMediaMattePresetName:
    """add_media_matte default preset_name should derive from matte_mode."""

    def test_default_preset_name_derives_from_mode(self):
        clip = BaseClip({
            '_type': 'VMFile', 'id': 1, 'start': 0, 'duration': EDIT_RATE,
            'mediaDuration': EDIT_RATE, 'scalar': 1, 'parameters': {},
            'effects': [], 'metadata': {}, 'animationTracks': {},
        })
        clip.add_media_matte()
        eff = clip._data['effects'][-1]
        # Default matte_mode=1 (Alpha), so preset should be 'Media Matte Alpha'
        assert eff['metadata']['presetName'] == 'Media Matte Alpha'


# ------------------------------------------------------------------
# Bug 6: set_speed propagates to Group internal tracks' clips
# ------------------------------------------------------------------

def test_set_speed_group_propagates_to_inner_clips() -> None:
    """set_speed on a Group clip scales inner clips' duration and scalar."""
    inner_dur = EDIT_RATE * 10
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [{
                '_type': 'VMFile', 'id': 20, 'src': 1,
                'start': 0, 'duration': inner_dur,
                'mediaStart': 0, 'mediaDuration': inner_dur,
                'scalar': 1,
            }],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    inner = data['tracks'][0]['medias'][0]
    # scalar: old(1) * 1/2 = 1/2
    assert inner['scalar'] == '1/2'
    # duration: inner_dur * 1/2
    assert inner['duration'] == inner_dur // 2


# ------------------------------------------------------------------
# Bug 1: is_image includes ScreenIMFile
# ------------------------------------------------------------------

def test_is_image_includes_screen_image() -> None:
    """ScreenIMFile clips should be recognized as image clips."""
    data = {'_type': 'ScreenIMFile', 'id': 1, 'start': 0, 'duration': 100}
    clip = clip_from_dict(data)
    assert clip.is_image is True


def test_is_image_still_true_for_imfile() -> None:
    """IMFile clips should still be recognized as image clips."""
    data = {'_type': 'IMFile', 'id': 1, 'start': 0, 'duration': 100}
    clip = clip_from_dict(data)
    assert clip.is_image is True


def test_is_image_false_for_video() -> None:
    """VMFile clips should not be recognized as image clips."""
    data = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': 100}
    clip = clip_from_dict(data)
    assert clip.is_image is False


# ------------------------------------------------------------------
# Bug 2: set_time_range delegates to property setters (UnifiedMedia)
# ------------------------------------------------------------------

def test_set_time_range_unified_media_propagates() -> None:
    """set_time_range on UnifiedMedia must propagate to video/audio sub-dicts."""
    data = {
        '_type': 'UnifiedMedia', 'id': 1, 'src': 1,
        'start': 0, 'duration': EDIT_RATE * 10,
        'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
        'video': {'_type': 'VMFile', 'start': 0, 'duration': EDIT_RATE * 10,
                  'mediaDuration': EDIT_RATE * 10, 'scalar': 1, 'mediaStart': 0},
        'audio': {'_type': 'AMFile', 'start': 0, 'duration': EDIT_RATE * 10,
                  'mediaDuration': EDIT_RATE * 10, 'scalar': 1, 'mediaStart': 0},
    }
    clip = BaseClip(data)
    clip.set_time_range(2.0, 5.0)
    expected_start = seconds_to_ticks(2.0)
    expected_dur = seconds_to_ticks(5.0)
    assert data['video']['start'] == expected_start
    assert data['video']['duration'] == expected_dur
    assert data['audio']['start'] == expected_start
    assert data['audio']['duration'] == expected_dur


# ------------------------------------------------------------------
# Bug 4+5+6: set_speed Group scales start, propagates to UnifiedMedia/StitchedMedia
# ------------------------------------------------------------------

def test_set_speed_group_scales_inner_start() -> None:
    """set_speed on Group must scale inner clip start positions."""
    inner_dur = EDIT_RATE * 5
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [
                {'_type': 'VMFile', 'id': 20, 'src': 1,
                 'start': 0, 'duration': inner_dur,
                 'mediaStart': 0, 'mediaDuration': inner_dur, 'scalar': 1},
                {'_type': 'VMFile', 'id': 21, 'src': 1,
                 'start': inner_dur, 'duration': inner_dur,
                 'mediaStart': 0, 'mediaDuration': inner_dur, 'scalar': 1},
            ],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    inner0 = data['tracks'][0]['medias'][0]
    inner1 = data['tracks'][0]['medias'][1]
    # start should be scaled by 1/2
    assert inner0['start'] == 0
    assert inner1['start'] == inner_dur // 2


def test_set_speed_group_propagates_to_unified_media() -> None:
    """set_speed on Group must propagate scalar/start/duration to UnifiedMedia sub-dicts."""
    inner_dur = EDIT_RATE * 10
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 30, 'src': 1,
                'start': 0, 'duration': inner_dur,
                'mediaStart': 0, 'mediaDuration': inner_dur, 'scalar': 1,
                'video': {'_type': 'VMFile', 'start': 0, 'duration': inner_dur,
                          'scalar': 1, 'mediaStart': 0},
                'audio': {'_type': 'AMFile', 'start': 0, 'duration': inner_dur,
                          'scalar': 1, 'mediaStart': 0},
            }],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    inner = data['tracks'][0]['medias'][0]
    assert inner['video']['scalar'] == inner['scalar']
    assert inner['video']['start'] == inner['start']
    assert inner['video']['duration'] == inner['duration']
    assert inner['audio']['scalar'] == inner['scalar']
    assert inner['audio']['duration'] == inner['duration']


def test_set_speed_group_propagates_to_stitched_media() -> None:
    """set_speed on Group must re-layout StitchedMedia nested segments."""
    seg_dur = EDIT_RATE * 5
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [{
                '_type': 'StitchedMedia', 'id': 40, 'src': 1,
                'start': 0, 'duration': EDIT_RATE * 10,
                'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                'medias': [
                    {'_type': 'VMFile', 'id': 41, 'start': 0, 'duration': seg_dur,
                     'mediaDuration': seg_dur, 'scalar': 1},
                    {'_type': 'VMFile', 'id': 42, 'start': seg_dur, 'duration': seg_dur,
                     'mediaDuration': seg_dur, 'scalar': 1},
                ],
            }],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    stitched = data['tracks'][0]['medias'][0]
    seg0 = stitched['medias'][0]
    seg1 = stitched['medias'][1]
    # Segments should have scaled duration and sequential starts
    assert seg0['duration'] == seg_dur // 2
    assert seg0['start'] == 0
    assert seg1['start'] == seg_dur // 2
    assert seg1['scalar'] == '1/2'


# ------------------------------------------------------------------
# Bug fix: set_speed Group propagates mediaDuration/mediaStart to UnifiedMedia sub-dicts
# ------------------------------------------------------------------

def test_set_speed_group_propagates_media_duration_to_unified_sub_dicts() -> None:
    """set_speed on Group must propagate mediaDuration and mediaStart to UnifiedMedia video/audio."""
    inner_dur = EDIT_RATE * 10
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 30, 'src': 1,
                'start': 0, 'duration': inner_dur,
                'mediaStart': 1000, 'mediaDuration': inner_dur, 'scalar': 1,
                'video': {'_type': 'VMFile', 'start': 0, 'duration': inner_dur,
                          'scalar': 1, 'mediaStart': 1000, 'mediaDuration': inner_dur},
                'audio': {'_type': 'AMFile', 'start': 0, 'duration': inner_dur,
                          'scalar': 1, 'mediaStart': 1000, 'mediaDuration': inner_dur},
            }],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    inner = data['tracks'][0]['medias'][0]
    assert inner['video']['mediaDuration'] == inner['mediaDuration']
    assert inner['video']['mediaStart'] == inner['mediaStart']
    assert inner['audio']['mediaDuration'] == inner['mediaDuration']
    assert inner['audio']['mediaStart'] == inner['mediaStart']


# ------------------------------------------------------------------
# Bug fix: set_speed Group sets clipSpeedAttribute on inner clips
# ------------------------------------------------------------------

def test_set_speed_group_sets_clip_speed_attribute_on_inner_clips() -> None:
    """set_speed on Group must set clipSpeedAttribute metadata on inner clips."""
    inner_dur = EDIT_RATE * 10
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [{
                '_type': 'VMFile', 'id': 20, 'src': 1,
                'start': 0, 'duration': inner_dur,
                'mediaStart': 0, 'mediaDuration': inner_dur, 'scalar': 1,
                'metadata': {},
            }],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    inner = data['tracks'][0]['medias'][0]
    assert inner['metadata']['clipSpeedAttribute'] == {'type': 'bool', 'value': True}


def test_set_speed_group_sets_clip_speed_attribute_on_unified_sub_dicts() -> None:
    """set_speed on Group must set clipSpeedAttribute on UnifiedMedia video/audio sub-dicts."""
    inner_dur = EDIT_RATE * 10
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 30, 'src': 1,
                'start': 0, 'duration': inner_dur,
                'mediaStart': 0, 'mediaDuration': inner_dur, 'scalar': 1,
                'metadata': {},
                'video': {'_type': 'VMFile', 'start': 0, 'duration': inner_dur,
                          'scalar': 1, 'mediaStart': 0, 'metadata': {}},
                'audio': {'_type': 'AMFile', 'start': 0, 'duration': inner_dur,
                          'scalar': 1, 'mediaStart': 0, 'metadata': {}},
            }],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    inner = data['tracks'][0]['medias'][0]
    assert inner['metadata']['clipSpeedAttribute'] == {'type': 'bool', 'value': True}
    assert inner['video']['metadata']['clipSpeedAttribute'] == {'type': 'bool', 'value': True}
    assert inner['audio']['metadata']['clipSpeedAttribute'] == {'type': 'bool', 'value': True}


def test_set_speed_group_sets_clip_speed_attribute_on_stitched_segments() -> None:
    """set_speed on Group must set clipSpeedAttribute on StitchedMedia segments."""
    seg_dur = EDIT_RATE * 5
    data = _base_clip_dict(
        _type='Group',
        duration=EDIT_RATE * 10,
        mediaDuration=EDIT_RATE * 10,
        tracks=[{
            'trackIndex': 0,
            'medias': [{
                '_type': 'StitchedMedia', 'id': 40, 'src': 1,
                'start': 0, 'duration': EDIT_RATE * 10,
                'mediaStart': 0, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
                'metadata': {},
                'medias': [
                    {'_type': 'VMFile', 'id': 41, 'start': 0, 'duration': seg_dur,
                     'mediaDuration': seg_dur, 'scalar': 1, 'metadata': {}},
                ],
            }],
        }],
    )
    clip = BaseClip(data)
    clip.set_speed(2.0)
    stitched = data['tracks'][0]['medias'][0]
    assert stitched['metadata']['clipSpeedAttribute'] == {'type': 'bool', 'value': True}
    assert stitched['medias'][0]['metadata']['clipSpeedAttribute'] == {'type': 'bool', 'value': True}


# ------------------------------------------------------------------
# Bug fix: scalar.setter no duplicate mediaDuration write
# ------------------------------------------------------------------

def test_scalar_setter_no_duplicate_media_duration() -> None:
    """scalar.setter on UnifiedMedia should write mediaDuration exactly once to sub-dicts."""
    data = {
        '_type': 'UnifiedMedia', 'id': 1, 'src': 1,
        'start': 0, 'duration': EDIT_RATE * 10,
        'mediaStart': 5000, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
        'video': {'_type': 'VMFile', 'start': 0, 'duration': EDIT_RATE * 10,
                  'scalar': 1, 'mediaStart': 5000, 'mediaDuration': EDIT_RATE * 10},
        'audio': {'_type': 'AMFile', 'start': 0, 'duration': EDIT_RATE * 10,
                  'scalar': 1, 'mediaStart': 5000, 'mediaDuration': EDIT_RATE * 10},
    }
    clip = BaseClip(data)
    clip.scalar = Fraction(1, 2)
    # mediaDuration should be duration / scalar = 10s * 2 = 20s in ticks
    expected_md = Fraction(EDIT_RATE * 10) / Fraction(1, 2)
    assert Fraction(str(data['video']['mediaDuration'])) == expected_md
    assert Fraction(str(data['audio']['mediaDuration'])) == expected_md
    assert data['video']['mediaStart'] == data['mediaStart']
    assert data['audio']['mediaStart'] == data['mediaStart']


# ------------------------------------------------------------------
# Bug 1: set_speed Group branch — wrapper duration must be scaled
# ------------------------------------------------------------------

def test_set_speed_group_scales_wrapper_duration():
    """Bug 1: set_speed on a Group must scale the wrapper's duration."""
    data: dict = {
        '_type': 'Group', 'id': 1, 'start': 0,
        'duration': EDIT_RATE * 10, 'mediaDuration': EDIT_RATE * 10,
        'scalar': 1, 'mediaStart': 0,
        'tracks': [{
            'medias': [{
                '_type': 'VMFile', 'id': 2, 'start': 0,
                'duration': EDIT_RATE * 10, 'mediaDuration': EDIT_RATE * 10,
                'scalar': 1, 'mediaStart': 0,
            }],
        }],
    }
    clip = BaseClip(data)
    clip.set_speed(2.0)
    # At 2x speed, wrapper duration should halve
    assert data['duration'] == EDIT_RATE * 5


# ------------------------------------------------------------------
# Bug 5: set_speed StitchedMedia — wrapper duration must be updated
# ------------------------------------------------------------------

def test_set_speed_stitched_scales_wrapper_duration():
    """Bug 5: set_speed on StitchedMedia must update wrapper duration."""
    seg_dur = EDIT_RATE * 5
    data: dict = {
        '_type': 'StitchedMedia', 'id': 1, 'start': 0,
        'duration': seg_dur * 2, 'mediaDuration': seg_dur * 2,
        'scalar': 1, 'mediaStart': 0,
        'medias': [
            {'_type': 'VMFile', 'id': 2, 'start': 0,
             'duration': seg_dur, 'mediaDuration': seg_dur, 'scalar': 1},
            {'_type': 'VMFile', 'id': 3, 'start': seg_dur,
             'duration': seg_dur, 'mediaDuration': seg_dur, 'scalar': 1},
        ],
    }
    clip = BaseClip(data)
    clip.set_speed(2.0)
    # Each segment halves, so wrapper = sum of halved segments
    expected = seg_dur // 2 + seg_dur // 2
    assert data['duration'] == expected


# ------------------------------------------------------------------
# Bug 7: is_video — UnifiedMedia segments inside StitchedMedia
# ------------------------------------------------------------------

def test_is_video_stitched_with_unified_media_segment():
    """Bug 7: is_video should detect VMFile inside UnifiedMedia segments of StitchedMedia."""
    data: dict = {
        '_type': 'StitchedMedia', 'id': 1, 'start': 0,
        'duration': 1000, 'mediaDuration': 1000, 'scalar': 1,
        'medias': [{
            '_type': 'UnifiedMedia', 'id': 2, 'start': 0,
            'duration': 1000, 'mediaDuration': 1000, 'scalar': 1,
            'video': {'_type': 'VMFile'},
            'audio': {'_type': 'AMFile'},
        }],
    }
    clip = BaseClip(data)
    assert clip.is_video is True


class TestIsVideoStitchedMediaFallback:
    def test_stitched_with_only_audio_segments_returns_false(self):
        clip = BaseClip({
            '_type': 'StitchedMedia', 'id': 1, 'start': 0,
            'duration': 100, 'mediaDuration': 100, 'scalar': 1,
            'medias': [
                {'_type': 'AMFile', 'id': 2},
                {'_type': 'UnifiedMedia', 'id': 3, 'video': {'_type': 'IMFile'}},
            ],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        })
        assert clip.is_video is False


def _group_data(inner_dur: int = EDIT_RATE * 5) -> dict:
    return {
        '_type': 'Group', 'id': 1,
        'start': 0, 'duration': inner_dur * 2,
        'mediaStart': 0, 'mediaDuration': inner_dur * 2, 'scalar': 1,
        'tracks': [{
            'trackIndex': 0,
            'medias': [
                {'_type': 'VMFile', 'id': 20, 'src': 1,
                 'start': 0, 'duration': inner_dur,
                 'mediaStart': 0, 'mediaDuration': inner_dur, 'scalar': 1},
                {'_type': 'VMFile', 'id': 21, 'src': 1,
                 'start': inner_dur, 'duration': inner_dur,
                 'mediaStart': 0, 'mediaDuration': inner_dur, 'scalar': 1},
            ],
        }],
        'effects': [], 'parameters': {}, 'metadata': {}, 'animationTracks': {},
    }


def test_set_speed_group_idempotent() -> None:
    """Calling set_speed twice with the same value should produce the same result."""
    data = _group_data()
    clip = BaseClip(data)
    clip.set_speed(2.0)
    dur_after_first = data['duration']
    inner0_dur_first = data['tracks'][0]['medias'][0]['duration']
    inner1_start_first = data['tracks'][0]['medias'][1]['start']

    clip.set_speed(2.0)
    assert data['duration'] == dur_after_first
    assert data['tracks'][0]['medias'][0]['duration'] == inner0_dur_first
    assert data['tracks'][0]['medias'][1]['start'] == inner1_start_first


def test_set_speed_group_then_reset() -> None:
    """set_speed(2.0) then set_speed(1.0) should restore original values."""
    inner_dur = EDIT_RATE * 5
    data = _group_data(inner_dur)
    orig_dur = data['duration']
    orig_inner_dur = data['tracks'][0]['medias'][0]['duration']
    orig_inner1_start = data['tracks'][0]['medias'][1]['start']

    clip = BaseClip(data)
    clip.set_speed(2.0)
    assert data['duration'] != orig_dur

    clip.set_speed(1.0)
    assert data['duration'] == orig_dur
    assert data['tracks'][0]['medias'][0]['duration'] == orig_inner_dur
    assert data['tracks'][0]['medias'][1]['start'] == orig_inner1_start


def test_set_speed_group_scalar_reset_not_composed() -> None:
    """Inner scalar should be set to scalar_fraction, not composed with old."""
    data = _group_data()
    clip = BaseClip(data)
    clip.set_speed(2.0)
    inner_scalar_1 = Fraction(str(data['tracks'][0]['medias'][0]['scalar']))

    clip.set_speed(3.0)
    inner_scalar_2 = Fraction(str(data['tracks'][0]['medias'][0]['scalar']))

    # Should be 1/3, not 1/2 * 1/3 = 1/6
    assert inner_scalar_2 == Fraction(1, 3)
    assert inner_scalar_1 == Fraction(1, 2)


def _vmfile(start: int = 0, duration: int = 600, **kw) -> dict:
    d = {
        "id": 1, "_type": "VMFile", "src": 1,
        "start": start, "duration": duration,
        "mediaStart": 0, "mediaDuration": duration, "scalar": 1,
    }
    d.update(kw)
    return d


def _group(inner_clips: list[dict], duration: int = 600, scalar=1) -> dict:
    return {
        "id": 10, "_type": "Group", "start": 0,
        "duration": duration, "mediaDuration": duration,
        "scalar": scalar,
        "tracks": [{"medias": inner_clips, "trackIndex": 0}],
        "attributes": {"ident": "G"},
    }


def _stitched(segments: list[dict], duration: int | None = None) -> dict:
    total = sum(s.get("duration", 0) for s in segments)
    return {
        "id": 20, "_type": "StitchedMedia", "start": 0,
        "duration": duration or total, "mediaDuration": total,
        "scalar": 1, "medias": segments,
    }


# -- Bug 1: Group set_speed stores duration/start as int, not string --

class TestSetSpeedGroupStoresIntDuration:
    def test_group_duration_is_int_after_fractional_speed(self):
        inner = _vmfile(start=0, duration=600)
        grp = _group([inner], duration=600)
        clip = BaseClip(grp)
        clip.set_speed(3.0)
        assert isinstance(clip._data["duration"], int)

    def test_group_inner_start_is_int_after_fractional_speed(self):
        inner = _vmfile(start=100, duration=600)
        grp = _group([inner], duration=700)
        clip = BaseClip(grp)
        clip.set_speed(3.0)
        inner_data = clip._data["tracks"][0]["medias"][0]
        assert isinstance(inner_data["start"], int)
        assert isinstance(inner_data["duration"], int)

    def test_group_duration_rounded_correctly(self):
        inner = _vmfile(start=0, duration=100)
        grp = _group([inner], duration=100)
        clip = BaseClip(grp)
        clip.set_speed(3.0)
        # scalar = 1/3, duration = 100 * 1/3 ≈ 33
        assert clip._data["duration"] == 33


# -- Bug 2: StitchedMedia cursor uses round --

class TestSetSpeedStitchedCursorUsesRound:
    def test_stitched_cursor_uses_round(self):
        seg1 = {"id": 21, "_type": "VMFile", "start": 0, "duration": 100,
                "mediaDuration": 100, "scalar": 1, "src": 1}
        seg2 = {"id": 22, "_type": "VMFile", "start": 100, "duration": 100,
                "mediaDuration": 100, "scalar": 1, "src": 1}
        st = _stitched([seg1, seg2])
        clip = BaseClip(st)
        clip.set_speed(3.0)
        # After speed change, segments should have int starts
        for seg in clip._data["medias"]:
            assert isinstance(seg["start"], int)
        assert isinstance(clip._data["duration"], int)


# -- Bug 3: clear_keyframes('opacity') clears animationTracks.visual --

class TestClearKeyframesOpacityClearsAnimationTracks:
    def test_clear_opacity_clears_animation_tracks_visual(self):
        d = _vmfile()
        d["parameters"] = {
            "opacity": {"type": "double", "defaultValue": 1.0,
                        "keyframes": [{"time": 0, "value": 1.0}]},
        }
        d["animationTracks"] = {"visual": [{"time": 0, "value": 1.0}]}
        clip = BaseClip(d)
        clip.clear_keyframes("opacity")
        assert "keyframes" not in clip._data["parameters"]["opacity"]
        assert clip._data["animationTracks"]["visual"] == []

    def test_clear_non_opacity_does_not_touch_animation_tracks(self):
        d = _vmfile()
        d["parameters"] = {
            "scale0": {"type": "double", "defaultValue": 1.0,
                       "keyframes": [{"time": 0, "value": 1.0}]},
        }
        d["animationTracks"] = {"visual": [{"time": 0, "value": 1.0}]}
        clip = BaseClip(d)
        clip.clear_keyframes("scale0")
        assert clip._data["animationTracks"]["visual"] == [{"time": 0, "value": 1.0}]


# -- Bug 2: set_speed Group inner IMFile clips get mediaDuration=1 --

def test_set_speed_group_imfile_media_duration_guard() -> None:
    """set_speed on a Group must set mediaDuration=1 for inner IMFile clips."""
    inner_clip = {
        "_type": "IMFile", "id": 10, "src": 1,
        "start": 0, "duration": EDIT_RATE, "mediaStart": 0,
        "mediaDuration": 1, "scalar": 1,
        "parameters": {}, "effects": [], "metadata": {}, "animationTracks": {},
    }
    group_data = {
        "_type": "Group", "id": 1,
        "start": 0, "duration": EDIT_RATE, "mediaStart": 0,
        "mediaDuration": EDIT_RATE, "scalar": 1,
        "parameters": {}, "effects": [], "metadata": {}, "animationTracks": {},
        "attributes": {"ident": "G"},
        "tracks": [{"trackIndex": 0, "medias": [inner_clip]}],
    }
    from camtasia.timeline.clips import Group
    group = Group(group_data)
    group.set_speed(2.0)
    assert inner_clip["mediaDuration"] == 1


# -- Bug 3: set_speed Group scalar uses consistent format --

def test_set_speed_group_scalar_format_consistency() -> None:
    """set_speed on a Group must use `1` (not `int(scalar_fraction)`) for speed=1.0."""
    inner_clip = {
        "_type": "VMFile", "id": 10, "src": 1,
        "start": 0, "duration": EDIT_RATE * 2, "mediaStart": 0,
        "mediaDuration": EDIT_RATE * 2, "scalar": 1,
        "parameters": {}, "effects": [], "metadata": {}, "animationTracks": {},
    }
    group_data = {
        "_type": "Group", "id": 1,
        "start": 0, "duration": EDIT_RATE * 2, "mediaStart": 0,
        "mediaDuration": EDIT_RATE * 2, "scalar": 1,
        "parameters": {}, "effects": [], "metadata": {}, "animationTracks": {},
        "attributes": {"ident": "G"},
        "tracks": [{"trackIndex": 0, "medias": [inner_clip]}],
    }
    from camtasia.timeline.clips import Group
    group = Group(group_data)
    # Set speed to 2x then back to 1x
    group.set_speed(2.0)
    group.set_speed(1.0)
    assert group_data["scalar"] == 1
    assert inner_clip["scalar"] == 1


class TestIsAudioStitchedMediaEdgeCases:
    def test_empty_stitched_returns_false(self):
        clip = BaseClip({
            '_type': 'StitchedMedia', 'id': 1, 'start': 0,
            'duration': 100, 'mediaDuration': 100, 'scalar': 1,
            'medias': [],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        })
        assert clip.is_audio is False

    def test_non_audio_segment_returns_false(self):
        clip = BaseClip({
            '_type': 'StitchedMedia', 'id': 1, 'start': 0,
            'duration': 100, 'mediaDuration': 100, 'scalar': 1,
            'medias': [
                {'_type': 'AMFile', 'id': 2},
                {'_type': 'VMFile', 'id': 3},  # non-audio
            ],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        })
        assert clip.is_audio is False


class TestAnimateFadeOutLongerThanFadeInLeaves:
    def test_fade_out_larger_than_remaining_clamped(self, project):
        """fade_out > dur - fade_in gets clamped."""
        from camtasia.timing import seconds_to_ticks
        track = project.timeline.tracks[0]
        clip = track.add_clip('VMFile', 0, 0, seconds_to_ticks(2.0))
        # fade_in takes 1.5s, fade_out requested 2.0s — should clamp to 0.5s
        clip.animate(fade_in=1.5, fade_out=2.0)
        # No crash, keyframes valid (no negative time)
        params = clip._data.get('parameters', {})
        opacity = params.get('opacity', {})
        kfs = opacity.get('keyframes', [])
        for kf in kfs:
            assert kf.get('time', 0) >= 0


def _group_with_vmfile_inner() -> dict:
    """Group containing a VMFile inner clip."""
    return {
        "id": 1, "_type": "Group",
        "start": 0, "duration": 1000, "mediaStart": 0,
        "mediaDuration": 1000, "scalar": 1,
        "tracks": [{"trackIndex": 0, "medias": [{
            "id": 2, "_type": "VMFile", "src": 1,
            "start": 0, "duration": 1000, "mediaStart": 0,
            "mediaDuration": 1000, "scalar": 1,
        }]}],
    }


def _group_with_callout_inner() -> dict:
    """Group containing a Callout inner clip."""
    return {
        "id": 1, "_type": "Group",
        "start": 0, "duration": 1000, "mediaStart": 0,
        "mediaDuration": 1000, "scalar": 1,
        "tracks": [{"trackIndex": 0, "medias": [{
            "id": 2, "_type": "Callout",
            "start": 0, "duration": 1000, "mediaStart": 0,
            "mediaDuration": 1000, "scalar": 1,
        }]}],
    }


# -- Bug 1: Group inner mediaDuration recalculated for regular clips --

class TestSetSpeedGroupRecalculatesInnerMediaDuration:
    def test_vmfile_inner_gets_media_duration_recalculated(self):
        data = _group_with_vmfile_inner()
        clip = BaseClip(data)
        clip.set_speed(2.0)
        inner = data["tracks"][0]["medias"][0]
        scalar = Fraction(str(inner["scalar"]))
        assert scalar != 0
        expected_md = Fraction(inner["duration"]) / scalar
        actual_md = Fraction(str(inner["mediaDuration"]))
        assert actual_md == expected_md

    def test_callout_inner_gets_media_duration_recalculated(self):
        data = _group_with_callout_inner()
        clip = BaseClip(data)
        clip.set_speed(0.5)
        inner = data["tracks"][0]["medias"][0]
        scalar = Fraction(str(inner["scalar"]))
        expected_md = Fraction(inner["duration"]) / scalar
        actual_md = Fraction(str(inner["mediaDuration"]))
        assert actual_md == expected_md

    def test_imfile_inner_keeps_media_duration_1(self):
        data = {
            "id": 1, "_type": "Group",
            "start": 0, "duration": 1000, "mediaStart": 0,
            "mediaDuration": 1000, "scalar": 1,
            "tracks": [{"trackIndex": 0, "medias": [{
                "id": 2, "_type": "IMFile", "src": 1,
                "start": 0, "duration": 1000, "mediaStart": 0,
                "mediaDuration": 1, "scalar": 1,
            }]}],
        }
        clip = BaseClip(data)
        clip.set_speed(2.0)
        assert data["tracks"][0]["medias"][0]["mediaDuration"] == 1


# -- Bug 2: UnifiedMedia is_audio --

class TestIsAudioStandaloneUnifiedMedia:
    def test_audio_only_unified_media(self):
        data = {
            "id": 1, "_type": "UnifiedMedia",
            "video": None,
            "audio": {"id": 2, "_type": "AMFile"},
            "start": 0, "duration": 1000,
        }
        clip = BaseClip(data)
        assert clip.is_audio is True

    def test_video_unified_media_not_audio(self):
        data = {
            "id": 1, "_type": "UnifiedMedia",
            "video": {"id": 2, "_type": "VMFile"},
            "audio": {"id": 3, "_type": "AMFile"},
            "start": 0, "duration": 1000,
        }
        clip = BaseClip(data)
        assert clip.is_audio is False

    def test_no_video_key_unified_media(self):
        data = {
            "id": 1, "_type": "UnifiedMedia",
            "audio": {"id": 2, "_type": "AMFile"},
            "start": 0, "duration": 1000,
        }
        clip = BaseClip(data)
        assert clip.is_audio is True


# -- Bug 3: StitchedMedia set_speed start/duration consistency --

class TestSetSpeedStitchedStartsMatchDurations:
    def test_starts_are_consistent_with_durations(self):
        data = {
            "id": 1, "_type": "StitchedMedia",
            "start": 0, "duration": 3000, "mediaStart": 0,
            "mediaDuration": 3000, "scalar": 1,
            "medias": [
                {"id": 2, "_type": "VMFile", "start": 0, "duration": 1000,
                 "mediaDuration": 1000, "scalar": 1},
                {"id": 3, "_type": "VMFile", "start": 1000, "duration": 1000,
                 "mediaDuration": 1000, "scalar": 1},
                {"id": 4, "_type": "VMFile", "start": 2000, "duration": 1000,
                 "mediaDuration": 1000, "scalar": 1},
            ],
        }
        clip = BaseClip(data)
        clip.set_speed(3.0)
        medias = data["medias"]
        for i in range(len(medias) - 1):
            assert medias[i]["start"] + medias[i]["duration"] == medias[i + 1]["start"]
        assert data["duration"] == sum(m["duration"] for m in medias)

    def test_durations_are_always_int(self):
        data = {
            "id": 1, "_type": "StitchedMedia",
            "start": 0, "duration": 3000, "mediaStart": 0,
            "mediaDuration": 3000, "scalar": 1,
            "medias": [
                {"id": 2, "_type": "VMFile", "start": 0, "duration": 1000,
                 "mediaDuration": 1000, "scalar": 1},
                {"id": 3, "_type": "VMFile", "start": 1000, "duration": 2000,
                 "mediaDuration": 2000, "scalar": 1},
            ],
        }
        clip = BaseClip(data)
        clip.set_speed(3.0)
        for m in data["medias"]:
            assert isinstance(m["duration"], int)
            assert isinstance(m["start"], int)


# -- Bug 4: Group→StitchedMedia int truncation --

class TestSetSpeedGroupNestedStitchedUsesRound:
    def test_stitched_inner_starts_use_round(self):
        data = {
            "id": 1, "_type": "Group",
            "start": 0, "duration": 6000, "mediaStart": 0,
            "mediaDuration": 6000, "scalar": 1,
            "tracks": [{"trackIndex": 0, "medias": [{
                "id": 2, "_type": "StitchedMedia",
                "start": 0, "duration": 6000, "mediaStart": 0,
                "mediaDuration": 6000, "scalar": 1,
                "medias": [
                    {"id": 3, "_type": "VMFile", "start": 0, "duration": 3000,
                     "mediaDuration": 3000, "scalar": 1},
                    {"id": 4, "_type": "VMFile", "start": 3000, "duration": 3000,
                     "mediaDuration": 3000, "scalar": 1},
                ],
            }]}],
        }
        clip = BaseClip(data)
        clip.set_speed(3.0)
        inner_stitched = data["tracks"][0]["medias"][0]
        medias = inner_stitched["medias"]
        for i in range(len(medias) - 1):
            assert medias[i]["start"] + round(Fraction(str(medias[i]["duration"]))) == medias[i + 1]["start"]


# ------------------------------------------------------------------
# is_video: UnifiedMedia checks video presence (Bug 1)
# ------------------------------------------------------------------

class TestIsVideoUnifiedMediaChecksVideoPresence:
    def test_unified_media_with_video_is_video(self) -> None:
        clip = BaseClip({'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
                         'video': {'_type': 'VMFile', 'id': 2}, 'audio': {'_type': 'AMFile', 'id': 3}})
        assert clip.is_video is True

    def test_unified_media_without_video_is_not_video(self) -> None:
        clip = BaseClip({'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
                         'audio': {'_type': 'AMFile', 'id': 3}})
        assert clip.is_video is False

    def test_unified_media_with_none_video_is_not_video(self) -> None:
        clip = BaseClip({'id': 1, '_type': 'UnifiedMedia', 'start': 0, 'duration': 100,
                         'video': None, 'audio': {'_type': 'AMFile', 'id': 3}})
        assert clip.is_video is False


# ------------------------------------------------------------------
# is_video: StitchedMedia with UnifiedMedia None video (Bug 2)
# ------------------------------------------------------------------

class TestIsVideoStitchedMediaUnifiedMediaNoneVideo:
    def test_stitched_with_unified_none_video_is_not_video(self) -> None:
        clip = BaseClip({'id': 1, '_type': 'StitchedMedia', 'start': 0, 'duration': 100,
                         'medias': [{'_type': 'UnifiedMedia', 'video': None}]})
        assert clip.is_video is False

    def test_stitched_with_unified_valid_video_is_video(self) -> None:
        clip = BaseClip({'id': 1, '_type': 'StitchedMedia', 'start': 0, 'duration': 100,
                         'medias': [{'_type': 'UnifiedMedia', 'video': {'_type': 'VMFile'}}]})
        assert clip.is_video is True


# ------------------------------------------------------------------
# fade_in/fade_out: repeated calls don't accumulate visual tracks (Bug 3)
# ------------------------------------------------------------------

class TestFadeInOutDoNotAccumulateVisualTracks:
    def test_repeated_fade_in_does_not_accumulate(self) -> None:
        data: dict[str, Any] = _coverage_clip(duration=EDIT_RATE * 10)
        clip = BaseClip(data)
        clip.fade_in(1.0)
        clip.fade_in(2.0)
        visual = data.get('animationTracks', {}).get('visual', [])
        assert len(visual) == 1

    def test_repeated_fade_out_does_not_accumulate(self) -> None:
        data: dict[str, Any] = _coverage_clip(duration=EDIT_RATE * 10)
        clip = BaseClip(data)
        clip.fade_out(1.0)
        clip.fade_out(2.0)
        visual = data.get('animationTracks', {}).get('visual', [])
        assert len(visual) == 1


# ------------------------------------------------------------------
# set_speed: Group inner UnifiedMedia mediaDuration recalc (Bug 4)
# ------------------------------------------------------------------

class TestSetSpeedGroupInnerUnifiedMediaDurationRecalc:
    def test_group_inner_unified_media_gets_media_duration(self) -> None:
        inner_um = {
            '_type': 'UnifiedMedia', 'id': 10, 'start': 0,
            'duration': EDIT_RATE * 10, 'mediaStart': 0,
            'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
            'video': {'_type': 'VMFile', 'id': 11, 'start': 0,
                      'duration': EDIT_RATE * 10, 'mediaDuration': EDIT_RATE * 10, 'scalar': 1},
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        data: dict[str, Any] = {
            'id': 1, '_type': 'Group', 'start': 0,
            'duration': EDIT_RATE * 10, 'mediaStart': 0,
            'mediaDuration': EDIT_RATE * 10, 'scalar': 1,
            'tracks': [{'trackIndex': 0, 'medias': [inner_um]}],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        clip = BaseClip(data)
        clip.set_speed(2.0)
        inner = data['tracks'][0]['medias'][0]
        assert 'mediaDuration' in inner
        assert Fraction(str(inner['mediaDuration'])) == Fraction(inner['duration']) / Fraction(str(inner['scalar']))


# ------------------------------------------------------------------
# set_speed: StitchedMedia propagates to UnifiedMedia sub-clips (Bug 5)
# ------------------------------------------------------------------

class TestSetSpeedStitchedMediaPropagatesUnifiedMedia:
    def test_stitched_propagates_scalar_to_unified_sub_clips(self) -> None:
        inner_um = {
            '_type': 'UnifiedMedia', 'id': 20, 'start': 0,
            'duration': EDIT_RATE * 5, 'mediaStart': 0,
            'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
            'video': {'_type': 'VMFile', 'id': 21, 'start': 0,
                      'duration': EDIT_RATE * 5, 'mediaDuration': EDIT_RATE * 5, 'scalar': 1},
            'metadata': {},
        }
        data: dict[str, Any] = {
            'id': 1, '_type': 'StitchedMedia', 'start': 0,
            'duration': EDIT_RATE * 5, 'mediaStart': 0,
            'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
            'medias': [inner_um],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        clip = BaseClip(data)
        clip.set_speed(2.0)
        seg = data['medias'][0]
        video = seg['video']
        assert video['scalar'] == seg['scalar']
        assert video['duration'] == seg['duration']
        assert video['start'] == seg['start']


# ------------------------------------------------------------------
# set_speed: Group-nested StitchedMedia propagates to UnifiedMedia (Bug 6)
# ------------------------------------------------------------------

class TestSetSpeedGroupNestedStitchedMediaPropagatesUnifiedMedia:
    def test_group_stitched_inner_unified_propagated(self) -> None:
        inner_um = {
            '_type': 'UnifiedMedia', 'id': 30, 'start': 0,
            'duration': EDIT_RATE * 5, 'mediaStart': 0,
            'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
            'video': {'_type': 'VMFile', 'id': 31, 'start': 0,
                      'duration': EDIT_RATE * 5, 'mediaDuration': EDIT_RATE * 5, 'scalar': 1},
            'metadata': {},
        }
        stitched = {
            '_type': 'StitchedMedia', 'id': 32, 'start': 0,
            'duration': EDIT_RATE * 5, 'mediaStart': 0,
            'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
            'medias': [inner_um],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        data: dict[str, Any] = {
            'id': 1, '_type': 'Group', 'start': 0,
            'duration': EDIT_RATE * 5, 'mediaStart': 0,
            'mediaDuration': EDIT_RATE * 5, 'scalar': 1,
            'tracks': [{'trackIndex': 0, 'medias': [stitched]}],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        clip = BaseClip(data)
        clip.set_speed(2.0)
        seg = data['tracks'][0]['medias'][0]['medias'][0]
        video = seg['video']
        assert video['scalar'] == seg['scalar']
        assert video['duration'] == seg['duration']


# ------------------------------------------------------------------
# duration/scalar setter: StitchedMedia re-layouts inner segments (Bug 7)
# ------------------------------------------------------------------

class TestDurationSetterStitchedMediaRelayout:
    def test_duration_setter_relayouts_stitched_segments(self) -> None:
        data: dict[str, Any] = {
            'id': 1, '_type': 'StitchedMedia', 'start': 0,
            'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
            'medias': [
                {'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 400,
                 'mediaDuration': 400, 'scalar': 1},
                {'_type': 'VMFile', 'id': 3, 'start': 400, 'duration': 600,
                 'mediaDuration': 600, 'scalar': 1},
            ],
        }
        clip = BaseClip(data)
        clip.duration = 2000
        seg0 = data['medias'][0]
        seg1 = data['medias'][1]
        assert seg0['duration'] + seg1['duration'] == 2000
        assert seg0['start'] == 0
        assert seg1['start'] == seg0['duration']


class TestScalarSetterStitchedMediaRelayout:
    def test_scalar_setter_relayouts_stitched_segments(self) -> None:
        data: dict[str, Any] = {
            'id': 1, '_type': 'StitchedMedia', 'start': 0,
            'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1,
            'medias': [
                {'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 500,
                 'mediaDuration': 500, 'scalar': 1},
                {'_type': 'VMFile', 'id': 3, 'start': 500, 'duration': 500,
                 'mediaDuration': 500, 'scalar': 1},
            ],
        }
        clip = BaseClip(data)
        clip.scalar = Fraction(1, 2)
        seg0 = data['medias'][0]
        seg1 = data['medias'][1]
        assert seg0['start'] == 0
        assert seg1['start'] == seg0['duration']


class TestSetSpeedStitchedInGroupDurationAlwaysInt:
    """Bug 2: set_speed on Group with StitchedMedia inner segments must produce int duration."""

    def test_duration_is_int_not_string(self):
        data = {
            '_type': 'Group', 'id': 1, 'start': 0, 'duration': 1000,
            'mediaDuration': 1000, 'scalar': 1,
            'tracks': [{'trackIndex': 0, 'medias': [{
                '_type': 'StitchedMedia', 'id': 2, 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1,
                'medias': [
                    {'_type': 'VMFile', 'id': 3, 'start': 0, 'duration': 500,
                     'mediaDuration': 500, 'scalar': 1},
                    {'_type': 'VMFile', 'id': 4, 'start': 500, 'duration': 500,
                     'mediaDuration': 500, 'scalar': 1},
                ],
            }]}],
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        clip = BaseClip(data)
        clip.set_speed(3.0)
        for seg in data['tracks'][0]['medias'][0]['medias']:
            assert isinstance(seg['duration'], int), f"duration should be int, got {type(seg['duration'])}"


class TestDurationSetterStitchedMediaUnifiedMediaPropagation:
    """Bug 3: duration setter on StitchedMedia must propagate to UnifiedMedia sub-clips."""

    def test_inner_unified_media_gets_start_and_duration(self):
        data = {
            '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 1000,
            'mediaDuration': 1000, 'scalar': 1,
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 2, 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1,
                'video': {'_type': 'VMFile', 'id': 3, 'start': 0, 'duration': 1000,
                          'mediaDuration': 1000, 'scalar': 1},
                'audio': {'_type': 'AMFile', 'id': 4, 'start': 0, 'duration': 1000,
                          'mediaDuration': 1000, 'scalar': 1},
            }],
        }
        clip = BaseClip(data)
        clip.duration = 2000
        inner = data['medias'][0]
        assert inner['video']['start'] == inner['start']
        assert inner['video']['duration'] == inner['duration']
        assert inner['audio']['start'] == inner['start']
        assert inner['audio']['duration'] == inner['duration']


class TestScalarSetterStitchedMediaUnifiedMediaPropagation:
    """Bug 4: scalar setter on StitchedMedia must propagate to UnifiedMedia sub-clips."""

    def test_inner_unified_media_gets_start_and_duration(self):
        data = {
            '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 1000,
            'mediaDuration': 1000, 'scalar': 1,
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 2, 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1,
                'video': {'_type': 'VMFile', 'id': 3, 'start': 0, 'duration': 1000,
                          'mediaDuration': 1000, 'scalar': 1},
                'audio': {'_type': 'AMFile', 'id': 4, 'start': 0, 'duration': 1000,
                          'mediaDuration': 1000, 'scalar': 1},
            }],
        }
        clip = BaseClip(data)
        clip.scalar = Fraction(1, 2)
        inner = data['medias'][0]
        assert inner['video']['start'] == inner['start']
        assert inner['video']['duration'] == inner['duration']
        assert inner['audio']['start'] == inner['start']
        assert inner['audio']['duration'] == inner['duration']


def test_set_position_keyframes_accepts_interp_mode():
    """set_position_keyframes writes the specified interp mode onto all keyframes."""
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.set_position_keyframes([(0.0, 0, 0), (2.0, 100, 100)], interp='eioe')
    kfs = clip._data['parameters']['translation0']['keyframes']
    assert all(kf['interp'] == 'eioe' for kf in kfs)


def test_set_position_keyframes_with_interp_per_keyframe():
    """Per-keyframe interp allows heterogeneous easing (e.g., ease in then linear)."""
    t = seconds_to_ticks
    media = {'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(10.0)}
    track = _make_track(medias=[media])
    clip = next(iter(track.clips))
    clip.set_position_keyframes_with_interp([
        (0.0, 0, 0, 'easi'),
        (1.0, 50, 50, 'linr'),
        (2.0, 100, 100, 'easo'),
    ])
    kfs = clip._data['parameters']['translation0']['keyframes']
    assert [kf['interp'] for kf in kfs] == ['easi', 'linr', 'easo']
