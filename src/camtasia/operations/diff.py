"""Compare two Camtasia projects and report differences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.project import Project


@dataclass
class ProjectDiff:
    """Differences between two Camtasia projects."""

    tracks_added: list[int] = field(default_factory=list)
    tracks_removed: list[int] = field(default_factory=list)
    clips_added: list[tuple[int, int]] = field(default_factory=list)  # (track_idx, clip_id)
    clips_removed: list[tuple[int, int]] = field(default_factory=list)
    media_added: list[int] = field(default_factory=list)  # media IDs
    media_removed: list[int] = field(default_factory=list)
    settings_changed: dict[str, tuple] = field(default_factory=dict)  # key: (old, new)

    @property
    def has_changes(self) -> bool:
        """Whether any differences were found."""
        return bool(
            self.tracks_added or self.tracks_removed
            or self.clips_added or self.clips_removed
            or self.media_added or self.media_removed
            or self.settings_changed
        )

    def summary(self) -> str:
        """Human-readable summary of changes."""
        lines = []
        if self.tracks_added:
            lines.append(f'Tracks added: {self.tracks_added}')
        if self.tracks_removed:
            lines.append(f'Tracks removed: {self.tracks_removed}')
        if self.clips_added:
            lines.append(f'Clips added: {len(self.clips_added)}')
        if self.clips_removed:
            lines.append(f'Clips removed: {len(self.clips_removed)}')
        if self.media_added:
            lines.append(f'Media added: {len(self.media_added)}')
        if self.media_removed:
            lines.append(f'Media removed: {len(self.media_removed)}')
        if self.settings_changed:
            for k, (old, new) in self.settings_changed.items():
                lines.append(f'{k}: {old} -> {new}')
        return '\n'.join(lines) if lines else 'No changes'


def diff_projects(a: Project, b: Project) -> ProjectDiff:
    """Compare two projects and return their differences."""
    result = ProjectDiff()

    # Track differences
    a_tracks = {t.index for t in a.timeline.tracks}
    b_tracks = {t.index for t in b.timeline.tracks}
    result.tracks_added = sorted(b_tracks - a_tracks)
    result.tracks_removed = sorted(a_tracks - b_tracks)

    # Clip differences (on shared tracks)
    for idx in a_tracks & b_tracks:
        a_clips = {c.id for c in a.timeline.tracks[idx].clips}
        b_clips = {c.id for c in b.timeline.tracks[idx].clips}
        for cid in sorted(b_clips - a_clips):
            result.clips_added.append((idx, cid))
        for cid in sorted(a_clips - b_clips):
            result.clips_removed.append((idx, cid))

    # Clips on removed tracks
    for idx in a_tracks - b_tracks:
        for c in a.timeline.tracks[idx].clips:
            result.clips_removed.append((idx, c.id))

    # Clips on added tracks
    for idx in b_tracks - a_tracks:
        for c in b.timeline.tracks[idx].clips:
            result.clips_added.append((idx, c.id))

    # Media differences
    a_media = {m.id for m in a.media_bin}
    b_media = {m.id for m in b.media_bin}
    result.media_added = sorted(b_media - a_media)
    result.media_removed = sorted(a_media - b_media)

    # Settings differences
    for key in ('width', 'height'):
        av = getattr(a, key)
        bv = getattr(b, key)
        if av != bv:
            result.settings_changed[key] = (av, bv)

    return result
