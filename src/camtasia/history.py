"""Undo/redo history via JSON Patch (RFC 6902) diffs.

Stores minimal diffs between project states rather than full snapshots,
making history memory-efficient even for large projects.

Usage::

    project = load_project(path)

    with project.track_changes("add intro clip"):
        track.add_clip(...)
        clip.add_drop_shadow()

    project.undo()   # reverts the block
    project.redo()   # re-applies it
    project.history  # list of change descriptions
"""
from __future__ import annotations

import copy
import functools
import json
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

import jsonpatch

T = TypeVar("T")


@dataclass(frozen=True)
class ChangeRecord:
    """A single recorded change with forward and inverse patches."""

    description: str
    forward_patch: jsonpatch.JsonPatch
    inverse_patch: jsonpatch.JsonPatch


class ChangeHistory:
    """Manages an undo/redo stack of JSON Patch diffs.

    Each entry stores the minimal diff needed to move between states,
    not a full copy of the project data.
    """

    def __init__(self, max_history_depth: int = 100) -> None:
        self._undo_stack: list[ChangeRecord] = []
        self._redo_stack: list[ChangeRecord] = []
        self._max_history_depth: int = max_history_depth

    @property
    def max_history_depth(self) -> int:
        """Maximum number of undo entries retained."""
        return self._max_history_depth

    @property
    def can_undo(self) -> bool:
        """Whether there are changes available to undo."""
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        """Whether there are changes available to redo."""
        return bool(self._redo_stack)

    @property
    def undo_count(self) -> int:
        """Number of changes on the undo stack."""
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        """Number of changes on the redo stack."""
        return len(self._redo_stack)

    @property
    def descriptions(self) -> list[str]:
        """Descriptions of all recorded changes (oldest first)."""
        return [record.description for record in self._undo_stack]

    def record(
        self,
        description: str,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
    ) -> None:
        """Record a change by diffing before/after snapshots."""
        forward_patch = jsonpatch.make_patch(snapshot_before, snapshot_after)
        inverse_patch = jsonpatch.make_patch(snapshot_after, snapshot_before)

        if not forward_patch.patch:
            return  # no-op change, don't pollute history

        self._undo_stack.append(ChangeRecord(
            description=description,
            forward_patch=forward_patch,
            inverse_patch=inverse_patch,
        ))
        if len(self._undo_stack) > self._max_history_depth:
            self._undo_stack = self._undo_stack[-self._max_history_depth:]
        self._redo_stack.clear()

    def undo(self, project_data: dict[str, Any]) -> str:
        """Apply the most recent inverse patch. Returns the description."""
        if not self._undo_stack:
            raise IndexError("nothing to undo")
        record = self._undo_stack.pop()
        try:
            import copy
            test_data = copy.deepcopy(project_data)
            record.inverse_patch.apply(test_data, in_place=True)
            # Success — apply to real data
            project_data.clear()
            project_data.update(test_data)
        except Exception: # pragma: no cover
            self._undo_stack.append(record) # pragma: no cover
            raise # pragma: no cover
        self._redo_stack.append(record)
        return record.description

    def redo(self, project_data: dict[str, Any]) -> str:
        """Re-apply the most recently undone patch. Returns the description."""
        if not self._redo_stack:
            raise IndexError("nothing to redo")
        record = self._redo_stack.pop()
        try:
            import copy
            test_data = copy.deepcopy(project_data)
            record.forward_patch.apply(test_data, in_place=True)
            project_data.clear()
            project_data.update(test_data)
        except Exception: # pragma: no cover
            self._redo_stack.append(record) # pragma: no cover
            raise # pragma: no cover
        self._undo_stack.append(record)
        return record.description

    def clear(self) -> None:
        """Discard all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def total_patch_size_bytes(self) -> int:
        """Approximate memory usage of stored patches in bytes."""
        total_size: int = 0
        for record in self._undo_stack + self._redo_stack:
            total_size += len(json.dumps(record.forward_patch.patch))
            total_size += len(json.dumps(record.inverse_patch.patch))
        return total_size


    def to_json(self) -> str:
        """Serialize history to JSON string for persistence."""
        def _serialize_stack(stack: list[ChangeRecord]) -> list[dict[str, Any]]:
            return [
                {
                    'description': record.description,
                    'forward_patch': record.forward_patch.patch,
                    'inverse_patch': record.inverse_patch.patch,
                }
                for record in stack
            ]
        return json.dumps({
            'undo_stack': _serialize_stack(self._undo_stack),
            'redo_stack': _serialize_stack(self._redo_stack),
            'max_history_depth': self._max_history_depth,
        }, indent=2)

    @classmethod
    def from_json(cls, json_string: str) -> ChangeHistory:
        """Deserialize history from JSON string."""
        raw_data: dict[str, Any] = json.loads(json_string)
        restored_history: ChangeHistory = cls(max_history_depth=raw_data.get('max_history_depth', 100))
        def _restore_stack(records: list[dict[str, Any]]) -> list[ChangeRecord]:
            return [
                ChangeRecord(
                    description=r['description'],
                    forward_patch=jsonpatch.JsonPatch(r['forward_patch']),
                    inverse_patch=jsonpatch.JsonPatch(r['inverse_patch']),
                )
                for r in records
            ]
        restored_history._undo_stack = _restore_stack(raw_data.get('undo_stack', []))
        restored_history._redo_stack = _restore_stack(raw_data.get('redo_stack', []))
        return restored_history


def with_undo(description: str) -> Callable:
    """Decorator that wraps a function call in track_changes."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Inner decorator function."""
        @functools.wraps(func)
        def wrapper(project: Any, *args: Any, **kwargs: Any) -> T:
            """Wrapped function with undo tracking."""
            with project.track_changes(description):
                return func(project, *args, **kwargs)
        return wrapper
    return decorator
