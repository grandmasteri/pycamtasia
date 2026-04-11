from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.builders.timeline_builder import TimelineBuilder

FIXTURES = Path(__file__).parent / 'fixtures'


class TestTimelineBuilder:
    def test_initial_cursor_is_zero(self, project):
        builder = TimelineBuilder(project)
        assert builder.cursor == 0.0

    def test_advance_moves_cursor(self, project):
        builder = TimelineBuilder(project)
        builder.advance(3.5)
        assert builder.cursor == 3.5

    def test_seek_sets_cursor(self, project):
        builder = TimelineBuilder(project)
        builder.advance(10.0)
        builder.seek(2.0)
        assert builder.cursor == 2.0

    def test_seek_negative_raises(self, project):
        builder = TimelineBuilder(project)
        with pytest.raises(ValueError, match='non-negative'):
            builder.seek(-1.0)

    def test_add_pause_advances_cursor(self, project):
        builder = TimelineBuilder(project)
        builder.add_pause(4.0)
        assert builder.cursor == 4.0

    def test_add_audio_places_clip_and_advances(self, project):
        builder = TimelineBuilder(project)
        clip = builder.add_audio(FIXTURES / 'empty.wav', duration=3.0)
        assert clip is not None
        assert builder.cursor == 3.0

    def test_add_image_places_clip_no_advance(self, project):
        builder = TimelineBuilder(project)
        builder.advance(2.0)
        clip = builder.add_image(FIXTURES / 'empty.wav', duration=5.0)
        assert clip is not None
        assert builder.cursor == 2.0

    def test_add_title_places_clip_no_advance(self, project):
        builder = TimelineBuilder(project)
        builder.advance(1.0)
        clip = builder.add_title('Hello World', duration=4.0)
        assert clip is not None
        assert builder.cursor == 1.0

    def test_chaining_works(self, project):
        builder = TimelineBuilder(project)
        result = builder.advance(1.0).add_pause(2.0).seek(5.0)
        assert result is builder
        assert builder.cursor == 5.0
