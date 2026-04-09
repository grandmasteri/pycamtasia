from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from camtasia.operations.speed import rescale_project, set_audio_speed
from camtasia.operations.sync import SyncSegment, match_marker_to_transcript, plan_sync
from camtasia.operations.template import clone_project_structure, replace_media_source
from camtasia.timing import EDIT_RATE, parse_scalar


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
        # old scalar = 51/101, new = old / factor = 51/202
        expected_scalar = Fraction(51, 101) / Fraction(2)
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
        {"word": "selecting", "start": 0.75, "end": 1.0},
        {"word": "a", "start": 1.0, "end": 1.1},
        {"word": "recent", "start": 1.25, "end": 1.5},
        {"word": "batch", "start": 1.5, "end": 1.75},
        {"word": "run", "start": 1.75, "end": 2.0},
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
            {"word": "selecting", "start": 0.0, "end": 0.25},
            {"word": "a", "start": 0.25, "end": 0.3},
            {"word": "recent", "start": 0.3, "end": 0.5},
            {"word": "batch", "start": 0.5, "end": 0.75},
            {"word": "run", "start": 0.75, "end": 1.0},
            {"word": "navigating", "start": 1.0, "end": 1.25},
            {"word": "to", "start": 1.25, "end": 1.3},
            {"word": "the", "start": 1.3, "end": 1.4},
            {"word": "dashboard", "start": 1.4, "end": 1.75},
        ]

        actual_result = plan_sync(markers, words)

        assert actual_result[0].video_start_ticks == 0
        assert actual_result[0].video_end_ticks == 705_600_000
        assert actual_result[0].audio_start_seconds == 0.0
        assert actual_result[0].audio_end_seconds == 1.0

    def test_fewer_than_two_markers_returns_empty(self):
        assert plan_sync([("only one", 0)], [{"word": "only", "start": 0.0, "end": 0.5}]) == []

    def test_no_transcript_match_returns_empty(self):
        markers = [("aaa", 0), ("bbb", 705_600_000)]
        words = [{"word": "zzz", "start": 0.0, "end": 1.0}]
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
