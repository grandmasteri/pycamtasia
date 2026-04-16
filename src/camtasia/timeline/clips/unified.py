"""UnifiedMedia clip type for bundled video and audio."""

from __future__ import annotations

import sys
from typing import Any
if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

from camtasia.timeline.clips.base import BaseClip


_EFFECT_MSG = 'Effects must be added to .video or .audio, not the UnifiedMedia wrapper'


class UnifiedMedia(BaseClip):
    """A clip bundling video and audio from the same source (e.g., Camtasia Rev).

    Contains a ``video`` child and an ``audio`` child, both referencing the
    same .trec source file. The video child is either a ScreenVMFile (screen
    recording) or a VMFile (camera recording).
    """

    _video_cache: BaseClip | None = None
    _audio_cache: BaseClip | None = None

    @property
    def video(self) -> BaseClip:
        """The video child clip (ScreenVMFile or VMFile)."""
        if self._video_cache is None:
            from camtasia.timeline.clips import clip_from_dict
            self._video_cache = clip_from_dict(self._data['video'])
        return self._video_cache

    @property
    def audio(self) -> BaseClip:
        """The audio child clip (AMFile)."""
        if self._audio_cache is None:
            from camtasia.timeline.clips import clip_from_dict
            self._audio_cache = clip_from_dict(self._data['audio'])
        return self._audio_cache

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

    def set_source(self, source_id: int) -> Self:
        """Not supported on UnifiedMedia."""
        raise TypeError('Cannot set_source on UnifiedMedia; set it on .video or .audio instead')

    def add_effect(self, effect_data: dict[str, Any]) -> Any:
        raise TypeError(_EFFECT_MSG)

    def add_drop_shadow(self, **kwargs: Any) -> Any:
        raise TypeError(_EFFECT_MSG)

    def add_round_corners(self, **kwargs: Any) -> Any:
        raise TypeError(_EFFECT_MSG)

    def add_glow(self, **kwargs: Any) -> Any:
        raise TypeError(_EFFECT_MSG)

    def add_glow_timed(self, **kwargs: Any) -> Any:
        raise TypeError(_EFFECT_MSG)

    def mute_audio(self) -> Self:
        """Set audio gain to zero."""
        if self.has_audio:
            self._data['audio'].setdefault('attributes', {})['gain'] = 0.0
        return self
