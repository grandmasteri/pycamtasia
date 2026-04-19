"""Tests for proj.add_four_corner_gradient() high-level API."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.project import Project


def _make_shader(tmp_path: Path) -> Path:
    shader = tmp_path / "gradient.tscshadervid"
    shader.write_text("shader")
    return shader


class TestAddFourCornerGradient:
    def test_imports_and_places_clip(self, tmp_path: Path, project: Project):
        shader = _make_shader(tmp_path)
        clip = project.add_four_corner_gradient(shader, duration_seconds=10.0)

        assert clip is not None
        assert clip._data['_type'] == 'VMFile'
        assert clip.start == 0
        shaders = project.find_media_by_suffix('.tscshadervid')
        assert [s.identity for s in shaders] == ['gradient']

    def test_reuses_existing_shader(self, tmp_path: Path, project: Project):
        shader = _make_shader(tmp_path)
        clip1 = project.add_four_corner_gradient(shader, duration_seconds=5.0)
        source_id = project.find_media_by_suffix('.tscshadervid')[0].id

        clip2 = project.add_four_corner_gradient(shader, duration_seconds=10.0)

        # Still only one shader in the bin
        assert [s.identity for s in project.find_media_by_suffix('.tscshadervid')] == ['gradient']
        assert clip2._data['src'] == source_id

    def test_creates_named_track(self, tmp_path: Path, project: Project):
        shader = _make_shader(tmp_path)
        project.add_four_corner_gradient(shader, duration_seconds=5.0)

        track_names = [t.name for t in project.timeline.tracks]
        assert 'Background' in track_names

    def test_custom_track_name(self, tmp_path: Path, project: Project):
        shader = _make_shader(tmp_path)
        project.add_four_corner_gradient(shader, duration_seconds=5.0, track_name='BG')

        track_names = [t.name for t in project.timeline.tracks]
        assert 'BG' in track_names

    def test_clip_starts_at_zero(self, tmp_path: Path, project: Project):
        shader = _make_shader(tmp_path)
        clip = project.add_four_corner_gradient(shader, duration_seconds=5.0)

        assert clip.start == 0

    def test_accepts_path_object(self, tmp_path: Path, project: Project):
        shader = _make_shader(tmp_path)
        clip = project.add_four_corner_gradient(Path(shader), duration_seconds=5.0)

        assert clip._data['_type'] == 'VMFile'

    def test_accepts_string_path(self, tmp_path: Path, project: Project):
        shader = _make_shader(tmp_path)
        clip = project.add_four_corner_gradient(str(shader), duration_seconds=5.0)

        assert clip._data['_type'] == 'VMFile'


class TestGradientBackgroundNonMatchingShader:
    """Cover project.py line 1453: existing shader without Color0/Color1 is not reused."""

    def test_creates_new_shader_when_existing_lacks_color_defs(self, project: Project):
        # Add a shader media entry WITHOUT Color0/Color1 effectDef
        project._data['sourceBin'].append({
            'id': 99, 'src': './media/other.tscshadervid',
            'sourceTracks': [], 'effectDef': [{'name': 'SomeOtherEffect'}],
            'rect': [0, 0, 1920, 1080], 'lastMod': '0',
        })
        project.add_gradient_background(duration_seconds=5.0)
        # Should have created a new shader, not reused the existing one
        shaders = [m for m in project.media_bin if str(m.source).endswith('.tscshadervid')]
        assert len(shaders) >= 2


class TestFourCornerGradientNonMatchingShader:
    """Cover project.py line 1624: existing shader IS a 2-color gradient, so not reused for 4-corner."""

    def test_imports_new_shader_when_existing_is_two_color(self, tmp_path: Path, project: Project):
        # Add a 2-color gradient shader (has Color0 and Color1 only)
        project._data['sourceBin'].append({
            'id': 99, 'src': './media/gradient.tscshadervid',
            'sourceTracks': [], 'effectDef': [{'name': 'Color0'}, {'name': 'Color1'}],
            'rect': [0, 0, 1920, 1080], 'lastMod': '0',
        })
        shader = _make_shader(tmp_path)
        clip = project.add_four_corner_gradient(shader, duration_seconds=5.0)
        assert clip._data['_type'] == 'VMFile'
