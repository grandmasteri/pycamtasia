# Undo and History

pycamtasia records project changes as JSON Patch diffs (RFC 6902), giving you
memory-efficient undo/redo without full-project snapshots.

## How it works

The `ChangeHistory` object maintains two stacks:

- **Undo stack** — changes that can be reverted
- **Redo stack** — changes that were undone and can be re-applied

Each entry is a `ChangeRecord` containing:

- A human-readable `description`
- A `forward_patch` (the diff to apply the change)
- An `inverse_patch` (the diff to revert it)

Patches are computed by diffing the project JSON before and after a change.
Only the minimal diff is stored — not a full copy of the project.

## Tracking changes with `track_changes`

Wrap edits in the `track_changes` context manager to record them as a single
undoable unit:

```python
from camtasia import load_project

project = load_project("demo.cmproj")
track = list(project.timeline.tracks)[0]

with project.track_changes("add intro clip"):
    track.add_video(source_id=1, start_seconds=0, duration_seconds=5.0)

with project.track_changes("apply drop shadow"):
    clip = list(track.clips)[0]
    clip.add_drop_shadow()
```

Each block captures a before/after snapshot. If nothing actually changed inside
the block, no history entry is created.

## Undo and redo

```python
project.undo()  # reverts "apply drop shadow"
project.undo()  # reverts "add intro clip"
project.redo()  # re-applies "add intro clip"
```

**Important:** After undo/redo, any previously-obtained references to nested
project objects (Timeline, Track, clips) become stale. Always re-access project
properties after undo/redo.

## Inspecting history

```python
project.history.can_undo       # True/False
project.history.can_redo       # True/False
project.history.descriptions   # ["add intro clip", "apply drop shadow"]
project.history.undo_count     # number of undo steps available
project.history.redo_count     # number of redo steps available
```

## The `@with_undo` decorator

For functions that always modify a project, use the decorator shorthand:

```python
from camtasia.history import with_undo

@with_undo("normalize audio levels")
def normalize_audio(project):
    for track in project.timeline.tracks:
        for clip in track.clips:
            clip.gain = 0.5
```

Calling `normalize_audio(project)` automatically wraps the body in
`track_changes`.

## Memory efficiency

History stores only the JSON diffs, not full project copies. Check usage:

```python
project.history.total_patch_size_bytes  # approximate memory in bytes
```

The default limit is 100 entries. Older entries are discarded when the limit is
exceeded. Configure it when creating a history:

```python
from camtasia.history import ChangeHistory
project.history = ChangeHistory(max_history_depth=50)
```

## Persisting history across sessions

History can be serialized to JSON for storage alongside the project:

```python
from pathlib import Path
from camtasia.history import ChangeHistory

# Save
history_json = project.history.to_json()
Path("project_history.json").write_text(history_json)

# Restore
saved = Path("project_history.json").read_text()
project.history = ChangeHistory.from_json(saved)
```

The serialized format stores both undo and redo stacks with their patches and
descriptions.

## See also

- {doc}`/concepts/project-model` — the Project object that owns history
- {doc}`/guides/undo-redo` — practical undo/redo guide
- {doc}`/api/history` — full API reference
- {doc}`/concepts/the-two-api-layers` — how mutations flow through the dict
