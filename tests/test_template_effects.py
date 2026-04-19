"""Tests for Project.apply_template_effects() and Project.remove_all_effects()."""

from __future__ import annotations

import pytest
from pathlib import Path

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'



# Module-level list to prevent TemporaryDirectory from being GC'd during test
_TEMP_DIRS: list = []

def _isolated_project():
    """Load template into an isolated temp copy (safe for parallel execution)."""
    import shutil, tempfile
    from camtasia.project import load_project
    td = tempfile.TemporaryDirectory()
    _TEMP_DIRS.append(td)  # prevent premature GC
    dst = Path(td.name) / 'test.cmproj'
    shutil.copytree(RESOURCES / 'new.cmproj', dst)
    return load_project(dst)

@pytest.fixture
def project_with_clips():
    """Load the new.cmproj template and add a video + image clip."""
    from camtasia.project import load_project

    proj = _isolated_project()
    track = proj.timeline.get_or_create_track('TestTrack')
    # Add a source bin entry for a fake video
    proj._data.setdefault('sourceBin', []).append({
        'id': 900,
        'src': './media/fake.mp4',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'loudnessNormalization': True,
        'sourceTracks': [{
            'range': [0, 300],
            'type': 0,
            'editRate': 30,
            'trackRect': [0, 0, 1920, 1080],
            'sampleRate': 44100,
            'bitDepth': 16,
            'numChannels': 2,
            'integratedLUFS': 100.0,
            'peakLevel': -1.0,
        }],
    })
    proj._data['sourceBin'].append({
        'id': 901,
        'src': './media/fake.png',
        'rect': [0, 0, 1920, 1080],
        'lastMod': '20260101T000000',
        'loudnessNormalization': True,
        'sourceTracks': [{
            'range': [0, 300],
            'type': 2,
            'editRate': 30,
            'trackRect': [0, 0, 1920, 1080],
            'sampleRate': 44100,
            'bitDepth': 16,
            'numChannels': 0,
            'integratedLUFS': 100.0,
            'peakLevel': -1.0,
        }],
    })
    track.add_clip('VMFile', 900, 0, 705600000)
    track.add_clip('IMFile', 901, 705600000, 705600000)
    return proj


class TestApplyTemplateEffects:
    def test_applies_matching_effects(self, project_with_clips):
        proj = project_with_clips
        config = {'VMFile': ['add_drop_shadow'], 'IMFile': ['add_drop_shadow']}
        count = proj.apply_template_effects(config)
        assert count == 2

    def test_applies_multiple_effects_per_type(self, project_with_clips):
        proj = project_with_clips
        config = {'VMFile': ['add_drop_shadow', 'add_round_corners']}
        count = proj.apply_template_effects(config)
        assert count == 2

    def test_skips_unmatched_clip_types(self, project_with_clips):
        proj = project_with_clips
        config = {'AMFile': ['add_drop_shadow']}
        count = proj.apply_template_effects(config)
        assert count == 0

    def test_skips_missing_methods(self, project_with_clips):
        proj = project_with_clips
        config = {'VMFile': ['nonexistent_method']}
        count = proj.apply_template_effects(config)
        assert count == 0

    def test_empty_config(self, project_with_clips):
        proj = project_with_clips
        count = proj.apply_template_effects({})
        assert count == 0

    def test_empty_project(self):
        from camtasia.project import load_project
        proj = _isolated_project()
        count = proj.apply_template_effects({'VMFile': ['add_drop_shadow']})
        assert count == 0


class TestStripAllEffects:
    def test_strips_effects_returns_count(self, project_with_clips):
        proj = project_with_clips
        # First apply some effects
        proj.apply_template_effects({'VMFile': ['add_drop_shadow'], 'IMFile': ['add_drop_shadow']})
        assert proj.total_effect_count > 0
        removed = proj.remove_all_effects()
        assert removed > 0
        assert proj.total_effect_count == 0

    def test_strips_zero_on_no_effects(self, project_with_clips):
        proj = project_with_clips
        removed = proj.remove_all_effects()
        assert removed == 0

    def test_strips_empty_project(self):
        from camtasia.project import load_project
        proj = _isolated_project()
        assert proj.remove_all_effects() == 0

    def test_roundtrip_apply_then_strip(self, project_with_clips):
        proj = project_with_clips
        proj.apply_template_effects({
            'VMFile': ['add_drop_shadow', 'add_round_corners'],
            'IMFile': ['add_drop_shadow'],
        })
        applied_count = proj.total_effect_count
        assert applied_count >= 3
        removed = proj.remove_all_effects()
        assert removed == applied_count
        assert proj.total_effect_count == 0


class TestApplyColorGrade:
    def test_applies_to_video_clips(self, project):
        track = project.timeline.add_track('Video')
        track.add_clip('VMFile', 1, 0, 705600000)
        count = project.apply_color_grade(brightness=0.1)
        assert count == 1

    def test_skips_audio_clips(self, project):
        track = project.timeline.add_track('Audio')
        track.add_audio(1, start_seconds=0, duration_seconds=1)
        count = project.apply_color_grade()
        assert count == 0

    def test_empty_project(self, project):
        assert project.apply_color_grade() == 0


# ── from test_coverage_phase4b: operations/template.py tests ──

from camtasia.operations.template import _walk_clips


class TestWalkClipsEdgeCases:
    def test_unified_media_inside_stitched_media(self):
        tracks = [{
            "medias": [{
                "_type": "StitchedMedia",
                "medias": [{
                    "_type": "UnifiedMedia",
                    "video": {"_type": "VMFile", "src": 1},
                    "audio": {"_type": "AMFile", "src": 2},
                }],
            }],
        }]
        clips = list(_walk_clips(tracks))
        types = [c.get("_type") for c in clips]
        assert "StitchedMedia" in types
        assert "UnifiedMedia" in types
        assert "VMFile" in types
        assert "AMFile" in types

    def test_top_level_unified_media(self):
        tracks = [{
            "medias": [{
                "_type": "UnifiedMedia",
                "video": {"_type": "VMFile", "src": 1},
                "audio": {"_type": "AMFile", "src": 2},
            }],
        }]
        clips = list(_walk_clips(tracks))
        types = [c.get("_type") for c in clips]
        assert "UnifiedMedia" in types
        assert "VMFile" in types
        assert "AMFile" in types

    def test_duplicate_project_clear_media_with_keyframes(self, tmp_path):
        import shutil
        from camtasia.operations.template import duplicate_project
        from camtasia.project import load_project

        src = Path(__file__).parent.parent / "src" / "camtasia" / "resources" / "new.cmproj"
        src_copy = tmp_path / "source.cmproj"
        shutil.copytree(src, src_copy)

        proj = load_project(src_copy)
        toc = proj._data.setdefault("timeline", {}).setdefault("parameters", {}).setdefault("toc", {})
        toc["keyframes"] = [{"time": 100, "value": "Chapter 1"}]
        proj.save()

        dest = tmp_path / "dest.cmproj"
        result = duplicate_project(src_copy, dest, clear_media=True)
        result_toc = result._data.get("timeline", {}).get("parameters", {}).get("toc", {})
        assert result_toc.get("keyframes") == []
