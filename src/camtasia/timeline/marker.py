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
