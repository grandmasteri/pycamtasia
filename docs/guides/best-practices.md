# Best Practices

Guidelines for building reliable Camtasia project pipelines with pycamtasia.

## Always validate before saving

Call `project.validate()` before `save()` in production workflows. While `save()` emits warnings for errors, catching issues early prevents corrupted projects:

```python
issues = proj.validate()
errors = [i for i in issues if i.level == "error"]
if errors:
    for e in errors:
        print(f"ERROR: {e.message}")
    raise RuntimeError(f"{len(errors)} validation error(s)")
proj.save()
```

## Use track_changes() for atomic edits

Wrap multi-step edits in `track_changes()` so they can be undone as a single unit. If an exception occurs inside the block, the change is not recorded — but the mutations are *not* rolled back automatically, so pair with undo if you need transactional safety:

```python
with proj.track_changes("add intro sequence"):
    track.add_image(img_id, start_seconds=0, duration_seconds=5.0)
    track.add_audio(audio_id, start_seconds=0, duration_seconds=5.0)
    track.add_transition("FadeThroughBlack", clip_a, clip_b, duration_seconds=0.5)

# One undo reverts all three operations
proj.undo()
```

## Prefer the typed API over raw dict manipulation

Use `Effect` subclasses and typed methods instead of constructing raw dicts. The typed API validates parameter names and provides IDE autocompletion:

```python
# Good — typed, validated
clip.add_drop_shadow(offset=5, blur=10, opacity=0.5)
clip.set_speed(1.5)

# Avoid — fragile, no validation
clip._data["effects"].append({"effectName": "dropShadow", ...})
```

## Don't hand-edit the .tscproj JSON

Always roundtrip through `load_project()` / `save()`. The save method handles Camtasia-specific JSON formatting (NSJSONSerialization style, collapsed scalar arrays, trailing spaces) that hand-editing will break. Camtasia's parser is sensitive to formatting — a missing trailing space can cause `.trec` screen recordings to fail to load.

## Use JSON-patch history for structured change tracking

The `ChangeHistory` system stores RFC 6902 JSON Patch diffs, not full snapshots. This makes it practical to persist and audit every change:

```python
from pathlib import Path

# After a series of edits
Path("audit_log.json").write_text(proj.history.to_json())

# Later — inspect what changed
from camtasia.history import ChangeHistory
history = ChangeHistory.from_json(Path("audit_log.json").read_text())
for desc in history.descriptions:
    print(desc)
```

## Version-control your .cmproj bundles

`.cmproj` bundles are mostly JSON (the `.tscproj` file) plus binary media files. The JSON diffs cleanly in Git. Add binary media files with Git LFS:

```gitattributes
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.trec filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
```

## Use batch operations for bulk edits

When applying the same transformation to many clips, use `camtasia.operations.batch` instead of manual loops. It's cleaner and ensures consistent application:

```python
from camtasia.operations.batch import fade_all, apply_to_all_tracks

# Fade every clip on every track
count = apply_to_all_tracks(proj.timeline, lambda c: c.fade(0.3, 0.3))
print(f"Faded {count} clips")

# Or target a single track
fade_all(proj.timeline.tracks[0].clips, fade_in=0.5, fade_out=0.5)
```

## Test pipelines against the test fixture

The repository includes `tests/fixtures/test_project_a.tscproj` — a comprehensive project with multiple tracks, effects, transitions, groups, and screen recordings. Use it to validate your pipeline handles real-world complexity:

```python
from camtasia import load_project

proj = load_project("tests/fixtures/test_project_a.tscproj")
assert proj.validate() is not None  # should return a list
print(proj.statistics())
```
