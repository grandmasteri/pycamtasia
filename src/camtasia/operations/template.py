"""Template-based project creation and media source replacement."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path
from typing import Any, Iterator


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
                yield from (m for m in clip.get("medias", []))
            elif clip.get("_type") == "Group":
                yield from _walk_clips(clip.get("tracks", []))


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
) -> 'Project':
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

    return proj
