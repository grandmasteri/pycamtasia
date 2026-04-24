"""Fluent builder for assembling video productions from high-level steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from camtasia.project import Project


@dataclass
class _Section:
    name: str
    voiceover: Path | None = None
    images: list[Path] = field(default_factory=list)
    screen_recording: Path | None = None


class VideoProductionBuilder:
    """Fluent builder that chains high-level video production steps.

    Delegates all timeline work to existing :class:`Project` methods.

    Usage::

        (VideoProductionBuilder(project)
            .add_intro(title='Welcome', duration=3.0)
            .add_section('Demo', voiceover=Path('demo.wav'))
            .add_outro(text='Thanks!')
            .add_background_music(Path('bg.mp3'), volume=0.3)
            .build())
    """

    def __init__(self, project: Project) -> None:
        self._project = project
        self._intro: dict[str, Any] | None = None
        self._outro: dict[str, Any] | None = None
        self._sections: list[_Section] = []
        self._bg_music: dict[str, Any] | None = None
        self._watermark: dict[str, Any] | None = None

    def add_intro(
        self,
        title: str,
        subtitle: str = '',
        duration: float = 5.0,
    ) -> VideoProductionBuilder:
        self._intro = {'title': title, 'subtitle': subtitle, 'duration': duration}
        return self

    def add_section(
        self,
        name: str,
        *,
        voiceover: Path | str | None = None,
        images: list[Path | str] | None = None,
        screen_recording: Path | str | None = None,
    ) -> VideoProductionBuilder:
        self._sections.append(_Section(
            name=name,
            voiceover=Path(voiceover) if voiceover else None,
            images=[Path(p) for p in images] if images else [],
            screen_recording=Path(screen_recording) if screen_recording else None,
        ))
        return self

    def add_outro(
        self,
        text: str = 'Thank You',
        duration: float = 5.0,
    ) -> VideoProductionBuilder:
        self._outro = {'text': text, 'duration': duration}
        return self

    def add_background_music(
        self,
        audio_path: Path | str,
        volume: float = 0.3,
    ) -> VideoProductionBuilder:
        self._bg_music = {'path': Path(audio_path), 'volume': volume}
        return self

    def add_watermark(
        self,
        image_path: Path | str,
        opacity: float = 0.3,
    ) -> VideoProductionBuilder:
        self._watermark = {'path': Path(image_path), 'opacity': opacity}
        return self

    def build(self) -> dict[str, Any]:
        """Execute all queued steps and return a summary dict."""
        p = self._project

        if self._intro:
            p.add_title_card(
                self._intro['title'],
                duration_seconds=self._intro['duration'],
                track_name='Intro',
                font_size=72.0,
            )
            if self._intro['subtitle']:
                p.add_title_card(
                    self._intro['subtitle'],
                    duration_seconds=self._intro['duration'],
                    track_name='Intro Subtitle',
                    font_size=36.0,
                )

        for section in self._sections:
            cursor = p.duration_seconds
            p.add_section_divider(section.name, at_seconds=cursor)

            if section.voiceover:
                p.add_voiceover_sequence_v2(
                    [section.voiceover],
                    start_seconds=cursor,
                )

            if section.images:
                p.add_image_sequence(
                    section.images,
                    start_seconds=cursor,
                )

            if section.screen_recording:
                media = p.import_media(section.screen_recording)
                track = p.timeline.get_or_create_track('Screen Recording')
                track.add_video(media.id, start_seconds=cursor, duration_seconds=media.duration_seconds)

        if self._outro:
            p.add_end_card(
                title_text=self._outro['text'],
                duration_seconds=self._outro['duration'],
            )

        if self._bg_music:
            p.add_background_music(
                self._bg_music['path'],
                volume=self._bg_music['volume'],
            )

        if self._watermark:
            p.add_watermark(
                self._watermark['path'],
                opacity=self._watermark['opacity'],
            )

        return {
            'sections': len(self._sections),
            'has_intro': self._intro is not None,
            'has_outro': self._outro is not None,
            'has_background_music': self._bg_music is not None,
            'has_watermark': self._watermark is not None,
            'total_duration': p.duration_seconds,
        }
