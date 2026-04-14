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
from dataclasses import dataclass, field
from typing import Any

import jsonpatch


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

    def __init__(self) -> None:
        self._undo_stack: list[ChangeRecord] = []
        self._redo_stack: list[ChangeRecord] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    @property
    def undo_count(self) -> int:
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
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
        self._redo_stack.clear()

    def undo(self, project_data: dict[str, Any]) -> str:
        """Apply the most recent inverse patch. Returns the description."""
        if not self._undo_stack:
            raise IndexError("nothing to undo")
        record = self._undo_stack.pop()
        record.inverse_patch.apply(project_data, in_place=True)
        self._redo_stack.append(record)
        return record.description

    def redo(self, project_data: dict[str, Any]) -> str:
        """Re-apply the most recently undone patch. Returns the description."""
        if not self._redo_stack:
            raise IndexError("nothing to redo")
        record = self._redo_stack.pop()
        record.forward_patch.apply(project_data, in_place=True)
        self._undo_stack.append(record)
        return record.description

    def clear(self) -> None:
        """Discard all history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
