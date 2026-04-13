from __future__ import annotations
import json
from pathlib import Path
import pytest
from camtasia.timeline.clips import clip_from_dict
from camtasia.validation import (
    _check_duplicate_clip_ids,
    _check_track_indices,
    _check_transition_references,
)

FIXTURES = Path(__file__).parent / 'fixtures'
SAMPLE = FIXTURES / 'techsmith_sample.tscproj'


@pytest.fixture
def sample_data():
    return json.loads(SAMPLE.read_text())


class TestTechSmithSampleStructure:
    def test_project_version(self, sample_data):
        assert sample_data.get('version') == '8.0'

    def test_canvas_dimensions(self, sample_data):
        assert sample_data.get('width') == 1920
        assert sample_data.get('height') == 1080

    def test_edit_rate(self, sample_data):
        assert sample_data.get('editRate') == 705600000

    def test_track_count(self, sample_data):
        tracks = sample_data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        assert len(tracks) == 5


class TestTechSmithSampleClips:
    def test_all_clips_load(self, sample_data):
        """Every clip in the TechSmith sample loads without error."""
        tracks = sample_data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        clip_count = 0
        def _check(medias):
            nonlocal clip_count
            for m in medias:
                clip = clip_from_dict(m)
                assert clip.id is not None
                clip_count += 1
                for t in m.get('tracks', []):
                    _check(t.get('medias', []))
        for track in tracks:
            _check(track.get('medias', []))
        assert clip_count > 50  # The sample has ~77 clips

    def test_clip_types_found(self, sample_data):
        """Expected clip types are present."""
        tracks = sample_data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        types = set()
        def _collect(medias):
            for m in medias:
                types.add(m.get('_type'))
                for t in m.get('tracks', []):
                    _collect(t.get('medias', []))
        for track in tracks:
            _collect(track.get('medias', []))
        assert 'Callout' in types
        assert 'Group' in types
        assert 'VMFile' in types


class TestTechSmithSampleValidation:
    def test_no_duplicate_ids(self, sample_data):
        assert _check_duplicate_clip_ids(sample_data) == []

    def test_track_indices_consistent(self, sample_data):
        assert _check_track_indices(sample_data) == []

    def test_no_stale_transitions(self, sample_data):
        assert _check_transition_references(sample_data) == []


class TestTechSmithLibraryAsset:
    @pytest.fixture
    def asset_data(self):
        path = FIXTURES / 'techsmith_library_asset.tscproj'
        if not path.exists():
            pytest.skip('TechSmith library asset not available')
        return json.loads(path.read_text())

    def test_all_clips_load(self, asset_data):
        tracks = asset_data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        clip_count = 0
        def _check(medias):
            nonlocal clip_count
            for m in medias:
                clip = clip_from_dict(m)
                assert clip.id is not None
                clip_count += 1
                for t in m.get('tracks', []):
                    _check(t.get('medias', []))
        for track in tracks:
            _check(track.get('medias', []))
        assert clip_count > 10

    def test_has_media_matte_effect(self, asset_data):
        tracks = asset_data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']
        def _has_effect(medias, name):
            for m in medias:
                for e in m.get('effects', []):
                    if e.get('effectName') == name:
                        return True
                for t in m.get('tracks', []):
                    if _has_effect(t.get('medias', []), name):
                        return True
            return False
        found = any(_has_effect(t.get('medias', []), 'MediaMatte') for t in tracks)
        assert found