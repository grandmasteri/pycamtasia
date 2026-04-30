"""Theme/color palette system for Camtasia projects.

Camtasia stores theme mappings inside ``assetProperties`` entries on clips.
Each mapping says "this clip's property X should use theme slot Y" (e.g.,
``outline -> accent-1``). A :class:`Theme` defines concrete values for
the slots; :func:`apply_theme` walks the project and substitutes them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from camtasia.project import Project


# RGBA tuple: (red, green, blue, alpha) with components in 0.0-1.0
RGBA = tuple[float, float, float, float]


@dataclass
class Theme:
    """A named theme with concrete values for each slot.

    Attributes follow the semantic slot names used in Camtasia's
    ``assetProperties.themeMappings`` values: ``accent-1``, ``accent-2``,
    ``background-1``, ``background-2``, ``foreground-1``, ``font-1``,
    ``font-2``.
    """

    name: str = 'Default'
    accent_1: RGBA = (0.18, 0.47, 0.78, 1.0)         # blue
    accent_2: RGBA = (0.98, 0.66, 0.15, 1.0)         # orange
    background_1: RGBA = (0.10, 0.10, 0.10, 1.0)     # near-black
    background_2: RGBA = (1.0, 1.0, 1.0, 1.0)        # white
    foreground_1: RGBA = (1.0, 1.0, 1.0, 1.0)        # white (text on accent/bg)
    font_1: str = 'Helvetica'
    font_2: str = 'Helvetica'
    logo_path: Path | None = None
    # Arbitrary custom slots (e.g., logo-1 image paths) can live here
    custom: dict[str, Any] = field(default_factory=dict)

    def resolve(self, slot: str) -> Any:
        """Return the concrete value for a semantic slot name.

        Raises KeyError if the slot is unknown and not in ``custom``.
        """
        mapping = {
            'accent-1': self.accent_1,
            'accent-2': self.accent_2,
            'background-1': self.background_1,
            'background-2': self.background_2,
            'foreground-1': self.foreground_1,
            'font-1': self.font_1,
            'font-2': self.font_2,
        }
        if slot in mapping:
            return mapping[slot]
        if slot in self.custom:
            return self.custom[slot]
        raise KeyError(f'Unknown theme slot: {slot!r}')

    def add_color(self, name: str, rgba: RGBA) -> None:
        """Add a dynamic accent color as a custom slot.

        Args:
            name: Slot name (e.g., ``accent-3``).
            rgba: Color as (red, green, blue, alpha) with 0.0-1.0 components.
        """
        self.custom[name] = rgba


class ThemeManager:
    """In-memory registry of named themes.

    Provides CRUD operations for managing a collection of :class:`Theme`
    instances keyed by name.
    """

    def __init__(self) -> None:
        self._themes: dict[str, Theme] = {}

    def create_theme(self, name: str, theme: Theme) -> None:
        """Register a theme under *name*.

        Args:
            name: Registry key.
            theme: Theme instance to store.

        Raises:
            KeyError: If *name* is already registered.
        """
        if name in self._themes:
            raise KeyError(f'Theme already exists: {name!r}')
        self._themes[name] = theme

    def rename(self, old_name: str, new_name: str) -> None:
        """Rename a registered theme.

        Args:
            old_name: Current name.
            new_name: Desired name.

        Raises:
            KeyError: If *old_name* does not exist or *new_name* already exists.
        """
        if old_name not in self._themes:
            raise KeyError(f'Theme not found: {old_name!r}')
        if new_name in self._themes:
            raise KeyError(f'Theme already exists: {new_name!r}')
        self._themes[new_name] = self._themes.pop(old_name)
        self._themes[new_name].name = new_name

    def delete(self, name: str) -> None:
        """Remove a theme by name.

        Raises:
            KeyError: If *name* does not exist.
        """
        if name not in self._themes:
            raise KeyError(f'Theme not found: {name!r}')
        del self._themes[name]

    def list(self) -> list[str]:
        """Return sorted list of registered theme names."""
        return sorted(self._themes)

    def get(self, name: str) -> Theme:
        """Retrieve a theme by name.

        Raises:
            KeyError: If *name* does not exist.
        """
        if name not in self._themes:
            raise KeyError(f'Theme not found: {name!r}')
        return self._themes[name]


# ---------------------------------------------------------------------------
# Export / Import (pycamtasia JSON format — NOT native .camtheme)
# ---------------------------------------------------------------------------

def export_theme(theme: Theme, path: Path) -> None:
    """Write a theme to a JSON file in pycamtasia JSON format.

    This is **not** the native Camtasia ``.camtheme`` format — it is a
    pycamtasia-specific JSON representation for interchange.

    Args:
        theme: Theme to serialize.
        path: Destination file path.
    """
    data: dict[str, Any] = {
        'format': 'pycamtasia-theme',
        'version': 1,
        'name': theme.name,
        'accent_1': list(theme.accent_1),
        'accent_2': list(theme.accent_2),
        'background_1': list(theme.background_1),
        'background_2': list(theme.background_2),
        'foreground_1': list(theme.foreground_1),
        'font_1': theme.font_1,
        'font_2': theme.font_2,
        'logo_path': str(theme.logo_path) if theme.logo_path else None,
        'custom': {k: list(v) if isinstance(v, tuple) else v
                   for k, v in theme.custom.items()},
    }
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def import_theme(path: Path) -> Theme:
    """Read a theme from a pycamtasia JSON file.

    Args:
        path: Source file path.

    Returns:
        Reconstructed Theme instance.

    Raises:
        ValueError: If the file is not a valid pycamtasia theme.
    """
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('format') != 'pycamtasia-theme':
        raise ValueError(f'Not a pycamtasia theme file: {path}')
    logo = Path(data['logo_path']) if data.get('logo_path') else None
    custom = {k: tuple(v) if isinstance(v, list) else v
              for k, v in data.get('custom', {}).items()}
    return Theme(
        name=data['name'],
        accent_1=tuple(data['accent_1']),
        accent_2=tuple(data['accent_2']),
        background_1=tuple(data['background_1']),
        background_2=tuple(data['background_2']),
        foreground_1=tuple(data['foreground_1']),
        font_1=data['font_1'],
        font_2=data['font_2'],
        logo_path=logo,
        custom=custom,
    )


# ---------------------------------------------------------------------------
# Standalone annotation helper
# ---------------------------------------------------------------------------

def add_annotation_from_theme(
    track: Any,
    theme: Theme,
    annotation_type: str,
    text: str,
    start: float,
    duration: float,
    **kwargs: Any,
) -> Any:
    """Add an annotation to *track* with colors pre-filled from *theme*.

    This is a convenience wrapper around ``track.add_callout()`` that
    applies the theme's accent/foreground/font slots to the new callout.

    Args:
        track: A Track instance.
        theme: Theme whose slots supply colors and fonts.
        annotation_type: Currently only ``'callout'`` is supported.
        text: Annotation text.
        start: Start time in seconds.
        duration: Duration in seconds.
        **kwargs: Extra keyword arguments forwarded to ``add_callout()``.

    Returns:
        The newly created clip.

    Raises:
        ValueError: If *annotation_type* is not supported.
    """
    if annotation_type != 'callout':
        raise ValueError(f'Unsupported annotation type: {annotation_type!r}')
    callout = track.add_callout(text, start, duration, **kwargs)
    cdef = callout._data.setdefault('def', {})
    _apply_rgba(cdef, 'fill-color', theme.accent_2)
    _apply_rgba(cdef, 'stroke-color', theme.accent_1)
    font = cdef.setdefault('font', {})
    _apply_rgba(font, 'color', theme.foreground_1)
    font['name'] = theme.font_1
    return callout


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_rgba(target: dict, prefix: str, rgba: RGBA) -> None:
    """Write r/g/b/a to ``target[prefix+'-red']`` etc."""
    r, g, b, a = rgba
    target[f'{prefix}-red'] = r
    target[f'{prefix}-green'] = g
    target[f'{prefix}-blue'] = b
    target[f'{prefix}-opacity'] = a


def _find_clip_by_id(project: Project, clip_id: int) -> dict | None:
    """Walk the whole timeline (including nested) to find a clip dict by id."""
    def _walk(media: dict) -> dict | None:
        if media.get('id') == clip_id:
            return media
        for track in media.get('tracks', []):
            for m in track.get('medias', []):
                found = _walk(m)
                if found is not None:
                    return found
        for m in media.get('medias', []):
            found = _walk(m)
            if found is not None:
                return found
        for key in ('video', 'audio'):
            sub = media.get(key)
            if isinstance(sub, dict):
                found = _walk(sub)
                if found is not None:
                    return found
        return None

    for track_data in project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']:
        for media in track_data.get('medias', []):
            result = _walk(media)
            if result is not None:
                return result
    return None


def apply_theme(project: Project, theme: Theme) -> int:
    """Apply a theme to all clips that participate in themeMappings.

    Walks every ``assetProperties`` entry (on any clip, including nested)
    that has a ``themeMappings`` block, follows its ``objects`` list to
    the referenced clips, and writes the theme's concrete values onto
    each clip's relevant properties.

    Supported mapping keys:
    - ``fill``: sets ``fill-color-*`` on the clip's ``def`` dict
    - ``outline``: sets ``stroke-color-*`` on the clip's ``def`` dict
    - ``font-color``: sets font color on the clip's ``def`` dict and
      updates the ``fgColor`` textAttribute if present
    - ``font-family``: sets ``font.name`` on the clip's ``def`` dict
    - ``annotation-background``: sets ``annotation-bg-color-*`` on the
      clip's ``def`` dict
    - ``stroke-width``: sets ``stroke-width`` on the clip's ``def`` dict
    - ``stroke-style``: sets ``stroke-style`` on the clip's ``def`` dict

    Args:
        project: Target project.
        theme: Theme to apply.

    Returns:
        Number of clip-property mutations performed.
    """
    mutations = 0

    def _walk_asset_properties(media: dict) -> None:
        nonlocal mutations
        # Check this clip's own attributes
        attrs = media.get('attributes', {})
        for ap in attrs.get('assetProperties', []):
            mappings = ap.get('themeMappings', {})
            objects = ap.get('objects', [])
            if not mappings or not objects:
                continue
            for obj_id in objects:
                clip = _find_clip_by_id(project, obj_id)
                if clip is None:
                    continue
                cdef = clip.setdefault('def', {})
                for map_key, slot in mappings.items():
                    if not slot:
                        continue
                    try:
                        value = theme.resolve(slot)
                    except KeyError:
                        continue
                    if map_key == 'fill' and isinstance(value, tuple):
                        _apply_rgba(cdef, 'fill-color', value)
                        mutations += 1
                    elif map_key == 'outline' and isinstance(value, tuple):
                        _apply_rgba(cdef, 'stroke-color', value)
                        mutations += 1
                    elif map_key == 'font-color' and isinstance(value, tuple):
                        font = cdef.setdefault('font', {})
                        _apply_rgba(font, 'color', value)
                        mutations += 1
                    elif map_key == 'font-family' and isinstance(value, str):
                        font = cdef.setdefault('font', {})
                        font['name'] = value
                        mutations += 1
                    elif map_key == 'annotation-background' and isinstance(value, tuple):
                        _apply_rgba(cdef, 'annotation-bg-color', value)
                        mutations += 1
                    elif map_key == 'stroke-width':
                        cdef['stroke-width'] = value
                        mutations += 1
                    elif map_key == 'stroke-style':
                        cdef['stroke-style'] = value
                        mutations += 1
        # Recurse
        for track in media.get('tracks', []):
            for m in track.get('medias', []):
                _walk_asset_properties(m)
        for m in media.get('medias', []):
            _walk_asset_properties(m)

    for track_data in project._data['timeline']['sceneTrack']['scenes'][0]['csml']['tracks']:
        for media in track_data.get('medias', []):
            _walk_asset_properties(media)

    return mutations
