"""Tests for Project.set_vertical_preset and related canvas dimension methods."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from camtasia.project import Project


class TestSetVerticalPreset:
    """Tests for Project.set_vertical_preset()."""

    @pytest.mark.parametrize(
        'preset, expected_w, expected_h',
        [
            ('9:16_FHD', 1080, 1920),
            ('9:16_HD', 720, 1280),
            ('4:5', 1080, 1350),
            ('1:1', 1080, 1080),
            ('16:9_FHD', 1920, 1080),
        ],
    )
    def test_sets_correct_dimensions(self, project: Project, preset: str, expected_w: int, expected_h: int):
        project.set_vertical_preset(preset)
        assert project.width == expected_w
        assert project.height == expected_h

    def test_invalid_preset_raises(self, project: Project):
        with pytest.raises(ValueError, match='Unknown preset'):
            project.set_vertical_preset('invalid')

    def test_overwrite_previous_dimensions(self, project: Project):
        project.set_vertical_preset('9:16_FHD')
        assert project.width == 1080
        project.set_vertical_preset('1:1')
        assert project.width == 1080
        assert project.height == 1080

    def test_preset_after_manual_set(self, project: Project):
        project.width = 640
        project.height = 480
        project.set_vertical_preset('4:5')
        assert project.width == 1080
        assert project.height == 1350
