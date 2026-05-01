"""Integration tests for canvas presets and custom dimensions.

Verifies that Camtasia can open projects with various canvas sizes,
from standard presets to extreme dimensions.
"""
from __future__ import annotations

import pytest

from camtasia.canvas_presets import VerticalPreset
from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


class TestCanvasDimensions:
    """Standard and unusual canvas dimensions open without error."""

    def test_1080p_default(self, project):
        project.width = 1920
        project.height = 1080
        open_in_camtasia(project)

    def test_720p(self, project):
        project.width = 1280
        project.height = 720
        open_in_camtasia(project)

    def test_4k(self, project):
        project.width = 3840
        project.height = 2160
        open_in_camtasia(project)

    def test_vertical_1080x1920(self, project):
        project.width = 1080
        project.height = 1920
        open_in_camtasia(project)

    def test_square_1080(self, project):
        project.width = 1080
        project.height = 1080
        open_in_camtasia(project)

    def test_unusual_1000x1000(self, project):
        project.width = 1000
        project.height = 1000
        open_in_camtasia(project)

    def test_unusual_2560x1440(self, project):
        project.width = 2560
        project.height = 1440
        open_in_camtasia(project)

    def test_very_small_320x240(self, project):
        project.width = 320
        project.height = 240
        open_in_camtasia(project)

    def test_very_large_8k(self, project):
        project.width = 7680
        project.height = 4320
        open_in_camtasia(project)


class TestCanvasPresets:
    """Canvas presets from VerticalPreset enum open correctly."""

    @pytest.mark.parametrize('preset', list(VerticalPreset), ids=lambda p: p.name)
    def test_preset_opens(self, project, preset):
        w, h = preset.value
        project.width = w
        project.height = h
        open_in_camtasia(project)
