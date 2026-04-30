"""Canvas presets for vertical and standard aspect ratios, plus safe zones."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VerticalPreset(Enum):
    """Canvas dimension presets for common aspect ratios.

    Each value is a ``(width, height)`` tuple.
    """

    NINE_BY_SIXTEEN_FHD = (1080, 1920)
    NINE_BY_SIXTEEN_HD = (720, 1280)
    FOUR_BY_FIVE = (1080, 1350)
    ONE_BY_ONE = (1080, 1080)
    SIXTEEN_BY_NINE_FHD = (1920, 1080)


#: Map from string preset names to enum members.
PRESET_NAMES: dict[str, VerticalPreset] = {
    '9:16_FHD': VerticalPreset.NINE_BY_SIXTEEN_FHD,
    '9:16_HD': VerticalPreset.NINE_BY_SIXTEEN_HD,
    '4:5': VerticalPreset.FOUR_BY_FIVE,
    '1:1': VerticalPreset.ONE_BY_ONE,
    '16:9_FHD': VerticalPreset.SIXTEEN_BY_NINE_FHD,
}


class Platform(Enum):
    """Social media platforms with known safe-zone requirements."""

    INSTAGRAM_REELS = 'instagram_reels'
    YOUTUBE_SHORTS = 'youtube_shorts'
    TIKTOK = 'tiktok'


@dataclass(frozen=True)
class SafeZone:
    """Inset region where content is guaranteed visible on a platform.

    All values are in pixels from the respective canvas edge.
    """

    top: int
    bottom: int
    left: int
    right: int
    platform: Platform


#: Default safe zones per platform (for 1080×1920 canvas).
_SAFE_ZONES: dict[Platform, SafeZone] = {
    Platform.INSTAGRAM_REELS: SafeZone(top=250, bottom=400, left=40, right=40, platform=Platform.INSTAGRAM_REELS),
    Platform.YOUTUBE_SHORTS: SafeZone(top=200, bottom=300, left=40, right=40, platform=Platform.YOUTUBE_SHORTS),
    Platform.TIKTOK: SafeZone(top=150, bottom=350, left=40, right=40, platform=Platform.TIKTOK),
}


def get_safe_zone(platform: Platform | str) -> SafeZone:
    """Return the safe zone for a given platform.

    Args:
        platform: A :class:`Platform` member or its string value
            (e.g. ``'instagram_reels'``).

    Returns:
        The corresponding :class:`SafeZone`.

    Raises:
        ValueError: Unknown platform.
    """
    if isinstance(platform, str):
        try:
            platform = Platform(platform)
        except ValueError:
            raise ValueError(
                f"Unknown platform {platform!r}. "
                f"Valid: {[p.value for p in Platform]}"
            ) from None
    if platform not in _SAFE_ZONES:
        raise ValueError(f"No safe zone defined for {platform!r}")
    return _SAFE_ZONES[platform]
