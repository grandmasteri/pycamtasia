"""Device frame overlay builder — wrap a clip with a phone/laptop bezel image."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from camtasia.effects.base import Effect
    from camtasia.project import Project
    from camtasia.timeline.clips.base import BaseClip

# Stub mapping from DeviceFrameType to bundled frame image paths.
# No frame images are bundled with pycamtasia — users must supply their own
# or download from the TechSmith asset library:
# https://library.techsmith.com/Camtasia
DEVICE_FRAME_LIBRARY_URL = 'https://library.techsmith.com/Camtasia'


class DeviceFrameType(str, Enum):
    """Device frame type presets matching Camtasia's Type dropdown."""

    IPHONE = 'iphone'
    IPAD = 'ipad'
    ANDROID_PHONE = 'android_phone'
    ANDROID_TABLET = 'android_tablet'
    MACBOOK = 'macbook'
    IMAC = 'imac'
    BROWSER = 'browser'
    TV = 'tv'
    WATCH = 'watch'


# Map from DeviceFrameType to a stub frame image path.
# These are placeholders — no frame images are bundled. Users must provide
# their own PNG files or download from DEVICE_FRAME_LIBRARY_URL.
_FRAME_IMAGE_STUBS: dict[DeviceFrameType, str | None] = dict.fromkeys(DeviceFrameType, None)


def add_device_frame(
    project: Project,
    frame_image_path: str | Path,
    wrapped_clip: BaseClip,
    *,
    track_name: str = 'Device Frame',
    scale: float = 1.0,
    frame_type: DeviceFrameType | None = None,
    fit_to_canvas: bool = False,
    orientation: str = 'landscape',
) -> BaseClip:
    """Overlay a device bezel image (phone, laptop, tablet, etc.) on top of a clip.

    The frame image is imported as media and placed on a new track above
    the wrapped clip's track, matching its start and duration. Users
    should supply a PNG with a transparent cutout where the video shows through.

    Args:
        project: Target project.
        frame_image_path: Path to the bezel PNG (should have a transparent cutout).
        wrapped_clip: The clip (typically a screen recording or video) to
            wrap. The frame inherits its start and duration.
        track_name: Name for the new track hosting the frame overlay.
            Will be placed above the wrapped clip's track.
        scale: Uniform scale factor applied to the frame clip.
        frame_type: Optional device frame type preset. Currently informational
            only — the actual frame image must be provided via *frame_image_path*.
            No bundled frame images are included; download from
            https://library.techsmith.com/Camtasia
        fit_to_canvas: When True, scale the frame clip to fill the project
            canvas dimensions.
        orientation: Frame orientation — ``'landscape'`` or ``'portrait'``.
            Currently informational; the caller is responsible for supplying
            a frame image in the correct orientation.

    Returns:
        The placed frame clip (IMFile).
    """
    from camtasia.timing import ticks_to_seconds

    media = project.import_media(frame_image_path)
    track = project.timeline.get_or_create_track(track_name)
    frame_clip = track.add_image(
        media.id,
        start_seconds=ticks_to_seconds(wrapped_clip.start),
        duration_seconds=ticks_to_seconds(wrapped_clip.duration),
    )
    if fit_to_canvas:
        canvas_w = project.width
        canvas_h = project.height
        frame_clip.scale = (canvas_w / 1920, canvas_h / 1080)
    else:
        frame_clip.scale = (scale, scale)
    return frame_clip


def remove_device_frame(
    project: Project,
    track_name: str = 'Device Frame',
) -> None:
    """Remove the device frame track created by :func:`add_device_frame`.

    Finds the track by name and removes it from the timeline.

    Args:
        project: Target project.
        track_name: Name of the device frame track to remove.

    Raises:
        ValueError: If no track with the given name exists.
    """
    removed = project.timeline.remove_tracks_by_name(track_name)
    if removed == 0:
        raise ValueError(f'No track named {track_name!r} found')


def add_device_frame_effect(
    clip: BaseClip,
    frame_type: DeviceFrameType,
) -> Effect:
    """Attach a DeviceFrame visual effect directly to a clip.

    This is distinct from :func:`add_device_frame` which uses an overlay
    image on a separate track. This function applies a DeviceFrame effect
    as a ``visualEffect`` on the clip itself, matching Camtasia's native
    DeviceFrame effect.

    Uses a raw dict-based approach since the DeviceFrame Effect class may
    be registered in a parallel track. If a ``@register_effect('DeviceFrame')``
    class exists, :func:`effect_from_dict` will dispatch to it automatically.

    Args:
        clip: The clip to apply the device frame effect to.
        frame_type: The device frame type preset.

    Returns:
        Wrapped :class:`Effect` instance.
    """
    effect_data: dict[str, Any] = {
        'effectName': 'DeviceFrame',
        'bypassed': False,
        'category': 'categoryVisualEffects',
        'parameters': {
            'frame-type': {
                'defaultValue': frame_type.value,
                'type': 'string',
                'interp': 'hold',
            },
        },
    }
    return clip.add_effect(effect_data)
