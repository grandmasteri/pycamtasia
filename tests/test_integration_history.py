"""Integration tests for pycamtasia history (undo/redo).

Each test mutates a project, exercises undo/redo, then opens in Camtasia
to verify the resulting file is valid.
"""
from __future__ import annotations

from camtasia.operations.layout import ripple_insert
from camtasia.timing import seconds_to_ticks
from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


class TestUndoRedo:
    """Core undo/redo scenarios opened in Camtasia."""

    def test_simple_undo_opens(self, project):
        with project.track_changes("add track"):
            project.timeline.add_track("Audio")
        project.undo()
        open_in_camtasia(project)

    def test_multiple_undo_opens(self, project):
        for i in range(5):
            with project.track_changes(f"add track {i}"):
                project.timeline.add_track(f"Track {i}")
        for _ in range(5):
            project.undo()
        open_in_camtasia(project)

    def test_undo_then_redo_opens(self, project):
        with project.track_changes("add track"):
            project.timeline.add_track("Redo Target")
        project.undo()
        project.redo()
        open_in_camtasia(project)

    def test_undo_redo_oscillation_stress(self, project):
        with project.track_changes("add track"):
            project.timeline.add_track("Oscillation")
        for _ in range(50):
            project.undo()
            project.redo()
        open_in_camtasia(project)

    def test_undo_save_reload_roundtrip(self, project, tmp_path):
        with project.track_changes("add track"):
            project.timeline.add_track("Will Be Undone")
        project.undo()
        project.save()

        from camtasia.project import load_project
        reloaded = load_project(project.file_path)
        # The undone track should not be present after reload
        track_names = [t.name for t in reloaded.timeline.tracks]
        assert "Will Be Undone" not in track_names
        open_in_camtasia(reloaded)

    def test_undo_across_operation_types(self, project):
        # Add a track with two clips so we can add a transition
        with project.track_changes("add track"):
            track = project.timeline.add_track("Video")

        with project.track_changes("add clip A"):
            track = list(project.timeline.tracks)[-1]
            clip_a = track.add_clip("Callout", None, start=0, duration=seconds_to_ticks(3))

        with project.track_changes("add clip B"):
            track = list(project.timeline.tracks)[-1]
            clip_b = track.add_clip("Callout", None, start=seconds_to_ticks(3), duration=seconds_to_ticks(3))

        with project.track_changes("add transition"):
            track = list(project.timeline.tracks)[-1]
            clips = list(track.clips)
            track.add_transition("FadeThroughBlack", clips[0], clips[1], duration_seconds=0.5)

        with project.track_changes("add effect"):
            track = list(project.timeline.tracks)[-1]
            clip = list(track.clips)[0]
            clip.add_drop_shadow()

        with project.track_changes("remove clip"):
            track = list(project.timeline.tracks)[-1]
            clips = list(track.clips)
            track.remove_clip(clips[-1].id)

        # Undo all 5 operations
        for _ in range(5):
            project.undo()

        open_in_camtasia(project)

    def test_undo_past_start_does_not_crash(self, project):
        with project.track_changes("single change"):
            project.timeline.add_track("Only One")
        project.undo()
        # Attempting to undo with nothing left should raise but not corrupt
        try:
            project.undo()
        except IndexError:
            pass
        open_in_camtasia(project)

    def test_redo_past_end_does_not_crash(self, project):
        with project.track_changes("change"):
            project.timeline.add_track("Redo Edge")
        project.undo()
        project.redo()
        # Attempting to redo with nothing left should raise but not corrupt
        try:
            project.redo()
        except IndexError:
            pass
        open_in_camtasia(project)

    def test_ripple_insert_undo_restores_state(self, project):
        with project.track_changes("add track and clips"):
            track = project.timeline.add_track("Ripple")
            track.add_clip("Callout", None, start=0, duration=seconds_to_ticks(2))
            track.add_clip("Callout", None, start=seconds_to_ticks(2), duration=seconds_to_ticks(2))

        # Capture clip positions before ripple
        track = list(project.timeline.tracks)[-1]
        positions_before = [c.start for c in track.clips]

        with project.track_changes("ripple insert"):
            track = list(project.timeline.tracks)[-1]
            ripple_insert(track, position_seconds=1.0, duration_seconds=3.0)

        project.undo()  # undo the ripple

        # Verify positions restored
        track = list(project.timeline.tracks)[-1]
        positions_after = [c.start for c in track.clips]
        assert positions_before == positions_after

        open_in_camtasia(project)
