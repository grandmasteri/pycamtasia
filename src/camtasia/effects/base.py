"""Base effect class wrapping Camtasia effect dicts."""
from __future__ import annotations

from typing import Any, Callable

from camtasia.types import _EffectData


class Effect:
    """Thin wrapper around a Camtasia effect dict.

    Effects are stored in a clip's ``effects`` array as dicts with keys:
    ``effectName``, ``bypassed``, ``category``, ``parameters``.

    Each parameter is a nested dict like::

        {"type": "double", "defaultValue": 16.0, "interp": "linr"}

    Args:
        data: The raw effect dict from the project JSON.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data: _EffectData = data  # type: ignore[assignment]

    @property
    def data(self) -> _EffectData:
        """The underlying raw dict."""
        return self._data

    @property
    def name(self) -> str:
        """Effect name identifier."""
        return self._data.get("effectName", "")

    @property
    def bypassed(self) -> bool:
        """Whether the effect is bypassed (disabled)."""
        return bool(self._data.get("bypassed", False))

    @bypassed.setter
    def bypassed(self, value: bool) -> None:
        """Set whether the effect is bypassed."""
        self._data["bypassed"] = value

    @property
    def category(self) -> str:
        """Effect category string."""
        return self._data.get("category", "")

    @property
    def metadata(self) -> dict:
        """Top-level metadata dict for this effect."""
        return self._data.get('metadata', {})

    @property
    def parameters(self) -> dict[str, Any]:
        """Effect parameters dict."""
        return self._data.get("parameters", {})

    def get_parameter(self, name: str) -> Any:
        """Get a parameter's default value by name.

        Args:
            name: The parameter key inside the ``parameters`` dict.

        Returns:
            The ``defaultValue`` of the parameter, or the scalar value directly.

        Raises:
            KeyError: If the parameter does not exist.
        """
        val = self.parameters[name]
        return val['defaultValue'] if isinstance(val, dict) else val

    def set_parameter(self, name: str, value: Any) -> None:
        """Set a parameter's default value by name.

        Args:
            name: The parameter key inside the ``parameters`` dict.
            value: The new default value.

        If the parameter exists as an animated dict, updates defaultValue.
        If it exists as a scalar, replaces it. If missing, creates it.
        """
        params = self._data.setdefault("parameters", {})
        existing = params.get(name)
        if isinstance(existing, dict):
            existing["defaultValue"] = value
        else:
            params[name] = value

    # ------------------------------------------------------------------
    # Time-bounded effects
    # ------------------------------------------------------------------

    @property
    def start(self) -> int | None:
        """Effect start time in ticks, or ``None`` if not time-bounded."""
        return self._data.get('start')

    @property
    def duration(self) -> int | None:
        """Effect duration in ticks, or ``None`` if not time-bounded."""
        return self._data.get('duration')

    @property
    def is_time_bounded(self) -> bool:
        """Whether this effect has explicit start/duration."""
        return 'start' in self._data and 'duration' in self._data

    @property
    def left_edge_mods(self) -> list[dict[str, Any]]:
        """Left edge modifications (fade-in, etc.)."""
        return self._data.get('leftEdgeMods', [])

    @property
    def right_edge_mods(self) -> list[dict[str, Any]]:
        """Right edge modifications (fade-out, etc.)."""
        return self._data.get('rightEdgeMods', [])

    def __eq__(self, other: object) -> bool:
        """Return True if both wrappers reference the same underlying dict."""
        if not isinstance(other, Effect):
            return NotImplemented
        return self._data is other._data

    def __hash__(self) -> int:
        """Return hash based on the underlying dict identity."""
        return id(self._data)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"{type(self).__name__}(name={self.name!r})"


# Registry for effect_from_dict dispatch
_EFFECT_REGISTRY: dict[str, type[Effect]] = {}


def register_effect(name: str) -> Callable[[type[Effect]], type[Effect]]:
    """Class decorator to register an Effect subclass for factory dispatch."""
    def decorator(cls: type[Effect]) -> type[Effect]:
        """Inner decorator function."""
        _EFFECT_REGISTRY[name] = cls
        return cls
    return decorator


def effect_from_dict(data: dict[str, Any]) -> Effect:
    """Create the appropriate Effect subclass from a raw effect dict.

    Args:
        data: A dict with at least an ``effectName`` key.

    Returns:
        An instance of the matching Effect subclass, or a generic
        ``Effect`` if no specific class is registered.
    """
    if data.get('_type') == 'GenericBehaviorEffect':
        from camtasia.effects.behaviors import GenericBehaviorEffect
        return GenericBehaviorEffect(data)
    cls = _EFFECT_REGISTRY.get(data.get("effectName", ""), Effect)
    return cls(data)
