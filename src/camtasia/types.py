"""Strong types for the pycamtasia library."""
from __future__ import annotations
from enum import Enum, IntEnum
from typing import Literal

# Effect categories
EffectCategory = Literal['categoryVisualEffects', 'categoryAudioEffects', 'categoryCursorEffects']

# Alignment values for CaptionAttributes
Alignment = Literal[0, 1, 2]  # left, center, right

# Export formats
ReportFormat = Literal['markdown', 'json']


class ClipType(str, Enum):
    """Camtasia clip types."""
    AUDIO = 'AMFile'
    VIDEO = 'VMFile'
    IMAGE = 'IMFile'
    SCREEN_VIDEO = 'ScreenVMFile'
    SCREEN_IMAGE = 'ScreenIMFile'
    CALLOUT = 'Callout'
    GROUP = 'Group'
    UNIFIED_MEDIA = 'UnifiedMedia'
    STITCHED_MEDIA = 'StitchedMedia'
    PLACEHOLDER = 'PlaceholderMedia'


class EffectName(str, Enum):
    """Known Camtasia effect names."""
    DROP_SHADOW = 'DropShadow'
    ROUND_CORNERS = 'RoundCorners'
    GLOW = 'Glow'
    MOTION_BLUR = 'MotionBlur'
    MASK = 'Mask'
    BLUR_REGION = 'BlurRegion'
    COLOR_ADJUSTMENT = 'ColorAdjustment'
    BORDER = 'Border'
    COLORIZE = 'Colorize'
    SPOTLIGHT = 'Spotlight'
    LUT_EFFECT = 'LutEffect'
    EMPHASIZE = 'Emphasize'
    MEDIA_MATTE = 'MediaMatte'
    BLEND_MODE = 'BlendModeEffect'


class TransitionType(str, Enum):
    """Known Camtasia transition types."""
    FADE_THROUGH_BLACK = 'FadeThroughBlack'
    DISSOLVE = 'Dissolve'
    FADE_TO_WHITE = 'FadeThroughColor'
    SLIDE_LEFT = 'SlideLeft'
    SLIDE_RIGHT = 'SlideRight'
    SLIDE_UP = 'SlideUp'
    SLIDE_DOWN = 'SlideDown'
    WIPE_LEFT = 'WipeLeft'
    WIPE_RIGHT = 'WipeRight'
    WIPE_UP = 'WipeUp'
    WIPE_DOWN = 'WipeDown'
    CARD_FLIP = 'CardFlip'
    GLITCH = 'Glitch'
    LINEAR_BLUR = 'LinearBlur'
    STRETCH = 'Stretch'
    FADE = 'Fade'


class BehaviorPreset(str, Enum):
    """Known behavior animation presets."""
    REVEAL = 'Reveal'
    SLIDING = 'Sliding'
    FADE = 'Fade'
    FLY_IN = 'FlyIn'
    POP_UP = 'PopUp'


class BlendMode(IntEnum):
    """Blend mode values for BlendModeEffect."""
    NORMAL = 16
    MULTIPLY = 3
    # Add more as discovered from Camtasia projects


class ValidationLevel(str, Enum):
    """Validation issue severity levels."""
    ERROR = 'error'
    WARNING = 'warning'


class MediaType(IntEnum):
    """Media source types (matches existing MediaType in media_bin)."""
    VIDEO = 0
    IMAGE = 1
    AUDIO = 2


# ---------------------------------------------------------------------------
# TypedDicts – structured data returned / consumed by the library
# ---------------------------------------------------------------------------
from typing import TypedDict, NotRequired


class RGBA(TypedDict):
    """RGBA color as 0.0-1.0 floats."""
    red: float
    green: float
    blue: float
    alpha: NotRequired[float]


class DropShadowParams(TypedDict, total=False):
    """Parameters for DropShadow effect."""
    angle: float
    offset: float
    blur: float
    opacity: float


class RoundCornersParams(TypedDict, total=False):
    """Parameters for RoundCorners effect."""
    radius: float


class ColorAdjustmentParams(TypedDict, total=False):
    """Parameters for ColorAdjustment effect."""
    brightness: float
    contrast: float
    saturation: float


class EffectDict(TypedDict):
    """Structure of an effect entry in the effects array."""
    effectName: str
    bypassed: bool
    category: NotRequired[str]
    parameters: NotRequired[dict]


class TransitionDict(TypedDict):
    """Structure of a transition entry."""
    name: str
    duration: int
    leftMedia: NotRequired[int]
    rightMedia: NotRequired[int]
    attributes: NotRequired[dict]


class ClipSummary(TypedDict):
    """Summary dict returned by BaseClip.to_dict()."""
    id: int
    type: str
    start_seconds: float
    duration_seconds: float
    end_seconds: float
    source_id: NotRequired[int]
    effects: NotRequired[list[str]]


class HealthCheckResult(TypedDict):
    """Result of Project.health_check()."""
    healthy: bool
    errors: list[str]
    warnings: list[str]
    structural_issues: list[str]
    statistics: dict