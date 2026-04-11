"""GenericBehaviorEffect — Camtasia's text animation/behaviors system."""
from __future__ import annotations

from typing import Any, Union


class BehaviorPhase:
    """Wraps a single behavior phase dict (``in``, ``center``, or ``out``).

    Each phase has ``attributes`` controlling character-level animation
    timing and physics, plus ``parameters`` for direction/style keyframes.

    Args:
        data: The raw phase dict from the behavior effect.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def data(self) -> dict[str, Any]:
        """The underlying raw dict."""
        return self._data

    @property
    def _attrs(self) -> dict[str, Any]:
        return self._data["attributes"]

    @property
    def name(self) -> str:
        """Behavior name (e.g. ``'reveal'``, ``'none'``)."""
        return self._attrs["name"]

    @name.setter
    def name(self, value: str) -> None:
        self._attrs["name"] = value

    @property
    def phase_type(self) -> int:
        """Phase type: 0 for in/out, 1 for center."""
        return self._attrs["type"]

    @property
    def character_order(self) -> int:
        """Order in which characters animate (e.g. left-to-right, random)."""
        return self._attrs["characterOrder"]

    @character_order.setter
    def character_order(self, value: int) -> None:
        self._attrs["characterOrder"] = value

    @property
    def offset_between_characters(self) -> int:
        """Delay between characters in ticks."""
        return self._attrs.get("offsetBetweenCharacters", 0)

    @offset_between_characters.setter
    def offset_between_characters(self, value: int) -> None:
        self._attrs["offsetBetweenCharacters"] = value

    @property
    def suggested_duration_per_character(self) -> int:
        """Suggested duration per character in ticks."""
        return self._attrs.get("suggestedDurationPerCharacter", 0)

    @suggested_duration_per_character.setter
    def suggested_duration_per_character(self, value: int) -> None:
        self._attrs["suggestedDurationPerCharacter"] = value

    @property
    def overlap_proportion(self) -> int | float | str:
        """Overlap proportion — may be int, float, or string fraction (e.g. ``'1/2'``)."""
        return self._attrs.get("overlapProportion", 0)

    @overlap_proportion.setter
    def overlap_proportion(self, value: int | float | str) -> None:
        self._attrs["overlapProportion"] = value

    @property
    def movement(self) -> int:
        """Movement enum for animation direction/style."""
        return self._attrs.get("movement", 0)

    @movement.setter
    def movement(self, value: int) -> None:
        self._attrs["movement"] = value

    @property
    def spring_damping(self) -> float:
        """Spring damping coefficient for bounce animations."""
        return self._attrs.get("springDamping", 0.0)

    @spring_damping.setter
    def spring_damping(self, value: float) -> None:
        self._attrs["springDamping"] = value

    @property
    def spring_stiffness(self) -> float:
        """Spring stiffness coefficient for bounce animations."""
        return self._attrs.get("springStiffness", 0.0)

    @spring_stiffness.setter
    def spring_stiffness(self, value: float) -> None:
        self._attrs["springStiffness"] = value

    @property
    def bounce_bounciness(self) -> float:
        """Bounciness factor for bounce animations."""
        return self._attrs.get("bounceBounciness", 0.0)

    @bounce_bounciness.setter
    def bounce_bounciness(self, value: float) -> None:
        self._attrs["bounceBounciness"] = value

    @property
    def parameters(self) -> dict[str, Any]:
        """Raw parameters dict (direction keyframes, etc.)."""
        return self._data.get("parameters", {})

    def __repr__(self) -> str:
        return f"BehaviorPhase(name={self.name!r}, type={self.phase_type})"


class GenericBehaviorEffect:
    """Wraps a ``GenericBehaviorEffect`` dict — Camtasia's text behavior system.

    Unlike regular effects, behavior effects have a ``_type`` field set to
    ``'GenericBehaviorEffect'`` and contain three animation phases
    (``in``, ``center``, ``out``) instead of flat parameters.

    Args:
        data: The raw behavior effect dict from the project JSON.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def data(self) -> dict[str, Any]:
        """The underlying raw dict."""
        return self._data

    @property
    def effect_name(self) -> str:
        """Effect name identifier."""
        return self._data["effectName"]

    @property
    def bypassed(self) -> bool:
        """Whether the effect is bypassed (disabled)."""
        return self._data.get("bypassed", False)

    @bypassed.setter
    def bypassed(self, value: bool) -> None:
        self._data["bypassed"] = value

    @property
    def start(self) -> int:
        """Start time in ticks."""
        return self._data["start"]

    @start.setter
    def start(self, value: int) -> None:
        self._data["start"] = value

    @property
    def duration(self) -> int:
        """Duration in ticks."""
        return self._data["duration"]

    @duration.setter
    def duration(self, value: int) -> None:
        self._data["duration"] = value

    @property
    def entrance(self) -> BehaviorPhase:
        """The ``in`` (entrance) phase."""
        return BehaviorPhase(self._data["in"])

    @property
    def center(self) -> BehaviorPhase:
        """The ``center`` (sustain/loop) phase."""
        return BehaviorPhase(self._data["center"])

    @property
    def exit(self) -> BehaviorPhase:
        """The ``out`` (exit) phase."""
        return BehaviorPhase(self._data["out"])

    @property
    def preset_name(self) -> str:
        """Preset name from metadata (e.g. ``'Reveal'``)."""
        return self._data.get("metadata", {}).get("presetName", "")

    def __repr__(self) -> str:
        return f"GenericBehaviorEffect(name={self.effect_name!r}, preset={self.preset_name!r})"
