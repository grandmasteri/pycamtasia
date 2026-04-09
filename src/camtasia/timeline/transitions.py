"""Track-level transitions between clips."""

from __future__ import annotations

from typing import Any, Iterator, Optional

EDIT_RATE = 705_600_000


class Transition:
    """Wraps a single transition dict from the track's transitions array.

    Args:
        data: The raw transition dict from the JSON project.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def name(self) -> str:
        """Transition type name (e.g. 'FadeThroughBlack')."""
        return self._data['name']

    @property
    def duration(self) -> int:
        """Duration in editRate ticks."""
        return self._data['duration']

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return self.duration / EDIT_RATE

    @property
    def left_media_id(self) -> int:
        """Clip ID on the left side of the transition."""
        return self._data['leftMedia']

    @property
    def right_media_id(self) -> Optional[int]:
        """Clip ID on the right side, or None for fade-out at end."""
        return self._data.get('rightMedia')

    @property
    def attributes(self) -> dict[str, Any]:
        """Raw attributes dict."""
        return self._data.get('attributes', {})

    @property
    def bypassed(self) -> bool:
        """Whether the transition is bypassed (disabled)."""
        return self.attributes.get('bypass', False)

    @property
    def color(self) -> tuple[float, float, float]:
        """Transition color as (red, green, blue) floats."""
        attrs = self.attributes
        return (
            attrs.get('Color-red', 0.0),
            attrs.get('Color-green', 0.0),
            attrs.get('Color-blue', 0.0),
        )

    def __repr__(self) -> str:
        right = self.right_media_id
        return (
            f'Transition(name={self.name!r}, left={self.left_media_id}, '
            f'right={right}, duration_s={self.duration_seconds:.2f})'
        )


class TransitionList:
    """Wraps the track-level transitions array.

    Args:
        data: The track dict containing a 'transitions' key.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def _transitions(self) -> list[dict[str, Any]]:
        return self._data.setdefault('transitions', [])

    def __len__(self) -> int:
        return len(self._transitions)

    def __iter__(self) -> Iterator[Transition]:
        for t in self._transitions:
            yield Transition(t)

    def __getitem__(self, index: int) -> Transition:
        return Transition(self._transitions[index])

    def add(
        self,
        name: str,
        left_clip_id: int,
        right_clip_id: Optional[int],
        duration_ticks: int,
        **attributes: Any,
    ) -> Transition:
        """Add a transition between two clips.

        Args:
            name: Transition type name (e.g. 'FadeThroughBlack').
            left_clip_id: ID of the clip on the left.
            right_clip_id: ID of the clip on the right, or None for fade-out.
            duration_ticks: Duration in editRate ticks.
            **attributes: Additional transition attributes.

        Returns:
            The newly created Transition.
        """
        record: dict[str, Any] = {
            'name': name,
            'duration': duration_ticks,
            'leftMedia': left_clip_id,
            'attributes': attributes,
        }
        if right_clip_id is not None:
            record['rightMedia'] = right_clip_id

        self._transitions.append(record)
        return Transition(record)

    def add_fade_through_black(
        self,
        left_clip_id: int,
        right_clip_id: Optional[int],
        duration_ticks: int,
    ) -> Transition:
        """Add a FadeThroughBlack transition with default attributes.

        Args:
            left_clip_id: ID of the clip on the left.
            right_clip_id: ID of the clip on the right, or None for fade-out.
            duration_ticks: Duration in editRate ticks.

        Returns:
            The newly created Transition.
        """
        return self.add(
            'FadeThroughBlack',
            left_clip_id,
            right_clip_id,
            duration_ticks,
            **{
                'Color-blue': 0.0,
                'Color-green': 0.0,
                'Color-red': 0.0,
                'bypass': False,
                'reverse': False,
                'trivial': False,
                'useAudioPreRoll': True,
                'useVisualPreRoll': True,
            },
        )

    def remove(self, index: int) -> None:
        """Remove a transition by index.

        Args:
            index: Index of the transition to remove.

        Raises:
            IndexError: If the index is out of range.
        """
        del self._transitions[index]
