"""Tests targeting uncovered lines in clip modules: unified, group, callout, speed, placeholder, stitched."""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from camtasia.timing import seconds_to_ticks

S1 = seconds_to_ticks(1.0)
S5 = seconds_to_ticks(5.0)
S10 = seconds_to_ticks(10.0)


# ── helpers ──

def _um_data():
    return {
        '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': S10,
        'mediaDuration': S10, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'video': {
            '_type': 'ScreenVMFile', 'id': 2, 'src': 5, 'start': 0,
            'duration': S10, 'mediaDuration': S10, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'attributes': {'ident': 'rec'},
            'trackNumber': 0,
        },
        'audio': {
            '_type': 'AMFile', 'id': 3, 'src': 5, 'start': 0,
            'duration': S10, 'mediaDuration': S10, 'mediaStart': 0, 'scalar': 1,
            'attributes': {'gain': 1.0},
        },
    }


def _group_data(inner=None, duration=None):
    dur = duration or S10
    return {
        '_type': 'Group', 'id': 100, 'start': S1, 'duration': dur,
        'mediaDuration': dur, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'attributes': {'ident': 'grp', 'widthAttr': 1920, 'heightAttr': 1080},
        'tracks': [{'trackIndex': 0, 'medias': inner or [], 'transitions': []}],
    }


def _callout_data(**overrides):
    d = {
        '_type': 'Callout', 'id': 400, 'start': 0, 'duration': S5,
        'mediaDuration': S5, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'def': {
            'text': 'Hello', 'kind': 'remix', 'shape': 'text', 'style': 'basic',
            'font': {'name': 'Arial', 'weight': 400, 'size': 24},
            'width': 200, 'height': 100,
            'textAttributes': {
                'keyframes': [{
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


# ===== unified.py — lines 71,74,85,88,91,102,105 =====

class TestUnifiedMediaEffectBlocking:
    """All add_effect overrides raise TypeError."""

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


# ===== group.py — sync_internal_durations, set_internal_segment_speeds, ungroup =====

class TestGroupSyncInternalDurations:
    def test_sync_with_fractional_scalar(self):
        """sync_internal_durations recalculates mediaDuration via scalar."""
        from camtasia.timeline.clips.group import Group
        inner = {
            '_type': 'VMFile', 'id': 10, 'src': 1,
            'start': 0, 'duration': S10 * 2,
            'mediaDuration': S10 * 2, 'mediaStart': 0, 'scalar': '1/2',
            'parameters': {}, 'effects': [],
        }
        data = _group_data([inner], duration=S10)
        g = Group(data)
        g.sync_internal_durations()
        assert inner['duration'] == S10
        # mediaDuration = duration / scalar = S10 / (1/2) = S10*2
        expected_md = int(Fraction(S10) / Fraction(1, 2))
        assert inner['mediaDuration'] == expected_md

    def test_sync_propagates_to_unified(self):
        """sync_internal_durations calls _propagate_start_to_unified on UnifiedMedia."""
        from camtasia.timeline.clips.group import Group
        inner = copy.deepcopy(_um_data())
        inner['duration'] = S10 * 3
        inner['mediaDuration'] = S10 * 3
        data = _group_data([inner], duration=S10)
        g = Group(data)
        g.sync_internal_durations()
        assert inner['duration'] == S10


class TestGroupUngroup:
    def test_ungroup_adjusts_start_and_propagates(self):
        """ungroup offsets clip starts by group start and propagates to unified."""
        from camtasia.timeline.clips.group import Group
        inner_um = copy.deepcopy(_um_data())
        inner_um['start'] = 0
        data = _group_data([inner_um])
        data['start'] = S5  # group starts at 5s
        g = Group(data)
        clips = g.ungroup()
        assert len(clips) >= 1
        # Start should be offset by group start
        assert clips[0].start == S5


class TestGroupSetInternalSegmentSpeedsCanvasWidthOnly:
    def test_canvas_width_only(self):
        """set_internal_segment_speeds with only canvas_width (no height)."""
        from camtasia.timeline.clips.group import Group
        inner = copy.deepcopy(_um_data())
        data = _group_data([inner], duration=S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            canvas_width=1920,
        )
        clip = data['tracks'][0]['medias'][0]
        assert clip['parameters']['scale0']['defaultValue'] == 1.0

    def test_canvas_height_only(self):
        """set_internal_segment_speeds with only canvas_height (no width)."""
        from camtasia.timeline.clips.group import Group
        inner = copy.deepcopy(_um_data())
        data = _group_data([inner], duration=S10)
        g = Group(data)
        g.set_internal_segment_speeds(
            segments=[(0.0, 5.0, 5.0)],
            canvas_height=1080,
        )
        clip = data['tracks'][0]['medias'][0]
        assert clip['parameters']['scale1']['defaultValue'] == 1.0

    def test_source_bin_lookup_miss(self):
        """source_bin provided but no matching entry — falls back to group attrs."""
        from camtasia.timeline.clips.group import Group
        inner = copy.deepcopy(_um_data())
        data = _group_data([inner], duration=S10)
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
        """set_internal_segment_speeds raises when no media track found."""
        from camtasia.timeline.clips.group import Group
        data = _group_data()
        data['tracks'][0]['medias'] = []
        g = Group(data)
        with pytest.raises(ValueError, match='No internal track'):
            g.set_internal_segment_speeds(segments=[(0.0, 1.0, 1.0)])

    def test_stitched_media_template(self):
        """set_internal_segment_speeds with StitchedMedia as template."""
        from camtasia.timeline.clips.group import Group
        stitched = {
            '_type': 'StitchedMedia', 'id': 50, 'start': 0, 'duration': S10,
            'mediaDuration': S10, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'trackNumber': 0,
            'attributes': {'ident': 'stitch'},
            'medias': [{'_type': 'ScreenVMFile', 'id': 51, 'src': 5}],
        }
        data = _group_data([stitched], duration=S10)
        g = Group(data)
        g.set_internal_segment_speeds(segments=[(0.0, 5.0, 5.0)])
        assert data['tracks'][0]['medias'][0]['_type'] == 'ScreenVMFile'


# ===== callout.py — set_font with textAttributes, set_colors with fgColor, definition =====

class TestCalloutSetFontWithIntWeight:
    def test_set_font_int_weight_updates_keyframes(self):
        """set_font with int weight updates textAttributes keyframes."""
        from camtasia.timeline.clips.callout import Callout
        d = _callout_data()
        c = Callout(d)
        c.set_font('Montserrat', weight=700, size=48)
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fontName'] == 'Montserrat'
        assert attrs['fontWeight'] == 700
        assert attrs['fontSize'] == 48

    def test_set_font_string_weight(self):
        """set_font with string weight maps to numeric."""
        from camtasia.timeline.clips.callout import Callout
        d = _callout_data()
        c = Callout(d)
        c.set_font('Roboto', weight='Bold', size=36)
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fontWeight'] == 700


class TestCalloutSetColorsWithFgColor:
    def test_set_colors_updates_fgcolor_in_keyframes(self):
        """set_colors with font_color updates fgColor in textAttributes."""
        from camtasia.timeline.clips.callout import Callout
        d = _callout_data()
        c = Callout(d)
        c.set_colors(font_color=(0.0, 1.0, 0.0))
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert attrs['fgColor'] == '(0,255,0,255)'

    def test_set_colors_with_alpha(self):
        """set_colors with 4-component font_color."""
        from camtasia.timeline.clips.callout import Callout
        d = _callout_data()
        c = Callout(d)
        c.set_colors(font_color=(1.0, 0.0, 0.0, 0.5))
        attrs = {a['name']: a['value'] for a in d['def']['textAttributes']['keyframes'][0]['value']}
        assert '128' in attrs['fgColor'] or '127' in attrs['fgColor']


class TestCalloutDefinitionProperty:
    def test_definition_returns_def_dict(self):
        """definition property returns the 'def' dict."""
        from camtasia.timeline.clips.callout import Callout
        d = _callout_data()
        c = Callout(d)
        defn = c.definition
        assert defn['text'] == 'Hello'

    def test_definition_empty_when_no_def(self):
        """definition returns {} when no 'def' key."""
        from camtasia.timeline.clips.callout import Callout
        d = _callout_data()
        del d['def']
        c = Callout(d)
        assert c.definition == {}


# ===== speed.py — _adjust_scalar, _mark_speed_changed exclusions, overlap fix =====

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
        """_mark_speed_changed skips IMFile clips."""
        from camtasia.operations.speed import rescale_project
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0,
                    'medias': [
                        {'_type': 'IMFile', 'id': 1, 'start': 0, 'duration': S5,
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
        # IMFile should NOT get clipSpeedAttribute set to True
        assert clip.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is not True

    def test_callout_excluded(self):
        """_mark_speed_changed skips Callout clips."""
        from camtasia.operations.speed import rescale_project
        data = {
            'timeline': {
                'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                    'trackIndex': 0,
                    'medias': [
                        {'_type': 'Callout', 'id': 1, 'start': 0, 'duration': S5,
                         'mediaDuration': S5, 'mediaStart': 0, 'scalar': 1,
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
        """_mark_speed_changed recurses into video/audio children."""
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
        # video child (ScreenVMFile) should get speed marked
        vid = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['video']
        assert vid.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is True

    def test_mark_speed_recurses_into_group_tracks(self):
        """_mark_speed_changed recurses into Group internal tracks."""
        from camtasia.operations.speed import rescale_project
        inner_vm = {
            '_type': 'VMFile', 'id': 10, 'src': 1,
            'start': 0, 'duration': S5, 'mediaDuration': S5,
            'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
            'metadata': {},
        }
        group = _group_data([inner_vm], duration=S5)
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
        """_mark_speed_changed recurses into StitchedMedia nested clips."""
        from camtasia.operations.speed import rescale_project
        stitched = {
            '_type': 'StitchedMedia', 'id': 20, 'start': 0, 'duration': S5,
            'mediaDuration': S5, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'medias': [{
                '_type': 'VMFile', 'id': 21, 'src': 1,
                'start': 0, 'duration': S5, 'mediaDuration': S5,
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
        """Overlap fix calls _propagate_start_to_unified on UnifiedMedia."""
        from camtasia.operations.speed import rescale_project
        um1 = _um_data()
        um1['id'] = 1
        um1['start'] = 0
        um1['duration'] = S5 + 2
        um2 = copy.deepcopy(_um_data())
        um2['id'] = 4
        um2['video']['id'] = 5
        um2['audio']['id'] = 6
        um2['start'] = S5
        um2['duration'] = S5
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


# ===== placeholder.py — set_source raises TypeError =====

class TestPlaceholderSetSource:
    def test_set_source_raises(self):
        from camtasia.timeline.clips.placeholder import PlaceholderMedia
        p = PlaceholderMedia({
            '_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': S5,
            'mediaDuration': 1, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [],
        })
        with pytest.raises(TypeError, match='Cannot set_source'):
            p.set_source(1)


# ===== stitched.py — set_source raises TypeError =====

class TestStitchedSetSource:
    def test_set_source_raises(self):
        from camtasia.timeline.clips.stitched import StitchedMedia
        s = StitchedMedia({
            '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': S5,
            'mediaDuration': S5, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [], 'medias': [],
        })
        with pytest.raises(TypeError, match='do not have a top-level source'):
            s.set_source(1)
