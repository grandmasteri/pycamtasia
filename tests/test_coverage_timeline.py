"""Tests covering missing lines in timeline.py."""
from __future__ import annotations

import copy
import pytest
from camtasia.timing import seconds_to_ticks


def _make_timeline_data(tracks=None, attrs=None):
    """Build minimal timeline data dict."""
    return {
        'sceneTrack': {
            'scenes': [{
                'csml': {
                    'tracks': tracks or [],
                }
            }]
        },
        'trackAttributes': attrs or [],
    }


def _track_data(index, medias=None, transitions=None):
    return {'trackIndex': index, 'medias': medias or [], 'transitions': transitions or []}


def _media(id, start=0, dur=100, _type='VMFile', src=0, **kw):
    d = {'id': id, '_type': _type, 'src': src, 'start': start, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1,
         'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
         'animationTracks': {}}
    d.update(kw)
    return d


# timeline.py:571-572,574 — _register_ids for nested tracks and medias
class TestClipsOfTypeNestedIds:
    def test_nested_ids_registered(self):
        from camtasia.timeline.timeline import Timeline
        # Create a Group clip with inner tracks and medias
        inner_media = _media(10, 0, 50)
        group = _media(1, 0, 100, _type='Group')
        group['tracks'] = [{'medias': [inner_media]}]
        group['medias'] = [_media(20, 0, 50)]  # stitched-style sub-medias

        t_data = _track_data(0, [group])
        data = _make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        # clips_of_type triggers _register_ids which recurses into tracks/medias
        results = tl.clips_of_type('VMFile')
        # inner_media (id=10) and sub-media (id=20) should be found
        found_ids = {clip.id for _, clip in results}
        assert 10 in found_ids


# timeline.py:717,723,729 — validate_structure duplicate ID detection
class TestValidateStructureDuplicateIds:
    def test_duplicate_nested_id(self):
        from camtasia.timeline.timeline import Timeline
        m1 = _media(1, 0, 100)
        m2 = _media(2, 100, 100)
        # Nested clip with same ID as m1
        m2['tracks'] = [{'medias': [{'id': 1, '_type': 'VMFile'}]}]
        t_data = _track_data(0, [m1, m2])
        data = _make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        issues = tl.validate_structure()
        assert any('Duplicate clip ID 1' in i for i in issues)

    def test_duplicate_video_sub_id(self):
        from camtasia.timeline.timeline import Timeline
        m1 = _media(1, 0, 100)
        m2 = _media(2, 100, 100, _type='UnifiedMedia')
        m2['video'] = {'id': 1, '_type': 'VMFile'}  # duplicate of m1
        t_data = _track_data(0, [m1, m2])
        data = _make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        issues = tl.validate_structure()
        assert any('Duplicate clip ID 1' in i for i in issues)

    def test_duplicate_stitched_media_id(self):
        from camtasia.timeline.timeline import Timeline
        m1 = _media(1, 0, 100)
        m2 = _media(2, 100, 100, _type='StitchedMedia')
        m2['medias'] = [{'id': 1, '_type': 'VMFile'}]  # duplicate of m1
        t_data = _track_data(0, [m1, m2])
        data = _make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        issues = tl.validate_structure()
        assert any('Duplicate clip ID 1' in i for i in issues)


# timeline.py:812 — reverse_track_order pads attrs
class TestReverseTrackOrderPadsAttrs:
    def test_pads_missing_attrs(self):
        from camtasia.timeline.timeline import Timeline
        t0 = _track_data(0, [_media(1)])
        t1 = _track_data(1, [_media(2, start=100)])
        data = _make_timeline_data([t0, t1], [])  # no attrs at all
        tl = Timeline(data)
        tl.reverse_track_order()
        assert len(data['trackAttributes']) >= 2


# timeline.py:824 — sort_tracks_by_name pads attrs
class TestSortTracksByNamePadsAttrs:
    def test_pads_missing_attrs(self):
        from camtasia.timeline.timeline import Timeline
        t0 = _track_data(0, [_media(1)])
        t1 = _track_data(1, [_media(2, start=100)])
        data = _make_timeline_data([t0, t1], [{'ident': 'B'}])  # only 1 attr for 2 tracks
        tl = Timeline(data)
        tl.sort_tracks_by_name()
        assert len(data['trackAttributes']) >= 2


# timeline.py:1245 — reorder_tracks pads attrs
class TestReorderTracksPadsAttrs:
    def test_pads_missing_attrs(self):
        from camtasia.timeline.timeline import Timeline
        t0 = _track_data(0, [_media(1)])
        t1 = _track_data(1, [_media(2, start=100)])
        data = _make_timeline_data([t0, t1], [])  # no attrs
        tl = Timeline(data)
        tl.reorder_tracks([1, 0])
        assert len(data['trackAttributes']) >= 2
