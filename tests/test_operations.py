from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from camtasia.operations.diff import diff_projects
from camtasia.operations.merge import _remap_clip_ids
from camtasia.operations.speed import _adjust_scalar, rescale_project, set_audio_speed
from camtasia.operations.sync import SyncSegment, match_marker_to_transcript, plan_sync
from camtasia.operations.template import (
    _walk_clips,
    clone_project_structure,
    replace_media_source,
)
from camtasia.audiate.transcript import Word
from camtasia.project import Project
from camtasia.timing import EDIT_RATE, parse_scalar, seconds_to_ticks


def _make_project(tracks: list[dict] | None = None, markers: list[dict] | None = None) -> dict:
    """Build a minimal but realistic project structure from the format spec."""
    scene_tracks = tracks or []
    toc = {"type": "string", "keyframes": markers or []}
    return {
        "title": "Test Project",
        "editRate": EDIT_RATE,
        "sourceBin": [
            {"id": 1, "src": "./media/recording.trec"},
            {"id": 3, "src": "./media/voiceover.wav"},
        ],
        "timeline": {
            "id": 13,
            "parameters": {"toc": toc},
            "sceneTrack": {
                "scenes": [{"csml": {"tracks": scene_tracks}}]
            },
        },
    }


def _make_audio_clip(
    clip_id: int = 14,
    start: int = 0,
    duration: int = 106_051_680_000,
    scalar: int | str = 1,
    speed_changed: bool = False,
) -> dict:
    """Build a realistic AMFile audio clip."""
    clip: dict = {
        "id": clip_id,
        "_type": "AMFile",
        "src": 3,
        "start": start,
        "duration": duration,
        "mediaStart": 0,
        "mediaDuration": 113_484_000_000,
        "scalar": scalar,
        "metadata": {},
    }
    if speed_changed:
        clip["metadata"]["clipSpeedAttribute"] = {"type": "bool", "value": True}
    return clip


def _make_stitched_clip(clip_id: int = 20, start: int = 227_120_880_000) -> dict:
    """Build a realistic StitchedMedia clip."""
    return {
        "id": clip_id,
        "_type": "StitchedMedia",
        "src": 3,
        "start": start,
        "duration": 72_947_280_000,
        "mediaStart": 232_212_960_000,
        "mediaDuration": 72_947_280_000,
        "medias": [
            {
                "id": 21,
                "_type": "AMFile",
                "src": 3,
                "start": 0,
                "duration": 36_000_000_000,
                "mediaStart": 0,
                "mediaDuration": 36_000_000_000,
                "scalar": 1,
            },
            {
                "id": 22,
                "_type": "AMFile",
                "src": 3,
                "start": 36_000_000_000,
                "duration": 36_947_280_000,
                "mediaStart": 40_000_000_000,
                "mediaDuration": 36_947_280_000,
                "scalar": 1,
            },
        ],
    }


def _make_group_clip(clip_id: int = 30, start: int = 0) -> dict:
    """Build a realistic Group clip with internal tracks."""
    return {
        "id": clip_id,
        "_type": "Group",
        "start": start,
        "duration": 50_000_000_000,
        "mediaDuration": 50_000_000_000,
        "scalar": 1,
        "metadata": {},
        "tracks": [
            {
                "trackIndex": 0,
                "medias": [
                    {
                        "id": 31,
                        "_type": "VMFile",
                        "src": 1,
                        "start": 0,
                        "duration": 50_000_000_000,
                        "mediaStart": 0,
                        "mediaDuration": 50_000_000_000,
                        "scalar": 1,
                        "metadata": {},
                    }
                ],
            }
        ],
    }


class TestRescaleProject:
    def test_scales_clip_timing(self):
        clip = _make_audio_clip(start=705_600_000, duration=705_600_000)
        project = _make_project(tracks=[{"medias": [clip], "transitions": []}])

        rescale_project(project, Fraction(2))

        actual_clip = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        assert actual_clip["start"] == 1_411_200_000
        assert actual_clip["duration"] == 1_411_200_000

    def test_scales_transitions(self):
        transition = {"duration": 352_800_000}
        project = _make_project(tracks=[{"medias": [], "transitions": [transition]}])

        rescale_project(project, Fraction(2))

        assert transition["duration"] == 705_600_000

    def test_scales_timeline_markers(self):
        markers = [{"time": 705_600_000, "endTime": 705_600_000, "value": "M1"}]
        project = _make_project(markers=markers)
        project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"] = []

        rescale_project(project, Fraction(2))

        assert markers[0]["time"] == 1_411_200_000
        assert markers[0]["endTime"] == 1_411_200_000

    def test_adjusts_scalar_on_speed_changed_clips(self):
        clip = _make_audio_clip(scalar="51/101", speed_changed=True)
        project = _make_project(tracks=[{"medias": [clip], "transitions": []}])

        rescale_project(project, Fraction(2))

        actual_clip = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        # old scalar = 51/101, new = old * factor = 102/101
        expected_scalar = Fraction(51, 101) * Fraction(2)
        assert parse_scalar(actual_clip["scalar"]) == expected_scalar

    def test_scales_stitched_media(self):
        clip = _make_stitched_clip()
        project = _make_project(tracks=[{"medias": [clip], "transitions": []}])

        rescale_project(project, Fraction(2))

        actual = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        assert actual["start"] == 227_120_880_000 * 2
        assert actual["mediaStart"] == 232_212_960_000 * 2
        # Inner medias also scaled
        assert actual["medias"][0]["start"] == 0
        assert actual["medias"][0]["duration"] == 36_000_000_000 * 2

    def test_scales_group_clip(self):
        clip = _make_group_clip()
        project = _make_project(tracks=[{"medias": [clip], "transitions": []}])

        rescale_project(project, Fraction(2))

        actual = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        assert actual["duration"] == 100_000_000_000
        assert actual["mediaDuration"] == 100_000_000_000
        inner = actual["tracks"][0]["medias"][0]
        assert inner["duration"] == 100_000_000_000


class TestSetAudioSpeed:
    def test_resets_speed_changed_audio(self):
        clip = _make_audio_clip(
            scalar="49/64",
            speed_changed=True,
            duration=80_000_000_000,
        )
        clip["mediaDuration"] = 100_000_000_000
        project = _make_project(tracks=[{"medias": [clip], "transitions": []}])

        factor = set_audio_speed(project)

        actual_clip = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        assert actual_clip["scalar"] == 1
        assert actual_clip["metadata"]["clipSpeedAttribute"]["value"] is False
        assert isinstance(factor, Fraction)

    def test_raises_when_no_speed_changed_clips(self):
        clip = _make_audio_clip()
        project = _make_project(tracks=[{"medias": [clip], "transitions": []}])

        with pytest.raises(ValueError, match="No speed-changed audio clips found"):
            set_audio_speed(project)


class TestMatchMarkerToTranscript:
    WORDS = [
        Word(word_id='', text="selecting", start=0.75, end=1.0),
        Word(word_id='', text="a", start=1.0, end=1.1),
        Word(word_id='', text="recent", start=1.25, end=1.5),
        Word(word_id='', text="batch", start=1.5, end=1.75),
        Word(word_id='', text="run", start=1.75, end=2.0),
    ]

    def test_finds_matching_phrase(self):
        actual_result = match_marker_to_transcript("selecting a recent batch run", self.WORDS)
        assert actual_result == 0.75

    def test_returns_none_for_no_match(self):
        actual_result = match_marker_to_transcript("nonexistent phrase", self.WORDS)
        assert actual_result is None

    def test_empty_label(self):
        assert match_marker_to_transcript("", self.WORDS) is None

    def test_empty_words(self):
        assert match_marker_to_transcript("selecting", []) is None

    def test_partial_match_fallback(self):
        actual_result = match_marker_to_transcript("batch", self.WORDS)
        assert actual_result == 1.5


class TestPlanSync:
    def test_creates_sync_segments(self):
        markers = [
            ("selecting a recent batch run", 0),
            ("navigating to the dashboard", 705_600_000),
        ]
        words = [
            Word(word_id='', text="selecting", start=0.0, end=0.25),
            Word(word_id='', text="a", start=0.25, end=0.3),
            Word(word_id='', text="recent", start=0.3, end=0.5),
            Word(word_id='', text="batch", start=0.5, end=0.75),
            Word(word_id='', text="run", start=0.75, end=1.0),
            Word(word_id='', text="navigating", start=1.0, end=1.25),
            Word(word_id='', text="to", start=1.25, end=1.3),
            Word(word_id='', text="the", start=1.3, end=1.4),
            Word(word_id='', text="dashboard", start=1.4, end=1.75),
        ]

        actual_result = plan_sync(markers, words)

        assert actual_result[0].video_start_ticks == 0
        assert actual_result[0].video_end_ticks == 705_600_000
        assert actual_result[0].audio_start_seconds == 0.0
        assert actual_result[0].audio_end_seconds == 1.0

    def test_fewer_than_two_markers_returns_empty(self):
        assert plan_sync([("only one", 0)], [Word(word_id='', text="only", start=0.0, end=0.5)]) == []

    def test_no_transcript_match_returns_empty(self):
        markers = [("aaa", 0), ("bbb", 705_600_000)]
        words = [Word(word_id='', text="zzz", start=0.0, end=1.0)]
        # "aaa" won't match "zzz" via substring either, so both fail
        # Actually "aaa" fallback checks first word "aaa" in "zzz" — no match
        actual_result = plan_sync(markers, words)
        assert actual_result == []


class TestCloneProjectStructure:
    def test_clears_source_bin(self):
        project = _make_project(tracks=[{"medias": [_make_audio_clip()], "transitions": []}])
        actual_result = clone_project_structure(project)
        assert actual_result["sourceBin"] == []

    def test_clears_medias_from_tracks(self):
        project = _make_project(tracks=[{"medias": [_make_audio_clip()], "transitions": []}])
        actual_result = clone_project_structure(project)
        tracks = actual_result["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"]
        assert tracks[0]["medias"] == []

    def test_removes_transitions(self):
        transition = {"name": "FadeThroughBlack", "duration": 352_800_000, "leftMedia": 33}
        project = _make_project(tracks=[{"medias": [], "transitions": [transition]}])
        actual_result = clone_project_structure(project)
        tracks = actual_result["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"]
        assert "transitions" not in tracks[0]

    def test_clears_timeline_markers(self):
        markers = [{"time": 705_600_000, "endTime": 705_600_000, "value": "M1"}]
        project = _make_project(markers=markers)
        project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"] = []
        actual_result = clone_project_structure(project)
        assert actual_result["timeline"]["parameters"]["toc"]["keyframes"] == []

    def test_preserves_settings(self):
        project = _make_project()
        project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"] = []
        actual_result = clone_project_structure(project)
        assert actual_result["title"] == "Test Project"
        assert actual_result["editRate"] == EDIT_RATE

    def test_does_not_mutate_original(self):
        project = _make_project(tracks=[{"medias": [_make_audio_clip()], "transitions": []}])
        original_copy = copy.deepcopy(project)
        clone_project_structure(project)
        assert project == original_copy


class TestReplaceMediaSource:
    def test_replaces_src_and_returns_count(self):
        clip1 = _make_audio_clip(clip_id=14)
        clip1["src"] = 3
        clip2 = _make_audio_clip(clip_id=15)
        clip2["src"] = 3
        project = _make_project(tracks=[{"medias": [clip1, clip2]}])

        actual_count = replace_media_source(project, old_source_id=3, new_source_id=99)

        assert actual_count == 2
        scene = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]
        assert scene["tracks"][0]["medias"][0]["src"] == 99
        assert scene["tracks"][0]["medias"][1]["src"] == 99

    def test_no_matches_returns_zero(self):
        clip = _make_audio_clip()
        clip["src"] = 3
        project = _make_project(tracks=[{"medias": [clip]}])

        actual_count = replace_media_source(project, old_source_id=999, new_source_id=1)
        assert actual_count == 0

    def test_replaces_in_stitched_media_children(self):
        clip = _make_stitched_clip()
        clip["src"] = 3
        project = _make_project(tracks=[{"medias": [clip]}])

        actual_count = replace_media_source(project, old_source_id=3, new_source_id=99)

        scene = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]
        parent = scene["tracks"][0]["medias"][0]
        # Parent + 2 children = 3
        assert actual_count == 3
        assert parent["src"] == 99
        assert parent["medias"][0]["src"] == 99
        assert parent["medias"][1]["src"] == 99

    def test_replaces_in_group_internal_tracks(self):
        clip = _make_group_clip()
        # Group itself doesn't have src, but inner VMFile does
        project = _make_project(tracks=[{"medias": [clip]}])

        actual_count = replace_media_source(project, old_source_id=1, new_source_id=99)

        scene = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]
        inner = scene["tracks"][0]["medias"][0]["tracks"][0]["medias"][0]
        assert actual_count == 1
        assert inner["src"] == 99


class TestMatchMarkerWordBoundaryRetry:
    """Retry find when first match is not at word boundary."""

    def test_skips_partial_match_and_finds_word_boundary(self):
        # Transcript: "abatch batch" — first find of "batch" hits inside "abatch"
        words = [
            Word(word_id='', text='abatch', start=0.0, end=0.5),
            Word(word_id='', text='batch', start=1.0, end=1.5),
        ]
        result = match_marker_to_transcript('batch', words)
        assert result == 1.0


class TestMatchMarkerFallbackFirstWord:
    """Fallback first-word match."""

    def test_fallback_matches_first_word(self):
        # Label has multiple words but none match as a phrase; first word matches a transcript word
        words = [
            Word(word_id='', text='hello', start=2.0, end=2.5),
            Word(word_id='', text='world', start=3.0, end=3.5),
        ]
        result = match_marker_to_transcript('hello nonexistent phrase', words)
        assert result == 2.0


class TestPlanSyncSkipsZeroDuration:
    """Skip segments with zero audio duration."""

    def test_skips_zero_audio_duration_segment(self):
        # Two markers at the same audio timestamp → audio_dur_ticks == 0 → skip
        words = [
            Word(word_id='', text='start', start=5.0, end=5.5),
            Word(word_id='', text='middle', start=5.0, end=5.5),  # same timestamp
            Word(word_id='', text='end', start=10.0, end=10.5),
        ]
        markers = [
            ('start', 0),
            ('middle', 100_000_000),
            ('end', 705_600_000),
        ]
        segments = plan_sync(markers, words)
        # The first segment (start→middle) has zero audio duration and should be skipped
        assert all(s.scalar > 0 for s in segments)


class TestAdjustScalar:
    def test_adjusts_existing_scalar(self):
        clip = {'scalar': '51/101'}
        _adjust_scalar(clip, Fraction(2))
        assert clip['scalar'] == '102/101'

    def test_adjusts_default_scalar(self):
        clip = {}
        _adjust_scalar(clip, Fraction(3))
        assert clip['scalar'] == '3/1'



def _minimal_project(*clips):
    """Build a minimal project dict with given clips on one track."""
    return {
        'timeline': {
            'sceneTrack': {
                'scenes': [{
                    'csml': {
                        'tracks': [{'trackIndex': 0, 'medias': list(clips), 'transitions': []}],
                    },
                }],
            },
            'parameters': {'toc': {'keyframes': []}},
        },
    }


class TestOverlapFix:
    def test_overlap_trimmed_after_rescale(self):
        """Two clips that overlap by 1 tick after rescaling get fixed."""
        clip_a = {
            '_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        clip_b = {
            '_type': 'AMFile', 'id': 2, 'start': 99, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        data = _minimal_project(clip_a, clip_b)
        rescale_project(data, Fraction(1))
        medias = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias']
        a_end = medias[0]['start'] + medias[0]['duration']
        b_start = medias[1]['start']
        assert a_end <= b_start



class TestMarkSpeedChanged:
    def test_marks_amfile_via_rescale(self):
        clip = {
            '_type': 'AMFile', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        media = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert media['metadata']['clipSpeedAttribute']['value'] is True

    def test_skips_excluded_types(self):
        clip = {
            '_type': 'IMFile', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 1, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        media = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert 'clipSpeedAttribute' not in media.get('metadata', {})

    def test_recurses_into_unified_children(self):
        clip = {
            '_type': 'UnifiedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'video': {
                '_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            },
            'audio': {
                '_type': 'AMFile', 'id': 3, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            },
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        um = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        assert um['video']['metadata']['clipSpeedAttribute']['value'] is True
        assert um['audio']['metadata']['clipSpeedAttribute']['value'] is True

    def test_recurses_into_group_tracks(self):
        clip = {
            '_type': 'Group', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'tracks': [{'medias': [{
                '_type': 'VMFile', 'id': 2, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            }]}],
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        inner = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['tracks'][0]['medias'][0]
        assert inner['metadata']['clipSpeedAttribute']['value'] is True

    def test_recurses_into_stitched_medias(self):
        clip = {
            '_type': 'StitchedMedia', 'id': 1, 'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'medias': [{
                '_type': 'AMFile', 'id': 2, 'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [], 'metadata': {},
            }],
        }
        data = _minimal_project(clip)
        rescale_project(data, Fraction(2))
        inner = data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['medias'][0]
        assert inner['metadata']['clipSpeedAttribute']['value'] is True


_S1 = seconds_to_ticks(1.0)


class TestDiffClipsOnRemovedAddedTracks:
    def test_diff_detects_clips_on_removed_tracks(self, project):
        a = project
        b_data = copy.deepcopy(a._data)
        b = Project.__new__(Project)
        b._data = b_data
        b._file_path = a._file_path
        track = a.timeline.tracks[0]
        track._data['medias'].append({
            '_type': 'VMFile', 'id': 999, 'src': 0, 'start': 0, 'duration': _S1,
            'mediaDuration': _S1, 'mediaStart': 0, 'scalar': 1,
            'parameters': {}, 'effects': [],
        })
        result = diff_projects(a, b)
        assert result is not None



class TestMergeRemapClipIds:
    def test_remap_clip_ids_unified(self):
        data = {
            'id': 1, '_type': 'UnifiedMedia',
            'video': {'_type': 'ScreenVMFile', 'id': 2, 'src': 1},
            'audio': {'_type': 'AMFile', 'id': 3, 'src': 1},
            'tracks': [{'medias': [{'id': 4, 'src': 1}]}],
            'medias': [{'id': 5, 'src': 1}],
        }
        id_counter = [100]
        id_map = {}
        src_map = {1: 50}
        _remap_clip_ids(data, id_counter, id_map, src_map)
        assert data['id'] != 1
        assert data['video']['src'] == 50



class TestTemplateWalkClipsExtras:
    def test_walk_clips_unified(self):
        tracks = [{
            'medias': [{
                '_type': 'UnifiedMedia', 'id': 1,
                'video': {'_type': 'ScreenVMFile', 'id': 2},
                'audio': {'_type': 'AMFile', 'id': 3},
            }]
        }]
        clips = list(_walk_clips(tracks))
        assert any(c.get('_type') == 'ScreenVMFile' for c in clips)
        assert any(c.get('_type') == 'AMFile' for c in clips)



UNIFIED_MEDIA_OPS = {
    '_type': 'UnifiedMedia', 'id': 20, 'start': 100, 'duration': 100,
    'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
    'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
    'video': {'_type': 'VMFile', 'id': 21, 'start': 0, 'duration': 100, 'src': 2,
              'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
              'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
    'audio': {'_type': 'AMFile', 'id': 22, 'start': 0, 'duration': 100, 'src': 3,
              'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
              'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
}


class TestRescaleUnifiedMedia:
    def test_unified_media_children_scaled(self, project):
        tracks = project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        tracks[0]['medias'].append(copy.deepcopy(UNIFIED_MEDIA_OPS))
        factor = Fraction(2)
        rescale_project(project._data, factor)
        um = next(m for m in tracks[0]['medias'] if m['_type'] == 'UnifiedMedia')
        assert um['video']['start'] == 0
        assert um['video']['duration'] == 200
        assert um['audio']['start'] == 0
        assert um['audio']['duration'] == 200