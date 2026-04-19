"""UnifiedMedia clip type for bundled video and audio."""

from __future__ import annotations

import sys
from typing import Any, NoReturn

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

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)
        self._video_cache: BaseClip | None = None
        self._audio_cache: BaseClip | None = None

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

    def set_source(self, source_id: int) -> NoReturn:
        """Not supported on UnifiedMedia."""
        raise TypeError('Cannot set_source on UnifiedMedia; set it on .video or .audio instead')

    def add_effect(self, effect_data: dict[str, Any]) -> NoReturn:
        raise TypeError(_EFFECT_MSG)

    def add_drop_shadow(
        self,
        offset: float = 5,
        blur: float = 10,
        opacity: float = 0.5,
        angle: float = 5.5,
        color: tuple[float, float, float] = (0, 0, 0),
        enabled: int = 1,
    ) -> NoReturn:
        raise TypeError(_EFFECT_MSG)

    def add_round_corners(self, radius: float = 12.0) -> NoReturn:
        raise TypeError(_EFFECT_MSG)

    def add_glow(self, radius: float = 35.0, intensity: float = 0.35) -> NoReturn:
        raise TypeError(_EFFECT_MSG)

    def add_glow_timed(
        self,
        start_seconds: float = 0.0,
        duration_seconds: float = 0.0,
        radius: float = 35.0,
        intensity: float = 0.35,
        fade_in_seconds: float = 0.4,
        fade_out_seconds: float = 1.0,
    ) -> NoReturn:
        raise TypeError(_EFFECT_MSG)

    def copy_effects_from(self, source: Any) -> NoReturn:
        raise TypeError(_EFFECT_MSG)

    def duplicate_effects_to(self, target: BaseClip) -> NoReturn:
        raise TypeError('Cannot duplicate effects from UnifiedMedia wrapper; access .video or .audio effects directly')

    def mute_audio(self) -> Self:
        """Set audio gain to zero."""
        if self.has_audio:
            self._data['audio'].setdefault('attributes', {})['gain'] = 0.0
        return self
