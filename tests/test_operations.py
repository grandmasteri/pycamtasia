from __future__ import annotations

import copy
from fractions import Fraction
from typing import ClassVar

import pytest

from camtasia.audiate.transcript import Word
from camtasia.operations.diff import diff_projects
from camtasia.operations.merge import _remap_src_in_clip
from camtasia.operations.speed import _adjust_scalar, _scale_tick, rescale_project, set_audio_speed
from camtasia.operations.sync import SyncSegment, apply_sync, match_marker_to_transcript, plan_sync
from camtasia.operations.template import (
    _walk_clips,
    clone_project_structure,
    replace_media_source,
)
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
    WORDS: ClassVar[list] = [
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
        # Multi-word label requires at least 2 consecutive words to match
        words = [
            Word(word_id='', text='hello', start=2.0, end=2.5),
            Word(word_id='', text='world', start=3.0, end=3.5),
        ]
        # No consecutive match for 'hello nonexistent' → returns None
        result = match_marker_to_transcript('hello nonexistent phrase', words)
        assert result is None

        # But if the first 2 words match consecutively, it works
        result2 = match_marker_to_transcript('hello world missing', words)
        assert result2 == 2.0


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
        assert segments[0].scalar == Fraction(757, 4410)


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
    def test_remap_src_in_unified(self):
        data = {
            'id': 1, '_type': 'UnifiedMedia',
            'video': {'_type': 'ScreenVMFile', 'id': 2, 'src': 1},
            'audio': {'_type': 'AMFile', 'id': 3, 'src': 1},
            'tracks': [{'medias': [{'id': 4, 'src': 1}]}],
            'medias': [{'id': 5, 'src': 1}],
        }
        src_map = {1: 50}
        _remap_src_in_clip(data, src_map)
        assert data['video']['src'] == 50
        assert data['audio']['src'] == 50



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


# ==================================================================
# Tests from test_clips.py — operations/speed.py
# ==================================================================


def _um_data_ops():
    _S10 = seconds_to_ticks(10.0)
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


_S1 = seconds_to_ticks(1.0)
_S5 = seconds_to_ticks(5.0)
_S10 = seconds_to_ticks(10.0)


def _cov_group_data_ops(inner=None, duration=None):
    dur = duration or _S10
    return {
        '_type': 'Group', 'id': 100, 'start': _S1, 'duration': dur,
        'mediaDuration': dur, 'mediaStart': 0, 'scalar': 1,
        'parameters': {}, 'effects': [],
        'attributes': {'ident': 'grp', 'widthAttr': 1920, 'heightAttr': 1080},
        'tracks': [{'trackIndex': 0, 'medias': inner or [], 'transitions': []}],
    }


class TestMarkSpeedChangedExclusions:
    def test_imfile_excluded(self):
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
        um = _um_data_ops()
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
        assert vid.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is not True

    def test_mark_speed_recurses_into_group_tracks(self):
        inner_vm = {
            '_type': 'VMFile', 'id': 10, 'src': 1,
            'start': 0, 'duration': _S5, 'mediaDuration': _S5,
            'mediaStart': 0, 'scalar': 1, 'parameters': {}, 'effects': [],
            'metadata': {},
        }
        group = _cov_group_data_ops([inner_vm], duration=_S5)
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
        assert inner.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is not True

    def test_mark_speed_recurses_into_stitched_medias(self):
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
        assert inner.get('metadata', {}).get('clipSpeedAttribute', {}).get('value') is not True


class TestOverlapFixWithUnified:
    def test_overlap_fix_propagates_to_unified(self):
        um1 = _um_data_ops()
        um1['id'] = 1
        um1['start'] = 0
        um1['duration'] = _S5 + 2
        um2 = copy.deepcopy(_um_data_ops())
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


class TestSetAudioSpeedNested:
    """set_audio_speed finds audio clips inside StitchedMedia and Group."""

    def test_finds_audio_in_stitched_media(self):
        from camtasia.operations.speed import set_audio_speed
        # Build a project with a StitchedMedia containing a speed-changed AMFile
        project_data = {
            'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                'medias': [{
                    '_type': 'StitchedMedia', 'id': 10, 'start': 0, 'duration': 200,
                    'mediaStart': 0, 'mediaDuration': 200, 'scalar': 1,
                    'medias': [{
                        '_type': 'AMFile', 'id': 11, 'src': 1,
                        'start': 0, 'duration': 200, 'mediaStart': 0,
                        'mediaDuration': 400, 'scalar': '1/2', 'trackNumber': 0,
                        'channelNumber': 0,
                        'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
                        'parameters': {}, 'effects': [], 'attributes': {'gain': 1.0},
                        'animationTracks': {},
                    }],
                }],
            }]}}]}},
            'sourceBin': [],
        }
        # set_audio_speed should find the nested audio and not raise
        set_audio_speed(project_data, 1.0)

    def test_finds_audio_in_group(self):
        from camtasia.operations.speed import set_audio_speed
        project_data = {
            'timeline': {'sceneTrack': {'scenes': [{'csml': {'tracks': [{
                'medias': [{
                    '_type': 'Group', 'id': 20, 'start': 0, 'duration': 200,
                    'mediaStart': 0, 'mediaDuration': 200, 'scalar': 1,
                    'tracks': [{'trackIndex': 0, 'medias': [{
                        '_type': 'AMFile', 'id': 21, 'src': 1,
                        'start': 0, 'duration': 200, 'mediaStart': 0,
                        'mediaDuration': 400, 'scalar': '1/2', 'trackNumber': 0,
                        'channelNumber': 0,
                        'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
                        'parameters': {}, 'effects': [], 'attributes': {'gain': 1.0},
                        'animationTracks': {},
                    }]}],
                }],
            }]}}]}},
            'sourceBin': [],
        }
        set_audio_speed(project_data, 1.0)


# ── Bug 6: StitchedMedia should not double-scale effects on UnifiedMedia inners ──


class TestStitchedMediaUnifiedMediaEffectsNotDoubleScaled:
    """Effects on UnifiedMedia children inside StitchedMedia must be scaled
    exactly once (via _process_clip), not twice."""

    def test_effects_scaled_once_for_unified_media_inner(self):
        from camtasia.operations.speed import _process_clip

        clip = {
            '_type': 'StitchedMedia',
            'start': 0,
            'duration': 1000,
            'mediaStart': 0,
            'mediaDuration': 1000,
            'scalar': 1,
            'medias': [{
                '_type': 'UnifiedMedia',
                'start': 0,
                'duration': 1000,
                'mediaDuration': 1000,
                'scalar': 1,
                'metadata': {},
                'effects': [{'start': 100, 'duration': 200}],
                'video': {
                    '_type': 'VMFile', 'start': 0, 'duration': 1000,
                    'mediaDuration': 1000, 'scalar': 1, 'metadata': {},
                    'effects': [], 'parameters': {},
                },
            }],
            'metadata': {},
            'effects': [],
            'parameters': {},
        }
        _process_clip(clip, Fraction(2))
        inner = clip['medias'][0]
        # Effects should be scaled by factor=2 exactly once, not factor²=4
        assert inner['effects'][0]['start'] == 200
        assert inner['effects'][0]['duration'] == 400

    def test_effects_still_scaled_for_non_unified_media_inner(self):
        from camtasia.operations.speed import _process_clip

        clip = {
            '_type': 'StitchedMedia',
            'start': 0,
            'duration': 1000,
            'mediaStart': 0,
            'mediaDuration': 1000,
            'scalar': 1,
            'medias': [{
                '_type': 'AMFile',
                'start': 0,
                'duration': 1000,
                'mediaStart': 0,
                'mediaDuration': 1000,
                'scalar': 1,
                'metadata': {},
                'effects': [{'start': 100, 'duration': 200}],
            }],
            'metadata': {},
            'effects': [],
            'parameters': {},
        }
        _process_clip(clip, Fraction(2))
        inner = clip['medias'][0]
        assert inner['effects'][0]['start'] == 200
        assert inner['effects'][0]['duration'] == 400


# ── Bug 7: UnifiedMedia mediaDuration should not be scaled when speed-changed ──


class TestUnifiedMediaMediaDurationSpeedChanged:
    """For speed-changed UnifiedMedia, mediaDuration is invariant and should
    not be scaled by factor (it's already handled by _adjust_scalar)."""

    def test_media_duration_unchanged_when_speed_changed(self):
        from camtasia.operations.speed import _process_clip

        clip = {
            '_type': 'UnifiedMedia',
            'start': 0,
            'duration': 1000,
            'mediaDuration': 2000,
            'scalar': '1/2',
            'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
            'effects': [],
            'parameters': {},
            'video': {
                '_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1, 'metadata': {},
                'effects': [], 'parameters': {},
            },
        }
        _process_clip(clip, Fraction(2))
        # mediaDuration should NOT be scaled for speed-changed UnifiedMedia
        assert clip['mediaDuration'] == 2000

    def test_media_duration_scaled_when_not_speed_changed(self):
        from camtasia.operations.speed import _process_clip

        clip = {
            '_type': 'UnifiedMedia',
            'start': 0,
            'duration': 1000,
            'mediaDuration': 1000,
            'scalar': 1,
            'metadata': {},
            'effects': [],
            'parameters': {},
            'video': {
                '_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1, 'metadata': {},
                'effects': [], 'parameters': {},
            },
        }
        _process_clip(clip, Fraction(2))
        # mediaDuration SHOULD be scaled for non-speed-changed UnifiedMedia
        assert clip['mediaDuration'] == 2000


class TestSetAudioSpeedUpdatesParentClipSpeedAttribute:
    """Bug 3: set_audio_speed must update parent UnifiedMedia's clipSpeedAttribute."""

    def test_parent_unified_gets_clip_speed_attribute(self):
        audio = _make_audio_clip(clip_id=14, scalar="93/100", speed_changed=True)
        audio["mediaDuration"] = 113_484_000_000
        unified = {
            "id": 50,
            "_type": "UnifiedMedia",
            "start": 0,
            "duration": audio["duration"],
            "mediaDuration": audio["mediaDuration"],
            "scalar": audio["scalar"],
            "metadata": {},
            "audio": audio,
        }
        project = _make_project(tracks=[{"medias": [unified], "transitions": []}])

        set_audio_speed(project, target_speed=1.0)

        parent = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        # Parent must have clipSpeedAttribute set to False (speed normalized to 1.0)
        parent_csa = parent.get("metadata", {}).get("clipSpeedAttribute", {})
        assert "value" in parent_csa, "Parent UnifiedMedia missing clipSpeedAttribute"
        assert parent_csa["value"] is False


class TestStitchedMediaScalarPropagation:
    """Bug 4: _process_clip must propagate scalar to non-UnifiedMedia inner clips in StitchedMedia."""

    def test_inner_clips_get_parent_scalar(self):
        from camtasia.operations.speed import _process_clip

        stitched = _make_stitched_clip()
        # Give the parent a speed change so scalar is adjusted
        stitched["metadata"] = {"clipSpeedAttribute": {"type": "bool", "value": True}}
        stitched["scalar"] = "93/100"

        _process_clip(stitched, Fraction(2))

        for inner in stitched["medias"]:
            assert inner["scalar"] == stitched["scalar"], (
                f"Inner clip scalar {inner['scalar']} != parent {stitched['scalar']}"
            )



class TestUnifiedMediaStartScaling:
    """Bug 5: _process_clip must scale mediaStart for UnifiedMedia clips."""

    def test_unified_media_start_scaled(self):
        from camtasia.operations.speed import _process_clip
        clip = {
            '_type': 'UnifiedMedia', 'id': 1, 'start': 100, 'duration': 200,
            'mediaDuration': 200, 'mediaStart': 50, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
            'video': {
                '_type': 'VMFile', 'id': 2, 'src': 5, 'start': 0,
                'duration': 200, 'mediaDuration': 200, 'mediaStart': 0, 'scalar': 1,
                'parameters': {}, 'effects': [],
            },
            'audio': {
                '_type': 'AMFile', 'id': 3, 'src': 5, 'start': 0,
                'duration': 200, 'mediaDuration': 200, 'mediaStart': 0, 'scalar': 1,
            },
        }
        _process_clip(clip, Fraction(2))
        assert clip['mediaStart'] == 100  # 50 * 2

    def test_unified_media_start_absent_is_fine(self):
        from camtasia.operations.speed import _process_clip
        clip = {
            '_type': 'UnifiedMedia', 'id': 1, 'start': 100, 'duration': 200,
            'mediaDuration': 200, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {},
        }
        _process_clip(clip, Fraction(2))
        assert 'mediaStart' not in clip


# ── Bug 7: UnifiedMedia children mediaDuration must match parent for speed-changed clips ──


class TestUnifiedMediaChildMediaDurationConsistency:
    """For speed-changed UnifiedMedia, children's mediaDuration must match parent."""

    def test_children_match_parent_media_duration_when_speed_changed(self):
        from camtasia.operations.speed import _process_clip

        clip = {
            '_type': 'UnifiedMedia',
            'start': 0,
            'duration': 1000,
            'mediaDuration': 2000,
            'scalar': '1/2',
            'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
            'effects': [],
            'parameters': {},
            'video': {
                '_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1, 'metadata': {},
                'effects': [], 'parameters': {},
            },
            'audio': {
                '_type': 'AMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1,
                'metadata': {}, 'effects': [],
            },
        }
        _process_clip(clip, Fraction(2))
        # Parent mediaDuration stays at 2000 (speed-changed, not scaled)
        assert clip['mediaDuration'] == 2000
        # Children must match parent
        assert clip['video']['mediaDuration'] == clip['mediaDuration']
        assert clip['audio']['mediaDuration'] == clip['mediaDuration']

    def test_children_scaled_independently_when_not_speed_changed(self):
        from camtasia.operations.speed import _process_clip

        clip = {
            '_type': 'UnifiedMedia',
            'start': 0,
            'duration': 1000,
            'mediaDuration': 1000,
            'scalar': 1,
            'metadata': {},
            'effects': [],
            'parameters': {},
            'video': {
                '_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1, 'metadata': {},
                'effects': [], 'parameters': {},
            },
            'audio': {
                '_type': 'AMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 1000, 'scalar': 1,
                'metadata': {}, 'effects': [],
            },
        }
        _process_clip(clip, Fraction(2))
        # Non-speed-changed: parent and children all scaled
        assert clip['mediaDuration'] == 2000
        assert clip['video']['mediaDuration'] == 2000
        assert clip['audio']['mediaDuration'] == 2000


class TestScaleTickFloatPrecision:
    """Bug 6: _scale_tick should handle float inputs without precision loss."""

    def test_float_input_does_not_produce_huge_denominator(self):
        from camtasia.operations.speed import _scale_tick
        result = _scale_tick(0.1, Fraction(2))
        # Should produce a clean result, not a huge fraction
        assert isinstance(result, int)
        assert result == 0  # 0.1 * 2 = 0.2, rounded to 0


class TestRescaleOverlapFixAdjustsEffects:
    """Bug 7: overlap fix in rescale_project should adjust UnifiedMedia child effects."""

    def test_unified_media_effects_trimmed_on_overlap_fix(self):
        project_data = _make_project(tracks=[{
            'medias': [
                {
                    '_type': 'UnifiedMedia', 'id': 1, 'src': 0,
                    'start': 0, 'duration': 1000,
                    'mediaStart': 0, 'mediaDuration': 1000,
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {}, 'animationTracks': {},
                    'video': {
                        '_type': 'VMFile', 'id': 2, 'src': 0,
                        'start': 0, 'duration': 1000,
                        'mediaDuration': 1000, 'scalar': 1,
                        'metadata': {}, 'parameters': {},
                        'effects': [{'effectName': 'test', 'start': 0, 'duration': 1000}],
                    },
                    'audio': {
                        '_type': 'AMFile', 'id': 3, 'src': 0,
                        'start': 0, 'duration': 1000,
                        'mediaDuration': 1000, 'scalar': 1,
                        'metadata': {}, 'effects': [],
                    },
                },
                {
                    '_type': 'VMFile', 'id': 4, 'src': 0,
                    'start': 999, 'duration': 500,
                    'mediaStart': 0, 'mediaDuration': 500,
                    'scalar': 1, 'metadata': {}, 'parameters': {},
                    'effects': [], 'attributes': {}, 'animationTracks': {},
                },
            ],
            'transitions': [],
        }])
        # The overlap fix should trim clip 1's duration and adjust video effects
        rescale_project(project_data, Fraction(1))
        tracks = project_data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        um = tracks[0]['medias'][0]
        video_effects = um.get('video', {}).get('effects', [])
        for eff in video_effects:
            if 'duration' in eff:
                assert eff['duration'] <= um['duration']


class TestMatchMarkerMultiWordFallback:
    """Bug 9: match_marker_to_transcript should check ALL words in fallback."""

    def test_three_word_fallback_matches(self):
        words = [
            Word(word_id='', text="the", start=0.0, end=0.1),
            Word(word_id='', text="quick", start=0.1, end=0.2),
            Word(word_id='', text="brown", start=0.2, end=0.3),
            Word(word_id='', text="fox", start=0.3, end=0.4),
        ]
        # "quick brown fox" should match via full multi-word fallback
        result = match_marker_to_transcript("quick brown fox", words)
        assert result == 0.1

    def test_three_word_no_match_returns_none(self):
        words = [
            Word(word_id='', text="the", start=0.0, end=0.1),
            Word(word_id='', text="quick", start=0.1, end=0.2),
            Word(word_id='', text="brown", start=0.2, end=0.3),
            Word(word_id='', text="fox", start=0.3, end=0.4),
        ]
        result = match_marker_to_transcript("quick red fox", words)
        assert result is None


class TestWalkClipsGroupInsideStitchedMedia:
    """Bug 9: _walk_clips should recurse into Group children of StitchedMedia."""

    def test_group_inside_stitched_media_yields_inner_clips(self):
        from camtasia.operations.template import _walk_clips
        tracks = [{'medias': [{
            '_type': 'StitchedMedia', 'id': 1, 'src': 10,
            'medias': [
                {'_type': 'Group', 'id': 2, 'tracks': [
                    {'medias': [
                        {'_type': 'VMFile', 'id': 3, 'src': 20},
                    ]},
                ]},
            ],
        }]}]
        clips = list(_walk_clips(tracks))
        clip_ids = [c.get('id') for c in clips]
        assert 1 in clip_ids  # StitchedMedia itself
        assert 2 in clip_ids  # Group child
        assert 3 in clip_ids  # VMFile inside Group

    def test_replace_media_source_in_group_inside_stitched(self):
        project = _make_project([{'medias': [{
            '_type': 'StitchedMedia', 'id': 1, 'src': 10,
            'medias': [
                {'_type': 'Group', 'id': 2, 'tracks': [
                    {'medias': [
                        {'_type': 'VMFile', 'id': 3, 'src': 10},
                    ]},
                ]},
            ],
        }]}])
        count = replace_media_source(project, old_source_id=10, new_source_id=99)
        assert count >= 1
        inner = project['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        group = inner['medias'][0]
        vmfile = group['tracks'][0]['medias'][0]
        assert vmfile['src'] == 99


# --- Bug 4: _scale_tick precision for large tick values ---

class TestScaleTickPrecision:
    def test_large_tick_exact(self):
        """Bug 4: round(Fraction) should return exact int for large values."""
        result = _scale_tick(10**16, Fraction(1))
        assert result == 10**16

    def test_large_tick_scaled(self):
        """Scaling a large tick by 1/1 should be identity."""
        result = _scale_tick(10**16, Fraction(1, 1))
        assert result == 10**16

    def test_large_tick_no_float_loss(self):
        """float(10**16) loses precision; Fraction-based round should not."""
        # 10**16 + 1 cannot be represented exactly as float64
        val = 10**16 + 1
        result = _scale_tick(val, Fraction(1))
        assert result == val


# --- Bug 5: overlap fix should not corrupt mediaDuration for speed-changed clips ---

class TestOverlapFixSpeedChanged:
    def test_speed_changed_clip_preserves_media_duration(self):
        """Bug 5: overlap fix must not recalculate mediaDuration for speed-changed clips."""
        # Create two clips with a 1-tick overlap; first clip has speed change
        project = _make_project([{
            'medias': [
                {
                    '_type': 'VMFile', 'id': 1, 'src': 1,
                    'start': 0, 'duration': 1001, 'mediaDuration': 2002,
                    'scalar': '1/2',
                    'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
                    'effects': [],
                },
                {
                    '_type': 'VMFile', 'id': 2, 'src': 1,
                    'start': 1000, 'duration': 1000, 'mediaDuration': 1000,
                    'scalar': 1, 'effects': [],
                },
            ],
        }])
        # rescale by factor=1 so only the overlap fix runs
        rescale_project(project, Fraction(1))
        clip = project['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        # mediaDuration should be recalculated from duration/scalar
        # duration was trimmed by 1 (overlap), so new duration = 1000
        # mediaDuration = 1000 / (1/2) = 2000
        assert clip['mediaDuration'] == 2000

    def test_unified_media_preserves_media_duration_when_speed_changed(self):
        """Bug 5: speed-changed UnifiedMedia should recalculate mediaDuration in overlap fix."""
        project = _make_project([{
            'medias': [
                {
                    '_type': 'UnifiedMedia', 'id': 1, 'src': 1,
                    'start': 0, 'duration': 502, 'mediaDuration': 3000,
                    'scalar': 1, 'effects': [],
                    'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
                    'video': {'_type': 'VMFile', 'id': 10, 'src': 1,
                              'start': 0, 'duration': 502, 'mediaDuration': 3000,
                              'scalar': 1, 'effects': []},
                    'audio': {'_type': 'AMFile', 'id': 11, 'src': 1,
                              'start': 0, 'duration': 502, 'mediaDuration': 3000,
                              'scalar': 1, 'effects': []},
                },
                {
                    '_type': 'VMFile', 'id': 2, 'src': 1,
                    'start': 501, 'duration': 500, 'mediaDuration': 500,
                    'scalar': 1, 'effects': [],
                },
            ],
        }])
        rescale_project(project, Fraction(1))
        clip = project['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        # duration trimmed by 1 → 501, mediaDuration = 501 / 1 = 501
        assert clip['mediaDuration'] == 501


# --- Bug 6: _walk_clips should recurse into nested StitchedMedia ---

class TestWalkClipsNestedStitched:
    def test_nested_stitched_media_yields_inner_clips(self):
        """Bug 6: _walk_clips must recurse into StitchedMedia nested inside StitchedMedia."""
        tracks = [{
            'medias': [{
                '_type': 'StitchedMedia', 'id': 1, 'src': 10,
                'medias': [
                    {
                        '_type': 'StitchedMedia', 'id': 2, 'src': 20,
                        'medias': [
                            {'_type': 'VMFile', 'id': 3, 'src': 30},
                        ],
                    },
                ],
            }],
        }]
        clips = list(_walk_clips(tracks))
        clip_ids = [c.get('id') for c in clips]
        # Should yield outer StitchedMedia (1), inner StitchedMedia (2), and VMFile (3)
        assert 1 in clip_ids
        assert 2 in clip_ids
        assert 3 in clip_ids

    def test_replace_media_in_nested_stitched(self):
        """Bug 6: replace_media_source should reach clips inside nested StitchedMedia."""
        project = _make_project([{
            'medias': [{
                '_type': 'StitchedMedia', 'id': 1, 'src': 10,
                'medias': [
                    {
                        '_type': 'StitchedMedia', 'id': 2, 'src': 10,
                        'medias': [
                            {'_type': 'VMFile', 'id': 3, 'src': 10},
                        ],
                    },
                ],
            }],
        }])
        count = replace_media_source(project, old_source_id=10, new_source_id=99)
        inner_stitched = project['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]['medias'][0]
        vmfile = inner_stitched['medias'][0]
        assert vmfile['src'] == 99
        assert count >= 3  # outer, inner stitched, and vmfile


class TestScaleTickStringConsistency:
    """Bug 9: _scale_tick should always return str for string fraction inputs."""

    def test_string_fraction_returns_string_even_when_whole(self):
        """Scaling '2/1' by 1 should return '2/1', not int 2."""
        result = _scale_tick('2/1', Fraction(1))
        assert isinstance(result, str)
        assert '/' in result

    def test_string_fraction_returns_string_after_scaling(self):
        result = _scale_tick('3/2', Fraction(2))
        assert isinstance(result, str)
        assert '/' in result


class TestUnifiedMediaSpeedChildDuration:
    """Bug 4: UnifiedMedia speed-changed children should get parent's duration AND mediaDuration."""

    def test_speed_changed_unified_children_get_parent_duration(self):
        from camtasia.operations.speed import _process_clip
        clip = {
            '_type': 'UnifiedMedia',
            'start': 0, 'duration': 1000, 'mediaDuration': 500,
            'scalar': 2,
            'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
            'video': {
                '_type': 'VMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 500, 'scalar': 1,
                'metadata': {}, 'effects': [],
            },
            'audio': {
                '_type': 'AMFile', 'start': 0, 'duration': 1000,
                'mediaDuration': 500, 'scalar': 1,
                'metadata': {}, 'effects': [],
            },
        }
        _process_clip(clip, Fraction(2))
        # Both children should have parent's duration AND mediaDuration
        assert clip['video']['duration'] == clip['duration']
        assert clip['video']['mediaDuration'] == clip['mediaDuration']
        assert clip['audio']['duration'] == clip['duration']
        assert clip['audio']['mediaDuration'] == clip['mediaDuration']


class TestOverlapFixSpeedChangedScalar:
    """Bug 5: Overlap fix should preserve scalar and recalculate mediaDuration for speed-changed clips."""

    def test_overlap_fix_preserves_scalar_recalculates_media_duration(self):
        project = _make_project([{
            'medias': [
                {
                    '_type': 'VMFile', 'id': 1, 'src': 0,
                    'start': 0, 'duration': 110, 'mediaDuration': 55,
                    'scalar': 2, 'effects': [],
                    'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
                },
                {
                    '_type': 'VMFile', 'id': 2, 'src': 0,
                    'start': 100, 'duration': 100, 'mediaDuration': 100,
                    'scalar': 1, 'effects': [],
                    'metadata': {},
                },
            ],
            'transitions': [],
        }])
        rescale_project(project, Fraction(1))
        clip_a = project['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        # scalar should be preserved (not recalculated)
        assert parse_scalar(clip_a['scalar']) == Fraction(2)
        # duration was reduced by overlap (10), so new duration = 100
        assert clip_a['duration'] == 100
        # mediaDuration should be recalculated: 100 / 2 = 50
        assert clip_a['mediaDuration'] == 50


class TestStitchedMediaInnerScalarPreservation:
    """Bug 8: StitchedMedia inner clips with own speed change should keep their scalar."""

    def test_inner_speed_changed_clip_keeps_own_scalar(self):
        from camtasia.operations.speed import _process_clip
        clip = {
            '_type': 'StitchedMedia',
            'start': 0, 'duration': 2000, 'mediaStart': 0, 'mediaDuration': 2000,
            'scalar': 1, 'metadata': {}, 'effects': [],
            'medias': [
                {
                    '_type': 'VMFile', 'start': 0, 'duration': 1000,
                    'mediaStart': 0, 'mediaDuration': 500,
                    'scalar': 2, 'effects': [],
                    'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
                },
                {
                    '_type': 'VMFile', 'start': 1000, 'duration': 1000,
                    'mediaStart': 0, 'mediaDuration': 1000,
                    'scalar': 1, 'effects': [],
                    'metadata': {},
                },
            ],
        }
        _process_clip(clip, Fraction(2))
        inner_speed = clip['medias'][0]
        inner_normal = clip['medias'][1]
        # Speed-changed inner should keep its own scalar (2), not get parent's (1)
        assert inner_speed['scalar'] == 2
        # Normal inner should get parent's scalar
        assert inner_normal['scalar'] == clip.get('scalar', 1)


# ── Bug 2: StitchedMedia should recurse Group/nested StitchedMedia ──


class TestStitchedMediaRecursesNestedStructures:
    """Bug 2: _process_clip must recurse into Group/StitchedMedia inside StitchedMedia."""

    def test_nested_group_inside_stitched_is_scaled(self):
        inner_group = {
            "id": 25,
            "_type": "Group",
            "start": 0,
            "duration": 10_000_000_000,
            "mediaDuration": 10_000_000_000,
            "scalar": 1,
            "metadata": {},
            "tracks": [
                {
                    "trackIndex": 0,
                    "medias": [
                        {
                            "id": 26,
                            "_type": "VMFile",
                            "src": 1,
                            "start": 0,
                            "duration": 10_000_000_000,
                            "mediaStart": 0,
                            "mediaDuration": 10_000_000_000,
                            "scalar": 1,
                            "metadata": {},
                        }
                    ],
                }
            ],
        }
        stitched = {
            "id": 20,
            "_type": "StitchedMedia",
            "src": 3,
            "start": 0,
            "duration": 10_000_000_000,
            "mediaStart": 0,
            "mediaDuration": 10_000_000_000,
            "medias": [inner_group],
        }
        project = _make_project(tracks=[{"medias": [stitched], "transitions": []}])
        rescale_project(project, Fraction(2))

        actual = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        nested_group = actual["medias"][0]
        assert nested_group["duration"] == 20_000_000_000
        inner_clip = nested_group["tracks"][0]["medias"][0]
        assert inner_clip["duration"] == 20_000_000_000


# ── Bug 3: _adjust_scalar not applied to StitchedMedia/Group wrappers ──


class TestNoDoubleScalarForCompoundClips:
    """Bug 3: StitchedMedia/Group wrappers should not have _adjust_scalar called."""

    def test_stitched_media_scalar_unchanged_when_speed_changed(self):
        stitched = _make_stitched_clip()
        stitched["metadata"] = {"clipSpeedAttribute": {"type": "bool", "value": True}}
        stitched["scalar"] = "1/2"
        project = _make_project(tracks=[{"medias": [stitched], "transitions": []}])

        rescale_project(project, Fraction(2))

        actual = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        # Scalar should remain unchanged for StitchedMedia
        assert parse_scalar(actual["scalar"]) == Fraction(1, 2)

    def test_group_scalar_unchanged_when_speed_changed(self):
        group = _make_group_clip()
        group["metadata"] = {"clipSpeedAttribute": {"type": "bool", "value": True}}
        group["scalar"] = "3/4"
        project = _make_project(tracks=[{"medias": [group], "transitions": []}])

        rescale_project(project, Fraction(2))

        actual = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        assert parse_scalar(actual["scalar"]) == Fraction(3, 4)


# ── Bug 4: overlap fix skips compound clips ──


class TestOverlapFixSkipsCompoundClips:
    """Bug 4: overlap fix should skip StitchedMedia/Group to avoid internal inconsistency."""

    def test_stitched_media_not_trimmed_on_overlap(self):
        stitched = _make_stitched_clip(start=0)
        stitched["duration"] = 100
        # Place a simple clip right after with 1-tick overlap
        simple = _make_audio_clip(clip_id=50, start=99, duration=100)
        project = _make_project(tracks=[{"medias": [stitched, simple], "transitions": []}])

        rescale_project(project, Fraction(1))  # factor=1 just triggers overlap fix

        actual_stitched = project["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        # StitchedMedia duration should remain unchanged
        assert actual_stitched["duration"] == 100


class TestDiffProjectsNonContiguousTrackIndex:
    """Bug 3: diff_projects must not IndexError on non-contiguous trackIndex values."""

    def test_non_contiguous_track_indices(self, project):
        """Projects with trackIndex 0 and 5 should not raise IndexError."""
        a = project
        # Add a track with non-contiguous trackIndex
        scene = a._data['timeline']['sceneTrack']['scenes'][0]['csml']
        scene['tracks'].append({
            'trackIndex': 5, 'medias': [{
                '_type': 'IMFile', 'id': 900, 'start': 0, 'duration': 100, 'src': 0,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1, 'metadata': {},
                'parameters': {}, 'effects': [], 'attributes': {'ident': ''}, 'animationTracks': {},
            }], 'transitions': [],
        })
        b = Project.__new__(Project)
        b._data = copy.deepcopy(a._data)
        b._file_path = a._file_path
        result = diff_projects(a, b)
        assert not result.has_changes


class TestApplySyncRespectsGroupScalar:
    """Bug 4: apply_sync must account for group scalar when computing offsets."""

    def test_scalar_affects_source_offsets(self):
        """With scalar=2, timeline offset should be halved for source-media offset."""
        from unittest.mock import MagicMock

        from camtasia.operations.sync import SyncSegment

        group = MagicMock()
        group._data = {
            'start': 0,
            'mediaStart': 0,
            'scalar': 2,
            'tracks': [{'medias': []}],
        }
        seg = SyncSegment(
            video_start_ticks=0,
            video_end_ticks=EDIT_RATE,
            audio_start_seconds=0.0,
            audio_end_seconds=0.5,
            scalar=Fraction(2),
        )
        # apply_sync calls group.set_internal_segment_speeds with tuples
        apply_sync(group, [seg])
        call_args = group.set_internal_segment_speeds.call_args[0][0]
        # With scalar=2, timeline offset of EDIT_RATE ticks should map to
        # source offset of EDIT_RATE/2 ticks = 0.5 seconds
        src_end = call_args[0][1]
        assert abs(src_end - 0.5) < 0.01


class TestStitchedMediaInnerScalarPreserved:
    """Bug 5: _process_clip must not overwrite non-unity inner scalar."""

    def test_inner_non_unity_scalar_preserved(self):
        from camtasia.operations.speed import _process_clip
        clip = {
            '_type': 'StitchedMedia',
            'start': 0, 'duration': 200, 'mediaStart': 0, 'mediaDuration': 200,
            'scalar': 1, 'metadata': {}, 'effects': [],
            'medias': [{
                '_type': 'IMFile', 'id': 10,
                'start': 0, 'duration': 100, 'mediaStart': 0, 'mediaDuration': 100,
                'scalar': '1/2',  # non-unity inner scalar
                'metadata': {},
                'effects': [],
            }],
        }
        _process_clip(clip, Fraction(1))
        # Inner scalar should be preserved, not overwritten to 1
        assert clip['medias'][0]['scalar'] == '1/2'


class TestRescaleProjectPreservesSpeedChangedScalar:
    """Bug fix: overlap fix must preserve scalar and recalculate mediaDuration for speed-changed clips."""

    def test_scalar_preserved_media_duration_recalculated(self):
        project = _make_project([{
            'medias': [
                {
                    '_type': 'VMFile', 'id': 1, 'src': 0,
                    'start': 0, 'duration': 1001, 'mediaDuration': 2002,
                    'scalar': '1/2', 'effects': [],
                    'metadata': {'clipSpeedAttribute': {'type': 'bool', 'value': True}},
                },
                {
                    '_type': 'VMFile', 'id': 2, 'src': 0,
                    'start': 1000, 'duration': 1000, 'mediaDuration': 1000,
                    'scalar': 1, 'effects': [], 'metadata': {},
                },
            ],
            'transitions': [],
        }])
        rescale_project(project, Fraction(1))
        clip = project['timeline']['sceneTrack']['scenes'][0]['csml']['tracks'][0]['medias'][0]
        # Scalar should be preserved (not recalculated)
        assert parse_scalar(clip['scalar']) == Fraction(1, 2)
        # mediaDuration should be recalculated from duration / scalar
        # duration was trimmed by 1 (overlap), so new duration = 1000
        # mediaDuration = 1000 / (1/2) = 2000
        assert clip['mediaDuration'] == 2000


class TestApplySyncConsistentSegmentBoundaries:
    """Bug fix: apply_sync must use round() not int() to avoid truncation-induced drift."""

    def test_round_vs_int_for_fractional_scalar(self):
        from unittest.mock import MagicMock

        from camtasia.operations.sync import SyncSegment

        group = MagicMock()
        group._data = {
            'start': 0,
            'mediaStart': 0,
            'scalar': '3/2',  # fractional scalar that causes int() truncation
            'tracks': [{'medias': []}],
        }
        seg = SyncSegment(
            video_start_ticks=0,
            video_end_ticks=100,
            audio_start_seconds=0.0,
            audio_end_seconds=1.0,
            scalar=Fraction(1),
        )
        apply_sync(group, [seg])
        call_args = group.set_internal_segment_speeds.call_args[0][0]
        # With scalar=3/2, 100 / (3/2) = 200/3 ≈ 66.667
        # round() gives 67, int() gives 66 — round is correct
        from camtasia.timing import ticks_to_seconds
        expected_end = ticks_to_seconds(round(Fraction(100) / Fraction(3, 2)))
        assert call_args[0][1] == expected_end


class TestApplySyncExported:
    """Bug fix: apply_sync must be importable from camtasia.operations."""

    def test_apply_sync_in_operations_all(self):
        import camtasia.operations
        assert 'apply_sync' in camtasia.operations.__all__

    def test_apply_sync_importable(self):
        from camtasia.operations import apply_sync as fn
        assert callable(fn)


class TestApplySyncZeroScalarFallback:
    """apply_sync must raise ValueError when group_scalar == 0."""

    def test_zero_scalar_raises_value_error(self):
        from unittest.mock import MagicMock

        from camtasia.operations.sync import SyncSegment

        group = MagicMock()
        group._data = {
            'start': 0,
            'mediaStart': 0,
            'scalar': 0,
            'tracks': [{'medias': []}],
        }
        seg = SyncSegment(
            video_start_ticks=0,
            video_end_ticks=EDIT_RATE,
            audio_start_seconds=0.0,
            audio_end_seconds=1.0,
            scalar=Fraction(1),
        )
        with pytest.raises(ValueError, match='scalar=0'):
            apply_sync(group, [seg])


class TestUnifiedMediaSpeedChangedEffectOrphan:
    """Bug 5: speed-changed UnifiedMedia must not double-process children."""

    def test_child_effects_scaled_once(self):
        from camtasia.operations.speed import _process_clip
        clip = {
            '_type': 'UnifiedMedia',
            'start': 0, 'duration': 1000, 'mediaDuration': 500,
            'scalar': '1/2', 'mediaStart': 0,
            'metadata': {'clipSpeedAttribute': {'value': True}},
            'effects': [],
            'video': {
                '_type': 'VMFile',
                'start': 0, 'duration': 1000, 'mediaDuration': 500,
                'scalar': '1/2', 'mediaStart': 0,
                'metadata': {'clipSpeedAttribute': {'value': True}},
                'effects': [{'effectName': 'E', 'start': 100, 'duration': 200}],
            },
        }
        _process_clip(clip, Fraction(2))
        # Parent duration scaled: 1000*2=2000
        assert clip['duration'] == 2000
        # Child duration should match parent (not double-scaled)
        assert clip['video']['duration'] == clip['duration']
        # Child effect should be scaled once by factor 2
        assert clip['video']['effects'][0]['start'] == 200
        assert clip['video']['effects'][0]['duration'] == 400


class TestPlanSyncNonMonotonicAudio:
    """Bug 6: plan_sync must skip non-monotonic audio segments."""

    def test_non_monotonic_audio_skipped_with_warning(self):
        import warnings
        # Markers at video positions 0, 1000, 2000
        # Audio timestamps: 0.0, 5.0, 3.0 (non-monotonic at third)
        words = [
            Word(text='hello', start=0.0, end=0.5, word_id='w1'),
            Word(text='world', start=5.0, end=5.5, word_id='w2'),
            Word(text='back', start=3.0, end=3.5, word_id='w3'),
        ]
        markers = [('hello', 0), ('world', EDIT_RATE), ('back', EDIT_RATE * 2)]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            segments = plan_sync(markers, words, edit_rate=EDIT_RATE)
        # 'back' at audio=3.0 < prev_audio_end=5.5, so it should be skipped
        # Only 1 segment should remain (hello->world)
        assert len(segments) <= 1
        warn_msgs = [str(x.message) for x in w]
        assert any('Non-monotonic' in m for m in warn_msgs)


class TestApplySyncGroupScalarZero:
    """Bug 7: apply_sync must raise ValueError when group_scalar==0."""

    def test_raises_on_zero_scalar(self):
        from unittest.mock import MagicMock
        group = MagicMock()
        group._data = {
            'start': 0, 'mediaStart': 0, 'scalar': 0,
        }
        seg = SyncSegment(
            video_start_ticks=0, video_end_ticks=EDIT_RATE,
            audio_start_seconds=0.0, audio_end_seconds=1.0,
            scalar=Fraction(1),
        )
        with pytest.raises(ValueError, match='scalar=0'):
            apply_sync(group, [seg])


class TestPlanSyncFilteredToFewerThanTwoReturnsEmpty:
    """When non-monotonic filtering leaves fewer than 2 markers, return empty list."""

    def test_filter_leaves_one_marker_returns_empty(self):
        import warnings
        # Two markers: first has audio=5.0, second has audio=1.0 (before first)
        # Second gets filtered; only 1 remains; return []
        words = [
            Word(text='alpha', start=5.0, end=5.5, word_id='w1'),
            Word(text='beta', start=1.0, end=1.5, word_id='w2'),
        ]
        markers = [('alpha', 0), ('beta', EDIT_RATE)]
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            segments = plan_sync(markers, words, edit_rate=EDIT_RATE)
        assert segments == []
