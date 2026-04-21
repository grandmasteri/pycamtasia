"""Theme/color palette system for Camtasia projects.

Camtasia stores theme mappings inside ``assetProperties`` entries on clips.
Each mapping says "this clip's property X should use theme slot Y" (e.g.,
``outline -> accent-1``). A :class:`Theme` defines concrete values for
the slots; :func:`apply_theme` walks the project and substitutes them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
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
