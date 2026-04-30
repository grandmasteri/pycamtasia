"""Clip type hierarchy and factory function.

Usage::

    from camtasia.timeline.clips import clip_from_dict

    clip = clip_from_dict(raw_dict)
"""
from __future__ import annotations

from typing import Any

from .audio import AMFile
from .base import EDIT_RATE, BaseClip
from .callout import Callout, CalloutBuilder
from .group import Group, GroupTrack
from .image import IMFile
from .placeholder import PlaceholderMedia
from .screen_recording import CursorType, ScreenIMFile, ScreenVMFile
from .stitched import StitchedMedia
from .unified import UnifiedMedia
from .video import VMFile

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
    'PlaceholderMedia': PlaceholderMedia,
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
    'AMFile',
    'BaseClip',
    'Callout',
    'CalloutBuilder',
    'CursorType',
    'Group',
    'GroupTrack',
    'IMFile',
    'PlaceholderMedia',
    'ScreenIMFile',
    'ScreenVMFile',
    'StitchedMedia',
    'UnifiedMedia',
    'VMFile',
    'clip_from_dict',
]
