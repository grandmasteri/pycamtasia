"""Tests for Track selection/cut/copy/paste, exported frame, and ripple replace."""
from __future__ import annotations

import pytest

from camtasia.operations.layout import ripple_replace_in_group
from camtasia.timing import seconds_to_ticks


class TestSelection:
    def test_selection_initially_none(self, project):
        track = project.timeline.get_or_create_track('Video')
        assert track.selection is None

    def test_set_and_get_selection(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.set_selection(1.0, 3.0)
        assert track.selection == {'start': 1.0, 'end': 3.0}

    def test_clear_selection(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.set_selection(1.0, 3.0)
        track.clear_selection()
        assert track.selection is None

    def test_set_selection_invalid_range(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(ValueError, match='start must be < end'):
            track.set_selection(5.0, 2.0)

    def test_set_selection_equal_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(ValueError):
            track.set_selection(3.0, 3.0)

    def test_selection_returns_copy(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.set_selection(1.0, 5.0)
        sel = track.selection
        sel['start'] = 99.0
        assert track.selection == {'start': 1.0, 'end': 5.0}


class TestCutSelection:
    def test_cut_removes_clips_in_range(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.add_image(1, 0.0, 2.0)
        track.add_image(2, 3.0, 2.0)
        track.add_image(3, 6.0, 2.0)
        track.set_selection(2.5, 5.5)
        cut = track.cut_selection()
        assert len(cut) == 1
        assert cut[0]['src'] == 2
        assert len(track) == 2

    def test_cut_clears_selection(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.add_image(1, 0.0, 2.0)
        track.set_selection(0.0, 3.0)
        track.cut_selection()
        assert track.selection is None

    def test_cut_no_selection_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(ValueError, match='No selection'):
            track.cut_selection()


class TestCopySelection:
    def test_copy_returns_deep_copies(self, project):
        track = project.timeline.get_or_create_track('Video')
        clip = track.add_image(1, 0.0, 2.0)
        track.set_selection(0.0, 3.0)
        copied = track.copy_selection()
        assert len(copied) == 1
        assert copied[0]['src'] == 1
        # Verify deep copy — mutating copy doesn't affect original
        copied[0]['src'] = 999
        assert track.find_clip(clip.id).source_id == 1

    def test_copy_no_selection_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(ValueError, match='No selection'):
            track.copy_selection()

    def test_copy_preserves_clip_count(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.add_image(1, 0.0, 2.0)
        track.add_image(2, 3.0, 2.0)
        track.set_selection(0.0, 5.5)
        copied = track.copy_selection()
        assert len(copied) == 2
        assert len(track) == 2


class TestPasteAt:
    def test_paste_inserts_clips_at_time(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.add_image(1, 0.0, 2.0)
        track.set_selection(0.0, 3.0)
        copied = track.copy_selection()
        pasted = track.paste_at(copied, 5.0)
        assert len(pasted) == 1
        assert pasted[0].start == seconds_to_ticks(5.0)

    def test_paste_empty_list(self, project):
        track = project.timeline.get_or_create_track('Video')
        result = track.paste_at([], 0.0)
        assert result == []

    def test_paste_assigns_fresh_ids(self, project):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        track.set_selection(0.0, 3.0)
        copied = track.copy_selection()
        pasted = track.paste_at(copied, 5.0)
        assert pasted[0].id != c1.id

    def test_cut_then_paste_roundtrip(self, project):
        track = project.timeline.get_or_create_track('Video')
        track.add_image(1, 0.0, 2.0)
        track.add_image(2, 3.0, 2.0)
        track.set_selection(0.0, 3.0)
        cut_clips = track.cut_selection()
        assert len(track) == 1
        pasted = track.paste_at(cut_clips, 10.0)
        assert len(track) == 2
        assert pasted[0].start == seconds_to_ticks(10.0)


class TestAddExportedFrame:
    def test_creates_imfile_at_time(self, project):
        track = project.timeline.get_or_create_track('Video')
        source = track.add_image(1, 0.0, 5.0)
        frame = track.add_exported_frame(source.id, 10.0)
        assert frame.clip_type == 'IMFile'
        assert frame.start == seconds_to_ticks(10.0)

    def test_metadata_contains_source_info(self, project):
        track = project.timeline.get_or_create_track('Video')
        source = track.add_image(1, 0.0, 5.0)
        frame = track.add_exported_frame(source.id, 10.0)
        meta = frame._data.get('metadata', {})
        assert meta['exported_frame']['source_clip_id'] == source.id
        assert meta['exported_frame']['at_seconds'] == 10.0

    def test_missing_clip_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(KeyError):
            track.add_exported_frame(9999, 0.0)


class TestRippleReplaceMedia:
    def test_ripple_mode_shifts_subsequent(self, project):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        c2 = track.add_image(2, 2.0, 2.0)
        new_media = {
            '_type': 'IMFile', 'duration': seconds_to_ticks(4.0),
            'mediaDuration': 1, 'scalar': 1, 'src': 10,
        }
        track.ripple_replace_media(c1.id, new_media, mode='ripple')
        # c2 should have shifted by +2s (new 4s - old 2s)
        refreshed_c2 = track.find_clip(c2.id)
        assert refreshed_c2.start == seconds_to_ticks(4.0)

    def test_overwrite_mode_no_shift(self, project):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        c2 = track.add_image(2, 2.0, 2.0)
        new_media = {
            '_type': 'IMFile', 'duration': seconds_to_ticks(4.0),
            'mediaDuration': 1, 'scalar': 1, 'src': 10,
        }
        track.ripple_replace_media(c1.id, new_media, mode='overwrite')
        refreshed_c2 = track.find_clip(c2.id)
        assert refreshed_c2.start == seconds_to_ticks(2.0)

    def test_invalid_mode_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        with pytest.raises(ValueError, match='mode'):
            track.ripple_replace_media(c1.id, {}, mode='bad')

    def test_missing_clip_raises(self, project):
        track = project.timeline.get_or_create_track('Video')
        with pytest.raises(KeyError):
            track.ripple_replace_media(9999, {})


class TestRippleReplaceInGroup:
    def test_replaces_clip_in_group(self, project):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        c2 = track.add_image(2, 2.0, 2.0)
        group = track.group_clips([c1.id, c2.id])
        inner_medias = group._data['tracks'][0]['medias']
        target_id = inner_medias[0]['id']
        new_media = {
            '_type': 'IMFile', 'duration': seconds_to_ticks(3.0),
            'mediaDuration': 1, 'scalar': 1, 'src': 99,
        }
        result = ripple_replace_in_group(group, target_id, new_media)
        assert result is True
        replaced = group._data['tracks'][0]['medias'][0]
        assert replaced['src'] == 99

    def test_returns_false_when_not_found(self, project):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        group = track.group_clips([c1.id])
        assert ripple_replace_in_group(group, 99999, {}) is False

    def test_ripple_shifts_subsequent_in_group(self, project):
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        c2 = track.add_image(2, 2.0, 2.0)
        group = track.group_clips([c1.id, c2.id])
        inner_medias = group._data['tracks'][0]['medias']
        first_id = inner_medias[0]['id']
        second_start_before = inner_medias[1]['start']
        new_media = {
            '_type': 'IMFile', 'duration': seconds_to_ticks(4.0),
            'mediaDuration': 1, 'scalar': 1, 'src': 99,
        }
        ripple_replace_in_group(group, first_id, new_media)
        # Second clip should have shifted by the duration difference
        second_start_after = inner_medias[1]['start']
        expected_delta = seconds_to_ticks(4.0) - seconds_to_ticks(2.0)
        assert second_start_after == second_start_before + expected_delta

    def test_recurses_into_nested_group(self, project):
        """Cover layout.py lines 416-419: recurse into nested Group."""
        track = project.timeline.get_or_create_track('Video')
        c1 = track.add_image(1, 0.0, 2.0)
        c2 = track.add_image(2, 2.0, 2.0)
        outer = track.group_clips([c1.id, c2.id])
        # Now group the inner clips into a nested group
        inner_medias = outer._data['tracks'][0]['medias']
        inner_id = inner_medias[0]['id']
        # Wrap inner_medias[0] in a nested Group
        nested_group = {
            '_type': 'Group',
            'id': 8888,
            'start': 0,
            'duration': seconds_to_ticks(2.0),
            'tracks': [{'medias': [inner_medias[0]]}],
        }
        outer._data['tracks'][0]['medias'][0] = nested_group
        new_media = {
            '_type': 'IMFile', 'duration': seconds_to_ticks(2.0),
            'mediaDuration': 1, 'scalar': 1, 'src': 77,
        }
        result = ripple_replace_in_group(outer, inner_id, new_media)
        assert result is True
