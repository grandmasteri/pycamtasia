"""Project loading, saving, and creation for Camtasia .cmproj bundles."""

from __future__ import annotations

import json
import shutil
from contextlib import contextmanager
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any, Iterator

from camtasia.authoring_client import AuthoringClient
from camtasia.media_bin import Media, MediaBin, MediaType
from camtasia.timeline import Timeline
from camtasia.timing import EDIT_RATE, seconds_to_ticks


import subprocess as _sp


def _probe_image_dimensions(path: Path) -> tuple[int, int]:
    """Return (width, height) via ffprobe, or (1920, 1080) as fallback."""
    try:
        out = _sp.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'stream=width,height',
             '-of', 'csv=p=0', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        w, h = out.stdout.strip().split(',')
        return int(w), int(h)
    except Exception:
        return 1920, 1080


def _probe_audio_duration(path: Path, sample_rate: int = 44100) -> int:
    """Return total sample count via ffprobe, or a safe default."""
    try:
        out = _sp.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        seconds = float(out.stdout.strip())
        return int(seconds * sample_rate)
    except Exception:
        return 44100 * 60  # 1-minute fallback


def _probe_video_duration(path: Path) -> int:
    """Return duration in edit-rate ticks via ffprobe, or a safe default."""
    try:
        out = _sp.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        seconds = float(out.stdout.strip())
        return int(seconds * 30)  # video editRate is typically 30
    except Exception:
        return 30 * 60  # 1-minute fallback


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

    @staticmethod
    def _flatten_parameters(obj: Any) -> None:
        """Convert parameter dicts without keyframes to bare defaultValues.

        Camtasia v10 saves parameters as scalar values when there are no
        keyframes.  This walks the entire data tree in-place and replaces
        ``{"type": ..., "defaultValue": X, ...}`` with just ``X`` when
        the dict has no ``"keyframes"`` key.  Dicts that also carry a
        ``"name"`` key (effectDef entries) are left untouched.
        """
        if isinstance(obj, dict):
            for key in list(obj):
                val = obj[key]
                if (isinstance(val, dict)
                        and 'type' in val and 'defaultValue' in val
                        and 'name' not in val and 'keyframes' not in val):
                    obj[key] = val['defaultValue']
                else:
                    Project._flatten_parameters(val)
        elif isinstance(obj, list):
            for item in obj:
                Project._flatten_parameters(item)

    def save(self) -> None:
        """Write the current project state to disk.

        Matches Camtasia's ``NSJSONSerialization`` JSON formatting to
        avoid parser crashes with ``.trec`` screen recordings.
        """
        import re

        self._flatten_parameters(self._data)

        # Step 1: Standard pretty-print, preserving extreme floats
        # Python converts -1.79769e+308 to -inf during json.loads, then
        # json.dumps writes -Infinity which Camtasia cannot parse.
        text = json.dumps(self._data, indent=2, ensure_ascii=False,
                          allow_nan=True)
        # Replace -Infinity/Infinity/NaN with the original extreme values
        text = text.replace('-Infinity', '-1.79769313486232e+308')
        text = text.replace('Infinity', '1.79769313486232e+308')
        text = text.replace('NaN', '0.0')

        # Step 2: Add space before colon (NSJSONSerialization style)
        # "key": value  ->  "key" : value
        text = re.sub(r'"(\s*):', r'" :', text)

        # Step 3: Collapse scalar arrays to single lines
        def _collapse(m: re.Match) -> str:
            items = re.findall(
                r'-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null',
                m.group(0))
            return '[' + ', '.join(items) + ']'

        text = re.sub(
            r'\[\s*(?:-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null)'
            r'(?:,\s*(?:-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null))*'
            r'\s*\]',
            _collapse, text, flags=re.DOTALL,
        )

        # Step 4: Expand empty objects to multi-line with proper indentation
        def _expand_empty(m: re.Match) -> str:
            indent = m.group(1)
            return '{\n' + indent + '  ' + '}'
        text = re.sub(r'\{\}(?=\n(\s*))', _expand_empty, text)

        # Step 5: Add trailing space after commas at end of lines
        text = re.sub(r',\n', ', \n', text)

        with self._project_file.open(mode='wt', encoding=self._encoding) as handle:
            handle.write(text)
            handle.write('\n')

    # ------------------------------------------------------------------
    # L2 convenience methods
    # ------------------------------------------------------------------

    _EXTENSION_TYPE_MAP: dict[str, MediaType] = {
        '.png': MediaType.Image, '.jpg': MediaType.Image,
        '.jpeg': MediaType.Image, '.gif': MediaType.Image,
        '.bmp': MediaType.Image, '.tiff': MediaType.Image,
        '.wav': MediaType.Audio, '.mp3': MediaType.Audio,
        '.m4a': MediaType.Audio, '.aac': MediaType.Audio,
        '.mov': MediaType.Video, '.mp4': MediaType.Video,
        '.trec': MediaType.Video, '.avi': MediaType.Video,
    }

    def import_media(self, file_path: Path | str, **kwargs: Any) -> Media:
        """Import a media file into the project's source bin.

        Detects media type from the file extension and passes appropriate
        defaults so that pymediainfo is not required.

        Args:
            file_path: Path to the media file.
            **kwargs: Additional overrides forwarded to
                :meth:`MediaBin.import_media`.

        Returns:
            The newly created Media entry.

        Raises:
            ValueError: Unknown file extension.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        media_type = kwargs.pop('media_type', None) or self._EXTENSION_TYPE_MAP.get(suffix)
        if media_type is None:
            raise ValueError(f"Cannot determine media type for extension '{suffix}'")

        if media_type == MediaType.Image:
            kwargs.setdefault('duration', 1)
            if 'width' not in kwargs or 'height' not in kwargs:
                w, h = _probe_image_dimensions(path)
                kwargs.setdefault('width', w)
                kwargs.setdefault('height', h)
        elif media_type == MediaType.Audio and 'duration' not in kwargs:
            kwargs['duration'] = _probe_audio_duration(path, kwargs.get('sample_rate', 44100))
        elif media_type == MediaType.Video and 'duration' not in kwargs:
            kwargs['duration'] = _probe_video_duration(path)
        return self.media_bin.import_media(path, media_type=media_type, **kwargs)

    def total_duration_seconds(self) -> float:
        """Total timeline duration in seconds.

        Returns:
            Duration in seconds, delegated to the timeline.
        """
        return self.timeline.total_duration_seconds()

    def find_media_by_name(self, name: str) -> Media | None:
        """Search the source bin for media whose filename stem matches *name*.

        Args:
            name: Filename stem to match (case-sensitive).

        Returns:
            The first matching Media, or None.
        """
        for media in self.media_bin:
            if media.identity == name:
                return media
        return None

    def find_media_by_suffix(self, suffix: str) -> list[Media]:
        """Return all media entries whose source path ends with *suffix*.

        Args:
            suffix: Extension or suffix to match (e.g. ``'.png'``).

        Returns:
            List of matching Media entries.
        """
        return [m for m in self.media_bin if str(m.source).endswith(suffix)]

    def add_gradient_background(
        self,
        duration_seconds: float,
        color0: tuple[float, float, float, float] = (0.16, 0.16, 0.16, 1.0),
        color1: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        track_index: int = 1,
    ) -> Any:
        """Create a gradient shader background on the specified track.

        Adds a sourceBin entry for the gradient shader and places a VMFile
        clip on the given track.

        Args:
            duration_seconds: How long the background should last.
            color0: First RGBA gradient colour.
            color1: Second RGBA gradient colour.
            track_index: Track index to place the clip on (default 1).

        Returns:
            The created clip.
        """
        import datetime
        import time as _time

        width = int(self._data.get('width', 1920))
        height = int(self._data.get('height', 1080))
        media_id = self.media_bin.next_id()
        timestamp = datetime.datetime.now()
        ts_str = f"{timestamp.year}{timestamp.month:02}{timestamp.day:02}T{timestamp.hour:02}{timestamp.minute:02}{timestamp.second:02}"
        shader_name = f"gradient-bg-{media_id}.tscshadervid"
        src_path = f"./media/{_time.time()}/{shader_name}"

        source_entry: dict[str, Any] = {
            "id": media_id,
            "src": src_path,
            "rect": [0, 0, width, height],
            "lastMod": ts_str,
            "loudnessNormalization": True,
            "sourceTracks": [{
                "range": [0, 9223372036854775807],
                "type": 0,
                "editRate": 30,
                "trackRect": [0, 0, width, height],
                "sampleRate": 30,
                "bitDepth": 32,
                "numChannels": 0,
                "integratedLUFS": 100.0,
                "peakLevel": -1.0,
                "tag": 0,
                "metaData": f"{shader_name};",
                "parameters": {},
            }],
            "effectDef": [
                {"name": "Color0", "type": "Color",
                 "defaultValue": list(color0),
                 "scalingType": 3, "unitType": 0, "userInterfaceType": 6},
                {"name": "Color1", "type": "Color",
                 "defaultValue": list(color1),
                 "scalingType": 3, "unitType": 0, "userInterfaceType": 6},
                {"name": "sourceFileType", "type": "string",
                 "defaultValue": "tscshadervid",
                 "maxValue": "", "minValue": "",
                 "scalingType": 0, "unitType": 0, "userInterfaceType": 0},
            ],
            "metadata": {"timeAdded": timestamp.strftime("%Y%m%dT%H%M%S.%f")},
        }
        self.media_bin.add_media_entry(source_entry)

        dur_ticks = seconds_to_ticks(duration_seconds)
        track = self.timeline.tracks[track_index]

        def _color_params(prefix: str, rgba: tuple[float, float, float, float]) -> dict:
            return {
                f"{prefix}-red": {"type": "double", "defaultValue": rgba[0], "interp": "linr"},
                f"{prefix}-green": {"type": "double", "defaultValue": rgba[1], "interp": "linr"},
                f"{prefix}-blue": {"type": "double", "defaultValue": rgba[2], "interp": "linr"},
                f"{prefix}-alpha": {"type": "double", "defaultValue": rgba[3], "interp": "linr"},
            }

        source_effect = {
            "effectName": "SourceEffect",
            "bypassed": False,
            "category": "",
            "parameters": {
                **_color_params("Color0", color0),
                **_color_params("Color1", color1),
                "sourceFileType": "tscshadervid",
            },
        }

        return track.add_clip(
            'VMFile', media_id, 0, dur_ticks,
            attributes={"ident": shader_name.replace(".tscshadervid", "")},
            sourceEffect=source_effect,
        )

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
