# AGENTS.md — pycamtasia

## Project Overview

pycamtasia is a Python library for reading, writing, and manipulating TechSmith Camtasia project files (`.cmproj`/`.tscproj`). It wraps the underlying JSON format with typed Python classes, enabling programmatic video assembly without the Camtasia GUI.

Primary use case: assembling demo videos from voiceover audio, diagram images, screen recordings, and title cards via scripts.

- 390+ commits, 1825+ tests, 100% line coverage (`fail_under = 100`)
- Python 3.10+, no required runtime dependencies (optional: `pymediainfo`, `docopt-subcommands`, `jsonpatch>=1.33`)
- Package: `src/camtasia/`, installed as `camtasia`, CLI entry point: `pytsc`

## Architecture

### Data Flow

```
.cmproj bundle (directory)
  └── project.tscproj (JSON)
        ↓ load_project()
      Project
        ├── MediaBin (source files)
        ├── Timeline
        │     └── Track[]
        │           ├── Clip[] (AMFile, VMFile, IMFile, Callout, Group, ...)
        │           │     └── Effect[] (DropShadow, Glow, SourceEffect, ...)
        │           ├── Transition[] (FadeThroughBlack, ...)
        │           └── Marker[]
        └── AuthoringClient (export settings)
        ↓ project.save()
      project.tscproj (JSON written back)
```

All classes are thin wrappers over the JSON dict. Mutations go directly to `_data` — no separate model/serialization step. `project.save()` writes current state.

### Source Layout

```
src/camtasia/
├── project.py              # Project: load/save .cmproj, import_media, validation
├── timing.py               # EDIT_RATE (705600000 ticks/sec), tick↔second conversion, rational scalars
├── color.py                # RGBA, hex_rgb
├── validation.py           # Pre-save checks: duplicate IDs, track indices, transition refs
├── effects.py              # Legacy effect helpers (being replaced by effects/)
├── effects/
│   ├── base.py             # Effect base class, effect_from_dict factory
│   ├── visual.py           # Glow, RoundCorners, DropShadow, Mask, ColorAdjustment, ...
│   ├── source.py           # SourceEffect (shader parameters: gradients, colors)
│   ├── cursor.py           # CursorMotionBlur, CursorShadow, CursorPhysics, LeftClickScaling
│   └── behaviors.py        # Behavior effects (animations)
├── timeline/
│   ├── timeline.py         # Timeline class
│   ├── track.py            # Track: add/remove clips, split, transitions, reorder
│   ├── markers.py          # MarkerList
│   ├── marker.py           # Marker dataclass
│   ├── transitions.py      # Transition, TransitionList
│   ├── captions.py         # Caption support
│   ├── track_media.py      # Low-level track media helpers
│   └── clips/
│       ├── base.py         # BaseClip: id, start, duration, scalar, effects, fade, mute, gain, opacity
│       ├── audio.py        # AMFile
│       ├── video.py        # VMFile
│       ├── image.py        # IMFile
│       ├── screen_recording.py  # ScreenVMFile, ScreenIMFile
│       ├── stitched.py     # StitchedMedia
│       ├── group.py        # Group (compound clips with internal tracks)
│       ├── callout.py      # Callout (text overlays)
│       └── unified.py      # UnifiedMedia
├── media_bin/
│   ├── media_bin.py        # MediaBin, Media, MediaType enum
│   └── trec_probe.py       # .trec file metadata extraction
├── annotations/
│   ├── callouts.py         # Callout definition builders
│   ├── shapes.py           # Shape definitions
│   └── types.py            # Annotation type constants
├── audiate/
│   ├── project.py          # AudiateProject reader
│   └── transcript.py       # Word-level transcript with timestamps
├── operations/
│   ├── speed.py            # rescale_project, set_audio_speed
│   ├── sync.py             # Audio-video sync from transcript + markers
│   ├── merge.py            # Project merging
│   ├── layout.py           # Layout operations
│   ├── batch.py            # Batch operations across clips
│   ├── cleanup.py          # Project cleanup utilities
│   ├── diff.py             # Project diffing
│   └── template.py         # Template-based project creation
├── builders/
│   ├── timeline_builder.py # Fluent timeline construction
│   └── screenplay_builder.py  # Screenplay-driven assembly
├── templates/
│   ├── lower_third.py      # Right Angle Lower Third JSON template
│   └── behavior_presets.py # Animation presets
├── export/
│   ├── edl.py              # EDL export
│   ├── srt.py              # SRT subtitle export
│   ├── report.py           # Project report generation
│   └── timeline_json.py    # Timeline JSON export
├── screenplay.py           # Screenplay parser
├── cli.py                  # CLI entry point (pytsc)
├── frame_stamp.py          # Frame stamping utilities
├── extras.py               # Miscellaneous helpers
├── app_validation.py       # Camtasia app-level validation
├── authoring_client.py     # Export/authoring settings
└── resources/              # Bundled template projects (new.cmproj, simple-video.cmproj)
```

### Two API Layers

- **L2 (high-level)**: `clip.fade(0.5, 0.5)`, `track.add_lower_third(...)`, `proj.import_media(path)`. Use this.
- **L1 (low-level)**: `clip._data` dict access. Escape hatch only. Never use in consumer code — if you need something L2 doesn't expose, add it to the library first.

## Key Conventions — MUST FOLLOW

### 1. Clip mutations MUST cascade-delete transitions

When removing a clip from a track, all transitions referencing that clip's ID (as `leftMedia` or `rightMedia`) must be removed. `track.remove_clip()` handles this. Never delete clips by directly mutating `track._data['medias']` — use the API.

See: `tests/test_remove_clip_cascade.py`

### 2. Parameter keys use hyphens, not underscores

Camtasia's JSON uses hyphenated parameter keys: `mask-shape`, `mask-opacity`, `top-left`, `bottom-right`. Python properties map these with underscores (`mask_shape`), but the underlying dict keys MUST use hyphens.

```python
# CORRECT — hyphenated keys in the dict
{"mask-shape": {"defaultValue": 2, "type": "double", "interp": "linr"}}

# WRONG — underscored keys will be silently ignored by Camtasia
{"mask_shape": {"defaultValue": 2, "type": "double", "interp": "linr"}}
```

See: `tests/test_effect_key_fixes.py`

### 3. Effects use plain scalar format

Effect parameter values use the plain scalar format — a flat dict with `defaultValue`, `type`, `interp`. NOT a dict-wrapped or nested structure.

```python
# CORRECT
{"defaultValue": 16.0, "type": "double", "interp": "linr"}

# WRONG — dict-wrapped
{"value": {"defaultValue": 16.0, "type": "double", "interp": "linr"}}
```

### 4. Camtasia integration testing is mandatory

Any change that affects `.tscproj` output MUST be validated by opening the result in Camtasia. The JSON format is reverse-engineered — there is no spec. Camtasia silently ignores some errors and crashes on others.

Run: `scripts/camtasia_validate.sh` (requires macOS with Camtasia installed)

### 5. Never guess at JSON format

Always reverse-engineer from real Camtasia output:
1. Perform the action in Camtasia GUI
2. Diff the project JSON before/after
3. Implement based on findings

### 6. Library-first moratorium

No raw `_data` access in consumer/assembly scripts. If pycamtasia doesn't support an operation, implement it in the library first, then use the API.

### Documentation Consistency
Every commit that changes source code MUST include corresponding documentation updates. This includes:
- Docstrings on new/changed public methods
- Updates to relevant docs/guides/ if behavior changes
- Updates to docs/api/*.rst if new modules are added
- README feature list updates for user-facing additions
- CHANGELOG.md entries for all changes

Documentation must never go stale. If a PR changes the API, the docs changes are part of the same commit, not a follow-up.

## Running Tests

```bash
# All unit tests (excludes integration by default)
PYTHONPATH=src python3 -m pytest tests/ -q

# Parallel execution
PYTHONPATH=src python3 -m pytest tests/ -n auto -q

# With coverage (must stay at 100%)
PYTHONPATH=src python3 -m pytest tests/ --cov=camtasia --cov-report=term-missing

# Integration tests only (requires Camtasia app on macOS)
PYTHONPATH=src python3 -m pytest tests/ -m integration

# Hypothesis property-based tests (included in default run)
# Configured via .hypothesis/ directory, auto-discovered by pytest

# Single test file
PYTHONPATH=src python3 -m pytest tests/test_transitions.py -q

# Timeout: 10s per test (configured in pyproject.toml)
```

Key pytest config from `pyproject.toml`:
- `addopts = "-m 'not integration'"` — integration tests excluded by default
- `timeout = 10` — per-test timeout
- `markers = ["integration: Camtasia integration tests (slow, requires Camtasia app)"]`

## Camtasia Validation

```bash
# Full validation: rebuild project, run assembly, launch Camtasia, check for exceptions
./scripts/camtasia_validate.sh
```

Requirements: macOS, `/Applications/Camtasia.app`.

The script:
1. Runs the assembly script (if found)
2. Launches Camtasia with the project
3. Checks stderr for EXCEPTION lines
4. Reports PASS (0 exceptions) or FAIL

## Common Pitfalls

### Transition cascade bug
Removing a clip without removing its transitions leaves dangling references. Camtasia crashes or silently corrupts the project. Always use `track.remove_clip()` which cascade-deletes.

### Hyphenated parameter keys
Using `mask_shape` instead of `mask-shape` in effect parameter dicts. Camtasia silently ignores the parameter — the effect appears to do nothing. Python properties handle the mapping, but if you're constructing dicts manually, use hyphens.

### Effect scalar format
Wrapping effect parameters in an extra dict layer. Camtasia expects flat `{"defaultValue": ..., "type": ..., "interp": ...}` dicts.

### Opacity fade keyframe pattern
Camtasia v10 uses a target-value pattern with 2 keyframes + 2 visual segments. `defaultValue: 0.0` means the clip starts invisible. Don't use start/end value patterns.

### JSON formatting on save
Camtasia expects `" : "` (spaces around colon), not `": "`. Scalar arrays must be on one line. `-Infinity` in JSON crashes the parser — `save()` handles this automatically.

### Callout collision
Callouts on the same track at the same time cause a "Collision exception" in Camtasia. Place them on separate tracks or ensure no temporal overlap.

### Group clip viewing window
Groups contain internal tracks. `mediaStart`/`mediaDuration` act as a viewing window into the group's internal timeline — they don't define the group's content duration.

### Duplicate clip IDs
Every clip ID must be unique across the entire project. The validation module checks this before save. Use `project.next_id()` for new clips.

## File Structure Overview

```
pycamtasia/
├── src/camtasia/           # Library source (the package)
├── tests/                  # 100+ test files, 1825+ tests
│   ├── conftest.py         # Fixtures: project, simple_video, test_project_a_data
│   └── fixtures/           # .tscproj files and .wav files for testing
├── scripts/
│   └── camtasia_validate.sh  # Integration validation script
├── docs/                   # Sphinx documentation
│   ├── api/                # API reference (.rst)
│   └── guides/             # User guides (.md)
├── pyproject.toml          # Build config, test config, coverage config
├── ARCHITECTURE.md         # Detailed architecture design doc
├── ROADMAP.md              # Planned and completed features
├── CHANGELOG.md            # Version history
└── AGENTS.md               # This file
```

### Test Fixtures

- `tests/fixtures/test_project_a.tscproj` — Large real-world project (2.7MB)
- `tests/fixtures/test_project_b.tscproj` — Medium project (1.1MB)
- `tests/fixtures/test_project_c.tscproj` — Small project (241KB)
- `tests/fixtures/test_project_d.tscproj` — Additional test project
- `tests/fixtures/techsmith_sample.tscproj` — TechSmith sample project (695KB)
- `tests/fixtures/techsmith_library_asset.tscproj` — Library asset project
- `tests/fixtures/empty.wav`, `empty2.wav` — Audio fixtures for media tests
- `src/camtasia/resources/new.cmproj` — Blank template project
- `src/camtasia/resources/simple-video.cmproj` — Simple video template
