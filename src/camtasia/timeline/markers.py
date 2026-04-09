"""Timeline and per-media markers (table-of-contents keyframes)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

EDIT_RATE = 705_600_000


@dataclass
class Marker:
    """A single marker (TOC keyframe).

    Args:
        name: The marker label text.
        time: Position in editRate ticks.
    """

    name: str
    time: int

    @property
    def time_seconds(self) -> float:
        """Position in seconds."""
        return self.time / EDIT_RATE


class MarkerList:
    """Wraps a parameters dict that may contain toc keyframes.

    Handles the case where the parameters/toc/keyframes path doesn't
    exist yet — it is created on first add.

    Args:
        data: The parent dict containing a 'parameters' key
              (e.g. the timeline dict or a media dict).
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def _keyframes(self) -> list[dict[str, Any]]:
        return (
            self._data
            .get('parameters', {})
            .get('toc', {})
            .get('keyframes', [])
        )

    def _ensure_keyframes(self) -> list[dict[str, Any]]:
        """Return the keyframes list, creating the path if needed."""
        params = self._data.setdefault('parameters', {})
        toc = params.setdefault('toc', {'type': 'string'})
        return toc.setdefault('keyframes', [])

    def __len__(self) -> int:
        return len(self._keyframes)

    def __iter__(self) -> Iterator[Marker]:
        for kf in self._keyframes:
            yield Marker(name=kf['value'], time=kf['time'])

    def add(self, name: str, time_ticks: int) -> Marker:
        """Add a marker at the given time.

        Args:
            name: The marker label text.
            time_ticks: Position in editRate ticks.

        Returns:
            The newly created Marker.
        """
        kf = {
            'time': time_ticks,
            'endTime': time_ticks,
            'value': name,
            'duration': 0,
        }
        self._ensure_keyframes().append(kf)
        return Marker(name=name, time=time_ticks)

    def remove_at(self, time: int) -> None:
        """Remove all markers at the given time.

        Args:
            time: Position in editRate ticks.

        Raises:
            KeyError: No marker exists at the given time.
        """
        keyframes = self._ensure_keyframes()
        before = len(keyframes)
        keyframes[:] = [kf for kf in keyframes if kf['time'] != time]
        if len(keyframes) == before:
            raise KeyError(f'No marker at time={time}')
