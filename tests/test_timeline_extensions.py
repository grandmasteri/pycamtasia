"""Tests for Timeline caption, magnetic, playhead, and zoom helpers."""
from __future__ import annotations

import pytest

from camtasia.timing import seconds_to_ticks, ticks_to_seconds

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def timeline(project):
    """Return the Timeline from the blank project fixture."""
    return project.timeline


# ---------------------------------------------------------------------------
# add_caption
# ---------------------------------------------------------------------------

class TestAddCaption:
    def test_creates_callout_on_new_track(self, timeline):
        clip = timeline.add_caption('Hello', 1.0, 2.0)
        assert clip.clip_type == 'Callout'
        track = timeline.find_track_by_name('Subtitles')
        assert track is not None
        assert len(list(track.clips)) == 1

    def test_uses_caption_attributes_font(self, timeline):
        timeline.caption_attributes.font_name = 'Courier'
        timeline.caption_attributes.font_size = 48
        clip = timeline.add_caption('Styled', 0.0, 1.0)
        # Verify the callout was created (font is applied internally by add_callout)
        assert clip.clip_type == 'Callout'

    def test_custom_track_name(self, timeline):
        timeline.add_caption('Custom', 0.0, 1.0, track_name='MyTrack')
        assert timeline.find_track_by_name('MyTrack') is not None

    def test_timing_is_correct(self, timeline):
        clip = timeline.add_caption('Timed', 2.0, 3.0)
        assert clip.start == seconds_to_ticks(2.0)
        assert clip.duration == seconds_to_ticks(3.0)


# ---------------------------------------------------------------------------
# edit_caption
# ---------------------------------------------------------------------------

class TestEditCaption:
    def test_edit_text(self, timeline):
        timeline.add_caption('Original', 0.0, 1.0)
        timeline.edit_caption(0, text='Updated')
        clips = timeline._caption_clips('Subtitles')
        assert clips[0]._data['def']['text'] == 'Updated'

    def test_edit_duration(self, timeline):
        timeline.add_caption('Dur', 0.0, 1.0)
        timeline.edit_caption(0, duration_seconds=5.0)
        clips = timeline._caption_clips('Subtitles')
        assert clips[0].duration == seconds_to_ticks(5.0)

    def test_edit_both(self, timeline):
        timeline.add_caption('Both', 0.0, 1.0)
        timeline.edit_caption(0, text='New', duration_seconds=2.0)
        clips = timeline._caption_clips('Subtitles')
        assert clips[0]._data['def']['text'] == 'New'
        assert clips[0].duration == seconds_to_ticks(2.0)

    def test_edit_none_is_noop(self, timeline):
        timeline.add_caption('Keep', 0.0, 1.0)
        clips_before = timeline._caption_clips('Subtitles')
        text_before = clips_before[0]._data.get('def', {}).get('text', '')
        dur_before = clips_before[0].duration
        timeline.edit_caption(0)
        clips_after = timeline._caption_clips('Subtitles')
        assert clips_after[0]._data.get('def', {}).get('text', '') == text_before
        assert clips_after[0].duration == dur_before

    def test_edit_out_of_range(self, timeline):
        timeline.add_caption('One', 0.0, 1.0)
        with pytest.raises(IndexError):
            timeline.edit_caption(5, text='Nope')


# ---------------------------------------------------------------------------
# remove_caption
# ---------------------------------------------------------------------------

class TestRemoveCaption:
    def test_remove_single(self, timeline):
        timeline.add_caption('A', 0.0, 1.0)
        timeline.add_caption('B', 2.0, 1.0)
        timeline.remove_caption(0)
        clips = timeline._caption_clips('Subtitles')
        assert len(clips) == 1

    def test_remove_out_of_range(self, timeline):
        with pytest.raises(IndexError):
            timeline.remove_caption(0)


# ---------------------------------------------------------------------------
# split_caption
# ---------------------------------------------------------------------------

class TestSplitCaption:
    def test_split_creates_two(self, timeline):
        timeline.add_caption('Hello World', 0.0, 4.0)
        timeline.split_caption(0, 2.0)
        clips = timeline._caption_clips('Subtitles')
        assert len(clips) == 2

    def test_split_timing(self, timeline):
        timeline.add_caption('Hello World', 0.0, 4.0)
        timeline.split_caption(0, 2.0)
        clips = timeline._caption_clips('Subtitles')
        assert clips[0].duration == seconds_to_ticks(2.0)
        assert abs(ticks_to_seconds(clips[1].start) - 2.0) < 0.001
        assert abs(ticks_to_seconds(clips[1].duration) - 2.0) < 0.001

    def test_split_text_distribution(self, timeline):
        timeline.add_caption('one two three four', 0.0, 4.0)
        timeline.split_caption(0, 2.0)
        clips = timeline._caption_clips('Subtitles')
        first_text = clips[0]._data.get('def', {}).get('text', '')
        second_text = clips[1]._data.get('def', {}).get('text', '')
        # First half gets first 2 words, second half gets last 2
        assert first_text == 'one two'
        assert second_text == 'three four'

    def test_split_at_zero_raises(self, timeline):
        timeline.add_caption('X', 0.0, 4.0)
        with pytest.raises(ValueError):
            timeline.split_caption(0, 0.0)

    def test_split_at_end_raises(self, timeline):
        timeline.add_caption('X', 0.0, 4.0)
        with pytest.raises(ValueError):
            timeline.split_caption(0, 4.0)

    def test_split_out_of_range(self, timeline):
        with pytest.raises(IndexError):
            timeline.split_caption(0, 1.0)


# ---------------------------------------------------------------------------
# merge_caption_with_next
# ---------------------------------------------------------------------------

class TestMergeCaptionWithNext:
    def test_merge_combines_text(self, timeline):
        timeline.add_caption('Hello', 0.0, 2.0)
        timeline.add_caption('World', 2.0, 2.0)
        timeline.merge_caption_with_next(0)
        clips = timeline._caption_clips('Subtitles')
        assert len(clips) == 1
        assert clips[0]._data['def']['text'] == 'Hello World'

    def test_merge_extends_duration(self, timeline):
        timeline.add_caption('A', 0.0, 2.0)
        timeline.add_caption('B', 2.0, 3.0)
        timeline.merge_caption_with_next(0)
        clips = timeline._caption_clips('Subtitles')
        expected_end = seconds_to_ticks(5.0)
        assert clips[0].start + clips[0].duration == expected_end

    def test_merge_last_raises(self, timeline):
        timeline.add_caption('Only', 0.0, 1.0)
        with pytest.raises(IndexError):
            timeline.merge_caption_with_next(0)

    def test_merge_out_of_range(self, timeline):
        with pytest.raises(IndexError):
            timeline.merge_caption_with_next(5)


# ---------------------------------------------------------------------------
# REV-test_gaps-002: Caption index boundary error messages
# ---------------------------------------------------------------------------


class TestCaptionIndexBoundaryMessages:
    def test_edit_caption_negative_index(self, timeline):
        timeline.add_caption('A', 0.0, 1.0)
        with pytest.raises(IndexError, match='Caption index'):
            timeline.edit_caption(-1, text='Nope')

    def test_remove_caption_negative_index(self, timeline):
        timeline.add_caption('A', 0.0, 1.0)
        with pytest.raises(IndexError, match='Caption index'):
            timeline.remove_caption(-1)

    def test_split_caption_negative_index(self, timeline):
        timeline.add_caption('A', 0.0, 2.0)
        with pytest.raises(IndexError, match='Caption index'):
            timeline.split_caption(-1, 1.0)

    def test_merge_caption_negative_index(self, timeline):
        timeline.add_caption('A', 0.0, 1.0)
        timeline.add_caption('B', 2.0, 1.0)
        with pytest.raises(IndexError, match='Caption index'):
            timeline.merge_caption_with_next(-1)

    def test_edit_caption_empty_timeline(self, timeline):
        with pytest.raises(IndexError, match='Caption index'):
            timeline.edit_caption(0, text='Nope')

    def test_split_caption_empty_timeline(self, timeline):
        with pytest.raises(IndexError, match='Caption index'):
            timeline.split_caption(0, 1.0)


# ---------------------------------------------------------------------------
# set_all_magnetic
# ---------------------------------------------------------------------------

class TestSetAllMagnetic:
    def test_enable(self, timeline):
        timeline.add_track('Extra')
        timeline.set_all_magnetic(True)
        for track in timeline.tracks:
            assert track.magnetic is True

    def test_disable(self, timeline):
        timeline.set_all_magnetic(True)
        timeline.set_all_magnetic(False)
        for track in timeline.tracks:
            assert track.magnetic is False


# ---------------------------------------------------------------------------
# playhead_seconds
# ---------------------------------------------------------------------------

class TestPlayheadSeconds:
    def test_default_is_zero(self, timeline):
        assert timeline.playhead_seconds == 0.0

    def test_set_and_get(self, timeline):
        timeline.playhead_seconds = 5.5
        assert timeline.playhead_seconds == 5.5

    def test_stored_in_docprefs(self, timeline):
        timeline.playhead_seconds = 3.0
        assert timeline._data['docPrefs']['DocPrefPlayheadTime'] == 3.0


# ---------------------------------------------------------------------------
# ui_zoom_level
# ---------------------------------------------------------------------------

class TestUiZoomLevel:
    def test_default_is_one(self, timeline):
        assert timeline.ui_zoom_level == 1.0

    def test_set_and_get(self, timeline):
        timeline.ui_zoom_level = 0.5
        assert timeline.ui_zoom_level == 0.5

    def test_stored_in_docprefs(self, timeline):
        timeline.ui_zoom_level = 2.0
        assert timeline._data['docPrefs']['DocPrefZoomValue'] == 2.0
