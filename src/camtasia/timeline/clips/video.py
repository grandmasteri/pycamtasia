"""Video media clip (VMFile)."""
from __future__ import annotations

from .base import BaseClip


class VMFile(BaseClip):
    """Video media file clip.

    Minimal wrapper — video clips use mostly BaseClip properties.

    Args:
        data: The raw clip dict.
    """
