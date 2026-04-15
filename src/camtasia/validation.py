"""Project validation — checks for common issues before save."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from importlib import resources as importlib_resources
from typing import Any


@dataclass
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
    mid = media.get('id')
    if mid is not None:
        ids.append((mid, path))
    for key in ('video', 'audio'):
        if key in media:
            sid = media[key].get('id')
            if sid is not None:
                ids.append((sid, f'{path}/{key}'))
    for track in media.get('tracks', []):
        for inner in track.get('medias', []):
            _collect_ids(inner, ids, f'{path}/group{mid}')


def _check_duplicate_clip_ids(data: dict) -> list[ValidationIssue]:
    """Check for duplicate clip IDs across all tracks."""
    issues: list[ValidationIssue] = []
    all_ids: list[tuple] = []
    tracks = data.get('timeline', {}).get('sceneTrack', {}).get('scenes', [{}])[0].get('csml', {}).get('tracks', [])
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
    """Check that trackIndex values match array positions."""
    issues: list[ValidationIssue] = []
    tracks = data.get('timeline', {}).get('sceneTrack', {}).get('scenes', [{}])[0].get('csml', {}).get('tracks', [])
    for i, track in enumerate(tracks):
        idx = track.get('trackIndex')
        if idx != i:
            issues.append(ValidationIssue('warning', f'Track array[{i}] has trackIndex={idx} (expected {i})'))
    return issues


def _check_transition_references(data: dict) -> list[ValidationIssue]:
    """Check that all transitions reference existing clips on their track."""
    issues: list[ValidationIssue] = []
    tracks = (data.get('timeline', {}).get('sceneTrack', {})
              .get('scenes', [{}])[0].get('csml', {}).get('tracks', []))
    for ti, track in enumerate(tracks):
        clip_ids = {m['id'] for m in track.get('medias', [])}
        for j, trans in enumerate(track.get('transitions', [])):
            left = trans.get('leftMedia')
            right = trans.get('rightMedia')
            if left is not None and left not in clip_ids:
                issues.append(ValidationIssue(
                    'error',
                    f'Track[{ti}] transition[{j}] leftMedia={left} '
                    f'not found in track clips {clip_ids}'
                ))
            if right is not None and right not in clip_ids:
                issues.append(ValidationIssue(
                    'error',
                    f'Track[{ti}] transition[{j}] rightMedia={right} '
                    f'not found in track clips {clip_ids}'
                ))
    return issues


def validate_against_schema(project_data: dict[str, Any]) -> list[ValidationIssue]:
    """Validate project data against the Camtasia JSON schema.

    Returns:
        A list of :class:`ValidationIssue` for each schema violation.
    """
    try:
        import jsonschema
    except ImportError:
        return [ValidationIssue('warning', 'jsonschema not installed; skipping schema validation')]

    schema_path = importlib_resources.files('camtasia.resources') / 'camtasia-project-schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))

    issues: list[ValidationIssue] = []
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(project_data):
        path = '/'.join(str(p) for p in error.absolute_path) or '(root)'
        issues.append(ValidationIssue('error', f'Schema violation at {path}: {error.message}'))
    return issues