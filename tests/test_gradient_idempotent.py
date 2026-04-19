"""Tests for idempotent gradient background shader reuse."""
from __future__ import annotations

from camtasia.project import Project


class TestAddGradientBackgroundIdempotent:
    def test_creates_shader_when_none_exists(self, project: Project):
        project.add_gradient_background(duration_seconds=5.0)

        shader_sources = project.find_media_by_suffix('.tscshadervid')
        actual_shader_count = len(shader_sources)
        assert actual_shader_count == 1
        assert '.tscshadervid' in str(shader_sources[0].source)

    def test_reuses_existing_shader(self, project: Project):
        project.add_gradient_background(duration_seconds=5.0)
        expected_source_id = project.find_media_by_suffix('.tscshadervid')[0].id

        project.add_gradient_background(duration_seconds=5.0)

        shader_sources = project.find_media_by_suffix('.tscshadervid')
        actual_shader_count = len(shader_sources)
        assert actual_shader_count == 1
        assert shader_sources[0].id == expected_source_id

    def test_different_duration_reuses_shader(self, project: Project):
        project.add_gradient_background(duration_seconds=5.0)
        expected_source_id = project.find_media_by_suffix('.tscshadervid')[0].id

        project.add_gradient_background(duration_seconds=10.0)

        shader_sources = project.find_media_by_suffix('.tscshadervid')
        actual_shader_count = len(shader_sources)
        assert actual_shader_count == 1
        assert shader_sources[0].id == expected_source_id
