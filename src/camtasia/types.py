"""Strong types for the pycamtasia library."""
from __future__ import annotations
from enum import Enum, IntEnum
from typing import Literal

__all__ = [
    'ClipType', 'EffectName', 'TransitionType', 'BehaviorPreset',
    'BehaviorInnerName', 'BlendMode', 'ValidationLevel', 'MediaType',
    'MaskShape', 'CalloutShape', 'CalloutKind', 'InterpolationType',
    'TrackType', 'EffectCategory', 'Alignment', 'ReportFormat',
    'RGBA', 'DropShadowParams', 'RoundCornersParams', 'ColorAdjustmentParams',
    'EffectDict', 'TransitionDict', 'ClipSummary', 'HealthCheckResult',
    'CompactResult', 'TimelineSummary', 'ScreenplayBuildResult',
]

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
    COLOR_ADJUSTMENT = 'ColorAdjustment'
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
    GLITCH3 = 'Glitch3'
    PAINT_ARCS = 'PaintArcs'
    SPHERICAL_SPIN = 'SphericalSpin'


class BehaviorPreset(str, Enum):
    """Known behavior animation presets."""
    REVEAL = 'Reveal'
    SLIDING = 'Sliding'
    FADE = 'Fade'
    FLY_IN = 'FlyIn'
    POP_UP = 'PopUp'


class BehaviorInnerName(str, Enum):
    """Inner animation names used in GenericBehaviorEffect in/center/out phases."""
    # In-phase animations
    FADE_IN = 'fadeIn'
    REVEAL = 'reveal'
    SLIDING = 'sliding'
    FLY_IN = 'flyIn'
    GROW = 'grow'
    HINGE = 'hinge'
    # Out-phase animations
    FADE_OUT = 'fadeOut'
    FLY_OUT = 'flyOut'
    SHRINK = 'shrink'
    SHIFTING = 'shifting'
    # Center-phase animations
    NONE = 'none'
    TREMBLE = 'tremble'


class BlendMode(IntEnum):
    """Blend mode values for BlendModeEffect."""
    NORMAL = 16
    MULTIPLY = 3
    # Add more as discovered from Camtasia projects


class MaskShape(IntEnum):
    """Mask shape values."""
    RECTANGLE = 0
    ELLIPSE = 1
    # Add more as discovered


class CalloutShape(str, Enum):
    """Callout annotation shapes (verified against 93 TechSmith samples)."""
    EMPTY = ''
    TEXT = 'text'
    TEXT_RECTANGLE = 'text-rectangle'
    TEXT_ARROW2 = 'text-arrow2'
    ARROW = 'arrow'
    SHAPE_RECTANGLE = 'shape-rectangle'
    SHAPE_ELLIPSE = 'shape-ellipse'
    SHAPE_TRIANGLE = 'shape-triangle'


class InterpolationType(str, Enum):
    """Keyframe interpolation types."""
    LINEAR = 'linr'
    EASE_IN_OUT_ELASTIC = 'eioe'
    HOLD = 'hold'


class CalloutKind(str, Enum):
    """Callout kind identifiers."""
    REMIX = 'remix'
    WIN_BLUR = 'TypeWinBlur'


class TrackType(str, Enum):
    """Track content types (for future use)."""
    AUDIO = 'audio'
    VIDEO = 'video'
    ANNOTATION = 'annotation'
    MIXED = 'mixed'


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
# Internal TypedDicts – raw JSON data shapes (total=False: all keys optional)
# ---------------------------------------------------------------------------
from typing import Any, TypedDict
import sys
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import NotRequired
else:  # pragma: no cover
    from typing_extensions import NotRequired
from fractions import Fraction


class _ClipData(TypedDict, total=False):
    """Internal structure of a clip's raw JSON data."""
    _type: str
    id: int
    start: int
    duration: int
    mediaStart: int | Fraction
    mediaDuration: int | Fraction
    src: Any
    scalar: float | str
    parameters: dict[str, Any]
    effects: list[dict[str, Any]]
    metadata: dict[str, Any]
    attributes: dict[str, Any]
    animationTracks: dict[str, Any]
    tracks: list[dict[str, Any]]
    channelNumber: str
    video: dict[str, Any]
    audio: dict[str, Any]
    medias: list[dict[str, Any]]
    minMediaStart: int
    sourceEffect: dict[str, Any]
    # 'def' key exists at runtime but can't be declared (Python keyword);
    # accesses use type: ignore[typeddict-item].


class _EffectData(TypedDict, total=False):
    """Internal structure of an effect's raw JSON data."""
    effectName: str
    _type: str
    bypassed: bool
    category: str
    parameters: dict[str, Any]
    metadata: dict[str, Any]
    start: int
    duration: int
    leftEdgeMods: list[dict[str, Any]]
    rightEdgeMods: list[dict[str, Any]]


class _TransitionData(TypedDict, total=False):
    """Internal structure of a transition's raw JSON data."""
    name: str
    duration: int
    leftMedia: int
    rightMedia: int
    attributes: dict[str, Any]


class _BehaviorPhaseData(TypedDict, total=False):
    """Internal structure of a behavior phase dict."""
    attributes: dict[str, Any]
    parameters: dict[str, Any]


class _BehaviorEffectData(TypedDict, total=False):
    """Internal structure of a GenericBehaviorEffect dict."""
    effectName: str
    bypassed: bool
    start: int
    duration: int
    metadata: dict[str, Any]
    # 'in', 'center', 'out' keys exist at runtime but can't be declared
    # (Python keywords); accesses use type: ignore[typeddict-item].


class _CaptionData(TypedDict, total=False):
    """Internal structure of caption attributes."""
    enabled: bool
    fontName: str
    fontSize: int
    backgroundColor: list[int]
    foregroundColor: list[int]
    lang: str
    alignment: int
    opacity: float
    backgroundEnabled: bool




# ---------------------------------------------------------------------------
# TypedDicts – structured data returned / consumed by the library
# ---------------------------------------------------------------------------


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
    channel: int
    shadowRampStart: float
    shadowRampEnd: float
    highlightRampStart: float
    highlightRampEnd: float


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


class CompactResult(TypedDict):
    """Result of compact_project()."""
    orphaned_media_removed: int
    empty_tracks_removed: int


class TimelineSummary(TypedDict):
    """Result of Timeline.to_dict()."""
    track_count: int
    total_clip_count: int
    duration_seconds: float
    has_clips: bool
    track_names: list[str]


class ScreenplayBuildResult(TypedDict):
    """Result of build_from_screenplay()."""
    clips_placed: int
    pauses_added: int
    total_duration: float