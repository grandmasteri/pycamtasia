"""Timeline markers for Camtasia projects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Marker:
    """A named marker at a specific time on the timeline.

    Attributes:
        name: Display name of the marker.
        time: Position in editRate ticks.
    """

    name: str
    time: int

    def __repr__(self) -> str:
        from camtasia.timing import ticks_to_seconds
        return f'Marker(name={self.name!r}, time_seconds={ticks_to_seconds(self.time):.2f})'
