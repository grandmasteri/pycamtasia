from __future__ import annotations
import json
import pytest
from pathlib import Path
from camtasia.timeline.clips import clip_from_dict
from camtasia.validation import (
    _check_duplicate_clip_ids,
    _check_track_indices,
    _check_transition_references,
)

FIXTURES = Path(__file__).parent / 'fixtures'


@pytest.mark.parametrize('fixture', [
    'test_project_a.tscproj',
    'test_project_b.tscproj',
    'test_project_c.tscproj',
    'test_project_d.tscproj',
])
class TestFixtureValidation:
    def test_loads_without_error(self, fixture):
        """Fixture JSON loads and all clips parse."""
        data = json.loads((FIXTURES / fixture).read_text())
        tracks = data.get('timeline', {}).get('sceneTrack', {}).get('scenes', [{}])[0].get('csml', {}).get('tracks', [])
        for track in tracks:
            for media in track.get('medias', []):
                clip = clip_from_dict(media)
                assert clip.id is not None

    def test_no_duplicate_ids(self, fixture):
        data = json.loads((FIXTURES / fixture).read_text())
        issues = _check_duplicate_clip_ids(data)
        assert issues == []

    def test_track_indices_consistent(self, fixture):
        data = json.loads((FIXTURES / fixture).read_text())
        issues = _check_track_indices(data)
        assert issues == []

    def test_no_stale_transitions(self, fixture):
        data = json.loads((FIXTURES / fixture).read_text())
        issues = _check_transition_references(data)
        assert issues == []
