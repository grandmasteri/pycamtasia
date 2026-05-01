"""REV-test_gaps-010: No end-to-end save-reload-validate roundtrip test.

While individual save tests exist, there's no test that:
1. Creates a complex project with multiple features
2. Saves it
3. Reloads from disk
4. Validates the reloaded project matches the original
5. Runs validate() on the reloaded project

This is an integration gap — individual features are tested but the
full roundtrip with multiple features combined is not.
"""
import json

from camtasia import new_project
from camtasia.timing import seconds_to_ticks


def test_complex_project_save_reload_roundtrip(tmp_path):
    """A project with multiple features should survive save/reload."""
    proj_dir = tmp_path / "roundtrip.cmproj"
    proj = new_project(str(proj_dir))

    # Add tracks, clips, markers, captions
    track = proj.timeline.add_track("video")
    proj.media_bin.import_media_by_id(1, "clip.mp4", duration_ticks=seconds_to_ticks(30))
    track.add_clip("VMFile", 1, start_seconds=0, duration_seconds=30)

    audio_track = proj.timeline.add_track("audio")
    proj.media_bin.import_media_by_id(2, "narration.wav", duration_ticks=seconds_to_ticks(30))
    audio_track.add_clip("AMFile", 2, start_seconds=0, duration_seconds=30)

    proj.timeline.markers.add("Chapter 1", seconds_to_ticks(0))
    proj.timeline.markers.add("Chapter 2", seconds_to_ticks(15))

    proj.save()

    # Reload and validate
    from camtasia.project import Project
    reloaded = Project(proj_dir)

    assert len(list(reloaded.timeline.tracks)) >= 2
    assert len(list(reloaded.media_bin)) >= 2
    assert len(list(reloaded.timeline.markers)) == 2

    issues = reloaded.validate()
    errors = [i for i in issues if i.severity == 'error']
    assert not errors, f"Validation errors after roundtrip: {errors}"
