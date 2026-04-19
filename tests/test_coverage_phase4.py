"""Targeted tests to cover remaining gaps in timeline, visual, base, project, group."""
from __future__ import annotations

import copy
import json
import warnings
from fractions import Fraction
from pathlib import Path

import pytest

from camtasia.timing import seconds_to_ticks

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


@pytest.fixture
def project(tmp_path):
    import shutil
    src = RESOURCES / 'new.cmproj'
    dst = tmp_path / 'new.cmproj'
    shutil.copytree(src, dst)
    from camtasia.project import load_project
    return load_project(dst)


# ── timeline.py: _remap_clip_ids_recursive (lines 35-44) ──

def test_remap_clip_ids_recursive_with_video_audio_and_tracks():
    from camtasia.timeline.timeline import _remap_clip_ids_recursive
    clip = {
        'id': 100,
        'video': {'id': 200},
        'audio': {'id': 300},
        'tracks': [{'medias': [{'id': 400}]}],
    }
    counter = [1]
    _remap_clip_ids_recursive(clip, counter)
    assert clip['id'] == 1
    assert clip['video']['id'] == 2
    assert clip['audio']['id'] == 3
    assert clip['tracks'][0]['medias'][0]['id'] == 4
    assert counter[0] == 5


# ── timeline.py: _remap_clip_ids_with_map (lines 48-58) ──

def test_remap_clip_ids_with_map():
    from camtasia.timeline.timeline import _remap_clip_ids_with_map
    clip = {
        'id': 10,
        'video': {'id': 20},
        'tracks': [{'medias': [{'id': 30}]}],
    }
    counter = [100]
    id_map: dict[int, int] = {}
    _remap_clip_ids_with_map(clip, counter, id_map)
    assert id_map == {10: 100, 20: 101, 30: 102}
    assert clip['id'] == 100


# ── timeline.py: group_clips_in_range (lines 1028-1040) ──

def test_group_clips_in_range(project):
    tl = project.timeline
    track = tl.tracks[0]
    clip = track.add_video(1, start_seconds=0, duration_seconds=5)
    clip_id = clip.id
    group = tl.group_clips_in_range(0.0, 5.0, 0)
    assert group is not None


def test_group_clips_in_range_no_clips(project):
    tl = project.timeline
    with pytest.raises(ValueError, match='No clips found'):
        tl.group_clips_in_range(100.0, 200.0, 0)


# ── timeline.py: build_section_timeline (lines 1056-1100) ──

def test_build_section_timeline(project):
    tl = project.timeline
    t0 = tl.tracks[0]
    c1 = t0.add_video(1, start_seconds=0, duration_seconds=3)
    c2 = t0.add_video(1, start_seconds=5, duration_seconds=3)
    tl.build_section_timeline(
        [(c1.id, None), (c2.id, 'FadeThrough')],
        target_track_index=0,
        transition_duration_seconds=0.5,
    )
    # c1 should start at 0, c2 should follow
    assert c1._data['start'] == 0


def test_build_section_timeline_clip_not_found(project):
    tl = project.timeline
    with pytest.raises(KeyError, match='Clip 9999 not found'):
        tl.build_section_timeline([(9999, None)], 0)


def test_build_section_timeline_moves_clip_across_tracks(project):
    tl = project.timeline
    t0 = tl.tracks[0]
    t1 = tl.get_or_create_track('Track2')
    c1 = t0.add_video(1, start_seconds=0, duration_seconds=2)
    c2 = t1.add_video(1, start_seconds=0, duration_seconds=2)
    tl.build_section_timeline(
        [(c1.id, None), (c2.id, 'FadeThrough')],
        target_track_index=0,
    )


# ── timeline.py: line 569 (_register_ids in duplicate_track) ──

def test_duplicate_track_registers_ids(project):
    tl = project.timeline
    t0 = tl.tracks[0]
    t0.add_video(1, start_seconds=0, duration_seconds=3)
    tl.duplicate_track(0)
    assert tl.track_count >= 2


# ── visual.py: RoundCorners getters (lines 36, 46, 56, 66) ──

def test_round_corners_properties():
    from camtasia.effects.visual import RoundCorners
    data = {
        'effectName': 'RoundCorners',
        'parameters': {
            'radius': 10.0,
            'top-left': 1.0,
            'top-right': 0.0,
            'bottom-left': 1.0,
            'bottom-right': 0.0,
        },
    }
    rc = RoundCorners(data)
    assert rc.top_left is True
    assert rc.top_right is False
    assert rc.bottom_left is True
    assert rc.bottom_right is False
    rc.top_left = False
    rc.top_right = True
    rc.bottom_left = False
    rc.bottom_right = True
    assert rc.top_right is True
    assert rc.bottom_right is True


# ── visual.py: DropShadow getters (lines 107, 126, 136, 146) ──

def test_drop_shadow_properties():
    from camtasia.effects.visual import DropShadow
    data = {
        'effectName': 'DropShadow',
        'parameters': {
            'angle': 0.5,
            'enabled': 1,
            'offset': 5.0,
            'blur': 3.0,
            'opacity': 0.8,
            'color-red': 0.0,
            'color-green': 0.0,
            'color-blue': 0.0,
            'color-alpha': 1.0,
        },
    }
    ds = DropShadow(data)
    assert ds.angle == 0.5
    assert ds.offset == 5.0
    assert ds.blur == 3.0
    assert ds.opacity == 0.8
    ds.angle = 1.0
    ds.offset = 10.0
    ds.blur = 5.0
    ds.opacity = 0.5
    assert ds.angle == 1.0
    assert ds.offset == 10.0
    assert ds.blur == 5.0
    assert ds.opacity == 0.5


# ── visual.py: Mask properties (lines 208-278) ──

def test_mask_properties():
    from camtasia.effects.visual import Mask
    data = {
        'effectName': 'Mask',
        'parameters': {
            'mask-shape': 1,
            'mask-opacity': 0.9,
            'mask-blend': 0.5,
            'mask-invert': 0,
            'mask-rotation': 1.57,
            'mask-width': 100.0,
            'mask-height': 200.0,
            'mask-positionX': 0.5,
            'mask-positionY': 0.5,
            'mask-cornerRadius': 10.0,
        },
    }
    m = Mask(data)
    assert m.mask_opacity == pytest.approx(0.9)
    assert m.mask_blend == pytest.approx(0.5)
    assert m.mask_invert == 0
    assert m.mask_rotation == pytest.approx(1.57)
    assert m.mask_width == pytest.approx(100.0)
    assert m.mask_height == pytest.approx(200.0)
    assert m.mask_position_x == pytest.approx(0.5)
    assert m.mask_position_y == pytest.approx(0.5)
    assert m.mask_corner_radius == pytest.approx(10.0)
    # setters
    m.mask_opacity = 0.5
    m.mask_blend = 0.3
    m.mask_invert = 1
    m.mask_rotation = 3.14
    m.mask_width = 50.0
    m.mask_height = 50.0
    m.mask_position_x = 0.2
    m.mask_position_y = 0.8
    m.mask_corner_radius = 5.0
    assert m.mask_opacity == pytest.approx(0.5)


# ── visual.py: BlurRegion properties (lines 346-371) ──

def test_blur_region_properties():
    from camtasia.effects.visual import BlurRegion
    data = {
        'effectName': 'BlurRegion',
        'parameters': {
            'sigma': 5.0,
            'mask-cornerRadius': 8.0,
            'mask-invert': 0,
            'color-alpha': 0.5,
        },
    }
    br = BlurRegion(data)
    assert br.sigma == 5.0
    assert br.mask_corner_radius == 8.0
    assert br.mask_invert == 0
    assert br.color_alpha == 0.5
    br.sigma = 10.0
    br.mask_corner_radius = 12.0
    br.mask_invert = 1
    br.color_alpha = 1.0
    assert br.sigma == 10.0


# ── cursor.py: CursorShadow properties (lines 19-86) ──

def test_cursor_shadow_properties():
    from camtasia.effects.cursor import CursorShadow
    data = {
        'effectName': 'CursorShadow',
        'parameters': {
            'enabled': 1,
            'angle': 0.5,
            'offset': 3.0,
            'blur': 2.0,
            'opacity': 0.7,
            'color-red': 0.0,
            'color-green': 0.0,
            'color-blue': 0.0,
            'color-alpha': 1.0,
        },
    }
    cs = CursorShadow(data)
    assert cs.enabled == 1
    assert cs.angle == 0.5
    assert cs.offset == 3.0
    assert cs.blur == 2.0
    assert cs.opacity == 0.7
    assert cs.color == (0.0, 0.0, 0.0, 1.0)
    cs.enabled = 0
    cs.angle = 1.0
    cs.offset = 5.0
    cs.blur = 4.0
    cs.opacity = 0.5
    cs.color = (1.0, 0.0, 0.0, 0.5)
    assert cs.enabled == 0


def test_cursor_motion_blur():
    from camtasia.effects.cursor import CursorMotionBlur
    data = {'effectName': 'CursorMotionBlur', 'parameters': {'intensity': 0.5}}
    cmb = CursorMotionBlur(data)
    assert cmb.intensity == 0.5
    cmb.intensity = 1.0
    assert cmb.intensity == 1.0


# ── base.py: is_audio for StitchedMedia (line 61-62) ──

def test_base_clip_is_audio_stitched_media():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'StitchedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'medias': [{'_type': 'AMFile'}],
    })
    assert clip.is_audio is True


def test_base_clip_is_video_stitched_media():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'StitchedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'medias': [{'_type': 'VMFile'}],
    })
    assert clip.is_video is True


# ── base.py: is_muted / mute for UnifiedMedia (lines 201, 216) ──

def test_base_clip_is_muted_unified_media():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'audio': {'attributes': {'gain': 0.0}},
    })
    assert clip.is_muted is True


def test_base_clip_mute_unified_media():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'audio': {'attributes': {'gain': 1.0}},
    })
    clip.mute()
    assert clip._data['audio']['attributes']['gain'] == 0.0


def test_base_clip_mute_unified_media_no_audio():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
    })
    with pytest.raises(ValueError, match='no audio'):
        clip.mute()


# ── base.py: media_start setter with Fraction (line 236, 241-244) ──

def test_base_clip_media_start_fraction():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'video': {'start': 0, 'mediaStart': 0},
        'audio': {'start': 0, 'mediaStart': 0},
    })
    clip.media_start = Fraction(1, 3)
    assert clip._data['mediaStart'] == '1/3'
    assert clip._data['video']['mediaStart'] == '1/3'
    # Integer fraction
    clip.media_start = Fraction(10, 1)
    assert clip._data['mediaStart'] == 10


# ── base.py: opacity setter with dict (lines 419-420) ──

def test_base_clip_opacity_setter_dict():
    from camtasia.timeline.clips.base import BaseClip
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


# ── base.py: volume setter with dict (lines 442-443) ──

def test_base_clip_volume_setter_dict():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'VMFile',
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {'volume': {'type': 'double', 'defaultValue': 1.0, 'keyframes': []}},
    })
    clip.volume = 0.5
    assert clip._data['parameters']['volume']['defaultValue'] == 0.5


# ── base.py: is_silent for UnifiedMedia (line 451) ──

def test_base_clip_is_silent_unified_media():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'audio': {'attributes': {'gain': 0.0}},
    })
    assert clip.is_silent is True


# ── base.py: set_start_seconds for UnifiedMedia (lines 580-583) ──

def test_base_clip_set_start_seconds_unified():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'UnifiedMedia',
        'id': 1, 'start': 0, 'duration': 100,
        'video': {'start': 0},
        'audio': {'start': 0},
    })
    clip.set_start_seconds(2.0)
    expected = seconds_to_ticks(2.0)
    assert clip._data['start'] == expected
    assert clip._data['video']['start'] == expected
    assert clip._data['audio']['start'] == expected


# ── base.py: set_opacity with dict (lines 906-907, 912) ──

def test_base_clip_set_opacity_method_dict():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'VMFile',
        'id': 1, 'start': 0, 'duration': 100,
        'parameters': {'opacity': {'type': 'double', 'defaultValue': 1.0, 'keyframes': []}},
        'animationTracks': {'visual': [{'key': 'val'}]},
    })
    clip.set_opacity(0.3)
    assert clip._data['parameters']['opacity']['defaultValue'] == 0.3
    assert clip._data['animationTracks']['visual'] == []


# ── base.py: source_path deprecation (line 1633-1634) ──

def test_base_clip_source_path_deprecation():
    from camtasia.timeline.clips.base import BaseClip
    clip = BaseClip({
        '_type': 'VMFile',
        'id': 1, 'start': 0, 'duration': 100,
        'src': 42,
    })
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        result = clip.source_path
        assert result == 42
        assert len(w) == 1
        assert 'deprecated' in str(w[0].message).lower()


# ── project.py: _remap_src_recursive (lines 143-148) ──

def test_remap_src_recursive():
    from camtasia.project import _remap_src_recursive
    clip = {
        'src': 1,
        'video': {'src': 1},
        'audio': {'src': 2},
        'tracks': [{'medias': [{'src': 1}]}],
        'medias': [{'src': 2}],
    }
    _remap_src_recursive(clip, {1: 10, 2: 20})
    assert clip['src'] == 10
    assert clip['video']['src'] == 10
    assert clip['audio']['src'] == 20
    assert clip['tracks'][0]['medias'][0]['src'] == 10
    assert clip['medias'][0]['src'] == 20


# ── project.py: has_screen_recording (line 369) ──

def test_has_screen_recording_false(project):
    assert project.has_screen_recording is False


def test_has_screen_recording_screen_vm_file(project):
    t = project.timeline.tracks[0]
    t._data.setdefault('medias', []).append({
        '_type': 'ScreenVMFile',
        'id': 999, 'start': 0, 'duration': 100,
    })
    assert project.has_screen_recording is True


def test_has_screen_recording_unified_media(project):
    t = project.timeline.tracks[0]
    t._data.setdefault('medias', []).append({
        '_type': 'UnifiedMedia',
        'id': 998, 'start': 0, 'duration': 100,
        'video': {'_type': 'ScreenVMFile'},
    })
    assert project.has_screen_recording is True


# ── project.py: swap_tracks short attrs warning (lines 413-414) ──

def test_swap_tracks_short_attrs_warning(project):
    """Exercise the warning branch in Project.swap_tracks (lines 413-414)."""
    from unittest.mock import MagicMock
    tl = project.timeline
    # Create mock tracks at high indices
    mock_a = MagicMock()
    mock_a.index = 5
    mock_a._data = {'trackIndex': 5}
    mock_b = MagicMock()
    mock_b.index = 6
    mock_b._data = {'trackIndex': 6}
    # Ensure _track_list is long enough
    while len(tl._track_list) <= 6:
        tl._track_list.append({'medias': [], 'trackIndex': len(tl._track_list)})
    # Set trackAttributes to a short list (not None, but shorter than max index)
    tl._data['trackAttributes'] = [{'ident': ''}]
    from unittest.mock import patch
    with patch.object(type(tl), 'find_track_by_name', side_effect=[mock_a, mock_b]):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            project.swap_tracks('A', 'B')
            warns = [x for x in w if 'trackAttributes too short' in str(x.message)]
            assert len(warns) >= 1


# ── project.py: validate overlapping clips (line 871) ──

def test_validate_overlapping_clips(project):
    t = project.timeline.tracks[0]
    t.add_video(1, start_seconds=0, duration_seconds=5)
    t.add_video(1, start_seconds=2, duration_seconds=5)
    issues = project.validate()
    overlap_issues = [i for i in issues if 'Overlapping' in str(i)]
    assert len(overlap_issues) >= 1


# ── project.py: save with NaN/Infinity (lines 969-972) ──

def test_save_handles_infinity_nan(project, tmp_path):
    # Inject a NaN and Infinity into project data
    project._data.setdefault('parameters', {})['testNaN'] = float('nan')
    project._data['parameters']['testInf'] = float('inf')
    project._data['parameters']['testNegInf'] = float('-inf')
    project.save()  # Should not raise


# ── project.py: normalize_audio (lines 2367-2370) ──

def test_normalize_audio(project):
    t = project.timeline.tracks[0]
    # Add a UnifiedMedia clip with audio
    clip = t.add_video(1, start_seconds=0, duration_seconds=2)
    clip._data['_type'] = 'UnifiedMedia'
    clip._data['audio'] = {'_type': 'AMFile', 'attributes': {'gain': 0.5}, 'start': 0, 'duration': 100}
    clip._data['video'] = {'_type': 'VMFile', 'start': 0, 'duration': 100, 'src': 1, 'id': clip.id + 100}
    count = project.normalize_audio(target_gain=0.8)
    assert count >= 1
    assert clip._data['audio']['attributes']['gain'] == 0.8


# ── project.py: rescale_timeline (lines 2357-2360) ──

def test_rescale_timeline(project):
    t = project.timeline.tracks[0]
    t.add_video(1, start_seconds=0, duration_seconds=5)
    project.rescale_timeline(1.1)


# ── group.py: GroupTrack.transitions raises (line 57) ──

def test_group_track_transitions_raises():
    from camtasia.timeline.clips.group import GroupTrack
    gt = GroupTrack({'medias': []})
    with pytest.raises(AttributeError, match='do not support transitions'):
        gt.transitions


# ── group.py: Group.set_source raises (line 137) ──

def test_group_set_source_raises():
    from camtasia.timeline.clips.group import Group
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 100,
        'tracks': [],
    })
    with pytest.raises(TypeError, match='do not have a source'):
        g.set_source(1)


# ── group.py: set_internal_segment_speeds >8 warning (lines 423-424) ──

def test_set_internal_segment_speeds_warns_over_8():
    from camtasia.timeline.clips.group import Group
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 10000,
        'tracks': [{'medias': [{'_type': 'ScreenVMFile', 'id': 10, 'start': 0, 'duration': 10000,
                                 'src': 1, 'mediaStart': 0, 'mediaDuration': 10000,
                                 'attributes': {'ident': ''}, 'trackNumber': 0}]}],
    })
    segments = [(i * 0.1, (i + 1) * 0.1, 0.1) for i in range(9)]
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        g.set_internal_segment_speeds(segments)
        warns = [x for x in w if '>8' in str(x.message)]
        assert len(warns) >= 1


# ── group.py: canvas scaling with aspect ratio mismatch (lines 529-536) ──

def test_set_internal_segment_speeds_canvas_aspect_mismatch():
    from camtasia.timeline.clips.group import Group
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 10000,
        'attributes': {'widthAttr': 1920, 'heightAttr': 1080},
        'tracks': [{'medias': [{'_type': 'ScreenVMFile', 'id': 10, 'start': 0, 'duration': 10000,
                                 'src': 1, 'mediaStart': 0, 'mediaDuration': 10000,
                                 'attributes': {'ident': ''}, 'trackNumber': 0}]}],
    })
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        g.set_internal_segment_speeds(
            [(0, 5.0, 5.0)],
            canvas_width=800,
            canvas_height=800,
            source_width=1920,
            source_height=1080,
        )
        warns = [x for x in w if 'aspect ratio' in str(x.message)]
        assert len(warns) >= 1


def test_set_internal_segment_speeds_source_bin_resolve():
    """Exercise source_bin auto-resolve path (group.py lines 470-476)."""
    from camtasia.timeline.clips.group import Group
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 10000,
        'tracks': [{'medias': [{'_type': 'ScreenVMFile', 'id': 10, 'start': 0, 'duration': 10000,
                                 'src': 42, 'mediaStart': 0, 'mediaDuration': 10000,
                                 'attributes': {'ident': ''}, 'trackNumber': 0}]}],
    })
    source_bin = [
        {'id': 42, 'sourceTracks': [{'trackRect': [0, 0, 3840, 2160]}]},
    ]
    g.set_internal_segment_speeds(
        [(0, 5.0, 5.0)],
        canvas_width=1920,
        canvas_height=1080,
        source_bin=source_bin,
    )


# ── group.py: trim_to_group_duration (line 590) ──

def test_group_trim_to_group_duration():
    from camtasia.timeline.clips.group import Group
    g = Group({
        '_type': 'Group',
        'id': 1, 'start': 0, 'duration': 500,
        'tracks': [{'medias': [
            {'_type': 'VMFile', 'id': 10, 'start': 0, 'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000, 'scalar': 1},
            {'_type': 'IMFile', 'id': 11, 'start': 0, 'duration': 1000, 'mediaStart': 0, 'mediaDuration': 1000},
        ]}],
    })
    g.sync_internal_durations()
    assert g._data['tracks'][0]['medias'][0]['duration'] == 500
    assert g._data['tracks'][0]['medias'][1]['mediaDuration'] == 1


# ── effects/__init__.py: EffectSchema raises (line 23) ──

def test_effect_schema_raises():
    from camtasia.effects import EffectSchema
    with pytest.raises(RuntimeError, match='marshmallow'):
        EffectSchema()


# ── effects/behaviors.py: BehaviorPhase.data, GenericBehaviorEffect.start/duration setters (lines 26, 187, 197) ──

def test_behavior_phase_data():
    from camtasia.effects.behaviors import BehaviorPhase
    phase_data = {'attributes': {'name': 'test'}}
    bp = BehaviorPhase(phase_data)
    assert bp.data is phase_data


def test_generic_behavior_start_duration_setters():
    from camtasia.effects.behaviors import GenericBehaviorEffect
    data = {
        'effectName': 'TestBehavior',
        'parameters': {},
        'in': {'attributes': {}},
        'center': {'attributes': {}},
        'out': {'attributes': {}},
    }
    gbe = GenericBehaviorEffect(data)
    gbe.start = 100
    assert gbe.start == 100
    gbe.duration = 200
    assert gbe.duration == 200


# ── effects/base.py: left_edge_mods / right_edge_mods (lines 100, 105) ──

def test_effect_edge_mods():
    from camtasia.effects.base import Effect
    data = {
        'effectName': 'Test',
        'parameters': {},
        'start': 100,
        'duration': 500,
        'leftEdgeMods': [{'type': 'fadeIn'}],
        'rightEdgeMods': [{'type': 'fadeOut'}],
    }
    e = Effect(data)
    assert e.left_edge_mods == [{'type': 'fadeIn'}]
    assert e.right_edge_mods == [{'type': 'fadeOut'}]
    assert e.start == 100
    assert e.duration == 500
