"""Tests for Project.apply_template_effects() and Project.strip_all_effects()."""

from __future__ import annotations

import pytest
from pathlib import Path

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'


@pytest.fixture
def project_with_clips():
    """Load the new.cmproj template and add a video + image clip."""
    from camtasia.project import load_project

    proj = load_project(RESOURCES / 'new.cmproj')
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
        proj = load_project(RESOURCES / 'new.cmproj')
        count = proj.apply_template_effects({'VMFile': ['add_drop_shadow']})
        assert count == 0


class TestStripAllEffects:
    def test_strips_effects_returns_count(self, project_with_clips):
        proj = project_with_clips
        # First apply some effects
        proj.apply_template_effects({'VMFile': ['add_drop_shadow'], 'IMFile': ['add_drop_shadow']})
        assert proj.total_effect_count > 0
        removed = proj.strip_all_effects()
        assert removed > 0
        assert proj.total_effect_count == 0

    def test_strips_zero_on_no_effects(self, project_with_clips):
        proj = project_with_clips
        removed = proj.strip_all_effects()
        assert removed == 0

    def test_strips_empty_project(self):
        from camtasia.project import load_project
        proj = load_project(RESOURCES / 'new.cmproj')
        assert proj.strip_all_effects() == 0

    def test_roundtrip_apply_then_strip(self, project_with_clips):
        proj = project_with_clips
        proj.apply_template_effects({
            'VMFile': ['add_drop_shadow', 'add_round_corners'],
            'IMFile': ['add_drop_shadow'],
        })
        applied_count = proj.total_effect_count
        assert applied_count >= 3
        removed = proj.strip_all_effects()
        assert removed == applied_count
        assert proj.total_effect_count == 0
