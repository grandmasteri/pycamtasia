from __future__ import annotations

from camtasia.timeline.clips.base import BaseClip


class UnifiedMedia(BaseClip):
    """A clip bundling video and audio from the same source (e.g., Camtasia Rev with mic).

    Contains a ``video`` child (ScreenVMFile) and an ``audio`` child (AMFile),
    both referencing the same .trec source file.
    """

    @property
    def video(self) -> BaseClip:
        """The video child clip (typically ScreenVMFile)."""
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(self._data['video'])

    @property
    def audio(self) -> BaseClip:
        """The audio child clip (typically AMFile)."""
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(self._data['audio'])

    @property
    def has_audio(self) -> bool:
        """Whether this unified media contains an audio track."""
        return 'audio' in self._data
