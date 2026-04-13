"""Strong types for the pycamtasia library."""
from __future__ import annotations
from enum import Enum, IntEnum


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
    GLITCH = 'Glitch3'
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
