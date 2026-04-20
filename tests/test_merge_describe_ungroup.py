"""Tests for Group.merge_internal_tracks, Group.describe override, and Track.ungroup_clip."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips import BaseClip, Group, GroupTrack
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

        clip_ids: set[int] = {c.id for c in merged_track.clips}
        assert clip_ids == {10, 20}

    def test_merge_three_tracks(self) -> None:
        """All clips from three tracks end up on the first track."""
        clip_a: dict = _clip_data('VMFile', 1, 0.0, 3.0)
        clip_b: dict = _clip_data('AMFile', 2, 0.0, 3.0)
        clip_c: dict = _clip_data('IMFile', 3, 0.0, 3.0)
        group: Group = _make_group([[clip_a], [clip_b], [clip_c]])

        merged_track: GroupTrack = group.merge_internal_tracks()

        assert [c.clip_type for c in merged_track.clips] == ['VMFile', 'AMFile', 'IMFile']
        assert merged_track.track_index == 0

    def test_merge_single_track_is_noop(self) -> None:
        """Merging a group with one track returns that track unchanged."""
        clip: dict = _clip_data('VMFile', 5, 0.0, 2.0)
        group: Group = _make_group([[clip]])

        merged_track: GroupTrack = group.merge_internal_tracks()

        assert [c.id for c in merged_track.clips] == [5]

    def test_merge_empty_group_creates_track(self) -> None:
        """Merging a group with no tracks creates a new empty track."""
        group: Group = _make_group([])

        merged_track: GroupTrack = group.merge_internal_tracks()

        assert list(merged_track.clips) == []

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

        assert [c.clip_type for c in placed_clips] == ['VMFile', 'AMFile']
        # Group clip should be gone
        assert group_id not in track

    def test_ungroup_assigns_new_ids(self) -> None:
        """Each placed clip gets a unique ID from _next_clip_id."""
        track, group_id = self._group_on_track()

        placed_clips: list[BaseClip] = track.ungroup_clip(group_id)

        placed_ids: set[int] = {c.id for c in placed_clips}
        # Original internal IDs (50, 51) should not survive; all IDs unique
        assert placed_ids.isdisjoint({50, 51})

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
        assert {c.clip_type for c in track.clips} == {'VMFile', 'AMFile'}


# ---------------------------------------------------------------------------
# Bug 3: ungroup effect timing must be integer ticks, not string fractions
# Bug 6: StitchedMedia inner duration must be integer ticks
# Bug 7: StitchedMedia inner start must use round(), not int() truncation
# ---------------------------------------------------------------------------

def _make_group_with_scalar(inner_clips, scalar='1', start=0, duration=100):
    """Build a Group dict with a custom scalar for ungroup tests."""
    return Group({
        '_type': 'Group', 'id': 100,
        'start': start, 'duration': duration,
        'mediaStart': 0, 'mediaDuration': duration, 'scalar': scalar,
        'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        'attributes': {'ident': 'Test'},
        'tracks': [{'trackIndex': 0, 'medias': inner_clips, 'transitions': []}],
    })


class TestUngroupEffectTimingIntegerTicks:
    """Bug 3: Effect start/duration must be int after ungroup with non-unit scalar."""

    def test_effect_timing_is_int_after_ungroup(self) -> None:
        clip = {'id': 10, '_type': 'VMFile', 'src': 1,
                'start': 0, 'duration': 100,
                'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'effects': [{'effectName': 'Glow', 'start': 30, 'duration': 60}],
                'parameters': {}, 'metadata': {}, 'animationTracks': {}}
        group = _make_group_with_scalar([clip], scalar='2/3')
        clips = group.ungroup()
        eff = clips[0]._data['effects'][0]
        assert isinstance(eff['start'], int)
        assert isinstance(eff['duration'], int)


class TestUngroupStitchedMediaInnerDurationInt:
    """Bug 6: StitchedMedia inner duration must be int after ungroup."""

    def test_inner_duration_is_int(self) -> None:
        inner_seg = {
            'id': 20, '_type': 'ScreenVMFile', 'src': 1,
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        stitched = {
            'id': 10, '_type': 'StitchedMedia',
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'medias': [inner_seg],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        group = _make_group_with_scalar([stitched], scalar='2/3')
        clips = group.ungroup()
        for inner in clips[0]._data.get('medias', []):
            assert isinstance(inner['duration'], int), f"inner duration is {type(inner['duration'])}"


class TestUngroupStitchedMediaInnerStartRound:
    """Bug 7: StitchedMedia inner start must use round(), not int() truncation."""

    def test_inner_starts_are_consistent(self) -> None:
        seg1 = {
            'id': 20, '_type': 'ScreenVMFile', 'src': 1,
            'start': 0, 'duration': 50,
            'mediaStart': 0, 'mediaDuration': 50, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        seg2 = {
            'id': 21, '_type': 'ScreenVMFile', 'src': 1,
            'start': 50, 'duration': 50,
            'mediaStart': 50, 'mediaDuration': 50, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        stitched = {
            'id': 10, '_type': 'StitchedMedia',
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'medias': [seg1, seg2],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        group = _make_group_with_scalar([stitched], scalar='2/3')
        clips = group.ungroup()
        medias = clips[0]._data.get('medias', [])
        # Second segment start should equal first segment duration (no gap)
        assert medias[1]['start'] == medias[0]['duration']


# -- Bug: merge_internal_tracks must check nested IDs for collision --

class TestMergeInternalTracksNestedIdCollision:
    """merge_internal_tracks should detect collisions in nested IDs, not just top-level."""

    def test_nested_id_collision_triggers_remap(self) -> None:
        """If a nested ID in track[1] collides with any ID in track[0], remap."""
        # Track 0: clip with id=1 containing nested id=10
        clip_a = {
            '_type': 'Group', 'id': 1, 'src': 1,
            'start': 0, 'duration': 100, 'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'attributes': {'ident': 'A'},
            'tracks': [{'trackIndex': 0, 'medias': [
                {'_type': 'VMFile', 'id': 10, 'src': 1, 'start': 0, 'duration': 100,
                 'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                 'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
            ], 'transitions': []}],
        }
        # Track 1: clip with id=2 (no top-level collision) but nested id=10 (collision!)
        clip_b = {
            '_type': 'Group', 'id': 2, 'src': 1,
            'start': 100, 'duration': 100, 'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'attributes': {'ident': 'B'},
            'tracks': [{'trackIndex': 0, 'medias': [
                {'_type': 'VMFile', 'id': 10, 'src': 1, 'start': 0, 'duration': 100,
                 'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                 'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {}},
            ], 'transitions': []}],
        }
        group = _make_group([[clip_a], [clip_b]])
        group.merge_internal_tracks()
        # After merge, all IDs should be unique
        from camtasia.timeline.clips.group import _collect_all_ids
        all_ids: list[int] = []
        for m in group._data['tracks'][0]['medias']:
            all_ids.extend(_collect_all_ids(m))
        assert len(all_ids) == len(set(all_ids)), f"Duplicate IDs found: {all_ids}"


# -- Bug: ungroup must scale effects on nested StitchedMedia inner segments --

class TestUngroupNestedStitchedEffectsAndUnified:
    """Bugs 4-5: ungroup must scale effects on StitchedMedia inner segments
    and propagate scalar/duration to UnifiedMedia sub-clips within nested Groups."""

    def test_inner_segment_effects_scaled(self) -> None:
        """Effects on StitchedMedia inner segments within a nested Group must be scaled."""
        inner_seg = {
            'id': 20, '_type': 'ScreenVMFile', 'src': 1,
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'metadata': {}, 'animationTracks': {},
            'effects': [{'effectName': 'Glow', 'start': 10, 'duration': 50}],
        }
        stitched = {
            'id': 10, '_type': 'StitchedMedia',
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'medias': [inner_seg],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        nested_group = {
            'id': 5, '_type': 'Group',
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'attributes': {'ident': 'inner'},
            'tracks': [{'trackIndex': 0, 'medias': [stitched], 'transitions': []}],
        }
        group = _make_group_with_scalar([nested_group], scalar='2', start=0, duration=100)
        clips = group.ungroup()
        inner_group = clips[0]._data
        inner_stitched = inner_group['tracks'][0]['medias'][0]
        seg_eff = inner_stitched['medias'][0]['effects'][0]
        assert seg_eff['start'] == 20  # 10 * 2
        assert seg_eff['duration'] == 100  # 50 * 2

    def test_unified_media_sub_clips_propagated(self) -> None:
        """UnifiedMedia sub-clips within StitchedMedia in nested Groups must get scalar/duration."""
        inner_seg = {
            'id': 20, '_type': 'UnifiedMedia',
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'video': {
                '_type': 'VMFile', 'id': 21, 'src': 1,
                'start': 0, 'duration': 100, 'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
                'parameters': {}, 'effects': [{'effectName': 'Blur', 'start': 0, 'duration': 100}],
                'metadata': {}, 'animationTracks': {},
            },
            'audio': None,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        stitched = {
            'id': 10, '_type': 'StitchedMedia',
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'medias': [inner_seg],
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
        }
        nested_group = {
            'id': 5, '_type': 'Group',
            'start': 0, 'duration': 100,
            'mediaStart': 0, 'mediaDuration': 100, 'scalar': 1,
            'parameters': {}, 'effects': [], 'metadata': {}, 'animationTracks': {},
            'attributes': {'ident': 'inner'},
            'tracks': [{'trackIndex': 0, 'medias': [stitched], 'transitions': []}],
        }
        group = _make_group_with_scalar([nested_group], scalar='2', start=0, duration=100)
        clips = group.ungroup()
        inner_group = clips[0]._data
        inner_stitched = inner_group['tracks'][0]['medias'][0]
        um_seg = inner_stitched['medias'][0]
        assert um_seg['duration'] == 200  # 100 * 2
        video = um_seg['video']
        assert video['duration'] == 200
        assert video['effects'][0]['start'] == 0  # 0 * 2
        assert video['effects'][0]['duration'] == 200  # 100 * 2
