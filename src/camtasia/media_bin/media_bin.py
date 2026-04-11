"""Media bin management for Camtasia projects.

Wraps the ``sourceBin`` JSON array in a project file, providing typed access
to imported media entries (video, image, audio).
"""
from __future__ import annotations

import datetime
import shutil
from enum import Enum
from pathlib import Path
from typing import Any, Iterator


class MediaType(Enum):
    """Camtasia media type codes used in ``sourceBin/sourceTracks/type``."""

    Video = 0
    Image = 1
    Audio = 2


class IntEncodedTime:
    """Integer-encoded time used in ``sourceTracks[].range``.

    The three least significant digits represent milliseconds; everything
    above represents whole seconds.  This encoding is specific to Camtasia's
    sourceTracks range fields and is **not** interchangeable with tick-based
    timeline timing.

    Args:
        encoded_time: The raw integer from the ``range`` array.
    """

    def __init__(self, encoded_time: int) -> None:
        self._seconds, self._milliseconds = divmod(encoded_time, 1000)

    @property
    def seconds(self) -> int:
        """Whole-second component."""
        return self._seconds

    @property
    def milliseconds(self) -> int:
        """Millisecond component (0–999)."""
        return self._milliseconds

    def to_frame(self, frame_rate: int = 30) -> int:
        """Convert to a frame index at the given frame rate.

        Args:
            frame_rate: Frames per second (default 30).

        Returns:
            Zero-based frame index.
        """
        return int((self.seconds + self.milliseconds / 1000) * frame_rate)

    def __str__(self) -> str:
        return f"{self.seconds}s{self.milliseconds}ms"

    def __repr__(self) -> str:
        return f"IntEncodedTime(encoded_time={self.seconds * 1000 + self.milliseconds})"


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
    def type(self) -> MediaType:
        """Media type derived from the first source track."""
        return MediaType(self._data["sourceTracks"][0]["type"])

    @property
    def rect(self) -> tuple[int, int, int, int]:
        """Native bounding rect as ``(x, y, width, height)``."""
        return tuple(self._data["rect"])  # type: ignore[return-value]

    @property
    def dimensions(self) -> tuple[int, int]:
        """Native dimensions as ``(width, height)`` extracted from *rect*."""
        r = self._data["rect"]
        return (r[2], r[3])

    @property
    def range(self) -> tuple[IntEncodedTime, IntEncodedTime]:
        """Start and stop times from the first source track.

        Returns:
            A ``(start, stop)`` tuple of :class:`IntEncodedTime` values.
        """
        r = self._data["sourceTracks"][0]["range"]
        return (IntEncodedTime(r[0]), IntEncodedTime(r[1]))

    @property
    def last_modification(self) -> datetime.datetime:
        """Timestamp of last modification (parsed from ``lastMod``)."""
        return datetime.datetime.strptime(self._data["lastMod"], "%Y%m%dT%H%M%S")

    @property
    def duration_seconds(self) -> float | None:
        """Return the source media duration in seconds, or None if unavailable."""
        for st in self._data.get('sourceTracks', []):
            if st.get('type') == 0:  # video track
                range_val = st.get('range', [0, 0])
                edit_rate = st.get('editRate', 1)
                if edit_rate > 0 and len(range_val) >= 2:
                    return range_val[1] / edit_rate
        for st in self._data.get('sourceTracks', []):
            if st.get('type') == 2:  # audio track
                range_val = st.get('range', [0, 0])
                edit_rate = st.get('editRate', 1)
                if edit_rate > 0 and len(range_val) >= 2:
                    return range_val[1] / edit_rate
        return None

    @property
    def id(self) -> int:
        """Unique integer ID referenced by clips via ``src``."""
        return self._data["id"]

    def __repr__(self) -> str:
        return f'Media(id={self.id}, source="{self.source}")'


class MediaBin:
    """The project's source-bin — a collection of imported media.

    Wraps the ``sourceBin`` JSON array.  Mutations go directly to the
    underlying list so that ``project.save()`` persists changes.

    Args:
        media_bin_data: The ``sourceBin`` list from the project dict.
        root_path: Path to the root directory of the ``.cmproj`` bundle.
    """

    def __init__(self, media_bin_data: list[dict[str, Any]], root_path: Path) -> None:
        self._data = media_bin_data
        self._root_path = root_path

    def __len__(self) -> int:
        return len(self._data)

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
        raise KeyError(f"No media with id {media_id}")

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
        """Return the next available media ID (max existing + 1).

        Returns:
            An integer suitable for a new sourceBin entry's ``id`` field.
            Returns ``1`` if the bin is empty.
        """
        return max((rec["id"] for rec in self._data), default=0) + 1

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
        file_path: Path,
        *,
        width: int | None = None,
        height: int | None = None,
        duration: int | None = None,
        media_type: MediaType | None = None,
        sample_rate: int | None = None,
        bit_depth: int | None = None,
        num_channels: int | None = None,
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

        # Try pymediainfo if explicit metadata not provided
        if media_type is None:
            track = _parse_with_pymediainfo(file_path)
            if track is None:
                raise ValueError(
                    f"Cannot determine media type for {file_path}. "
                    "Either install pymediainfo or pass media_type explicitly."
                )
            media_type = _get_media_type(track)
            width = width or track.get("width")
            height = height or track.get("height")
            duration = duration or int(track.get("duration", 1))
            sample_rate = sample_rate or track.get("sampling_rate")
            bit_depth = bit_depth or track.get("bit_depth", 0)
            num_channels = num_channels or track.get("channel_s")

        # Copy file into project media directory
        timestamp = datetime.datetime.now()
        media_dir = self._root_path / "media" / str(timestamp.timestamp())
        media_dir.mkdir(parents=True)
        dest = shutil.copy(file_path, media_dir)

        next_media_id = self.next_id()
        rel_path = './' + str(Path(dest).relative_to(self._root_path))
        filename = Path(dest).name

        if media_type == MediaType.Audio:
            json_data = _audio_track_to_json(
                next_media_id, rel_path, timestamp,
                sample_rate=sample_rate or 44100,
                bit_depth=bit_depth or 16,
                num_channels=num_channels or 2,
                duration=duration or 0,
                filename=filename,
            )
        else:
            json_data = _visual_track_to_json(
                next_media_id, rel_path, timestamp,
                media_type=media_type,
                width=width or 0,
                height=height or 0,
                duration=duration if duration is not None else 1,
                filename=filename,
            )

        self._data.append(json_data)
        return self[next_media_id]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

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
    except Exception:
        return None

    if len(media_info.tracks) < 2:
        return None
    return media_info.tracks[1].to_data()


def _get_media_type(track: dict[str, Any]) -> MediaType:
    """Map a pymediainfo ``kind_of_stream`` value to :class:`MediaType`."""
    return {
        "Image": MediaType.Image,
        "Video": MediaType.Video,
        "Audio": MediaType.Audio,
    }[track["kind_of_stream"]]


def _visual_track_to_json(
    media_id: int,
    source_file: str,
    timestamp: datetime.datetime,
    *,
    media_type: MediaType,
    width: int,
    height: int,
    duration: int,
    filename: str = "",
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
                "editRate": 1000,
                "trackRect": media_rect,
                "sampleRate": 0,
                "bitDepth": 0,
                "numChannels": 0,
                "integratedLUFS": 100.0,
                "peakLevel": -1.0,
                "tag": 0,
                "metaData": f"{filename};" if filename else "",
                "parameters": {},
            }
        ],
        "metadata": {},
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
        "metadata": {},
    }


def _datetime_to_str(dt: datetime.datetime) -> str:
    """Format a datetime as Camtasia's ``lastMod`` string.

    Format: ``YYYYMMDDTHHmmss``, e.g. ``20190606T103830``.
    """
    return f"{dt.year}{dt.month:02}{dt.day:02}T{dt.hour:02}{dt.minute:02}{dt.second:02}"
