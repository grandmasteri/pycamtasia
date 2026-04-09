"""Project loading, saving, and creation for Camtasia .cmproj bundles."""

from __future__ import annotations

import json
import shutil
from contextlib import contextmanager
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Iterator

from camtasia.authoring_client import AuthoringClient
from camtasia.media_bin import MediaBin
from camtasia.timeline import Timeline
from camtasia.timing import EDIT_RATE


class Project:
    """Main entry-point for interacting with Camtasia projects.

    A Camtasia project is a macOS bundle directory (.cmproj) containing a
    project.tscproj JSON file, media assets, and recordings.

    Args:
        file_path: Path to the .cmproj directory or .tscproj file.
        encoding: Text encoding of the project file.
    """

    def __init__(self, file_path: Path, encoding: str | None = None) -> None:
        self._file_path = file_path
        self._encoding = encoding
        self._data: dict = json.loads(self._project_file.read_text(encoding=encoding))

    @property
    def file_path(self) -> Path:
        """The full path to the Camtasia project."""
        return self._file_path

    @property
    def edit_rate(self) -> int:
        """The editing tick rate (ticks per second).

        Default is 705,600,000 — divisible by 30fps, 60fps, 44100Hz, 48000Hz.
        """
        return self._data.get('editRate', EDIT_RATE)

    @property
    def authoring_client(self) -> AuthoringClient:
        """Details about the software used to edit the project."""
        return AuthoringClient(**self._data['authoringClientName'])

    @property
    def media_bin(self) -> MediaBin:
        """The project's media bin (sourceBin)."""
        return MediaBin(self._data.setdefault('sourceBin', []), self._file_path)

    @property
    def timeline(self) -> Timeline:
        """The project's timeline."""
        return Timeline(self._data['timeline'])

    def save(self) -> None:
        """Write the current project state to disk."""
        with self._project_file.open(mode='wt', encoding=self._encoding) as handle:
            json.dump(self._data, handle)

    @property
    def _project_file(self) -> Path:
        """Locate the .tscproj JSON file within the project bundle."""
        if self.file_path.is_dir():
            for file in self.file_path.iterdir():
                if file.is_file() and file.suffix == '.tscproj':
                    return file
            raise FileNotFoundError("No .tscproj file was found in directory")
        return self.file_path

    def __repr__(self) -> str:
        return f'Project(file_path="{self.file_path}")'


def load_project(file_path: str | Path, encoding: str | None = None) -> Project:
    """Load a Camtasia project from disk.

    Args:
        file_path: Path to the .cmproj directory or .tscproj file.
        encoding: Text encoding of the project file.

    Returns:
        A Project instance.
    """
    return Project(Path(file_path).resolve(), encoding=encoding)


@contextmanager
def use_project(
    file_path: str | Path,
    save_on_exit: bool = True,
    encoding: str | None = None,
) -> Iterator[Project]:
    """Context manager that loads a project and optionally saves on exit.

    Saves the project on normal exit if *save_on_exit* is True.
    Discards changes on exceptional exit.

    Args:
        file_path: Path to the .cmproj directory or .tscproj file.
        save_on_exit: Whether to save on normal exit.
        encoding: Text encoding of the project file.

    Yields:
        A Project instance.
    """
    proj = load_project(file_path, encoding=encoding)
    yield proj
    if save_on_exit:
        proj.save()


def new_project(file_path: str | Path) -> None:
    """Create a new, empty Camtasia project at *file_path*.

    Copies the bundled template project to the target path.

    Args:
        file_path: Destination path for the new .cmproj bundle.
    """
    template = importlib_resources.files('camtasia').joinpath('resources', 'new.cmproj')
    shutil.copytree(str(template), str(file_path))
