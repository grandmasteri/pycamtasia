"""Camtasia effects — thin wrappers over effect dicts."""
from __future__ import annotations

import importlib.util
import pathlib

from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.visual import BlurRegion, DropShadow, Glow, Mask, MotionBlur, RoundCorners
from camtasia.effects.cursor import (
    CursorMotionBlur,
    CursorPhysics,
    CursorShadow,
    LeftClickScaling,
)
from camtasia.effects.source import SourceEffect
from camtasia.effects.behaviors import BehaviorPhase, GenericBehaviorEffect

# Re-export legacy EffectSchema so existing code keeps working.
# The old effects.py depends on marshmallow; provide a stub if unavailable.
_legacy_path = pathlib.Path(__file__).parent.parent / "effects.py"
_EffectSchema: type | None = None
_ChromaKeyEffect: type | None = None
try:
    _spec = importlib.util.spec_from_file_location("camtasia._effects_legacy", _legacy_path)
    if _spec is not None and _spec.loader is not None:
        _legacy = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_legacy)  # type: ignore[union-attr]
        _EffectSchema = _legacy.EffectSchema  # pragma: no cover
        _ChromaKeyEffect = _legacy.ChromaKeyEffect  # pragma: no cover
except Exception:
    pass

if _EffectSchema is not None:
    EffectSchema = _EffectSchema
    ChromaKeyEffect = _ChromaKeyEffect
else:

    class EffectSchema:  # type: ignore[no-redef]
        """Stub for legacy marshmallow-based EffectSchema.

        Install ``marshmallow`` and ``marshmallow-oneofschema`` to use
        the full schema-based serialization.
        """

        def __init__(self) -> None:
            raise ImportError(
                "EffectSchema requires marshmallow and marshmallow-oneofschema. "
                "Install them or use the new dict-wrapper API (effect_from_dict)."
            )

__all__ = [
    "Effect",
    "EffectSchema",
    "effect_from_dict",
    "RoundCorners",
    "DropShadow",
    "MotionBlur",
    "Mask",
    "BlurRegion",
    "Glow",
    "CursorMotionBlur",
    "CursorPhysics",
    "CursorShadow",
    "LeftClickScaling",
    "SourceEffect",
    "BehaviorPhase",
    "GenericBehaviorEffect",
]
