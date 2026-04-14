"""Track-level transitions between clips."""

from __future__ import annotations

from typing import Any, Iterator

from camtasia.types import TransitionType

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
        return self._data['name']  # type: ignore[no-any-return]

    @property
    def duration(self) -> int:
        """Duration in editRate ticks."""
        return int(self._data['duration'])

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return self.duration / EDIT_RATE

    @property
    def left_media_id(self) -> int | None:
        """Clip ID on the left side, or None for fade-in at start."""
        return self._data.get('leftMedia')

    @property
    def right_media_id(self) -> int | None:
        """Clip ID on the right side, or None for fade-out at end."""
        return self._data.get('rightMedia')

    @property
    def attributes(self) -> dict[str, Any]:
        """Raw attributes dict."""
        return self._data.get('attributes', {})  # type: ignore[no-any-return]

    @property
    def bypassed(self) -> bool:
        """Whether the transition is bypassed (disabled)."""
        return bool(self.attributes.get('bypass', False))

    @property
    def color(self) -> tuple[float, float, float]:
        """Transition color as (red, green, blue) floats."""
        attrs = self.attributes
        return (
            attrs.get('Color-red', 0.0),
            attrs.get('Color-green', 0.0),
            attrs.get('Color-blue', 0.0),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transition):
            return NotImplemented
        return self._data is other._data

    def __hash__(self) -> int:
        return id(self._data)

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
        return self._data.setdefault('transitions', [])  # type: ignore[no-any-return]

    def __len__(self) -> int:
        return len(self._transitions)

    def __repr__(self) -> str:
        return f'TransitionList(count={len(self)})'

    def __iter__(self) -> Iterator[Transition]:
        for t in self._transitions:
            yield Transition(t)

    def __getitem__(self, index: int) -> Transition:
        return Transition(self._transitions[index])

    def add(
        self,
        name: str,
        left_clip_id: int,
        right_clip_id: int | None,
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
        right_clip_id: int | None,
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
            TransitionType.FADE_THROUGH_BLACK,
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

    @staticmethod
    def _clip_id(clip: Any) -> int:
        """Extract clip ID from a BaseClip or plain int."""
        return clip.id if hasattr(clip, 'id') else int(clip)

    def add_dissolve(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a dissolve transition between two clips."""
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(TransitionType.DISSOLVE, self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_fade_to_white(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a fade-through-white transition."""
        ticks = int(duration_seconds * EDIT_RATE)
        t = self.add(TransitionType.FADE_TO_WHITE, self._clip_id(left_clip), self._clip_id(right_clip), ticks)
        t._data['attributes']['Color-red'] = 1.0
        t._data['attributes']['Color-green'] = 1.0
        t._data['attributes']['Color-blue'] = 1.0
        return t

    def add_slide(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
        *,
        direction: str = 'left',
    ) -> Transition:
        """Add a slide transition.

        Args:
            direction: 'left', 'right', 'up', or 'down'.
        """
        name_map = {
            'left': TransitionType.SLIDE_LEFT,
            'right': TransitionType.SLIDE_RIGHT,
            'up': TransitionType.SLIDE_UP,
            'down': TransitionType.SLIDE_DOWN,
        }
        if direction not in name_map:
            raise ValueError(f'Invalid direction {direction!r}. Use: {sorted(name_map)}')
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(name_map[direction], self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_wipe(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
        *,
        direction: str = 'left',
    ) -> Transition:
        """Add a wipe transition.

        Args:
            direction: 'left', 'right', 'up', or 'down'.
        """
        name_map = {
            'left': TransitionType.WIPE_LEFT,
            'right': TransitionType.WIPE_RIGHT,
            'up': TransitionType.WIPE_UP,
            'down': TransitionType.WIPE_DOWN,
        }
        if direction not in name_map:
            raise ValueError(f'Invalid direction {direction!r}. Use: {sorted(name_map)}')
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(name_map[direction], self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_card_flip(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a card-flip transition."""
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(TransitionType.CARD_FLIP, self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_glitch(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a glitch transition."""
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(TransitionType.GLITCH, self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_linear_blur(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a linear-blur transition."""
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(TransitionType.LINEAR_BLUR, self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_stretch(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a stretch transition."""
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(TransitionType.STRETCH, self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_paint_arcs(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a paint-arcs transition."""
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(TransitionType.PAINT_ARCS, self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def add_spherical_spin(
        self,
        left_clip: Any,
        right_clip: Any,
        duration_seconds: float = 0.5,
    ) -> Transition:
        """Add a spherical-spin transition."""
        ticks = int(duration_seconds * EDIT_RATE)
        return self.add(TransitionType.SPHERICAL_SPIN, self._clip_id(left_clip), self._clip_id(right_clip), ticks)

    def remove(self, index: int) -> None:
        """Remove a transition by index.

        Args:
            index: Index of the transition to remove.

        Raises:
            IndexError: If the index is out of range.
        """
        del self._transitions[index]
