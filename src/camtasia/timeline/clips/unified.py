"""UnifiedMedia clip type for bundled video and audio."""

from __future__ import annotations

import sys
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from camtasia.timeline.clips.base import BaseClip


class UnifiedMedia(BaseClip):
    """A clip bundling video and audio from the same source (e.g., Camtasia Rev).

    Contains a ``video`` child and an ``audio`` child, both referencing the
    same .trec source file. The video child is either a ScreenVMFile (screen
    recording) or a VMFile (camera recording).
    """

    @property
    def video(self) -> BaseClip:
        """The video child clip (ScreenVMFile or VMFile)."""
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(self._data['video'])

    @property
    def audio(self) -> BaseClip:
        """The audio child clip (AMFile)."""
        from camtasia.timeline.clips import clip_from_dict
        return clip_from_dict(self._data['audio'])

    @property
    def has_audio(self) -> bool:
        """Whether this unified media contains an audio track."""
        return 'audio' in self._data

    @property
    def is_screen_recording(self) -> bool:
        """Whether the video child is a screen recording (vs camera)."""
        return bool(self._data.get('video', {}).get('_type') == 'ScreenVMFile')

    @property
    def is_camera(self) -> bool:
        """Whether the video child is a camera recording."""
        return bool(self._data.get('video', {}).get('_type') == 'VMFile')

    @property
    def source_id(self) -> int | None:
        """Source bin ID from the video child."""
        return self._data.get('video', {}).get('src')

    def mute_audio(self) -> Self:
        """Set audio gain to zero."""
        if self.has_audio:
            self._data['audio']['gain'] = 0.0
        return self
