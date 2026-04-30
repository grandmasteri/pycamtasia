"""Template-based project creation and media source replacement.

This module provides two categories of template functionality:

1. **Low-level helpers** — ``clone_project_structure``, ``replace_media_source``,
   ``duplicate_project`` — operate on raw project dicts or .cmproj bundles.

2. **pycamtasia template I/O** — ``save_as_template``, ``new_from_template``,
   ``install_camtemplate``, ``list_installed_templates``, ``new_project_from_template``,
   ``TemplateManager``, ``replace_placeholder`` — manage a pycamtasia-specific
   ``.camtemplate`` archive format.

.. warning::

   The ``.camtemplate`` files produced here are **pycamtasia-JSON templates**,
   NOT native TechSmith ``.camtemplate`` files.  They cannot be opened directly
   in the Camtasia GUI.  Use ``new_from_template`` to materialise them into
   standard ``.cmproj`` projects that Camtasia can open.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any, Literal
import zipfile

if TYPE_CHECKING:
    from collections.abc import Iterator

    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip
    from camtasia.timeline.clips.placeholder import PlaceholderMedia

_TEMPLATES_DIR = Path.home() / '.pycamtasia' / 'templates'


def clone_project_structure(source_data: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy a project, clearing media-specific content.

    Preserves project settings, track structure, and effects templates.
    Empties the source bin and removes all clips from tracks.

    Args:
        source_data: The raw project JSON dict to use as a template.

    Returns:
        A new project dict with media content cleared.
    """
    data = copy.deepcopy(source_data)
    data["sourceBin"] = []

    scene = data["timeline"]["sceneTrack"]["scenes"][0]["csml"]
    for track in scene["tracks"]:
        track["medias"] = []
        track.pop("transitions", None)

    # Clear timeline markers
    toc = data["timeline"].get("parameters", {}).get("toc", {})
    if "keyframes" in toc:
        toc["keyframes"] = []

    return data


def _walk_clips(tracks: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Yield every clip dict, recursing into Groups and StitchedMedia."""
    for track in tracks:
        for clip in track.get("medias", []):
            yield clip
            if clip.get("_type") == "StitchedMedia":
                for m in clip.get("medias", []):
                    yield m
                    if m.get("_type") == "UnifiedMedia":
                        for key in ("video", "audio"):
                            child = m.get(key)
                            if child and isinstance(child, dict):
                                yield child
                                if child.get("_type") == "Group":
                                    yield from _walk_clips(child.get("tracks", []))
                                elif child.get("_type") == "StitchedMedia":
                                    yield from _walk_clips([child])
                    elif m.get("_type") == "Group":
                        yield from _walk_clips(m.get("tracks", []))
                    elif m.get("_type") == "StitchedMedia":
                        yield from _walk_clips([m])
            elif clip.get("_type") == "Group":
                yield from _walk_clips(clip.get("tracks", []))
            elif clip.get("_type") == "UnifiedMedia":
                for key in ("video", "audio"):
                    child = clip.get(key)
                    if child and isinstance(child, dict):
                        yield child
                        # Recurse if child is a compound type
                        if child.get("_type") == "Group":
                            yield from _walk_clips(child.get("tracks", []))
                        elif child.get("_type") == "StitchedMedia":
                            yield from _walk_clips([child])


def replace_media_source(
    project_data: dict[str, Any],
    old_source_id: int,
    new_source_id: int,
) -> int:
    """Replace all references to one media source with another.

    Walks all clips (including nested StitchedMedia children and Group
    internal tracks) and replaces ``src`` fields.

    Args:
        project_data: The raw project JSON dict.
        old_source_id: Source bin ID to replace.
        new_source_id: Replacement source bin ID.

    Returns:
        Number of clips updated.
    """
    scene = project_data["timeline"]["sceneTrack"]["scenes"][0]["csml"]
    count = 0
    for clip in _walk_clips(scene["tracks"]):
        if clip.get("src") == old_source_id:
            clip["src"] = new_source_id
            count += 1
    return count


def duplicate_project(
    source_path: str | Path,
    dest_path: str | Path,
    *,
    clear_media: bool = False,
) -> Project:
    """Duplicate a Camtasia project to a new location.

    Copies the entire .cmproj bundle (including media files) to dest_path.
    If clear_media is True, removes all clips and media from the copy
    while preserving project settings (canvas size, edit rate, etc.).

    Args:
        source_path: Path to the source .cmproj project.
        dest_path: Path for the new project copy.
        clear_media: If True, strip all clips and media from the copy.

    Returns:
        The loaded Project at dest_path.
    """
    from camtasia.project import load_project

    src = Path(source_path)
    dst = Path(dest_path)
    if dst.exists():
        raise FileExistsError(f'Destination already exists: {dst}')
    shutil.copytree(src, dst)

    proj = load_project(str(dst))
    if clear_media:
        for track in proj.timeline.tracks:
            track.clear()
        proj._data['sourceBin'] = []
        toc = proj._data.get('timeline', {}).get('parameters', {}).get('toc', {})
        if 'keyframes' in toc:
            toc['keyframes'] = []
        proj.save()

        media_dir = dst / 'media' if dst.is_dir() else dst.parent / 'media'
        if media_dir and media_dir.exists():
            shutil.rmtree(media_dir)
            media_dir.mkdir(parents=True, exist_ok=True)

    return proj


# ---------------------------------------------------------------------------
# pycamtasia template I/O
# ---------------------------------------------------------------------------

_MANIFEST_VERSION = 1


def _collect_placeholders(project_data: dict[str, Any]) -> list[dict[str, str]]:
    """Return a list of ``{title, subtitle}`` dicts for every PlaceholderMedia clip."""
    scene = project_data['timeline']['sceneTrack']['scenes'][0]['csml']
    result: list[dict[str, str]] = []
    for clip in _walk_clips(scene['tracks']):
        if clip.get('_type') == 'PlaceholderMedia':
            meta = clip.get('metadata', {})
            result.append({
                'title': meta.get('placeHolderTitle', '') or '',
                'subtitle': meta.get('placeHolderSubTitle', '') or '',
            })
    return result


def save_as_template(project: Project, name: str, dest_path: str | Path) -> Path:
    """Save a project as a pycamtasia ``.camtemplate`` archive.

    The archive is a ZIP file containing:

    * ``manifest.json`` — template name, version, placeholder list.
    * ``project.tscproj`` — the full project JSON.
    * ``metadata.json`` — canvas dimensions and edit rate.

    .. warning::

       This produces a **pycamtasia-JSON template**, NOT a native TechSmith
       ``.camtemplate``.  Use :func:`new_from_template` to create a real
       ``.cmproj`` project from it.

    Args:
        project: The source project.
        name: Human-readable template name stored in the manifest.
        dest_path: Destination file path (should end in ``.camtemplate``).

    Returns:
        Resolved path to the written archive.
    """
    dest = Path(dest_path).resolve()
    data = copy.deepcopy(project._data)
    placeholders = _collect_placeholders(data)

    manifest = {
        'format': 'pycamtasia-template',
        'version': _MANIFEST_VERSION,
        'name': name,
        'placeholders': placeholders,
    }
    metadata = {
        'width': data.get('width', 1920),
        'height': data.get('height', 1080),
        'editRate': data.get('editRate', 705600000),
    }

    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps(manifest, indent=2))
        zf.writestr('project.tscproj', json.dumps(data, indent=2))
        zf.writestr('metadata.json', json.dumps(metadata, indent=2))

    return dest


def export_camtemplate(project: Project, dest_path: str | Path) -> Path:
    """Alias for :func:`save_as_template` using the project title as name.

    Args:
        project: The source project.
        dest_path: Destination file path.

    Returns:
        Resolved path to the written archive.
    """
    name = project._data.get('title', '') or Path(dest_path).stem
    return save_as_template(project, name, dest_path)


def _read_template(template_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read manifest and project data from a .camtemplate archive.

    Returns:
        ``(manifest, project_data)`` tuple.

    Raises:
        FileNotFoundError: If *template_path* does not exist.
        ValueError: If the archive is not a valid pycamtasia template.
    """
    if not template_path.exists():
        raise FileNotFoundError(template_path)
    with zipfile.ZipFile(template_path, 'r') as zf:
        try:
            manifest = json.loads(zf.read('manifest.json'))
        except KeyError:
            raise ValueError(f'Not a valid pycamtasia template: {template_path}') from None
        if manifest.get('format') != 'pycamtasia-template':
            raise ValueError(f'Not a valid pycamtasia template: {template_path}')
        project_data = json.loads(zf.read('project.tscproj'))
    return manifest, project_data


def new_from_template(template_path: str | Path, dest_project_path: str | Path) -> Project:
    """Create a new ``.cmproj`` project from a pycamtasia template.

    Placeholder clips are kept but their titles are cleared, giving the
    caller a blank slate to fill in.

    Args:
        template_path: Path to the ``.camtemplate`` archive.
        dest_project_path: Destination ``.cmproj`` directory.

    Returns:
        The loaded Project at *dest_project_path*.

    Raises:
        FileExistsError: If *dest_project_path* already exists.
        ValueError: If the template is invalid.
    """
    from camtasia.project import load_project, new_project

    tpl = Path(template_path)
    dest = Path(dest_project_path)
    if dest.exists():
        raise FileExistsError(f'Destination already exists: {dest}')

    _manifest, project_data = _read_template(tpl)

    # Clear placeholder titles so the new project starts fresh
    scene = project_data['timeline']['sceneTrack']['scenes'][0]['csml']
    for clip in _walk_clips(scene['tracks']):
        if clip.get('_type') == 'PlaceholderMedia':
            meta = clip.setdefault('metadata', {})
            meta['placeHolderTitle'] = ''
            meta['placeHolderSubTitle'] = ''

    new_project(dest)
    proj = load_project(dest)
    proj._data.update(project_data)
    proj.save()
    return load_project(dest)


def install_camtemplate(path: str | Path) -> Path:
    """Copy a ``.camtemplate`` archive into the user template directory.

    The template directory is ``~/.pycamtasia/templates/``.

    Args:
        path: Path to the ``.camtemplate`` file.

    Returns:
        Path to the installed copy.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file is not a valid pycamtasia template.
    """
    src = Path(path).resolve()
    # Validate before installing
    _read_template(src)
    _TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    dest = _TEMPLATES_DIR / src.name
    shutil.copy2(src, dest)
    return dest


def list_installed_templates() -> list[Path]:
    """Return paths to all installed ``.camtemplate`` files.

    Returns:
        Sorted list of paths in ``~/.pycamtasia/templates/``.
    """
    if not _TEMPLATES_DIR.exists():
        return []
    return sorted(_TEMPLATES_DIR.glob('*.camtemplate'))


def new_project_from_template(template_name: str, dest_path: str | Path) -> Project:
    """Create a project from an installed template looked up by name.

    The *template_name* is matched against the manifest ``name`` field of
    each installed template.

    Args:
        template_name: Name stored in the template manifest.
        dest_path: Destination ``.cmproj`` directory.

    Returns:
        The loaded Project.

    Raises:
        FileNotFoundError: If no installed template matches *template_name*.
    """
    for tpl_path in list_installed_templates():
        try:
            manifest, _ = _read_template(tpl_path)
        except (ValueError, KeyError):
            continue
        if manifest.get('name') == template_name:
            return new_from_template(tpl_path, dest_path)
    raise FileNotFoundError(f'No installed template named {template_name!r}')


class TemplateManager:
    """Manage installed pycamtasia templates.

    Provides list, rename, and delete operations on the user template
    directory at ``~/.pycamtasia/templates/``.
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._dir = templates_dir or _TEMPLATES_DIR

    def list(self) -> list[Path]:
        """Return sorted paths to all installed templates."""
        if not self._dir.exists():
            return []
        return sorted(self._dir.glob('*.camtemplate'))

    def rename(self, old_filename: str, new_filename: str) -> Path:
        """Rename an installed template file.

        Args:
            old_filename: Current filename (e.g. ``'my.camtemplate'``).
            new_filename: New filename.

        Returns:
            Path to the renamed file.

        Raises:
            FileNotFoundError: If *old_filename* does not exist.
        """
        src = self._dir / old_filename
        if not src.exists():
            raise FileNotFoundError(src)
        dest = self._dir / new_filename
        src.rename(dest)
        return dest

    def delete(self, filename: str) -> None:
        """Delete an installed template.

        Args:
            filename: Filename to remove.

        Raises:
            FileNotFoundError: If *filename* does not exist.
        """
        target = self._dir / filename
        if not target.exists():
            raise FileNotFoundError(target)
        target.unlink()


def replace_placeholder(
    placeholder: PlaceholderMedia,
    new_media: BaseClip,
    *,
    mode: Literal['ripple', 'clip_speed', 'from_end', 'from_start'] = 'ripple',
) -> None:
    """Replace a placeholder clip's data with real media data.

    Because ``PlaceholderMedia.set_source`` raises ``TypeError``, this
    function works around the limitation by directly mutating the
    placeholder's underlying ``_data`` dict.

    Args:
        placeholder: The placeholder clip to replace.
        new_media: A clip whose source and timing to copy.
        mode: How to handle duration mismatch:

            * ``'ripple'`` — adopt the new media's duration (default).
            * ``'clip_speed'`` — keep the placeholder's duration, adjust
              scalar so the full media plays within it.
            * ``'from_end'`` — align the media to the placeholder's end,
              trimming from the start.
            * ``'from_start'`` — keep the placeholder's duration, trim
              from the end.

    Raises:
        ValueError: If *mode* is not one of the supported values.
    """
    from fractions import Fraction


    valid_modes = ('ripple', 'clip_speed', 'from_end', 'from_start')
    if mode not in valid_modes:
        raise ValueError(f'Invalid mode {mode!r}; expected one of {valid_modes}')

    src_data = new_media._data
    ph_data = placeholder._data

    # Copy source reference
    if 'src' in src_data:
        ph_data['src'] = src_data['src']

    # Change type to match the new media
    ph_data['_type'] = src_data['_type']

    # Copy media-file fields
    for key in ('trackNumber', 'attributes', 'channelNumber'):
        if key in src_data:
            ph_data[key] = copy.deepcopy(src_data[key])

    media_dur = int(src_data.get('mediaDuration', ph_data.get('duration', 0)))
    ph_dur = int(ph_data['duration'])

    if mode == 'ripple':
        ph_data['duration'] = int(src_data.get('duration', ph_dur))
        ph_data['mediaDuration'] = media_dur
        ph_data['mediaStart'] = int(src_data.get('mediaStart', 0))
        ph_data['scalar'] = src_data.get('scalar', 1)

    elif mode == 'clip_speed':
        # Keep placeholder duration, adjust scalar
        if media_dur > 0:
            scalar = Fraction(ph_dur, media_dur)
            ph_data['scalar'] = str(scalar) if scalar.denominator != 1 else int(scalar)
        ph_data['mediaDuration'] = media_dur
        ph_data['mediaStart'] = int(src_data.get('mediaStart', 0))

    elif mode == 'from_end':
        # Align to end of placeholder, trim from start
        ph_data['mediaDuration'] = media_dur
        ph_data['scalar'] = src_data.get('scalar', 1)
        if media_dur > ph_dur:
            ph_data['mediaStart'] = media_dur - ph_dur
        else:
            ph_data['mediaStart'] = 0
            ph_data['duration'] = media_dur

    elif mode == 'from_start':
        # Keep placeholder duration, trim from end
        ph_data['mediaDuration'] = media_dur
        ph_data['mediaStart'] = int(src_data.get('mediaStart', 0))
        ph_data['scalar'] = src_data.get('scalar', 1)
        # Duration stays as-is (placeholder's original duration)
