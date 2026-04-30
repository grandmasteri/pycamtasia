"""Tests for annotation favorites save/load/list/delete."""
from __future__ import annotations

import json

import pytest

from camtasia.annotations.callouts import (
    delete_favorite,
    list_favorites,
    load_favorite,
    save_as_favorite,
    text,
)
from camtasia.annotations.types import Color


class TestSaveAsFavorite:
    def test_saves_json_file(self, tmp_path):
        callout = text('Hello', 'Arial', 'Bold')
        path = save_as_favorite(callout, 'my-callout', favorites_dir=tmp_path)
        assert path == tmp_path / 'my-callout.json'
        assert path.exists()

    def test_saved_content_matches_input(self, tmp_path):
        callout = text('Hello', 'Arial', 'Bold')
        save_as_favorite(callout, 'test', favorites_dir=tmp_path)
        loaded = json.loads((tmp_path / 'test.json').read_text())
        assert loaded == callout

    def test_creates_parent_directories(self, tmp_path):
        nested = tmp_path / 'a' / 'b' / 'c'
        callout = {'kind': 'remix', 'shape': 'text'}
        path = save_as_favorite(callout, 'deep', favorites_dir=nested)
        assert path.exists()

    def test_overwrites_existing_favorite(self, tmp_path):
        save_as_favorite({'v': 1}, 'dup', favorites_dir=tmp_path)
        save_as_favorite({'v': 2}, 'dup', favorites_dir=tmp_path)
        assert load_favorite('dup', favorites_dir=tmp_path) == {'v': 2}


class TestLoadFavorite:
    def test_round_trips_callout(self, tmp_path):
        callout = text('World', 'Montserrat', 'Regular', font_size=48.0)
        save_as_favorite(callout, 'rt', favorites_dir=tmp_path)
        loaded = load_favorite('rt', favorites_dir=tmp_path)
        assert loaded == callout

    def test_raises_on_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_favorite('nonexistent', favorites_dir=tmp_path)


class TestListFavorites:
    def test_empty_directory(self, tmp_path):
        assert list_favorites(favorites_dir=tmp_path) == []

    def test_nonexistent_directory(self, tmp_path):
        assert list_favorites(favorites_dir=tmp_path / 'nope') == []

    def test_returns_sorted_names(self, tmp_path):
        for name in ['zebra', 'alpha', 'middle']:
            save_as_favorite({}, name, favorites_dir=tmp_path)
        assert list_favorites(favorites_dir=tmp_path) == ['alpha', 'middle', 'zebra']

    def test_ignores_non_json_files(self, tmp_path):
        save_as_favorite({}, 'real', favorites_dir=tmp_path)
        (tmp_path / 'not-json.txt').write_text('hello')
        assert list_favorites(favorites_dir=tmp_path) == ['real']


class TestDeleteFavorite:
    def test_removes_file(self, tmp_path):
        save_as_favorite({}, 'doomed', favorites_dir=tmp_path)
        delete_favorite('doomed', favorites_dir=tmp_path)
        assert not (tmp_path / 'doomed.json').exists()

    def test_raises_on_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            delete_favorite('ghost', favorites_dir=tmp_path)


class TestCalloutAddToFavorites:
    def test_saves_definition_via_clip(self, project):
        track = project.timeline.tracks[0]
        callout_def = text('Fav', 'Arial', 'Bold')
        clip = track.add_callout('Fav', start_seconds=0, duration_seconds=3, font_name='Arial', font_weight='Bold')
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            fav_dir = Path(td)
            import camtasia.annotations.callouts as mod
            orig = mod._DEFAULT_FAVORITES_DIR
            mod._DEFAULT_FAVORITES_DIR = fav_dir
            try:
                path = clip.add_to_favorites('my-fav')
                assert path.exists()
                loaded = json.loads(path.read_text())
                assert loaded['text'] == 'Fav'
                assert loaded['shape'] == 'text'
            finally:
                mod._DEFAULT_FAVORITES_DIR = orig


class TestReExports:
    def test_module_level_imports(self):
        from camtasia.annotations import (
            delete_favorite,
            list_favorites,
            load_favorite,
            save_as_favorite,
        )
        assert callable(save_as_favorite)
        assert callable(load_favorite)
        assert callable(list_favorites)
        assert callable(delete_favorite)
