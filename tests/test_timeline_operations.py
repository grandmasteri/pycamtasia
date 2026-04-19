"""Tests for Timeline.pack_all_tracks and Timeline.remove_empty_tracks."""
from __future__ import annotations

from camtasia.timeline.timeline import Timeline
from camtasia.timing import EDIT_RATE


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

    def test_delegates_to_remove_empty_tracks(self) -> None:
        """Verify remove_empty_tracks produces the same result as remove_empty_tracks."""
        tracks_a = [{"medias": []}, {"medias": [_clip(1, 0, 100)]}, {"medias": []}]
        tracks_b = [{"medias": []}, {"medias": [_clip(1, 0, 100)]}, {"medias": []}]

        timeline_a = Timeline(_make_timeline_data(tracks_a))
        timeline_b = Timeline(_make_timeline_data(tracks_b))

        count_a: int = timeline_a.remove_empty_tracks()
        count_b: int = timeline_b.remove_empty_tracks()

        assert count_a == count_b
        assert timeline_a.track_count == timeline_b.track_count


def test_timeline_duration_seconds_property(project):
    """Timeline.duration_seconds delegates to total_duration_seconds."""
    assert project.timeline.duration_seconds == 0.0


# ── Merged from test_coverage_timeline.py ────────────────────────────

import copy
import pytest
from camtasia.timing import seconds_to_ticks


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
        assert len(data['trackAttributes']) >= 2


class TestSortTracksByNamePadsAttrs:
    def test_pads_missing_attrs(self):
        t0 = _tl_track_data(0, [_tl_media(1)])
        t1 = _tl_track_data(1, [_tl_media(2, start=100)])
        data = _tl_make_timeline_data([t0, t1], [{'ident': 'B'}])
        tl = Timeline(data)
        tl.sort_tracks_by_name()
        assert len(data['trackAttributes']) >= 2


class TestReorderTracksPadsAttrs:
    def test_pads_missing_attrs(self):
        t0 = _tl_track_data(0, [_tl_media(1)])
        t1 = _tl_track_data(1, [_tl_media(2, start=100)])
        data = _tl_make_timeline_data([t0, t1], [])
        tl = Timeline(data)
        tl.reorder_tracks([1, 0])
        assert len(data['trackAttributes']) >= 2
