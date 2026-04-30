"""Camtasia effects — thin wrappers over effect dicts."""
from __future__ import annotations

from camtasia.effects.audio import NoiseRemoval
from camtasia.effects.audio_visualizer import AudioVisualizer
from camtasia.effects.base import Effect, effect_from_dict
from camtasia.effects.behaviors import BehaviorPhase, GenericBehaviorEffect
from camtasia.effects.cursor import (
    CursorColor,
    CursorGlow,
    CursorGradient,
    CursorHighlight,
    CursorIsolation,
    CursorLens,
    CursorMagnify,
    CursorMotionBlur,
    CursorNegative,
    CursorPathCreator,
    CursorPhysics,
    CursorShadow,
    CursorSmoothing,
    CursorSpotlight,
    LeftClickBurst1,
    LeftClickBurst2,
    LeftClickBurst3,
    LeftClickBurst4,
    LeftClickRings,
    LeftClickRipple,
    LeftClickScaling,
    LeftClickScope,
    LeftClickSound,
    LeftClickTarget,
    LeftClickWarp,
    LeftClickZoom,
    RightClickBurst1,
    RightClickBurst2,
    RightClickBurst3,
    RightClickBurst4,
    RightClickRings,
    RightClickRipple,
    RightClickScaling,
    RightClickScope,
    RightClickSound,
    RightClickTarget,
    RightClickWarp,
    RightClickZoom,
)
from camtasia.effects.source import SourceEffect
from camtasia.effects.visual import (
    BlendModeEffect,
    BlurRegion,
    ChromaKey,
    ColorAdjustment,
    CornerPin,
    Crop,
    DropShadow,
    Emphasize,
    Glow,
    LutEffect,
    Mask,
    MediaMatte,
    MotionBlur,
    RoundCorners,
    Spotlight,
)


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
    "AudioVisualizer",
    "BehaviorPhase",
    "BlendModeEffect",
    "BlurRegion",
    "ChromaKey",
    "ColorAdjustment",
    "CornerPin",
    "Crop",
    "CursorColor",
    "CursorGlow",
    "CursorGradient",
    "CursorHighlight",
    "CursorIsolation",
    "CursorLens",
    "CursorMagnify",
    "CursorMotionBlur",
    "CursorNegative",
    "CursorPathCreator",
    "CursorPhysics",
    "CursorShadow",
    "CursorSmoothing",
    "CursorSpotlight",
    "DropShadow",
    "Effect",
    "EffectSchema",
    "Emphasize",
    "GenericBehaviorEffect",
    "Glow",
    "LeftClickBurst1",
    "LeftClickBurst2",
    "LeftClickBurst3",
    "LeftClickBurst4",
    "LeftClickRings",
    "LeftClickRipple",
    "LeftClickScaling",
    "LeftClickScope",
    "LeftClickSound",
    "LeftClickTarget",
    "LeftClickWarp",
    "LeftClickZoom",
    "LutEffect",
    "Mask",
    "MediaMatte",
    "MotionBlur",
    "NoiseRemoval",
    "RightClickBurst1",
    "RightClickBurst2",
    "RightClickBurst3",
    "RightClickBurst4",
    "RightClickRings",
    "RightClickRipple",
    "RightClickScaling",
    "RightClickScope",
    "RightClickSound",
    "RightClickTarget",
    "RightClickWarp",
    "RightClickZoom",
    "RoundCorners",
    "SourceEffect",
    "Spotlight",
    "effect_from_dict",
]
