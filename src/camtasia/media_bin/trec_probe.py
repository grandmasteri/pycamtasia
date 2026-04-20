"""Probe .trec files using pymediainfo to extract stream metadata."""
from __future__ import annotations

import datetime
from fractions import Fraction
import os
from pathlib import Path
from typing import Any

# Static GUIDs for screen recording video tracks
_SCREEN_VIDEO_GUIDS = (
    '2b7b6a0b-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af0-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af1-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af2-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af3-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af5-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af6-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af7-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af8-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6af9-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6afa-7a1f-11e2-83d0-0017f200be7f;'
    '2b7b6afb-7a1f-11e2-83d0-0017f200be7f;'
)


def probe_trec(path: str | Path) -> dict[str, Any]:
    """Probe a .trec file and return source bin metadata.

    Uses pymediainfo to extract stream information and builds
    the sourceTracks array matching Camtasia's expected format.

    Args:
        path: Path to the .trec file.

    Returns:
        Dict with 'rect', 'sourceTracks', and 'lastMod' fields
        ready to merge into a source bin entry.

    Raises:
        ImportError: pymediainfo not installed.
        FileNotFoundError: .trec file not found.
    """
    try:
        import pymediainfo
    except ImportError:
        raise ImportError(
            'pymediainfo is required for .trec import. '
            'Install with: pip install pymediainfo'
        ) from None

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f'.trec file not found: {path}')

    mi = pymediainfo.MediaInfo.parse(str(path))
    filename = path.name

    source_tracks = []
    width = 0
    height = 0
    last_mod = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y%m%dT%H%M%S')

    for track in mi.tracks:
        if track.track_type == 'General':
            tagged = track.tagged_date or track.encoded_date or ''
            if tagged:
                # Convert 'UTC 2026-04-10 09:41:03' to '20260410T094103'
                parts = tagged.replace('UTC ', '').strip()
                try:
                    date_str = parts.split('.')[0]  # remove fractional seconds
                    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    last_mod = dt.strftime('%Y%m%dT%H%M%S')
                except ValueError:
                    last_mod = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y%m%dT%H%M%S')

        elif track.track_type == 'Video':
            w = track.width or 0
            h = track.height or 0
            if w > width:
                width = w
            if h > height:
                height = h

            codec = (track.codec_id or '').lower()
            tag = 1 if 'tsc' in codec else 0

            fps = track.frame_rate or 30.0
            frac = Fraction(float(fps)).limit_denominator(1000)
            sample_rate = f'{frac.numerator}/{frac.denominator}' if frac.denominator != 1 else int(float(fps))

            dur_ms = float(track.duration or 0)
            edit_rate = round(float(fps))
            range_end = round(dur_ms / 1000 * edit_rate)

            source_tracks.append({
                'range': [0, range_end],
                'type': 0,
                'editRate': edit_rate,
                'trackRect': [0, 0, w, h],
                'sampleRate': sample_rate,
                'bitDepth': 24,
                'numChannels': 0,
                'integratedLUFS': 100.0,
                'peakLevel': -1.0,
                'tag': tag,
                'metaData': f'{filename};{_SCREEN_VIDEO_GUIDS}' if tag == 1 else f'{filename};',
                'parameters': {},
            })

        elif track.track_type == 'Audio':
            raw_ch = track.channel_s or '1'
            channels = int(str(raw_ch).split('/')[0].strip())
            sample_rate = track.sampling_rate or 44100
            dur_ms = float(track.duration or 0)
            range_end = round(dur_ms / 1000 * int(float(sample_rate)))

            tag = 0

            source_tracks.append({
                'range': [0, range_end],
                'type': 2,
                'editRate': int(float(sample_rate)),
                'trackRect': [0, 0, 0, 0],
                'sampleRate': int(float(sample_rate)),
                'bitDepth': 16,
                'numChannels': channels,
                'integratedLUFS': 100.0,
                'peakLevel': -1.0,
                'tag': tag,
                'metaData': f'{filename};',
                'parameters': {},
            })

    return {
        'rect': [0, 0, width, height],
        'sourceTracks': source_tracks,
        'lastMod': last_mod,
        'loudnessNormalization': True,
    }
