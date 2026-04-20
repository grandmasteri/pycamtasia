# pycamtasia Roadmap

## Pending Bugs

_This section is the authoritative list of bugs reported by adversarial reviewers but not yet fixed. Add entries here immediately upon report. Mark `[verified]` or `[withdrawn: reason]` after verification. Remove entries after the fix is committed and CI is green._

### From unbiased 6-domain review (cycle 5 domains 4-6)

**Project/validation/history:**

1. [verified] `add_background_music` no guard against overlapping fade regions when fade_in + fade_out > clip_duration. Hold keyframe gets negative duration. (project.py)

2. [verified] `validation._check_timing_consistency` exclusion list missing `Callout`. May trigger false-positive warnings for speed-changed Callouts. (validation.py ~L225)

**Operations:**

3. [verified] `pack_track` type-mismatch `m['start'] != cursor`. String fraction vs int — always unequal, triggers spurious transition clearing. (layout.py L34)

4. [verified] `ripple_insert`/`ripple_delete`/`snap_to_grid` lossy int conversion when writing back start from string-fraction. Changes representation type. (layout.py)

5. [verified] `merge_tracks()` loses source track attributes (audioMuted, videoHidden, solo). Creates new track with defaults. (merge.py)

6. [verified] `_scale_tick` float precision loss: `Fraction(float_value)` creates enormous denominators; `round(float(f))` loses precision. (speed.py L28)

7. [verified] `rescale_project` overlap fix doesn't adjust child effects. Effects that referenced old duration boundary extend past new clip end. (speed.py ~L157)

8. [verified] `apply_sync` passes timeline positions instead of source-media offsets. Wrong when Group's mediaStart != 0. (sync.py ~L175)

9. [verified] `match_marker_to_transcript` fallback only checks first 2 words of multi-word labels. False-positive matches. (sync.py ~L113)

**Supporting:**

10. [verified] `_compute_audio_duration` uses `int()` truncation. Off by up to 1 sample. (media_bin/media_bin.py L487)

11. [verified] `trec_probe.probe_trec` video `range_end` uses `int()` truncation. Last frame may be excluded. (trec_probe.py L93)

12. [verified] `trec_probe.probe_trec` audio `range_end` uses `int()` truncation. Same pattern. (trec_probe.py L105)

13. [verified] `square()` default `stroke_color` passes `int(0)` where `float(0.0)` expected by Camtasia format. (annotations/callouts.py L89)

14. [verified] `_format_timecode` silently clamps negative seconds to 0. Wrong timecodes without warning. (export/edl.py L12)

## TechSmith Tutorial Analysis

Review each official Camtasia tutorial to extract insights about features pycamtasia should support.

> **Source pages:**
> - https://www.techsmith.com/learn/tutorials/camtasia
> - https://www.techsmith.com/learn/projects/

### Getting Started (5)

- [ ] [What's New in Camtasia Editor](https://www.techsmith.com/learn/tutorials/camtasia/whats-new-camtasia/)
- [ ] [Build Your First Video](https://www.techsmith.com/learn/tutorials/camtasia/record-edit-share/)
- [ ] [Basic Edits After Recording](https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/)
- [ ] [Introduction to Camtasia Recorder](https://www.techsmith.com/learn/tutorials/camtasia/camtasia-recorder/)
- [ ] [Export & Share Your Video](https://www.techsmith.com/learn/tutorials/camtasia/export-share/)

### Common Ways to Make a Video (9)

- [ ] [Edit Zoom Recordings](https://www.techsmith.com/learn/tutorials/camtasia/edit-zoom-recording/)
- [ ] [Import & Manage Your Project Media (Media Bin)](https://www.techsmith.com/learn/tutorials/camtasia/import-manage-media/)
- [ ] [Edit Microsoft Teams & Other Meeting Recordings](https://www.techsmith.com/learn/tutorials/camtasia/meeting-recordings/)
- [ ] [Create Vertical Videos](https://www.techsmith.com/learn/tutorials/camtasia/create-vertical-videos/)
- [ ] [Create a Video from a Script](https://www.techsmith.com/learn/tutorials/camtasia/create-video-from-script/)
- [ ] [Collaborate on a Video Project](https://www.techsmith.com/learn/tutorials/camtasia/collaborate-video-project/)
- [ ] [Record an iOS Demo or Tutorial](https://www.techsmith.com/learn/tutorials/camtasia/recording-your-ios-device/)
- [ ] [Record a PowerPoint Presentation](https://www.techsmith.com/learn/tutorials/camtasia/record-a-powerpoint-presentation/)
- [ ] [Import Presentation Slides](https://www.techsmith.com/learn/tutorials/camtasia/import-powerpoint-slides/)

### Enhance Your Video (12)

- [ ] [Visual Effects Overview](https://www.techsmith.com/learn/tutorials/camtasia/visual-effects/)
- [ ] [Add Arrows, Shapes, & Callouts](https://www.techsmith.com/learn/tutorials/camtasia/annotations/)
- [ ] [Add a Dynamic Background](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-backgrounds/)
- [ ] [4 Ways to Visualize Your Audio](https://www.techsmith.com/learn/tutorials/camtasia/audio-visualizers/)
- [ ] [Create the Illusion of 3D Perspective (Corner Pinning)](https://www.techsmith.com/learn/tutorials/camtasia/corner-pinning/)
- [ ] [Remove a Background from Your Video](https://www.techsmith.com/learn/tutorials/camtasia/video-background-removal/)
- [ ] [Enhance Your Video Overview](https://www.techsmith.com/learn/tutorials/camtasia/enhance-video/)
- [ ] [Add Video Filters](https://www.techsmith.com/learn/tutorials/camtasia/filters/)
- [ ] [Provide Context with Device Frames](https://www.techsmith.com/learn/tutorials/camtasia/device-frames/)
- [ ] [Remove A Color (Green Screen)](https://www.techsmith.com/learn/tutorials/camtasia/how-to-remove-a-color/)

### Edit on the Timeline (13)

- [ ] [Basic Edits After Recording](https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/)
- [ ] [3 Keys to the Camtasia Editor Timeline](https://www.techsmith.com/learn/tutorials/camtasia/timeline-key-concepts/)
- [ ] [Explore the Timeline](https://www.techsmith.com/learn/tutorials/camtasia/video-editing/)
- [ ] [Add Markers & Video Table of Contents](https://www.techsmith.com/learn/tutorials/camtasia/markers-and-table-of-contents/)
- [ ] [Freeze Video Clips with Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/extend-frame/)
- [ ] [Speed Up & Slow Down Video Clips](https://www.techsmith.com/learn/tutorials/camtasia/clip-speed/)
- [ ] [Join Clips Together](https://www.techsmith.com/learn/tutorials/camtasia/stitch-media/)
- [ ] [Move Multiple Clips at Once](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move/)
- [ ] [Ripple Move & Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move-and-extend-frame/)
- [ ] [Close Timeline Gaps with Magnetic Tracks](https://www.techsmith.com/learn/tutorials/camtasia/magnetic-tracks/)

### AI Video (6)

- [ ] [Speed Up Editing with Camtasia Audiate](https://www.techsmith.com/learn/tutorials/camtasia/camtasia-audio-sync/)
- [ ] [Introduction to AI Video Generation](https://www.techsmith.com/learn/tutorials/camtasia/introduction-ai-video/)
- [ ] [Generate AI Avatars](https://www.techsmith.com/learn/tutorials/camtasia/ai-avatar/)
- [ ] [Generate AI Voices from Text or a Script](https://www.techsmith.com/learn/tutorials/camtasia/text-to-speech/)
- [ ] [Generate a Script with AI](https://www.techsmith.com/learn/tutorials/camtasia/ai-script/)
- [ ] [Translate Your Script, Audio, and Captions](https://www.techsmith.com/learn/tutorials/camtasia/translate/)

### Edit Audio (8)

- [ ] [Recommended Audio Edits](https://www.techsmith.com/learn/tutorials/camtasia/recommended-audio-edits/)
- [ ] [Tips for Getting the Best Audio](https://www.techsmith.com/learn/tutorials/camtasia/best-audio-tips/)
- [ ] [Set the Tone with Background Music](https://www.techsmith.com/learn/tutorials/camtasia/background-music/)
- [ ] [Edit Audio](https://www.techsmith.com/learn/tutorials/camtasia/editing-audio/)
- [ ] [Add Audio Effects](https://www.techsmith.com/learn/tutorials/camtasia/add-audio-effects/)
- [ ] [Record Voice Narration](https://www.techsmith.com/learn/tutorials/camtasia/record-voice-narration/)

### Cursor Edits & Effects (5)

- [ ] [Add Cursor Effects](https://www.techsmith.com/learn/tutorials/camtasia/cursor-effects/)
- [ ] [Introduction to Cursor Editing](https://www.techsmith.com/learn/tutorials/camtasia/cursor-editing-basics/)
- [ ] [Replace the Cursor](https://www.techsmith.com/learn/tutorials/camtasia/change-cursor/)
- [ ] [Customize the Cursor Path](https://www.techsmith.com/learn/tutorials/camtasia/customize-your-cursor-path/)
- [ ] [Quickly Smooth Cursor Movements](https://www.techsmith.com/learn/tutorials/camtasia/cursor-smoothing/)

### Video Animations (7)

- [ ] [Zoom In to Focus Attention](https://www.techsmith.com/learn/tutorials/camtasia/animations/)
- [ ] [Add a Transition](https://www.techsmith.com/learn/tutorials/camtasia/video-transitions/)
- [ ] [Animations In-Depth](https://www.techsmith.com/learn/tutorials/camtasia/animations-in-depth/)
- [ ] [Add Movement to Any Object (Motion Paths)](https://www.techsmith.com/learn/tutorials/camtasia/motion-path/)
- [ ] [Blur or Mask a Video](https://www.techsmith.com/learn/tutorials/camtasia/blur-mask-video/)
- [ ] [Animate Text & Images with Behaviors](https://www.techsmith.com/learn/tutorials/camtasia/animation-behaviors/)
- [ ] [Create Stunning Animations with Media Mattes](https://www.techsmith.com/learn/tutorials/camtasia/animations-with-media-mattes/)

### Viewer Engagement & Accessibility (5)

- [ ] [Add Closed Captions to a Video](https://www.techsmith.com/learn/tutorials/camtasia/add-closed-captions/)
- [ ] [Add Dynamic Captions](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-captions/)
- [ ] [Build Quizzes & Surveys](https://www.techsmith.com/learn/tutorials/camtasia/quizzing/)
- [ ] [Add Hotspots (Interactive Videos)](https://www.techsmith.com/learn/tutorials/camtasia/add-interactive-hotspots-to-a-video/)

### Export & Share (5)

- [ ] [Use Camtasia Videos in Your LMS](https://www.techsmith.com/learn/tutorials/camtasia/lms-options/)
- [ ] [Export & Share Your Video](https://www.techsmith.com/learn/tutorials/camtasia/export-share/)
- [ ] [Watermark Your Videos](https://www.techsmith.com/learn/tutorials/camtasia/video-watermark/)
- [ ] [Batch Export Videos](https://www.techsmith.com/learn/tutorials/camtasia/batch-export/)
- [ ] [Export an Audio File](https://www.techsmith.com/learn/tutorials/camtasia/export-audio/)

### Customizations & Branding (8)

- [ ] [Reuse Media Across Projects (Library)](https://www.techsmith.com/learn/tutorials/camtasia/library/)
- [ ] [Customize Camtasia Editor](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia/)
- [ ] [How to Use a Template](https://www.techsmith.com/learn/tutorials/camtasia/use-a-template/)
- [ ] [Build a Video Template to Share](https://www.techsmith.com/learn/tutorials/camtasia/create-a-template/)
- [ ] [Build Your Color Palette (Themes)](https://www.techsmith.com/learn/tutorials/camtasia/themes/)
- [ ] [Package & Share Camtasia Editor Resources](https://www.techsmith.com/learn/tutorials/camtasia/package-share-camtasia-resources/)
- [ ] [Customize Shortcuts](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia-shortcuts/)
- [ ] [Create Custom Assets](https://www.techsmith.com/learn/tutorials/camtasia/create-custom-assets/)

### Projects (6)

- [ ] [How to Make an Intro for a Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-intro/)
- [ ] [Create a Quick Tip Style Video](https://www.techsmith.com/learn/tutorials/camtasia/create-a-quick-tip-style-video-template/)
- [ ] [How to Create a Software Tutorial](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-great-tutorial/)
- [ ] [How to Make an Explainer Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-explainer-video/)
- [ ] [How to Create a Product Walkthrough Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-product-walkthrough-video/)
- [ ] [How to Make a Software Demo](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-a-software-demo/)

## High-Level API Improvement Ideas (from demo production)

- [x] VideoProductionBuilder
- [x] ScreenRecordingSync
- [x] import_media() format validation and auto-conversion
- [x] ProgressiveDisclosure helper
- [x] Project.clean_inherited_state()
- [x] MarkerList.clear() and MarkerList.replace()
- [x] Project.remove_orphaned_media()
- [x] Recap/tile layout helper

## Feature Gaps (discovered during adversarial review & integration testing)

### Clip API
- [ ] `BaseClip.unmute()` — no way to reverse `mute()` without raw dict access
- [ ] `BaseClip.remove_all_effects()` should redirect to children for UnifiedMedia
- [ ] `UnifiedMedia` effect read properties (`has_effects`, `effect_count`, `effect_names`) read from wrapper instead of children — should redirect or warn
- [x] `Callout.text` setter should update `textAttributes` `rangeEnd` to match new text length
- [ ] `BaseClip.add_keyframe()` should create corresponding `animationTracks.visual` entries (currently only `fade_in`/`fade_out`/`fade` do this)
- [ ] `set_position_keyframes` / `set_scale_keyframes` / `set_rotation_keyframes` should also create `animationTracks.visual` entries
- [ ] `add_progressive_disclosure(replace_previous=True)` option for non-accumulating sequences

### Track API
- [ ] `clip_after()` uses `>=` (at-or-after) — consider renaming or adding `clip_strictly_after()`
- [x] `insert_gap()` and `shift_all_clips()` don't clear/adjust transitions that may become invalid
- [x] `merge_adjacent_clips()` doesn't verify clips are actually adjacent before merging
- [x] `set_segment_speeds()` uses float accumulation for `mediaStart` — should use Fraction
- [x] `split_clip()` uses raw `Fraction(orig_scalar)` instead of `_parse_scalar()` — inconsistent precision

### Timeline API
- [x] `clips_of_type()` is O(n²) and misattributes nested clips to `None` track
- [x] `shift_all()` doesn't shift transition or effect `start` times
- [ ] `insert_gap()` / `remove_gap()` don't adjust transitions or markers
- [ ] `flatten_to_track()` drops transitions silently — should document or warn
- [ ] `build_section_timeline()` helper — place all sections on one track with transitions

### Validation
- [ ] Validate that `timeline.id` exists and is unique
- [ ] Validate `GenericBehaviorEffect` structure (required `in`/`center`/`out` phases)
- [ ] Validate overlapping clips on same track (Camtasia tracks are single-occupancy)
- [ ] Flag explicit `null` in transition `leftMedia`/`rightMedia` (format says omit, not null)

### Effects
- [ ] Typed wrapper classes for `LutEffect`, `Emphasize`, `Spotlight`, `ColorAdjustment`, `BlendModeEffect`, `MediaMatte`
- [ ] `BlurRegion` is exported but not registered — either register or remove from `__all__`
- [ ] `DropShadow.enabled` / `CursorShadow.enabled` should document that setting them doesn't affect keyframes

### Export
- [ ] EDL exporter doesn't recurse into Groups/StitchedMedia — nested clips invisible
- [ ] CSV/report exporters same issue — only top-level clips exported
- [x] EDL `UnifiedMedia` source is always `AX` — should use video sub-clip's source
- [ ] SRT exporter writes empty file silently when no markers — should warn
- [ ] `timeline_json` export doesn't include effects, transitions, or metadata

### Builders
- [x] `timeline_builder.add_title()` ignores `subtitle` parameter (dead code)
- [ ] `tile_layout` scale doesn't account for image dimensions vs cell size
- [x] `screenplay_builder._find_audio_file()` only searches `.wav` — should support `.mp3`, `.m4a`

### Schema
- [ ] Schema `effect.effectName` enum includes behavior names — weakens `oneOf` discriminator
- [x] Schema `effect` definition doesn't require `bypassed` (format reference says required)
- [ ] Non-schema transition names: `FadeThroughColor`, `SlideUp`, `SlideDown`, `WipeLeft/Right/Up/Down` — document as unsupported or remove methods

### Behavior Presets
- [ ] Preset values don't fully match real TechSmith samples (ongoing refinement)
- [ ] `reveal` preset has `start: 1411200000` (~2s) — may not be the right default
- [x] `BehaviorInnerName` enum missing `'fading'` phase name
- [x] `pulsating` center phase `offsetBetweenCharacters` should be `49392000` (not `0`)

### Infrastructure
- [ ] `media_bin.import_media()` directory naming can collide on rapid successive imports
- [x] `media_bin._visual_track_to_json()` uses `sampleRate=0` for video (should be frame rate)
- [ ] `media_bin._visual_track_to_json()` / `_audio_track_to_json()` omit `tag` field
- [ ] `scalar_to_string()` name implies string return but returns `int` for scalar=1
- [ ] `parse_scalar()` `limit_denominator(10_000)` is arbitrary — document the tradeoff
- [ ] `history.py` `clear()`+`update()` pattern invalidates nested object references — add warning in docstring

### Known Design Decisions (not bugs — documented to avoid re-reporting)
- `UnifiedMedia` caches video/audio child clips without invalidation — works because dict references are shared; only breaks if someone replaces the entire sub-dict (not a real-world pattern)
- `BaseClip.clone()` sets `id=-1` sentinel — caller must reassign before saving; no auto-enforcement by design
- `BaseClip.__eq__` uses `id` comparison — cloned clips with `id=-1` compare equal; known tradeoff for simplicity
- `BaseClip.gain` reads `attributes.gain` which only applies to AMFile — returns 1.0 default for other clip types; `is_silent` checks both `gain` and `volume` as a workaround
- `BaseClip.mute()` sets `attributes.gain=0` for non-Group/non-StitchedMedia/non-UnifiedMedia clips — only effective for AMFile; VMFile/Callout/IMFile don't use `attributes.gain`
- `GroupTrack.add_clip()` auto-ID is only locally unique — warning emitted; caller should pass `next_id` for global uniqueness
- `set_speed()` propagates `mediaStart` from wrapper to UnifiedMedia sub-clips — correct when they're in sync (the normal case); would be wrong if sub-clips had independent mediaStart (not observed in real projects)
- `Callout.text` setter updates all `rangeEnd` values to new text length — correct for single-range text; destroys multi-range per-character formatting (a known limitation)
- `fade_out()`/`fade()`/`set_opacity_fade()` use clip `duration` for keyframe timing — correct for normal-speed clips; may be wrong for speed-changed clips where keyframes should use `mediaDuration`
- `duplicate_clip` uses ad-hoc `_remap_ids` instead of `_remap_clip_ids_with_map` — works for current nesting depths but less robust than the timeline-level remapper
- `Effect.__eq__` uses identity (`is`) not value equality — intentional for mutation tracking
- `GenericBehaviorEffect.parameters` returns `{}` — intentional since behavior params live in phases, not at top level
- `GenericBehaviorEffect.get_parameter()`/`set_parameter()` raise `NotImplementedError` — intentional LSP violation; use phase accessors instead
- `BehaviorPhase` objects created fresh on each property access — no caching; mutations propagate via shared dict reference
- `_flatten_parameters` uses negative-condition list — fragile but correct for all known parameter shapes
- `save()` warns on validation errors but doesn't prevent saving — by design; `compact()` raises on errors
- `all_clips()` creates ephemeral wrappers for StitchedMedia/UnifiedMedia sub-clips — mutations propagate via shared dict; identity comparisons fail
- `clips_in_range()` only checks top-level clips — by design; use `all_clips()` for nested
- `add_gradient_background()` uses `time.time()` in source path — non-deterministic but functional
- Non-schema transition names (`FadeThroughColor`, `SlideUp/Down`, `Wipe*`) — documented with warnings in docstrings; kept for forward-compatibility
- `add_border()`/`add_colorize()` use effect names not in schema — may be valid in newer Camtasia versions
- `group_clips_across_tracks()` emits v10-style typed metadata regardless of project version — works for v10+; may cause silent repair on v6/v8
- `scale_all_durations()` recalculates scalar from new duration/old mediaDuration — changes playback speed as side effect; documented behavior
- `_check_timing_consistency` uses 1% tolerance — generous for large durations but avoids false positives on rational arithmetic rounding
- `EffectName` enum missing behavior effect names — behavior effects use `GenericBehaviorEffect._type` dispatch, not the enum
- `_BehaviorEffectData` TypedDict can't declare `in`/`center`/`out` keys — Python keyword limitation
- `RGBA.__eq__` uses `type(self)` not `isinstance` — prevents subclass equality; intentional strictness
- `merge_tracks()` in `operations/merge.py` silently drops transitions from source tracks — known limitation; transitions require complex ID remapping that isn't implemented yet
- `shift_all()` on Timeline doesn't shift timeline markers — known limitation; markers are in `parameters.toc` and would need separate scaling
- `rescale_project()` doesn't scale keyframe timing in `parameters`, `animationTracks.visual`, or behavior effect phase timing — known limitation; only clip-level and effect-level `start`/`duration` are scaled
- `add_screen_recording()` creates UnifiedMedia and sub-clips without `metadata`, `parameters`, or `animationTracks` keys on the wrapper — Camtasia silently repairs on load; internal Group tracks also missing format keys (`ident`, `audioMuted`, etc.)
- `insert_track()` creates track data dicts missing some format-reference keys (`ident`, `audioMuted`, `videoHidden`, `magnetic`, `matte`, `solo`) — these exist in `trackAttributes` but not in the track dict itself
- `mediaStart` is NOT scaled for regular clips (VMFile, AMFile, IMFile, Callout, ScreenVMFile) in `rescale_project()` — this is CORRECT because `mediaStart` is a source-media offset, not a timeline position; only StitchedMedia internal sub-clips need `mediaStart` scaling
- `insert_gap()` transition adjustment checks for `t['start']` which transitions don't have per the format spec — dead code; transitions are positioned by `leftMedia`/`rightMedia` clip references, not absolute `start` times
- `move_clip_to_track()` double-remaps then restores top-level ID, leaving `id_map` with stale entry — `assetProperties.objects` references may point to wrong ID for moved Group clips
- `remove_gap()` only shifts clips starting at or after `position + gap_duration` — clips within the gap region are left in place; caller is expected to verify the gap is empty
- `add_gradient_background()` creates sourceBin entry pointing to a non-existent shader file — the shader is a virtual media type that Camtasia generates internally; the path is a placeholder
- `average_clip_duration_seconds` and `clip_count` count top-level clips only — consistent with each other but different from `all_clips()` which includes nested clips; this is by design
- `merge_projects()` doesn't copy source track attributes (`audioMuted`, `videoHidden`, `solo`, etc.) — creates default attributes for merged tracks
- `merge_tracks()` `_remap_clip_ids` doesn't remap `assetProperties.objects` references — use `merge_projects()` for full-fidelity merging

### Additional Known Design Decisions (added after Round 110)

- `copy_to_track()` uses sequential IDs from `_remap_clip_ids_with_map` starting at `_next_clip_id()` — for compound clips (Group/UnifiedMedia/StitchedMedia), nested IDs are sequential and globally unique because `_next_clip_id()` scans all tracks. The top-level ID self-mapping in `id_map` is harmless.
- `set_audio_speed()` only corrects the first speed-changed AMFile — by design, the function targets a single audio clip. Multiple speed-changed audio clips require separate calls.
- `diff_projects()` compares tracks by positional index — track insertions/deletions cause renumbering, making the diff semantically misleading. This is a known limitation.
- `behavior_presets.py` `get_behavior_preset()` sets `duration = duration_ticks` (full clip duration) — Camtasia clips behavior effects at the clip boundary, so `start + duration > clip_duration` is valid. The lower_third template confirms this pattern.
- `_pauses_with_positions()` uses `max(0, idx)` for pauses before the first VO — maps to `after_vo_index=0`, placing the pause after the first VO. This is the current design; a leading-pause sentinel would require changes to `build_from_screenplay`.
- `UnifiedMedia` inherits `remove_all_effects()`, `remove_effect_by_name()`, `is_effect_applied()` from BaseClip — these operate on the wrapper's empty effects list. Feature gap: should redirect to children or raise TypeError.
- `swap_clips()` only swaps `start` times, not positions — clips of different durations will create gaps. This is the documented behavior.
- `group_clips()` ID counter is not incremented after Group ID assignment — safe because `_next_clip_id()` scans all medias on next call.

## Tooling

### Linting with Ruff

Add [ruff](https://docs.astral.sh/ruff/) as the linter and formatter. Ruff replaces flake8 + black + isort as a single tool. Configure via `ruff.toml` or `pyproject.toml` `[tool.ruff]` section. Selected rules: `E` (pycodestyle errors), `F` (pyflakes), `I` (isort), `UP` (pyupgrade — enforce `X | Y` over `Union[X, Y]`), `W` (pycodestyle warnings). Add to CI workflow.

### Additional Known Design Decisions (added after Round 123)

- `_PerMediaMarkers` silently drops markers on IMFile/ScreenIMFile clips — `mediaDuration=1` causes the `media_offset >= media_dur` filter to reject all markers. Known limitation.
- `validate_structure()` duplicate-ID check only recurses one level into Groups/StitchedMedia/UnifiedMedia — deeply nested duplicate IDs go undetected. Known limitation.
- `repair()` doesn't handle cascading overlaps — when a clip is reduced to zero duration, the next pair isn't re-checked. Multiple `repair()` calls may be needed.
- `Timeline.insert_gap()`/`remove_gap()` don't shift timeline markers — markers become misaligned after gap operations. Known limitation.
- `duplicate_track()` returns Track without `_all_tracks`/`_timeline_id` — `_next_clip_id()` on the returned Track only scans its own medias. Known limitation.
- `is_muted` for UnifiedMedia only checks `audio.attributes.gain`, ignores `parameters.volume` — if volume is set to 0 via the volume setter, `is_muted` returns False. Known limitation.
- `Group.set_internal_segment_speeds()` uses float-based `seconds_to_ticks()` for `mediaStart` — can cause frame-level drift for segments deep into a recording. Known limitation.
- `ripple_delete()` threshold `>= target_start + gap` is BY DESIGN — only shifts clips after the deleted clip's end, not clips overlapping with it.
- `get_behavior_preset()` clamps `start` to `duration_ticks - 1` — Camtasia clips behavior effects at the clip boundary, so `start + duration > clip_duration` is valid.
- `_VO_RE` regex requires specific bold-colon markdown pattern — screenplays using different formatting will silently produce empty VO blocks. Known limitation.
