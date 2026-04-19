"""Camtasia effects — thin wrappers over effect dicts."""
from __future__ import annotations

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

class EffectSchema:
    """Stub for legacy marshmallow-based EffectSchema.

    Install ``marshmallow`` and ``marshmallow-oneofschema`` to use
    the full schema-based serialization.
    """

    def __init__(self) -> None:
        raise RuntimeError(
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
