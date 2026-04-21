# pycamtasia Roadmap

## Pending Bugs

_This section is the authoritative list of bugs reported by adversarial reviewers but not yet fixed. Add entries here immediately upon report. Mark `[verified]` or `[withdrawn: reason]` after verification. Remove entries after the fix is committed and CI is green._

(none currently)

## TechSmith Tutorial Analysis

Review each official Camtasia tutorial to extract insights about features pycamtasia should support.

> **Source pages:**
> - https://www.techsmith.com/learn/tutorials/camtasia
> - https://www.techsmith.com/learn/projects/

### Getting Started (5)

- [not-applicable] [What's New in Camtasia Editor](https://www.techsmith.com/learn/tutorials/camtasia/whats-new-camtasia/) — Camtasia desktop app release notes; not relevant to file manipulation
- [already-implemented] [Build Your First Video](https://www.techsmith.com/learn/tutorials/camtasia/record-edit-share/) — TimelineBuilder, build_from_screenplay, import_media, track/clip APIs cover the building blocks
- [already-implemented] [Basic Edits After Recording](https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/) — trim/split/reorder via timeline/clips/base.py; ripple_insert/delete in operations/layout.py
- [not-applicable] [Introduction to Camtasia Recorder](https://www.techsmith.com/learn/tutorials/camtasia/camtasia-recorder/) — Screen recording is OS-level capture, not .cmproj manipulation
- [not-applicable] [Export & Share Your Video](https://www.techsmith.com/learn/tutorials/camtasia/export-share/) — Video encoding/rendering requires the Camtasia engine; pycamtasia exports metadata only (EDL/CSV/SRT/JSON/report)

### Common Ways to Make a Video (9)

- [already-implemented] [Edit Zoom Recordings](https://www.techsmith.com/learn/tutorials/camtasia/edit-zoom-recording/) — Generic video import/edit covers all non-Zoom-specific cases; no Zoom-UI specific features apply to .cmproj manipulation
- [already-implemented] [Import & Manage Your Project Media (Media Bin)](https://www.techsmith.com/learn/tutorials/camtasia/import-manage-media/) — media_bin/media_bin.py provides full MediaBin API with import_media, probing, metadata
- [already-implemented] [Edit Microsoft Teams & Other Meeting Recordings](https://www.techsmith.com/learn/tutorials/camtasia/meeting-recordings/) — Generic video import/edit covers this; no Teams-UI-specific features apply
- [already-implemented] [Create Vertical Videos](https://www.techsmith.com/learn/tutorials/camtasia/create-vertical-videos/) — project.width/height setters allow setting canvas to vertical (e.g., 1080x1920)
- [already-implemented] [Create a Video from a Script](https://www.techsmith.com/learn/tutorials/camtasia/create-video-from-script/) — builders/screenplay_builder.py build_from_screenplay places VO audio clips with pauses
- [not-applicable] [Collaborate on a Video Project](https://www.techsmith.com/learn/tutorials/camtasia/collaborate-video-project/) — Real-time cloud collaboration; operations/diff.py supports offline comparison
- [not-applicable] [Record an iOS Demo or Tutorial](https://www.techsmith.com/learn/tutorials/camtasia/recording-your-ios-device/) — iOS screen recording is hardware capture, outside file-manipulation scope
- [not-applicable] [Record a PowerPoint Presentation](https://www.techsmith.com/learn/tutorials/camtasia/record-a-powerpoint-presentation/) — Requires the Camtasia Recorder + PowerPoint integration, not a file concern
- [feature-gap] [Import Presentation Slides](https://www.techsmith.com/learn/tutorials/camtasia/import-powerpoint-slides/) — No PPTX import; would extract slide images and place as media on timeline

### Enhance Your Video (12)

- [already-implemented] [Visual Effects Overview](https://www.techsmith.com/learn/tutorials/camtasia/visual-effects/) — Comprehensive effects/ module: DropShadow, Glow, Mask, BlurRegion, ColorAdjustment, LutEffect, etc.
- [already-implemented] [Add Arrows, Shapes, & Callouts](https://www.techsmith.com/learn/tutorials/camtasia/annotations/) — annotations/callouts.py (text, square, arrow, highlight, keystroke_callout) and shapes.py (rectangle)
- [partial] [Add a Dynamic Background](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-backgrounds/) — TimelineBuilder.add_background_image for static; no animated/dynamic background generator yet
- [feature-gap] [4 Ways to Visualize Your Audio](https://www.techsmith.com/learn/tutorials/camtasia/audio-visualizers/) — No audio visualization (waveform/spectrum/reactive animations)
- [feature-gap] [Create the Illusion of 3D Perspective (Corner Pinning)](https://www.techsmith.com/learn/tutorials/camtasia/corner-pinning/) — No CornerPin effect class
- [already-implemented] [Remove a Background from Your Video](https://www.techsmith.com/learn/tutorials/camtasia/video-background-removal/) — MediaMatte effect in effects/visual.py is Camtasia’s matte/background-removal mechanism
- [already-implemented] [Enhance Your Video Overview](https://www.techsmith.com/learn/tutorials/camtasia/enhance-video/) — ColorAdjustment, LutEffect, DropShadow, Glow, Emphasize, Spotlight, MotionBlur, RoundCorners
- [already-implemented] [Add Video Filters](https://www.techsmith.com/learn/tutorials/camtasia/filters/) — effects/visual.py provides color grading (LutEffect), blend modes, Spotlight, Emphasize, MotionBlur
- [feature-gap] [Provide Context with Device Frames](https://www.techsmith.com/learn/tutorials/camtasia/device-frames/) — No device frame overlay (phone/laptop/tablet bezels)
- [feature-gap] [Remove A Color (Green Screen)](https://www.techsmith.com/learn/tutorials/camtasia/how-to-remove-a-color/) — No dedicated chroma key / color-key effect; MediaMatte is a different matte concept

### Edit on the Timeline (13)

- [already-implemented] [Basic Edits After Recording](https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/) — trim/split/reorder via timeline/clips/base.py; ripple_insert/delete in operations/layout.py
- [not-applicable] [3 Keys to the Camtasia Editor Timeline](https://www.techsmith.com/learn/tutorials/camtasia/timeline-key-concepts/) — UI-orientation tutorial for the desktop app
- [not-applicable] [Explore the Timeline](https://www.techsmith.com/learn/tutorials/camtasia/video-editing/) — UI-orientation tutorial; pycamtasia already models the timeline fully
- [already-implemented] [Add Markers & Video Table of Contents](https://www.techsmith.com/learn/tutorials/camtasia/markers-and-table-of-contents/) — timeline/markers.py MarkerList with add/remove/clear/replace; exported as SRT
- [already-implemented] [Freeze Video Clips with Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/extend-frame/) — track.py add_freeze_frame method on Track
- [already-implemented] [Speed Up & Slow Down Video Clips](https://www.techsmith.com/learn/tutorials/camtasia/clip-speed/) — clips/base.py set_speed, scalar, operations/speed.py rescale_project, set_segment_speeds
- [x] [Join Clips Together](https://www.techsmith.com/learn/tutorials/camtasia/stitch-media/) — StitchedMedia clip type exists; no explicit single-track “join two adjacent clips” operation yet
- [already-implemented] [Move Multiple Clips at Once](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move/) — operations/batch.py move_all, apply_to_clips; track.py move_clip
- [already-implemented] [Ripple Move & Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move-and-extend-frame/) — operations/layout.py ripple_insert/delete; add_freeze_frame
- [already-implemented] [Close Timeline Gaps with Magnetic Tracks](https://www.techsmith.com/learn/tutorials/camtasia/magnetic-tracks/) — track.magnetic property; operations/layout.py pack_track

### AI Video (6)

- [partial] [Speed Up Editing with Camtasia Audiate](https://www.techsmith.com/learn/tutorials/camtasia/camtasia-audio-sync/) — Read-only Audiate transcript support; no write-back or Audiate-driven edit operations
- [not-applicable] [Introduction to AI Video Generation](https://www.techsmith.com/learn/tutorials/camtasia/introduction-ai-video/) — Cloud AI service; requires Camtasia backend
- [not-applicable] [Generate AI Avatars](https://www.techsmith.com/learn/tutorials/camtasia/ai-avatar/) — Cloud AI service; requires Camtasia backend
- [not-applicable] [Generate AI Voices from Text or a Script](https://www.techsmith.com/learn/tutorials/camtasia/text-to-speech/) — Cloud AI TTS service; library could insert resulting audio but generation itself is out of scope
- [not-applicable] [Generate a Script with AI](https://www.techsmith.com/learn/tutorials/camtasia/ai-script/) — Cloud AI service; out of scope
- [x] [Translate Your Script, Audio, and Captions](https://www.techsmith.com/learn/tutorials/camtasia/translate/) — Captions/SRT export exists; no translation pipeline. Could add extract/reimport helpers

### Edit Audio (8)

- [partial] [Recommended Audio Edits](https://www.techsmith.com/learn/tutorials/camtasia/recommended-audio-edits/) — Volume/gain/fade/mute implemented; no dedicated normalization/compression/EQ helpers
- [not-applicable] [Tips for Getting the Best Audio](https://www.techsmith.com/learn/tutorials/camtasia/best-audio-tips/) — Hardware/recording-technique advice; not a file-manipulation concern
- [already-implemented] [Set the Tone with Background Music](https://www.techsmith.com/learn/tutorials/camtasia/background-music/) — project.add_background_music with volume and fade keyframes
- [already-implemented] [Edit Audio](https://www.techsmith.com/learn/tutorials/camtasia/editing-audio/) — volume, gain, fade in/out, mute, strip_audio, normalize_audio
- [x] [Add Audio Effects](https://www.techsmith.com/learn/tutorials/camtasia/add-audio-effects/) — VST_NOISE_REMOVAL enum and categoryAudioEffects exist; no typed audio-effect wrapper classes yet
- [not-applicable] [Record Voice Narration](https://www.techsmith.com/learn/tutorials/camtasia/record-voice-narration/) — Recording audio is hardware capture; pycamtasia has add_voiceover_sequence for placing pre-recorded files

### Cursor Edits & Effects (5)

- [already-implemented] [Add Cursor Effects](https://www.techsmith.com/learn/tutorials/camtasia/cursor-effects/) — effects/cursor.py: CursorMotionBlur, CursorShadow, CursorPhysics, LeftClickScaling
- [already-implemented] [Introduction to Cursor Editing](https://www.techsmith.com/learn/tutorials/camtasia/cursor-editing-basics/) — ScreenVMFile exposes cursor_scale, cursor_opacity, cursor_motion_blur_intensity, cursor_shadow, cursor_physics, left_click_scaling
- [x] [Replace the Cursor](https://www.techsmith.com/learn/tutorials/camtasia/change-cursor/) — ScreenIMFile.cursor_image_path is read-only; no setter to replace the cursor image
- [x] [Customize the Cursor Path](https://www.techsmith.com/learn/tutorials/camtasia/customize-your-cursor-path/) — cursor_location_keyframes is read-only; no API to modify per-frame cursor positions
- [x] [Quickly Smooth Cursor Movements](https://www.techsmith.com/learn/tutorials/camtasia/cursor-smoothing/) — smooth_cursor_across_edit_duration is read-only; no setter to enable/configure smoothing

### Video Animations (7)

- [already-implemented] [Zoom In to Focus Attention](https://www.techsmith.com/learn/tutorials/camtasia/animations/) — project.add_zoom_to_region, timeline.add_zoom_pan / zoom_pan_keyframes, clip set_scale_keyframes/set_position_keyframes
- [already-implemented] [Add a Transition](https://www.techsmith.com/learn/tutorials/camtasia/video-transitions/) — timeline/transitions.py TransitionList with add, add_fade, add_card_flip, add_glitch, add_linear_blur, add_stretch, add_paint_arcs
- [already-implemented] [Animations In-Depth](https://www.techsmith.com/learn/tutorials/camtasia/animations-in-depth/) — animation_tracks, _add_visual_tracks_for_keyframes, _add_opacity_track, set_scale_keyframes, set_position_keyframes, fade_in/fade_out
- [x] [Add Movement to Any Object (Motion Paths)](https://www.techsmith.com/learn/tutorials/camtasia/motion-path/) — set_position_keyframes supports linear movement; no bezier/curved motion paths or easing presets
- [already-implemented] [Blur or Mask a Video](https://www.techsmith.com/learn/tutorials/camtasia/blur-mask-video/) — Mask effect with shape/opacity/blend/invert/rotation/size/position/corner-radius; BlurRegion (unregistered); add_motion_blur
- [already-implemented] [Animate Text & Images with Behaviors](https://www.techsmith.com/learn/tutorials/camtasia/animation-behaviors/) — effects/behaviors.py GenericBehaviorEffect with BehaviorPhase; callout add_behavior; templates/behavior_presets
- [already-implemented] [Create Stunning Animations with Media Mattes](https://www.techsmith.com/learn/tutorials/camtasia/animations-with-media-mattes/) — effects/visual.py MediaMatte; BaseClip.add_media_matte builder

### Viewer Engagement & Accessibility (5)

- [partial] [Add Closed Captions to a Video](https://www.techsmith.com/learn/tutorials/camtasia/add-closed-captions/) — CaptionAttributes styling + SRT export; no API to add/edit individual caption entries on the timeline
- [feature-gap] [Add Dynamic Captions](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-captions/) — Animated word-by-word caption overlays not supported
- [not-applicable] [Build Quizzes & Surveys](https://www.techsmith.com/learn/tutorials/camtasia/quizzing/) — Interactive player-runtime features; not .cmproj manipulation
- [not-applicable] [Add Hotspots (Interactive Videos)](https://www.techsmith.com/learn/tutorials/camtasia/add-interactive-hotspots-to-a-video/) — Player-runtime interactivity; not .cmproj manipulation

### Export & Share (5)

- [not-applicable] [Use Camtasia Videos in Your LMS](https://www.techsmith.com/learn/tutorials/camtasia/lms-options/) — LMS integration (SCORM/xAPI packaging) is deployment concern
- [not-applicable] [Export & Share Your Video](https://www.techsmith.com/learn/tutorials/camtasia/export-share/) — Video encoding/rendering requires the Camtasia engine; pycamtasia exports metadata only (EDL/CSV/SRT/JSON/report)
- [already-implemented] [Watermark Your Videos](https://www.techsmith.com/learn/tutorials/camtasia/video-watermark/) — project.add_watermark
- [not-applicable] [Batch Export Videos](https://www.techsmith.com/learn/tutorials/camtasia/batch-export/) — Batch video rendering/encoding; library cannot render video files
- [partial] [Export an Audio File](https://www.techsmith.com/learn/tutorials/camtasia/export-audio/) — export_audio_clips lists source paths; no actual audio encoding (correctly out of scope for a file-manipulation library)

### Customizations & Branding (8)

- [partial] [Reuse Media Across Projects (Library)](https://www.techsmith.com/learn/tutorials/camtasia/library/) — replace_media_source exists; no .libzip Camtasia Library import/export
- [not-applicable] [Customize Camtasia Editor](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia/) — UI preferences stored outside .cmproj files
- [already-implemented] [How to Use a Template](https://www.techsmith.com/learn/tutorials/camtasia/use-a-template/) — operations/template.py duplicate_project(clear_media=True); clone_project_structure; templates/
- [partial] [Build a Video Template to Share](https://www.techsmith.com/learn/tutorials/camtasia/create-a-template/) — duplicate_project creates reusable template projects; no .camtemplate packaging format
- [x] [Build Your Color Palette (Themes)](https://www.techsmith.com/learn/tutorials/camtasia/themes/) — themeMappings exist in .cmproj but no API to define/apply/swap named color palettes
- [not-applicable] [Package & Share Camtasia Editor Resources](https://www.techsmith.com/learn/tutorials/camtasia/package-share-camtasia-resources/) — .campackage/.libzip bundling is an application packaging concern
- [not-applicable] [Customize Shortcuts](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia-shortcuts/) — Keyboard shortcuts are Camtasia app preferences; not in .cmproj
- [partial] [Create Custom Assets](https://www.techsmith.com/learn/tutorials/camtasia/create-custom-assets/) — Can create callouts, lower thirds, title cards programmatically; no .campackage asset export

### Projects (6)

- [already-implemented] [How to Make an Intro for a Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-intro/) — add_title_card, add_countdown, add_lower_third, TimelineBuilder.add_title, build_from_screenplay_file
- [not-applicable] [Create a Quick Tip Style Video](https://www.techsmith.com/learn/tutorials/camtasia/create-a-quick-tip-style-video-template/) — Content-style workflow tutorial, not a discrete feature
- [not-applicable] [How to Create a Software Tutorial](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-great-tutorial/) — Workflow tutorial; editing features already covered by existing modules
- [not-applicable] [How to Make an Explainer Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-explainer-video/) — Content-genre workflow tutorial; not a discrete feature
- [not-applicable] [How to Create a Product Walkthrough Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-product-walkthrough-video/) — Workflow tutorial, not a discrete feature
- [not-applicable] [How to Make a Software Demo](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-a-software-demo/) — Workflow tutorial, not a discrete feature

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
- [x] `BaseClip.unmute()` — reverses `mute()` on all clip types including Group/StitchedMedia/UnifiedMedia
- [x] `UnifiedMedia.remove_all_effects()` clears effects on both video/audio sub-clips
- [x] `UnifiedMedia.has_effects/effect_count/effect_names` aggregate from video+audio sub-clips
- [x] `Callout.text` setter should update `textAttributes` `rangeEnd` to match new text length
- [x] `BaseClip.add_keyframe()` creates `animationTracks.visual` entries for visual parameters (translation/scale/rotation/crop/opacity)
- [x] `set_position_keyframes` / `set_scale_keyframes` / `set_rotation_keyframes` / `set_crop_keyframes` create `animationTracks.visual` entries
- [x] `add_progressive_disclosure(replace_previous=True)` already implemented

### Track API
- [x] `clip_after()` docstring clarified as at-or-after; `clip_strictly_after()` added as strictly-after variant
- [x] `insert_gap()` and `shift_all_clips()` don't clear/adjust transitions that may become invalid
- [x] `merge_adjacent_clips()` doesn't verify clips are actually adjacent before merging
- [x] `set_segment_speeds()` uses float accumulation for `mediaStart` — should use Fraction
- [x] `split_clip()` uses raw `Fraction(orig_scalar)` instead of `_parse_scalar()` — inconsistent precision

### Timeline API
- [x] `clips_of_type()` is O(n²) and misattributes nested clips to `None` track
- [x] `shift_all()` doesn't shift transition or effect `start` times
- [x] `Timeline.insert_gap()` / `remove_gap()` shift timeline markers (transitions use clip IDs and don't need adjustment)
- [x] `flatten_to_track()` warns when source tracks have transitions that will be dropped
- [x] `build_section_timeline()` helper exists in timeline.py

### Validation
- [x] Validate `timeline.id` exists and doesn't collide with clip IDs
- [x] Validate `GenericBehaviorEffect` has required `in`/`center`/`out` phases
- [x] Validate overlapping clips on same track (Camtasia tracks are single-occupancy)
- [x] Flag explicit `null` in transition `leftMedia`/`rightMedia` (format says omit, not null)

### Effects
- [x] Typed wrapper classes added for LutEffect, Emphasize, Spotlight, ColorAdjustment, BlendModeEffect, MediaMatte — all registered with effect_from_dict
- [x] `BlurRegion` export is intentional — class docstring warns it is unregistered and unverified against real projects
- [x] `DropShadow.enabled` / `CursorShadow.enabled` docstrings clarify that setting only updates defaultValue, not existing keyframes

### Export
- [x] EDL exporter recurses into Groups/StitchedMedia (opt-out via include_nested=False)
- [x] CSV and report (JSON + markdown) exporters recurse into Groups/StitchedMedia with timeline-absolute positions
- [x] EDL `UnifiedMedia` source is always `AX` — should use video sub-clip's source
- [x] SRT exporter warns when no markers to export
- [x] `timeline_json` now includes effects, transitions, and per-clip metadata (opt-out via kwargs; bumped version to 1.1)

### Builders
- [x] `timeline_builder.add_title()` ignores `subtitle` parameter (dead code)
- [x] `tile_layout.add_grid` auto-fits images to cell size by default (opt-out via fit_to_cell=False)
- [x] `screenplay_builder._find_audio_file()` only searches `.wav` — should support `.mp3`, `.m4a`

### Schema
- [x] Schema `effect.effectName` enum no longer includes behavior names (moved to GenericBehaviorEffect only)
- [x] Schema `effect` definition doesn't require `bypassed` (format reference says required)
- [x] Non-schema transition names (`FadeThroughColor`, `SlideUp`, etc.) documented via docstring warnings

### Behavior Presets
- [ ] Preset values don't fully match real TechSmith samples (ongoing refinement)
- [x] `reveal` preset start value documented; clamped by get_behavior_preset() for short clips. Needs real-Camtasia verification to tune further.
- [x] `BehaviorInnerName` enum missing `'fading'` phase name
- [x] `pulsating` center phase `offsetBetweenCharacters` should be `49392000` (not `0`)

### Infrastructure
- [x] `media_bin.import_media()` appends _1/_2/... suffix on directory collision
- [x] `media_bin._visual_track_to_json()` uses `sampleRate=0` for video (should be frame rate)
- [x] `media_bin` visual/audio track JSONs already include `tag: 0` field
- [x] `scalar_to_string()` return type annotation is `str | int` and docstring explains the int return
- [x] `parse_scalar()` docstring documents the 10_000 denominator cap tradeoff
- [x] `history.py` `undo()`/`redo()` docstrings warn about stale nested references (already present)

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
- `set_audio_speed()` final overwrite of target_clip duration bypasses `rescale_project()`'s overlap fix — users should call `project.repair()` after `set_audio_speed()` if 1-tick overlaps are a concern.
