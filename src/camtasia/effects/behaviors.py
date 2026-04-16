"""GenericBehaviorEffect — Camtasia's text animation/behaviors system."""
from __future__ import annotations

from typing import Any, Union

from camtasia.effects.base import Effect
from camtasia.types import _BehaviorEffectData, _BehaviorPhaseData


class BehaviorPhase:
    """Wraps a single behavior phase dict (``in``, ``center``, or ``out``).

    Each phase has ``attributes`` controlling character-level animation
    timing and physics, plus ``parameters`` for direction/style keyframes.

    Args:
        data: The raw phase dict from the behavior effect.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data: _BehaviorPhaseData = data  # type: ignore[assignment]

    @property
    def data(self) -> _BehaviorPhaseData:
        """The underlying raw dict."""
        return self._data

    @property
    def _attrs(self) -> dict[str, Any]:
        return self._data["attributes"]

    @property
    def name(self) -> str:
        """Behavior name (e.g. ``'reveal'``, ``'none'``)."""
        return str(self._attrs.get("name", ""))

    @name.setter
    def name(self, value: str) -> None:
        """Set the behavior name."""
        self._attrs["name"] = value

    @property
    def phase_type(self) -> int:
        """Animation granularity: 0 = whole-object, 1 = per-character."""
        return int(self._attrs.get("type", 0))

    @property
    def character_order(self) -> int:
        """Order in which characters animate (e.g. left-to-right, random)."""
        return int(self._attrs.get('characterOrder', 0))

    @character_order.setter
    def character_order(self, value: int) -> None:
        """Set the character animation order."""
        self._attrs["characterOrder"] = value

    @property
    def offset_between_characters(self) -> int:
        """Delay between characters in ticks."""
        return int(self._attrs.get("offsetBetweenCharacters", 0))

    @offset_between_characters.setter
    def offset_between_characters(self, value: int) -> None:
        """Set the delay between characters in ticks."""
        self._attrs["offsetBetweenCharacters"] = value

    @property
    def suggested_duration_per_character(self) -> int:
        """Suggested duration per character in ticks."""
        return int(self._attrs.get("suggestedDurationPerCharacter", 0))

    @suggested_duration_per_character.setter
    def suggested_duration_per_character(self, value: int) -> None:
        """Set the suggested duration per character in ticks."""
        self._attrs["suggestedDurationPerCharacter"] = value

    @property
    def overlap_proportion(self) -> int | float | str:
        """Overlap proportion — may be int, float, or string fraction (e.g. ``'1/2'``)."""
        return self._attrs.get("overlapProportion", 0)  # type: ignore[no-any-return]

    @overlap_proportion.setter
    def overlap_proportion(self, value: int | float | str) -> None:
        """Set the overlap proportion value."""
        self._attrs["overlapProportion"] = value

    @property
    def movement(self) -> int:
        """Movement enum for animation direction/style."""
        return int(self._attrs.get("movement", 0))

    @movement.setter
    def movement(self, value: int) -> None:
        """Set the movement enum value."""
        self._attrs["movement"] = value

    @property
    def spring_damping(self) -> float:
        """Spring damping coefficient for bounce animations."""
        return float(self._attrs.get("springDamping", 0.0))

    @spring_damping.setter
    def spring_damping(self, value: float) -> None:
        """Set the spring damping coefficient."""
        self._attrs["springDamping"] = value

    @property
    def spring_stiffness(self) -> float:
        """Spring stiffness coefficient for bounce animations."""
        return float(self._attrs.get("springStiffness", 0.0))

    @spring_stiffness.setter
    def spring_stiffness(self, value: float) -> None:
        """Set the spring stiffness coefficient."""
        self._attrs["springStiffness"] = value

    @property
    def bounce_bounciness(self) -> float:
        """Bounciness factor for bounce animations."""
        return float(self._attrs.get("bounceBounciness", 0.0))

    @bounce_bounciness.setter
    def bounce_bounciness(self, value: float) -> None:
        """Set the bounciness factor."""
        self._attrs["bounceBounciness"] = value

    @property
    def parameters(self) -> dict[str, Any]:
        """Raw parameters dict (direction keyframes, etc.)."""
        return self._data.get("parameters", {})

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"BehaviorPhase(name={self.name!r}, type={self.phase_type})"


class GenericBehaviorEffect(Effect):
    """Wraps a ``GenericBehaviorEffect`` dict — Camtasia's text behavior system.

    Unlike regular effects, behavior effects have a ``_type`` field set to
    ``'GenericBehaviorEffect'`` and contain three animation phases
    (``in``, ``center``, ``out``) instead of flat parameters.

    Args:
        data: The raw behavior effect dict from the project JSON.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        Effect.__init__(self, data)

    @property
    def effect_name(self) -> str:
        """Effect name identifier."""
        return self._data["effectName"]

    @property
    def name(self) -> str:
        """Alias for effect_name (polymorphic with Effect)."""
        return self.effect_name

    @property
    def category(self) -> str:
        """Behavior effects have no category."""
        return ''

    @property
    def parameters(self) -> dict[str, Any]:
        """Behavior effects have no flat parameters."""
        return {}

    @property
    def start(self) -> int:
        """Start time in ticks."""
        return int(self._data["start"])

    @start.setter
    def start(self, value: int) -> None:
        """Set the start time in ticks."""
        self._data["start"] = value

    @property
    def duration(self) -> int:
        """Duration in ticks."""
        return int(self._data["duration"])

    @duration.setter
    def duration(self, value: int) -> None:
        """Set the duration in ticks."""
        self._data["duration"] = value

    @property
    def entrance(self) -> BehaviorPhase:
        """The ``in`` (entrance) phase."""
        return BehaviorPhase(self._data["in"])  # type: ignore[typeddict-item]

    @property
    def center(self) -> BehaviorPhase:
        """The ``center`` (sustain/loop) phase."""
        return BehaviorPhase(self._data["center"])  # type: ignore[typeddict-item]

    @property
    def exit(self) -> BehaviorPhase:
        """The ``out`` (exit) phase."""
        return BehaviorPhase(self._data["out"])  # type: ignore[typeddict-item]

    @property
    def preset_name(self) -> str:
        """Preset name from metadata (e.g. ``'Reveal'``)."""
        return self._data.get("metadata", {}).get("presetName", "")  # type: ignore[no-any-return]

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"GenericBehaviorEffect(name={self.effect_name!r}, preset={self.preset_name!r})"

    @property
    def is_time_bounded(self) -> bool:
        """Whether this behavior effect has explicit start/duration."""
        return 'start' in self._data and 'duration' in self._data
