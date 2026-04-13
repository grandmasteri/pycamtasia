"""Clip type hierarchy and factory function.

Usage::

    from camtasia.timeline.clips import clip_from_dict

    clip = clip_from_dict(raw_dict)
"""
from __future__ import annotations

from typing import Any

from .base import BaseClip, EDIT_RATE
from .audio import AMFile
from .video import VMFile
from .image import IMFile
from .screen_recording import ScreenVMFile, ScreenIMFile
from .stitched import StitchedMedia
from .group import Group, GroupTrack
from .callout import Callout, CalloutBuilder
from .unified import UnifiedMedia

_TYPE_MAP: dict[str, type[BaseClip]] = {
    'AMFile': AMFile,
    'VMFile': VMFile,
    'IMFile': IMFile,
    'ScreenVMFile': ScreenVMFile,
    'ScreenIMFile': ScreenIMFile,
    'StitchedMedia': StitchedMedia,
    'Group': Group,
    'Callout': Callout,
    'UnifiedMedia': UnifiedMedia,
    'PlaceholderMedia': BaseClip,
}


def clip_from_dict(data: dict[str, Any]) -> BaseClip:
    """Create the appropriate clip subclass from a JSON dict.

    Args:
        data: Raw clip dict containing at least an ``_type`` key.

    Returns:
        A typed clip instance (``AMFile``, ``VMFile``, etc.), or
        ``BaseClip`` if the type is unrecognised.
    """
    cls = _TYPE_MAP.get(data.get('_type', ''), BaseClip)
    return cls(data)


__all__ = [
    'EDIT_RATE',
    'BaseClip',
    'AMFile',
    'VMFile',
    'IMFile',
    'ScreenVMFile',
    'ScreenIMFile',
    'StitchedMedia',
    'Group',
    'GroupTrack',
    'Callout',
    'CalloutBuilder',
    'UnifiedMedia',
    'clip_from_dict',
]
