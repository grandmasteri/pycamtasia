"""Tests for camtasia.timeline.timeline — track management and L2 methods."""
from __future__ import annotations

from typing import Any

import pytest

from camtasia.timeline.timeline import Timeline
from camtasia.timeline.track import Track
from camtasia.timeline.marker import Marker
from camtasia.timing import EDIT_RATE, seconds_to_ticks


def _timeline_data(num_tracks: int = 1) -> dict[str, Any]:
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
        tl = Timeline(_timeline_data())
        assert tl.total_duration_ticks == 0
        assert tl.total_duration_seconds() == 0.0

    def test_duration_from_clips(self):
        data = _timeline_data()
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
        tl = Timeline(_timeline_data(2))
        actual_track = tl.get_or_create_track("Track 0")
        assert actual_track.name == "Track 0"

    def test_creates_new_track_when_not_found(self):
        tl = Timeline(_timeline_data())
        actual_track = tl.get_or_create_track("New Track")
        assert actual_track.name == "New Track"
        assert tl.track_count == 2


class TestTimelineAllClips:
    def test_empty_timeline_returns_empty(self):
        tl = Timeline(_timeline_data())
        assert tl.all_clips() == []

    def test_collects_clips_across_tracks(self):
        data = _timeline_data(2)
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
        tl = Timeline(_timeline_data())
        actual_marker = tl.add_marker("Chapter 1", 2.5)
        assert actual_marker.name == "Chapter 1"
        assert actual_marker.time == seconds_to_ticks(2.5)


class TestTimelineRemoveTrack:
    def test_remove_track_reduces_count(self):
        tl = Timeline(_timeline_data(3))
        assert tl.track_count == 3
        tl.remove_track(1)
        assert tl.track_count == 2

    def test_remove_track_renumbers(self):
        tl = Timeline(_timeline_data(3))
        tl.remove_track(0)
        actual_indices = [t.index for t in tl.tracks]
        assert actual_indices == [0, 1]

    def test_remove_nonexistent_track_raises(self):
        tl = Timeline(_timeline_data())
        with pytest.raises(KeyError, match="No track with index=99"):
            tl.remove_track(99)


class TestDuplicateTrackRemapsTransitions:
    """Cover timeline.py lines 188-193: transition leftMedia/rightMedia remapping."""

    def test_duplicate_track_remaps_transition_references(self):
        data = _timeline_data()
        tl = Timeline(data)
        track = tl.tracks[0]
        c1 = track.add_clip('VMFile', 1, 0, seconds_to_ticks(5.0))
        c2 = track.add_clip('VMFile', 1, seconds_to_ticks(5.0), seconds_to_ticks(5.0))
        track.add_transition('FadeThroughBlack', c1, c2, duration_seconds=0.5)
        tl.duplicate_track(0)
        dup_track = tl.tracks[1]
        dup_transitions = dup_track._data.get('transitions', [])
        # Transitions should reference the new clip IDs, not the originals
        orig_ids = {c1.id, c2.id}
        for t in dup_transitions:
            if t.get('leftMedia') is not None:
                assert t['leftMedia'] not in orig_ids
            if t.get('rightMedia') is not None:
                assert t['rightMedia'] not in orig_ids


class TestClipsOfTypeWithStitchedMedia:
    """Cover timeline.py line 569: _register_ids recursion into video/audio sub-dicts."""

    def test_finds_clips_inside_unified_media(self):
        data = _timeline_data()
        # Add a UnifiedMedia clip with video/audio sub-dicts
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


# ── from test_coverage_phase4: timeline.py remap helpers ──

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


def test_group_clips_in_range(project):
    tl = project.timeline
    track = tl.tracks[0]
    track.add_video(1, start_seconds=0, duration_seconds=5)
    group = tl.group_clips_in_range(0.0, 5.0, 0)
    assert group is not None


def test_group_clips_in_range_no_clips(project):
    tl = project.timeline
    with pytest.raises(ValueError, match='No clips found'):
        tl.group_clips_in_range(100.0, 200.0, 0)


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


def test_duplicate_track_registers_ids(project):
    tl = project.timeline
    t0 = tl.tracks[0]
    t0.add_video(1, start_seconds=0, duration_seconds=3)
    tl.duplicate_track(0)
    assert tl.track_count >= 2
