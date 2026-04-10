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
from camtasia.validation import ValidationIssue


import subprocess as _sp


def _probe_media(path: Path) -> dict:
    """Probe media file for metadata. Uses pymediainfo if available, falls back to ffprobe.

    Returns a dict with available keys:
    - Images: ``width``, ``height``
    - Audio: ``duration_seconds``, ``sample_rate``, ``channels``, ``bit_depth``
    - Video: ``duration_seconds``, ``width``, ``height``, ``frame_rate``
    """
    try:
        from pymediainfo import MediaInfo  # type: ignore[import-untyped]
        info = MediaInfo.parse(path)
        result: dict = {}
        for track in info.tracks:
            if track.track_type == 'Video':
                result['width'] = track.width
                result['height'] = track.height
                if track.duration:
                    result['duration_seconds'] = track.duration / 1000.0
                if track.frame_rate:
                    result['frame_rate'] = float(track.frame_rate)
            elif track.track_type == 'Audio':
                if track.duration:
                    result['duration_seconds'] = track.duration / 1000.0
                if track.sampling_rate:
                    result['sample_rate'] = int(track.sampling_rate)
                if track.channel_s:
                    result['channels'] = int(track.channel_s)
                if track.bit_depth:
                    result['bit_depth'] = int(track.bit_depth)
            elif track.track_type == 'Image':
                result['width'] = track.width
                result['height'] = track.height
            elif track.track_type == 'General':
                if 'duration_seconds' not in result and track.duration:
                    result['duration_seconds'] = track.duration / 1000.0
        if result:
            result['_backend'] = 'pymediainfo'
            return result
    except ImportError:
        pass
    except Exception:
        pass
    return _probe_media_ffprobe(path)


def _probe_media_ffprobe(path: Path) -> dict:
    """Probe media file using ffprobe subprocess."""
    result: dict = {'_backend': 'ffprobe'}
    try:
        out = _sp.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'stream=width,height',
             '-of', 'csv=p=0', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        parts = out.stdout.strip().split(',')
        if len(parts) >= 2 and parts[0] and parts[1]:
            result['width'] = int(parts[0])
            result['height'] = int(parts[1])
    except Exception:
        pass
    try:
        out = _sp.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        val = out.stdout.strip()
        if val:
            result['duration_seconds'] = float(val)
    except Exception:
        pass
    return result


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

    def validate(self) -> list[ValidationIssue]:
        """Check for common project issues.

        Returns:
            A list of :class:`ValidationIssue` instances (may be empty).
        """
        issues: list[ValidationIssue] = []
        bin_ids: set[int] = set()

        for media in self.media_bin:
            bin_ids.add(media.id)
            raw = media._data

            # Zero-range audio
            if media.type == MediaType.Audio:
                r = raw['sourceTracks'][0]['range']
                if r == [0, 0]:
                    issues.append(ValidationIssue('error', f'Zero-range audio source: {media.source}', media.id))

            # Zero-dimension image
            if media.type == MediaType.Image:
                if raw['rect'] == [0, 0, 0, 0]:
                    issues.append(ValidationIssue('error', f'Zero-dimension image source: {media.source}', media.id))

            # Missing source file
            src_path = self._file_path / media.source if self._file_path.is_dir() else self._file_path.parent / media.source
            if not src_path.exists():
                issues.append(ValidationIssue('warning', f'Missing source file: {media.source}', media.id))

        # Collect all clip source references
        referenced_ids: set[int] = set()
        for clip in self.timeline.all_clips():
            if clip.source_id is not None:
                referenced_ids.add(clip.source_id)
                if clip.source_id not in bin_ids:
                    issues.append(ValidationIssue('error', f'Clip references missing source ID {clip.source_id}', clip.source_id))

        # Orphaned media
        for media in self.media_bin:
            if media.id not in referenced_ids:
                issues.append(ValidationIssue('warning', f'Orphaned media not used by any clip: {media.source}', media.id))

        return issues

    def save(self) -> None:
        """Write the current project state to disk.

        Matches Camtasia's ``NSJSONSerialization`` JSON formatting to
        avoid parser crashes with ``.trec`` screen recordings.
        """
        import re
        import sys

        for issue in self.validate():
            print(f'[{issue.level}] {issue.message}', file=sys.stderr)

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
        '.tscshadervid': MediaType.Video,
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

        meta = _probe_media(path)

        if media_type == MediaType.Image:
            kwargs.setdefault('duration', 1)
            kwargs.setdefault('width', meta.get('width', 1920))
            kwargs.setdefault('height', meta.get('height', 1080))
        elif media_type == MediaType.Audio:
            sr = meta.get('sample_rate', kwargs.get('sample_rate', 44100))
            kwargs.setdefault('sample_rate', sr)
            if meta.get('_backend') == 'pymediainfo':
                kwargs.setdefault('num_channels', meta.get('channels', 2))
                kwargs.setdefault('bit_depth', meta.get('bit_depth', 16))
            if 'duration' not in kwargs:
                dur_secs = meta.get('duration_seconds')
                kwargs['duration'] = int(dur_secs * sr) if dur_secs else sr * 60
        elif media_type == MediaType.Video and 'duration' not in kwargs:
            if suffix == '.tscshadervid':
                # Shaders have infinite duration and no audio
                kwargs['duration'] = 9223372036854775807  # MAX_INT64
                kwargs.setdefault('width', 1920)
                kwargs.setdefault('height', 1080)
                kwargs.setdefault('sample_rate', 30)
                kwargs.setdefault('num_channels', 0)
                kwargs.setdefault('bit_depth', 32)
            else:
                dur_secs = meta.get('duration_seconds')
                kwargs['duration'] = int(dur_secs * 30) if dur_secs else 30 * 60
        return self.media_bin.import_media(path, media_type=media_type, **kwargs)

    def total_duration_seconds(self) -> float:
        """Total timeline duration in seconds.

        Returns:
            Duration in seconds, delegated to the timeline.
        """
        return self.timeline.total_duration_seconds()

    def export_frame(
        self,
        video_path: Path | str,
        timestamp_seconds: float,
        output_path: Path | str | None = None,
    ) -> Path:
        """Extract a single frame from a video file as a PNG image.

        Uses ffmpeg to extract the frame. If output_path is None,
        saves to the project's media directory with an auto-generated name.

        Args:
            video_path: Path to the video file (.trec, .mp4, etc.)
            timestamp_seconds: Time position to extract the frame from.
            output_path: Where to save the PNG. Defaults to project media dir.

        Returns:
            Path to the extracted PNG file.

        Raises:
            RuntimeError: If ffmpeg exits with a non-zero return code.
        """
        video_path = Path(video_path)
        if output_path is None:
            media_dir = self._file_path / 'media'
            media_dir.mkdir(parents=True, exist_ok=True)
            stem = video_path.stem
            output_path = media_dir / f'{stem}_frame_{timestamp_seconds:.3f}s.png'
        else:
            output_path = Path(output_path)

        result = _sp.run(
            ['ffmpeg', '-ss', str(timestamp_seconds), '-i', str(video_path),
             '-frames:v', '1', '-q:v', '2', str(output_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f'ffmpeg failed (rc={result.returncode}): {result.stderr}')
        return output_path

    def export_frame_and_import(
        self,
        video_path: Path | str,
        timestamp_seconds: float,
    ) -> Media:
        """Extract a frame from video and import it into the project media bin.

        Args:
            video_path: Path to the video file.
            timestamp_seconds: Time position to extract the frame from.

        Returns:
            The newly created Media entry.
        """
        png_path = self.export_frame(video_path, timestamp_seconds)
        return self.import_media(png_path)

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
        existing = self.find_media_by_suffix('.tscshadervid')
        if existing:
            media_id = existing[0].id
            shader_name = existing[0].source.name
        else:
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
