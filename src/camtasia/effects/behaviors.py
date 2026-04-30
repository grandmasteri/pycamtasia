"""GenericBehaviorEffect — Camtasia's text animation/behaviors system."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from camtasia.effects.base import Effect

if TYPE_CHECKING:
    from camtasia.types import _BehaviorPhaseData


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
        return self._data.setdefault("parameters", {})

    # ------------------------------------------------------------------
    # Center-phase loop properties
    # ------------------------------------------------------------------

    @property
    def seconds_per_loop(self) -> float:
        """Seconds per animation loop cycle."""
        val = self._attrs.get("secondsPerLoop", 0)
        if isinstance(val, str):
            from fractions import Fraction
            return float(Fraction(val))
        return float(val)

    @seconds_per_loop.setter
    def seconds_per_loop(self, value: float) -> None:
        """Set seconds per loop cycle."""
        self._attrs["secondsPerLoop"] = value

    @property
    def number_of_loops(self) -> int:
        """Number of loops (-1 = infinite)."""
        return int(self._attrs.get("numberOfLoops", 0))

    @number_of_loops.setter
    def number_of_loops(self, value: int) -> None:
        """Set number of loops (-1 = infinite)."""
        self._attrs["numberOfLoops"] = value

    @property
    def delay_between_loops(self) -> float:
        """Delay between loop cycles in seconds."""
        return float(self._attrs.get("delayBetweenLoops", 0))

    @delay_between_loops.setter
    def delay_between_loops(self, value: float) -> None:
        """Set delay between loop cycles."""
        self._attrs["delayBetweenLoops"] = value

    # ------------------------------------------------------------------
    # Animation parameter accessors (read from parameters dict)
    # ------------------------------------------------------------------

    @property
    def opacity(self) -> float:
        """Opacity parameter default value."""
        p = self._data.get("parameters", {}).get("opacity")
        if isinstance(p, dict):
            return float(p.get("defaultValue", 1.0))
        return float(p) if p is not None else 1.0

    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set opacity parameter default value."""
        params = self._data.setdefault("parameters", {})
        p = params.get("opacity")
        if isinstance(p, dict):
            p["defaultValue"] = value
        else:
            params["opacity"] = value

    @property
    def jump(self) -> float:
        """Jump parameter default value."""
        p = self._data.get("parameters", {}).get("jump")
        if isinstance(p, dict):
            return float(p.get("defaultValue", 0.0))
        return float(p) if p is not None else 0.0

    @jump.setter
    def jump(self, value: float) -> None:
        """Set jump parameter default value."""
        params = self._data.setdefault("parameters", {})
        p = params.get("jump")
        if isinstance(p, dict):
            p["defaultValue"] = value
        else:
            params["jump"] = value

    @property
    def rotation(self) -> float:
        """Rotation parameter default value."""
        p = self._data.get("parameters", {}).get("rotation")
        if isinstance(p, dict):
            return float(p.get("defaultValue", 0.0))
        return float(p) if p is not None else 0.0

    @rotation.setter
    def rotation(self, value: float) -> None:
        """Set rotation parameter default value."""
        params = self._data.setdefault("parameters", {})
        p = params.get("rotation")
        if isinstance(p, dict):
            p["defaultValue"] = value
        else:
            params["rotation"] = value

    @property
    def scale(self) -> float:
        """Scale parameter default value."""
        p = self._data.get("parameters", {}).get("scale")
        if isinstance(p, dict):
            return float(p.get("defaultValue", 1.0))
        return float(p) if p is not None else 1.0

    @scale.setter
    def scale(self, value: float) -> None:
        """Set scale parameter default value."""
        params = self._data.setdefault("parameters", {})
        p = params.get("scale")
        if isinstance(p, dict):
            p["defaultValue"] = value
        else:
            params["scale"] = value

    @property
    def shift(self) -> tuple[float, float]:
        """Shift as (horizontal, vertical) from parameters."""
        params = self._data.get("parameters", {})
        h = params.get("horizontal")
        v = params.get("vertical")
        hv = float(h["defaultValue"] if isinstance(h, dict) else (h or 0.0))
        vv = float(v["defaultValue"] if isinstance(v, dict) else (v or 0.0))
        return (hv, vv)

    @shift.setter
    def shift(self, value: tuple[float, float]) -> None:
        """Set shift as (horizontal, vertical)."""
        params = self._data.setdefault("parameters", {})
        h, v = value
        ph = params.get("horizontal")
        pv = params.get("vertical")
        if isinstance(ph, dict):
            ph["defaultValue"] = h
        else:
            params["horizontal"] = h
        if isinstance(pv, dict):
            pv["defaultValue"] = v
        else:
            params["vertical"] = v

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

    @classmethod
    def from_preset(cls, name: str, duration_seconds: float = 2.0) -> GenericBehaviorEffect:
        """Create a behavior effect from a named preset.

        Args:
            name: Preset name (e.g. ``'flyOut'``, ``'emphasize'``, ``'jiggle'``).
            duration_seconds: Effect duration in seconds.

        Returns:
            A new ``GenericBehaviorEffect`` wrapping the preset data.

        Raises:
            ValueError: Unknown preset name.
        """
        from camtasia.templates.behavior_presets import get_behavior_preset
        from camtasia.timing import seconds_to_ticks

        ticks = seconds_to_ticks(duration_seconds)
        data = get_behavior_preset(name, ticks)
        return cls(data)

    @property
    def effect_name(self) -> str:
        """Effect name identifier."""
        return self._data.get("effectName", "")

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

    def get_parameter(self, name: str) -> Any:
        """Behavior effects do not support flat parameters."""
        raise NotImplementedError('Behavior effects do not support flat parameters. Use entrance/center/exit phases instead.')

    def set_parameter(self, name: str, value: Any) -> None:
        """Behavior effects do not support flat parameters."""
        raise NotImplementedError('Behavior effects do not support flat parameters. Use entrance/center/exit phases instead.')

    @property
    def start(self) -> int | None:
        """Start time in ticks."""
        return self._data.get("start")

    @start.setter
    def start(self, value: int) -> None:
        """Set the start time in ticks."""
        self._data["start"] = value

    @property
    def duration(self) -> int | None:
        """Duration in ticks."""
        return self._data.get("duration")

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


