"""Device frame asset library — stub catalog for TechSmith device frame images.

No frame images are bundled with pycamtasia. Users must provide their own
PNG files or download from the TechSmith asset library.
"""
from __future__ import annotations

from dataclasses import dataclass

from camtasia.builders.device_frame import DeviceFrameType

DEVICE_FRAME_LIBRARY_URL = 'https://library.techsmith.com/Camtasia'
"""URL for the TechSmith Camtasia asset library where device frames can be downloaded."""

# Default display areas (x, y, width, height) as fractions of the frame image.
# These are approximate values for common device frames in landscape orientation.
_DEFAULT_DISPLAY_AREAS: dict[DeviceFrameType, dict[str, tuple[float, float, float, float]]] = {
    DeviceFrameType.IPHONE: {
        'landscape': (0.06, 0.12, 0.88, 0.76),
        'portrait': (0.12, 0.06, 0.76, 0.88),
    },
    DeviceFrameType.IPAD: {
        'landscape': (0.05, 0.08, 0.90, 0.84),
        'portrait': (0.08, 0.05, 0.84, 0.90),
    },
    DeviceFrameType.ANDROID_PHONE: {
        'landscape': (0.06, 0.10, 0.88, 0.80),
        'portrait': (0.10, 0.06, 0.80, 0.88),
    },
    DeviceFrameType.ANDROID_TABLET: {
        'landscape': (0.05, 0.08, 0.90, 0.84),
        'portrait': (0.08, 0.05, 0.84, 0.90),
    },
    DeviceFrameType.MACBOOK: {
        'landscape': (0.11, 0.06, 0.78, 0.78),
        'portrait': (0.11, 0.06, 0.78, 0.78),
    },
    DeviceFrameType.IMAC: {
        'landscape': (0.04, 0.04, 0.92, 0.76),
        'portrait': (0.04, 0.04, 0.92, 0.76),
    },
    DeviceFrameType.BROWSER: {
        'landscape': (0.01, 0.08, 0.98, 0.91),
        'portrait': (0.01, 0.08, 0.98, 0.91),
    },
    DeviceFrameType.TV: {
        'landscape': (0.04, 0.04, 0.92, 0.84),
        'portrait': (0.04, 0.04, 0.92, 0.84),
    },
    DeviceFrameType.WATCH: {
        'landscape': (0.18, 0.18, 0.64, 0.64),
        'portrait': (0.18, 0.18, 0.64, 0.64),
    },
}


@dataclass(frozen=True)
class DeviceFrameAsset:
    """Metadata for a device frame image asset.

    Attributes:
        type: The device frame type.
        orientation: Frame orientation (``'landscape'`` or ``'portrait'``).
        image_path: Path to the frame PNG image, or ``None`` if the user
            must provide their own. Download frames from
            https://library.techsmith.com/Camtasia
        display_area: The (x, y, width, height) rectangle within the frame
            image where the video content is visible, expressed as fractions
            of the frame image dimensions (0.0-1.0).
    """

    type: DeviceFrameType
    orientation: str
    image_path: str | None
    display_area: tuple[float, float, float, float]


def get_device_frame_asset(
    type: DeviceFrameType,
    orientation: str = 'landscape',
) -> DeviceFrameAsset:
    """Return a stub :class:`DeviceFrameAsset` with metadata for the given device type.

    The returned asset has ``image_path=None`` — the user must provide their
    own frame image PNG. Download frames from the TechSmith asset library:
    https://library.techsmith.com/Camtasia

    Args:
        type: The device frame type.
        orientation: ``'landscape'`` or ``'portrait'``.

    Returns:
        A :class:`DeviceFrameAsset` with valid metadata but no image path.

    Raises:
        ValueError: If *orientation* is not ``'landscape'`` or ``'portrait'``.
    """
    if orientation not in ('landscape', 'portrait'):
        raise ValueError(f"orientation must be 'landscape' or 'portrait', got {orientation!r}")
    areas = _DEFAULT_DISPLAY_AREAS[type]
    display_area = areas[orientation]
    return DeviceFrameAsset(
        type=type,
        orientation=orientation,
        image_path=None,
        display_area=display_area,
    )
