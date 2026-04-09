"""Base effect class wrapping Camtasia effect dicts."""
from __future__ import annotations

from typing import Any


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
        self._data = data

    @property
    def data(self) -> dict[str, Any]:
        """The underlying raw dict."""
        return self._data

    @property
    def name(self) -> str:
        return self._data["effectName"]

    @property
    def bypassed(self) -> bool:
        return self._data.get("bypassed", False)

    @bypassed.setter
    def bypassed(self, value: bool) -> None:
        self._data["bypassed"] = value

    @property
    def category(self) -> str:
        return self._data.get("category", "")

    @property
    def parameters(self) -> dict[str, Any]:
        return self._data.get("parameters", {})

    def get_parameter(self, name: str) -> Any:
        """Get a parameter's default value by name.

        Args:
            name: The parameter key inside the ``parameters`` dict.

        Returns:
            The ``defaultValue`` of the parameter.

        Raises:
            KeyError: If the parameter does not exist.
        """
        return self.parameters[name]["defaultValue"]

    def set_parameter(self, name: str, value: Any) -> None:
        """Set a parameter's default value by name.

        Args:
            name: The parameter key inside the ``parameters`` dict.
            value: The new default value.

        Raises:
            KeyError: If the parameter does not exist.
        """
        self.parameters[name]["defaultValue"] = value

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r})"


# Registry for effect_from_dict dispatch
_EFFECT_REGISTRY: dict[str, type[Effect]] = {}


def register_effect(name: str):
    """Class decorator to register an Effect subclass for factory dispatch."""
    def decorator(cls: type[Effect]) -> type[Effect]:
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
    cls = _EFFECT_REGISTRY.get(data["effectName"], Effect)
    return cls(data)
