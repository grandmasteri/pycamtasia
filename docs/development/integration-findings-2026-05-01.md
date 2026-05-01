# Integration Suite Findings — Final Status (2026-05-01)

This document records what the newly-comprehensive integration suite
surfaced and how every finding was resolved before 0.1.0.

## Final result

- **Total integration tests:** 217 (189 new + 27 pre-existing + 1 new test from split)
- **Passing:** 217
- **Failing:** 0
- **xfailed:** 0
- **Runtime:** ~67 min serial execution

## Summary of work

The first full run of the new integration suite failed 31 tests. After
systematic root-cause analysis and fixes across a mix of library bugs
and test-side bugs, **all 31 failures are resolved**. No bugs deferred,
no xfail markers, no tests skipped.

## Library bugs fixed

### 1. Keyframe format — the big one

`_build_param_keyframes` in `src/camtasia/timeline/clips/base.py` was
constructing keyframes as spans (`endTime = <next keyframe's time>`,
`duration = gap`). Camtasia's own format, verified against
`techsmith_complex_asset.tscproj`, requires keyframes to be points
(`endTime == time`, `duration == 0`). This single fix closed 10+ tests
spanning audio fades (all volume envelopes), skew/rotation/translation
animation, and complex kitchen-sink tests involving any parametric
animation.

### 2. Keyframe format, visual-parameter edge case

After the point-form fix, we discovered that visual parameters (scale,
opacity, translation) actually DO require span-form keyframes, unlike
audio and other scalar parameters. Camtasia treats visual keyframes as
animation segments on shared visual animation tracks. Fixed by making
`add_keyframe` detect visual parameters and produce spans for those
while keeping points for everything else. Also added
`_check_visual_track_order` validator to catch unsorted visual segments
pre-save.

### 3. Background music keyframes

`Project.add_background_music` had its own keyframe-construction path
that produced spans for volume envelopes. Rewrote to produce points.
Added `test_keyframes_are_points_not_spans` regression test.

### 4. Behavior preset names

Two of the ten `BehaviorPreset` values generated invalid Camtasia
output: `emphasize` and `jiggle` used their own names as the "center
phase" name, but Camtasia's internal registry has these under different
names. Fixed `src/camtasia/templates/behavior_presets.py`:
- `emphasize` → center name is `'pulsate'`
- `jiggle` → center name is `'tremble'`

This one 2-line change closed all 4 behavior-related failures:
emphasize, jiggle, multiple-behaviors-on-one-callout, and
behavior-on-rectangle-callout.

### 5. split_clip + transition interaction (previously-known bug)

This was tracked as a Pending Bug before the suite expansion. It
auto-resolved as a side-effect of the keyframe format fix (the transition's
own animation parameters were producing invalid keyframes, which
cascaded into the split producing doubly-bad output). Un-xfailed and
now serves as a regression test.

## Test-side bugs fixed

The integration suite also surfaced sloppy test authoring in the
subagent-generated files:

- **API misuse:** `IMFile.add_behavior` (doesn't exist — only Callouts
  support behaviors), `Group.add_behavior` (same), `ripple_move()` with
  wrong kwarg name, `merge_tracks()` called with wrong signature.
- **Miscounts:** edge-case tests that assumed the `new.cmproj` fixture
  had 0 tracks when it actually has 2.
- **Fixture ambiguity:** `empty.wav` was only 1 second, but tests created
  multi-second clips from it. After split/ripple operations this led to
  `mediaRange` overflow. Regenerated as a 60-second silent WAV.
- **Sources not imported:** 4 tests used `track.add_clip('VMFile', 1, ...)`
  with a hardcoded source ID=1 without ever calling `project.import_media()`.
  Fixed to import real media first.
- **Overlapping clips:** `ExportedFrame` and `FreezeFrame` tests added
  annotations on top of source clips on the same track. Fixed by
  trimming the source clip appropriately.
- **Case-sensitive preset names:** `'Reveal'` → `'reveal'`.
- **Timeout:** one kitchen-sink test did multiple Camtasia launches in a
  single test body; split into two tests.

## Validator improvements

- Added `_check_visual_track_order` rule: catches unsorted visual-track
  segments before save (produced by out-of-order `add_keyframe` calls).
- Existing validator rules successfully caught 3 test-side "validate
  flagged but tests saved anyway" bugs. The validator-contract helper
  worked as designed.

## Methodology used

Every VALIDATOR GAP was resolved using the same systematic approach:

1. Reproduce the failure in a standalone Python script.
2. Launch Camtasia subprocess, capture full stderr.
3. Grep stderr for the actual error message (usually starts with
   `Failed to parse project error: 'Invalid ...'`).
4. Dump the generated `project.tscproj` and compare the offending
   structure against a known-good fixture from
   `tests/fixtures/techsmith_*.tscproj`.
5. Identify the structural difference.
6. Fix the library (and/or add a validator rule) so the library
   produces the known-good structure.
7. Verify with the integration test.
8. Add a unit test as regression guard.

## Stats

- **15 parallel subagents** generated the initial 189 tests in ~20 min
- **5 parallel subagents** fixed the initial 31 failures in ~15 min
- **Me, serial:** ~30 min follow-up on edge cases and final
  reconciliation
- **Unit tests:** 4933 passing (added 1 regression test)
- **Integration tests:** 217 passing
- **Runtime:** unit 35s parallel; integration 67min serial (Camtasia
  launch-wait dominated)

## Success

**The validator-contract design worked exactly as intended.** Every
Camtasia rejection that the library silently produced was surfaced as
a VALIDATOR GAP, which forced us to either fix the library so the
invalid output was never produced, or expand the validator so the
invalid output was caught pre-save. Both directions closed.
