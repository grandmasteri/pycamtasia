"""Media bin management for Camtasia projects.

Wraps the ``sourceBin`` JSON array in a project file, providing typed access
to imported media entries (video, image, audio).
"""
from __future__ import annotations

import datetime
from fractions import Fraction
import json
from pathlib import Path
import shutil
import subprocess
from typing import TYPE_CHECKING, Any
import warnings

from camtasia.types import MediaType

if TYPE_CHECKING:
    from collections.abc import Iterator

# Alias builtin sorted() so the MediaBin.sorted() method can use it.
builtins_sorted = sorted

# Shader/Lottie assets use INT64_MAX to signal unbounded duration.
_INT64_MAX = 9223372036854775807


class Media:
    """A single media entry from the project's source bin.

    Wraps one element of the ``sourceBin`` JSON array.

    Args:
        data: The raw sourceBin dict for this media item.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def source(self) -> Path:
        """Relative path to the media file within the project bundle."""
        return Path(self._data["src"])

    @property
    def identity(self) -> str:
        """Filename stem of the source path."""
        return self.source.stem

    @property
    def type(self) -> MediaType | None:
        """Media type derived from the first source track."""
        if not self._data.get('sourceTracks'):
            return None
        return MediaType(self._data["sourceTracks"][0]["type"])

    @property
    def rect(self) -> tuple[int | float, ...]:
        """Native bounding rect as ``(x, y, width, height)``."""
        return tuple(self._data["rect"])

    @property
    def dimensions(self) -> tuple[int, int]:
        """Native dimensions as ``(width, height)`` extracted from *rect*."""
        r = self._data["rect"]
        return (int(r[2]), int(r[3]))

    @property
    def range(self) -> tuple[int, int]:
        """Start and stop values from the first source track.

        Returns:
            A ``(start, stop)`` tuple of raw integer values.
        """
        if not self._data.get('sourceTracks'):
            return (0, 0)
        r = self._data["sourceTracks"][0]["range"]
        return (int(r[0]), int(r[1]))

    @property
    def last_modification(self) -> datetime.datetime:
        """Timestamp of last modification (parsed from ``lastMod``)."""
        return datetime.datetime.strptime(self._data["lastMod"], "%Y%m%dT%H%M%S")

    @property
    def duration_seconds(self) -> float | None:
        """Return the source media duration in seconds, or None if unavailable.

        Shader and Lottie assets use INT64_MAX as their range end to signal
        unbounded/infinite duration; this method returns ``None`` for those.
        """
        for st in self._data.get('sourceTracks', []):
            if st.get('type') == 0:  # video track
                range_val = st.get('range', [0, 0])
                edit_rate = float(Fraction(str(st.get('editRate', 1))))
                if edit_rate > 0 and len(range_val) >= 2:
                    if range_val[1] >= _INT64_MAX:
                        return None # pragma: no cover
                    return (range_val[1] - range_val[0]) / edit_rate  # type: ignore[no-any-return]
        for st in self._data.get('sourceTracks', []):
            if st.get('type') == 2:  # audio track
                range_val = st.get('range', [0, 0])
                edit_rate = float(Fraction(str(st.get('editRate', 1))))
                if edit_rate > 0 and len(range_val) >= 2:
                    if range_val[1] >= _INT64_MAX:
                        return None # pragma: no cover
                    return (range_val[1] - range_val[0]) / edit_rate  # type: ignore[no-any-return]
        for st in self._data.get('sourceTracks', []):
            if st.get('type') == 1:  # image
                return None
        return None

    @property
    def source_tracks(self) -> list[dict[str, Any]]:
        """Raw source track metadata dicts."""
        return self._data.get('sourceTracks', [])  # type: ignore[no-any-return]

    @property
    def video_edit_rate(self) -> int | str | None:
        """Edit rate of the first video source track, or None."""
        for st in self.source_tracks:
            if st.get('type') == 0:
                return st.get('editRate')
        return None

    @property
    def id(self) -> int:
        """Unique integer ID referenced by clips via ``src``."""
        return int(self._data["id"])

    def rename(self, new_name: str) -> None:
        """Rename this media entry by updating the filename stem in ``src``.

        The directory portion and extension are preserved; only the stem
        (the ``identity``) changes.

        Args:
            new_name: The new filename stem (without extension).
        """
        src = Path(self._data["src"])
        self._data["src"] = str(src.with_name(new_name + src.suffix))

    def create_proxy(self, proxy_path: Path) -> None:
        """Set a proxy file path on this media entry.

        Args:
            proxy_path: Path to the proxy media file.
        """
        self._data.setdefault("metadata", {})["proxyPath"] = str(proxy_path)

    def delete_proxy(self) -> None:
        """Remove the proxy path from this media entry."""
        meta = self._data.get("metadata")
        if meta is not None:
            meta.pop("proxyPath", None)

    def reverse(self) -> None:
        """Mark this media entry as reversed.

        Sets ``metadata.reversed`` to ``True`` and adds a reversed variant
        reference to the source tracks.
        """
        self._data.setdefault("metadata", {})["reversed"] = True
        for st in self._data.get("sourceTracks", []):
            st.setdefault("variants", [])
            if not any(v.get("type") == "reversed" for v in st["variants"]):
                st["variants"].append({"type": "reversed", "src": self._data["src"]})

    @property
    def zoom_metadata(self) -> dict[str, str]:
        """Zoom meeting metadata (meeting_id, host, topic, date).

        Returns:
            A dict with the four Zoom fields, empty strings for unset keys.
        """
        meta = self._data.get("metadata", {}).get("zoom", {})
        return {
            "meeting_id": meta.get("meeting_id", ""),
            "host": meta.get("host", ""),
            "topic": meta.get("topic", ""),
            "date": meta.get("date", ""),
        }

    @zoom_metadata.setter
    def zoom_metadata(self, value: dict[str, str]) -> None:
        """Set Zoom meeting metadata.

        Args:
            value: Dict with any of meeting_id, host, topic, date.
        """
        self._data.setdefault("metadata", {})["zoom"] = {
            "meeting_id": value.get("meeting_id", ""),
            "host": value.get("host", ""),
            "topic": value.get("topic", ""),
            "date": value.get("date", ""),
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Media):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f'Media(id={self.id}, identity={self.identity!r}, type={self.type.name if self.type is not None else "unknown"})'


class MediaBin:
    """The project's source-bin — a collection of imported media.

    Wraps the ``sourceBin`` JSON array.  Mutations go directly to the
    underlying list so that ``project.save()`` persists changes.

    Args:
        media_bin_data: The ``sourceBin`` list from the project dict.
        root_path: Path to the root directory of the ``.cmproj`` bundle.
        project: Optional project reference for whole-project ID scanning.
    """

    def __init__(self, media_bin_data: list[dict[str, Any]], root_path: Path, project: Any = None) -> None:
        self._data = media_bin_data
        self._root_path = root_path
        self._project = project

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f'MediaBin(count={len(self)})'

    def __iter__(self) -> Iterator[Media]:
        """Iterate over all :class:`Media` entries in the bin."""
        for record in self._data:
            yield Media(record)

    def __getitem__(self, media_id: int) -> Media:
        """Look up a media entry by its integer ID.

        Args:
            media_id: The ``id`` field of the desired media.

        Returns:
            The matching :class:`Media` instance.

        Raises:
            KeyError: No media with the given ID exists.
        """
        for media in self:
            if media.id == media_id:
                return media
        available = sorted(m.id for m in self)
        raise KeyError(f"No media with id {media_id}. Available IDs: {available}")

    def find_by_type(self, media_type: MediaType) -> list[Media]:
        """Find all media entries of a specific type."""
        return [m for m in self if m.type == media_type]

    @property
    def audio_files(self) -> list[Media]:
        """All audio media entries."""
        return self.find_by_type(MediaType.Audio)

    @property
    def video_files(self) -> list[Media]:
        """All video media entries."""
        return self.find_by_type(MediaType.Video)

    @property
    def image_files(self) -> list[Media]:
        """All image media entries."""
        return self.find_by_type(MediaType.Image)

    def unused_media(self, timeline: Any) -> list[Media]:
        """Return media entries not referenced by any clip on *timeline*.

        A media entry is considered "used" if any clip's ``src`` field
        matches the entry's ``id``.

        Args:
            timeline: A timeline object with an ``all_clips()`` method.

        Returns:
            List of :class:`Media` entries not referenced on the timeline.
        """
        used_ids = {c.source_id for c in timeline.all_clips() if c.source_id is not None}
        return [m for m in self if m.id not in used_ids]

    def delete_unused(self, timeline: Any) -> list[str]:
        """Remove media entries not referenced by any clip on *timeline*.

        Args:
            timeline: A timeline object with an ``all_clips()`` method.

        Returns:
            List of identity names of the removed entries.
        """
        unused = self.unused_media(timeline)
        names = [m.identity for m in unused]
        for m in unused:
            del self[m.id]
        return names

    def add_to_library(self, media: Media, library: Any) -> Any:
        """Bridge a media entry into a library as an asset.

        Imports the library module at call time to avoid circular dependencies.

        Args:
            media: The :class:`Media` entry to add.
            library: A :class:`~camtasia.library.Library` instance.

        Returns:
            The :class:`~camtasia.library.LibraryAsset` created.
        """

        return library.add_asset(media._data, media.identity)

    def sorted(self, *, key: str = 'name', reverse: bool = False) -> list[Media]:
        """Return media entries sorted by the given key.

        Args:
            key: Sort key — one of ``'name'``, ``'duration'``, ``'width'``,
                ``'height'``, ``'date'``.
            reverse: If ``True``, sort in descending order.

        Returns:
            A new sorted list of :class:`Media` entries.

        Raises:
            ValueError: *key* is not a recognised sort key.
        """
        key_funcs: dict[str, Any] = {
            'name': lambda m: m.identity.lower(),
            'duration': lambda m: m.duration_seconds or 0.0,
            'width': lambda m: m.dimensions[0],
            'height': lambda m: m.dimensions[1],
            'date': lambda m: m.last_modification,
        }
        if key not in key_funcs:
            raise ValueError(f"Invalid sort key {key!r}. Valid keys: {', '.join(key_funcs)}")
        return builtins_sorted(self, key=key_funcs[key], reverse=reverse)

    def import_folder(
        self,
        folder_path: Path | str,
        *,
        recursive: bool = False,
        extensions: tuple[str, ...] = ('.mp4', '.mov', '.png', '.jpg', '.jpeg', '.wav', '.mp3', '.m4a'),
        media_type: MediaType | None = None,
    ) -> list[Media]:
        """Batch-import all matching files from a directory.

        Args:
            folder_path: Directory to scan.
            recursive: If ``True``, scan subdirectories as well.
            extensions: File extensions to include (case-insensitive).
            media_type: Optional explicit media type applied to all files.
                Useful when ``pymediainfo`` is not available and all files
                share a known kind (e.g. a batch of PNG slides).

        Returns:
            List of newly imported :class:`Media` entries.
        """
        folder_path = Path(folder_path)
        pattern = '**/*' if recursive else '*'
        ext_lower = {e.lower() for e in extensions}
        paths = sorted(
            p for p in folder_path.glob(pattern)
            if p.is_file() and p.suffix.lower() in ext_lower
        )
        return self.import_many(paths, media_type=media_type)

    def import_many(
        self,
        paths: list[Path] | list[str],
        *,
        media_type: MediaType | None = None,
    ) -> list[Media]:
        """Import multiple media files.

        Args:
            paths: List of file paths to import.
            media_type: Optional explicit media type applied to all files.
                Useful when ``pymediainfo`` is not available and all files
                share a known kind (e.g. a batch of PNG slides).

        Returns:
            List of newly imported :class:`Media` entries.
        """
        return [self.import_media(Path(p), media_type=media_type) for p in paths]

    def __delitem__(self, media_id: int) -> None:
        """Remove a media entry by its integer ID.

        Args:
            media_id: The ``id`` of the media to remove.

        Raises:
            KeyError: No media with the given ID exists.
        """
        for idx, record in enumerate(self._data):
            if record["id"] == media_id:
                self._data.pop(idx)
                return
        raise KeyError(f"No media with id {media_id}")

    def next_id(self) -> int:
        """Return the next available media ID.

        When a project reference is available, scans the entire project
        (sourceBin IDs, clip IDs, timeline ID) to avoid collisions.
        Otherwise falls back to max sourceBin ID + 1.

        Returns:
            An integer suitable for a new sourceBin entry's ``id`` field.
            Returns ``1`` if no IDs exist.
        """
        if self._project is not None:
            return int(self._project.next_available_id)
        return int(max((rec["id"] for rec in self._data), default=0) + 1)

    def add_media_entry(self, entry: dict[str, Any]) -> Media:
        """Directly append a pre-built sourceBin dict.

        Useful when copying entries from a template project or constructing
        the JSON structure manually.

        Args:
            entry: A complete sourceBin dict (must contain at least ``id``).

        Returns:
            A :class:`Media` wrapper around the added entry.
        """
        self._data.append(entry)
        return Media(entry)

    def import_media(
        self,
        file_path: Path | str,
        *,
        validate_format: bool = False,
        auto_convert: bool = False,
        width: int | None = None,
        height: int | None = None,
        duration: int | None = None,
        media_type: MediaType | None = None,
        sample_rate: int | None = None,
        bit_depth: int | None = None,
        num_channels: int | None = None,
        edit_rate: int | None = None,
    ) -> Media:
        """Import a media file into the project.

        The file is copied into the project's ``media/`` directory.  Metadata
        can be supplied explicitly or, if *pymediainfo* is installed, parsed
        automatically from the file.

        Args:
            file_path: Path to the media file to import.
            width: Native width in pixels (required for video/image without pymediainfo).
            height: Native height in pixels (required for video/image without pymediainfo).
            duration: Duration value for the ``range`` field.  For images this
                defaults to ``1``; for audio it is the sample count.
            media_type: The :class:`MediaType`.  Required when pymediainfo is
                not available.
            sample_rate: Audio sample rate (e.g. 44100).
            bit_depth: Audio bit depth (e.g. 16).
            num_channels: Number of audio channels (e.g. 2).

        Returns:
            A :class:`Media` instance for the newly imported entry.

        Raises:
            FileNotFoundError: *file_path* does not exist.
            ValueError: Insufficient metadata and pymediainfo is not installed.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if validate_format:
            file_path = _validate_media_format(
                file_path, auto_convert=auto_convert,
            )

        # Try pymediainfo if explicit metadata not provided
        _detected_fps: float | None = None
        if media_type is None:
            track = _parse_with_pymediainfo(file_path)
            if track is None:
                raise ValueError(
                    f"Cannot determine media type for {file_path}. "
                    "Either install pymediainfo or pass media_type explicitly."
                )
            media_type = _get_media_type(track)
            width = width if width is not None else track.get("width")
            height = height if height is not None else track.get("height")
            sample_rate = sample_rate if sample_rate is not None else track.get("sampling_rate")
            if sample_rate is not None and not isinstance(sample_rate, int):
                try:
                    sample_rate = int(float(sample_rate))
                except (ValueError, TypeError):
                    sample_rate = None
            bit_depth = bit_depth if bit_depth is not None else track.get("bit_depth", 0)
            num_channels = num_channels if num_channels is not None else track.get("channel_s")
            if num_channels is not None:
                num_channels = int(str(num_channels).split('/')[0].strip())
            if duration is None:
                if media_type == MediaType.Audio:
                    duration = _compute_audio_duration(track, sample_rate)
                else:
                    fps = float(track.get('frame_rate', track.get('sampling_rate', 30)) or 30)
                    _detected_fps = fps
                    dur_val = track.get('duration')
                    if dur_val is None:
                        dur_val = 1000  # pragma: no cover  # defensive: pymediainfo rarely returns None for video duration
                    duration = round(float(dur_val) / 1000.0 * fps)

        # Copy file into project media directory. Use the timestamp plus a
        # numeric suffix on collision — rapid successive imports can produce
        # identical timestamps at microsecond resolution.
        timestamp = datetime.datetime.now()
        base = self._root_path / "media" / str(timestamp.timestamp())
        media_dir = base
        suffix = 1
        while media_dir.exists():
            media_dir = base.with_name(f'{base.name}_{suffix}')
            suffix += 1
        media_dir.mkdir(parents=True)
        dest = shutil.copy(file_path, media_dir)

        next_media_id = self.next_id()
        rel_path = './' + str(Path(dest).relative_to(self._root_path))
        filename = Path(dest).name

        if media_type == MediaType.Audio:
            json_data = _audio_track_to_json(
                next_media_id, rel_path, timestamp,
                sample_rate=sample_rate or 44100,
                bit_depth=bit_depth if bit_depth is not None else 16,
                num_channels=num_channels or 2,
                duration=duration or 0,
                filename=filename,
            )
        else:
            if media_type == MediaType.Image:
                _bit_depth = 0
                _edit_rate = 600
            else:
                _bit_depth = 24
                _edit_rate = round(_detected_fps) if _detected_fps else (edit_rate or 30)
            _sample_rate_val: int | str | None = _edit_rate if media_type == MediaType.Image else sample_rate
            if media_type == MediaType.Video and _sample_rate_val is None and _detected_fps is not None:
                _ntsc = {23.976: '24000/1001', 23.98: '24000/1001', 29.97: '30000/1001', 59.94: '60000/1001'}
                for _nfps, _nstr in _ntsc.items():
                    if abs(float(_detected_fps) - _nfps) < 0.01:
                        _sample_rate_val = _nstr
                        break
            json_data = _visual_track_to_json(
                next_media_id, rel_path, timestamp,
                media_type=media_type,
                width=width if width is not None else 0,
                height=height if height is not None else 0,
                duration=duration if duration is not None else 1,
                filename=filename,
                bit_depth=_bit_depth,
                edit_rate=_edit_rate,
                sample_rate=_sample_rate_val,
            )

        self._data.append(json_data)
        return self[next_media_id]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

# Maps ffprobe codec names to the file extensions they correspond to.
_CODEC_TO_EXTENSIONS: dict[str, set[str]] = {
    "mp3": {".mp3"},
    "aac": {".aac", ".m4a"},
    "vorbis": {".ogg"},
    "opus": {".opus", ".ogg"},
    "pcm_s16le": {".wav"},
    "pcm_s24le": {".wav"},
    "pcm_s32le": {".wav"},
    "pcm_f32le": {".wav"},
    "pcm_u8": {".wav"},
    "flac": {".flac"},
    "h264": {".mp4", ".m4v", ".mov"},
    "hevc": {".mp4", ".m4v", ".mov"},
    "vp9": {".webm"},
    "av1": {".mp4", ".webm"},
    "png": {".png"},
    "mjpeg": {".jpg", ".jpeg"},
}


def _detect_codec(file_path: Path) -> str | None:
    """Use ffprobe to detect the codec of the first stream.

    Returns the codec name string, or ``None`` if ffprobe is unavailable or fails.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "json",
                str(file_path),
            ],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        if streams:
            return streams[0].get("codec_name") # type: ignore[no-any-return]
        # Retry with audio stream
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name",
                "-of", "json",
                str(file_path),
            ],
            capture_output=True, text=True, timeout=10,
        )
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        if streams:
            return streams[0].get("codec_name") # type: ignore[no-any-return]
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass
    return None


def _validate_media_format(
    file_path: Path,
    *,
    auto_convert: bool = False,
) -> Path:
    """Check that the file's actual codec matches its extension.

    Emits a warning on mismatch.  If *auto_convert* is ``True``, converts
    the file to the format implied by its extension using ffmpeg and returns
    the path to the converted file.

    Returns the (possibly converted) file path.
    """
    codec = _detect_codec(file_path)
    if codec is None:
        return file_path

    ext = file_path.suffix.lower()
    expected_exts = _CODEC_TO_EXTENSIONS.get(codec)
    if expected_exts is None or ext in expected_exts:
        return file_path

    warnings.warn(
        f"Format mismatch: {file_path.name} has extension '{ext}' "
        f"but contains '{codec}' data (expected extensions: "
        f"{', '.join(sorted(expected_exts))})",
        UserWarning,
        stacklevel=3,
    )

    if not auto_convert:
        return file_path

    try:
        converted = file_path.with_suffix(f".converted{ext}")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(file_path), str(converted)],
            capture_output=True, timeout=60, check=True,
        )
        return converted
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
        return file_path


def _parse_with_pymediainfo(file_path: Path) -> dict[str, Any] | None:
    """Attempt to parse media metadata via pymediainfo.

    Returns:
        A track data dict, or ``None`` if pymediainfo is not installed or
        parsing fails.
    """
    try:
        from pymediainfo import MediaInfo  # type: ignore[import-untyped]
    except ImportError:
        return None

    try:
        media_info = MediaInfo.parse(file_path)
    except (RuntimeError, OSError):
        return None
    except Exception as exc:
        import warnings
        warnings.warn(
            f'Unexpected pymediainfo error ({type(exc).__name__}): {exc}',
            stacklevel=2,
        )
        return None

    if len(media_info.tracks) < 2:
        return None
    return media_info.tracks[1].to_data()  # type: ignore[no-any-return]


def _compute_audio_duration(track: dict[str, Any], sample_rate: int | None) -> int:
    """Return the audio duration as a sample count suitable for ``range``.

    For all audio formats, pymediainfo reports duration in milliseconds.
    We convert to sample counts via ``duration_ms * sample_rate / 1000``.
    """
    duration_ms = float(track.get("duration", 0) or 0)
    if not sample_rate or sample_rate <= 0:
        return 0  # Can't compute sample count without sample rate
    return round(duration_ms * sample_rate / 1000)


def _get_media_type(track: dict[str, Any]) -> MediaType:
    """Map a pymediainfo ``kind_of_stream`` value to :class:`MediaType`."""
    mapping = {
        "Image": MediaType.Image,
        "Video": MediaType.Video,
        "Audio": MediaType.Audio,
    }
    kind = track.get('kind_of_stream', '')
    if kind not in mapping:
        raise ValueError(f'Unsupported media stream type: {kind}')
    return mapping[kind]


def _visual_track_to_json(
    media_id: int,
    source_file: str,
    timestamp: datetime.datetime,
    *,
    media_type: MediaType,
    width: int,
    height: int,
    duration: int,
    edit_rate: int = 30,
    sample_rate: int | str | None = None,
    filename: str = "",
    bit_depth: int = 0,
) -> dict[str, Any]:
    """Build a sourceBin entry for a video or image track."""
    media_rect = [0, 0, width, height]
    return {
        "id": media_id,
        "src": source_file,
        "rect": media_rect,
        "lastMod": _datetime_to_str(timestamp),
        "loudnessNormalization": True,
        "sourceTracks": [
            {
                "range": [0, duration],
                "type": media_type.value,
                "editRate": edit_rate,
                "trackRect": media_rect,
                "sampleRate": sample_rate if sample_rate is not None else edit_rate,
                "bitDepth": bit_depth,
                "numChannels": 0,
                "integratedLUFS": 100.0,
                "peakLevel": -1.0,
                "tag": 0,
                "metaData": f"{filename};" if filename else "",
                "parameters": {},
            }
        ],
        "metadata": {"timeAdded": timestamp.strftime("%Y%m%dT%H%M%S.%f")},
    }


def _audio_track_to_json(
    media_id: int,
    source_file: str,
    timestamp: datetime.datetime,
    *,
    sample_rate: int,
    bit_depth: int,
    num_channels: int,
    duration: int,
    filename: str = "",
) -> dict[str, Any]:
    """Build a sourceBin entry for an audio track."""
    return {
        "id": media_id,
        "src": source_file,
        "rect": [0, 0, 0, 0],
        "lastMod": _datetime_to_str(timestamp),
        "loudnessNormalization": True,
        "sourceTracks": [
            {
                "range": [0, duration],
                "type": MediaType.Audio.value,
                "editRate": sample_rate,
                "trackRect": [0, 0, 0, 0],
                "sampleRate": sample_rate,
                "bitDepth": bit_depth,
                "numChannels": num_channels,
                "integratedLUFS": 100.0,
                "peakLevel": -1.0,
                "tag": 0,
                "metaData": f"{filename};" if filename else "",
                "parameters": {},
            }
        ],
        "metadata": {"timeAdded": timestamp.strftime("%Y%m%dT%H%M%S.%f")},
    }


def _datetime_to_str(dt: datetime.datetime) -> str:
    """Format a datetime as Camtasia's ``lastMod`` string.

    Format: ``YYYYMMDDTHHmmss``, e.g. ``20190606T103830``.
    """
    return f"{dt.year}{dt.month:02}{dt.day:02}T{dt.hour:02}{dt.minute:02}{dt.second:02}"
