"""Tests for Track.add_placeholder and PlaceholderMedia.title property."""
from __future__ import annotations

from camtasia.timeline.clips.placeholder import PlaceholderMedia
from camtasia.timing import seconds_to_ticks


class TestAddPlaceholder:
    def test_returns_placeholder_media(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_placeholder(0.0, 5.0)
        assert isinstance(clip, PlaceholderMedia)

    def test_clip_type(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_placeholder(0.0, 5.0)
        assert clip.clip_type == 'PlaceholderMedia'

    def test_start_and_duration(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_placeholder(2.0, 3.0)
        assert clip.start == seconds_to_ticks(2.0)
        assert clip.duration == seconds_to_ticks(3.0)

    def test_title_and_note(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_placeholder(0.0, 5.0, title='My Title', note='My Note')
        assert clip.title == 'My Title'
        assert clip.subtitle == 'My Note'

    def test_default_title_and_note_empty(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_placeholder(0.0, 5.0)
        assert clip.title == ''
        assert clip.subtitle == ''

    def test_adds_to_track(self, project):
        track = project.timeline.get_or_create_track('Video')
        initial = len(track)
        track.add_placeholder(0.0, 5.0)
        assert len(track) == initial + 1


class TestPlaceholderTitle:
    def test_getter_from_metadata(self):
        clip = PlaceholderMedia({
            '_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
            'metadata': {'placeHolderTitle': 'hello'},
        })
        assert clip.title == 'hello'

    def test_setter(self):
        clip = PlaceholderMedia({
            '_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
        })
        clip.title = 'new title'
        assert clip.title == 'new title'
        assert clip._data['metadata']['placeHolderTitle'] == 'new title'

    def test_missing_metadata_returns_empty(self):
        clip = PlaceholderMedia({
            '_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
        })
        assert clip.title == ''

    def test_none_value_returns_empty(self):
        clip = PlaceholderMedia({
            '_type': 'PlaceholderMedia', 'id': 1, 'start': 0, 'duration': 100,
            'metadata': {'placeHolderTitle': None},
        })
        assert clip.title == ''
