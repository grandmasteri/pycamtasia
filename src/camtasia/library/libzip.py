"""Portable library archive format (.libzip) for pycamtasia.

.. warning::

    This module implements a **pycamtasia-defined** portable archive format,
    NOT the native TechSmith ``.libzip`` format. The native format is
    proprietary and undocumented. Archives produced here use a JSON-based
    structure (zip containing ``manifest.json`` + per-asset JSON files) and
    are only interoperable with other pycamtasia installations.

    Do **not** attempt to open these archives in TechSmith Camtasia — they
    will not be recognized.
"""
from __future__ import annotations

import json
from pathlib import Path
import warnings
import zipfile

from camtasia.library.library import Library, LibraryAsset

_FORMAT_WARNING = (
    "pycamtasia .libzip files use a custom JSON-based format, "
    "NOT the native TechSmith .libzip format. "
    "These archives are only compatible with pycamtasia."
)


def _is_safe_relative_path(p: str) -> bool:
    """Return True if *p* is a safe relative path (no '..' components, not absolute)."""
    path = Path(p)
    if path.is_absolute():
        return False
    return '..' not in path.parts


def import_libzip(
    path: Path,
    *,
    target_library: Library | None = None,
    create_new: bool = True,
) -> Library:
    """Import a pycamtasia ``.libzip`` archive into a library.

    Args:
        path: Path to the ``.libzip`` file.
        target_library: Existing library to import into. If ``None`` and
            *create_new* is ``True``, a new library is created.
        create_new: Create a new library if *target_library* is ``None``.

    Returns:
        The library containing the imported assets.

    Raises:
        FileNotFoundError: *path* does not exist.
        ValueError: *target_library* is ``None`` and *create_new* is ``False``,
            or the archive contains unsafe paths.
        zipfile.BadZipFile: *path* is not a valid zip archive.
    """
    warnings.warn(_FORMAT_WARNING, UserWarning, stacklevel=2)
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if target_library is None:
        if not create_new:
            raise ValueError("target_library is None and create_new is False")
        target_library = Library(path.stem)

    with zipfile.ZipFile(path, "r") as zf:
        manifest_data = json.loads(zf.read("manifest.json"))
        for entry in manifest_data.get("assets", []):
            entry_file = entry["file"]
            if not _is_safe_relative_path(entry_file):
                raise ValueError(
                    f"Unsafe path in libzip manifest: {entry_file!r}"
                )
            asset_data = json.loads(zf.read(entry_file))
            thumbnail_raw = asset_data.get("thumbnail")
            if thumbnail_raw and not _is_safe_relative_path(thumbnail_raw):
                raise ValueError(
                    f"Unsafe thumbnail path in libzip asset: {thumbnail_raw!r}"
                )
            asset = LibraryAsset(
                name=asset_data["name"],
                kind=asset_data["kind"],
                payload=asset_data.get("payload", {}),
                thumbnail_path=Path(thumbnail_raw) if thumbnail_raw else None,
            )
            target_library.assets.append(asset)
        for folder_name in manifest_data.get("folders", []):
            target_library.create_folder(folder_name)

    return target_library


def export_libzip(library: Library, path: Path) -> Path:
    """Export a library to a pycamtasia ``.libzip`` archive.

    Args:
        library: The library to export.
        path: Destination path for the archive. If it does not end with
            ``.libzip``, the extension is appended.

    Returns:
        The path to the created archive file.
    """
    warnings.warn(_FORMAT_WARNING, UserWarning, stacklevel=2)
    path = Path(path)
    if path.suffix != ".libzip":
        path = path.with_suffix(".libzip")

    manifest: dict[str, list[dict[str, str]] | list[str]] = {"assets": [], "folders": list(library.folders.keys())}
    asset_entries: list[dict[str, str]] = []

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, asset in enumerate(library):
            filename = f"asset_{i}.json"
            asset_data = {
                "name": asset.name,
                "kind": asset.kind,
                "payload": asset.payload,
                "thumbnail": str(asset.thumbnail_path) if asset.thumbnail_path else None,
            }
            zf.writestr(filename, json.dumps(asset_data, indent=2))
            asset_entries.append({"name": asset.name, "file": filename})

        manifest["assets"] = asset_entries
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    return path
