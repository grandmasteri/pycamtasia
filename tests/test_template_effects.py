"""Tests for Project.apply_template_effects() and Project.remove_all_effects()."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from camtasia.operations.template import _walk_clips, duplicate_project
from camtasia.project import load_project

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


@pytest.fixture
def project_with_clips(project):
    """Load the new.cmproj template and add a video + image clip."""
    track = project.timeline.get_or_create_track('TestTrack')
    project._data.setdefault('sourceBin', []).append({
        'id': 900,
        'src': './media/fake.mp4',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'loudnessNormalization': True,
        'sourceTracks': [{
            'range': [0, 300], 'type': 0, 'editRate': 30,
            'trackRect': [0, 0, 1920, 1080], 'sampleRate': 44100,
            'bitDepth': 16, 'numChannels': 2,
            'integratedLUFS': 100.0, 'peakLevel': -1.0,
        }],
    })
    project._data['sourceBin'].append({
        'id': 901,
        'src': './media/fake.png',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'loudnessNormalization': True,
        'sourceTracks': [{
            'range': [0, 300], 'type': 2, 'editRate': 30,
            'trackRect': [0, 0, 1920, 1080], 'sampleRate': 44100,
            'bitDepth': 16, 'numChannels': 0,
            'integratedLUFS': 100.0, 'peakLevel': -1.0,
        }],
    })
    track.add_clip('VMFile', 900, 0, 705600000)
    track.add_clip('IMFile', 901, 705600000, 705600000)
    return project


class TestApplyTemplateEffects:
    def test_applies_matching_effects(self, project_with_clips):
        config = {'VMFile': ['add_drop_shadow'], 'IMFile': ['add_drop_shadow']}
        assert project_with_clips.apply_template_effects(config) == 2

    def test_applies_multiple_effects_per_type(self, project_with_clips):
        config = {'VMFile': ['add_drop_shadow', 'add_round_corners']}
        assert project_with_clips.apply_template_effects(config) == 2

    def test_skips_unmatched_clip_types(self, project_with_clips):
        assert project_with_clips.apply_template_effects({'AMFile': ['add_drop_shadow']}) == 0

    def test_skips_missing_methods(self, project_with_clips):
        assert project_with_clips.apply_template_effects({'VMFile': ['nonexistent_method']}) == 0

    def test_empty_config(self, project_with_clips):
        assert project_with_clips.apply_template_effects({}) == 0

    def test_empty_project(self, project):
        assert project.apply_template_effects({'VMFile': ['add_drop_shadow']}) == 0


class TestStripAllEffects:
    def test_strips_effects_returns_count(self, project_with_clips):
        project_with_clips.apply_template_effects(
            {'VMFile': ['add_drop_shadow'], 'IMFile': ['add_drop_shadow']})
        assert project_with_clips.total_effect_count == 2
        assert project_with_clips.remove_all_effects() == 2
        assert project_with_clips.total_effect_count == 0

    def test_strips_zero_on_no_effects(self, project_with_clips):
        assert project_with_clips.remove_all_effects() == 0

    def test_strips_empty_project(self, project):
        assert project.remove_all_effects() == 0

    def test_roundtrip_apply_then_strip(self, project_with_clips):
        project_with_clips.apply_template_effects({
            'VMFile': ['add_drop_shadow', 'add_round_corners'],
            'IMFile': ['add_drop_shadow'],
        })
        assert project_with_clips.total_effect_count == 3
        assert project_with_clips.remove_all_effects() == 3
        assert project_with_clips.total_effect_count == 0


class TestApplyColorGrade:
    def test_applies_to_video_clips(self, project):
        track = project.timeline.add_track('Video')
        track.add_clip('VMFile', 1, 0, 705600000)
        assert project.apply_color_grade(brightness=0.1) == 1

    def test_skips_audio_clips(self, project):
        track = project.timeline.add_track('Audio')
        track.add_audio(1, start_seconds=0, duration_seconds=1)
        assert project.apply_color_grade() == 0

    def test_empty_project(self, project):
        assert project.apply_color_grade() == 0


class TestWalkClipsEdgeCases:
    def test_unified_media_inside_stitched_media(self):
        tracks = [{"medias": [{"_type": "StitchedMedia", "medias": [{
            "_type": "UnifiedMedia",
            "video": {"_type": "VMFile", "src": 1},
            "audio": {"_type": "AMFile", "src": 2},
        }]}]}]
        types = {c.get("_type") for c in _walk_clips(tracks)}
        assert types >= {"StitchedMedia", "UnifiedMedia", "VMFile", "AMFile"}

    def test_top_level_unified_media(self):
        tracks = [{"medias": [{
            "_type": "UnifiedMedia",
            "video": {"_type": "VMFile", "src": 1},
            "audio": {"_type": "AMFile", "src": 2},
        }]}]
        types = {c.get("_type") for c in _walk_clips(tracks)}
        assert types >= {"UnifiedMedia", "VMFile", "AMFile"}

    def test_duplicate_project_clear_media_with_keyframes(self, tmp_path):
        src = RESOURCES / "new.cmproj"
        src_copy = tmp_path / "source.cmproj"
        shutil.copytree(src, src_copy)

        proj = load_project(src_copy)
        toc = proj._data.setdefault("timeline", {}).setdefault(
            "parameters", {}).setdefault("toc", {})
        toc["keyframes"] = [{"time": 100, "value": "Chapter 1"}]
        proj.save()

        dest = tmp_path / "dest.cmproj"
        result = duplicate_project(src_copy, dest, clear_media=True)
        result_toc = result._data.get("timeline", {}).get(
            "parameters", {}).get("toc", {})
        assert result_toc.get("keyframes") == []
