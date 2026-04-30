"""Library and Libraries abstractions for Camtasia asset management.

Provides a container for reusable assets (clips, groups, media) that can be
organized into folders and shared across projects. This is the pycamtasia
equivalent of Camtasia's Library panel.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class LibraryAsset:
    """A single reusable asset stored in a library.

    Attributes:
        name: Display name of the asset.
        kind: Asset type identifier (e.g. ``'clip'``, ``'group'``, ``'media'``).
        payload: Serializable dict representing the asset's data.
        thumbnail_path: Optional path to a thumbnail image.
    """

    name: str
    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    thumbnail_path: Path | None = None


class Library:
    """A named collection of reusable assets organized into folders.

    Args:
        name: Display name of this library.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._assets: list[LibraryAsset] = []
        self._folders: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        """Display name of this library."""
        return self._name

    @property
    def assets(self) -> list[LibraryAsset]:
        """All assets in this library."""
        return self._assets

    @property
    def folders(self) -> dict[str, dict[str, Any]]:
        """Nested folder structure as ``{name: {children...}}``."""
        return self._folders

    def add_asset(
        self,
        clip_or_group: dict[str, Any],
        name: str,
        *,
        use_canvas_size: bool = True,
    ) -> LibraryAsset:
        """Add a clip or group dict as a library asset.

        Args:
            clip_or_group: Raw clip/group data dict to store.
            name: Display name for the asset.
            use_canvas_size: If ``True``, store canvas size metadata.

        Returns:
            The newly created :class:`LibraryAsset`.
        """
        payload = copy.deepcopy(clip_or_group)
        if use_canvas_size:
            payload["_useCanvasSize"] = True
        kind = "group" if "medias" in clip_or_group else "clip"
        asset = LibraryAsset(name=name, kind=kind, payload=payload)
        self._assets.append(asset)
        return asset

    def add_timeline_selection(
        self,
        timeline: Any,
        start: int,
        end: int,
        name: str,
        *,
        use_canvas_size: bool = True,
    ) -> LibraryAsset:
        """Capture a time range from a timeline as a library asset.

        Args:
            timeline: A timeline object with ``all_clips()`` method.
            start: Start tick (inclusive).
            end: End tick (exclusive).
            name: Display name for the asset.
            use_canvas_size: If ``True``, store canvas size metadata.

        Returns:
            The newly created :class:`LibraryAsset`.
        """
        clips = [
            copy.deepcopy(c._data)
            for c in timeline.all_clips()
            if c.start < end and (c.start + c.duration) > start
        ]
        payload: dict[str, Any] = {"clips": clips, "range": [start, end]}
        if use_canvas_size:
            payload["_useCanvasSize"] = True
        asset = LibraryAsset(name=name, kind="selection", payload=payload)
        self._assets.append(asset)
        return asset

    def create_folder(self, name: str, *, parent: str | None = None) -> dict[str, Any]:
        """Create a new folder in the library.

        Args:
            name: Folder name.
            parent: If provided, create as a subfolder of *parent*.

        Returns:
            The folder dict (which can contain nested children).

        Raises:
            KeyError: *parent* does not exist.
        """
        new_folder: dict[str, Any] = {}
        if parent is None:
            self._folders[name] = new_folder
        else:
            if parent not in self._folders:
                raise KeyError(f"Parent folder {parent!r} does not exist")
            self._folders[parent][name] = new_folder
        return new_folder

    def move(self, asset_or_folder: str, dest: str) -> None:
        """Move an asset or folder into a destination folder.

        Args:
            asset_or_folder: Name of the asset or folder to move.
            dest: Name of the destination folder.

        Raises:
            KeyError: *dest* does not exist or *asset_or_folder* not found.
        """
        if dest not in self._folders:
            raise KeyError(f"Destination folder {dest!r} does not exist")
        # Try moving a folder first
        if asset_or_folder in self._folders:
            self._folders[dest][asset_or_folder] = self._folders.pop(asset_or_folder)
            return
        # Try moving an asset
        for asset in self._assets:
            if asset.name == asset_or_folder:
                self._folders[dest][asset_or_folder] = {"_asset": True}
                return
        raise KeyError(f"{asset_or_folder!r} not found as asset or folder")

    def import_media(self, paths: list[Path] | list[str], *, folder: str | None = None) -> list[LibraryAsset]:
        """Import media files as library assets.

        Args:
            paths: File paths to import.
            folder: Optional folder to place imported assets into.

        Returns:
            List of newly created :class:`LibraryAsset` instances.

        Raises:
            KeyError: *folder* does not exist.
        """
        if folder is not None and folder not in self._folders:
            raise KeyError(f"Folder {folder!r} does not exist")
        assets = []
        for p in paths:
            p = Path(p)
            asset = LibraryAsset(
                name=p.stem,
                kind="media",
                payload={"source": str(p)},
            )
            self._assets.append(asset)
            if folder is not None:
                self._folders[folder][p.stem] = {"_asset": True}
            assets.append(asset)
        return assets

    def __iter__(self) -> Iterator[LibraryAsset]:
        """Iterate over all assets in this library."""
        yield from self._assets

    def __len__(self) -> int:
        return len(self._assets)

    def __repr__(self) -> str:
        return f"Library(name={self._name!r}, assets={len(self._assets)}, folders={len(self._folders)})"


class Libraries:
    """Container managing multiple :class:`Library` instances.

    Provides creation, lookup, and a default library.
    """

    def __init__(self) -> None:
        self._libraries: dict[str, Library] = {}
        self._default_name: str | None = None

    def create(self, name: str, *, start_from: Library | None = None) -> Library:
        """Create a new library.

        Args:
            name: Name for the new library.
            start_from: If provided, deep-copy assets from this library.

        Returns:
            The newly created :class:`Library`.

        Raises:
            ValueError: A library with *name* already exists.
        """
        if name in self._libraries:
            raise ValueError(f"Library {name!r} already exists")
        lib = Library(name)
        if start_from is not None:
            for asset in start_from:
                lib.add_asset(copy.deepcopy(asset.payload), asset.name)
        self._libraries[name] = lib
        if self._default_name is None:
            self._default_name = name
        return lib

    @property
    def default(self) -> Library:
        """The default library (the first one created).

        Raises:
            RuntimeError: No libraries have been created.
        """
        if self._default_name is None or self._default_name not in self._libraries:
            raise RuntimeError("No libraries exist")
        return self._libraries[self._default_name]

    def list(self) -> list[str]:
        """Return names of all libraries."""
        return list(self._libraries.keys())

    def get(self, name: str) -> Library:
        """Look up a library by name.

        Args:
            name: Library name.

        Returns:
            The matching :class:`Library`.

        Raises:
            KeyError: No library with *name* exists.
        """
        if name not in self._libraries:
            raise KeyError(f"Library {name!r} not found")
        return self._libraries[name]

    def __len__(self) -> int:
        return len(self._libraries)

    def __repr__(self) -> str:
        return f"Libraries(count={len(self._libraries)})"
