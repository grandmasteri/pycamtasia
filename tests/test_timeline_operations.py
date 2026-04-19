"""Tests for Timeline operations: pack, remove, duration, grouping, duplication, remap."""
from __future__ import annotations

import copy
from typing import Any

import pytest

from camtasia.timeline.timeline import (
    Timeline,
    _remap_clip_ids_recursive,
    _remap_clip_ids_with_map,
)
from camtasia.timeline.track import Track
from camtasia.timeline.marker import Marker
from camtasia.timing import EDIT_RATE, seconds_to_ticks


def _make_timeline_data(
    tracks: list[dict] | None = None,
) -> dict:
    """Build minimal timeline data with matching trackAttributes."""
    scene_tracks = tracks or []
    attrs = [
        {"ident": f"Track {i}", "audioMuted": False, "videoHidden": False}
        for i in range(len(scene_tracks))
    ]
    for i, t in enumerate(scene_tracks):
        t.setdefault("trackIndex", i)
        t.setdefault("medias", [])
    return {
        "id": 1,
        "parameters": {"toc": {"type": "string", "keyframes": []}},
        "sceneTrack": {"scenes": [{"csml": {"tracks": scene_tracks}}]},
        "trackAttributes": attrs,
    }


def _clip(clip_id: int, start: int, duration: int) -> dict:
    """Build a minimal clip dict."""
    return {"id": clip_id, "_type": "VMFile", "start": start, "duration": duration}


# ── pack_all_tracks ──────────────────────────────────────────────────


class TestPackAllTracks:
    def test_returns_zero_for_empty_timeline(self) -> None:
        timeline = Timeline(_make_timeline_data())
        assert timeline.pack_all_tracks() == 0

    def test_returns_zero_when_all_tracks_empty(self) -> None:
        timeline = Timeline(_make_timeline_data([
            {"medias": []},
            {"medias": []},
        ]))
        assert timeline.pack_all_tracks() == 0

    def test_packs_single_track_with_gap(self) -> None:
        tracks = [{
            "medias": [
                _clip(1, start=0, duration=100),
                _clip(2, start=500, duration=200),
            ],
            "transitions": [],
        }]
        timeline = Timeline(_make_timeline_data(tracks))

        packed_count: int = timeline.pack_all_tracks()

        assert packed_count == 1
        medias = tracks[0]["medias"]
        assert medias[0]["start"] == 0
        assert medias[1]["start"] == 100

    def test_packs_multiple_tracks(self) -> None:
        tracks = [
            {
                "medias": [
                    _clip(1, start=0, duration=100),
                    _clip(2, start=300, duration=100),
                ],
                "transitions": [],
            },
            {
                "medias": [
                    _clip(3, start=50, duration=200),
                    _clip(4, start=1000, duration=100),
                ],
                "transitions": [],
            },
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        packed_count: int = timeline.pack_all_tracks()

        assert packed_count == 2
        assert tracks[0]["medias"][0]["start"] == 0
        assert tracks[0]["medias"][1]["start"] == 100
        assert tracks[1]["medias"][0]["start"] == 0
        assert tracks[1]["medias"][1]["start"] == 200

    def test_skips_empty_tracks(self) -> None:
        tracks = [
            {"medias": [_clip(1, start=500, duration=100)], "transitions": []},
            {"medias": []},
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        packed_count: int = timeline.pack_all_tracks()

        assert packed_count == 1
        assert tracks[0]["medias"][0]["start"] == 0

    def test_already_packed_track_is_idempotent(self) -> None:
        tracks = [{
            "medias": [
                _clip(1, start=0, duration=100),
                _clip(2, start=100, duration=200),
            ],
            "transitions": [],
        }]
        timeline = Timeline(_make_timeline_data(tracks))

        timeline.pack_all_tracks()

        assert tracks[0]["medias"][0]["start"] == 0
        assert tracks[0]["medias"][1]["start"] == 100


# ── remove_empty_tracks ──────────────────────────────────────────


class TestRemoveAllEmptyTracks:
    def test_returns_zero_when_no_empty_tracks(self) -> None:
        tracks = [{"medias": [_clip(1, 0, 100)]}]
        timeline = Timeline(_make_timeline_data(tracks))
        assert timeline.remove_empty_tracks() == 0

    def test_removes_single_empty_track(self) -> None:
        tracks = [
            {"medias": [_clip(1, 0, 100)]},
            {"medias": []},
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        removed_count: int = timeline.remove_empty_tracks()

        assert removed_count == 1
        assert timeline.track_count == 1

    def test_removes_all_empty_tracks(self) -> None:
        tracks = [
            {"medias": []},
            {"medias": [_clip(1, 0, 100)]},
            {"medias": []},
        ]
        timeline = Timeline(_make_timeline_data(tracks))

        removed_count: int = timeline.remove_empty_tracks()

        assert removed_count == 2
        assert timeline.track_count == 1

    def test_returns_zero_for_empty_timeline(self) -> None:
        timeline = Timeline(_make_timeline_data())
        assert timeline.remove_empty_tracks() == 0

    def test_removes_all_when_every_track_empty(self) -> None:
        tracks = [{"medias": []}, {"medias": []}]
        timeline = Timeline(_make_timeline_data(tracks))

        removed_count: int = timeline.remove_empty_tracks()

        assert removed_count == 2
        assert timeline.track_count == 0



def test_timeline_duration_seconds_property(project):
    """Timeline.duration_seconds delegates to total_duration_seconds."""
    assert project.timeline.duration_seconds == 0.0


# ── Merged from test_coverage_timeline.py ────────────────────────────


def _tl_media(id, start=0, dur=100, _type='VMFile', src=0, **kw):
    d = {'id': id, '_type': _type, 'src': src, 'start': start, 'duration': dur,
         'mediaStart': 0, 'mediaDuration': dur, 'scalar': 1,
         'metadata': {}, 'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
         'animationTracks': {}}
    d.update(kw)
    return d


def _tl_track_data(index, medias=None, transitions=None):
    return {'trackIndex': index, 'medias': medias or [], 'transitions': transitions or []}


def _tl_make_timeline_data(tracks=None, attrs=None):
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


class TestClipsOfTypeNestedIds:
    def test_nested_ids_registered(self):
        inner_media = _tl_media(10, 0, 50)
        group = _tl_media(1, 0, 100, _type='Group')
        group['tracks'] = [{'medias': [inner_media]}]
        group['medias'] = [_tl_media(20, 0, 50)]

        t_data = _tl_track_data(0, [group])
        data = _tl_make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        results = tl.clips_of_type('VMFile')
        found_ids = {clip.id for _, clip in results}
        assert 10 in found_ids


class TestValidateStructureDuplicateIds:
    def test_duplicate_nested_id(self):
        m1 = _tl_media(1, 0, 100)
        m2 = _tl_media(2, 100, 100)
        m2['tracks'] = [{'medias': [{'id': 1, '_type': 'VMFile'}]}]
        t_data = _tl_track_data(0, [m1, m2])
        data = _tl_make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        issues = tl.validate_structure()
        assert any('Duplicate clip ID 1' in i for i in issues)

    def test_duplicate_video_sub_id(self):
        m1 = _tl_media(1, 0, 100)
        m2 = _tl_media(2, 100, 100, _type='UnifiedMedia')
        m2['video'] = {'id': 1, '_type': 'VMFile'}
        t_data = _tl_track_data(0, [m1, m2])
        data = _tl_make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        issues = tl.validate_structure()
        assert any('Duplicate clip ID 1' in i for i in issues)

    def test_duplicate_stitched_media_id(self):
        m1 = _tl_media(1, 0, 100)
        m2 = _tl_media(2, 100, 100, _type='StitchedMedia')
        m2['medias'] = [{'id': 1, '_type': 'VMFile'}]
        t_data = _tl_track_data(0, [m1, m2])
        data = _tl_make_timeline_data([t_data], [{'ident': 'T0'}])
        tl = Timeline(data)
        issues = tl.validate_structure()
        assert any('Duplicate clip ID 1' in i for i in issues)


class TestReverseTrackOrderPadsAttrs:
    def test_pads_missing_attrs(self):
        t0 = _tl_track_data(0, [_tl_media(1)])
        t1 = _tl_track_data(1, [_tl_media(2, start=100)])
        data = _tl_make_timeline_data([t0, t1], [])
        tl = Timeline(data)
        tl.reverse_track_order()
        assert [type(a) for a in data['trackAttributes']] == [dict, dict]


class TestSortTracksByNamePadsAttrs:
    def test_pads_missing_attrs(self):
        t0 = _tl_track_data(0, [_tl_media(1)])
        t1 = _tl_track_data(1, [_tl_media(2, start=100)])
        data = _tl_make_timeline_data([t0, t1], [{'ident': 'B'}])
        tl = Timeline(data)
        tl.sort_tracks_by_name()
        assert [type(a) for a in data['trackAttributes']] == [dict, dict]


class TestReorderTracksPadsAttrs:
    def test_pads_missing_attrs(self):
        t0 = _tl_track_data(0, [_tl_media(1)])
        t1 = _tl_track_data(1, [_tl_media(2, start=100)])
        data = _tl_make_timeline_data([t0, t1], [])
        tl = Timeline(data)
        tl.reorder_tracks([1, 0])
        assert [type(a) for a in data['trackAttributes']] == [dict, dict]


# =========================================================================
# Tests migrated from test_convenience.py
# =========================================================================

def _make_timeline(track_specs):
    """Build a Timeline with tracks described as (name, media_list) tuples."""
    tracks = []
    attrs = []
    for i, (name, medias) in enumerate(track_specs):
        tracks.append({'trackIndex': i, 'medias': medias})
        attrs.append({'ident': name})
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
        'trackAttributes': attrs,
    }
    return Timeline(data)




# ---------------------------------------------------------------------------
# Timeline.find_track
# ---------------------------------------------------------------------------

def test_timeline_find_track_found():
    tl = _make_timeline([('Audio', []), ('Video', [{'id': 1, 'start': 0, 'duration': 1}])])
    found = tl.find_track_by_name('Video')
    assert found is not None
    assert found.name == 'Video'


def test_timeline_find_track_not_found():
    tl = _make_timeline([('Audio', [])])
    assert tl.find_track_by_name('Missing') is None




# ---------------------------------------------------------------------------
# Timeline.empty_tracks
# ---------------------------------------------------------------------------

def test_timeline_empty_tracks():
    tl = _make_timeline([
        ('Empty1', []),
        ('HasClip', [{'id': 1, 'start': 0, 'duration': 1}]),
        ('Empty2', []),
    ])
    empties = tl.empty_tracks
    assert {t.name for t in empties} == {'Empty1', 'Empty2'}







# ---------------------------------------------------------------------------
# Timeline.to_dict
# ---------------------------------------------------------------------------

def test_timeline_to_dict():
    media = {'id': 1, 'start': 0, 'duration': seconds_to_ticks(5.0)}
    tl = _make_timeline([('Video', [media]), ('Audio', [])])
    d = tl.to_dict()
    assert d['track_count'] == 2
    assert d['total_clip_count'] == 1
    assert d['duration_seconds'] == pytest.approx(5.0)
    assert d['has_clips'] is True
    assert d['track_names'] == ['Video', 'Audio']




# ---------------------------------------------------------------------------
# Timeline.describe
# ---------------------------------------------------------------------------

def test_timeline_describe():
    media = {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 300}
    tl = _make_timeline([('Video', [media]), ('Audio', [])])
    desc = tl.describe()
    assert 'Timeline:' in desc
    assert '2 tracks' in desc
    assert '1 clips' in desc




# ---------------------------------------------------------------------------
# Timeline.apply_to_all_clips
# ---------------------------------------------------------------------------

def test_timeline_apply_to_all_clips():
    t = seconds_to_ticks
    tl = _make_timeline([
        ('A', [{'_type': 'VMFile', 'id': 1, 'start': 0, 'duration': t(5.0)}]),
        ('B', [
            {'_type': 'VMFile', 'id': 2, 'start': 0, 'duration': t(3.0)},
            {'_type': 'VMFile', 'id': 3, 'start': t(3.0), 'duration': t(2.0)},
        ]),
    ])
    touched = []
    count = tl.apply_to_all_clips(lambda c: touched.append(c.id))
    assert count == 3
    assert sorted(touched) == [1, 2, 3]




# ---------------------------------------------------------------------------
# Timeline.end_seconds
# ---------------------------------------------------------------------------

def test_timeline_end_seconds():
    medias = [
        {'id': 1, 'start': 0, 'duration': seconds_to_ticks(10)},
    ]
    tl = _make_timeline([('Track1', medias)])
    assert tl.end_seconds == pytest.approx(10.0)




# ---------------------------------------------------------------------------
# Timeline gain / background_color / new CalloutShape values
# ---------------------------------------------------------------------------

def test_timeline_gain():
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
        'trackAttributes': [],
    }
    tl = Timeline(data)
    assert tl.gain == 1.0  # default
    tl.gain = 0.5
    assert tl.gain == 0.5
    assert data['gain'] == 0.5


def test_timeline_background_color():
    data = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': []}}]},
        'trackAttributes': [],
    }
    tl = Timeline(data)
    assert tl.background_color == [0, 0, 0, 255]  # default
    tl.background_color = [255, 0, 0, 255]
    assert tl.background_color == [255, 0, 0, 255]
    assert data['backgroundColor'] == [255, 0, 0, 255]


def test_timeline_legacy_attenuate():
    tl = _make_timeline([('T', [])])
    assert tl.legacy_attenuate_audio_mix is True
    tl._data['legacyAttenuateAudioMix'] = False
    assert tl.legacy_attenuate_audio_mix is False




# ---------------------------------------------------------------------------
# Timeline.total_transition_count
# ---------------------------------------------------------------------------

def test_timeline_total_transition_count_empty():
    """total_transition_count is 0 for a timeline with no transitions."""
    timeline = _make_timeline([('A', []), ('B', [])])
    assert timeline.total_transition_count == 0


def test_timeline_total_transition_count_with_transitions():
    """total_transition_count sums transitions across all tracks."""
    data: dict = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': [
            {'trackIndex': 0, 'medias': [], 'transitions': [{'duration': 100}]},
            {'trackIndex': 1, 'medias': [], 'transitions': [{'duration': 200}, {'duration': 300}]},
        ]}}]},
        'trackAttributes': [{'ident': 'A'}, {'ident': 'B'}],
    }
    timeline = Timeline(data)
    assert timeline.total_transition_count == 3



# ── Merged from test_timeline_coverage.py ────────────────────────────


def _coverage_timeline_data(num_tracks: int = 1) -> dict[str, Any]:
    tracks = []
    attrs = []
    for i in range(num_tracks):
        tracks.append({"trackIndex": i, "medias": [], "parameters": {}})
        attrs.append({"ident": f"Track {i}", "audioMuted": False, "videoHidden": False,
                       "magnetic": False, "metadata": {"IsLocked": "False"}})
    return {
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": attrs,
        "parameters": {},
    }


class TestTimelineTotalDuration:
    def test_empty_timeline_returns_zero(self):
        tl = Timeline(_coverage_timeline_data())
        assert tl.total_duration_ticks == 0
        assert tl.total_duration_seconds() == 0.0

    def test_duration_from_clips(self):
        data = _coverage_timeline_data()
        clip_end = EDIT_RATE * 5
        data["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"] = [
            {"_type": "IMFile", "id": 1, "start": 0, "duration": clip_end,
             "mediaStart": 0, "mediaDuration": clip_end, "scalar": 1,
             "src": 1, "metadata": {}, "animationTracks": {}, "parameters": {}, "effects": []},
        ]
        tl = Timeline(data)
        assert tl.total_duration_ticks == clip_end
        assert tl.total_duration_seconds() == pytest.approx(5.0)


class TestTimelineGetOrCreateTrack:
    def test_returns_existing_track_by_name(self):
        tl = Timeline(_coverage_timeline_data(2))
        actual_track = tl.get_or_create_track("Track 0")
        assert actual_track.name == "Track 0"

    def test_creates_new_track_when_not_found(self):
        tl = Timeline(_coverage_timeline_data())
        actual_track = tl.get_or_create_track("New Track")
        assert actual_track.name == "New Track"
        assert tl.track_count == 2


class TestTimelineAllClips:
    def test_empty_timeline_returns_empty(self):
        tl = Timeline(_coverage_timeline_data())
        assert tl.all_clips() == []

    def test_collects_clips_across_tracks(self):
        data = _coverage_timeline_data(2)
        clip_a = {"_type": "IMFile", "id": 1, "start": 0, "duration": EDIT_RATE,
                  "mediaStart": 0, "mediaDuration": EDIT_RATE, "scalar": 1,
                  "src": 1, "metadata": {}, "animationTracks": {}, "parameters": {}, "effects": []}
        clip_b = {"_type": "IMFile", "id": 2, "start": 0, "duration": EDIT_RATE,
                  "mediaStart": 0, "mediaDuration": EDIT_RATE, "scalar": 1,
                  "src": 2, "metadata": {}, "animationTracks": {}, "parameters": {}, "effects": []}
        data["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"] = [clip_a]
        data["sceneTrack"]["scenes"][0]["csml"]["tracks"][1]["medias"] = [clip_b]
        tl = Timeline(data)
        actual_ids = [c.id for c in tl.all_clips()]
        assert actual_ids == [1, 2]


class TestTimelineAddMarker:
    def test_add_marker_returns_marker(self):
        tl = Timeline(_coverage_timeline_data())
        actual_marker = tl.add_marker("Chapter 1", 2.5)
        assert actual_marker.name == "Chapter 1"
        assert actual_marker.time == seconds_to_ticks(2.5)


class TestTimelineRemoveTrack:
    def test_remove_track_reduces_count(self):
        tl = Timeline(_coverage_timeline_data(3))
        assert tl.track_count == 3
        tl.remove_track(1)
        assert tl.track_count == 2

    def test_remove_track_renumbers(self):
        tl = Timeline(_coverage_timeline_data(3))
        tl.remove_track(0)
        actual_indices = [t.index for t in tl.tracks]
        assert actual_indices == [0, 1]

    def test_remove_nonexistent_track_raises(self):
        tl = Timeline(_coverage_timeline_data())
        with pytest.raises(KeyError, match="No track with index=99"):
            tl.remove_track(99)


class TestDuplicateTrackRemapsTransitions:
    """Cover transition leftMedia/rightMedia remapping during duplication."""

    def test_duplicate_track_remaps_transition_references(self):
        data = _coverage_timeline_data()
        tl = Timeline(data)
        track = tl.tracks[0]
        c1 = track.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
        c2 = track.add_clip('VMFile', 1, seconds_to_ticks(5.0), seconds_to_ticks(5.0))
        track.add_transition('FadeThroughBlack', c1, c2, duration_seconds=0.5)
        tl.duplicate_track(0)
        dup_track = tl.tracks[1]
        dup_transitions = dup_track._data.get('transitions', [])
        orig_ids = {c1.id, c2.id}
        for t in dup_transitions:
            if t.get('leftMedia') is not None:
                assert t['leftMedia'] not in orig_ids
            if t.get('rightMedia') is not None:
                assert t['rightMedia'] not in orig_ids


class TestClipsOfTypeWithStitchedMedia:
    """Cover _register_ids recursion into video/audio sub-dicts."""

    def test_finds_clips_inside_unified_media(self):
        data = _coverage_timeline_data()
        data['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'].append({
            'id': 10, '_type': 'UnifiedMedia', 'start': 0,
            'duration': seconds_to_ticks(10.0),
            'mediaStart': 0, 'mediaDuration': seconds_to_ticks(10.0),
            'scalar': 1, 'parameters': {}, 'effects': [],
            'attributes': {'ident': ''},
            'video': {
                'id': 11, '_type': 'ScreenVMFile', 'src': 1, 'start': 0,
                'duration': seconds_to_ticks(10.0), 'mediaStart': 0,
                'mediaDuration': seconds_to_ticks(10.0), 'scalar': 1,
                'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
            },
            'audio': {
                'id': 12, '_type': 'AMFile', 'src': 1, 'start': 0,
                'duration': seconds_to_ticks(10.0), 'mediaStart': 0,
                'mediaDuration': seconds_to_ticks(10.0), 'scalar': 1,
                'parameters': {}, 'effects': [], 'attributes': {'ident': ''},
            },
        })
        tl = Timeline(data)
        results = tl.clips_of_type('ScreenVMFile')
        assert any(clip.id == 11 for _, clip in results)


class TestRemapClipIdsRecursive:
    def test_remaps_video_audio_and_tracks(self):
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


class TestRemapClipIdsWithMap:
    def test_builds_id_map(self):
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


class TestGroupClipsInRange:
    def test_groups_clips(self, project):
        tl = project.timeline
        track = tl.tracks[0]
        track.add_video(1, start_seconds=0, duration_seconds=5)
        group = tl.group_clips_in_range(0.0, 5.0, 0)
        assert group is not None

    def test_no_clips_raises(self, project):
        tl = project.timeline
        with pytest.raises(ValueError, match='No clips found'):
            tl.group_clips_in_range(100.0, 200.0, 0)


class TestBuildSectionTimeline:
    def test_basic(self, project):
        tl = project.timeline
        t0 = tl.tracks[0]
        c1 = t0.add_video(1, start_seconds=0, duration_seconds=3)
        c2 = t0.add_video(1, start_seconds=5, duration_seconds=3)
        tl.build_section_timeline(
            [(c1.id, None), (c2.id, 'FadeThrough')],
            target_track_index=0,
            transition_duration_seconds=0.5,
        )
        assert c1._data['start'] == 0

    def test_clip_not_found_raises(self, project):
        tl = project.timeline
        with pytest.raises(KeyError, match='Clip 9999 not found'):
            tl.build_section_timeline([(9999, None)], 0)

    def test_moves_clip_across_tracks(self, project):
        tl = project.timeline
        t0 = tl.tracks[0]
        t1 = tl.get_or_create_track('Track2')
        c1 = t0.add_video(1, start_seconds=0, duration_seconds=2)
        c2 = t1.add_video(1, start_seconds=0, duration_seconds=2)
        tl.build_section_timeline(
            [(c1.id, None), (c2.id, 'FadeThrough')],
            target_track_index=0,
        )


class TestDuplicateTrackRegistersIds:
    def test_registers_ids(self, project):
        tl = project.timeline
        t0 = tl.tracks[0]
        t0.add_video(1, start_seconds=0, duration_seconds=3)
        tl.duplicate_track(0)
        assert tl.track_count == 3


# ── Merged from test_timeline_protocols.py ───────────────────────────


def _protocols_timeline_data(n_tracks=3, clips_per_track=0):
    tracks = []
    clip_id = 1
    for i in range(n_tracks):
        medias = []
        for j in range(clips_per_track):
            medias.append({
                "id": clip_id, "_type": "IMFile", "src": 10,
                "trackNumber": 0, "start": j * 1000, "duration": 1000,
                "mediaStart": 0, "mediaDuration": 1, "scalar": 1,
                "metadata": {}, "animationTracks": {}, "parameters": {},
                "effects": [],
            })
            clip_id += 1
        tracks.append({"trackIndex": i, "medias": medias})
    attrs = [
        {"ident": f"Track-{i}", "audioMuted": False, "videoHidden": False,
         "magnetic": False, "metadata": {"IsLocked": "False"}}
        for i in range(n_tracks)
    ]
    return {
        "id": 1,
        "sceneTrack": {"scenes": [{"csml": {"tracks": tracks}}]},
        "trackAttributes": attrs,
    }


class TestTimelineRepr:
    def test_repr(self):
        tl = Timeline(_protocols_timeline_data(3))
        assert repr(tl) == "Timeline(tracks=3)"

    def test_repr_empty(self):
        tl = Timeline(_protocols_timeline_data(0))
        assert repr(tl) == "Timeline(tracks=0)"


class TestTimelineLen:
    def test_len(self):
        tl = Timeline(_protocols_timeline_data(5))
        assert [t.index for t in tl.tracks] == [0, 1, 2, 3, 4]

    def test_len_empty(self):
        tl = Timeline(_protocols_timeline_data(0))
        assert list(tl.tracks) == []


class TestMoveTrackToBack:
    def test_moves_to_position_zero(self):
        tl = Timeline(_protocols_timeline_data(3))
        tl.move_track_to_back(2)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-2", "Track-0", "Track-1"]

    def test_already_at_back_is_noop(self):
        tl = Timeline(_protocols_timeline_data(3))
        tl.move_track_to_back(0)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-0", "Track-1", "Track-2"]


class TestMoveTrackToFront:
    def test_moves_to_last_position(self):
        tl = Timeline(_protocols_timeline_data(3))
        tl.move_track_to_front(0)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-1", "Track-2", "Track-0"]

    def test_already_at_front_is_noop(self):
        tl = Timeline(_protocols_timeline_data(3))
        tl.move_track_to_front(2)
        names = [t.name for t in tl.tracks]
        assert names == ["Track-0", "Track-1", "Track-2"]


class TestTimelineFindClip:
    def test_found(self):
        tl = Timeline(_protocols_timeline_data(3, clips_per_track=2))
        result = tl.find_clip(3)
        assert result is not None
        track, clip = result
        assert track.index == 1
        assert clip.id == 3

    def test_not_found(self):
        tl = Timeline(_protocols_timeline_data(3, clips_per_track=2))
        assert tl.find_clip(999) is None

    def test_empty_timeline(self):
        tl = Timeline(_protocols_timeline_data(0))
        assert tl.find_clip(1) is None


# ── all_effects with Group / StitchedMedia / UnifiedMedia ────────────


class TestAllEffectsNestedClips:
    def test_group_effects_collected(self):
        group_clip = {
            "id": 1, "_type": "Group", "start": 0, "duration": 100,
            "effects": [{"effectName": "outer"}],
            "tracks": [{
                "medias": [{
                    "id": 2, "_type": "VMFile", "start": 0, "duration": 100,
                    "effects": [{"effectName": "inner"}],
                }],
            }],
        }
        tl = Timeline(_make_timeline_data([{"medias": [group_clip]}]))
        effs = tl.all_effects
        names = {e[2]["effectName"] for e in effs}
        assert names >= {"outer", "inner"}

    def test_stitched_media_effects_collected(self):
        clip = {
            "id": 1, "_type": "StitchedMedia", "start": 0, "duration": 100,
            "effects": [],
            "medias": [{
                "id": 2, "_type": "VMFile", "start": 0, "duration": 50,
                "effects": [{"effectName": "nested_eff"}],
            }],
        }
        tl = Timeline(_make_timeline_data([{"medias": [clip]}]))
        effs = tl.all_effects
        names = [e[2]["effectName"] for e in effs]
        assert "nested_eff" in names

    def test_unified_media_effects_collected(self):
        clip = {
            "id": 1, "_type": "UnifiedMedia", "start": 0, "duration": 100,
            "effects": [],
            "video": {
                "id": 2, "_type": "VMFile", "start": 0, "duration": 100,
                "effects": [{"effectName": "vid_eff"}],
            },
            "audio": {
                "id": 3, "_type": "AMFile", "start": 0, "duration": 100,
                "effects": [{"effectName": "aud_eff"}],
            },
        }
        tl = Timeline(_make_timeline_data([{"medias": [clip]}]))
        effs = tl.all_effects
        names = {e[2]["effectName"] for e in effs}
        assert names >= {"vid_eff", "aud_eff"}
