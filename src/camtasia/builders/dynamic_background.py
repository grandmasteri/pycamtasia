"""Dynamic background assets — gradient, Lottie, and shader-based backgrounds."""
from __future__ import annotations

import enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from camtasia.timing import seconds_to_ticks

if TYPE_CHECKING:
    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip


class DynamicBackgroundAsset(enum.Enum):
    """Named dynamic background asset types."""

    GRADIENT_FOUR_CORNER = 'gradient_four_corner'
    GRADIENT_RADIAL = 'gradient_radial'
    ABSTRACT_SHAPES = 'abstract_shapes'
    WAVES = 'waves'
    BOKEH = 'bokeh'


# Assets that map to gradient backgrounds (handled via add_gradient_background
# or add_four_corner_gradient on the project).
_GRADIENT_ASSETS = {
    DynamicBackgroundAsset.GRADIENT_FOUR_CORNER,
    DynamicBackgroundAsset.GRADIENT_RADIAL,
}


def _build_source_effect_data(
    *,
    colors: list[tuple[float, float, float, float]] | None = None,
    speed: float = 1.0,
) -> dict[str, Any]:
    """Build a SourceEffect dict with color and speed parameters.

    Args:
        colors: Optional list of RGBA tuples (0.0-1.0).
        speed: Animation speed.

    Returns:
        A SourceEffect dict suitable for clip ``sourceEffect``.
    """
    params: dict[str, Any] = {'Speed': speed}
    if colors:
        for i, rgba in enumerate(colors):
            prefix = f'Color{i}'
            params[f'{prefix}-red'] = rgba[0]
            params[f'{prefix}-green'] = rgba[1]
            params[f'{prefix}-blue'] = rgba[2]
            params[f'{prefix}-alpha'] = rgba[3]
    return {
        'effectName': 'SourceEffect',
        'category': '',
        'parameters': params,
    }


def _build_lottie_source_effect_data() -> dict[str, Any]:
    """Build a SourceEffect dict with padded Color000-style keys for Lottie.

    Returns:
        A SourceEffect dict with Color000/Color001 placeholders.
    """
    params: dict[str, Any] = {}
    for i in range(2):
        prefix = f'Color{i:03d}'
        params[f'{prefix}-red'] = 1.0 if i == 0 else 0.0
        params[f'{prefix}-green'] = 1.0 if i == 0 else 0.0
        params[f'{prefix}-blue'] = 1.0 if i == 0 else 0.0
        params[f'{prefix}-alpha'] = 1.0
    return {
        'effectName': 'SourceEffect',
        'category': '',
        'parameters': params,
    }


def add_dynamic_background(
    project: Project,
    asset_name: str | DynamicBackgroundAsset,
    *,
    duration_seconds: float,
    colors: list[tuple[float, float, float, float]] | None = None,
    speed: float = 1.0,
    track_name: str = 'Background',
) -> BaseClip:
    """Add a dynamic background to the project.

    For gradient assets (``GRADIENT_FOUR_CORNER``, ``GRADIENT_RADIAL``),
    delegates to the project's gradient helpers. For other assets
    (``ABSTRACT_SHAPES``, ``WAVES``, ``BOKEH``), creates a clip with a
    ``SourceEffect`` carrying the color/speed parameters.

    Args:
        project: Target project.
        asset_name: A :class:`DynamicBackgroundAsset` member or its string value.
        duration_seconds: Duration of the background clip.
        colors: Optional RGBA colour list (0.0-1.0 per channel).
        speed: Animation speed multiplier.
        track_name: Name of the background track.

    Returns:
        The placed background clip.

    Raises:
        ValueError: If *asset_name* is not a valid asset.
    """
    if isinstance(asset_name, str):
        try:
            asset = DynamicBackgroundAsset(asset_name)
        except ValueError:
            raise ValueError(
                f"Unknown asset: {asset_name!r}. "
                f"Valid assets: {[a.value for a in DynamicBackgroundAsset]}"
            ) from None
    else:
        asset = asset_name

    if asset == DynamicBackgroundAsset.GRADIENT_FOUR_CORNER:
        c0 = colors[0] if colors and len(colors) > 0 else (0.16, 0.16, 0.16, 1.0)
        c1 = colors[1] if colors and len(colors) > 1 else (0.0, 0.0, 0.0, 1.0)
        clip = project.add_gradient_background(
            duration_seconds=duration_seconds,
            color0=c0,
            color1=c1,
        )
        return cast('BaseClip', clip)

    if asset == DynamicBackgroundAsset.GRADIENT_RADIAL:
        c0 = colors[0] if colors and len(colors) > 0 else (0.16, 0.16, 0.16, 1.0)
        c1 = colors[1] if colors and len(colors) > 1 else (0.0, 0.0, 0.0, 1.0)
        clip = project.add_gradient_background(
            duration_seconds=duration_seconds,
            color0=c0,
            color1=c1,
        )
        return cast('BaseClip', clip)

    # Non-gradient assets: create a placeholder clip with SourceEffect
    track = project.timeline.get_or_create_track(track_name)
    media_id = project.media_bin.next_id()
    duration_ticks = seconds_to_ticks(duration_seconds)

    clip_data: dict[str, Any] = {
        '_type': 'VMFile',
        'id': media_id,
        'src': media_id,
        'trackNumber': 0,
        'trimStartSum': 0,
        'start': 0,
        'duration': duration_ticks,
        'mediaStart': 0,
        'mediaDuration': duration_ticks,
        'scalar': 1,
        'metadata': {'clipSpeedAttribute': 1},
        'effects': [],
        'sourceEffect': _build_source_effect_data(colors=colors, speed=speed),
        'parameters': {'opacity': {'defaultValue': 1.0, 'type': 'double', 'interp': 'linr'}},
    }
    track._data.setdefault('medias', []).append(clip_data)

    from camtasia.timeline.clips.video import VMFile

    return VMFile(clip_data)


def add_lottie_background(
    project: Project,
    lottie_path: Path | str,
    *,
    duration_seconds: float,
    track_name: str = 'Background',
) -> BaseClip:
    """Add a Lottie animation as a background via SourceEffect.

    Creates a source bin entry for the Lottie file and places it on the
    background track with a ``SourceEffect`` using padded ``Color000``-style
    parameter keys.

    Args:
        project: Target project.
        lottie_path: Path to the Lottie JSON/dotLottie file.
        duration_seconds: Duration of the background clip.
        track_name: Name of the background track.

    Returns:
        The placed background clip.
    """
    lottie_path = Path(lottie_path)
    track = project.timeline.get_or_create_track(track_name)
    media_id = project.media_bin.next_id()
    clip_id = media_id + 1
    duration_ticks = seconds_to_ticks(duration_seconds)
    width, height = project.width, project.height

    # Add source bin entry directly (Lottie files aren't standard media)
    source_entry: dict[str, Any] = {
        'id': media_id,
        'src': f'./media/{lottie_path.name}',
        'rect': [0, 0, width, height],
        'lastMod': '0',
        'sourceTracks': [{
            'range': [0, 9223372036854775807],
            'type': 0,
            'editRate': 30,
            'trackRect': [0, 0, width, height],
            'sampleRate': 30,
            'bitDepth': 32,
            'numChannels': 0,
            'integratedLUFS': 100.0,
            'peakLevel': -1.0,
        }],
    }
    project._data['sourceBin'].append(source_entry)

    clip_data: dict[str, Any] = {
        '_type': 'VMFile',
        'id': clip_id,
        'src': media_id,
        'trackNumber': 0,
        'trimStartSum': 0,
        'start': 0,
        'duration': duration_ticks,
        'mediaStart': 0,
        'mediaDuration': duration_ticks,
        'scalar': 1,
        'metadata': {'clipSpeedAttribute': 1},
        'effects': [],
        'sourceEffect': _build_lottie_source_effect_data(),
        'parameters': {'opacity': {'defaultValue': 1.0, 'type': 'double', 'interp': 'linr'}},
    }
    track._data.setdefault('medias', []).append(clip_data)

    from camtasia.timeline.clips.video import VMFile

    return VMFile(clip_data)
