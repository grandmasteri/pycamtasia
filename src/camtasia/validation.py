"""Project validation — checks for common issues before save."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from importlib import resources as importlib_resources
import json
from typing import Any


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation finding.

    Attributes:
        level: ``'warning'`` or ``'error'``.
        message: Human-readable description of the issue.
        source_id: Related source-bin ID, if applicable.
    """

    level: str
    message: str
    source_id: int | None = None


def _collect_ids(media: dict, ids: list, path: str) -> None:
    """Recursively collect clip IDs from a media dict."""
    if media.get('id') is not None:
        ids.append((media['id'], path))
    for key in ('video', 'audio'):
        if key in media and isinstance(media[key], dict):
            _collect_ids(media[key], ids, f'{path}/{key}')
    for track in media.get('tracks', []):
        for inner in track.get('medias', []):
            _collect_ids(inner, ids, f'{path}/group{media.get("id")}')
    for inner in media.get('medias', []):
        _collect_ids(inner, ids, f'{path}/stitched{media.get("id")}')


def _get_tracks(data: dict) -> list:
    """Extract top-level tracks from project data, safely handling empty scenes."""
    scenes = data.get('timeline', {}).get('sceneTrack', {}).get('scenes', [{}])
    if not scenes:
        return []
    result: list = scenes[0].get('csml', {}).get('tracks', [])
    return result


def _check_duplicate_clip_ids(data: dict) -> list[ValidationIssue]:
    """Check for duplicate clip IDs across all tracks."""
    issues: list[ValidationIssue] = []
    all_ids: list[tuple] = []
    tracks = _get_tracks(data)
    for ti, track in enumerate(tracks):
        for media in track.get('medias', []):
            _collect_ids(media, all_ids, f'track[{ti}]')
    counts = Counter(mid for mid, _ in all_ids)
    for mid, count in counts.items():
        if count > 1:
            locs = [loc for i, loc in all_ids if i == mid]
            issues.append(ValidationIssue('error', f'Duplicate clip ID {mid} in: {locs}'))
    return issues


def _check_track_indices(data: dict) -> list[ValidationIssue]:
    """Check that trackIndex values match array positions, recursing into Groups."""
    issues: list[ValidationIssue] = []

    def _check_tracks(tracks: list, path: str) -> None:
        for i, track in enumerate(tracks):
            idx = track.get('trackIndex')
            if idx != i:
                issues.append(ValidationIssue('warning', f'{path}[{i}] has trackIndex={idx} (expected {i})'))
            for media in track.get('medias', []):
                inner = media.get('tracks', [])
                if inner:
                    _check_tracks(inner, f'{path}[{i}]/group{media.get("id")}')

    tracks = _get_tracks(data)
    _check_tracks(tracks, 'Track array')
    return issues


def _check_transition_references(data: dict) -> list[ValidationIssue]:
    """Check that all transitions reference existing clips on their track, recursing into Groups."""
    issues: list[ValidationIssue] = []

    def _check_tracks(tracks: list, path: str) -> None:
        for ti, track in enumerate(tracks):
            clip_ids = {m['id'] for m in track.get('medias', []) if 'id' in m}
            for j, trans in enumerate(track.get('transitions', [])):
                left = trans.get('leftMedia')
                right = trans.get('rightMedia')
                if left is not None and left not in clip_ids:
                    issues.append(ValidationIssue(
                        'error',
                        f'{path}[{ti}] transition[{j}] leftMedia={left} '
                        f'not found in track clips {clip_ids}'
                    ))
                if right is not None and right not in clip_ids:
                    issues.append(ValidationIssue(
                        'error',
                        f'{path}[{ti}] transition[{j}] rightMedia={right} '
                        f'not found in track clips {clip_ids}'
                    ))
            for media in track.get('medias', []):
                inner = media.get('tracks', [])
                if inner:
                    _check_tracks(inner, f'{path}[{ti}]/group{media.get("id")}')

    tracks = _get_tracks(data)
    _check_tracks(tracks, 'Track')
    return issues


def _check_transition_completeness(data: dict) -> list[ValidationIssue]:
    """Check that every transition has at least one of leftMedia/rightMedia and required keys."""
    issues: list[ValidationIssue] = []

    def _check_tracks(tracks: list, path: str) -> None:
        for ti, track in enumerate(tracks):
            for j, trans in enumerate(track.get('transitions', [])):
                if trans.get('leftMedia') is None and trans.get('rightMedia') is None:
                    issues.append(ValidationIssue(
                        'error',
                        f'{path}[{ti}] transition[{j}] has neither leftMedia nor rightMedia',
                    ))
                for key in ('name', 'duration'):
                    if key not in trans:
                        issues.append(ValidationIssue(
                            'error',
                            f'{path}[{ti}] transition[{j}] missing required key {key!r}',
                        ))
            for media in track.get('medias', []):
                inner = media.get('tracks', [])
                if inner:
                    _check_tracks(inner, f'{path}[{ti}]/group{media.get("id")}')

    tracks = _get_tracks(data)
    _check_tracks(tracks, 'Track')
    return issues


def _check_track_attributes_count(data: dict) -> list[ValidationIssue]:
    """Check that trackAttributes length matches the number of top-level tracks."""
    issues: list[ValidationIssue] = []
    tracks = _get_tracks(data)
    attrs = data.get('timeline', {}).get('trackAttributes', [])
    if len(attrs) != len(tracks):
        issues.append(ValidationIssue(
            'warning',
            f'trackAttributes length ({len(attrs)}) != tracks length ({len(tracks)})',
        ))
    return issues


def _check_src_references(data: dict) -> list[ValidationIssue]:
    """Check that all clip src values reference existing sourceBin IDs."""
    issues: list[ValidationIssue] = []
    source_ids = {s.get('id') for s in data.get('sourceBin', []) if s.get('id') is not None}
    tracks = _get_tracks(data)

    def _check_medias(medias: list, path: str) -> None:
        for media in medias:
            src = media.get('src')
            if src is not None and src not in source_ids:
                issues.append(ValidationIssue(
                    'error',
                    f'{path} clip id={media.get("id")} src={src} not found in sourceBin',
                ))
            for inner_track in media.get('tracks', []):
                _check_medias(inner_track.get('medias', []),
                              f'{path}/group{media.get("id")}')
            # Recurse into StitchedMedia
            _check_medias(media.get('medias', []),
                          f'{path}/stitched{media.get("id")}')
            # Recurse into UnifiedMedia
            for key in ('video', 'audio'):
                sub = media.get(key)
                if sub is not None:
                    _check_medias([sub], f'{path}/{key}{media.get("id")}')

    for ti, track in enumerate(tracks):
        _check_medias(track.get('medias', []), f'track[{ti}]')
    return issues


def _check_group_required_fields(data: dict) -> list[ValidationIssue]:
    """Check that Group clips have required parameters and metadata keys."""
    issues: list[ValidationIssue] = []
    required_params = {'geometryCrop0', 'geometryCrop1', 'geometryCrop2', 'geometryCrop3', 'volume'}
    required_meta = {'clipSpeedAttribute', 'effectApplied', 'isOpen'}
    try:
        version_str = str(data.get('version', '0'))
        major = int(version_str.split('.')[0])
        version = float(major)
    except (ValueError, TypeError, IndexError):
        version = 0.0
    if version >= 10.0:
        required_meta = required_meta | {'colorAttribute'}
    check_meta = version >= 8.0

    def _check_medias(medias: list, path: str) -> None:
        for media in medias:
            if media.get('_type') == 'Group':
                mid = media.get('id')
                params = set(media.get('parameters', {}).keys())
                missing_p = required_params - params
                if missing_p:
                    issues.append(ValidationIssue(
                        'warning',
                        f'{path} group id={mid} missing parameters: {sorted(missing_p)}',
                    ))
                if check_meta:
                    meta = set(media.get('metadata', {}).keys())
                    missing_m = required_meta - meta
                    if missing_m:
                        issues.append(ValidationIssue(
                            'warning',
                            f'{path} group id={mid} missing metadata: {sorted(missing_m)}',
                        ))
                for inner_track in media.get('tracks', []):
                    _check_medias(inner_track.get('medias', []),
                                  f'{path}/group{mid}')
            elif media.get('_type') == 'StitchedMedia':
                _check_medias(media.get('medias', []), path)
            elif media.get('_type') == 'UnifiedMedia':
                for key in ('video', 'audio'):
                    sub = media.get(key)
                    if sub:
                        _check_medias([sub], path)

    tracks = _get_tracks(data)
    for ti, track in enumerate(tracks):
        _check_medias(track.get('medias', []), f'track[{ti}]')
    return issues


def _check_clip_timing(data: dict) -> list[ValidationIssue]:
    """Check for clips with negative start or zero/negative duration."""
    issues: list[ValidationIssue] = []

    def _check_medias(medias: list, path: str, nested: bool = False) -> None:
        for media in medias:
            mid = media.get('id')
            start = media.get('start', 0)
            duration = media.get('duration')
            if not nested and start < 0:
                issues.append(ValidationIssue(
                    'warning',
                    f'{path} clip id={mid} has negative start={start}',
                ))
            if duration is not None and duration <= 0:
                issues.append(ValidationIssue(
                    'warning',
                    f'{path} clip id={mid} has non-positive duration={duration}',
                ))
            for inner_track in media.get('tracks', []):
                _check_medias(inner_track.get('medias', []),
                              f'{path}/group{mid}', nested=True)
            _check_medias(media.get('medias', []),
                          f'{path}/stitched{mid}', nested=True)
            for key in ('video', 'audio'):
                sub = media.get(key)
                if sub is not None:
                    _check_medias([sub], f'{path}/{key}{media.get("id", "")}', nested=True)

    tracks = _get_tracks(data)
    for ti, track in enumerate(tracks):
        _check_medias(track.get('medias', []), f'track[{ti}]')
    return issues


def _check_timing_consistency(data: dict) -> list[ValidationIssue]:
    """Check that mediaDuration ≈ duration / scalar for clips with non-unity scalar."""
    issues: list[ValidationIssue] = []

    def _check_medias(medias: list, path: str) -> None:
        for media in medias:
            scalar_raw = media.get('scalar', 1)
            duration = media.get('duration')
            media_dur = media.get('mediaDuration')
            if duration is not None and media_dur is not None and scalar_raw not in (1, 1.0, '1', '1/1') and media.get('_type') not in ('IMFile', 'ScreenIMFile', 'Group', 'StitchedMedia', 'UnifiedMedia', 'Callout'):
                from fractions import Fraction
                try:
                    scalar = Fraction(str(scalar_raw))
                except (ValueError, ZeroDivisionError):
                    continue
                if scalar == 0:
                    issues.append(ValidationIssue(
                        'error',
                        f'{path} clip id={media.get("id")} has scalar=0 (invalid)',
                    ))
                elif scalar != 0:
                    expected = float(Fraction(duration) / scalar)
                    media_dur_f = float(Fraction(str(media_dur)))
                    if abs(expected - media_dur_f) > max(1, abs(expected) * 0.01):
                        issues.append(ValidationIssue(
                            'warning',
                            f'{path} clip id={media.get("id")} mediaDuration={media_dur} '
                            f'!= duration/scalar ({duration}/{scalar_raw} ≈ {expected:.0f})',
                        ))
            for inner_track in media.get('tracks', []):
                _check_medias(inner_track.get('medias', []),
                              f'{path}/group{media.get("id")}')
            _check_medias(media.get('medias', []),
                          f'{path}/stitched{media.get("id")}')
            for key in ('video', 'audio'):
                sub = media.get(key)
                if sub is not None:
                    _check_medias([sub], f'{path}/{key}{media.get("id")}')

    tracks = _get_tracks(data)
    for ti, track in enumerate(tracks):
        _check_medias(track.get('medias', []), f'track[{ti}]')
    return issues


def _check_edit_rate(data: dict[str, Any]) -> list[ValidationIssue]:
    """Check that editRate is the expected 705600000."""
    issues: list[ValidationIssue] = []
    edit_rate = data.get('editRate')
    if edit_rate is None:
        issues.append(ValidationIssue('error', 'editRate is missing'))
    elif edit_rate != 705600000:
        issues.append(ValidationIssue('warning', f'editRate is {edit_rate}, expected 705600000'))
    return issues


def _check_source_bin_ids(data: dict[str, Any]) -> list[ValidationIssue]:
    """Check for duplicate sourceBin entry IDs."""
    issues: list[ValidationIssue] = []
    seen: dict[int, str] = {}
    for entry in data.get('sourceBin', []):
        eid = entry.get('id')
        if eid is None:
            issues.append(ValidationIssue('error', f'sourceBin entry missing id field: {entry.get("src", "<no src>")}'))
            continue
        if eid in seen:
            issues.append(ValidationIssue('error', f'Duplicate sourceBin ID {eid}'))
        seen[eid] = entry.get('src', '')
    return issues


def _check_compound_invariants(data: dict[str, Any]) -> list[ValidationIssue]:
    """Check structural invariants on compound clips.

    Invariants (verified against real TechSmith fixtures):
    - UnifiedMedia: wrapper.start/duration/mediaDuration/mediaStart/scalar == video/audio sub-clip values.
    - StitchedMedia: inner.start and inner.duration are integers (not string fractions).

    (StitchedMedia sum-of-inner-durations and Group inner-end-fit-wrapper were tried but fire
    on real TechSmith projects that legitimately trim/replay compound content — not invariants.)
    """
    issues: list[ValidationIssue] = []

    def _check(media: dict, path: str) -> None:
        mid = media.get('id')
        mtype = media.get('_type')

        if mtype == 'UnifiedMedia':
            for sub_key in ('video', 'audio'):
                sub = media.get(sub_key)
                if sub is None:
                    continue
                for field in ('start', 'duration', 'mediaDuration', 'mediaStart', 'scalar'):
                    if field in media and field in sub and str(media[field]) != str(sub[field]):
                        issues.append(ValidationIssue(
                            'warning',
                            f'{path} UnifiedMedia id={mid} {sub_key}.{field}={sub[field]} '
                            f'!= wrapper.{field}={media[field]}',
                        ))

        if mtype == 'StitchedMedia':
            for i, inner in enumerate(media.get('medias', [])):
                for field in ('start', 'duration'):
                    raw = inner.get(field)
                    if isinstance(raw, str) and '/' in raw:
                        issues.append(ValidationIssue(
                            'error',
                            f'{path} StitchedMedia id={mid} segment[{i}].{field}={raw!r} '
                            f'is a string fraction (must be integer tick)',
                        ))

        # Recurse
        for inner_track in media.get('tracks', []):
            for inner in inner_track.get('medias', []):
                _check(inner, f'{path}/group{mid}')
        for inner in media.get('medias', []):
            _check(inner, f'{path}/stitched{mid}')
        for key in ('video', 'audio'):
            sub = media.get(key)
            if sub is not None:
                _check(sub, f'{path}/{key}{mid}')

    tracks = _get_tracks(data)
    for ti, track in enumerate(tracks):
        for media in track.get('medias', []):
            _check(media, f'track[{ti}]')
    return issues


def validate_all(data: dict[str, Any]) -> list[ValidationIssue]:
    """Run all structural validation checks on project data."""
    issues: list[ValidationIssue] = []
    issues.extend(_check_duplicate_clip_ids(data))
    issues.extend(_check_track_indices(data))
    issues.extend(_check_transition_references(data))
    issues.extend(_check_transition_completeness(data))
    issues.extend(_check_track_attributes_count(data))
    issues.extend(_check_src_references(data))
    issues.extend(_check_group_required_fields(data))
    issues.extend(_check_clip_timing(data))
    issues.extend(_check_edit_rate(data))
    issues.extend(_check_source_bin_ids(data))
    issues.extend(_check_timing_consistency(data))
    issues.extend(_check_compound_invariants(data))
    return issues


_CACHED_SCHEMA: dict[str, Any] | None = None


def _get_schema() -> dict[str, Any]:
    """Load and cache the Camtasia project JSON schema."""
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is None:
        schema_path = importlib_resources.files('camtasia.resources') / 'camtasia-project-schema.json'
        _CACHED_SCHEMA = json.loads(schema_path.read_text(encoding='utf-8'))
    return _CACHED_SCHEMA


def validate_against_schema(project_data: dict[str, Any]) -> list[ValidationIssue]:
    """Validate project data against the Camtasia JSON schema.

    Returns:
        A list of :class:`ValidationIssue` for each schema violation.
    """
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return [ValidationIssue('warning', 'jsonschema not installed; skipping schema validation')]  # pragma: no cover

    schema = _get_schema()

    issues: list[ValidationIssue] = []
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(project_data):
        path = '/'.join(str(p) for p in error.absolute_path) or '(root)'
        issues.append(ValidationIssue('error', f'Schema violation at {path}: {error.message}'))
    return issues
