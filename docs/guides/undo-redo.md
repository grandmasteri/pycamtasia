# Undo & Redo

pycamtasia records project changes as JSON Patch diffs (RFC 6902), giving you
memory-efficient undo/redo without full-project snapshots.

## Tracking changes

Wrap edits in `track_changes` to record them as a single undoable unit:

```python
from camtasia import load_project

project = load_project("demo.cmproj")
track = project.timeline.tracks[0]

with project.track_changes("add intro clip"):
    track.add_video(media.id, start_seconds=0, duration_seconds=5.0)

with project.track_changes("apply drop shadow"):
    clip = track.clips[0]
    clip.add_drop_shadow()
```

Each `track_changes` block captures a before/after diff. If nothing actually
changed inside the block, no history entry is created.

## Undo and redo

```python
project.undo()  # reverts "apply drop shadow"
project.undo()  # reverts "add intro clip"
project.redo()  # re-applies "add intro clip"
```

Check what's available:

```python
project.history.can_undo   # True/False
project.history.can_redo   # True/False
project.history.descriptions  # ["add intro clip", ...]
```

## Persisting history

Save history to disk alongside your project so users can undo across sessions:

```python
# Save
history_json = project.history.to_json()
Path("project_history.json").write_text(history_json)

# Restore
from camtasia.history import ChangeHistory

saved = Path("project_history.json").read_text()
project.history = ChangeHistory.from_json(saved)
```

## The `@with_undo` decorator

For functions that always modify a project, use the decorator shorthand:

```python
from camtasia.history import with_undo

@with_undo("normalize audio levels")
def normalize_audio(project):
    for track in project.timeline.tracks:
        for clip in track.clips:
            clip.gain = 0.0
```

Calling `normalize_audio(project)` automatically wraps the body in
`track_changes`.

## Memory efficiency

History stores only the JSON diffs, not full project copies. Check usage with:

```python
project.history.total_patch_size_bytes  # e.g. 4096
project.history.undo_count              # number of undo steps
```

The default limit is 100 entries. Configure it when creating a history:

```python
from camtasia.history import ChangeHistory
project.history = ChangeHistory(max_history_depth=50)
```
