"""Project validation — checks for common issues before save."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from importlib import resources as importlib_resources
import json
import threading
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


def _collect_ids_grouped(media: dict, ids_to_locs: dict[Any, list[str]], path: str) -> None:
    """Recursively collect clip IDs into a dict mapping id -> [locations]."""
    if media.get('id') is not None:
        ids_to_locs.setdefault(media['id'], []).append(path)
    for key in ('video', 'audio'):
        if key in media and isinstance(media[key], dict):
            _collect_ids_grouped(media[key], ids_to_locs, f'{path}/{key}')
    for track in media.get('tracks', []):
        for inner in track.get('medias', []):
            _collect_ids_grouped(inner, ids_to_locs, f'{path}/group{media.get("id")}')
    for inner in media.get('medias', []):
        _collect_ids_grouped(inner, ids_to_locs, f'{path}/stitched{media.get("id")}')


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
    ids_to_locs: dict[Any, list[str]] = {}
    tracks = _get_tracks(data)
    for ti, track in enumerate(tracks):
        for media in track.get('medias', []):
            _collect_ids_grouped(media, ids_to_locs, f'track[{ti}]')
    for mid, locs in ids_to_locs.items():
        if len(locs) > 1:
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


def _check_timeline_id_unique(data: dict[str, Any]) -> list[ValidationIssue]:
    """Check that timeline.id exists and doesn't collide with any clip id."""
    issues: list[ValidationIssue] = []
    timeline_id = data.get('timeline', {}).get('id')
    if timeline_id is None:
        issues.append(ValidationIssue('warning', 'timeline.id is missing'))
        return issues

    # Collect all clip IDs across the project
    def _walk_ids(media: dict) -> set[int]:
        ids: set[int] = set()
        mid = media.get('id')
        if isinstance(mid, int):
            ids.add(mid)
        for track in media.get('tracks', []):
            for m in track.get('medias', []):
                ids.update(_walk_ids(m))
        for m in media.get('medias', []):
            ids.update(_walk_ids(m))
        for key in ('video', 'audio'):
            sub = media.get(key)
            if isinstance(sub, dict):
                ids.update(_walk_ids(sub))
        return ids

    clip_ids: set[int] = set()
    for track in _get_tracks(data):
        for media in track.get('medias', []):
            clip_ids.update(_walk_ids(media))
    if timeline_id in clip_ids:
        issues.append(ValidationIssue(
            'warning',
            f'timeline.id={timeline_id} collides with a clip id',
        ))
    return issues


def _check_behavior_effect_structure(data: dict[str, Any]) -> list[ValidationIssue]:
    """Check that GenericBehaviorEffect has required in/center/out phases."""
    issues: list[ValidationIssue] = []

    def _walk(media: dict, path: str) -> None:
        for effect in media.get('effects', []):
            if effect.get('_type') == 'GenericBehaviorEffect':
                for phase in ('in', 'center', 'out'):
                    if phase not in effect:
                        issues.append(ValidationIssue(
                            'error',
                            f'{path} GenericBehaviorEffect missing {phase!r} phase',
                        ))
        for track in media.get('tracks', []):
            for m in track.get('medias', []):
                _walk(m, f'{path}/group{media.get("id")}')
        for m in media.get('medias', []):
            _walk(m, f'{path}/stitched{media.get("id")}')
        for key in ('video', 'audio'):
            sub = media.get(key)
            if isinstance(sub, dict):
                _walk(sub, f'{path}/{key}{media.get("id")}')

    for ti, track in enumerate(_get_tracks(data)):
        for media in track.get('medias', []):
            _walk(media, f'track[{ti}]')
    return issues


def _check_clip_overlap_on_track(data: dict[str, Any]) -> list[ValidationIssue]:
    """Check that clips on the same track don't overlap (single-occupancy invariant)."""
    issues: list[ValidationIssue] = []
    for ti, track in enumerate(_get_tracks(data)):
        medias = sorted(
            track.get('medias', []),
            key=lambda m: int(Fraction(str(m.get('start', 0)))),
        )
        for i in range(len(medias) - 1):
            a = medias[i]
            b = medias[i + 1]
            a_end = int(Fraction(str(a.get('start', 0)))) + int(Fraction(str(a.get('duration', 0))))
            b_start = int(Fraction(str(b.get('start', 0))))
            if a_end > b_start:
                issues.append(ValidationIssue(
                    'warning',
                    f'track[{ti}] clip id={a.get("id")} ends at {a_end} overlapping '
                    f'clip id={b.get("id")} starting at {b_start}',
                ))
    return issues


def _check_transition_null_endpoints(data: dict[str, Any]) -> list[ValidationIssue]:
    """Flag explicit null in transition leftMedia/rightMedia (format says omit)."""
    issues: list[ValidationIssue] = []
    for ti, track in enumerate(_get_tracks(data)):
        for i, t in enumerate(track.get('transitions', [])):
            for field in ('leftMedia', 'rightMedia'):
                if field in t and t[field] is None:
                    issues.append(ValidationIssue(
                        'warning',
                        f'track[{ti}] transition[{i}] has explicit {field}=null '
                        f'(Camtasia format expects the field to be omitted)',
                    ))
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


def _check_visual_track_order(data: dict) -> list[ValidationIssue]:
    """Check that animationTracks.visual segments are sorted by start time."""
    issues: list[ValidationIssue] = []
    tracks = _get_tracks(data)
    for ti, track in enumerate(tracks):
        for media in track.get('medias', []):
            mid = media.get('id')
            visual = media.get('animationTracks', {}).get('visual', [])
            if len(visual) < 2:
                continue
            times = [seg.get('range', [0])[0] for seg in visual]
            if not all(times[i] <= times[i + 1] for i in range(len(times) - 1)):
                issues.append(ValidationIssue(
                    'error',
                    f'track[{ti}] clip id={mid} has unsorted animationTracks.visual segments',
                    source_id=mid,
                ))
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
    issues.extend(_check_timeline_id_unique(data))
    issues.extend(_check_behavior_effect_structure(data))
    issues.extend(_check_clip_overlap_on_track(data))
    issues.extend(_check_transition_null_endpoints(data))
    issues.extend(_check_visual_track_order(data))
    return issues


_schema_lock = threading.Lock()
_CACHED_SCHEMA: dict[str, Any] | None = None


def _get_schema() -> dict[str, Any]:
    """Load and cache the Camtasia project JSON schema (thread-safe)."""
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is None:
        with _schema_lock:
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


def _relative_luminance(rgba: list[int]) -> float:
    """Compute WCAG 2.x relative luminance from an RGBA list (0-255)."""
    channels = []
    for c in rgba[:3]:
        s = c / 255.0
        channels.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(fg: list[int], bg: list[int]) -> float:
    """Compute WCAG contrast ratio between two RGBA colors."""
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def validate_caption_accessibility(
    project: Any,
    *,
    max_words_per_line: int = 7,
    max_duration_seconds: float = 7.0,
    min_contrast_ratio: float = 4.5,
) -> list[dict]:
    """Check caption clips for accessibility issues.

    Inspects all Callout clips on the 'Subtitles' track and returns a list
    of issue dicts. Each dict has keys: ``type``, ``clip_index``, ``message``,
    and optionally ``value``.

    Checks performed:

    - ``line_too_long``: A line exceeds *max_words_per_line* words.
    - ``duration_too_long``: Clip duration exceeds *max_duration_seconds*.
    - ``duration_too_short``: Clip duration is less than 1 second.
    - ``low_contrast``: Foreground/background contrast ratio is below
      *min_contrast_ratio*. Returns ``None`` for contrast if colors are
      unavailable.

    Args:
        project: A :class:`~camtasia.project.Project` instance.
        max_words_per_line: Maximum words allowed per caption line.
        max_duration_seconds: Maximum caption duration in seconds.
        min_contrast_ratio: Minimum WCAG contrast ratio.

    Returns:
        List of issue dicts.
    """
    from camtasia.timing import ticks_to_seconds

    issues: list[dict] = []

    # Get caption attributes for contrast check
    attrs = project.timeline.caption_attributes
    fg = getattr(attrs, 'foreground_color', None)
    bg = getattr(attrs, 'background_color', None)

    contrast: float | None = None
    if fg is not None and bg is not None:
        contrast = _contrast_ratio(fg, bg)

    if contrast is not None and contrast < min_contrast_ratio:
        issues.append({
            'type': 'low_contrast',
            'clip_index': None,
            'message': (
                f'Caption contrast ratio {contrast:.2f} is below '
                f'minimum {min_contrast_ratio}'
            ),
            'value': round(contrast, 2),
        })

    # Find subtitle track
    track = project.timeline.find_track_by_name('Subtitles')
    if track is None:
        return issues

    idx = 0
    for clip in track.clips:
        if clip.clip_type != 'Callout':
            continue
        duration_s = ticks_to_seconds(clip.duration)
        text: str = (clip._data.get('def', {}) or {}).get('text', '')

        # Check duration
        if duration_s > max_duration_seconds:
            issues.append({
                'type': 'duration_too_long',
                'clip_index': idx,
                'message': (
                    f'Caption {idx} duration {duration_s:.1f}s exceeds '
                    f'maximum {max_duration_seconds}s'
                ),
                'value': round(duration_s, 3),
            })
        if duration_s < 1.0:
            issues.append({
                'type': 'duration_too_short',
                'clip_index': idx,
                'message': (
                    f'Caption {idx} duration {duration_s:.1f}s is below '
                    f'minimum 1.0s'
                ),
                'value': round(duration_s, 3),
            })

        # Check words per line
        for line in text.splitlines():
            word_count = len(line.split())
            if word_count > max_words_per_line:
                issues.append({
                    'type': 'line_too_long',
                    'clip_index': idx,
                    'message': (
                        f'Caption {idx} line has {word_count} words '
                        f'(max {max_words_per_line})'
                    ),
                    'value': word_count,
                })

        idx += 1

    return issues
