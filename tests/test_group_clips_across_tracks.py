"""Tests for Timeline.group_clips_across_tracks and Project convenience wrapper."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.group import Group
from camtasia.timing import seconds_to_ticks, ticks_to_seconds


class TestGroupClipsAcrossTracks:
    """Timeline.group_clips_across_tracks behaviour."""

    def test_basic_two_tracks(self, project):
        """Clips from two tracks are grouped onto a target track."""
        tl = project.timeline
        t0 = tl.add_track('Video')
        t1 = tl.add_track('Audio')
        c0 = t0.add_video(1, start_seconds=1.0, duration_seconds=2.0)
        c1 = t1.add_audio(2, start_seconds=2.0, duration_seconds=3.0)

        group = tl.group_clips_across_tracks(
            [c0.id, c1.id], target_track_index=t0.index, group_name='MyGroup',
        )

        assert isinstance(group, Group)
        assert group.ident == 'MyGroup'

    def test_clips_removed_from_source_tracks(self, project):
        """Source tracks lose their clips after grouping."""
        tl = project.timeline
        t0 = tl.add_track('A')
        t1 = tl.add_track('B')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)
        c1 = t1.add_audio(2, start_seconds=0.0, duration_seconds=1.0)

        tl.group_clips_across_tracks([c0.id, c1.id], t0.index)

        # Original clips gone from source tracks (only the Group remains on t0)
        source_a = tl.tracks[t0.index]
        source_b = tl.tracks[t1.index]
        original_ids = {c0.id, c1.id}
        assert not any(c.id in original_ids for c in source_a.clips if not isinstance(c, Group))
        assert list(source_b.clips) == []

    def test_empty_tracks_preserved(self, project):
        """Source tracks are NOT removed even when emptied."""
        tl = project.timeline
        t0 = tl.add_track('Keep')
        t1 = tl.add_track('Target')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)

        track_count_before = tl.track_count
        tl.group_clips_across_tracks([c0.id], t1.index)

        assert tl.track_count == track_count_before

    def test_internal_tracks_per_source_track(self, project):
        """Each source track becomes one internal track in the Group."""
        tl = project.timeline
        t0 = tl.add_track('V')
        t1 = tl.add_track('A')
        t2 = tl.add_track('Target')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)
        c1 = t1.add_audio(2, start_seconds=0.0, duration_seconds=1.0)

        group = tl.group_clips_across_tracks([c0.id, c1.id], t2.index)

        # Verify each internal track has the expected clip type
        track_types = [group.tracks[i].clips[0].clip_type for i in range(len(group.tracks))]
        assert set(track_types) == {'VMFile', 'AMFile'}

    def test_clip_starts_adjusted_to_group_relative(self, project):
        """Internal clip starts are relative to the Group's start."""
        tl = project.timeline
        t0 = tl.add_track('V')
        t1 = tl.add_track('A')
        # Clip at 2s and clip at 5s → group starts at 2s
        c0 = t0.add_video(1, start_seconds=2.0, duration_seconds=1.0)
        c1 = t1.add_audio(2, start_seconds=5.0, duration_seconds=1.0)

        group = tl.group_clips_across_tracks([c0.id, c1.id], t0.index)

        # Group should start at 2s
        assert abs(group.start_seconds - 2.0) < 0.01
        # Internal clip from t0 should start at 0 (2s - 2s)
        internal_clip_0 = group.tracks[0].clips[0]
        assert internal_clip_0.start == 0
        # Internal clip from t1 should start at 3s (5s - 2s)
        internal_clip_1 = group.tracks[1].clips[0]
        expected_offset = seconds_to_ticks(3.0)
        assert abs(internal_clip_1.start - expected_offset) < 100

    def test_group_duration_spans_all_clips(self, project):
        """Group duration covers from earliest start to latest end."""
        tl = project.timeline
        t0 = tl.add_track('V')
        t1 = tl.add_track('A')
        c0 = t0.add_video(1, start_seconds=1.0, duration_seconds=2.0)  # ends at 3s
        c1 = t1.add_audio(2, start_seconds=2.0, duration_seconds=4.0)  # ends at 6s

        group = tl.group_clips_across_tracks([c0.id, c1.id], t0.index)

        # Duration should be 6s - 1s = 5s
        assert abs(group.duration_seconds - 5.0) < 0.01

    def test_clips_get_new_ids(self, project):
        """Internal clips receive new IDs (not the originals)."""
        tl = project.timeline
        t0 = tl.add_track('V')
        t1 = tl.add_track('A')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)
        c1 = t1.add_audio(2, start_seconds=0.0, duration_seconds=1.0)
        original_ids = {c0.id, c1.id}

        group = tl.group_clips_across_tracks([c0.id, c1.id], t0.index)

        internal_ids = {c.id for gt in group.tracks for c in gt.clips}
        assert internal_ids.isdisjoint(original_ids)

    def test_internal_track_keys(self, project):
        """Internal tracks have the required Camtasia keys."""
        tl = project.timeline
        t0 = tl.add_track('V')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)

        group = tl.group_clips_across_tracks([c0.id], t0.index)

        required_keys = {
            'audioMuted', 'ident', 'magnetic', 'matte',
            'medias', 'metadata', 'solo', 'trackIndex', 'videoHidden',
        }
        for gt in group.tracks:
            assert required_keys.issubset(gt._data.keys())

    def test_missing_clip_raises(self, project):
        """KeyError raised when a clip ID doesn't exist."""
        tl = project.timeline
        t0 = tl.add_track('V')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)

        with pytest.raises(KeyError, match='Clips not found'):
            tl.group_clips_across_tracks([c0.id, 99999], t0.index)

    def test_transitions_cascade_removed(self, project):
        """Transitions referencing grouped clips are removed."""
        tl = project.timeline
        t0 = tl.add_track('V')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)
        c1 = t0.add_video(2, start_seconds=1.0, duration_seconds=1.0)
        # Manually inject a transition referencing c0
        t0._data.setdefault('transitions', []).append({
            'leftMedia': c0.id, 'rightMedia': c1.id,
        })

        tl.group_clips_across_tracks([c0.id], t0.index)

        # Transition referencing c0 should be gone
        remaining = t0._data.get('transitions', [])
        assert not any(
            t.get('leftMedia') == c0.id or t.get('rightMedia') == c0.id
            for t in remaining
        )

    def test_group_placed_on_target_track(self, project):
        """The Group clip appears on the specified target track."""
        tl = project.timeline
        t0 = tl.add_track('Source')
        t1 = tl.add_track('Target')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)

        tl.group_clips_across_tracks([c0.id], t1.index)

        target = tl.tracks[t1.index]
        groups = [c for c in target.clips if isinstance(c, Group)]
        assert [type(g).__name__ for g in groups] == ['Group']

    def test_single_clip_grouping(self, project):
        """Grouping a single clip works (one internal track, one clip)."""
        tl = project.timeline
        t0 = tl.add_track('V')
        c0 = t0.add_video(1, start_seconds=3.0, duration_seconds=2.0)

        group = tl.group_clips_across_tracks([c0.id], t0.index)

        assert [c.clip_type for c in group.tracks[0].clips] == ['VMFile']
        assert abs(group.start_seconds - 3.0) < 0.01
        assert abs(group.duration_seconds - 2.0) < 0.01

    def test_multiple_clips_same_track(self, project):
        """Multiple clips from the same track go into one internal track."""
        tl = project.timeline
        t0 = tl.add_track('V')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)
        c1 = t0.add_video(2, start_seconds=2.0, duration_seconds=1.0)

        group = tl.group_clips_across_tracks([c0.id, c1.id], t0.index)

        internal_clips = list(group.tracks[0].clips)
        assert [c.clip_type for c in internal_clips] == ['VMFile', 'VMFile']


class TestProjectGroupClipsAcrossTracks:
    """Project.group_clips_across_tracks convenience wrapper."""

    def test_by_track_name(self, project):
        """Project wrapper resolves track by name."""
        tl = project.timeline
        t0 = tl.add_track('Source')
        t1 = tl.add_track('Target')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)

        group = project.group_clips_across_tracks(
            [c0.id], 'Target', group_name='Named',
        )

        assert isinstance(group, Group)
        assert group.ident == 'Named'

    def test_missing_target_track_raises(self, project):
        """KeyError raised when target track name doesn't exist."""
        tl = project.timeline
        t0 = tl.add_track('Source')
        c0 = t0.add_video(1, start_seconds=0.0, duration_seconds=1.0)

        with pytest.raises(KeyError, match='Target track not found'):
            project.group_clips_across_tracks([c0.id], 'NoSuchTrack')
