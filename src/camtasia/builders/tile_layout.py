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
        fit_to_cell: bool = True,
    ) -> list[BaseClip]:
        """Place images in a grid layout.

        Args:
            image_paths: Images to place in the grid.
            start_seconds: When the first tile appears.
            end_seconds: When all tiles disappear.
            grid: (rows, cols) grid dimensions.
            stagger_seconds: Delay between each tile appearing.
            scale: Scale multiplier applied on top of the auto-fit (1.0 = no
                extra scaling). Use values > 1.0 to make tiles overflow their
                cell, < 1.0 to leave padding.
            fade_in_seconds: Fade-in duration for each tile.
            fit_to_cell: When True (default), each image is auto-scaled so
                its longest edge fits within the cell while preserving
                aspect ratio, then multiplied by ``scale``. When False,
                images use their native size multiplied by ``scale``.
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

            # Determine effective scale
            if fit_to_cell:
                img_w, img_h = media.dimensions
                if img_w > 0 and img_h > 0:  # pragma: no cover  # exercised only with pymediainfo installed + real image
                    fit_scale = min(cell_w / img_w, cell_h / img_h)
                else:
                    fit_scale = 1.0  # unknown dimensions, fall back
                effective_scale = fit_scale * scale
            else:
                effective_scale = scale
            clip.scale = (effective_scale, effective_scale)

            if fade_in_seconds > 0:
                clip.fade_in(fade_in_seconds)

            placed.append(clip)

        self._tiles.extend(placed)
        return placed

    @property
    def tiles(self) -> list[BaseClip]:
        """All placed tile clips."""
        return list(self._tiles)
