"""Project loading, saving, and creation for Camtasia .cmproj bundles."""

from __future__ import annotations

import json
import shutil
import warnings
from contextlib import contextmanager
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any, Iterator

from camtasia.authoring_client import AuthoringClient
from camtasia.media_bin import Media, MediaBin, MediaType
from camtasia.timeline import Timeline
from camtasia.timing import EDIT_RATE, seconds_to_ticks
from camtasia.validation import ValidationIssue, _check_duplicate_clip_ids, _check_track_indices, _check_transition_references


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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Project):
            return NotImplemented
        return self._data == other._data

    @property
    def file_path(self) -> Path:
        """The full path to the Camtasia project."""
        return self._file_path

    @property
    def width(self) -> int:
        """Canvas width in pixels."""
        return self._data.get('width', 1920)

    @width.setter
    def width(self, value: int) -> None:
        """Set the canvas width in pixels."""
        self._data['width'] = value

    @property
    def height(self) -> int:
        """Canvas height in pixels."""
        return self._data.get('height', 1080)

    @height.setter
    def height(self, value: int) -> None:
        """Set the canvas height in pixels."""
        self._data['height'] = value

    @property
    def title(self) -> str:
        """Project title."""
        return self._data.get('title', '')

    @title.setter
    def title(self, value: str) -> None:
        self._data['title'] = value

    @property
    def description(self) -> str:
        """Project description."""
        return self._data.get('description', '')

    @description.setter
    def description(self, value: str) -> None:
        self._data['description'] = value

    @property
    def author(self) -> str:
        """Project author."""
        return self._data.get('author', '')

    @author.setter
    def author(self, value: str) -> None:
        self._data['author'] = value

    @property
    def target_loudness(self) -> float:
        """Target loudness in LUFS for audio normalization."""
        return self._data.get('targetLoudness', -18.0)

    @target_loudness.setter
    def target_loudness(self, value: float) -> None:
        self._data['targetLoudness'] = value

    @property
    def frame_rate(self) -> int:
        """Video frame rate."""
        return self._data.get('videoFormatFrameRate', 30)

    @frame_rate.setter
    def frame_rate(self, value: int) -> None:
        self._data['videoFormatFrameRate'] = value

    @property
    def sample_rate(self) -> int:
        """Audio sample rate."""
        return self._data.get('audioFormatSampleRate', 44100)

    @sample_rate.setter
    def sample_rate(self, value: int) -> None:
        self._data['audioFormatSampleRate'] = value

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

    @property
    def has_screen_recording(self) -> bool:
        """Whether the project contains any screen recording clips."""
        from camtasia.timeline.clips.group import Group
        for track in self.timeline.tracks:
            for clip in track.clips:
                if isinstance(clip, Group) and clip.is_screen_recording:
                    return True
        return False

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

        # Duplicate clip IDs
        issues.extend(_check_duplicate_clip_ids(self._data))

        # Track index consistency
        issues.extend(_check_track_indices(self._data))

        # Transition references
        issues.extend(_check_transition_references(self._data))

        return issues

    def save(self) -> None:
        """Write the current project state to disk.

        Matches Camtasia's ``NSJSONSerialization`` JSON formatting to
        avoid parser crashes with ``.trec`` screen recordings.
        """
        import re

        for issue in self.validate():
            message = f'[{issue.level}] {issue.message}'
            warnings.warn(message, stacklevel=2)

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
            supported = ', '.join(sorted(self._EXTENSION_TYPE_MAP))
            raise ValueError(
                f"Cannot determine media type for extension '{suffix}'. "
                f"Supported extensions: {supported}"
            )

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

    def import_shader(self, shader_path: str | Path) -> Media:
        """Import a .tscshadervid shader with effectDef parsing.

        Reads the shader JSON, converts effectDef entries (hex colors to
        RGBA floats), and sets sourceTracks metadata for Camtasia.
        Reuses existing media if already imported.
        """
        path = Path(shader_path)
        existing = self.find_media_by_name(path.stem)
        if existing is not None:
            return existing

        media = self.import_media(path)
        shader_data = json.loads(path.read_text())

        effect_def = []
        for entry in shader_data['effectDef']:
            name = entry['name']
            if entry.get('type') == 'Color':
                hex_str = entry['value']
                r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
                effect_def.append({
                    'name': name, 'type': 'Color',
                    'defaultValue': [r / 255, g / 255, b / 255, 1.0],
                    'scalingType': 3, 'unitType': 0, 'userInterfaceType': 6,
                })
            else:
                effect_def.append({
                    'name': name, 'type': entry['type'],
                    'defaultValue': entry.get('defaultValue', entry.get('value')),
                    'scalingType': 0,
                    'unitType': 1 if 'MidPoint' in name else 0,
                    'userInterfaceType': 0,
                })
        effect_def.append({
            'name': 'sourceFileType', 'type': 'string',
            'defaultValue': 'tscshadervid', 'maxValue': '', 'minValue': '',
            'scalingType': 0, 'unitType': 0, 'userInterfaceType': 0,
        })

        # Find the source bin entry and patch it
        for entry in self._data['sourceBin']:
            if entry['id'] == media.id:
                entry['effectDef'] = effect_def
                st = entry['sourceTracks'][0]
                st['editRate'] = 30
                st['sampleRate'] = 30
                st['bitDepth'] = 32
                break

        return media

    def import_trec(self, trec_path: str | Path) -> 'Media':
        """Import a .trec screen recording with full stream metadata.

        Uses pymediainfo to probe the multi-track container and build
        correct source bin entries with all stream metadata.

        Args:
            trec_path: Path to the .trec file.

        Returns:
            The Media entry.

        Raises:
            ImportError: pymediainfo not installed.
        """
        from camtasia.media_bin.trec_probe import probe_trec

        path = Path(trec_path)

        # Check if already imported
        existing = self.find_media_by_name(path.stem)
        if existing:
            return existing

        # Import the file (copies into project bundle)
        media = self.import_media(path)

        # Probe and apply accurate metadata
        probe_data = probe_trec(path)

        # Update the source bin entry with probed metadata
        for sb in self._data['sourceBin']:
            if sb['id'] == media.id:
                sb['rect'] = probe_data['rect']
                sb['sourceTracks'] = probe_data['sourceTracks']
                sb['lastMod'] = probe_data['lastMod']
                sb['loudnessNormalization'] = probe_data['loudnessNormalization']
                break

        return media

    def statistics(self) -> dict[str, Any]:
        """Return detailed project statistics.

        Returns a dict with:
        - total_tracks: int
        - empty_tracks: int
        - total_clips: int
        - clips_by_type: dict[str, int]
        - total_media: int
        - media_by_type: dict[str, int]
        - total_transitions: int
        - total_markers: int
        - duration_seconds: float
        - canvas: dict with width and height
        """
        clips_by_type: dict[str, int] = {}
        total_clips = 0
        total_transitions = 0
        total_markers = 0
        empty_tracks = 0

        for track in self.timeline.tracks:
            track_clips = list(track.clips)
            if not track_clips:
                empty_tracks += 1
            for clip in track_clips:
                total_clips += 1
                ct = clip.clip_type
                clips_by_type[ct] = clips_by_type.get(ct, 0) + 1
            total_transitions += len(list(track.transitions))
            total_markers += len(list(track.markers))

        total_markers += len(list(self.timeline.markers))

        media_by_type: dict[str, int] = {}
        for m in self.media_bin:
            mt = m.type.name if hasattr(m.type, 'name') else str(m.type)
            media_by_type[mt] = media_by_type.get(mt, 0) + 1

        return {
            'total_tracks': self.timeline.track_count,
            'empty_tracks': empty_tracks,
            'total_clips': total_clips,
            'clips_by_type': clips_by_type,
            'total_media': len(self.media_bin),
            'media_by_type': media_by_type,
            'total_transitions': total_transitions,
            'total_markers': total_markers,
            'duration_seconds': self.total_duration_seconds(),
            'canvas': {'width': self.width, 'height': self.height},
        }

    def info(self) -> dict[str, Any]:
        """Return comprehensive project information.

        Combines statistics, validation, and structural analysis
        into a single dict for debugging and inspection.
        """
        stats = self.statistics()
        issues = self.validate()
        structure = self.timeline.validate_structure()

        return {
            **stats,
            'validation_errors': [i.message for i in issues if i.level == 'error'],
            'validation_warnings': [i.message for i in issues if i.level == 'warning'],
            'structural_issues': structure,
            'has_screen_recording': self.has_screen_recording,
            'title': self.title,
            'author': self.author,
            'frame_rate': self.frame_rate,
            'sample_rate': self.sample_rate,
        }

    def compact(self) -> dict[str, int]:
        """Run all cleanup operations and validate.

        Removes orphaned media, empty tracks, and validates the result.

        Returns:
            Summary dict with counts of items cleaned.

        Raises:
            ValueError: If validation finds errors after cleanup.
        """
        from camtasia.operations.cleanup import compact_project
        result = compact_project(self)

        issues = self.validate()
        errors = [i for i in issues if i.level == 'error']
        if errors:
            raise ValueError(
                f'Validation errors after compact: '
                f'{[e.message for e in errors]}'
            )

        return result

    def summary(self) -> str:
        """Return a human-readable summary of the project."""
        lines = [
            f'Project: {self.file_path.name}',
            f'Canvas: {self.width}x{self.height}',
            f'Duration: {self.total_duration_seconds():.1f}s',
            f'Tracks: {self.timeline.track_count}',
            f'Media: {len(self.media_bin)} items',
        ]
        for track in self.timeline.tracks:
            clip_count = len(track)
            if clip_count > 0:
                types = set()
                for clip in track.clips:
                    types.add(clip.clip_type)
                lines.append(f'  Track {track.index} "{track.name}": {clip_count} clips ({", ".join(sorted(types))})')
            else:
                lines.append(f'  Track {track.index} "{track.name}": empty')
        return '\n'.join(lines)

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

            width = self.width
            height = self.height
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

    def add_progressive_disclosure(
        self,
        images: list[tuple[int, float]],
        start_seconds: float,
        fade_in: float = 0.5,
        track_prefix: str = 'Prog',
    ) -> list:
        """Place images on separate tracks so they accumulate visually.

        Each image gets its own track (named ``{track_prefix}-{i}``) and
        a fade-in animation.  All clips start at *start_seconds*; each
        clip's duration comes from the corresponding tuple.

        Args:
            images: ``[(source_id, duration_seconds), ...]``
            start_seconds: Timeline position for every clip.
            fade_in: Fade-in duration in seconds (applied to each clip).
            track_prefix: Name prefix for the created tracks.

        Returns:
            List of created clips.
        """
        clips = []
        for i, (source_id, duration_seconds) in enumerate(images):
            track = self.timeline.get_or_create_track(f'{track_prefix}-{i}')
            clip = track.add_image(source_id, start_seconds, duration_seconds)
            clip.fade_in(fade_in)
            clips.append(clip)
        return clips

    def add_four_corner_gradient(
        self,
        shader_path: str | Path,
        duration_seconds: float,
        track_name: str = 'Background',
    ) -> 'BaseClip':
        """Import and place a 4-corner animated gradient shader background.

        Reuses an existing ``.tscshadervid`` source if one is already in the
        media bin; otherwise imports from *shader_path*.

        Args:
            shader_path: Path to the ``.tscshadervid`` shader file.
            duration_seconds: How long the background clip should last.
            track_name: Name of the track to place the clip on.

        Returns:
            The created video clip.
        """
        existing = self.find_media_by_suffix('.tscshadervid')
        if existing:
            shader_id = existing[0].id
        else:
            shader_id = self.import_media(shader_path).id
        track = self.timeline.get_or_create_track(track_name)
        return track.add_video(shader_id, start_seconds=0, duration_seconds=duration_seconds)

    def add_voiceover_sequence(
        self,
        vo_files: list[str | Path],
        pauses: dict[str, float] | None = None,
        track_name: str = 'Audio',
    ) -> dict[str, dict]:
        """Import voiceover files and place them sequentially on an audio track.

        Args:
            vo_files: List of audio file paths to import and place.
            pauses: Optional mapping of filename to seconds of silence
                to insert after that clip.
            track_name: Name of the track to place clips on.

        Returns:
            Dict mapping each filename to ``{'start': float,
            'duration': float, 'clip': AMFile}``.
        """
        pauses = pauses or {}
        track = self.timeline.get_or_create_track(track_name)
        cursor = 0.0
        result: dict[str, dict] = {}

        for vo_file in vo_files:
            path = Path(vo_file)
            media = self.import_media(path)
            meta = _probe_media(path)
            dur = meta.get('duration_seconds', 1.0)
            clip = track.add_audio(media.id, cursor, dur)
            result[path.name] = {'start': cursor, 'duration': dur, 'clip': clip}
            cursor += dur + pauses.get(path.name, 0.0)

        return result

    def copy_to(self, dest_path: str | Path) -> 'Project':
        """Copy this project to a new location.

        Args:
            dest_path: Destination path for the .cmproj copy.

        Returns:
            The loaded Project at the new location.
        """
        dst = Path(dest_path)
        if dst.exists():
            raise FileExistsError(f'Destination already exists: {dst}')
        shutil.copytree(self.file_path, dst)
        return load_project(str(dst))

    @property
    def _project_file(self) -> Path:
        """Locate the .tscproj JSON file within the project bundle."""
        if self.file_path.is_dir():
            for file in self.file_path.iterdir():
                if file.is_file() and file.suffix == '.tscproj':
                    return file
            raise FileNotFoundError(
                f"No .tscproj file found in '{self.file_path}'. "
                f"Ensure the path points to a valid .cmproj bundle."
            )
        return self.file_path

    def __repr__(self) -> str:
        return (f'Project(path={self.file_path.name!r}, '
                f'{self.width}x{self.height}, '
                f'tracks={self.timeline.track_count}, '
                f'duration={self.total_duration_seconds():.1f}s)')


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
