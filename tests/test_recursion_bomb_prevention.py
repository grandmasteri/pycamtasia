"""Regression test for REV-red_team-001: recursion-bomb DoS prevention.

A .tscproj with extreme group nesting (~500 levels) loads OK via
json.loads (C code, no Python recursion) but crashes save() and
validate() with RecursionError. The size-limit doesn't help because
the file is only ~100 KB.

Fix: Project.__init__ runs an explicit-stack depth check and rejects
files exceeding MAX_NESTING_DEPTH (100).
"""
from __future__ import annotations

import pytest

from camtasia.project import Project


def _make_nested_project_json(depth: int) -> str:
    """Build a .tscproj with `depth` levels of Group nesting."""
    leaf = (
        '{"id":0,"_type":"AMFile","start":0,"duration":100,"src":0,'
        '"mediaStart":0,"mediaDuration":100,"scalar":1,'
        '"metadata":{},"animationTracks":{},"parameters":{},"effects":[]}'
    )
    current = leaf
    for i in range(1, depth + 1):
        current = (
            f'{{"id":{i},"_type":"Group","start":0,"duration":100,'
            f'"mediaStart":0,"mediaDuration":100,"scalar":1,'
            f'"metadata":{{}},"animationTracks":{{}},"parameters":{{}},"effects":[],'
            f'"tracks":[{{"trackIndex":0,"medias":[{current}]}}]}}'
        )
    return (
        f'{{"timeline":{{"sceneTrack":{{"scenes":[{{"csml":{{"tracks":['
        f'{{"trackIndex":0,"medias":[{current}]}}]}}}}]}},"parameters":{{}}}},'
        f'"sourceBin":[]}}'
    )


def test_deeply_nested_project_rejected(tmp_path):
    """500-level deep nesting must be rejected by depth check."""
    proj_dir = tmp_path / "bomb.cmproj"
    proj_dir.mkdir()
    (proj_dir / "project.tscproj").write_text(_make_nested_project_json(500))
    with pytest.raises(ValueError, match="nesting depth"):
        Project.load(proj_dir)


def test_normal_nesting_accepted(tmp_path):
    """Normal Camtasia-like nesting (a handful of levels) must load OK."""
    proj_dir = tmp_path / "normal.cmproj"
    proj_dir.mkdir()
    # 5 levels of groups — well within real-project nesting depth.
    (proj_dir / "project.tscproj").write_text(_make_nested_project_json(5))
    proj = Project.load(proj_dir)
    # Sanity — project loaded and has the expected top-level shape.
    assert proj._data["timeline"]["sceneTrack"]["scenes"]


def test_boundary_depth_accepted(tmp_path):
    """Moderate depth (under the 100 limit accounting for scene wrapping) accepted."""
    proj_dir = tmp_path / "boundary.cmproj"
    proj_dir.mkdir()
    # Each nested group adds 4 depth levels (Group → tracks → Track → medias → Group...).
    # 20 nested groups reach ~90 max depth, well under the 100 limit.
    (proj_dir / "project.tscproj").write_text(_make_nested_project_json(20))
    proj = Project.load(proj_dir)
    assert proj is not None
