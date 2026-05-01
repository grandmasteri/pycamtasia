"""Tests for default per-slide duration sourced from project settings."""
from __future__ import annotations

from camtasia.builders.slide_import import import_slide_images


class TestSlideDurationFromProject:
    def test_default_duration_from_project_metadata(self, project):
        project._data.setdefault('metadata', {})['defaultImageDuration'] = 8.0
        png = project.file_path / 'slide.png'
        png.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        clips = import_slide_images(project, [png])
        assert len(clips) == 1
        assert abs(clips[0].duration_seconds - 8.0) < 0.01

    def test_fallback_to_5_when_no_metadata(self, project):
        png = project.file_path / 'slide.png'
        png.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        clips = import_slide_images(project, [png])
        assert len(clips) == 1
        assert abs(clips[0].duration_seconds - 5.0) < 0.01

    def test_explicit_overrides_project_setting(self, project):
        project._data.setdefault('metadata', {})['defaultImageDuration'] = 8.0
        png = project.file_path / 'slide.png'
        png.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        clips = import_slide_images(project, [png], per_slide_seconds=3.0)
        assert len(clips) == 1
        assert abs(clips[0].duration_seconds - 3.0) < 0.01

    def test_multiple_slides_use_project_duration(self, project):
        project._data.setdefault('metadata', {})['defaultImageDuration'] = 6.0
        slides = []
        for i in range(3):
            png = project.file_path / f'slide_{i}.png'
            png.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            slides.append(png)
        clips = import_slide_images(project, slides)
        assert len(clips) == 3
        for clip in clips:
            assert abs(clip.duration_seconds - 6.0) < 0.01
