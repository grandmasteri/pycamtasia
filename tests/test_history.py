"""Tests for undo/redo history via JSON Patch diffs."""
from __future__ import annotations

import copy
from typing import Any

import pytest

from camtasia.history import ChangeHistory, ChangeRecord, with_undo


def _minimal_project_data() -> dict[str, Any]:
    return {"title": "Test", "tracks": [{"clips": []}]}


class TestChangeHistory:
    def test_initially_empty(self) -> None:
        history = ChangeHistory()
        assert not history.can_undo
        assert not history.can_redo
        assert history.undo_count == 0
        assert history.redo_count == 0
        assert history.descriptions == []

    def test_record_creates_undo_entry(self) -> None:
        history = ChangeHistory()
        snapshot_before = {"value": 1}
        snapshot_after = {"value": 2}
        history.record("change value", snapshot_before, snapshot_after)
        assert history.can_undo
        assert history.undo_count == 1
        assert history.descriptions == ["change value"]

    def test_record_noop_is_ignored(self) -> None:
        history = ChangeHistory()
        identical_data = {"value": 1}
        history.record("no-op", identical_data, copy.deepcopy(identical_data))
        assert history.undo_count == 0

    def test_undo_reverts_change(self) -> None:
        history = ChangeHistory()
        project_data = {"value": 1}
        snapshot_before = copy.deepcopy(project_data)
        project_data["value"] = 2
        history.record("set to 2", snapshot_before, project_data)

        returned_description = history.undo(project_data)
        assert project_data["value"] == 1
        assert returned_description == "set to 2"

    def test_redo_reapplies_change(self) -> None:
        history = ChangeHistory()
        project_data = {"value": 1}
        snapshot_before = copy.deepcopy(project_data)
        project_data["value"] = 2
        history.record("set to 2", snapshot_before, project_data)
        history.undo(project_data)

        returned_description = history.redo(project_data)
        assert project_data["value"] == 2
        assert returned_description == "set to 2"

    def test_undo_then_new_record_clears_redo_stack(self) -> None:
        history = ChangeHistory()
        project_data = {"value": 1}

        snapshot_before_first = copy.deepcopy(project_data)
        project_data["value"] = 2
        history.record("first", snapshot_before_first, project_data)

        history.undo(project_data)
        assert history.can_redo

        snapshot_before_second = copy.deepcopy(project_data)
        project_data["value"] = 3
        history.record("second", snapshot_before_second, project_data)
        assert not history.can_redo

    def test_undo_empty_raises(self) -> None:
        history = ChangeHistory()
        with pytest.raises(IndexError, match="nothing to undo"):
            history.undo({"x": 1})

    def test_redo_empty_raises(self) -> None:
        history = ChangeHistory()
        with pytest.raises(IndexError, match="nothing to redo"):
            history.redo({"x": 1})

    def test_multiple_undo_redo_cycle(self) -> None:
        history = ChangeHistory()
        project_data = {"counter": 0}

        for step_number in range(1, 4):
            snapshot_before = copy.deepcopy(project_data)
            project_data["counter"] = step_number
            history.record(f"step {step_number}", snapshot_before, project_data)

        assert project_data["counter"] == 3
        history.undo(project_data)
        assert project_data["counter"] == 2
        history.undo(project_data)
        assert project_data["counter"] == 1
        history.redo(project_data)
        assert project_data["counter"] == 2

    def test_clear_empties_both_stacks(self) -> None:
        history = ChangeHistory()
        history.record("x", {"a": 1}, {"a": 2})
        history.clear()
        assert history.undo_count == 0
        assert history.redo_count == 0


class TestChangeRecord:
    def test_is_frozen_dataclass(self) -> None:
        import jsonpatch
        record = ChangeRecord(
            description="test",
            forward_patch=jsonpatch.make_patch({}, {"a": 1}),
            inverse_patch=jsonpatch.make_patch({"a": 1}, {}),
        )
        assert record.description == "test"
        with pytest.raises(AttributeError):
            record.description = "mutated"  # type: ignore[misc]


class TestProjectUndoRedo:
    def test_track_changes_enables_undo(self, project) -> None:
        with project.track_changes("add track"):
            project.timeline.add_track("UndoTest")
        assert project.history.can_undo
        track_count_after_add = project.timeline.track_count

        project.undo()
        assert project.timeline.track_count == track_count_after_add - 1

    def test_redo_after_undo(self, project) -> None:
        original_title = project.title
        with project.track_changes("change title"):
            project.title = "New Title"
        project.undo()
        assert project.title == original_title
        project.redo()
        assert project.title == "New Title"

    def test_track_changes_on_exception_does_not_record(self, project) -> None:
        with pytest.raises(ValueError):
            with project.track_changes("should not record"):
                project.title = "oops"
                raise ValueError("abort")
        assert not project.history.can_undo

    def test_history_descriptions(self, project) -> None:
        with project.track_changes("first edit"):
            project.title = "A"
        with project.track_changes("second edit"):
            project.title = "B"
        assert project.history.descriptions == ["first edit", "second edit"]

    def test_noop_block_not_recorded(self, project) -> None:
        with project.track_changes("no-op"):
            pass  # no mutations
        assert not project.history.can_undo


class TestMaxHistoryDepth:
    def test_max_history_depth_trims_oldest_entries(self) -> None:
        history = ChangeHistory(max_history_depth=3)
        for step_number in range(5):
            before: dict[str, Any] = {"v": step_number}
            after: dict[str, Any] = {"v": step_number + 1}
            history.record(f"step {step_number}", before, after)
        assert history.undo_count == 3
        assert history.descriptions == ["step 2", "step 3", "step 4"]

    def test_default_max_history_depth_is_100(self) -> None:
        history = ChangeHistory()
        assert history.max_history_depth == 100


class TestTotalPatchSizeBytes:
    def test_total_patch_size_bytes_empty(self) -> None:
        history = ChangeHistory()
        assert history.total_patch_size_bytes == 0

    def test_total_patch_size_bytes_includes_both_stacks(self) -> None:
        history = ChangeHistory()
        project_data: dict[str, Any] = {"value": 0}

        snapshot_before: dict[str, Any] = copy.deepcopy(project_data)
        project_data["value"] = 1
        history.record("first", snapshot_before, project_data)

        snapshot_before_second: dict[str, Any] = copy.deepcopy(project_data)
        project_data["value"] = 2
        history.record("second", snapshot_before_second, project_data)

        history.undo(project_data)  # moves "second" to redo stack

        total_size: int = history.total_patch_size_bytes
        assert total_size > 0
        # Both undo (1 entry) and redo (1 entry) contribute
        assert history.undo_count == 1
        assert history.redo_count == 1


class TestWithUndoDecorator:
    def test_with_undo_decorator_records_change(self, project) -> None:
        @with_undo("decorated title change")
        def change_title(proj: Any, new_title: str) -> None:
            proj.title = new_title

        change_title(project, "Decorated")
        assert project.title == "Decorated"
        assert project.history.can_undo
        assert project.history.descriptions[-1] == "decorated title change"

    def test_with_undo_decorator_supports_undo(self, project) -> None:
        original_title: str = project.title

        @with_undo("set title")
        def change_title(proj: Any, new_title: str) -> None:
            proj.title = new_title

        change_title(project, "Changed")
        project.undo()
        assert project.title == original_title

    def test_with_undo_decorator_returns_value(self, project) -> None:
        @with_undo("get title")
        def get_and_set_title(proj: Any, new_title: str) -> str:
            old_title: str = proj.title
            proj.title = new_title
            return old_title

        returned_title: str = get_and_set_title(project, "New")
        assert isinstance(returned_title, str)
