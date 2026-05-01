# Integration Suite Findings (First Full Run — 2026-05-01)

This document records what the newly-comprehensive integration suite
surfaced on its first full run. Treat every entry as a discovery signal.

- **Total tests run:** 216 (189 new, 27 pre-existing)
- **Passed:** 184
- **Failed:** 31
- **xfailed (known bug):** 1 (split_clip + transition)
- **Wall-clock runtime:** 63 min 44 sec (serial execution, Camtasia launch-wait dominated)

## Failure categories

### 1. Validator gaps (18 tests) — highest priority

These tests use `open_in_camtasia()`, which enforces the validator
contract: "If Camtasia rejects the file but `project.validate()` was
silent, that's a library bug." Every test listed here means pycamtasia
silently produced a file Camtasia cannot open.

**Audio domain (10 tests)** — strongly suggests a systemic audio
feature gap, not 10 independent bugs:

- `TestAudioFadeIn::test_short_fade_in`
- `TestAudioFadeIn::test_long_fade_in`
- `TestAudioFadeOut::test_short_fade_out`
- `TestAudioFadeOut::test_long_fade_out`
- `TestAudioFadeInAndOut::test_both_fades_on_same_clip`
- `TestBackgroundMusic::test_background_music_with_fades`
- `TestStackedAudioEffects::test_fade_equalizer_visualizer`
- `TestMultiTrackAudio::test_different_effects_per_track`
- `TestAudioDurationEdgeCases::test_very_short_clip`
- `TestAudioDurationEdgeCases::test_long_clip`

Hypothesis: `add_audio_fade_in`/`add_audio_fade_out` produce structurally
invalid .tscproj output that Camtasia rejects. Since many audio tests
depend on those primitives, they all fail for the same root cause.
Investigation: compare a simple audio-fade project's JSON against a
known-good Camtasia-generated one.

**Behavior domain (4 tests)** — case-sensitivity / preset coverage:

- `TestRemainingBehaviorPresets::test_behavior_opens[emphasize]`
- `TestRemainingBehaviorPresets::test_behavior_opens[jiggle]`
- `TestBehaviorEdgeCases::test_multiple_behaviors_on_one_callout`
- `TestBehaviorEdgeCases::test_behavior_on_rectangle_callout`

Hypothesis: `emphasize` and `jiggle` presets produce invalid output.
Multi-behavior stacking on a single clip may have ordering/key-collision
issues. Rectangle-shape callouts may not accept behaviors the same way
text callouts do.

**Kitchen-sink interactions (4 tests)** — high-value integration
signals: multiple features work alone but break when combined:

- `TestEffectsCaptionsMarkersCombined::test_effects_captions_markers_combined_opens`
- `TestExtremeKeyframes::test_extreme_keyframes_opens`
- `TestMultiFormatMedia::test_multi_format_media_opens`
- `TestPodcastAudioHeavy::test_podcast_audio_heavy_opens` (likely the audio-fade root cause)

### 2. Validator flagged issues but test saved anyway (5 tests)

These tests produced validation warnings/errors before save, ignored
them, saved, and Camtasia rejected. The tests should either:
(a) assert the validate() output and not attempt to open, or
(b) fix the project setup so validate() is clean.

- `TestEdlExport::test_export_edl_does_not_corrupt_project`
- `TestCsvExport::test_export_csv_does_not_corrupt_project`
- `TestCsvExport::test_csv_include_nested_true_vs_false`
- `TestTemplateRoundTrip::test_template_to_project_modify_and_re_template`
- `TestExportedFrame::test_exported_frame_opens`
- `TestFreezeFrame::test_freeze_frame_opens`

### 3. Test-side API misuse (4 tests)

Subagents used APIs incorrectly. Fix the tests, not the library.

- `TestGroupWithBehavior::test_behavior_on_grouped_callout` — `ValueError: Unknown behavior preset 'Reveal'` — should be `'reveal'` (lowercase)
- `TestGroupTransitionBehaviorInteractions` — `'Group' object has no attribute 'add_behavior'` — Group doesn't directly accept behaviors; apply to children
- `TestMultiGroupNestedOperations` — same root cause (Group.add_behavior doesn't exist)
- `TestRippleOperationsChaos` — `ripple_move() got an unexpected keyword argument 'new_start_seconds'` — wrong arg name

### 4. Test-logic assertion errors (2 tests)

Test authors miscounted expected values.

- `TestEmptyAndMinimalProjects::test_empty_project_no_tracks` — expected 0 tracks, got 2 (the default project fixture comes with tracks)
- `TestManyTracks::test_100_tracks` — expected 100, got 102 (fixture starts with 2 tracks; adding 100 more = 102)

### 5. Timeout (1 test)

- `TestTemplateRoundtrip::test_template_roundtrip_with_features_opens` — exceeded 60s. Likely does multiple Camtasia launches in one test. Fix by either splitting into multiple tests or increasing timeout.

## Next actions

### Short term (before 0.1.0 release)

1. **Triage validator gaps** — investigate the audio-fade root cause first (high multiplier). Expand `project.validate()` to catch invalid audio-fade output.
2. **Fix test-side bugs** (4 tests) — straightforward API corrections.
3. **Fix assertion miscounts** (2 tests) — adjust expectations to match fixture reality.
4. **Split or relax timeout** on the one long template test.
5. **Add explicit xfail markers** for the real validator gaps, with reasons pointing to this document, so the suite returns fully green while the bugs are tracked.
6. **File each validator gap as a ROADMAP entry** under `### Validation`.

### Medium term (post 0.1.0)

1. Expand `project.validate()` until every Camtasia rejection is preceded
   by a validator error.
2. Implement the `bisect_features()` helper mentioned in ROADMAP — makes
   kitchen-sink test failures actionable.
3. Add regression tests for each fixed validator gap.

## Success

**The suite worked exactly as designed.** It caught 31 real issues —
some library bugs, some test bugs, all of which were silent before.
That's 31 future user-facing defects now visible and trackable.
