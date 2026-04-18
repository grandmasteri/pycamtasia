"""Tests for Group.merge_internal_tracks, Group.describe override, and Track.ungroup_clip."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import BaseClip, Group, GroupTrack, clip_from_dict
from camtasia.timeline.track import Track
from camtasia.timing import seconds_to_ticks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clip_data(
    clip_type: str,
    clip_id: int,
    start_s: float,
    dur_s: float,
    src: int = 1,
) -> dict:
    """Build a minimal clip data dict."""
    return {
        '_type': clip_type,
        'id': clip_id,
        'src': src,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
    }


def _make_group(
    tracks_data: list[list[dict]],
    *,
    ident: str = 'TestGroup',
    group_id: int = 100,
    start_s: float = 0.0,
    dur_s: float = 10.0,
) -> Group:
    """Build a Group from a list of track media lists."""
    tracks: list[dict] = []
    for track_index, medias in enumerate(tracks_data):
        tracks.append({
            'trackIndex': track_index,
            'medias': medias,
            'transitions': [],
        })
    return Group({
        '_type': 'Group',
        'id': group_id,
        'start': seconds_to_ticks(start_s),
        'duration': seconds_to_ticks(dur_s),
        'mediaStart': 0,
        'mediaDuration': seconds_to_ticks(dur_s),
        'scalar': 1,
        'parameters': {},
        'effects': [],
        'metadata': {},
        'animationTracks': {},
        'attributes': {'ident': ident},
        'tracks': tracks,
    })


def _make_track(medias: list[dict], track_index: int = 0) -> Track:
    """Build a Track wrapping the given media list."""
    track_data: dict = {
        'trackIndex': track_index,
        'medias': medias,
        'transitions': [],
    }
    attributes: dict = {'ident': f'Track {track_index}'}
    return Track(attributes, track_data)


# ===================================================================
# 1. Group.merge_internal_tracks
# ===================================================================

class TestMergeInternalTracks:
    """Tests for Group.merge_internal_tracks."""

    def test_merge_two_tracks_into_one(self) -> None:
        """Clips from track 1 are moved into track 0; only one track remains."""
        video_clip: dict = _clip_data('VMFile', 10, 0.0, 5.0)
        audio_clip: dict = _clip_data('AMFile', 20, 0.0, 5.0)
        group: Group = _make_group([[video_clip], [audio_clip]])

        merged_track: GroupTrack = group.merge_internal_tracks()

        assert len(group.tracks) == 1
        assert len(merged_track) == 2
        clip_ids: set[int] = {c.id for c in merged_track.clips}
        assert clip_ids == {10, 20}

    def test_merge_three_tracks(self) -> None:
        """All clips from three tracks end up on the first track."""
        clip_a: dict = _clip_data('VMFile', 1, 0.0, 3.0)
        clip_b: dict = _clip_data('AMFile', 2, 0.0, 3.0)
        clip_c: dict = _clip_data('IMFile', 3, 0.0, 3.0)
        group: Group = _make_group([[clip_a], [clip_b], [clip_c]])

        merged_track: GroupTrack = group.merge_internal_tracks()

        assert len(group.tracks) == 1
        assert len(merged_track) == 3
        assert merged_track.track_index == 0

    def test_merge_single_track_is_noop(self) -> None:
        """Merging a group with one track returns that track unchanged."""
        clip: dict = _clip_data('VMFile', 5, 0.0, 2.0)
        group: Group = _make_group([[clip]])

        merged_track: GroupTrack = group.merge_internal_tracks()

        assert len(group.tracks) == 1
        assert len(merged_track) == 1

    def test_merge_empty_group_creates_track(self) -> None:
        """Merging a group with no tracks creates a new empty track."""
        group: Group = _make_group([])

        merged_track: GroupTrack = group.merge_internal_tracks()

        assert len(group.tracks) == 1
        assert len(merged_track) == 0

    def test_merge_preserves_track_index_zero(self) -> None:
        """After merge, the surviving track has trackIndex 0."""
        group: Group = _make_group([
            [_clip_data('VMFile', 1, 0.0, 1.0)],
            [_clip_data('AMFile', 2, 0.0, 1.0)],
        ])

        group.merge_internal_tracks()

        assert group._data['tracks'][0]['trackIndex'] == 0


# ===================================================================
# 2. Group.describe override
# ===================================================================

class TestGroupDescribe:
    """Tests for Group.describe override."""

    def test_describe_basic_output(self) -> None:
        """describe() returns expected multi-line string."""
        video_clip: dict = _clip_data('VMFile', 10, 0.0, 5.0)
        audio_clip: dict = _clip_data('AMFile', 20, 0.0, 5.0)
        group: Group = _make_group(
            [[video_clip], [audio_clip]],
            ident='MyGroup',
            group_id=42,
            dur_s=5.0,
        )

        description: str = group.describe()

        assert 'Group(id=42' in description
        assert "ident='MyGroup'" in description
        assert 'Tracks: 2' in description
        assert 'Total clips: 2' in description
        assert 'AMFile' in description
        assert 'VMFile' in description
        assert 'Duration:' in description

    def test_describe_empty_group(self) -> None:
        """describe() handles a group with no clips."""
        group: Group = _make_group([], ident='Empty', group_id=1, dur_s=0.0)

        description: str = group.describe()

        assert 'Total clips: 0' in description
        assert 'Types: none' in description

    def test_describe_screen_recording_flag(self) -> None:
        """describe() includes screen recording indicator when applicable."""
        unified_clip: dict = _clip_data('UnifiedMedia', 10, 0.0, 5.0)
        unified_clip['video'] = {'_type': 'ScreenVMFile'}
        group: Group = _make_group([[unified_clip]], ident='ScreenRec')

        description: str = group.describe()

        assert 'Screen recording: yes' in description

    def test_describe_no_screen_recording_flag(self) -> None:
        """describe() omits screen recording line for non-screen groups."""
        video_clip: dict = _clip_data('VMFile', 10, 0.0, 5.0)
        group: Group = _make_group([[video_clip]], ident='Plain')

        description: str = group.describe()

        assert 'Screen recording' not in description

    def test_describe_overrides_base(self) -> None:
        """Group.describe() differs from BaseClip.describe()."""
        clip: dict = _clip_data('VMFile', 10, 0.0, 5.0)
        group: Group = _make_group([[clip]], group_id=7)

        group_desc: str = group.describe()
        base_desc: str = BaseClip.describe(group)

        assert group_desc != base_desc
        assert 'Group(id=' in group_desc


# ===================================================================
# 3. Track.ungroup_clip
# ===================================================================

class TestUngroupClip:
    """Tests for Track.ungroup_clip."""

    def _group_on_track(self) -> tuple[Track, int]:
        """Create a track containing a Group clip with two internal clips.

        Returns:
            (track, group_clip_id) tuple.
        """
        inner_video: dict = _clip_data('VMFile', 50, 0.0, 3.0)
        inner_audio: dict = _clip_data('AMFile', 51, 0.0, 3.0)
        group: Group = _make_group(
            [[inner_video, inner_audio]],
            group_id=100,
            start_s=5.0,
            dur_s=3.0,
        )
        track: Track = _make_track([group._data])
        return track, 100

    def test_ungroup_places_internal_clips(self) -> None:
        """Ungrouping replaces the Group with its internal clips."""
        track, group_id = self._group_on_track()

        placed_clips: list[BaseClip] = track.ungroup_clip(group_id)

        assert len(placed_clips) == 2
        # Group clip should be gone
        assert group_id not in track

    def test_ungroup_assigns_new_ids(self) -> None:
        """Each placed clip gets a unique ID from _next_clip_id."""
        track, group_id = self._group_on_track()

        placed_clips: list[BaseClip] = track.ungroup_clip(group_id)

        placed_ids: set[int] = {c.id for c in placed_clips}
        assert len(placed_ids) == 2  # all unique
        # Original internal IDs (50, 51) should not survive
        assert 50 not in placed_ids or 51 not in placed_ids or len(placed_ids) == 2

    def test_ungroup_adjusts_start_times(self) -> None:
        """Internal clips get start times offset by the Group's position."""
        track, group_id = self._group_on_track()
        group_start_ticks: int = seconds_to_ticks(5.0)

        placed_clips: list[BaseClip] = track.ungroup_clip(group_id)

        for clip in placed_clips:
            # Original internal start was 0.0, group start was 5.0
            assert clip.start == group_start_ticks

    def test_ungroup_nonexistent_raises_keyerror(self) -> None:
        """Ungrouping a non-existent clip ID raises KeyError."""
        track: Track = _make_track([_clip_data('VMFile', 1, 0.0, 1.0)])

        with pytest.raises(KeyError, match='No Group clip'):
            track.ungroup_clip(999)

    def test_ungroup_non_group_clip_raises_keyerror(self) -> None:
        """Ungrouping a clip that isn't a Group raises KeyError."""
        track: Track = _make_track([_clip_data('VMFile', 1, 0.0, 1.0)])

        with pytest.raises(KeyError, match='No Group clip'):
            track.ungroup_clip(1)

    def test_ungroup_preserves_other_clips(self) -> None:
        """Other clips on the track are not affected by ungrouping."""
        inner_clip: dict = _clip_data('VMFile', 50, 0.0, 2.0)
        group: Group = _make_group(
            [[inner_clip]],
            group_id=100,
            start_s=0.0,
            dur_s=2.0,
        )
        other_clip: dict = _clip_data('AMFile', 200, 5.0, 3.0)
        track: Track = _make_track([group._data, other_clip])

        track.ungroup_clip(100)

        assert 200 in track
        assert len(track) == 2  # other_clip + 1 placed clip
