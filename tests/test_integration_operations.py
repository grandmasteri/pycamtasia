"""Integration tests for the pycamtasia operations module.

Each test creates a project with clips, applies an operation, then
opens in Camtasia to verify the result is valid.
"""
from __future__ import annotations

from pathlib import Path
import shutil

from camtasia import operations
from camtasia.project import load_project
from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS

FIXTURES = Path(__file__).parent / 'fixtures'


def _setup_track_with_clips(project, n=3, duration=2.0):
    """Import media and add n sequential audio clips to a new track."""
    media = project.import_media(FIXTURES / 'empty.wav')
    track = project.timeline.add_track('Audio')
    clips = []
    for i in range(n):
        c = track.add_audio(media.id, start_seconds=i * duration, duration_seconds=duration)
        clips.append(c)
    return track, clips, media


class TestRippleOperations:
    def test_ripple_insert_opens(self, project):
        track, clips, _ = _setup_track_with_clips(project)
        operations.ripple_insert(track, position_seconds=2.0, duration_seconds=1.0)
        open_in_camtasia(project)

    def test_ripple_delete_opens(self, project):
        track, clips, _ = _setup_track_with_clips(project)
        operations.ripple_delete(track, clip_id=clips[1].id)
        open_in_camtasia(project)

    def test_ripple_delete_range_opens(self, project):
        track, clips, _ = _setup_track_with_clips(project)
        operations.ripple_delete_range(track, start_seconds=1.0, end_seconds=3.0)
        open_in_camtasia(project)

    def test_ripple_extend_opens(self, project):
        track, clips, _ = _setup_track_with_clips(project)
        operations.ripple_extend(track, clip_id=clips[0].id, extend_seconds=1.5)
        open_in_camtasia(project)

    def test_ripple_move_opens(self, project):
        track, clips, _ = _setup_track_with_clips(project)
        operations.ripple_move(track, clip_id=clips[1].id, delta_seconds=1.0)
        open_in_camtasia(project)

    def test_ripple_move_multi_opens(self, project):
        track1, clips1, media = _setup_track_with_clips(project)
        track2 = project.timeline.add_track('Audio 2')
        c2a = track2.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        c2b = track2.add_audio(media.id, start_seconds=2.0, duration_seconds=2.0)
        operations.ripple_move_multi(
            tracks=[track1, track2],
            clip_ids_per_track=[[clips1[1].id], [c2b.id]],
            delta_seconds=0.5,
        )
        open_in_camtasia(project)


class TestSplitClip:
    def test_split_clip_opens(self, project):
        track, clips, _ = _setup_track_with_clips(project)
        track.split_clip(clip_id=clips[0].id, split_at_seconds=1.0)
        open_in_camtasia(project)


class TestMergeTracks:
    def test_merge_tracks_opens(self, project, tmp_path):
        # Create a second project to merge from
        src_dir = tmp_path / 'source.cmproj'
        shutil.copytree(project.file_path, src_dir)
        source = load_project(src_dir)
        media = source.import_media(FIXTURES / 'empty.wav')
        t = source.timeline.add_track('Merge Source')
        t.add_audio(media.id, start_seconds=0.0, duration_seconds=3.0)
        source.save()

        operations.merge_tracks(source, project, offset_seconds=5.0)
        open_in_camtasia(project)


class TestPackTrack:
    def test_pack_track_opens(self, project):
        media = project.import_media(FIXTURES / 'empty.wav')
        track = project.timeline.add_track('Gapped')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        track.add_audio(media.id, start_seconds=5.0, duration_seconds=2.0)
        track.add_audio(media.id, start_seconds=10.0, duration_seconds=2.0)
        operations.pack_track(track)
        open_in_camtasia(project)


class TestCleanupOperations:
    def test_remove_empty_tracks_opens(self, project):
        project.timeline.add_track('Empty 1')
        project.timeline.add_track('Empty 2')
        # Add one non-empty track
        media = project.import_media(FIXTURES / 'empty.wav')
        t = project.timeline.add_track('Has Clips')
        t.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        operations.remove_empty_tracks(project)
        open_in_camtasia(project)

    def test_remove_orphaned_media_opens(self, project):
        media = project.import_media(FIXTURES / 'empty.wav')
        media2 = project.import_media(FIXTURES / 'empty2.wav')
        track = project.timeline.add_track('Audio')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        # media2 is orphaned — not used by any clip
        removed = operations.remove_orphaned_media(project)
        assert media2.id in removed
        open_in_camtasia(project)

    def test_compact_project_opens(self, project):
        media = project.import_media(FIXTURES / 'empty.wav')
        project.import_media(FIXTURES / 'empty2.wav')  # orphaned
        project.timeline.add_track('Empty Track')
        track = project.timeline.add_track('Audio')
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        result = operations.compact_project(project)
        assert result['orphaned_media_removed'] >= 1
        assert result['empty_tracks_removed'] >= 1
        open_in_camtasia(project)


class TestAutoStitch:
    def test_auto_stitch_on_track_opens(self, project):
        media = project.import_media(FIXTURES / 'empty.wav')
        track = project.timeline.add_track('Stitch')
        # Add adjacent clips with same source — candidates for stitching
        track.add_audio(media.id, start_seconds=0.0, duration_seconds=2.0)
        track.add_audio(media.id, start_seconds=2.0, duration_seconds=2.0)
        track.add_audio(media.id, start_seconds=4.0, duration_seconds=2.0)
        operations.auto_stitch_on_track(track)
        open_in_camtasia(project)


class TestReplaceMediaSource:
    def test_replace_media_source_opens(self, project):
        media1 = project.import_media(FIXTURES / 'empty.wav')
        media2 = project.import_media(FIXTURES / 'empty2.wav')
        track = project.timeline.add_track('Audio')
        track.add_audio(media1.id, start_seconds=0.0, duration_seconds=2.0)
        track.add_audio(media1.id, start_seconds=2.0, duration_seconds=2.0)
        count = operations.replace_media_source(project._data, media1.id, media2.id)
        assert count == 2
        open_in_camtasia(project)


class TestCombinedOperations:
    def test_ripple_insert_then_delete_opens(self, project):
        track, clips, _ = _setup_track_with_clips(project, n=4, duration=2.0)
        # Insert gap at 2s, pushing clips forward
        operations.ripple_insert(track, position_seconds=2.0, duration_seconds=1.0)
        # Delete the first clip and close the gap
        operations.ripple_delete(track, clip_id=clips[0].id)
        open_in_camtasia(project)
