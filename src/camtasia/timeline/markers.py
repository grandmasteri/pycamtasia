"""Timeline and per-media markers (table-of-contents keyframes)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

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

    def __repr__(self) -> str:
        return f'Marker(name={self.name!r}, time_seconds={self.time_seconds:.2f})'


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
        return (  # type: ignore[no-any-return]
            self._data
            .get('parameters', {})
            .get('toc', {})
            .get('keyframes', [])
        )

    def _ensure_keyframes(self) -> list[dict[str, Any]]:
        """Return the keyframes list, creating the path if needed."""
        params = self._data.setdefault('parameters', {})
        toc = params.setdefault('toc', {'type': 'string'})
        return toc.setdefault('keyframes', [])  # type: ignore[no-any-return]

    def __len__(self) -> int:
        return len(self._keyframes)

    def __repr__(self) -> str:
        return f'MarkerList(count={len(self)})'

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

    def clear(self) -> None:
        """Remove all markers."""
        self._ensure_keyframes().clear()

    def rename(self, old_name: str, new_name: str) -> None:
        """Rename the first marker matching *old_name*.

        Raises:
            ValueError: No marker with the given name.
        """
        for kf in self._ensure_keyframes():
            if kf['value'] == old_name:
                kf['value'] = new_name
                return
        raise ValueError(f'No marker named {old_name!r}')

    def move(self, old_time_ticks: int, new_time_ticks: int) -> None:
        """Move the first marker at *old_time_ticks* to *new_time_ticks*.

        Raises:
            ValueError: No marker at the given time.
        """
        for kf in self._ensure_keyframes():
            if kf['time'] == old_time_ticks:
                kf['time'] = new_time_ticks
                kf['endTime'] = new_time_ticks
                return
        raise ValueError(f'No marker at time={old_time_ticks}')

    def remove_by_name(self, name: str) -> None:
        """Remove the first marker matching *name*.

        Raises:
            ValueError: No marker with the given name.
        """
        keyframes = self._ensure_keyframes()
        for i, kf in enumerate(keyframes):
            if kf['value'] == name:
                del keyframes[i]
                return
        raise ValueError(f'No marker named {name!r}')

    def next_after(self, time_ticks: int) -> Marker | None:
        """Return the first marker with time > *time_ticks*, or ``None``."""
        best: dict[str, Any] | None = None
        for kf in self._keyframes:
            if kf['time'] > time_ticks and (best is None or kf['time'] < best['time']):
                best = kf
        return Marker(name=best['value'], time=best['time']) if best else None

    def prev_before(self, time_ticks: int) -> Marker | None:
        """Return the last marker with time < *time_ticks*, or ``None``."""
        best: dict[str, Any] | None = None
        for kf in self._keyframes:
            if kf['time'] < time_ticks and (best is None or kf['time'] > best['time']):
                best = kf
        return Marker(name=best['value'], time=best['time']) if best else None

    def replace(self, markers: list[tuple[str, int]]) -> None:
        """Replace all markers with a new set.

        Args:
            markers: List of (name, time_ticks) tuples.
        """
        self.clear()
        for name, time_ticks in markers:
            self.add(name, time_ticks)
