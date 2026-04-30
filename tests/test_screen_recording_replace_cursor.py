"""Tests for ScreenIMFile replace_cursor, import_custom_cursor, CursorType, and related methods."""
from __future__ import annotations

import pytest

from camtasia.timeline.clips.screen_recording import CursorType, ScreenIMFile
from camtasia.timing import seconds_to_ticks

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_screen_im(params: dict | None = None, **overrides) -> ScreenIMFile:
    """Build a minimal ScreenIMFile from a raw dict."""
    data: dict = {
        '_type': 'ScreenIMFile',
        'id': 1,
        'start': 0,
        'duration': seconds_to_ticks(10.0),
        'mediaDuration': 1,
        'parameters': params or {},
    }
    data.update(overrides)
    return ScreenIMFile(data)


def _cursor_loc_params(keyframes: list[tuple[float, float, float]]) -> dict:
    """Build a cursorLocation parameter dict from (time, x, y) tuples."""
    kfs = []
    for i, (t, x, y) in enumerate(keyframes):
        ticks = seconds_to_ticks(t)
        next_ticks = seconds_to_ticks(keyframes[i + 1][0]) if i + 1 < len(keyframes) else ticks
        kfs.append({
            'endTime': next_ticks,
            'time': ticks,
            'value': [x, y, 0],
            'duration': next_ticks - ticks,
        })
    return {
        'cursorLocation': {
            'type': 'point',
            'keyframes': kfs,
        },
    }


# ===========================================================================
# CursorType enum
# ===========================================================================


class TestCursorTypeEnum:
    def test_all_members_exist(self):
        expected = {'ARROW', 'HAND', 'IBEAM', 'CROSSHAIR', 'WAIT', 'HELP', 'TEXT', 'NO_CURSOR'}
        assert set(CursorType.__members__) == expected

    def test_values_are_sentinel_strings(self):
        for member in CursorType:
            assert member.value.startswith('cursor://')

    def test_arrow_value(self):
        assert CursorType.ARROW.value == 'cursor://arrow'

    def test_no_cursor_value(self):
        assert CursorType.NO_CURSOR.value == 'cursor://none'


# ===========================================================================
# replace_cursor
# ===========================================================================


class TestReplaceCursor:
    def test_current_scope_sets_image_path(self):
        clip = _make_screen_im()
        result = clip.replace_cursor('/path/to/cursor.png')
        assert clip.cursor_image_path == '/path/to/cursor.png'
        assert result is clip

    def test_current_scope_does_not_write_metadata(self):
        clip = _make_screen_im()
        clip.replace_cursor('/path/to/cursor.png', scope='current')
        assert 'cursorReplaceScope' not in clip._data.get('metadata', {})

    def test_similar_scope_writes_metadata(self):
        clip = _make_screen_im()
        clip.replace_cursor('/path/to/cursor.png', scope='similar')
        assert clip.cursor_image_path == '/path/to/cursor.png'
        assert clip._data['metadata']['cursorReplaceScope'] == 'similar'

    def test_all_scope_writes_metadata(self):
        clip = _make_screen_im()
        clip.replace_cursor('/path/to/cursor.png', scope='all')
        assert clip._data['metadata']['cursorReplaceScope'] == 'all'

    def test_invalid_scope_raises(self):
        clip = _make_screen_im()
        with pytest.raises(ValueError, match='scope must be'):
            clip.replace_cursor('/path', scope='invalid')

    def test_default_scope_is_current(self):
        clip = _make_screen_im()
        clip.replace_cursor('/path/to/cursor.png')
        assert 'cursorReplaceScope' not in clip._data.get('metadata', {})


# ===========================================================================
# import_custom_cursor
# ===========================================================================


class TestImportCustomCursor:
    @pytest.mark.parametrize('ext', ['.bmp', '.jpeg', '.jpg', '.png', '.tif', '.tiff'])
    def test_valid_extensions_accepted(self, ext):
        clip = _make_screen_im()
        result = clip.import_custom_cursor(f'/cursors/my_cursor{ext}')
        assert clip.cursor_image_path == f'/cursors/my_cursor{ext}'
        assert result is clip

    def test_uppercase_extension_accepted(self):
        clip = _make_screen_im()
        clip.import_custom_cursor('/cursors/arrow.PNG')
        assert clip.cursor_image_path == '/cursors/arrow.PNG'

    def test_invalid_extension_raises(self):
        clip = _make_screen_im()
        with pytest.raises(ValueError, match='Unsupported cursor image extension'):
            clip.import_custom_cursor('/cursors/cursor.gif')

    def test_no_extension_raises(self):
        clip = _make_screen_im()
        with pytest.raises(ValueError, match='Unsupported cursor image extension'):
            clip.import_custom_cursor('/cursors/cursor')

    def test_delegates_to_replace_cursor(self):
        clip = _make_screen_im()
        clip.import_custom_cursor('/cursors/hand.bmp')
        # Default scope is 'current', so no metadata
        assert 'cursorReplaceScope' not in clip._data.get('metadata', {})


# ===========================================================================
# unpack_rev_media
# ===========================================================================


class TestUnpackRevMedia:
    def test_trec_source_flags_unpack(self):
        clip = _make_screen_im(src='./media/recording.trec')
        result = clip.unpack_rev_media()
        assert result is True
        assert clip._data['metadata']['needsUnpack'] is True

    def test_non_trec_source_returns_false(self):
        clip = _make_screen_im(src=42)
        result = clip.unpack_rev_media()
        assert result is False
        assert 'needsUnpack' not in clip._data.get('metadata', {})

    def test_rev_packed_metadata_flags_unpack(self):
        clip = _make_screen_im(src=42, metadata={'revPacked': True})
        result = clip.unpack_rev_media()
        assert result is True
        assert clip._data['metadata']['needsUnpack'] is True

    def test_no_src_returns_false(self):
        clip = _make_screen_im()
        result = clip.unpack_rev_media()
        assert result is False


# ===========================================================================
# extend_cursor_path
# ===========================================================================


class TestExtendCursorPath:
    def test_extends_beyond_last_keyframe(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 100, 200), (3.0, 300, 400)]))
        clip.extend_cursor_path(5.0)
        kfs = clip.cursor_location_keyframes
        assert len(kfs) == 3
        assert kfs[-1]['time'] == seconds_to_ticks(5.0)
        assert kfs[-1]['value'] == [300, 400, 0]

    def test_noop_when_already_at_target(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 100, 200), (5.0, 300, 400)]))
        clip.extend_cursor_path(5.0)
        assert len(clip.cursor_location_keyframes) == 2

    def test_noop_when_beyond_target(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 100, 200), (10.0, 300, 400)]))
        clip.extend_cursor_path(5.0)
        assert len(clip.cursor_location_keyframes) == 2

    def test_noop_when_no_keyframes(self):
        clip = _make_screen_im()
        clip.extend_cursor_path(5.0)
        assert clip.cursor_location_keyframes == []

    def test_durations_recomputed_after_extend(self):
        clip = _make_screen_im(_cursor_loc_params([(1.0, 10, 20)]))
        clip.extend_cursor_path(3.0)
        kfs = clip.cursor_location_keyframes
        assert kfs[0]['duration'] == seconds_to_ticks(3.0) - seconds_to_ticks(1.0)
        assert kfs[0]['endTime'] == seconds_to_ticks(3.0)
        assert kfs[1]['duration'] == 0


# ===========================================================================
# set_cursor_type
# ===========================================================================


class TestSetCursorType:
    def test_sets_arrow(self):
        clip = _make_screen_im()
        result = clip.set_cursor_type(CursorType.ARROW)
        assert clip.cursor_image_path == 'cursor://arrow'
        assert result is clip

    def test_sets_hand(self):
        clip = _make_screen_im()
        clip.set_cursor_type(CursorType.HAND)
        assert clip.cursor_image_path == 'cursor://hand'

    def test_sets_no_cursor(self):
        clip = _make_screen_im()
        clip.set_cursor_type(CursorType.NO_CURSOR)
        assert clip.cursor_image_path == 'cursor://none'

    @pytest.mark.parametrize('cursor_type', list(CursorType))
    def test_all_types_set_sentinel_path(self, cursor_type):
        clip = _make_screen_im()
        clip.set_cursor_type(cursor_type)
        assert clip.cursor_image_path == cursor_type.value
