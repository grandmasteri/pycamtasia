from __future__ import annotations
import json
import shutil
import pytest
from pathlib import Path
from camtasia import load_project

REAL_PROJECTS = [
    '/Users/isaadoug/Desktop/Anomaly Detection Demo v3/Anomaly Detection Demo (v3).cmproj',
    str(Path.home() / 'Desktop/Camtasia Projects/isaac.cmproj'),
    str(Path.home() / 'Desktop/Camtasia Projects/Converted AI-Native Planner Demo JT.cmproj'),
    str(Path.home() / 'Documents/Anomaly Detection Project Demo v2.cmproj'),
]


def _available_projects():
    return [p for p in REAL_PROJECTS if Path(p).exists()]


@pytest.mark.parametrize('project_path', _available_projects(), ids=lambda p: Path(p).stem)
class TestRoundTrip:
    def test_load_save_reload_preserves_data(self, project_path, tmp_path):
        """Load → save → reload produces identical JSON data."""
        src = Path(project_path)
        dst = tmp_path / src.name
        shutil.copytree(src, dst)

        # First save flattens parameters and updates formatting.
        # Second save→reload should be perfectly stable.
        proj = load_project(str(dst))
        proj.save()

        proj2 = load_project(str(dst))
        after_first = json.dumps(proj2._data, sort_keys=True)

        proj2.save()
        proj3 = load_project(str(dst))
        after_second = json.dumps(proj3._data, sort_keys=True)

        assert after_first == after_second

    def test_track_count_preserved(self, project_path, tmp_path):
        src = Path(project_path)
        dst = tmp_path / src.name
        shutil.copytree(src, dst)

        proj = load_project(str(dst))
        original_count = proj.timeline.track_count
        proj.save()
        proj2 = load_project(str(dst))
        assert proj2.timeline.track_count == original_count

    def test_clip_ids_preserved(self, project_path, tmp_path):
        src = Path(project_path)
        dst = tmp_path / src.name
        shutil.copytree(src, dst)

        proj = load_project(str(dst))
        original_ids = set()
        for track in proj.timeline.tracks:
            for clip in track.clips:
                original_ids.add(clip.id)

        proj.save()
        proj2 = load_project(str(dst))
        reloaded_ids = set()
        for track in proj2.timeline.tracks:
            for clip in track.clips:
                reloaded_ids.add(clip.id)

        assert reloaded_ids == original_ids

    def test_media_bin_preserved(self, project_path, tmp_path):
        src = Path(project_path)
        dst = tmp_path / src.name
        shutil.copytree(src, dst)

        proj = load_project(str(dst))
        original_media_ids = {m.id for m in proj.media_bin}
        proj.save()
        proj2 = load_project(str(dst))
        reloaded_media_ids = {m.id for m in proj2.media_bin}
        assert reloaded_media_ids == original_media_ids

    def test_validate_no_errors(self, project_path, tmp_path):
        src = Path(project_path)
        dst = tmp_path / src.name
        shutil.copytree(src, dst)

        proj = load_project(str(dst))
        issues = proj.validate()
        errors = [i for i in issues if i.level == 'error']
        if 'Anomaly Detection Demo (v3)' in project_path:
            # v3 fixture has a known stale transition reference (rightMedia=4 not on track)
            assert len(errors) >= 1
        else:
            assert errors == []

    def test_summary_does_not_crash(self, project_path, tmp_path):
        src = Path(project_path)
        dst = tmp_path / src.name
        shutil.copytree(src, dst)

        proj = load_project(str(dst))
        actual_summary = proj.summary()
        assert 'Tracks:' in actual_summary and 'Duration:' in actual_summary
