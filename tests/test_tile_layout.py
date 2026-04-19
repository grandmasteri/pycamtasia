"""Tests for TileLayout grid builder."""
from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.builders.tile_layout import TileLayout

FIXTURES = Path(__file__).parent / 'fixtures'
DUMMY_IMAGE = FIXTURES / 'empty.wav'  # reuse fixture as dummy media


class TestTileLayoutInit:
    def test_default_prefix(self, project):
        layout = TileLayout(project)
        assert layout.tiles == []

    def test_custom_prefix(self, project):
        layout = TileLayout(project, track_prefix='Grid')
        assert layout._track_prefix == 'Grid'


class TestAddGrid:
    def test_places_four_images_in_2x2(self, project):
        layout = TileLayout(project)
        images = [DUMMY_IMAGE] * 4
        placed = layout.add_grid(images, start_seconds=0, end_seconds=10)
        assert len(placed) == 4
        assert all(p.clip_type == 'IMFile' for p in placed)

    def test_tiles_property_accumulates(self, project):
        layout = TileLayout(project)
        layout.add_grid([DUMMY_IMAGE] * 2, start_seconds=0, end_seconds=5, grid=(1, 2))
        layout.add_grid([DUMMY_IMAGE], start_seconds=5, end_seconds=10, grid=(1, 1))
        assert len(layout.tiles) == 3
        assert all(t.clip_type == 'IMFile' for t in layout.tiles)

    def test_tiles_returns_copy(self, project):
        layout = TileLayout(project)
        layout.add_grid([DUMMY_IMAGE], start_seconds=0, end_seconds=5, grid=(1, 1))
        tiles = layout.tiles
        tiles.clear()
        assert len(layout.tiles) == 1

    def test_grid_truncates_excess_images(self, project):
        layout = TileLayout(project)
        images = [DUMMY_IMAGE] * 10
        placed = layout.add_grid(images, start_seconds=0, end_seconds=10, grid=(2, 2))
        assert len(placed) == 4  # 2x2 = 4 max
        assert all(p.clip_type == 'IMFile' for p in placed)

    def test_fewer_images_than_cells(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid([DUMMY_IMAGE], start_seconds=0, end_seconds=5, grid=(2, 2))
        assert len(placed) == 1
        assert placed[0].clip_type == 'IMFile'

    def test_empty_images_list(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid([], start_seconds=0, end_seconds=5)
        assert placed == []
        assert layout.tiles == []

    def test_scale_applied(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid(
            [DUMMY_IMAGE], start_seconds=0, end_seconds=5,
            grid=(1, 1), scale=0.5,
        )
        assert placed[0].scale == (0.5, 0.5)

    def test_translation_center_for_1x1(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid(
            [DUMMY_IMAGE], start_seconds=0, end_seconds=5, grid=(1, 1),
        )
        # Single cell: offset should be (0, 0)
        assert placed[0].translation == (0.0, 0.0)

    def test_translation_offsets_for_2x2(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid(
            [DUMMY_IMAGE] * 4, start_seconds=0, end_seconds=10, grid=(2, 2),
        )
        w = project.width
        h = project.height
        cell_w = w / 2
        cell_h = h / 2
        # (0,0) -> col=0, row=0 -> offset_x = (0 - 0.5)*cell_w, offset_y = (0 - 0.5)*cell_h
        assert placed[0].translation == (-cell_w / 2, -cell_h / 2)
        # (0,1) -> col=1, row=0
        assert placed[1].translation == (cell_w / 2, -cell_h / 2)
        # (1,0) -> col=0, row=1
        assert placed[2].translation == (-cell_w / 2, cell_h / 2)
        # (1,1) -> col=1, row=1
        assert placed[3].translation == (cell_w / 2, cell_h / 2)

    def test_stagger_offsets_start_times(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid(
            [DUMMY_IMAGE] * 2, start_seconds=1.0, end_seconds=10.0,
            grid=(1, 2), stagger_seconds=0.5,
        )
        # Second clip should start 0.5s later
        assert len(placed) == 2
        assert placed[0].start_seconds == pytest.approx(1.0)
        assert placed[1].start_seconds == pytest.approx(1.5)

    def test_no_fade_when_zero(self, project):
        layout = TileLayout(project)
        # Should not raise
        placed = layout.add_grid(
            [DUMMY_IMAGE], start_seconds=0, end_seconds=5,
            grid=(1, 1), fade_in_seconds=0,
        )
        assert len(placed) == 1
        assert placed[0].clip_type == 'IMFile'

    def test_custom_track_prefix(self, project):
        layout = TileLayout(project, track_prefix='Recap')
        layout.add_grid([DUMMY_IMAGE] * 2, start_seconds=0, end_seconds=5, grid=(1, 2))
        track_names = [t.name for t in project.timeline.tracks]
        assert any('Recap-0' in n for n in track_names)
        assert any('Recap-1' in n for n in track_names)

    def test_3x1_grid(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid(
            [DUMMY_IMAGE] * 3, start_seconds=0, end_seconds=5, grid=(3, 1),
        )
        assert len(placed) == 3
        assert all(p.clip_type == 'IMFile' for p in placed)
        # All should have x offset = 0 (single column)
        for clip in placed:
            assert clip.translation[0] == 0.0


class TestImportPath:
    def test_accepts_string_paths(self, project):
        layout = TileLayout(project)
        placed = layout.add_grid(
            [str(DUMMY_IMAGE)], start_seconds=0, end_seconds=5, grid=(1, 1),
        )
        assert len(placed) == 1
        assert placed[0].clip_type == 'IMFile'


# ── Merged from test_edge_case_coverage.py ───────────────────────────


class TestTileLayoutNegativeDuration:
    def test_stagger_causes_fewer_tiles(self, project):
        dummy = FIXTURES / 'empty.wav'
        layout = TileLayout(project)
        images = [dummy] * 6
        placed = layout.add_grid(images, start_seconds=0, end_seconds=5, stagger_seconds=2)
        assert len(placed) < 6