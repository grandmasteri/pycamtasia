from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from camtasia.timing import seconds_to_ticks


@pytest.fixture
def mock_clip():
    clip = MagicMock()
    clip.set_scale_keyframes = MagicMock(return_value=clip)
    clip.set_position_keyframes = MagicMock(return_value=clip)
    return clip


class TestAddZoomToRegion:
    def test_returns_clip(self, project, mock_clip):
        actual_result = project.add_zoom_to_region(mock_clip, start_seconds=2.0, duration_seconds=5.0)
        assert actual_result is mock_clip

    def test_default_scale_and_center(self, project, mock_clip):
        project.add_zoom_to_region(mock_clip, start_seconds=2.0, duration_seconds=5.0)
        scale_kfs = mock_clip.set_scale_keyframes.call_args[0][0]
        assert len(scale_kfs) == 5
        # Default scale=2.0
        assert scale_kfs[0] == (0.0, 1.0)
        assert scale_kfs[1] == (2.0, 1.0)
        assert scale_kfs[2] == (2.3, 2.0)
        assert scale_kfs[3] == (6.7, 2.0)
        assert scale_kfs[4] == (7.0, 1.0)

    def test_default_center_translation_is_zero(self, project, mock_clip):
        """center_x=0.5, center_y=0.5 means no translation needed."""
        project.add_zoom_to_region(mock_clip, start_seconds=1.0, duration_seconds=4.0)
        pos_kfs = mock_clip.set_position_keyframes.call_args[0][0]
        # All positions should be (0.0, 0.0) when centering on 0.5, 0.5
        for _, x, y in pos_kfs:
            assert x == 0.0 and y == 0.0

    def test_custom_scale(self, project, mock_clip):
        project.add_zoom_to_region(mock_clip, start_seconds=0.0, duration_seconds=3.0, scale=3.0)
        scale_kfs = mock_clip.set_scale_keyframes.call_args[0][0]
        assert scale_kfs[2][1] == 3.0
        assert scale_kfs[3][1] == 3.0

    def test_custom_center_produces_translation(self, project, mock_clip):
        project.add_zoom_to_region(
            mock_clip, start_seconds=1.0, duration_seconds=4.0,
            scale=2.0, center_x=0.25, center_y=0.75,
        )
        pos_kfs = mock_clip.set_position_keyframes.call_args[0][0]
        w, h = project.width, project.height
        expected_tx = (0.5 - 0.25) * (2.0 - 1) * w
        expected_ty = (0.5 - 0.75) * (2.0 - 1) * h
        # Zoomed-in keyframes should have the translation
        assert pos_kfs[2][1] == expected_tx and pos_kfs[2][2] == expected_ty
        assert pos_kfs[3][1] == expected_tx and pos_kfs[3][2] == expected_ty
        # Start/end should be zero
        assert pos_kfs[0][1] == 0.0 and pos_kfs[0][2] == 0.0
        assert pos_kfs[4][1] == 0.0 and pos_kfs[4][2] == 0.0

    def test_uses_project_dimensions(self, project, mock_clip):
        project.width = 3840
        project.height = 2160
        project.add_zoom_to_region(
            mock_clip, start_seconds=0.0, duration_seconds=2.0,
            scale=2.0, center_x=0.0, center_y=0.0,
        )
        pos_kfs = mock_clip.set_position_keyframes.call_args[0][0]
        expected_tx = 0.5 * 1.0 * 3840  # (0.5 - 0.0) * (2-1) * 3840
        expected_ty = 0.5 * 1.0 * 2160
        assert pos_kfs[2][1] == expected_tx and pos_kfs[2][2] == expected_ty

    def test_keyframe_timing(self, project, mock_clip):
        project.add_zoom_to_region(mock_clip, start_seconds=5.0, duration_seconds=10.0, scale=1.5)
        scale_kfs = mock_clip.set_scale_keyframes.call_args[0][0]
        assert scale_kfs[0][0] == 0.0
        assert scale_kfs[1][0] == 5.0
        assert scale_kfs[2][0] == pytest.approx(5.3)
        assert scale_kfs[3][0] == pytest.approx(14.7)
        assert scale_kfs[4][0] == 15.0

    def test_position_keyframe_count_matches_scale(self, project, mock_clip):
        project.add_zoom_to_region(mock_clip, start_seconds=0.0, duration_seconds=5.0)
        scale_kfs = mock_clip.set_scale_keyframes.call_args[0][0]
        pos_kfs = mock_clip.set_position_keyframes.call_args[0][0]
        assert len(scale_kfs) == len(pos_kfs)
