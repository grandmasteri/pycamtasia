"""Project loading, saving, and creation for Camtasia .cmproj bundles."""

from __future__ import annotations

import json
import shutil
import warnings
from contextlib import contextmanager
from importlib import resources as importlib_resources
from pathlib import Path
from typing import Any, Callable, Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from camtasia.history import ChangeHistory
    from camtasia.timeline.clips.group import Group

from camtasia.authoring_client import AuthoringClient
from camtasia.media_bin import Media, MediaBin, MediaType
from camtasia.timeline import Timeline
from camtasia.timeline.track import Track
from camtasia.timeline.clips import BaseClip
from camtasia.timing import EDIT_RATE, seconds_to_ticks
from camtasia.types import ClipType, CompactResult, EffectName, HealthCheckResult
from camtasia.validation import ValidationIssue, _check_duplicate_clip_ids, _check_track_indices, _check_transition_references, validate_against_schema


import subprocess as _sp


def _probe_media(path: Path) -> dict:
    """Probe media file for metadata. Uses pymediainfo if available, falls back to ffprobe.

    Returns a dict with available keys:
    - Images: ``width``, ``height``
    - Audio: ``duration_seconds``, ``sample_rate``, ``channels``, ``bit_depth``
    - Video: ``duration_seconds``, ``width``, ``height``, ``frame_rate``
    """
    try:
        from pymediainfo import MediaInfo  # type: ignore[import-untyped]
        info = MediaInfo.parse(path)
        result: dict = {}
        for track in info.tracks:
            if track.track_type == 'Video':
                result['width'] = track.width
                result['height'] = track.height
                if track.duration:
                    result['duration_seconds'] = track.duration / 1000.0
                if track.frame_rate:
                    result['frame_rate'] = float(track.frame_rate)
            elif track.track_type == 'Audio':
                if track.duration:
                    result['duration_seconds'] = track.duration / 1000.0
                if track.sampling_rate:
                    result['sample_rate'] = int(track.sampling_rate)
                if track.channel_s:
                    result['channels'] = int(track.channel_s)
                if track.bit_depth:
                    result['bit_depth'] = int(track.bit_depth)
            elif track.track_type == 'Image':
                result['width'] = track.width
                result['height'] = track.height
            elif track.track_type == 'General':
                if 'duration_seconds' not in result and track.duration:
                    result['duration_seconds'] = track.duration / 1000.0
        if result:
            result['_backend'] = 'pymediainfo'
            return result
    except ImportError:
        pass
    except Exception:
        pass
    return _probe_media_ffprobe(path)


def _probe_media_ffprobe(path: Path) -> dict:
    """Probe media file using ffprobe subprocess."""
    result: dict = {'_backend': 'ffprobe'}
    try:
        out = _sp.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'stream=width,height',
             '-of', 'csv=p=0', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        parts = out.stdout.strip().split(',')
        if len(parts) >= 2 and parts[0] and parts[1]:
            result['width'] = int(parts[0])
            result['height'] = int(parts[1])
    except Exception:
        pass
    try:
        out = _sp.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', str(path)],
            capture_output=True, text=True, timeout=10,
        )
        val = out.stdout.strip()
        if val:
            result['duration_seconds'] = float(val)
    except Exception:
        pass
    return result



class _ChangeTracker:
    """Context manager that snapshots project data before/after a block."""

    def __init__(self, project: Project, description: str) -> None:
        self._project = project
        self._description = description
        self._snapshot_before: dict[str, Any] | None = None

    def __enter__(self) -> _ChangeTracker:
        import copy
        self._snapshot_before = copy.deepcopy(self._project._data)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: object,
    ) -> None:
        if exception_type is None and self._snapshot_before is not None:
            self._project.history.record(
                self._description,
                self._snapshot_before,
                self._project._data,
            )

class Project:
    """Main entry-point for interacting with Camtasia projects.

    A Camtasia project is a macOS bundle directory (.cmproj) containing a
    project.tscproj JSON file, media assets, and recordings.

    Args:
        file_path: Path to the .cmproj directory or .tscproj file.
        encoding: Text encoding of the project file.
    """

    def __init__(self, file_path: Path, encoding: str | None = None) -> None:
        self._file_path = file_path
        self._encoding = encoding
        self._data: dict[str, Any] = json.loads(self._project_file.read_text(encoding=encoding))
        self._history: ChangeHistory | None = None

    @classmethod
    def load(cls, file_path: str | Path, encoding: str | None = None) -> Project:
        """Load a Camtasia project from disk.

        Args:
            file_path: Path to the .cmproj directory or .tscproj file.
            encoding: Text encoding of the project file.

        Returns:
            A Project instance.
        """
        return cls(Path(file_path).resolve(), encoding=encoding)

    @property
    def history(self) -> ChangeHistory:
        """Undo/redo history for this project."""
        from camtasia.history import ChangeHistory
        if self._history is None:
            self._history = ChangeHistory()
        return self._history

    def track_changes(self, description: str = "edit") -> _ChangeTracker:
        """Context manager that records a reversible change.

        Usage::

            with project.track_changes("add intro"):
                track.add_clip(...)

            project.undo()  # reverts the block
        """
        return _ChangeTracker(self, description)

    def undo(self) -> str:
        """Undo the most recent tracked change. Returns its description."""
        returned_description: str = self.history.undo(self._data)
        return returned_description

    def redo(self) -> str:
        """Redo the most recently undone change. Returns its description."""
        returned_description: str = self.history.redo(self._data)
        return returned_description

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Project):
            return NotImplemented
        return self._data == other._data

    @property
    def file_path(self) -> Path:
        """The full path to the Camtasia project."""
        return self._file_path

    @property
    def width(self) -> int:
        """Canvas width in pixels."""
        return int(self._data.get('width', 1920))

    @width.setter
    def width(self, value: int) -> None:
        """Set the canvas width in pixels."""
        self._data['width'] = value

    @property
    def height(self) -> int:
        """Canvas height in pixels."""
        return int(self._data.get('height', 1080))

    @height.setter
    def height(self, value: int) -> None:
        """Set the canvas height in pixels."""
        self._data['height'] = value

    @property
    def title(self) -> str:
        """Project title."""
        return self._data.get('title', '')  # type: ignore[no-any-return]

    @title.setter
    def title(self, value: str) -> None:
        """Set the project title."""
        self._data['title'] = value

    @property
    def description(self) -> str:
        """Project description."""
        return self._data.get('description', '')  # type: ignore[no-any-return]

    @description.setter
    def description(self, value: str) -> None:
        """Set the project description."""
        self._data['description'] = value

    @property
    def author(self) -> str:
        """Project author."""
        return self._data.get('author', '')  # type: ignore[no-any-return]

    @author.setter
    def author(self, value: str) -> None:
        """Set the project author."""
        self._data['author'] = value

    @property
    def target_loudness(self) -> float:
        """Target loudness in LUFS for audio normalization."""
        return float(self._data.get('targetLoudness', -18.0))

    @target_loudness.setter
    def target_loudness(self, value: float) -> None:
        """Set the target loudness in LUFS."""
        self._data['targetLoudness'] = value

    @property
    def frame_rate(self) -> int:
        """Video frame rate."""
        return int(self._data.get('videoFormatFrameRate', 30))

    @frame_rate.setter
    def frame_rate(self, value: int) -> None:
        """Set the video frame rate."""
        self._data['videoFormatFrameRate'] = value

    @property
    def sample_rate(self) -> int:
        """Audio sample rate."""
        return int(self._data.get('audioFormatSampleRate', 44100))

    @sample_rate.setter
    def sample_rate(self, value: int) -> None:
        """Set the audio sample rate."""
        self._data['audioFormatSampleRate'] = value

    @property
    def edit_rate(self) -> int:
        """The editing tick rate (ticks per second).

        Default is 705,600,000 — divisible by 30fps, 60fps, 44100Hz, 48000Hz.
        """
        return int(self._data.get('editRate', EDIT_RATE))

    @property
    def authoring_client(self) -> AuthoringClient | None:
        """Details about the software used to edit the project."""
        client = self._data.get('authoringClientName')
        if isinstance(client, dict):
            return AuthoringClient(**client)
        client_name = self._data.get('clientName')
        if isinstance(client_name, str):
            return AuthoringClient(name=client_name, platform='unknown', version='unknown')
        return None

    @property
    def media_bin(self) -> MediaBin:
        """The project's media bin (sourceBin)."""
        return MediaBin(self._data.setdefault('sourceBin', []), self._file_path)

    @property
    def media_count(self) -> int:
        """Number of media entries in the source bin."""
        return len(self.media_bin)

    @property
    def source_bin_paths(self) -> list[str]:
        """List of all source file paths in the media bin."""
        return [str(media_entry.source) for media_entry in self.media_bin]

    @property
    def timeline(self) -> Timeline:
        """The project's timeline."""
        return Timeline(self._data['timeline'])

    @property
    def is_empty(self) -> bool:
        """Whether the project has no clips on any track."""
        return not self.timeline.has_clips

    @property
    def empty_tracks(self) -> list[Track]:
        """All tracks with no clips."""
        return self.timeline.empty_tracks

    @property
    def track_names(self) -> list[str]:
        """Names of all tracks in the project."""
        return self.timeline.track_names

    @property
    def has_screen_recording(self) -> bool:
        """Whether the project contains any screen recording clips."""
        from camtasia.timeline.clips.group import Group
        for track in self.timeline.tracks:
            for clip in track.clips:
                if isinstance(clip, Group) and clip.is_screen_recording:
                    return True
        return False

    @property
    def track_count(self) -> int:
        """Number of tracks in the timeline."""
        return self.timeline.track_count

    def clone_track(self, source_track_name: str, new_track_name: str) -> Track:
        """Clone a track with all its clips and effects."""
        source = self.timeline.find_track_by_name(source_track_name)
        if source is None:
            raise KeyError(f'Track not found: {source_track_name}')
        new_track = self.timeline.duplicate_track(source.index)
        new_track.name = new_track_name
        return new_track

    def swap_tracks(self, track_name_a: str, track_name_b: str) -> None:
        """Swap the visual order of two tracks.

        Args:
            track_name_a: Name of the first track.
            track_name_b: Name of the second track.

        Raises:
            KeyError: If either track name is not found.
        """
        track_a = self.timeline.find_track_by_name(track_name_a)
        track_b = self.timeline.find_track_by_name(track_name_b)
        if track_a is None:
            raise KeyError(f'Track not found: {track_name_a}')
        if track_b is None:
            raise KeyError(f'Track not found: {track_name_b}')
        idx_a = track_a.index
        idx_b = track_b.index
        track_a._data['trackIndex'] = idx_b
        track_b._data['trackIndex'] = idx_a
        tracks = self.timeline._track_list
        tracks[idx_a], tracks[idx_b] = tracks[idx_b], tracks[idx_a]
        attrs = self.timeline._data.get('trackAttributes')
        if attrs and len(attrs) > max(idx_a, idx_b):
            attrs[idx_a], attrs[idx_b] = attrs[idx_b], attrs[idx_a]

    def remove_track_by_name(self, track_name: str) -> bool:
        """Remove the first track with the given name.

        Args:
            track_name: Display name of the track to remove.

        Returns:
            True if a matching track was found and removed, False otherwise.
        """
        for track in self.timeline.tracks:
            if track.name == track_name:
                self.timeline.remove_track(track.index)
                return True
        return False

    @property
    def clip_count(self) -> int:
        """Total number of clips across all tracks."""
        return self.timeline.total_clip_count

    @property
    def total_effect_count(self) -> int:
        """Total number of effects across all clips on all tracks."""
        return sum(
            clip.effect_count
            for track in self.timeline.tracks
            for clip in track.clips
        )

    @property
    def has_effects(self) -> bool:
        """Whether any clip in the project has effects."""
        return self.total_effect_count > 0

    @property
    def has_transitions(self) -> bool:
        """Whether any track in the project has transitions."""
        return self.total_transition_count > 0

    @property
    def has_keyframes(self) -> bool:
        """Whether any clip in the project has keyframes."""
        return self.total_keyframe_count > 0

    @property
    def total_transition_count(self) -> int:
        """Total number of transitions across all tracks."""
        return sum(
            track.transition_count
            for track in self.timeline.tracks
        )

    @property
    def total_keyframe_count(self) -> int:
        """Total keyframes across all clips on all tracks."""
        return sum(
            clip.keyframe_count
            for track in self.timeline.tracks
            for clip in track.clips
        )

    @property
    def duration_seconds(self) -> float:
        """Total project duration in seconds."""
        return self.total_duration_seconds()

    @property
    def duration_formatted(self) -> str:
        """Total duration as MM:SS string."""
        total_seconds: float = self.duration_seconds
        minutes: int = int(total_seconds // 60)
        remaining_seconds: int = int(total_seconds % 60)
        return f'{minutes}:{remaining_seconds:02d}'

    @property
    def total_duration_formatted(self) -> str:
        """Total duration as HH:MM:SS string.

        Returns ``H:MM:SS`` when the duration is one hour or more,
        otherwise ``M:SS``.
        """
        total_seconds: float = self.duration_seconds
        hours: int = int(total_seconds // 3600)
        minutes: int = int((total_seconds % 3600) // 60)
        remaining_seconds: int = int(total_seconds % 60)
        if hours > 0:
            return f'{hours}:{minutes:02d}:{remaining_seconds:02d}'
        return f'{minutes}:{remaining_seconds:02d}'

    @property
    def next_available_id(self) -> int:
        """Next available clip ID (max existing + 1)."""
        existing = self.timeline.all_clip_ids
        return max(existing, default=0) + 1

    @property
    def all_clips(self) -> list[tuple[Track, BaseClip]]:
        """All clips across all tracks as (track, clip) tuples."""
        return [(t, c) for t in self.timeline.tracks for c in t.clips]

    @property
    def all_groups(self) -> list[tuple[Track, Group]]:
        """All Group clips across all tracks as (track, group) tuples."""
        from camtasia.timeline.clips.group import Group
        return [(track, clip) for track, clip in self.all_clips if isinstance(clip, Group)]

    @property
    def group_count(self) -> int:
        """Number of Group clips across all tracks."""
        return len(self.all_groups)

    @property
    def screen_recording_groups(self) -> list[tuple[Track, Group]]:
        """All screen recording Group clips."""
        return [(track, group) for track, group in self.all_groups if group.is_screen_recording]

    def clips_between(self, range_start_seconds: float, range_end_seconds: float) -> list[tuple[Track, BaseClip]]:
        """Return all clips across all tracks that fall within the time range."""
        return [(track, clip) for track, clip in self.all_clips if clip.is_between(range_start_seconds, range_end_seconds)]

    @property
    def has_audio(self) -> bool:
        """Whether the project has any audio clips."""
        return any(c.is_audio for _, c in self.all_clips)

    @property
    def has_video(self) -> bool:
        """Whether the project has any video clips."""
        return any(c.is_video for _, c in self.all_clips)

    def find_clips_by_type(self, clip_type: str) -> list[tuple[Track, BaseClip]]:
        """Find all clips of a specific type across all tracks."""
        return [(t, c) for t, c in self.all_clips if c.clip_type == clip_type]

    def find_clips_with_effect(self, effect_name: str | EffectName) -> list[tuple[Track, BaseClip]]:
        """Find all clips that have a specific effect applied."""
        return [(track, clip) for track, clip in self.all_clips if clip.is_effect_applied(effect_name)]

    def find_clips_by_source(self, source_id: int) -> list[tuple[Track, BaseClip]]:
        """Find all clips that reference a specific source bin entry."""
        return [(track, clip) for track, clip in self.all_clips if clip._data.get('src') == source_id]

    def replace_all_media(self, old_source_id: int, new_source_id: int) -> int:
        """Replace all references to one media source with another. Returns count."""
        count: int = 0
        for _, clip in self.all_clips:
            if clip._data.get('src') == old_source_id:
                clip._data['src'] = new_source_id
                count += 1
        return count

    @property
    def longest_clip(self) -> tuple[Track, BaseClip] | None:
        """The longest clip across all tracks, or None if empty."""
        longest_pair: tuple[Track, BaseClip] | None = None
        longest_duration: int = 0
        for track, clip in self.all_clips:
            if clip.duration > longest_duration:
                longest_duration = clip.duration
                longest_pair = (track, clip)
        return longest_pair

    @property
    def shortest_clip(self) -> tuple[Track, BaseClip] | None:
        """The shortest clip across all tracks, or None if empty."""
        shortest_pair: tuple[Track, BaseClip] | None = None
        shortest_duration: int | None = None
        for track, clip in self.all_clips:
            if shortest_duration is None or clip.duration < shortest_duration:
                shortest_duration = clip.duration
                shortest_pair = (track, clip)
        return shortest_pair

    @property
    def average_clip_duration_seconds(self) -> float:
        """Average clip duration across all tracks, or 0.0 if empty."""
        total_clips: int = self.clip_count
        if total_clips == 0:
            return 0.0
        total_duration: float = sum(
            clip.duration_seconds for _, clip in self.all_clips
        )
        return total_duration / total_clips

    @property
    def effect_summary(self) -> dict[str, int]:
        """Count of each effect type across all clips."""
        from collections import Counter
        counts: Counter[str] = Counter()
        for track in self.timeline.tracks:
            for clip in track.clips:
                for e in clip._data.get('effects', []):
                    counts[e.get('effectName', '?')] += 1
        return dict(counts)

    @property
    def clip_type_summary(self) -> dict[str, int]:
        """Count of each clip type across all tracks."""
        from collections import Counter
        counts: Counter[str] = Counter()
        for track in self.timeline.tracks:
            for clip in track.clips:
                counts[clip.clip_type] += 1
        return dict(counts)

    def search_clips(
        self,
        *,
        clip_type: str | ClipType | None = None,
        min_duration_seconds: float | None = None,
        max_duration_seconds: float | None = None,
        has_effects: bool | None = None,
        has_keyframes: bool | None = None,
        on_track: str | None = None,
    ) -> list[tuple[Track, BaseClip]]:
        """Search for clips matching the given criteria.

        All criteria are AND-combined. None means 'any value'.
        """
        matching_results: list[tuple[Track, BaseClip]] = []
        for track, clip in self.all_clips:
            if clip_type is not None and clip.clip_type != clip_type:
                continue
            if min_duration_seconds is not None and clip.duration_seconds < min_duration_seconds:
                continue
            if max_duration_seconds is not None and clip.duration_seconds > max_duration_seconds:
                continue
            if has_effects is not None and clip.has_effects != has_effects:
                continue
            if has_keyframes is not None and clip.has_keyframes != has_keyframes:
                continue
            if on_track is not None and track.name != on_track:
                continue
            matching_results.append((track, clip))
        return matching_results

    @classmethod
    def from_template(cls, template_path: str | Path, output_path: str | Path) -> Project:
        """Create a new project by copying an existing one as a template.

        Copies the entire .cmproj bundle to the output path and loads it.
        """
        src = Path(template_path)
        dst = Path(output_path)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return cls.load(str(dst))

    @classmethod
    def new(cls, output_path: str | Path, title: str = 'Untitled', width: int = 1920, height: int = 1080) -> Project:
        """Create a brand new empty project at the given path."""
        template = importlib_resources.files('camtasia.resources') / 'new.cmproj'
        dst = Path(output_path)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(str(template), dst)
        proj = cls.load(str(dst))
        proj.title = title
        proj.width = width
        proj.height = height
        proj.save()
        return proj

    def batch_apply(
        self,
        operation: Callable[[BaseClip], Any],
        *,
        clip_type: str | ClipType | None = None,
        on_track: str | None = None,
    ) -> int:
        """Apply an operation to matching clips. Returns count of clips modified."""
        matching_clips: list[tuple[Track, BaseClip]] = self.search_clips(
            clip_type=clip_type,
            on_track=on_track,
        )
        for _, clip in matching_clips:
            operation(clip)
        return len(matching_clips)

    def replace_media_path(self, old_path_fragment: str, new_path_fragment: str) -> int:
        """Replace a path fragment in all source bin entries. Returns count changed."""
        replacement_count: int = 0
        for source_entry in self._data.get('sourceBin', []):
            current_source: str = source_entry.get('src', '')
            if old_path_fragment in current_source:
                source_entry['src'] = current_source.replace(old_path_fragment, new_path_fragment)
                replacement_count += 1
        return replacement_count

    @staticmethod
    def _flatten_parameters(obj: Any) -> None:
        """Convert parameter dicts without keyframes to bare defaultValues.

        Camtasia v10 saves parameters as scalar values when there are no
        keyframes.  This walks the entire data tree in-place and replaces
        ``{"type": ..., "defaultValue": X, ...}`` with just ``X`` when
        the dict has no ``"keyframes"`` key.  Dicts that also carry a
        ``"name"`` key (effectDef entries) are left untouched.
        """
        if isinstance(obj, dict):
            for key in list(obj):
                val = obj[key]
                if (isinstance(val, dict)
                        and 'type' in val and 'defaultValue' in val
                        and 'name' not in val and 'keyframes' not in val
                        and 'interp' not in val and 'uiHints' not in val
                        and 'valueBounds' not in val):
                    obj[key] = val['defaultValue']
                else:
                    Project._flatten_parameters(val)
        elif isinstance(obj, list):
            for item in obj:
                Project._flatten_parameters(item)

    def validate(self) -> list[ValidationIssue]:
        """Check for common project issues.

        Returns:
            A list of :class:`ValidationIssue` instances (may be empty).
        """
        issues: list[ValidationIssue] = []
        bin_ids: set[int] = set()

        for media in self.media_bin:
            bin_ids.add(media.id)
            raw = media._data

            # Zero-range audio
            if media.type == MediaType.Audio:
                r = raw['sourceTracks'][0]['range']
                if r == [0, 0]:
                    issues.append(ValidationIssue('error', f'Zero-range audio source: {media.source}', media.id))

            # Zero-dimension image
            if media.type == MediaType.Image:
                if raw['rect'] == [0, 0, 0, 0]:
                    issues.append(ValidationIssue('error', f'Zero-dimension image source: {media.source}', media.id))

            # Missing source file
            src_path = self._file_path / media.source if self._file_path.is_dir() else self._file_path.parent / media.source
            if not src_path.exists():
                issues.append(ValidationIssue('warning', f'Missing source file: {media.source}', media.id))

        # Collect all clip source references
        referenced_ids: set[int] = set()
        for clip in self.timeline.all_clips():
            if clip.source_id is not None:
                referenced_ids.add(clip.source_id)
                if clip.source_id not in bin_ids:
                    issues.append(ValidationIssue('error', f'Clip references missing source ID {clip.source_id}', clip.source_id))

        # Orphaned media
        for media in self.media_bin:
            if media.id not in referenced_ids:
                issues.append(ValidationIssue('warning', f'Orphaned media not used by any clip: {media.source}', media.id))

        # Duplicate clip IDs
        issues.extend(_check_duplicate_clip_ids(self._data))

        # Track index consistency
        issues.extend(_check_track_indices(self._data))

        # Transition references
        issues.extend(_check_transition_references(self._data))

        # JSON schema validation
        # Schema validation available via validate_schema() method

        return issues


    def validate_schema(self) -> list[ValidationIssue]:
        """Validate the project data against the Camtasia JSON Schema.

        This is a stricter check than validate() — it verifies the project
        structure matches the schema derived from 93 TechSmith sample projects.
        """
        return validate_against_schema(self._data)
    def validate_and_report(self) -> str:
        """Run validation and return a human-readable report."""
        validation_issues: list[ValidationIssue] = self.validate()
        if not validation_issues:
            return 'No issues found.'
        report_lines: list[str] = [f'{len(validation_issues)} issue(s) found:']
        for issue in validation_issues:
            report_lines.append(f'  [{issue.level}] {issue.message}')
        return '\n'.join(report_lines)

    def repair(self) -> dict[str, int]:
        """Remove stale transitions that reference non-existent clips. Returns counts of fixes applied."""
        fixes_applied: dict[str, int] = {'stale_transitions_removed': 0}
        # Fix stale transitions
        for track in self.timeline.tracks:
            clip_ids = {c.id for c in track.clips}
            original_count = len(track._data.get('transitions', []))
            track._data['transitions'] = [
                t for t in track._data.get('transitions', [])
                if (t.get('leftMedia') is None or t.get('leftMedia') in clip_ids)
                and (t.get('rightMedia') is None or t.get('rightMedia') in clip_ids)
            ]
            fixes_applied['stale_transitions_removed'] += original_count - len(track._data.get('transitions', []))
        return fixes_applied

    def save(self) -> None:
        """Write the current project state to disk.

        Matches Camtasia's ``NSJSONSerialization`` JSON formatting to
        avoid parser crashes with ``.trec`` screen recordings.
        """
        import re

        for issue in self.validate():
            message = f'[{issue.level}] {issue.message}'
            warnings.warn(message, stacklevel=2)

        self._flatten_parameters(self._data)

        # Step 1: Standard pretty-print, preserving extreme floats
        # Python converts -1.79769e+308 to -inf during json.loads, then
        # json.dumps writes -Infinity which Camtasia cannot parse.
        text = json.dumps(self._data, indent=2, ensure_ascii=False,
                          allow_nan=True)
        # Replace -Infinity/Infinity/NaN with the original extreme values
        # Only replace when they appear as bare JSON values (after : or , or [)
        # not inside quoted strings
        import re
        def _replace_special(m):
            token = m.group(0)
            if token == '-Infinity':
                return '-1.79769313486232e+308'  # pragma: no cover
            elif token == 'Infinity':
                return '1.79769313486232e+308'  # pragma: no cover
            else:
                return '0.0'  # pragma: no cover
        text = re.sub(r'(?<=: |, |\[ )-?Infinity\b|(?<=: |, |\[ )NaN\b', _replace_special, text)

        # Step 2: Add space before colon (NSJSONSerialization style)
        # "key": value  ->  "key" : value
        # Only on lines that don't contain escaped quotes (to avoid
        # corrupting JSON-inside-string values like textAttributes).
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '\\"' not in line:
                lines[i] = re.sub(r'"\s*:', '" :', line)
        text = '\n'.join(lines)

        # Step 3: Collapse scalar arrays to single lines
        def _collapse(m: re.Match) -> str:
            items = re.findall(
                r'-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null',
                m.group(0))
            return '[' + ', '.join(items) + ']'

        text = re.sub(
            r'\[\s*(?:-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null)'
            r'(?:,\s*(?:-?[\d.]+(?:e[+-]?\d+)?|"[^"]*"|true|false|null))*'
            r'\s*\]',
            _collapse, text, flags=re.DOTALL,
        )

        # Step 4: Expand empty objects to multi-line with proper indentation
        def _expand_empty(m: re.Match) -> str:
            indent = m.group(1)
            return str('{\n' + indent + '  ' + '}')
        text = re.sub(r'\{\}(?=\n(\s*))', _expand_empty, text)

        # Step 5: Add trailing space after commas at end of lines
        text = re.sub(r',\n', ', \n', text)

        with self._project_file.open(mode='wt', encoding=self._encoding) as handle:
            handle.write(text)
            handle.write('\n')

    # ------------------------------------------------------------------
    # L2 convenience methods
    # ------------------------------------------------------------------

    _EXTENSION_TYPE_MAP: dict[str, MediaType] = {
        '.png': MediaType.Image, '.jpg': MediaType.Image,
        '.jpeg': MediaType.Image, '.gif': MediaType.Image,
        '.bmp': MediaType.Image, '.tiff': MediaType.Image,
        '.wav': MediaType.Audio, '.mp3': MediaType.Audio,
        '.m4a': MediaType.Audio, '.aac': MediaType.Audio,
        '.mov': MediaType.Video, '.mp4': MediaType.Video,
        '.trec': MediaType.Video, '.avi': MediaType.Video,
        '.tscshadervid': MediaType.Video,
    }

    def import_media(self, file_path: Path | str, **kwargs: Any) -> Media:
        """Import a media file into the project's source bin.

        Detects media type from the file extension and passes appropriate
        defaults so that pymediainfo is not required.

        Args:
            file_path: Path to the media file.
            **kwargs: Additional overrides forwarded to
                :meth:`MediaBin.import_media`.

        Returns:
            The newly created Media entry.

        Raises:
            ValueError: Unknown file extension.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        media_type = kwargs.pop('media_type', None) or self._EXTENSION_TYPE_MAP.get(suffix)
        if media_type is None:
            supported = ', '.join(sorted(self._EXTENSION_TYPE_MAP))
            raise ValueError(
                f"Cannot determine media type for extension '{suffix}'. "
                f"Supported extensions: {supported}"
            )

        meta = _probe_media(path)

        if media_type == MediaType.Image:
            kwargs.setdefault('duration', 1)
            kwargs.setdefault('width', meta.get('width', 1920))
            kwargs.setdefault('height', meta.get('height', 1080))
        elif media_type == MediaType.Audio:
            sr = meta.get('sample_rate', kwargs.get('sample_rate', 44100))
            kwargs.setdefault('sample_rate', sr)
            if meta.get('_backend') == 'pymediainfo':
                kwargs.setdefault('num_channels', meta.get('channels', 2))
                kwargs.setdefault('bit_depth', meta.get('bit_depth', 16))
            if 'duration' not in kwargs:
                dur_secs = meta.get('duration_seconds')
                kwargs['duration'] = int(dur_secs * sr) if dur_secs else sr * 60
        elif media_type == MediaType.Video and 'duration' not in kwargs:
            if suffix == '.tscshadervid':
                # Shaders have infinite duration and no audio
                kwargs['duration'] = 9223372036854775807  # MAX_INT64
                kwargs.setdefault('width', 1920)
                kwargs.setdefault('height', 1080)
                kwargs.setdefault('sample_rate', 30)
                kwargs.setdefault('num_channels', 0)
                kwargs.setdefault('bit_depth', 32)
            else:
                dur_secs = meta.get('duration_seconds')
                kwargs['duration'] = int(dur_secs * 30) if dur_secs else 30 * 60
        return self.media_bin.import_media(path, media_type=media_type, **kwargs)

    def import_shader(self, shader_path: str | Path) -> Media:
        """Import a .tscshadervid shader with effectDef parsing.

        Reads the shader JSON, converts effectDef entries (hex colors to
        RGBA floats), and sets sourceTracks metadata for Camtasia.
        Reuses existing media if already imported.
        """
        path = Path(shader_path)
        existing = self.find_media_by_name(path.stem)
        if existing is not None:
            return existing

        media = self.import_media(path)
        shader_data = json.loads(path.read_text())

        effect_def = []
        for entry in shader_data['effectDef']:
            name = entry['name']
            if entry.get('type') == 'Color':
                hex_str = entry['value']
                r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
                effect_def.append({
                    'name': name, 'type': 'Color',
                    'defaultValue': [r / 255, g / 255, b / 255, 1.0],
                    'scalingType': 3, 'unitType': 0, 'userInterfaceType': 6,
                })
            else:
                effect_def.append({
                    'name': name, 'type': entry['type'],
                    'defaultValue': entry.get('defaultValue', entry.get('value')),
                    'scalingType': 0,
                    'unitType': 1 if 'MidPoint' in name else 0,
                    'userInterfaceType': 0,
                })
        effect_def.append({
            'name': 'sourceFileType', 'type': 'string',
            'defaultValue': 'tscshadervid', 'maxValue': '', 'minValue': '',
            'scalingType': 0, 'unitType': 0, 'userInterfaceType': 0,
        })

        # Find the source bin entry and patch it
        for entry in self._data['sourceBin']:
            if entry['id'] == media.id:
                entry['effectDef'] = effect_def
                st = entry['sourceTracks'][0]
                st['editRate'] = 30
                st['sampleRate'] = 30
                st['bitDepth'] = 32
                break

        return media

    def import_trec(self, trec_path: str | Path) -> 'Media':
        """Import a .trec screen recording with full stream metadata.

        Uses pymediainfo to probe the multi-track container and build
        correct source bin entries with all stream metadata.

        Args:
            trec_path: Path to the .trec file.

        Returns:
            The Media entry.

        Raises:
            ImportError: pymediainfo not installed.
        """
        from camtasia.media_bin.trec_probe import probe_trec

        path = Path(trec_path)

        # Check if already imported
        existing = self.find_media_by_name(path.stem)
        if existing:
            return existing

        # Import the file (copies into project bundle)
        media = self.import_media(path)

        # Probe and apply accurate metadata
        probe_data = probe_trec(path)

        # Update the source bin entry with probed metadata
        for sb in self._data['sourceBin']:
            if sb['id'] == media.id:
                sb['rect'] = probe_data['rect']
                sb['sourceTracks'] = probe_data['sourceTracks']
                sb['lastMod'] = probe_data['lastMod']
                sb['loudnessNormalization'] = probe_data['loudnessNormalization']
                break

        return media

    def statistics(self) -> dict[str, Any]:
        """Comprehensive project statistics as a dict."""
        all_clips_list = [(t, c) for t, c in self.all_clips]
        total_effects: int = sum(len(c._data.get('effects', [])) for _, c in all_clips_list)
        total_transitions: int = self.timeline.total_transition_count
        return {
            'title': self.title,
            'duration_seconds': self.duration_seconds,
            'duration_formatted': self.total_duration_formatted,
            'resolution': f'{self.width}x{self.height}',
            'track_count': self.track_count,
            'clip_count': self.clip_count,
            'group_count': self.group_count,
            'effect_count': total_effects,
            'transition_count': total_transitions,
            'media_count': len(list(self.media_bin)),
            'empty_tracks': len(self.empty_tracks),
            'clip_density': self.timeline.clip_density,
        }

    def to_markdown_report(self) -> str:
        """Format project statistics as a markdown document."""
        stats = self.statistics()
        lines = [
            f'# Project Report: {stats["title"] or "(untitled)"}',
            '',
            '## Overview',
            '',
            f'| Metric | Value |',
            f'|--------|-------|',
            f'| Duration | {stats["duration_formatted"]} ({stats["duration_seconds"]:.1f}s) |',
            f'| Resolution | {stats["resolution"]} |',
            f'| Tracks | {stats["track_count"]} |',
            f'| Clips | {stats["clip_count"]} |',
            f'| Groups | {stats["group_count"]} |',
            f'| Effects | {stats["effect_count"]} |',
            f'| Transitions | {stats["transition_count"]} |',
            f'| Media files | {stats["media_count"]} |',
            f'| Empty tracks | {stats["empty_tracks"]} |',
            f'| Clip density | {stats["clip_density"]:.2f} |',
        ]
        return '\n'.join(lines)

    def info(self) -> dict[str, Any]:
        """Return comprehensive project information.

        Combines statistics, validation, and structural analysis
        into a single dict for debugging and inspection.
        """
        stats = self.statistics()
        issues = self.validate()
        structure = self.timeline.validate_structure()

        return {
            **stats,
            'validation_errors': [i.message for i in issues if i.level == 'error'],
            'validation_warnings': [i.message for i in issues if i.level == 'warning'],
            'structural_issues': structure,
            'has_screen_recording': self.has_screen_recording,
            'title': self.title,
            'author': self.author,
            'frame_rate': self.frame_rate,
            'sample_rate': self.sample_rate,
        }

    def health_check(self) -> HealthCheckResult:
        """Run comprehensive project health check.

        Returns dict with:
        - healthy: bool (True if no errors)
        - errors: list of error messages
        - warnings: list of warning messages
        - structural_issues: list from timeline.validate_structure()
        - statistics: dict from statistics()
        """
        issues = self.validate()
        structure = self.timeline.validate_structure()
        stats = self.statistics()
        errors = [i.message for i in issues if i.level == 'error']
        warnings = [i.message for i in issues if i.level == 'warning']
        return {
            'healthy': not errors and not structure,
            'errors': errors,
            'warnings': warnings,
            'structural_issues': structure,
            'statistics': stats,
        }

    def compact(self) -> CompactResult:
        """Run all cleanup operations and validate.

        Removes orphaned media, empty tracks, and validates the result.

        Returns:
            Summary dict with counts of items cleaned.

        Raises:
            ValueError: If validation finds errors after cleanup.
        """
        from camtasia.operations.cleanup import compact_project
        result = compact_project(self)

        issues = self.validate()
        errors = [i for i in issues if i.level == 'error']
        if errors:
            raise ValueError(
                f'Validation errors after compact: '
                f'{[e.message for e in errors]}'
            )

        return result

    def summary(self) -> str:
        """Human-readable project summary."""
        lines: list[str] = [
            f'Project: {self.title}',
            f'Duration: {self.total_duration_formatted}',
            f'Resolution: {self.width}x{self.height}',
            f'Tracks: {self.track_count}',
            f'Clips: {self.clip_count}',
            f'Groups: {self.group_count}',
        ]
        if self.media_bin:
            lines.append(f'Media files: {len(list(self.media_bin))}')
        issues = self.validate()
        if issues:
            lines.append(f'Validation issues: {len(issues)}')
        else:
            lines.append('Validation: clean')
        return '\n'.join(lines)

    def describe(self) -> str:
        """Comprehensive human-readable project description."""
        lines = [
            f'Project: {self.file_path.name}',
            f'Canvas: {self.width}x{self.height} @ {self.frame_rate}fps',
            f'Duration: {self.total_duration_seconds():.1f}s',
            f'Tracks: {self.timeline.track_count} ({len(self.timeline.tracks_with_clips)} with clips)',
            f'Clips: {self.timeline.total_clip_count}',
            f'Media: {self.media_count} items',
            '',
        ]
        for track in self.timeline.tracks:
            lines.append(track.describe())
            lines.append('')
        health = self.health_check()
        if health['healthy']:
            lines.append('Health: ✅ Healthy')
        else:
            lines.append(f'Health: ❌ {len(health["errors"])} errors, {len(health["warnings"])} warnings')
        return '\n'.join(lines)

    def total_duration_seconds(self) -> float:
        """Total timeline duration in seconds.

        Returns:
            Duration in seconds, delegated to the timeline.
        """
        return self.timeline.total_duration_seconds()

    def export_frame(
        self,
        video_path: Path | str,
        timestamp_seconds: float,
        output_path: Path | str | None = None,
    ) -> Path:
        """Extract a single frame from a video file as a PNG image.

        Uses ffmpeg to extract the frame. If output_path is None,
        saves to the project's media directory with an auto-generated name.

        Args:
            video_path: Path to the video file (.trec, .mp4, etc.)
            timestamp_seconds: Time position to extract the frame from.
            output_path: Where to save the PNG. Defaults to project media dir.

        Returns:
            Path to the extracted PNG file.

        Raises:
            RuntimeError: If ffmpeg exits with a non-zero return code.
        """
        video_path = Path(video_path)
        if output_path is None:
            media_dir = self._file_path / 'media'
            media_dir.mkdir(parents=True, exist_ok=True)
            stem = video_path.stem
            output_path = media_dir / f'{stem}_frame_{timestamp_seconds:.3f}s.png'
        else:
            output_path = Path(output_path)

        result = _sp.run(
            ['ffmpeg', '-ss', str(timestamp_seconds), '-i', str(video_path),
             '-frames:v', '1', '-q:v', '2', str(output_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f'ffmpeg failed (rc={result.returncode}): {result.stderr}')
        return output_path

    def export_frame_and_import(
        self,
        video_path: Path | str,
        timestamp_seconds: float,
    ) -> Media:
        """Extract a frame from video and import it into the project media bin.

        Args:
            video_path: Path to the video file.
            timestamp_seconds: Time position to extract the frame from.

        Returns:
            The newly created Media entry.
        """
        png_path = self.export_frame(video_path, timestamp_seconds)
        return self.import_media(png_path)

    def find_media_by_name(self, name: str) -> Media | None:
        """Search the source bin for media whose filename stem matches *name*.

        Args:
            name: Filename stem to match (case-sensitive).

        Returns:
            The first matching Media, or None.
        """
        for media in self.media_bin:
            if media.identity == name:
                return media
        return None

    def find_media_by_suffix(self, suffix: str) -> list[Media]:
        """Return all media entries whose source path ends with *suffix*.

        Args:
            suffix: Extension or suffix to match (e.g. ``'.png'``).

        Returns:
            List of matching Media entries.
        """
        return [m for m in self.media_bin if str(m.source).endswith(suffix)]

    def find_media_by_extension(self, ext: str) -> list[Media]:
        """Find all media entries with the given file extension."""
        ext = ext.lower().lstrip('.')
        return [m for m in self.media_bin if str(m.source).lower().endswith(f'.{ext}')]

    def add_gradient_background(
        self,
        duration_seconds: float,
        color0: tuple[float, float, float, float] = (0.16, 0.16, 0.16, 1.0),
        color1: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
        track_index: int = 1,
    ) -> Any:
        """Create a gradient shader background on the specified track.

        Adds a sourceBin entry for the gradient shader and places a VMFile
        clip on the given track.

        Args:
            duration_seconds: How long the background should last.
            color0: First RGBA gradient colour.
            color1: Second RGBA gradient colour.
            track_index: Track index to place the clip on (default 1).

        Returns:
            The created clip.
        """
        existing = self.find_media_by_suffix('.tscshadervid')
        if existing:
            media_id = existing[0].id
            shader_name = existing[0].source.name
        else:
            import datetime
            import time as _time

            width = self.width
            height = self.height
            media_id = self.media_bin.next_id()
            timestamp = datetime.datetime.now()
            ts_str = f"{timestamp.year}{timestamp.month:02}{timestamp.day:02}T{timestamp.hour:02}{timestamp.minute:02}{timestamp.second:02}"
            shader_name = f"gradient-bg-{media_id}.tscshadervid"
            src_path = f"./media/{_time.time()}/{shader_name}"

            source_entry: dict[str, Any] = {
                "id": media_id,
                "src": src_path,
                "rect": [0, 0, width, height],
                "lastMod": ts_str,
                "loudnessNormalization": True,
                "sourceTracks": [{
                    "range": [0, 9223372036854775807],
                    "type": 0,
                    "editRate": 30,
                    "trackRect": [0, 0, width, height],
                    "sampleRate": 30,
                    "bitDepth": 32,
                    "numChannels": 0,
                    "integratedLUFS": 100.0,
                    "peakLevel": -1.0,
                    "tag": 0,
                    "metaData": f"{shader_name};",
                    "parameters": {},
                }],
                "effectDef": [
                    {"name": "Color0", "type": "Color",
                     "defaultValue": list(color0),
                     "scalingType": 3, "unitType": 0, "userInterfaceType": 6},
                    {"name": "Color1", "type": "Color",
                     "defaultValue": list(color1),
                     "scalingType": 3, "unitType": 0, "userInterfaceType": 6},
                    {"name": "sourceFileType", "type": "string",
                     "defaultValue": "tscshadervid",
                     "maxValue": "", "minValue": "",
                     "scalingType": 0, "unitType": 0, "userInterfaceType": 0},
                ],
                "metadata": {"timeAdded": timestamp.strftime("%Y%m%dT%H%M%S.%f")},
            }
            self.media_bin.add_media_entry(source_entry)

        dur_ticks = seconds_to_ticks(duration_seconds)
        track = self.timeline.tracks[track_index]

        def _color_params(prefix: str, rgba: tuple[float, float, float, float]) -> dict:
            return {
                f"{prefix}-red": {"type": "double", "defaultValue": rgba[0], "interp": "linr"},
                f"{prefix}-green": {"type": "double", "defaultValue": rgba[1], "interp": "linr"},
                f"{prefix}-blue": {"type": "double", "defaultValue": rgba[2], "interp": "linr"},
                f"{prefix}-alpha": {"type": "double", "defaultValue": rgba[3], "interp": "linr"},
            }

        source_effect = {
            "effectName": "SourceEffect",
            "bypassed": False,
            "category": "",
            "parameters": {
                **_color_params("Color0", color0),
                **_color_params("Color1", color1),
                "sourceFileType": "tscshadervid",
            },
        }

        return track.add_clip(
            'VMFile', media_id, 0, dur_ticks,
            attributes={"ident": shader_name.replace(".tscshadervid", "")},
            sourceEffect=source_effect,
        )

    def add_progressive_disclosure(
        self,
        image_file_paths: list[Path | str],
        start_seconds: float = 0.0,
        per_step_seconds: float = 5.0,
        fade_in_seconds: float = 0.5,
        track_name_prefix: str = 'Prog',
    ) -> list[BaseClip]:
        """Place images on separate tracks for progressive visual accumulation.

        Each image gets its own track so all previous images remain visible
        when a new one appears. Each image fades in and stays visible until
        the end of the sequence.

        Args:
            image_file_paths: Ordered list of image file paths.
            start_seconds: When the first image appears.
            per_step_seconds: Time between each image appearing.
            fade_in_seconds: Fade-in duration for each image.
            track_name_prefix: Prefix for auto-generated track names.

        Returns:
            List of placed image clips.
        """
        total_duration_seconds: float = per_step_seconds * len(image_file_paths)
        placed_clips: list[BaseClip] = []

        for step_index, image_path in enumerate(image_file_paths):
            media = self.import_media(image_path)
            track_name: str = f'{track_name_prefix}-{step_index}'
            track = self.timeline.get_or_create_track(track_name)

            clip_start: float = start_seconds + (step_index * per_step_seconds)
            clip_duration: float = total_duration_seconds - (step_index * per_step_seconds)

            clip = track.add_image(
                media.id,
                start_seconds=clip_start,
                duration_seconds=clip_duration,
            )
            if fade_in_seconds > 0:
                clip.fade_in(fade_in_seconds)
            placed_clips.append(clip)

        return placed_clips

    def add_four_corner_gradient(
        self,
        shader_path: str | Path,
        duration_seconds: float,
        track_name: str = 'Background',
    ) -> 'BaseClip':
        """Import and place a 4-corner animated gradient shader background.

        Reuses an existing ``.tscshadervid`` source if one is already in the
        media bin; otherwise imports from *shader_path*.

        Args:
            shader_path: Path to the ``.tscshadervid`` shader file.
            duration_seconds: How long the background clip should last.
            track_name: Name of the track to place the clip on.

        Returns:
            The created video clip.
        """
        existing = self.find_media_by_suffix('.tscshadervid')
        if existing:
            shader_id = existing[0].id
        else:
            shader_id = self.import_media(shader_path).id
        track = self.timeline.get_or_create_track(track_name)
        return track.add_video(shader_id, start_seconds=0, duration_seconds=duration_seconds)

    def add_voiceover_sequence(
        self,
        vo_files: list[str | Path],
        pauses: dict[str, float] | None = None,
        track_name: str = 'Audio',
    ) -> dict[str, dict]:
        """Import voiceover files and place them sequentially on an audio track.

        Args:
            vo_files: List of audio file paths to import and place.
            pauses: Optional mapping of filename to seconds of silence
                to insert after that clip.
            track_name: Name of the track to place clips on.

        Returns:
            Dict mapping each filename to ``{'start': float,
            'duration': float, 'clip': AMFile}``.
        """
        pauses = pauses or {}
        track = self.timeline.get_or_create_track(track_name)
        cursor = 0.0
        result: dict[str, dict] = {}

        for vo_file in vo_files:
            path = Path(vo_file)
            media = self.import_media(path)
            meta = _probe_media(path)
            dur = meta.get('duration_seconds', 1.0)
            clip = track.add_audio(media.id, cursor, dur)
            result[path.name] = {'start': cursor, 'duration': dur, 'clip': clip}
            cursor += dur + pauses.get(path.name, 0.0)

        return result

    def add_voiceover_sequence_v2(
        self,
        audio_file_paths: list[Path | str],
        track_name: str = 'Voiceover',
        start_seconds: float = 0.0,
        gap_seconds: float = 0.0,
    ) -> list[BaseClip]:
        """Import and place multiple audio files sequentially on a track.

        Each audio file is imported into the source bin, its duration is
        read from the source bin metadata, and the resulting clip is placed
        end-to-end (with an optional gap) on the named track.

        Args:
            audio_file_paths: Paths to audio files to import.
            track_name: Name of the track to place clips on.
            start_seconds: Timeline position for the first clip.
            gap_seconds: Silence gap between consecutive clips.

        Returns:
            The list of placed audio clips.
        """
        from camtasia.timing import seconds_to_ticks, ticks_to_seconds, EDIT_RATE

        track = self.timeline.get_or_create_track(track_name)
        cursor_seconds: float = start_seconds
        placed_clips: list[BaseClip] = []

        for audio_path in audio_file_paths:
            path = Path(audio_path)
            media = self.import_media(path)

            # Resolve duration from source bin metadata
            duration_ticks: int = 0
            for source_entry in self._data.get('sourceBin', []):
                if source_entry.get('id') == media.id:
                    source_tracks = source_entry.get('sourceTracks', [])
                    if source_tracks:
                        range_val = source_tracks[0].get('range', [0, 0])
                        edit_rate: int = source_tracks[0].get('editRate', 44100)
                        if edit_rate == 0:
                            edit_rate = 44100  # pragma: no cover
                        duration_samples: int = range_val[1] - range_val[0]
                        duration_ticks = int(duration_samples / edit_rate * EDIT_RATE)
                    break

            if duration_ticks == 0:
                duration_ticks = seconds_to_ticks(5.0)  # fallback  # pragma: no cover

            duration_seconds: float = ticks_to_seconds(duration_ticks)
            clip = track.add_audio(media.id, start_seconds=cursor_seconds, duration_seconds=duration_seconds)
            placed_clips.append(clip)
            cursor_seconds += duration_seconds + gap_seconds

        return placed_clips

    def add_image_sequence(
        self,
        image_file_paths: list[Path | str],
        track_name: str = 'Images',
        start_seconds: float = 0.0,
        per_image_seconds: float = 5.0,
        fade_seconds: float = 0.5,
    ) -> list[BaseClip]:
        """Import and place multiple images sequentially with fade animations.

        Each image is imported into the source bin and placed on the named
        track for the specified duration.  Optional fade-in and fade-out
        animations are applied to each clip.

        Args:
            image_file_paths: Paths to image files to import.
            track_name: Name of the track to place clips on.
            start_seconds: Timeline position for the first image.
            per_image_seconds: Display duration per image.
            fade_seconds: Fade-in and fade-out duration (0 to disable).

        Returns:
            The list of placed image clips.
        """
        track = self.timeline.get_or_create_track(track_name)
        cursor_seconds: float = start_seconds
        placed_clips: list[BaseClip] = []

        for image_path in image_file_paths:
            media = self.import_media(Path(image_path))
            clip = track.add_image(media.id, start_seconds=cursor_seconds, duration_seconds=per_image_seconds)
            if fade_seconds > 0:
                clip.fade_in(fade_seconds)
                clip.fade_out(fade_seconds)
            placed_clips.append(clip)
            cursor_seconds += per_image_seconds

        return placed_clips

    def copy_to(self, dest_path: str | Path) -> 'Project':
        """Copy this project to a new location.

        Args:
            dest_path: Destination path for the .cmproj copy.

        Returns:
            The loaded Project at the new location.
        """
        dst = Path(dest_path)
        if dst.exists():
            raise FileExistsError(f'Destination already exists: {dst}')
        shutil.copytree(self.file_path, dst)
        return load_project(str(dst))

    @property
    def _project_file(self) -> Path:
        """Locate the .tscproj JSON file within the project bundle."""
        if self.file_path.is_dir():
            for file in self.file_path.iterdir():
                if file.is_file() and file.suffix == '.tscproj':
                    return file
            raise FileNotFoundError(
                f"No .tscproj file found in '{self.file_path}'. "
                f"Ensure the path points to a valid .cmproj bundle."
            )
        return self.file_path

    def export_all(self, output_dir: str | Path) -> dict[str, Path]:
        """Export project in all available formats.

        Creates: report.md, report.json, timeline.json, markers.srt, timeline.edl

        Returns dict mapping format name to output path.
        """
        from camtasia.export import (
            export_project_report,
            export_markers_as_srt,
            export_edl,
        )
        from camtasia.export.timeline_json import export_timeline_json

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        results = {}
        results['report_md'] = export_project_report(self, out / 'report.md', format='markdown')
        results['report_json'] = export_project_report(self, out / 'report.json', format='json')
        results['timeline_json'] = export_timeline_json(self, out / 'timeline.json')
        results['markers_srt'] = export_markers_as_srt(self, out / 'markers.srt')
        results['edl'] = export_edl(self, out / 'timeline.edl')
        return results

    def set_canvas_size(self, width: int, height: int) -> None:
        """Set the project canvas dimensions."""
        self.width = width
        self.height = height

    def __repr__(self) -> str:
        return f'<Project {self.title!r} {self.width}x{self.height} tracks={self.track_count} clips={self.clip_count}>'

    def strip_audio(self) -> int:
        """Remove all audio clips from all tracks. Returns count removed."""
        count = 0
        for track in self.timeline.tracks:
            count += track.remove_clips_by_type('AMFile')
        return count

    def remove_all_effects(self) -> int:
        """Remove all effects from all clips. Returns count removed."""
        count = 0
        for track in self.timeline.tracks:
            for clip in track.clips:
                count += len(clip._data.get('effects', []))
                clip._data['effects'] = []
        return count

    def summary_table(self) -> str:
        """Return a markdown table summarizing all tracks and clips."""
        lines = ['| Track | Clips | Types | Duration | Effects |', '|-------|-------|-------|----------|---------|']
        for track in self.timeline.tracks:
            types = ', '.join(sorted(track.clip_types)) if track.clip_types else '-'
            effects = ', '.join(sorted(track.effect_names)) if track.effect_names else '-'
            lines.append(f'| {track.name or "(unnamed)"} | {len(track)} | {types} | {track.total_duration_seconds:.1f}s | {effects} |')
        lines.append(f'| **Total** | **{self.clip_count}** | | **{self.duration_seconds:.1f}s** | |')
        return '\n'.join(lines)

    def save_with_history(self) -> None:
        """Save the project and persist undo history to a sidecar file."""
        self.save()
        history_file_path: Path = self.file_path / '.pycamtasia_history.json'
        history_file_path.write_text(self.history.to_json())

    def load_history(self) -> None:
        """Load persisted undo history from the sidecar file."""
        from camtasia.history import ChangeHistory
        history_file_path: Path = self.file_path / '.pycamtasia_history.json'
        if history_file_path.exists():
            self._history = ChangeHistory.from_json(history_file_path.read_text())

    def diff_from(self, other: Project) -> list[dict[str, Any]]:
        """Return JSON Patch operations showing differences from another project.

        Useful for comparing two versions of the same project.

        Args:
            other: The project to compare against.

        Returns:
            List of RFC 6902 JSON Patch operations.
        """
        import jsonpatch
        patch = jsonpatch.make_patch(other._data, self._data)
        return patch.patch  # type: ignore[no-any-return]

    def diff_summary(self, other: Project) -> str:
        """Human-readable summary of differences from another project."""
        patch_operations = self.diff_from(other)
        if not patch_operations:
            return 'No differences'
        operation_counts: dict[str, int] = {}
        for operation in patch_operations:
            operation_type = operation.get('op', '?')
            operation_counts[operation_type] = operation_counts.get(operation_type, 0) + 1
        summary_parts = [f'{count} {op_type}' for op_type, count in sorted(operation_counts.items())]
        return f'{len(patch_operations)} changes: {", ".join(summary_parts)}'

    def to_dict(self) -> dict:
        """Return a deep copy of the project data dict."""
        import copy
        return copy.deepcopy(self._data)

    @property
    def media_summary(self) -> dict[str, int]:
        """Count of media entries by file extension."""
        from collections import Counter
        extension_counter: Counter[str] = Counter()
        for media_entry in self.media_bin:
            source_path: str = str(media_entry.source)
            extension: str = source_path.rsplit('.', 1)[-1].lower() if '.' in source_path else 'unknown'
            extension_counter[extension] += 1
        return dict(extension_counter)

    def move_all_clips_to_track(self, source_track_name: str, target_track_name: str) -> int:
        """Move all clips from one track to another by name.

        Args:
            source_track_name: Name of the track to move clips from.
            target_track_name: Name of the track to move clips to.

        Returns:
            The number of clips moved.

        Raises:
            KeyError: If either track name is not found.
        """
        source_track: Track | None = self.timeline.find_track_by_name(source_track_name)
        target_track: Track | None = self.timeline.find_track_by_name(target_track_name)
        if source_track is None:
            raise KeyError(f'Source track not found: {source_track_name}')
        if target_track is None:
            raise KeyError(f'Target track not found: {target_track_name}')
        clip_ids_to_move: list[int] = list(source_track.clip_ids)
        for clip_id in clip_ids_to_move:
            source_track.move_clip_to_track(clip_id, target_track)
        return len(clip_ids_to_move)

    def add_title_card(
        self,
        title_text: str,
        start_seconds: float = 0.0,
        duration_seconds: float = 5.0,
        track_name: str = 'Titles',
        font_name: str = 'Helvetica Neue',
        font_weight: str = 'Bold',
        font_size: float = 72.0,
        font_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
        fade_seconds: float = 0.5,
    ) -> BaseClip:
        """Add a text title card to the timeline.

        Creates a callout clip on the named track with the given text and
        styling. Optionally applies fade-in and fade-out transitions.

        Args:
            title_text: The text to display on the title card.
            start_seconds: Timeline position where the title card begins.
            duration_seconds: How long the title card is visible.
            track_name: Name of the track to place the title card on.
            font_name: Font family name.
            font_weight: Font weight (e.g. 'Bold', 'Regular').
            font_size: Font size in points.
            font_color: RGB color as a tuple of floats in [0.0, 1.0].
            fade_seconds: Duration of fade-in and fade-out. Pass 0 to skip.

        Returns:
            The created callout clip.
        """
        track = self.timeline.get_or_create_track(track_name)
        callout = track.add_callout(
            title_text, start_seconds, duration_seconds,
            font_name=font_name, font_weight=font_weight, font_size=font_size,
        )
        callout.set_colors(font_color=font_color)
        if fade_seconds > 0:
            callout.fade_in(fade_seconds)
            callout.fade_out(fade_seconds)
        return callout

    def add_background_music(
        self,
        audio_path: Path | str,
        volume: float = 0.3,
        fade_in_seconds: float = 2.0,
        fade_out_seconds: float = 3.0,
        track_name: str = 'Background Music',
    ) -> BaseClip:
        """Import and place background music spanning the full timeline.

        The audio is placed at the start and trimmed to match the timeline
        duration. Volume is reduced and fades are applied.
        """
        media = self.import_media(Path(audio_path))
        track = self.timeline.get_or_create_track(track_name)
        timeline_duration: float = self.duration_seconds
        if timeline_duration == 0:
            timeline_duration = 60.0  # fallback for empty projects
        clip = track.add_audio(
            media.id,
            start_seconds=0.0,
            duration_seconds=timeline_duration,
        )
        clip.volume = volume
        if fade_in_seconds > 0:
            clip.fade_in(fade_in_seconds)
        if fade_out_seconds > 0:
            clip.fade_out(fade_out_seconds)
        return clip

    def apply_to_all_groups(self, operation: Callable[[Group], Any]) -> int:
        """Apply a callable to every Group clip in the project.

        Args:
            operation: A callable that accepts a single :class:`Group` argument.

        Returns:
            The number of Group clips the operation was applied to.
        """
        group_pairs: list[tuple[Track, Group]] = self.all_groups
        for _track, group in group_pairs:
            operation(group)
        return len(group_pairs)

    def mute_all_groups(self) -> int:
        """Mute every Group clip in the project.

        Returns:
            The number of Group clips that were muted.
        """
        return self.apply_to_all_groups(lambda group: group.mute())

    def add_subtitle_track(
        self,
        subtitle_entries: list[tuple[float, float, str]],
        track_name: str = 'Subtitles',
        font_size: float = 36.0,
        font_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> list[BaseClip]:
        """Add subtitle text entries to a dedicated track.

        Each entry is placed as a callout clip at the specified time and
        duration. All subtitles share the same font size and color.

        Args:
            subtitle_entries: List of (start_seconds, duration_seconds, text)
                tuples, one per subtitle line.
            track_name: Name of the track to place subtitles on.
            font_size: Font size in points for all subtitle clips.
            font_color: RGB color as a tuple of floats in [0.0, 1.0].

        Returns:
            List of created callout clips in the same order as the input.
        """
        track = self.timeline.get_or_create_track(track_name)
        placed_subtitles: list[BaseClip] = []
        for entry_start, entry_duration, entry_text in subtitle_entries:
            callout = track.add_callout(
                entry_text, entry_start, entry_duration,
                font_size=font_size,
            )
            callout.set_colors(font_color=font_color)
            placed_subtitles.append(callout)
        return placed_subtitles

    def add_callout_sequence(
        self,
        callout_entries: list[tuple[float, float, str]],
        track_name: str = 'Callouts',
        font_size: float = 24.0,
        fade_seconds: float = 0.3,
    ) -> list[BaseClip]:
        """Add a sequence of timed callout annotations.

        Args:
            callout_entries: List of (start_seconds, duration_seconds, text) tuples.
            track_name: Name of the track to place callouts on.
            font_size: Font size in points for all callouts.
            fade_seconds: Fade-in and fade-out duration (0 to disable).

        Returns:
            List of created callout clips.
        """
        track = self.timeline.get_or_create_track(track_name)
        placed_callouts: list[BaseClip] = []
        for entry_start, entry_duration, entry_text in callout_entries:
            callout = track.add_callout(
                entry_text, entry_start, entry_duration,
                font_size=font_size,
            )
            if fade_seconds > 0:
                callout.fade_in(fade_seconds)
                callout.fade_out(fade_seconds)
            placed_callouts.append(callout)
        return placed_callouts

    def add_lower_third(
        self,
        title_text: str,
        subtitle_text: str = '',
        start_seconds: float = 0.0,
        duration_seconds: float = 5.0,
        track_name: str = 'Lower Thirds',
        fade_seconds: float = 0.5,
    ) -> BaseClip:
        """Add a lower-third title overlay.

        Creates a callout positioned in the lower portion of the frame
        with title and optional subtitle text.
        """
        display_text: str = title_text
        if subtitle_text:
            display_text = f'{title_text}\n{subtitle_text}'
        track = self.timeline.get_or_create_track(track_name)
        callout = track.add_callout(
            display_text, start_seconds, duration_seconds,
            font_size=28.0,
        )
        if fade_seconds > 0:
            callout.fade_in(fade_seconds)
            callout.fade_out(fade_seconds)
        return callout

    def add_section_divider(
        self,
        title_text: str,
        at_seconds: float,
        duration_seconds: float = 3.0,
        track_name: str = 'Section Dividers',
        fade_seconds: float = 0.5,
    ) -> BaseClip:
        """Add a section divider title card at the specified time.
        
        Creates a full-screen text callout that serves as a visual
        separator between sections of the video.
        """
        track = self.timeline.get_or_create_track(track_name)
        callout = track.add_callout(
            title_text, at_seconds, duration_seconds,
            font_size=48.0,
        )
        if fade_seconds > 0:
            callout.fade_in(fade_seconds)
            callout.fade_out(fade_seconds)
        # Add a marker at this section
        from camtasia.timing import seconds_to_ticks
        self.timeline.markers.add(title_text, seconds_to_ticks(at_seconds))
        return callout

    def add_end_card(
        self,
        title_text: str = 'Thank You',
        subtitle_text: str = '',
        duration_seconds: float = 5.0,
        track_name: str = 'End Card',
        fade_seconds: float = 1.0,
    ) -> BaseClip:
        """Add an end card at the end of the timeline."""
        end_time: float = self.duration_seconds
        display_text: str = title_text
        if subtitle_text:
            display_text = f'{title_text}\n{subtitle_text}'
        track = self.timeline.get_or_create_track(track_name)
        callout = track.add_callout(
            display_text, end_time, duration_seconds,
            font_size=48.0,
        )
        if fade_seconds > 0:
            callout.fade_in(fade_seconds)
            callout.fade_out(fade_seconds)
        return callout

    def add_chapter_markers(
        self,
        chapters: list[tuple[float, str]],
    ) -> int:
        """Add timeline markers at chapter boundaries.

        Args:
            chapters: List of (time_seconds, chapter_name) tuples.
        Returns:
            Number of markers added.
        """
        for time_seconds, chapter_name in chapters:
            self.timeline.markers.add(chapter_name, seconds_to_ticks(time_seconds))
        return len(chapters)

    def export_project_report(self, output_path: str | Path) -> Path:
        """Export a comprehensive project report as a markdown file.

        Includes: project summary, track listing, clip inventory,
        effect usage, transition listing, and validation results.
        """
        from pathlib import Path as P
        path = P(output_path)
        lines: list[str] = []
        lines.append(f'# Project Report: {self.title}')
        lines.append('')
        lines.append('## Overview')
        for key, value in self.statistics().items():
            lines.append(f'- **{key}**: {value}')
        lines.append('')
        lines.append('## Tracks')
        for track in self.timeline.tracks:
            lines.append(f'### {track.name}')
            lines.append(f'- Clips: {len(track)}')
            lines.append(f'- Duration: {track.total_duration_seconds:.2f}s')
            for clip in track.clips:
                lines.append(f'  - {clip.clip_type}(id={clip.id}) {clip.duration_seconds:.2f}s')
            lines.append('')
        issues = self.validate()
        lines.append('## Validation')
        if issues:
            for issue in issues:
                lines.append(f'- [{issue.level}] {issue.message}')
        else:
            lines.append('No issues found.')
        path.write_text('\n'.join(lines))
        return path

    def apply_template_effects(
        self,
        effect_config: dict[str, list[str]],
    ) -> int:
        """Apply effects to clips based on their type.

        Args:
            effect_config: Dict mapping clip types to effect method names.
                Example: {'VMFile': ['add_drop_shadow', 'add_round_corners'],
                          'IMFile': ['add_drop_shadow']}
        Returns:
            Number of effects applied.
        """
        count: int = 0
        for _, clip in self.all_clips:
            clip_type: str = clip.clip_type
            if clip_type in effect_config:
                for method_name in effect_config[clip_type]:
                    if hasattr(clip, method_name):
                        getattr(clip, method_name)()
                        count += 1
        return count

    def apply_color_grade(
        self,
        brightness: float = 0.0,
        contrast: float = 0.0,
        saturation: float = 0.0,
        clip_types: list[str] | None = None,
    ) -> int:
        """Apply color adjustment to all video/image clips.

        Args:
            brightness: Brightness adjustment (-1.0 to 1.0).
            contrast: Contrast adjustment (-1.0 to 1.0).
            saturation: Saturation adjustment (-1.0 to 1.0).
            clip_types: Clip types to apply to. Defaults to ['VMFile', 'IMFile', 'ScreenVMFile'].
        """
        if clip_types is None:
            clip_types = ['VMFile', 'IMFile', 'ScreenVMFile']
        count: int = 0
        for _, clip in self.all_clips:
            if clip.clip_type in clip_types:
                clip.add_color_adjustment(
                    brightness=brightness,
                    contrast=contrast,
                    saturation=saturation,
                )
                count += 1
        return count

    def strip_all_effects(self) -> int:
        """Remove all effects from all clips. Returns count removed."""
        count: int = 0
        for _, clip in self.all_clips:
            effects = clip._data.get('effects', [])
            count += len(effects)
            clip._data['effects'] = []
        return count

    def add_zoom_to_region(
        self,
        clip: BaseClip,
        start_seconds: float,
        duration_seconds: float,
        scale: float = 2.0,
        center_x: float = 0.5,
        center_y: float = 0.5,
    ) -> BaseClip:
        """Add a zoom-in animation to a clip at a specific time.

        Creates scale and translation keyframes that zoom into a region
        of the clip, hold, then zoom back out.
        """
        # Calculate translation to center on the target region
        translate_x: float = (0.5 - center_x) * (scale - 1) * self.width
        translate_y: float = (0.5 - center_y) * (scale - 1) * self.height

        clip.set_scale_keyframes([
            (0.0, 1.0),
            (start_seconds, 1.0),
            (start_seconds + 0.3, scale),
            (start_seconds + duration_seconds - 0.3, scale),
            (start_seconds + duration_seconds, 1.0),
        ])
        clip.set_position_keyframes([
            (0.0, 0.0, 0.0),
            (start_seconds, 0.0, 0.0),
            (start_seconds + 0.3, translate_x, translate_y),
            (start_seconds + duration_seconds - 0.3, translate_x, translate_y),
            (start_seconds + duration_seconds, 0.0, 0.0),
        ])
        return clip


    def normalize_audio(self, target_gain: float = 1.0) -> int:
        """Set all audio clips to the same gain level. Returns count adjusted."""
        count: int = 0
        for _, clip in self.all_clips:
            if clip.is_audio or clip.clip_type in ('AMFile', 'UnifiedMedia'):
                clip.gain = target_gain
                count += 1
        return count

    def mute_track(self, track_name: str) -> bool:
        """Mute a track by name. Returns True if found."""
        track = self.timeline.find_track_by_name(track_name)
        if track is None:
            return False
        track.audio_muted = True
        return True

    @staticmethod
    def convert_audio_to_wav(
        input_path: str | Path,
        output_path: str | Path | None = None,
        sample_rate: int = 48000,
    ) -> Path:
        """Convert an audio file to PCM WAV format using ffmpeg.

        This is recommended before importing audio into Camtasia projects,
        especially for compressed formats (MP3, AAC) that may have
        unreliable duration metadata.

        Args:
            input_path: Path to the input audio file.
            output_path: Path for the output WAV. If None, replaces the
                input file extension with .wav.
            sample_rate: Target sample rate (default 48000 Hz).

        Returns:
            Path to the converted WAV file.

        Raises:
            FileNotFoundError: If ffmpeg is not installed.
            subprocess.CalledProcessError: If conversion fails.
        """
        import subprocess
        input_p = Path(input_path)
        if output_path is None:
            output_p = input_p.with_suffix('.wav')
        else:
            output_p = Path(output_path)

        subprocess.run(
            ['ffmpeg', '-y', '-i', str(input_p), '-acodec', 'pcm_s16le',
             '-ar', str(sample_rate), str(output_p)],
            capture_output=True, check=True,
        )
        return output_p

    def import_and_convert_audio(
        self,
        audio_path: str | Path,
        sample_rate: int = 48000,
    ) -> Any:
        """Convert audio to WAV (if needed) and import into the project.

        Automatically converts compressed audio formats to PCM WAV
        before importing to avoid duration metadata issues.
        """
        import subprocess
        input_p = Path(audio_path)
        # Check if already PCM WAV
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=codec_name', '-of', 'csv=p=0',
                 str(input_p)],
                capture_output=True, text=True, check=True,
            )
            codec = result.stdout.strip()
            if codec == 'pcm_s16le':
                return self.import_media(input_p)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass  # ffprobe not available, convert anyway

        # Convert to WAV
        wav_path = self.convert_audio_to_wav(input_p, sample_rate=sample_rate)
        return self.import_media(wav_path)

    def build_from_screenplay_file(
        self,
        screenplay_path: str | Path,
        audio_dir: str | Path,
        track_name: str = 'Voiceover',
        gap_seconds: float = 0.5,
    ) -> dict[str, Any]:
        """Parse a screenplay file and build the voiceover timeline.

        Reads the screenplay markdown, finds matching audio files in
        audio_dir, and places them sequentially on the timeline.

        Args:
            screenplay_path: Path to the screenplay markdown file.
            audio_dir: Directory containing VO audio files.
            track_name: Name for the voiceover track.
            gap_seconds: Gap between VO clips in seconds.

        Returns:
            Dict with 'clips' (placed clips), 'total_duration' (seconds),
            'sections' (parsed screenplay sections).
        """
        from camtasia.screenplay import parse_screenplay
        screenplay = parse_screenplay(Path(screenplay_path))

        track = self.timeline.get_or_create_track(track_name)
        cursor_seconds: float = 0.0
        placed_clips: list[BaseClip] = []
        audio_dir_path = Path(audio_dir)

        for vo_block in screenplay.vo_blocks:
            audio_file = audio_dir_path / f'{vo_block.id}.wav'
            if not audio_file.exists():
                continue
            media = self.import_media(audio_file)
            duration_seconds: float = 5.0  # fallback
            for source in self._data.get('sourceBin', []):
                if source.get('id') == media.id:
                    tracks = source.get('sourceTracks', [])
                    if tracks:
                        r = tracks[0].get('range', [0, 0])
                        er = tracks[0].get('editRate', 48000)
                        if er > 0:
                            duration_seconds = (r[1] - r[0]) / er
                    break
            clip = track.add_audio(media.id, start_seconds=cursor_seconds, duration_seconds=duration_seconds)
            placed_clips.append(clip)
            cursor_seconds += duration_seconds + gap_seconds

        return {
            'clips': placed_clips,
            'total_duration': cursor_seconds,
            'sections': screenplay.sections,
        }

    def add_watermark(
        self,
        image_path: str | Path,
        opacity: float = 0.3,
        track_name: str = 'Watermark',
    ) -> BaseClip:
        """Add a watermark image that spans the entire timeline.

        The image is placed on its own track with reduced opacity.
        """
        media = self.import_media(Path(image_path))
        track = self.timeline.get_or_create_track(track_name)
        timeline_duration: float = self.duration_seconds
        if timeline_duration == 0:
            timeline_duration = 60.0
        clip = track.add_image(
            media.id,
            start_seconds=0.0,
            duration_seconds=timeline_duration,
        )
        clip.opacity = opacity
        return clip

    def add_countdown(
        self,
        seconds: int = 3,
        track_name: str = 'Countdown',
        per_number_seconds: float = 1.0,
    ) -> list[BaseClip]:
        """Add a countdown (3, 2, 1) at the start of the timeline."""
        track = self.timeline.get_or_create_track(track_name)
        clips: list[BaseClip] = []
        for i in range(seconds, 0, -1):
            offset: float = (seconds - i) * per_number_seconds
            callout = track.add_callout(
                str(i), offset, per_number_seconds,
                font_size=96.0,
            )
            callout.fade_in(0.2)
            callout.fade_out(0.2)
            clips.append(callout)
        return clips

    def solo_track(self, track_name: str) -> bool:
        """Solo a track by name (mute all others). Returns True if found."""
        target = self.timeline.find_track_by_name(track_name)
        if target is None:
            return False
        for track in self.timeline.tracks:
            track.audio_muted = track.name != track_name
        return True


def load_project(file_path: str | Path, encoding: str | None = None) -> Project:
    """Load a Camtasia project from disk.

    Args:
        file_path: Path to the .cmproj directory or .tscproj file.
        encoding: Text encoding of the project file.

    Returns:
        A Project instance.
    """
    return Project(Path(file_path).resolve(), encoding=encoding)


@contextmanager
def use_project(
    file_path: str | Path,
    save_on_exit: bool = True,
    encoding: str | None = None,
) -> Iterator[Project]:
    """Context manager that loads a project and optionally saves on exit.

    Saves the project on normal exit if *save_on_exit* is True.
    Discards changes on exceptional exit.

    Args:
        file_path: Path to the .cmproj directory or .tscproj file.
        save_on_exit: Whether to save on normal exit.
        encoding: Text encoding of the project file.

    Yields:
        A Project instance.
    """
    proj = load_project(file_path, encoding=encoding)
    yield proj
    if save_on_exit:
        proj.save()


def new_project(file_path: str | Path) -> None:
    """Create a new, empty Camtasia project at *file_path*.

    Copies the bundled template project to the target path.

    Args:
        file_path: Destination path for the new .cmproj bundle.
    """
    template = importlib_resources.files('camtasia').joinpath('resources', 'new.cmproj')
    shutil.copytree(str(template), str(file_path))
