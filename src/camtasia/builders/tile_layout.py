"""Tile layout builder for grid-based image arrangements."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip


class TileLayout:
    """Place images in a grid layout on the timeline."""

    def __init__(self, project: Project, track_prefix: str = 'Tile') -> None:
        self._project = project
        self._track_prefix = track_prefix
        self._tiles: list[BaseClip] = []

    def add_grid(
        self,
        image_paths: list[Path | str],
        start_seconds: float,
        end_seconds: float,
        grid: tuple[int, int] = (2, 2),
        stagger_seconds: float = 0.0,
        scale: float = 1.0,
        fade_in_seconds: float = 0.5,
    ) -> list[BaseClip]:
        """Place images in a grid layout.

        Args:
            image_paths: Images to place in the grid.
            start_seconds: When the first tile appears.
            end_seconds: When all tiles disappear.
            grid: (rows, cols) grid dimensions.
            stagger_seconds: Delay between each tile appearing.
            scale: Scale factor for each tile.
            fade_in_seconds: Fade-in duration for each tile.
        """
        rows, cols = grid
        if rows <= 0 or cols <= 0:
            raise ValueError(f'grid dimensions must be positive, got rows={rows}, cols={cols}')
        canvas_w = self._project.width
        canvas_h = self._project.height
        cell_w = canvas_w / cols
        cell_h = canvas_h / rows

        placed: list[BaseClip] = []
        for idx, image_path in enumerate(image_paths):
            row = idx // cols
            col = idx % cols
            if row >= rows:
                break  # grid full

            media = self._project.import_media(Path(image_path))
            track_name = f'{self._track_prefix}-{idx}'
            track = self._project.timeline.get_or_create_track(track_name)

            tile_start = start_seconds + (idx * stagger_seconds)
            tile_duration = end_seconds - tile_start
            if tile_duration <= 0:
                break  # remaining tiles would also be negative

            clip = track.add_image(
                media.id,
                start_seconds=tile_start,
                duration_seconds=tile_duration,
            )

            # Position in grid
            offset_x = (col - (cols - 1) / 2) * cell_w
            offset_y = (row - (rows - 1) / 2) * cell_h
            clip.translation = (offset_x, offset_y)
            clip.scale = (scale, scale)

            if fade_in_seconds > 0:
                clip.fade_in(fade_in_seconds)

            placed.append(clip)

        self._tiles.extend(placed)
        return placed

    @property
    def tiles(self) -> list[BaseClip]:
        """All placed tile clips."""
        return list(self._tiles)
