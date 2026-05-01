"""Integration tests for pycamtasia Groups (clip groups and group tracks).

Each test creates a project with group-related structures, then opens it
in Camtasia to verify round-trip correctness via the validator contract.
"""
from __future__ import annotations

from tests.integration_helpers import INTEGRATION_MARKERS, open_in_camtasia

pytestmark = INTEGRATION_MARKERS


class TestGroupBasics:
    """Basic group creation and manipulation."""

    def test_group_from_three_callouts(self, project):
        """Create 3 callout clips and group them."""
        track = project.timeline.add_track('Group Test')
        c1 = track.add_callout('One', 0, 3)
        c2 = track.add_callout('Two', 3, 3)
        c3 = track.add_callout('Three', 6, 3)
        track.group_clips([c1.id, c2.id, c3.id])
        open_in_camtasia(project)

    def test_nested_group(self, project):
        """Group within a group (nested groups)."""
        track = project.timeline.add_track('Nested')
        c1 = track.add_callout('A', 0, 2)
        c2 = track.add_callout('B', 2, 2)
        c3 = track.add_callout('C', 4, 2)
        # Group first two, then group that group with the third
        inner_group = track.group_clips([c1.id, c2.id])
        track.group_clips([inner_group.id, c3.id])
        open_in_camtasia(project)

    def test_empty_group(self, project):
        """An empty group (no internal clips)."""
        track = project.timeline.add_track('Empty Group')
        track.add_group(start_seconds=0, duration_seconds=5)
        open_in_camtasia(project)


class TestGroupTrack:
    """GroupTrack with multiple internal tracks."""

    def test_group_with_multiple_internal_tracks(self, project):
        """Group containing clips on multiple internal tracks."""
        track = project.timeline.add_track('Multi-track Group')
        group = track.add_group(start_seconds=0, duration_seconds=10)

        nid = project.next_available_id
        t0 = group.add_internal_track()
        t0.add_clip('Callout', None, 0, 150000, next_id=nid, **{
            'def': {'type': 'text', 'word': 'Track0'},
            'attributes': {'ident': '', 'autoRotateText': True},
        })

        t1 = group.add_internal_track()
        t1.add_clip('Callout', None, 0, 150000, next_id=nid + 1, **{
            'def': {'type': 'text', 'word': 'Track1'},
            'attributes': {'ident': '', 'autoRotateText': True},
        })

        open_in_camtasia(project)


class TestGroupWithTransition:
    """Group + transition on group boundary."""

    def test_transition_between_group_and_clip(self, project):
        """Transition between a group and an adjacent clip."""
        track = project.timeline.add_track('Transition')
        c1 = track.add_callout('Before', 0, 3)
        c2 = track.add_callout('Inside1', 3, 3)
        c3 = track.add_callout('Inside2', 6, 3)
        group = track.group_clips([c2.id, c3.id])
        # Add transition between the standalone clip and the group
        track.add_fade_through_black(c1, group, duration_seconds=0.5)
        open_in_camtasia(project)


class TestGroupWithEffect:
    """Effect applied to the whole group."""

    def test_drop_shadow_on_group(self, project):
        """Apply a drop shadow effect to an entire group."""
        track = project.timeline.add_track('Effect')
        c1 = track.add_callout('X', 0, 3)
        c2 = track.add_callout('Y', 3, 3)
        group = track.group_clips([c1.id, c2.id])
        group.add_drop_shadow(offset=8, blur=12, opacity=0.6)
        open_in_camtasia(project)


class TestGroupWithBehavior:
    """Behavior on a clip inside a group."""

    def test_behavior_on_grouped_callout(self, project):
        """Add a behavior to a callout, then group it."""
        track = project.timeline.add_track('Behavior')
        c1 = track.add_callout('Animated', 0, 4)
        c1.add_behavior('reveal')
        c2 = track.add_callout('Static', 4, 4)
        track.group_clips([c1.id, c2.id])
        open_in_camtasia(project)


class TestGroupSplit:
    """Split a clip inside a group."""

    def test_split_clip_in_group(self, project):
        """Split a callout inside a group at the midpoint."""
        track = project.timeline.add_track('Split')
        c1 = track.add_callout('Left', 0, 4)
        c2 = track.add_callout('Right', 4, 4)
        group = track.group_clips([c1.id, c2.id])
        # Split the group itself at 4 seconds (midpoint)
        track.split_clip(group.id, split_at_seconds=4.0)
        open_in_camtasia(project)


class TestGroupRemoveClip:
    """Remove a clip from inside a group."""

    def test_remove_internal_clip(self, project):
        """Remove one clip from a group, leaving the rest."""
        track = project.timeline.add_track('Remove')
        c1 = track.add_callout('Keep', 0, 3)
        c2 = track.add_callout('Remove', 3, 3)
        c3 = track.add_callout('Keep2', 6, 3)
        group = track.group_clips([c1.id, c2.id, c3.id])
        # Remove the middle clip from the group's internal track
        internal_clips = group.all_internal_clips
        group.remove_internal_clip(internal_clips[1].id)
        open_in_camtasia(project)


class TestGroupMultipleTracks:
    """Group spanning multiple timeline tracks."""

    def test_groups_on_separate_tracks(self, project):
        """Groups placed on different timeline tracks simultaneously."""
        t1 = project.timeline.add_track('Track A')
        t2 = project.timeline.add_track('Track B')

        a1 = t1.add_callout('A1', 0, 5)
        a2 = t1.add_callout('A2', 5, 5)
        t1.group_clips([a1.id, a2.id])

        b1 = t2.add_callout('B1', 0, 5)
        b2 = t2.add_callout('B2', 5, 5)
        t2.group_clips([b1.id, b2.id])

        open_in_camtasia(project)
