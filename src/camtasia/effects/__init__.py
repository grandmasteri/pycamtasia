"""Camtasia effects — thin wrappers over effect dicts."""
from __future__ import annotations

import importlib.util
import pathlib

from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.visual import BlurRegion, DropShadow, Mask, MotionBlur, RoundCorners
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
try:
    _spec = importlib.util.spec_from_file_location("camtasia._effects_legacy", _legacy_path)
    _legacy = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_legacy)
    EffectSchema = _legacy.EffectSchema
    ChromaKeyEffect = _legacy.ChromaKeyEffect
except Exception:

    class EffectSchema:
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
    "CursorMotionBlur",
    "CursorPhysics",
    "CursorShadow",
    "LeftClickScaling",
    "SourceEffect",
    "BehaviorPhase",
    "GenericBehaviorEffect",
]
