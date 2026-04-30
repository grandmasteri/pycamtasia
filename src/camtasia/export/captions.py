"""Caption extract/reimport for translation workflows."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from camtasia.project import Project


@dataclass
class CaptionEntry:
    """A single caption/subtitle entry.

    Attributes:
        start_seconds: Start time in seconds.
        duration_seconds: Duration in seconds.
        text: Caption text.
    """

    start_seconds: float
    duration_seconds: float
    text: str


def _parse_srt_time(ts: str) -> float:
    """Parse SRT timecode 'HH:MM:SS,mmm' to seconds."""
    m = re.match(r'(\d+):(\d+):(\d+)[,.](\d+)', ts.strip())
    if not m:
        raise ValueError(f'Invalid SRT timecode: {ts!r}')
    h, mn, s, ms = int(m[1]), int(m[2]), int(m[3]), int(m[4].ljust(3, '0')[:3])
    return h * 3600 + mn * 60 + s + ms / 1000


def _format_srt_time(seconds: float) -> str:
    """Format seconds as SRT timecode HH:MM:SS,mmm."""
    seconds = max(0.0, seconds)
    total_ms = round(seconds * 1000)
    h = total_ms // 3600000
    total_ms %= 3600000
    m = total_ms // 60000
    total_ms %= 60000
    s = total_ms // 1000
    ms = total_ms % 1000
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def import_captions_srt(path: Path) -> list[CaptionEntry]:
    """Parse an SRT subtitle file into caption entries.

    Args:
        path: Path to the .srt file.

    Returns:
        List of CaptionEntry parsed from the file.
    """
    text = Path(path).read_text(encoding='utf-8-sig')
    entries: list[CaptionEntry] = []
    blocks = re.split(r'\n\s*\n', text.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        # lines[0] = index, lines[1] = timecodes, lines[2:] = text
        tc = lines[1]
        m = re.match(r'(.+?)\s*-->\s*(.+)', tc)
        if not m:
            continue
        start = _parse_srt_time(m[1])
        end = _parse_srt_time(m[2])
        caption_text = '\n'.join(lines[2:])
        entries.append(CaptionEntry(
            start_seconds=round(start, 3),
            duration_seconds=round(end - start, 3),
            text=caption_text,
        ))
    return entries


def import_captions_vtt(path: Path) -> list[CaptionEntry]:
    """Parse a WebVTT subtitle file into caption entries.

    Args:
        path: Path to the .vtt file.

    Returns:
        List of CaptionEntry parsed from the file.
    """
    text = Path(path).read_text(encoding='utf-8-sig')
    entries: list[CaptionEntry] = []
    blocks = re.split(r'\n\s*\n', text.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        # Find the line with '-->'
        tc_idx = None
        for i, line in enumerate(lines):
            if '-->' in line:
                tc_idx = i
                break
        if tc_idx is None:
            continue
        m = re.match(r'(.+?)\s*-->\s*(.+)', lines[tc_idx])
        if not m:
            continue
        start = _parse_srt_time(m[1])
        end = _parse_srt_time(m[2])
        caption_text = '\n'.join(lines[tc_idx + 1:])
        if not caption_text:
            continue
        entries.append(CaptionEntry(
            start_seconds=round(start, 3),
            duration_seconds=round(end - start, 3),
            text=caption_text,
        ))
    return entries


def export_captions_srt(
    project: Project,
    path: str | Path,
    *,
    track_name: str = 'Subtitles',
) -> Path:
    """Export caption entries from a project track as an SRT file.

    Args:
        project: Source project.
        path: Destination .srt file path.
        track_name: Name of the caption track.

    Returns:
        The written path.

    Raises:
        KeyError: If no track with the given name exists.
    """
    from camtasia.timing import ticks_to_seconds
    out = Path(path)
    track = project.timeline.find_track_by_name(track_name)
    if track is None:
        raise KeyError(f'No track named {track_name!r}')
    lines: list[str] = []
    idx = 0
    for clip in track.clips:
        if clip.clip_type != 'Callout':
            continue
        idx += 1
        start = ticks_to_seconds(clip.start)
        end = start + ticks_to_seconds(clip.duration)
        text: str = (cast('dict', clip._data.get('def', {})) or {}).get('text', '')
        lines.append(str(idx))
        lines.append(f'{_format_srt_time(start)} --> {_format_srt_time(end)}')
        lines.append(text)
        lines.append('')
    out.write_text('\n'.join(lines), encoding='utf-8')
    return out


def export_captions_multilang(
    project: Project,
    output_dir: str | Path,
    languages: list[str],
    *,
    track_name: str = 'Subtitles',
) -> list[Path]:
    """Export one SRT file per language.

    Uses ``Project.captions_by_language`` if available, otherwise falls
    back to exporting the raw caption track for each language.

    Args:
        project: Source project.
        output_dir: Directory to write SRT files into.
        languages: Language codes to export (e.g. ['en', 'fr', 'de']).
        track_name: Name of the caption track (fallback).

    Returns:
        List of written file paths.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    if hasattr(project, 'captions_by_language'):
        by_lang = project.captions_by_language  # type: ignore[attr-defined]
        for lang in languages:
            srt_path = out_dir / f'{lang}.srt'
            entries = by_lang.get(lang, [])
            lines: list[str] = []
            for i, entry in enumerate(entries, 1):
                lines.append(str(i))
                start = entry.start_seconds
                end = start + entry.duration_seconds
                lines.append(f'{_format_srt_time(start)} --> {_format_srt_time(end)}')
                lines.append(entry.text)
                lines.append('')
            srt_path.write_text('\n'.join(lines), encoding='utf-8')
            paths.append(srt_path)
    else:
        for lang in languages:
            srt_path = out_dir / f'{lang}.srt'
            export_captions_srt(project, srt_path, track_name=track_name)
            paths.append(srt_path)
    return paths


def export_multilang_package(
    project: Project,
    output_dir: str | Path,
    languages: list[str],
    *,
    track_name: str = 'Subtitles',
) -> Path:
    """Export a multilanguage package with subfolders per language.

    Each language subfolder contains:
    - ``captions.srt`` — SRT captions for that language
    - ``metadata.json`` — language code and project info

    Args:
        project: Source project.
        output_dir: Root output directory.
        languages: Language codes to export.
        track_name: Name of the caption track (fallback).

    Returns:
        The root output directory path.
    """
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    srt_files = export_captions_multilang(
        project, root, languages, track_name=track_name,
    )
    for lang, srt_path in zip(languages, srt_files):
        lang_dir = root / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        srt_path.rename(lang_dir / 'captions.srt')
        metadata = {
            'language': lang,
            'track_name': track_name,
        }
        (lang_dir / 'metadata.json').write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding='utf-8',
        )
    return root


def export_captions(
    project: Project,
    output_path: str | Path,
    *,
    track_name: str = 'Subtitles',
) -> Path:
    """Extract caption entries from a subtitle/caption track to a JSON file.

    Useful for external translation workflows: export → translate → import.

    Args:
        project: Source project.
        output_path: Destination JSON file.
        track_name: Name of the track carrying caption callouts.

    Returns:
        The written path.

    Raises:
        KeyError: If no track with the given name exists.
    """
    from camtasia.timing import ticks_to_seconds
    path = Path(output_path)
    track = project.timeline.find_track_by_name(track_name)
    if track is None:
        raise KeyError(f'No track named {track_name!r}')
    entries: list[CaptionEntry] = []
    for clip in track.clips:
        if clip.clip_type != 'Callout':
            continue
        callout_def: dict = clip._data.get('def', {}) or {}  # type: ignore[assignment]
        text: str = callout_def.get('text', '')
        entries.append(CaptionEntry(
            start_seconds=round(ticks_to_seconds(clip.start), 3),
            duration_seconds=round(ticks_to_seconds(clip.duration), 3),
            text=text,
        ))
    path.write_text(json.dumps([asdict(e) for e in entries], indent=2, ensure_ascii=False))
    return path


def import_captions(
    project: Project,
    input_path: str | Path,
    *,
    track_name: str = 'Subtitles',
    overwrite: bool = True,
) -> int:
    """Import caption entries from a JSON file, updating text on existing
    clips with matching timing.

    Args:
        project: Target project.
        input_path: JSON file produced by :func:`export_captions`.
        track_name: Name of the caption track.
        overwrite: When True, update the text of existing clips whose
            start/duration match an entry. When False, raise if entry count
            differs from existing clip count.

    Returns:
        Number of caption entries updated.

    Raises:
        KeyError: No track with the given name exists.
        ValueError: overwrite=False and counts mismatch.
    """
    from camtasia.timing import ticks_to_seconds
    track = project.timeline.find_track_by_name(track_name)
    if track is None:
        raise KeyError(f'No track named {track_name!r}')
    raw = json.loads(Path(input_path).read_text())
    entries = [CaptionEntry(**e) for e in raw]
    callouts = [c for c in track.clips if c.clip_type == 'Callout']
    if not overwrite and len(entries) != len(callouts):
        raise ValueError(
            f'overwrite=False but entries={len(entries)} differs from '
            f'existing callouts={len(callouts)}'
        )
    # Match by (start_seconds, duration_seconds) tuple rounded to 0.001s
    by_key = {
        (round(ticks_to_seconds(c.start), 3), round(ticks_to_seconds(c.duration), 3)): c
        for c in callouts
    }
    updated = 0
    for entry in entries:
        key = (entry.start_seconds, entry.duration_seconds)
        match = by_key.get(key)
        if match is None:
            continue
        match._data.setdefault('def', {})['text'] = entry.text  # type: ignore[typeddict-item]
        updated += 1
    return updated


def export_burned_in_captions_stub(
    project: Project,
    dest_dir: str | Path,
    *,
    track_name: str = 'Subtitles',
) -> Path:
    """Export metadata describing captions that WOULD be burned into the video.

    Actual rendering of burned-in captions is out of scope for pycamtasia.
    This stub writes a JSON metadata file listing each caption entry with its
    timing and text, suitable for passing to an external rendering pipeline.

    Args:
        project: Source project.
        dest_dir: Directory to write the metadata file into.
        track_name: Name of the caption track.

    Returns:
        Path to the written ``burned_in_captions.json`` file.

    Raises:
        KeyError: If no track with the given name exists.
    """
    from camtasia.timing import ticks_to_seconds

    track = project.timeline.find_track_by_name(track_name)
    if track is None:
        raise KeyError(f'No track named {track_name!r}')

    entries: list[dict] = []
    for clip in track.clips:
        if clip.clip_type != 'Callout':
            continue
        callout_def: dict = clip._data.get('def', {}) or {}  # type: ignore[assignment]
        text: str = callout_def.get('text', '')
        entries.append({
            'start_seconds': round(ticks_to_seconds(clip.start), 3),
            'duration_seconds': round(ticks_to_seconds(clip.duration), 3),
            'text': text,
        })

    out_dir = Path(dest_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'burned_in_captions.json'
    metadata = {
        'format': 'pycamtasia-burned-in-stub',
        'version': '1.0',
        'note': 'Actual rendering is out of scope. This file describes captions for an external pipeline.',
        'track_name': track_name,
        'entry_count': len(entries),
        'entries': entries,
    }
    out_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    return out_path
