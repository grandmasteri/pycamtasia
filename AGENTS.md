# AGENTS.md — pycamtasia

## Meta: Keeping AGENTS.md Current

This file is the single source of truth for how to develop this library. When the user states a preference, convention, or decision during conversation, it MUST be encoded here immediately — not just followed in the moment. Any agent reading this file should have the complete, up-to-date understanding of how to work on this codebase without needing conversation history.

## Guiding Principle: Follow Top Python Libraries

When making decisions about project structure, testing patterns, API design, tooling, or conventions, follow the best practices established by top professional Python libraries (pydantic, rich, httpx, fastapi, pandas). Don't invent novel patterns — use what the ecosystem has proven works. When in doubt, check how these libraries handle the same situation.

Concrete implications:
- Use pytest (the universal standard)
- Flat `tests/` directory with one file per module/feature (appropriate for our size)
- Test file naming mirrors source modules, not meta-reasons (`test_track.py`, not `test_coverage_gaps.py`)
- Follow PEP 8, use type hints, use `pyproject.toml` for tool config where possible

## Project Overview

pycamtasia is a Python library for reading, writing, and manipulating TechSmith Camtasia project files (`.cmproj`/`.tscproj`). It wraps the underlying JSON format with typed Python classes, enabling programmatic video assembly without the Camtasia GUI.

Primary use case: assembling demo videos from voiceover audio, diagram images, screen recordings, and title cards via scripts.

- 620+ commits, 2616+ tests, 96% line coverage (`fail_under = 96`), 0 mypy errors, 93+ TechSmith samples validated
- Python 3.10+, required: `jsonpatch>=1.33`; optional: `pymediainfo`, `docopt-subcommands`
- Package: `src/camtasia/`, installed as `camtasia`, CLI entry point: `pytsc`
- Hardened through 106 rounds of adversarial code review

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
        │           │     └── Effect[] (DropShadow, Glow, SourceEffect, GenericBehaviorEffect, ...)
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
├── project.py              # Project: load/save .cmproj, import_media, validation, group_clips_across_tracks
├── timing.py               # EDIT_RATE (705600000 ticks/sec), tick↔second conversion, Fraction-based scalars
├── color.py                # RGBA, hex_rgb
├── validation.py           # validate_all(): duplicate IDs, track indices, transition refs, src refs
├── effects/
│   ├── base.py             # Effect base class, effect_from_dict factory
│   ├── visual.py           # Glow, RoundCorners, DropShadow, Mask, ColorAdjustment, ...
│   ├── source.py           # SourceEffect (shader parameters: gradients, colors)
│   ├── cursor.py           # CursorMotionBlur, CursorShadow, CursorPhysics, LeftClickScaling
│   └── behaviors.py        # GenericBehaviorEffect(Effect) — text behavior animations
├── timeline/
│   ├── timeline.py         # Timeline class, group_clips_across_tracks
│   ├── track.py            # Track: add/remove clips, split, transitions, reorder
│   ├── markers.py          # MarkerList
│   ├── marker.py           # Marker dataclass
│   ├── transitions.py      # Transition, TransitionList (add supports rightMedia-only)
│   ├── captions.py         # Caption support
│   └── clips/
│       ├── base.py         # BaseClip: id, start, duration, scalar, effects, fade, mute, gain, opacity, is_video
│       ├── audio.py        # AMFile
│       ├── video.py        # VMFile
│       ├── image.py        # IMFile
│       ├── screen_recording.py  # ScreenVMFile, ScreenIMFile
│       ├── stitched.py     # StitchedMedia
│       ├── group.py        # Group (compound clips with internal tracks)
│       ├── callout.py      # Callout (text overlays)
│       └── unified.py      # UnifiedMedia
├── media_bin/
│   ├── media_bin.py        # MediaBin, Media (range returns tuple[int,int], dimensions returns ints), next_id
│   └── trec_probe.py       # .trec file metadata extraction
├── annotations/
│   ├── callouts.py         # Callout definition builders
│   ├── shapes.py           # Shape definitions
│   └── types.py            # Annotation type constants
├── audiate/
│   ├── project.py          # AudiateProject reader
│   └── transcript.py       # Word-level transcript with timestamps
├── operations/
│   ├── speed.py            # rescale_project, set_audio_speed, set_internal_segment_speeds
│   ├── sync.py             # Audio-video sync from transcript + markers
│   ├── merge.py            # Project merging
│   ├── layout.py           # Layout operations
│   ├── batch.py            # Batch operations across clips
│   ├── cleanup.py          # Project cleanup utilities
│   ├── diff.py             # Project diffing
│   └── template.py         # Template-based project creation
├── builders/
│   ├── timeline_builder.py # Fluent timeline construction
│   └── screenplay_builder.py  # Screenplay-driven assembly (interleaves pauses correctly)
├── templates/
│   ├── lower_third.py      # Right Angle Lower Third JSON template (pre-flattened for Camtasia)
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
└── resources/              # Bundled template projects (new.cmproj ~12KB), schema
    └── camtasia-project-schema.json  # JSON Schema for .tscproj validation
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

### 4. Scalar convention: scalar = 1/speed

Camtasia stores speed as a **scalar** (timeline_duration / source_duration). Faster playback means a smaller scalar:

- 1x speed → scalar = 1
- 2x speed → scalar = 1/2
- 0.5x speed → scalar = 2

Use `speed_to_scalar(speed)` and `scalar_to_speed(scalar)` from `timing.py`. Both raise `ValueError` on zero input. Scalars are `Fraction`-based for exact rational arithmetic — no floating-point drift.

`_parse_scalar()` in `track.py` delegates to `timing.parse_scalar()` for consistent Fraction-based parsing across the codebase.

### 5. Camtasia integration testing is mandatory

Any change that affects `.tscproj` output MUST be validated by opening the result in Camtasia. The JSON format is reverse-engineered — there is no spec. Camtasia silently ignores some errors and crashes on others.

**Before/after testing process:**
1. Save the project JSON before your change (backup)
2. Apply your change and save
3. Open in Camtasia — check for exceptions, visual correctness, playback
4. Compare JSON diff to verify only intended changes were made

Run: `scripts/camtasia_validate.sh` (requires macOS with Camtasia installed)

### 6. Never guess at JSON format

Always reverse-engineer from real Camtasia output:
1. Perform the action in Camtasia GUI
2. Diff the project JSON before/after
3. Implement based on findings

### 7. Library-first moratorium

No raw `_data` access in consumer/assembly scripts. If pycamtasia doesn't support an operation, implement it in the library first, then use the API.

### 8. Adversarial review process

This library was hardened through 106 rounds of adversarial review, uncovering numerous bugs across edge cases, format assumptions, and silent data corruption paths. Any new feature or format change should be subjected to the same scrutiny: assume the format is hostile, test boundary conditions, and verify round-trip fidelity against real Camtasia output.

### 9. Documentation Consistency

Every commit that changes source code MUST include corresponding documentation updates. This includes:
- Docstrings on new/changed public methods
- Updates to relevant docs/guides/ if behavior changes
- Updates to docs/api/*.rst if new modules are added
- README feature list updates for user-facing additions
- CHANGELOG.md entries for all changes

Documentation must never go stale. If a PR changes the API, the docs changes are part of the same commit, not a follow-up.

### 10. No legacy APIs — delete immediately

If a module is fully replaced by a newer implementation, delete the old one immediately. No external users means zero backward compatibility burden.

### 11. Verify before fixing

When adversarial reviewers report bugs, read the actual source code and verify the bug exists before applying a fix. Reviewers can hallucinate or misread code.

## Code Style & Engineering Principles

### Efficiency Principle

When multiple approaches produce the same outcome, choose the most efficient one. Use shell commands for bulk operations instead of individual tool calls, prefer built-in OS operations over manual reconstruction. Don't do extra work when a simpler path exists.

### Cognitive Load

Code should minimize cognitive load — the average person holds ~4 chunks in working memory.

- **Deep modules over shallow ones**: Prefer fewer modules with simple interfaces and complex internals. Don't split code into many small functions just to satisfy a line count rule — split when it genuinely reduces cognitive load.
- **Complex conditionals → intermediate variables**: Extract named booleans for multi-part conditions.
- **Early returns over nested ifs**: Handle preconditions first, then the happy path.
- **A little copying is better than a little dependency**: Don't over-apply DRY across unrelated modules. Some duplication is healthier than a shared abstraction that constrains both.
- **No unnecessary abstraction layers**: Add layers only when justified by a practical extension point, not for architectural aesthetics.
- **Don't weaken source code to accommodate tests**: If a parameter should be required, keep it required — don't add `Optional` defaults just so tests can skip passing it.
- **Familiarity ≠ simplicity**: Code that feels easy because you wrote it may be hard for newcomers.

### Type Safety

Prefer the strongest, most specific type available. Weak types push validation to runtime; strong types centralize it at construction time.

- `Fraction` over `float` for tick arithmetic (exact rational math)
- Enums over literal strings for fixed value sets
- `X | None` over `Optional[X]` (PEP 604)
- `dict[str, Any]`, `list[str]` over `Dict`, `List` from `typing` (PEP 585)
- Parameterized generics (`list[str]`) over bare generics (`list`)

### Structured Docstrings

Functions with 3+ parameters, non-obvious return types, or explicit exception raising must have Google-style docstring sections (`Args:`, `Returns:`, `Raises:`). One-liner summaries are fine for simple, self-explanatory functions. Docstrings describe *what* and *contract* — not *why a standard pattern was chosen*.

### Error Handling

Two-tier approach:
- **Tier 1 — Isolatable errors → partial success**: If an error can be isolated to a single clip, track, or operation, handle it gracefully and continue. Return as much correct information as possible.
- **Tier 2 — Fundamental deviations → fail immediately**: If the system has fundamentally deviated from expectations (missing project file, corrupt JSON structure), fail with a clear error. Don't guess.

## Testing Standards

### Assertion Strength Tiers

**Tier 1 — Full object comparison** (for tests verifying complete output shape): Build the complete expected object, single `actual == expected` assertion.

**Tier 2 — Targeted property assertions** (for tests verifying a specific behavior): Assert the specific property precisely, don't build the entire expected object when most of it is irrelevant.

### Key Assertion Rules

- `assert len(x) == N` where N > 0 is always wrong — verify the content
- `assert x == []` is preferred over `assert len(x) == 0`
- `assert X in collection` repeated N times → use `assert set(collection) == {X, Y, ...}`
- Use exact values, not `>=` or approximate comparisons

### Descriptive Variable Naming

Use names that convey role: `actual_result`, `expected_result`, `actual_clips`, `expected_duration`.

### Parameterized Tests

Use `@pytest.mark.parametrize` for multiple cases. Select valuable cases at boundaries and transitions — avoid redundant mid-range cases.

### Test Efficiency

Quality is the primary goal — every test must verify real behavior with strong assertions. But given that bar is met, fewer tests covering the same logic is better than more. Redundant tests add maintenance burden, slow the suite, and dilute signal when something fails.

- If two tests verify the same code path with different inputs, parametrize into one
- If a test is a strict subset of another test (same assertions plus more), remove the subset
- Never delete a test that covers a unique code path just to reduce count
- Priority order: correctness > coverage > clarity > efficiency

### Test Organization

- Test files mirror the source layout: `src/camtasia/timeline/track.py` → `tests/test_track.py`, `src/camtasia/operations/speed.py` → `tests/test_speed.py`. New tests go in the existing file for that module — never in grab-bag files like `test_coverage_gaps.py` or `test_coverage_100.py`.
- Name test classes by category (`TestScalarArithmetic`, `TestGroupOperations`), not meta-details (`TestCoverageGaps`, `TestRound95Fixes`)
- Colocate related tests in the same class/file

### Python Conventions

- **Imports**: All imports at top of file (PEP 8). Function-level imports only for circular import avoidance or expensive/optional dependencies.
- **Concise**: Avoid unnecessary verbosity; express logic in the most direct way possible.
- **Idiomatic**: Follow PEP 8 conventions.
- **No redundant information in data models**: Don't include fields derivable from other fields in the same model.

## Subagent Parallelism

### Maximize Parallelism Through Divide and Conquer

Break work into the smallest independent units and run them simultaneously. The only reason to sequence tasks is a true dependency — one task's output is another task's input. If no such dependency exists, the tasks MUST run in parallel.

### Preserve the Orchestrator's Context Window

The orchestrator coordinates — it never implements. Subagents absorb the token cost of reading files, researching, and reasoning. Only conclusions flow back. Even when parallelism isn't possible, delegation is still valuable because it preserves context.

### When to Delegate vs Do Directly

Delegate when there's **leverage** — the subagent reads/reasons over significantly more tokens than the prompt+response cost. Do it yourself when the prompt overhead ≈ the work itself.

- Large file edits across many files → delegate (high leverage)
- Reading docs/code to answer a question → delegate (saves context)
- Adversarial review of code → delegate (fresh eyes, isolated context)
- Small single-file edit you already know how to make → do directly (no leverage)
- Appending a known block of text to a file → do directly (no leverage)

### File Boundary Rules

Each subagent owns specific files exclusively. No two subagents touch the same file in the same phase. If unavoidable, sequence the modifications or consolidate into one subagent.

### Mandatory Verification Phase

Every implementation phase MUST be followed by verification (mypy + pytest). Verify at checkpoints, not batched at the end. For adversarial review, use separate verification subagents — the implementer is biased.

### Subagent Failure Handling

1. Assess the failure (transient vs substantive)
2. Re-task a new subagent with original instructions + failure details
3. If re-tasking fails twice, report to user
4. Don't absorb the failure — resist doing it yourself

## Running Tests

Tests run in **parallel** via `pytest-xdist` (`-n auto` in `pyproject.toml`). Each test uses an **isolated temporary copy** of the template project via `tempfile.TemporaryDirectory` / `tmp_path` — no test ever mutates the shared template fixtures.

```bash
# All unit tests — parallel by default (configured in pyproject.toml: addopts = "-n auto")
PYTHONPATH=src python3 -m pytest tests/ -q

# Serial execution (useful for debugging)
PYTHONPATH=src python3 -m pytest tests/ -n0 -q

# With coverage (CI uses -n0 for accurate coverage collection)
PYTHONPATH=src python3 -m pytest tests/ -n0 --cov=camtasia --cov-report=term-missing

# Integration tests only (requires Camtasia app on macOS)
PYTHONPATH=src python3 -m pytest tests/ -m integration

# Hypothesis property-based tests (included in default run)
# Configured via .hypothesis/ directory, auto-discovered by pytest

# Single test file
PYTHONPATH=src python3 -m pytest tests/test_transitions.py -q

# Timeout: 10s per test (configured in pyproject.toml)
```

### Test conventions

- **Parallel-safe**: All tests run under `-n auto`. No shared mutable state between tests.
- **Isolated copies**: The `project` fixture in `conftest.py` copies `new.cmproj` into `tmp_path` before loading. Tests that need a project MUST use this fixture or create their own temp copy — never load templates in-place.
- **No template pollution**: The template at `src/camtasia/resources/new.cmproj` must stay clean (~12KB). The `media/` directory is gitignored. If a test creates media files, they go in `tmp_path`.
- **Coverage**: 96% line coverage enforced (`fail_under = 96`). CI runs with `-n0` and `--cov`.
- **Temp path cleanup**: `tmp_path_retention_policy = "none"` — pytest cleans up temp dirs after each run.

Key pytest config from `pyproject.toml`:
- `addopts = "-n auto -m 'not integration'"` — parallel, integration tests excluded by default
- `timeout = 10` — per-test timeout
- `tmp_path_retention_policy = "none"` — no leftover temp dirs

### Template cleanup

The template project at `src/camtasia/resources/new.cmproj` should stay at ~12KB. The `media/` subdirectory is gitignored (pattern: `src/camtasia/resources/new.cmproj/media/`). If media files accumulate during development:

```bash
# Clean template media dir (safe — gitignored files only)
rm -rf src/camtasia/resources/new.cmproj/media/*
touch src/camtasia/resources/new.cmproj/media/.gitkeep
```

## API Surface — Recent Changes

### New methods

- `Timeline.group_clips_across_tracks(clip_ids, target_track_index, ...)` — groups clips from different tracks into a single Group clip
- `Project.group_clips_across_tracks(clip_ids, target_track_name, ...)` — project-level wrapper for cross-track grouping
- `TransitionList.add(...)` — now supports rightMedia-only transitions (no leftMedia required); validates at least one clip ID provided
- `MediaBin.next_id()` — scans entire project (sourceBin IDs + clip IDs + timeline ID) to avoid collisions

### Changed methods/behavior

- `Project.validate()` — delegates to `validate_all()` for comprehensive structural checks (duplicate IDs, track indices, transition refs, src refs, trackAttributes count)
- `Media.range` — returns `tuple[int, int]`; guards against empty `sourceTracks`
- `Media.dimensions` — returns `int` values (not float)
- `BaseClip.is_video` — now includes `UnifiedMedia` and video-containing `StitchedMedia`
- `_parse_scalar()` (track.py) — delegates to `timing.parse_scalar()` for Fraction-based parsing
- `speed_to_scalar()` / `scalar_to_speed()` — raise `ValueError` on zero input
- `format_duration()` — rounds centiseconds with `min(99, round(...))` to avoid `100` overflow
- `set_internal_segment_speeds()` — uses integer tick accumulator and correct scalar formula
- `ScreenplayBuilder` — interleaves pauses at correct positions in the timeline

### Type/class changes

- `GenericBehaviorEffect` now inherits from `Effect` (was standalone)
- `IntEncodedTime` deleted — `Media.range` returns plain `tuple[int, int]`

### Schema changes

- Version field relaxed: accepts any string (not just specific versions)
- `bool` and `textAttributeList` added to allowed parameter types

### Templates

- `add_lower_third` template pre-flattened for Camtasia compatibility (no nested structures)
- Template project cleaned to ~12KB, media dir gitignored

### Undo/redo

- Stale reference limitation documented: after `undo()`/`redo()`, previously-obtained references to Timeline, Track, MediaBin become stale. Always re-access project properties after undo/redo.
- History persistence via `to_json()` / `from_json()`

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

### Before/after testing with Camtasia

For any change that modifies `.tscproj` output:

1. **Before**: Save a copy of the project JSON (`cp project.tscproj /tmp/before.json`)
2. **Apply**: Run your code change, save the project
3. **Diff**: `diff /tmp/before.json project.tscproj` — verify only intended changes
4. **Open**: Launch in Camtasia, check for crash/exception/visual issues
5. **Playback**: Scrub through the timeline, verify effects render correctly
6. **Round-trip**: Save from Camtasia, diff again — Camtasia may normalize your output

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
Every clip ID must be unique across the entire project. `next_id()` scans sourceBin IDs, clip IDs, and the timeline ID to avoid collisions. The validation module checks this before save.

### Undo/redo stale references
After `project.undo()` or `project.redo()`, any previously-obtained references to nested objects (Timeline, Track, Clip, MediaBin) become stale because the underlying `_data` dict is replaced. Always re-access `project.timeline`, `project.media_bin`, etc. after undo/redo.

### Speed/scalar zero
`speed_to_scalar(0)` and `scalar_to_speed(Fraction(0))` both raise `ValueError`. Guard against zero values before calling these functions.

## File Structure Overview

```
pycamtasia/
├── src/camtasia/           # Library source (the package)
├── tests/                  # 100+ test files, 2616+ tests (parallel via pytest-xdist)
│   ├── conftest.py         # Fixtures: project (isolated tmp_path copy), simple_video, test_project_a_data
│   └── fixtures/           # .tscproj files and .wav files for testing
├── scripts/
│   └── camtasia_validate.sh  # Integration validation script
├── docs/                   # Sphinx documentation
│   ├── api/                # API reference (.rst)
│   ├── guides/             # User guides (.md)
│   └── camtasia-format-reference.md  # Reverse-engineered .tscproj format reference
├── pyproject.toml          # Build config, test config (pytest-xdist -n auto), coverage config
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
- `tests/fixtures/techsmith_complex_asset.tscproj` — Complex asset project
- `tests/fixtures/empty.wav`, `empty2.wav` — Audio fixtures for media tests
- `src/camtasia/resources/new.cmproj` — Blank template project (~12KB, media/ gitignored)
- `src/camtasia/resources/camtasia-project-schema.json` — JSON Schema for .tscproj validation

## User Preferences (encoded from conversation history)

### Subagent Usage
- Use `gpu-dev` agent for all development subagents (NOT `kiro_default` — it has too many MCP servers causing slow cold starts)
- Always maximize parallelism — use 6 domain reviewers when possible
- Pipeline fixes with reviews (run reviewers 5-6 while fixing issues from reviewers 1-4)

### Adversarial Review Process
- 6 separate domain reviewers, one per domain — NEVER combine domains into fewer subagents
- Unbiased prompts only: "Find every bug you can. Be thorough." — NEVER add severity filters like "only report crash bugs"
- Fix ALL issues reported — no dismissing as "known design limitations"
- Continue rounds until bug count stabilizes at 0-2 per round
- Verify each reviewer-reported bug against actual code before fixing — do NOT blindly trust reviewer findings

### Code Quality
- Never use `# pragma: no cover` to hide uncovered lines — write real tests
- Never push commits with failing tests
- Always run tests before committing
- Tests must run in parallel (pytest-xdist, `-n auto`)
- Keep template project clean (~12KB) — never commit media files
- No legacy/deprecated APIs — delete dead code immediately rather than maintaining backward compatibility (no external users)
- Coverage threshold at 96% — write tests for new code, never lower the threshold without writing tests first

### Documentation
- Keep AGENTS.md, format reference, JSON schema, CHANGELOG, README up-to-date with every change
- Update AGENTS.md and ROADMAP.md Known Design Decisions with every round of changes
- Aggressive hyperlinking in documentation — all named entities with URLs should be hyperlinked
- Clean commit messages describing what changed and why
- NEVER reference adversarial review, subagents, round numbers, or domain numbers in commit messages

### Working Style
- Don't stop working — continue autonomously between check-ins
- Reliability > Features — fix bugs before adding features
- Default to action — implement changes rather than suggesting them
- When an approach fails twice, try a fundamentally different approach
- Always check demo agent gaps file before starting new feature work: `~/Desktop/Anomaly Detection Demo v3.5.3/pycamtasia-gaps.md`
- Demo agent gaps files at ~/Desktop/Anomaly Detection Demo v*/pycamtasia-gaps.md — check ALL versions
- Camtasia integration tests available — use freely unless user says they have Camtasia open

### Before/After Camtasia Testing
- Open the project in Camtasia for the user (don't assume they'll do it)
- Save before snapshot, let user make changes, save after snapshot
- Diff the JSON to understand exact format changes
- Use findings to update format reference and JSON schema
