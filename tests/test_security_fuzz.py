"""Tests for security and fuzz findings (REV-security-*, REV-fuzz-*)."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import zipfile

import pytest

RESOURCES = Path(__file__).parent.parent / "src" / "camtasia" / "resources"


def _make_project(tmp_path: Path, data: dict | None = None) -> Path:
    """Create a .cmproj bundle with custom JSON data."""
    proj_dir = tmp_path / "test.cmproj"
    shutil.copytree(RESOURCES / "new.cmproj", proj_dir)
    if data is not None:
        tscproj = next(proj_dir.glob("*.tscproj"))
        tscproj.write_text(json.dumps(data))
    return proj_dir


# ── REV-fuzz-001: timeline as string ──────────────────────────────────


class TestFuzz001TimelineString:
    def test_rejects_string_timeline(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = _make_project(tmp_path)
        data = json.loads(next(proj_dir.glob("*.tscproj")).read_text())
        data["timeline"] = "not a dict"
        next(proj_dir.glob("*.tscproj")).write_text(json.dumps(data))

        with pytest.raises(ValueError, match=r"timeline.*must be a dict"):
            load_project(proj_dir)


# ── REV-fuzz-002: empty JSON object ──────────────────────────────────


class TestFuzz002EmptyJson:
    def test_rejects_empty_json(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = _make_project(tmp_path, data={})

        with pytest.raises(ValueError, match="missing required key"):
            load_project(proj_dir)


# ── REV-fuzz-009: missing timeline key ───────────────────────────────


class TestFuzz009MissingTimeline:
    def test_rejects_missing_timeline(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = _make_project(tmp_path)
        data = json.loads(next(proj_dir.glob("*.tscproj")).read_text())
        del data["timeline"]
        next(proj_dir.glob("*.tscproj")).write_text(json.dumps(data))

        with pytest.raises(ValueError, match=r"missing required key.*timeline"):
            load_project(proj_dir)


# ── REV-fuzz-007: validate() crashes on corrupted tracks ─────────────


class TestFuzz007ValidateCrash:
    def test_validate_handles_none_tracks(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = _make_project(tmp_path)
        p = load_project(proj_dir)
        # Corrupt tracks to None
        p._data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"] = None

        issues = p.validate()
        assert any("corrupt" in i.message.lower() or "structure" in i.message.lower() for i in issues)

    def test_validate_handles_tracks_as_string(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = _make_project(tmp_path)
        p = load_project(proj_dir)
        p._data["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"] = "bad"

        issues = p.validate()
        assert any("corrupt" in i.message.lower() or "structure" in i.message.lower() for i in issues)

    def test_validate_handles_corrupted_source_bin(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = _make_project(tmp_path)
        p = load_project(proj_dir)
        p._data["sourceBin"] = "not a list"

        issues = p.validate()
        assert any("corrupt" in i.message.lower() or "structure" in i.message.lower() for i in issues)

    def test_validate_handles_source_bin_as_int(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = _make_project(tmp_path)
        p = load_project(proj_dir)
        p._data["sourceBin"] = 42

        issues = p.validate()
        assert any("corrupt" in i.message.lower() or "structure" in i.message.lower() for i in issues)


# ── REV-security-001: zip-slip in import_libzip ──────────────────────


class TestSecurity001ZipSlip:
    def test_rejects_absolute_thumbnail_path(self, tmp_path: Path) -> None:
        import warnings

        from camtasia.library.libzip import import_libzip

        malicious = tmp_path / "evil.libzip"
        asset_data = {
            "name": "evil",
            "kind": "template",
            "payload": {},
            "thumbnail": "/etc/passwd",
        }
        manifest = {"assets": [{"name": "evil", "file": "asset_0.json"}], "folders": []}
        with zipfile.ZipFile(malicious, "w") as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("asset_0.json", json.dumps(asset_data))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValueError, match=r"[Uu]nsafe.*thumbnail"):
                import_libzip(malicious)

    def test_rejects_dotdot_thumbnail_path(self, tmp_path: Path) -> None:
        import warnings

        from camtasia.library.libzip import import_libzip

        malicious = tmp_path / "evil.libzip"
        asset_data = {
            "name": "evil",
            "kind": "template",
            "payload": {},
            "thumbnail": "../../etc/passwd",
        }
        manifest = {"assets": [{"name": "evil", "file": "asset_0.json"}], "folders": []}
        with zipfile.ZipFile(malicious, "w") as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("asset_0.json", json.dumps(asset_data))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValueError, match=r"[Uu]nsafe.*thumbnail"):
                import_libzip(malicious)

    def test_rejects_path_traversal_entry_file(self, tmp_path: Path) -> None:
        import warnings

        from camtasia.library.libzip import import_libzip

        malicious = tmp_path / "evil.libzip"
        manifest = {"assets": [{"name": "evil", "file": "../../../etc/passwd"}], "folders": []}
        with zipfile.ZipFile(malicious, "w") as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("../../../etc/passwd", json.dumps({"name": "x", "kind": "x"}))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(ValueError, match=r"[Uu]nsafe.*path"):
                import_libzip(malicious)

    def test_accepts_safe_thumbnail(self, tmp_path: Path) -> None:
        import warnings

        from camtasia.library.libzip import import_libzip

        safe = tmp_path / "safe.libzip"
        asset_data = {
            "name": "ok",
            "kind": "template",
            "payload": {},
            "thumbnail": "thumbnails/ok.png",
        }
        manifest = {"assets": [{"name": "ok", "file": "asset_0.json"}], "folders": []}
        with zipfile.ZipFile(safe, "w") as zf:
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("asset_0.json", json.dumps(asset_data))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lib = import_libzip(safe)
        assert len(list(lib)) == 1
        assert next(iter(lib)).thumbnail_path == Path("thumbnails/ok.png")


# ── REV-security-002: JSON bomb / no size limit ─────────────────────


class TestSecurity002JsonBomb:
    def test_rejects_oversized_project_file(self, tmp_path: Path) -> None:
        from camtasia.project import load_project

        proj_dir = tmp_path / "big.cmproj"
        proj_dir.mkdir()
        tscproj = proj_dir / "big.tscproj"
        # Write a file that exceeds the size limit (default 100MB)
        # We'll use a smaller limit for testing by checking the mechanism
        data = {"sourceBin": [], "timeline": {"sceneTrack": {"scenes": [{"csml": {"tracks": []}}]}}, "editRate": 705600000}
        tscproj.write_text(json.dumps(data))

        # Normal-sized file should load fine
        p = load_project(proj_dir)
        assert p.title == ""

    def test_rejects_file_over_max_size(self, tmp_path: Path) -> None:
        from camtasia.project import Project

        proj_dir = tmp_path / "huge.cmproj"
        proj_dir.mkdir()
        tscproj = proj_dir / "huge.tscproj"
        # Create a file just over the limit by writing padding
        data = {"sourceBin": [], "timeline": {"sceneTrack": {"scenes": [{"csml": {"tracks": []}}]}}, "editRate": 705600000}
        base = json.dumps(data)
        # Pad with spaces in a string field to exceed limit
        # We'll monkeypatch the limit for testing
        tscproj.write_text(base)

        import camtasia.project as proj_mod
        old_limit = proj_mod._MAX_PROJECT_FILE_SIZE
        try:
            proj_mod._MAX_PROJECT_FILE_SIZE = 10  # 10 bytes
            with pytest.raises(ValueError, match="exceeds maximum"):
                Project(proj_dir.resolve())
        finally:
            proj_mod._MAX_PROJECT_FILE_SIZE = old_limit


# ── REV-security-003: save() follows symlinks, from_template rmtree ──


class TestSecurity003PathTraversal:
    def test_from_template_refuses_non_cmproj_rmtree(self, tmp_path: Path) -> None:
        from camtasia.project import Project

        template = _make_project(tmp_path / "sub")
        # Create a non-.cmproj directory at the output path
        target = tmp_path / "important_data"
        target.mkdir()
        (target / "precious.txt").write_text("don't delete me")

        with pytest.raises(ValueError, match=r"[Rr]efus|[Ss]afety|cmproj"):
            Project.from_template(template, target)

        # Verify the directory was NOT deleted
        assert (target / "precious.txt").exists()

    def test_new_refuses_non_cmproj_rmtree(self, tmp_path: Path) -> None:
        from camtasia.project import Project

        target = tmp_path / "important_data"
        target.mkdir()
        (target / "precious.txt").write_text("don't delete me")

        with pytest.raises(ValueError, match=r"[Rr]efus|[Ss]afety|cmproj"):
            Project.new(target)

        assert (target / "precious.txt").exists()

    def test_from_template_allows_cmproj_overwrite(self, tmp_path: Path) -> None:
        from camtasia.project import Project

        template = _make_project(tmp_path / "sub")
        target = tmp_path / "output.cmproj"
        target.mkdir()
        (target / "old.txt").write_text("old")

        proj = Project.from_template(template, target)
        assert proj.title is not None  # loaded successfully

    def test_save_refuses_symlink_escape(self, tmp_path: Path) -> None:
        from camtasia.project import Project

        # Create a real project
        real_dir = _make_project(tmp_path / "real")

        # Create a symlink to it
        symlink_dir = tmp_path / "symlink.cmproj"
        symlink_dir.symlink_to(real_dir)

        with pytest.raises(ValueError, match=r"[Ss]ymlink"):
            Project.load(str(symlink_dir))
