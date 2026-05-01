# Troubleshooting

Common issues and how to resolve them.

## FileNotFoundError on .cmproj

**Symptom:** `FileNotFoundError: [Errno 2] No such file or directory: 'project.cmproj/project.tscproj'`

**Cause:** On macOS, `.cmproj` is a *bundle directory* containing a `project.tscproj` JSON file plus media assets. If you pass a bare `.tscproj` file path, pycamtasia looks for the bundle structure.

**Fix:** Pass the `.cmproj` directory path, not the inner `.tscproj` file:

```python
# Correct — point to the bundle directory
proj = load_project("my-video.cmproj")

# Also correct — point directly to the .tscproj file
proj = load_project("my-video.cmproj/project.tscproj")
```

If you only have a standalone `.tscproj` file (no bundle), pass its path directly.

## Validation warnings after save

**Symptom:** `UserWarning: [error] ...` printed during `save()`.

**Cause:** `save()` runs `validate()` internally and emits warnings for any errors found (orphaned media, duplicate IDs, zero-range audio, etc.).

**Fix:** Run `validate()` before saving and fix the issues:

```python
issues = proj.validate()
for issue in issues:
    print(f"[{issue.level}] {issue.message}")

# Fix common issues automatically
proj.repair()
proj.save()
```

## pymediainfo not installed

**Symptom:** `import_media()` falls back to ffprobe, or media metadata (duration, dimensions) is missing.

**Cause:** pymediainfo is an optional dependency that provides more accurate media probing.

**Fix:** Install the media extra:

```bash
pip install pycamtasia[media]
# or install pymediainfo directly:
pip install pymediainfo
```

You also need the MediaInfo shared library. On macOS: `brew install mediainfo`. On Ubuntu: `apt install libmediainfo0v5`.

## Transitions emit schema warnings

**Symptom:** `validate_schema()` reports warnings about transition fields.

**When to ignore:** Transitions created by pycamtasia use a minimal field set. Camtasia itself adds extra fields (like `guid`, `parameters`) on first open. These schema warnings are cosmetic — Camtasia will open the project fine and fill in the missing fields.

**When to investigate:** If `validate()` (not `validate_schema()`) reports transition errors like "stale transition references clip ID that doesn't exist", a clip was deleted without cleaning up its transitions. Fix with:

```python
proj.repair()  # removes stale transitions automatically
```

## Camtasia can't open my saved project

**Debugging steps:**

1. **Run validate:** `proj.validate()` checks for structural issues (duplicate IDs, missing sources, overlapping clips).
2. **Run schema validation:** `proj.validate_schema()` checks against the JSON schema derived from 93 TechSmith sample projects.
3. **Check the JSON:** Open `project.tscproj` in a text editor and look for `NaN`, `Infinity`, or malformed arrays.
4. **Try repair:** `proj.repair()` fixes stale transitions and 1-tick overlaps from rounding.
5. **Compare with a known-good project:** Use `proj.diff(good_project)` to find structural differences.

## Effects don't appear after save

**Symptom:** You added an effect via `add_effect()` with a raw dict, but Camtasia ignores it.

**Cause:** Effect parameter names must match Camtasia's internal names exactly. Fixture-unverified effects (those not in the test fixtures) may have incorrect parameter names.

**Fix:** Use the typed API instead of raw dicts:

```python
# Preferred — typed API validates parameter names
clip.add_drop_shadow(offset=5, blur=10, opacity=0.5)
clip.add_round_corners(radius=12.0)

# If you must use raw dicts, inspect a working project's JSON
# to find the correct effectName and parameter keys
```

Check `EffectName` enum values for supported effect names:

```python
from camtasia.types import EffectName
print(list(EffectName))
```

## Audio duration mismatch warnings in screenplay builder

**Symptom:** `build_from_screenplay()` warns about audio duration not matching expected duration.

**Cause:** The screenplay specifies a duration for an audio segment, but the actual audio file has a different length. This happens when audio was re-recorded without updating the screenplay.

**Fix:** Either update the screenplay durations to match the audio files, or let the builder use the actual audio duration by omitting explicit durations in the screenplay.

## How to recover from an undo-stack overflow

**Symptom:** `project.history.undo_count` is at the maximum (default 100) and old changes are lost.

**Fix:** The history depth is configurable. Increase it before making changes:

```python
from camtasia.history import ChangeHistory

proj.history = ChangeHistory(max_history_depth=500)
```

To persist history across sessions so nothing is lost:

```python
from pathlib import Path

# Save
Path("history.json").write_text(proj.history.to_json())

# Restore
proj.history = ChangeHistory.from_json(Path("history.json").read_text())
```
