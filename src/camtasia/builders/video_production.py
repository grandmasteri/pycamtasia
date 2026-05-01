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
    images: list[Path | str] = field(default_factory=list)
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
        *,
        template_name: str | None = None,
        library_asset: str | None = None,
    ) -> VideoProductionBuilder:
        self._intro = {
            'title': title, 'subtitle': subtitle, 'duration': duration,
            'template_name': template_name, 'library_asset': library_asset,
        }
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
        *,
        scale: float = 1.0,
        x_offset: float = 0.0,
        y_offset: float = 0.0,
    ) -> VideoProductionBuilder:
        self._watermark = {
            'path': Path(image_path),
            'opacity': opacity,
            'scale': scale,
            'x_offset': x_offset,
            'y_offset': y_offset,
        }
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
            meta = p.timeline._data.setdefault('metadata', {})
            if self._intro.get('template_name'):
                meta['introTemplateName'] = self._intro['template_name']
            if self._intro.get('library_asset'):
                meta['introLibraryAsset'] = self._intro['library_asset']

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
                track.add_video(media.id, start_seconds=cursor, duration_seconds=media.duration_seconds or 0.0)

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
                scale=self._watermark['scale'],
                x_offset=self._watermark['x_offset'],
                y_offset=self._watermark['y_offset'],
            )

        return {
            'sections': len(self._sections),
            'has_intro': self._intro is not None,
            'has_outro': self._outro is not None,
            'has_background_music': self._bg_music is not None,
            'has_watermark': self._watermark is not None,
            'total_duration': p.duration_seconds,
        }


def insert_intro_template(
    project: Project,
    template_name: str = 'default',
    *,
    duration: float = 5.0,
) -> dict[str, Any]:
    """Insert a minimal intro title card at the start of the timeline.

    Stub that uses :meth:`Project.add_title_card` to place a title card
    and records the template name in project metadata for downstream
    tooling.

    Args:
        project: The project to modify.
        template_name: Name of the intro template.
        duration: Duration of the intro card in seconds.

    Returns:
        Summary dict with ``template_name`` and ``duration``.
    """
    project.add_title_card(
        f'Intro: {template_name}',
        duration_seconds=duration,
        track_name='Intro',
        font_size=72.0,
    )
    project.timeline._data.setdefault('metadata', {})['pendingIntroTemplate'] = template_name
    return {'template_name': template_name, 'duration': duration}
