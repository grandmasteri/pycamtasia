"""Tests for camtasia.library module."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock
import zipfile

import pytest

from camtasia.library.library import Libraries, Library, LibraryAsset
from camtasia.library.libzip import export_libzip, import_libzip


class TestLibraryAsset:
    def test_dataclass_fields(self):
        asset = LibraryAsset(name="intro", kind="clip", payload={"src": 1}, thumbnail_path=Path("/thumb.png"))
        assert asset.name == "intro"
        assert asset.kind == "clip"
        assert asset.payload == {"src": 1}
        assert asset.thumbnail_path == Path("/thumb.png")

    def test_defaults(self):
        asset = LibraryAsset(name="x", kind="media")
        assert asset.payload == {}
        assert asset.thumbnail_path is None


class TestLibrary:
    def test_name_and_empty(self):
        lib = Library("My Library")
        assert lib.name == "My Library"
        assert lib.assets == []
        assert lib.folders == {}
        assert len(lib) == 0

    def test_repr(self):
        lib = Library("test")
        assert "test" in repr(lib)

    def test_add_asset_clip(self):
        lib = Library("lib")
        clip_data = {"src": 1, "start": 0, "duration": 100}
        asset = lib.add_asset(clip_data, "my clip")
        assert asset.name == "my clip"
        assert asset.kind == "clip"
        assert asset.payload["_useCanvasSize"] is True
        # Original data not mutated
        assert "_useCanvasSize" not in clip_data

    def test_add_asset_group(self):
        lib = Library("lib")
        group_data = {"medias": [{"src": 1}], "name": "grp"}
        asset = lib.add_asset(group_data, "my group")
        assert asset.kind == "group"

    def test_add_asset_no_canvas_size(self):
        lib = Library("lib")
        asset = lib.add_asset({"src": 1}, "clip", use_canvas_size=False)
        assert "_useCanvasSize" not in asset.payload

    def test_add_timeline_selection(self):
        mock_clip = MagicMock()
        mock_clip.start = 50
        mock_clip.duration = 100
        mock_clip._data = {"src": 1, "start": 50}

        mock_clip_outside = MagicMock()
        mock_clip_outside.start = 200
        mock_clip_outside.duration = 50
        mock_clip_outside._data = {"src": 2, "start": 200}

        timeline = MagicMock()
        timeline.all_clips.return_value = [mock_clip, mock_clip_outside]

        lib = Library("lib")
        asset = lib.add_timeline_selection(timeline, 0, 150, "selection")
        assert asset.kind == "selection"
        assert len(asset.payload["clips"]) == 1
        assert asset.payload["range"] == [0, 150]
        assert asset.payload["_useCanvasSize"] is True

    def test_add_timeline_selection_no_canvas(self):
        timeline = MagicMock()
        timeline.all_clips.return_value = []
        lib = Library("lib")
        asset = lib.add_timeline_selection(timeline, 0, 100, "sel", use_canvas_size=False)
        assert "_useCanvasSize" not in asset.payload

    def test_create_folder(self):
        lib = Library("lib")
        folder = lib.create_folder("Intros")
        assert "Intros" in lib.folders
        assert folder == {}

    def test_create_subfolder(self):
        lib = Library("lib")
        lib.create_folder("parent")
        lib.create_folder("child", parent="parent")
        assert "child" in lib.folders["parent"]

    def test_create_subfolder_missing_parent(self):
        lib = Library("lib")
        with pytest.raises(KeyError, match="does not exist"):
            lib.create_folder("child", parent="nonexistent")

    def test_move_folder(self):
        lib = Library("lib")
        lib.create_folder("src")
        lib.create_folder("dest")
        lib.move("src", "dest")
        assert "src" not in lib.folders
        assert "src" in lib.folders["dest"]

    def test_move_asset(self):
        lib = Library("lib")
        lib.add_asset({"src": 1}, "clip1")
        lib.create_folder("folder")
        lib.move("clip1", "folder")
        assert "clip1" in lib.folders["folder"]

    def test_move_missing_dest(self):
        lib = Library("lib")
        lib.add_asset({"src": 1}, "clip1")
        with pytest.raises(KeyError, match="does not exist"):
            lib.move("clip1", "nonexistent")

    def test_move_not_found(self):
        lib = Library("lib")
        lib.create_folder("dest")
        with pytest.raises(KeyError, match="not found"):
            lib.move("ghost", "dest")

    def test_import_media(self, tmp_path):
        lib = Library("lib")
        f1 = tmp_path / "video.mp4"
        f2 = tmp_path / "audio.wav"
        f1.touch()
        f2.touch()
        assets = lib.import_media([f1, f2])
        assert len(assets) == 2
        assert {a.name for a in assets} == {"video", "audio"}
        assert all(a.kind == "media" for a in assets)
        assert len(lib) == 2

    def test_import_media_into_folder(self, tmp_path):
        lib = Library("lib")
        lib.create_folder("media")
        f = tmp_path / "clip.mp4"
        f.touch()
        lib.import_media([f], folder="media")
        assert "clip" in lib.folders["media"]

    def test_import_media_missing_folder(self, tmp_path):
        lib = Library("lib")
        with pytest.raises(KeyError, match="does not exist"):
            lib.import_media([tmp_path / "x.mp4"], folder="nope")

    def test_iteration(self):
        lib = Library("lib")
        lib.add_asset({"src": 1}, "a")
        lib.add_asset({"src": 2}, "b")
        names = [a.name for a in lib]
        assert names == ["a", "b"]


class TestLibraries:
    def test_create_and_list(self):
        libs = Libraries()
        libs.create("A")
        libs.create("B")
        assert libs.list() == ["A", "B"]
        assert len(libs) == 2

    def test_repr(self):
        libs = Libraries()
        assert "0" in repr(libs)

    def test_create_duplicate(self):
        libs = Libraries()
        libs.create("A")
        with pytest.raises(ValueError, match="already exists"):
            libs.create("A")

    def test_default_is_first_created(self):
        libs = Libraries()
        first = libs.create("first")
        libs.create("second")
        assert libs.default is first

    def test_default_no_libraries(self):
        libs = Libraries()
        with pytest.raises(RuntimeError, match="No libraries"):
            _ = libs.default

    def test_get(self):
        libs = Libraries()
        created = libs.create("mine")
        assert libs.get("mine") is created

    def test_get_missing(self):
        libs = Libraries()
        with pytest.raises(KeyError, match="not found"):
            libs.get("nope")

    def test_create_from_existing(self):
        libs = Libraries()
        source = libs.create("source")
        source.add_asset({"src": 1}, "clip1")
        clone = libs.create("clone", start_from=source)
        assert len(clone) == 1
        assert clone.assets[0].name == "clip1"
        # Deep copy — mutating clone doesn't affect source
        clone.assets[0].payload["extra"] = True
        assert "extra" not in source.assets[0].payload


class TestExportImportLibzip:
    def test_roundtrip(self, tmp_path):
        lib = Library("roundtrip")
        lib.add_asset({"src": 1, "start": 0}, "clip1")
        lib.add_asset({"src": 2}, "clip2")
        lib.create_folder("folder1")

        archive_path = tmp_path / "test.libzip"
        with pytest.warns(UserWarning, match="pycamtasia"):
            result_path = export_libzip(lib, archive_path)
        assert result_path == archive_path
        assert result_path.exists()

        with pytest.warns(UserWarning, match="pycamtasia"):
            imported = import_libzip(result_path)
        assert imported.name == "test"
        assert len(imported.assets) == 2
        assert {a.name for a in imported} == {"clip1", "clip2"}
        assert "folder1" in imported.folders

    def test_export_appends_suffix(self, tmp_path):
        lib = Library("lib")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            path = export_libzip(lib, tmp_path / "archive")
        assert path.suffix == ".libzip"

    def test_export_zip_structure(self, tmp_path):
        lib = Library("lib")
        lib.add_asset({"key": "val"}, "asset1")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            path = export_libzip(lib, tmp_path / "out.libzip")
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            assert "manifest.json" in names
            assert "asset_0.json" in names
            manifest = json.loads(zf.read("manifest.json"))
            assert len(manifest["assets"]) == 1
            asset_data = json.loads(zf.read("asset_0.json"))
            assert asset_data["name"] == "asset1"

    def test_import_not_found(self, tmp_path):
        with pytest.warns(UserWarning, match="custom JSON-based format"), pytest.raises(FileNotFoundError):
            import_libzip(tmp_path / "missing.libzip")

    def test_import_no_target_no_create(self, tmp_path):
        # Create a valid archive first
        lib = Library("x")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            path = export_libzip(lib, tmp_path / "x.libzip")
        with pytest.warns(UserWarning, match="custom JSON-based format"), pytest.raises(ValueError, match="create_new is False"):
            import_libzip(path, create_new=False)

    def test_import_into_existing_library(self, tmp_path):
        lib = Library("source")
        lib.add_asset({"src": 1}, "original")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            path = export_libzip(lib, tmp_path / "src.libzip")

        target = Library("target")
        target.add_asset({"src": 99}, "existing")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            result = import_libzip(path, target_library=target)
        assert result is target
        assert len(result.assets) == 2
        assert {a.name for a in result} == {"existing", "original"}

    def test_asset_with_thumbnail_roundtrip(self, tmp_path):
        lib = Library("thumbs")
        asset = LibraryAsset(name="pic", kind="media", payload={"src": "img.png"}, thumbnail_path=Path("thumbnails/t.png"))
        lib.assets.append(asset)
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            path = export_libzip(lib, tmp_path / "thumbs.libzip")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            imported = import_libzip(path)
        assert imported.assets[0].thumbnail_path == Path("thumbnails/t.png")

    def test_asset_without_thumbnail_roundtrip(self, tmp_path):
        lib = Library("no_thumb")
        lib.add_asset({"src": 1}, "clip")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            path = export_libzip(lib, tmp_path / "no_thumb.libzip")
        with pytest.warns(UserWarning, match="custom JSON-based format"):
            imported = import_libzip(path)
        assert imported.assets[0].thumbnail_path is None
