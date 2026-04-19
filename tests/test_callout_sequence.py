"""Tests for Project.add_callout_sequence()."""
from __future__ import annotations


class TestAddCalloutSequenceBasic:
    def test_returns_correct_count(self, project):
        entries = [(0.0, 3.0, 'A'), (5.0, 2.0, 'B'), (10.0, 4.0, 'C')]
        result = project.add_callout_sequence(entries)
        assert len(result) == 3
        assert [c.text for c in result] == ['A', 'B', 'C']

    def test_clips_have_correct_text(self, project):
        entries = [(0.0, 3.0, 'First'), (5.0, 2.0, 'Second')]
        result = project.add_callout_sequence(entries)
        assert result[0].text == 'First'
        assert result[1].text == 'Second'

    def test_clips_placed_on_named_track(self, project):
        entries = [(0.0, 2.0, 'Hello')]
        project.add_callout_sequence(entries, track_name='MyCallouts')
        track = project.timeline.find_track_by_name('MyCallouts')
        assert track is not None
        assert len(track) == 1
        assert next(iter(track.clips)).text == 'Hello'

    def test_default_track_name(self, project):
        entries = [(0.0, 2.0, 'Hello')]
        project.add_callout_sequence(entries)
        track = project.timeline.find_track_by_name('Callouts')
        assert track is not None


class TestAddCalloutSequenceEmpty:
    def test_empty_entries_returns_empty_list(self, project):
        result = project.add_callout_sequence([])
        assert result == []


class TestAddCalloutSequenceFades:
    def test_fades_applied_by_default(self, project):
        entries = [(0.0, 5.0, 'Faded')]
        result = project.add_callout_sequence(entries)
        clip = result[0]
        # fade_in/fade_out were called; verify effects exist
        assert clip._data.get("parameters", {}).get("opacity") is not None

    def test_no_fades_when_zero(self, project):
        entries = [(0.0, 5.0, 'NoFade')]
        result = project.add_callout_sequence(entries, fade_seconds=0.0)
        clip = result[0]
        assert clip.effect_count == 0


class TestAddCalloutSequenceFontSize:
    def test_custom_font_size(self, project):
        entries = [(0.0, 3.0, 'Big')]
        result = project.add_callout_sequence(entries, font_size=48.0)
        assert result[0].font['size'] == 48.0

    def test_default_font_size(self, project):
        entries = [(0.0, 3.0, 'Default')]
        result = project.add_callout_sequence(entries)
        assert result[0].font['size'] == 24.0


class TestAddCalloutSequenceMultiple:
    def test_multiple_entries_all_on_same_track(self, project):
        entries = [(0.0, 1.0, 'A'), (2.0, 1.0, 'B'), (4.0, 1.0, 'C')]
        project.add_callout_sequence(entries, track_name='Annotations')
        track = project.timeline.find_track_by_name('Annotations')
        assert len(track) == 3
        texts = [c.text for c in track.clips]
        assert texts == ['A', 'B', 'C']
