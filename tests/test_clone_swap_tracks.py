"""Tests for Project.clone_track() and Project.swap_tracks()."""

import pytest


def test_clone_track_creates_new_track_with_name(project):
    """clone_track duplicates a track and assigns the new name."""
    # Create a source track with a clip
    track = project.timeline.get_or_create_track('Source')
    original_count = project.track_count

    cloned = project.clone_track('Source', 'Cloned')

    assert cloned.name == 'Cloned'
    assert project.track_count == original_count + 1


def test_clone_track_raises_on_missing_source(project):
    """clone_track raises KeyError for a non-existent track name."""
    with pytest.raises(KeyError, match='Track not found: NoSuchTrack'):
        project.clone_track('NoSuchTrack', 'Copy')


def test_swap_tracks_swaps_indices(project):
    """swap_tracks exchanges the trackIndex values of two tracks."""
    track_a = project.timeline.get_or_create_track('TrackA')
    track_b = project.timeline.get_or_create_track('TrackB')
    idx_a = track_a.index
    idx_b = track_b.index

    project.swap_tracks('TrackA', 'TrackB')

    assert track_a.index == idx_b
    assert track_b.index == idx_a


def test_swap_tracks_raises_on_missing_first(project):
    """swap_tracks raises KeyError when the first track is missing."""
    project.timeline.get_or_create_track('Exists')
    with pytest.raises(KeyError, match='Track not found: Ghost'):
        project.swap_tracks('Ghost', 'Exists')


def test_swap_tracks_raises_on_missing_second(project):
    """swap_tracks raises KeyError when the second track is missing."""
    project.timeline.get_or_create_track('Exists')
    with pytest.raises(KeyError, match='Track not found: Ghost'):
        project.swap_tracks('Exists', 'Ghost')


def test_swap_tracks_same_track_is_noop(project):
    """Swapping a track with itself leaves the index unchanged."""
    track = project.timeline.get_or_create_track('Solo')
    original_idx = track.index

    project.swap_tracks('Solo', 'Solo')

    assert track.index == original_idx
