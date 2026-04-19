"""Tests for apply_if, partition_by_type, media_summary, and clip_density."""
from __future__ import annotations

from typing import Any

import pytest
from camtasia.timeline.clips.base import BaseClip
from camtasia.timeline.track import Track
from camtasia.timeline.timeline import Timeline
from camtasia.timing import seconds_to_ticks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_clip(clip_id: int = 1, clip_type: str = 'VMFile', start: int = 0, duration: int = 1000, **extra: Any) -> BaseClip:
    data: dict[str, Any] = {'id': clip_id, '_type': clip_type, 'start': start, 'duration': duration, **extra}
    return BaseClip(data)


def _make_track(medias: list[dict[str, Any]] | None = None, name: str = 'T') -> Track:
    data: dict[str, Any] = {'trackIndex': 0, 'medias': medias or []}
    attrs: dict[str, Any] = {'ident': name}
    return Track(attrs, data)


def _make_timeline(track_specs: list[tuple[str, list[dict[str, Any]]]]) -> Timeline:
    tracks: list[dict[str, Any]] = []
    attrs: list[dict[str, Any]] = []
    for i, (name, medias) in enumerate(track_specs):
        tracks.append({'trackIndex': i, 'medias': medias})
        attrs.append({'ident': name})
    data: dict[str, Any] = {
        'sceneTrack': {'scenes': [{'csml': {'tracks': tracks}}]},
        'trackAttributes': attrs,
    }
    return Timeline(data)


# ---------------------------------------------------------------------------
# BaseClip.apply_if
# ---------------------------------------------------------------------------

class TestApplyIf:
    """Tests for BaseClip.apply_if."""

    def test_apply_if_predicate_true_runs_operation(self) -> None:
        clip: BaseClip = _make_clip(duration=1000)
        result: BaseClip = clip.apply_if(
            lambda c: c.duration == 1000,
            lambda c: setattr(c, 'duration', 2000),
        )
        assert clip.duration == 2000
        assert result is clip

    def test_apply_if_predicate_false_skips_operation(self) -> None:
        clip: BaseClip = _make_clip(duration=1000)
        result: BaseClip = clip.apply_if(
            lambda c: c.duration == 9999,
            lambda c: setattr(c, 'duration', 2000),
        )
        assert clip.duration == 1000
        assert result is clip

    def test_apply_if_returns_self_for_chaining(self) -> None:
        clip: BaseClip = _make_clip()
        chained: BaseClip = clip.apply_if(lambda c: True, lambda c: None)
        assert chained is clip

    def test_apply_if_with_type_check_predicate(self) -> None:
        audio_clip: BaseClip = _make_clip(clip_type='AMFile')
        muted: list[int] = []
        audio_clip.apply_if(
            lambda c: c.clip_type == 'AMFile',
            lambda c: muted.append(c.id),
        )
        assert muted == [1]

    def test_apply_if_false_predicate_no_side_effects(self) -> None:
        clip: BaseClip = _make_clip(clip_type='VMFile')
        side_effects: list[int] = []
        clip.apply_if(
            lambda c: c.clip_type == 'AMFile',
            lambda c: side_effects.append(c.id),
        )
        assert side_effects == []


# ---------------------------------------------------------------------------
# Track.partition_by_type
# ---------------------------------------------------------------------------

class TestPartitionByType:
    """Tests for Track.partition_by_type."""

    def test_partition_empty_track(self) -> None:
        track: Track = _make_track(medias=[])
        partitioned: dict[str, list[BaseClip]] = track.partition_by_type()
        assert partitioned == {}

    def test_partition_single_type(self) -> None:
        medias: list[dict[str, Any]] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 1000},
            {'id': 2, '_type': 'VMFile', 'start': 1000, 'duration': 1000},
        ]
        track: Track = _make_track(medias=medias)
        partitioned: dict[str, list[BaseClip]] = track.partition_by_type()
        assert list(partitioned.keys()) == ['VMFile']
        assert len(partitioned['VMFile']) == 2

    def test_partition_multiple_types(self) -> None:
        medias: list[dict[str, Any]] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': 1000},
            {'id': 2, '_type': 'AMFile', 'start': 0, 'duration': 1000},
            {'id': 3, '_type': 'VMFile', 'start': 1000, 'duration': 1000},
        ]
        track: Track = _make_track(medias=medias)
        partitioned: dict[str, list[BaseClip]] = track.partition_by_type()
        assert len(partitioned['VMFile']) == 2
        assert len(partitioned['AMFile']) == 1

    def test_partition_returns_plain_dict(self) -> None:
        medias: list[dict[str, Any]] = [
            {'id': 1, '_type': 'IMFile', 'start': 0, 'duration': 500},
        ]
        track: Track = _make_track(medias=medias)
        partitioned: dict[str, list[BaseClip]] = track.partition_by_type()
        assert type(partitioned) is dict


# ---------------------------------------------------------------------------
# Project.media_summary
# ---------------------------------------------------------------------------

class TestMediaSummary:
    """Tests for Project.media_summary."""

    def test_media_summary_on_new_project(self, project) -> None:
        summary: dict[str, int] = project.media_summary
        assert summary == {}

    def test_media_summary_returns_dict(self, project) -> None:
        summary: dict[str, int] = project.media_summary
        for extension, count in summary.items():
            assert isinstance(extension, str)
            assert isinstance(count, int)
            assert count > 0


# ---------------------------------------------------------------------------
# Timeline.clip_density
# ---------------------------------------------------------------------------

class TestClipDensity:
    """Tests for Timeline.clip_density."""

    def test_clip_density_empty_timeline(self) -> None:
        timeline: Timeline = _make_timeline([('Empty', [])])
        assert timeline.clip_density == 0.0

    def test_clip_density_single_track_full_coverage(self) -> None:
        one_second_ticks: int = seconds_to_ticks(1.0)
        medias: list[dict[str, Any]] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_second_ticks},
        ]
        timeline: Timeline = _make_timeline([('Video', medias)])
        density: float = timeline.clip_density
        assert density == pytest.approx(1.0)

    def test_clip_density_multiple_tracks(self) -> None:
        one_second_ticks: int = seconds_to_ticks(1.0)
        video_medias: list[dict[str, Any]] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': one_second_ticks},
        ]
        audio_medias: list[dict[str, Any]] = [
            {'id': 2, '_type': 'AMFile', 'start': 0, 'duration': one_second_ticks},
        ]
        timeline: Timeline = _make_timeline([
            ('Video', video_medias),
            ('Audio', audio_medias),
        ])
        density: float = timeline.clip_density
        assert density == pytest.approx(2.0)

    def test_clip_density_partial_coverage(self) -> None:
        half_second_ticks: int = seconds_to_ticks(0.5)
        one_second_ticks: int = seconds_to_ticks(1.0)
        medias: list[dict[str, Any]] = [
            {'id': 1, '_type': 'VMFile', 'start': 0, 'duration': half_second_ticks},
            {'id': 2, '_type': 'VMFile', 'start': half_second_ticks, 'duration': half_second_ticks},
        ]
        # Timeline duration = 1s, total clip duration = 1s
        timeline: Timeline = _make_timeline([('Video', medias)])
        density: float = timeline.clip_density
        assert density == pytest.approx(1.0)

    def test_clip_density_no_clips_all_tracks(self) -> None:
        timeline: Timeline = _make_timeline([('A', []), ('B', [])])
        assert timeline.clip_density == 0.0


class TestMediaSummaryWithMedia:
    def test_media_summary_counts_extensions(self, project) -> None:
        """media_summary counts media by file extension."""
        from pathlib import Path
        wav_path: Path = Path(__file__).parent / 'fixtures' / 'empty.wav'
        project.import_media(wav_path)
        actual_summary: dict[str, int] = project.media_summary
        assert 'wav' in actual_summary
        assert actual_summary['wav'] == 1
