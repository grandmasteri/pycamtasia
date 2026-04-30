"""Export project assets as a .campackage ZIP archive.

.. warning::

    The ``.campackage`` format produced by this module is a **pycamtasia-defined
    interchange format**. It is NOT the native TechSmith ``.campackage`` format
    and cannot be imported by Camtasia directly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
import warnings
import zipfile

if TYPE_CHECKING:
    from camtasia.project import Project

_FORMAT_WARNING = (
    'export_campackage produces a pycamtasia-defined .campackage format, '
    'NOT the native TechSmith .campackage format. '
    'Files created by this function cannot be imported by Camtasia directly.'
)


def export_campackage(
    project: Project,
    assets: list[dict[str, Any]],
    dest_path: Path | str,
    *,
    package_name: str,
) -> Path:
    """Write a .campackage ZIP containing a manifest and per-asset JSON files.

    The archive contains:
    - ``manifest.json`` — package metadata and asset index
    - ``assets/<index>.json`` — one file per asset entry

    Args:
        project: Source project (used for canvas metadata).
        assets: List of asset dicts. Each must contain at least a ``"name"`` key.
        dest_path: Destination path for the .campackage file. The ``.campackage``
            extension is appended if not already present.
        package_name: Human-readable name for the package.

    Returns:
        The path to the written .campackage file.

    Raises:
        ValueError: If *assets* is empty or any asset lacks a ``"name"`` key.
    """
    warnings.warn(_FORMAT_WARNING, UserWarning, stacklevel=2)

    if not assets:
        raise ValueError('assets must not be empty')
    for i, asset in enumerate(assets):
        if 'name' not in asset:
            raise ValueError(f'asset at index {i} is missing required "name" key')

    dest = Path(dest_path)
    if dest.suffix != '.campackage':
        dest = dest.with_suffix('.campackage')
    dest.parent.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        'format': 'pycamtasia-campackage',
        'version': '1.0',
        'package_name': package_name,
        'canvas': {'width': project.width, 'height': project.height},
        'asset_count': len(assets),
        'assets': [
            {'index': i, 'name': a['name'], 'file': f'assets/{i}.json'}
            for i, a in enumerate(assets)
        ],
    }

    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps(manifest, indent=2))
        for i, asset in enumerate(assets):
            zf.writestr(f'assets/{i}.json', json.dumps(asset, indent=2))

    return dest
