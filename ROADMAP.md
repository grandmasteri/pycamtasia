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
- [already-implemented] [Import Presentation Slides](https://www.techsmith.com/learn/tutorials/camtasia/import-powerpoint-slides/) — No PPTX import; would extract slide images and place as media on timeline

### Enhance Your Video (12)

- [already-implemented] [Visual Effects Overview](https://www.techsmith.com/learn/tutorials/camtasia/visual-effects/) — Comprehensive effects/ module: DropShadow, Glow, Mask, BlurRegion, ColorAdjustment, LutEffect, etc.
- [already-implemented] [Add Arrows, Shapes, & Callouts](https://www.techsmith.com/learn/tutorials/camtasia/annotations/) — annotations/callouts.py (text, square, arrow, highlight, keystroke_callout) and shapes.py (rectangle)
- [deferred: needs fixture] [Add a Dynamic Background](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-backgrounds/) — TimelineBuilder.add_background_image for static; no animated/dynamic background generator yet
- [deferred: needs fixture] [4 Ways to Visualize Your Audio](https://www.techsmith.com/learn/tutorials/camtasia/audio-visualizers/) — Audio visualizers are likely rendered at export time by the Camtasia engine and do not appear as parameterized effects in any of our .tscproj fixtures. Implementing without a real fixture showing the JSON structure would produce invalid output. Revisit when a reference project is available.
- [already-implemented] [Create the Illusion of 3D Perspective (Corner Pinning)](https://www.techsmith.com/learn/tutorials/camtasia/corner-pinning/) — No CornerPin effect class
- [already-implemented] [Remove a Background from Your Video](https://www.techsmith.com/learn/tutorials/camtasia/video-background-removal/) — MediaMatte effect in effects/visual.py is Camtasia’s matte/background-removal mechanism
- [already-implemented] [Enhance Your Video Overview](https://www.techsmith.com/learn/tutorials/camtasia/enhance-video/) — ColorAdjustment, LutEffect, DropShadow, Glow, Emphasize, Spotlight, MotionBlur, RoundCorners
- [already-implemented] [Add Video Filters](https://www.techsmith.com/learn/tutorials/camtasia/filters/) — effects/visual.py provides color grading (LutEffect), blend modes, Spotlight, Emphasize, MotionBlur
- [already-implemented] [Provide Context with Device Frames](https://www.techsmith.com/learn/tutorials/camtasia/device-frames/) — No device frame overlay (phone/laptop/tablet bezels)
- [already-implemented] [Remove A Color (Green Screen)](https://www.techsmith.com/learn/tutorials/camtasia/how-to-remove-a-color/) — No dedicated chroma key / color-key effect; MediaMatte is a different matte concept

### Edit on the Timeline (13)

- [already-implemented] [Basic Edits After Recording](https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/) — trim/split/reorder via timeline/clips/base.py; ripple_insert/delete in operations/layout.py
- [not-applicable] [3 Keys to the Camtasia Editor Timeline](https://www.techsmith.com/learn/tutorials/camtasia/timeline-key-concepts/) — UI-orientation tutorial for the desktop app
- [not-applicable] [Explore the Timeline](https://www.techsmith.com/learn/tutorials/camtasia/video-editing/) — UI-orientation tutorial; pycamtasia already models the timeline fully
- [already-implemented] [Add Markers & Video Table of Contents](https://www.techsmith.com/learn/tutorials/camtasia/markers-and-table-of-contents/) — timeline/markers.py MarkerList with add/remove/clear/replace; exported as SRT
- [already-implemented] [Freeze Video Clips with Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/extend-frame/) — track.py add_freeze_frame method on Track
- [already-implemented] [Speed Up & Slow Down Video Clips](https://www.techsmith.com/learn/tutorials/camtasia/clip-speed/) — clips/base.py set_speed, scalar, operations/speed.py rescale_project, set_segment_speeds
- [already-implemented] [Join Clips Together](https://www.techsmith.com/learn/tutorials/camtasia/stitch-media/) — StitchedMedia clip type exists; no explicit single-track “join two adjacent clips” operation yet
- [already-implemented] [Move Multiple Clips at Once](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move/) — operations/batch.py move_all, apply_to_clips; track.py move_clip
- [already-implemented] [Ripple Move & Extend Frame](https://www.techsmith.com/learn/tutorials/camtasia/ripple-move-and-extend-frame/) — operations/layout.py ripple_insert/delete; add_freeze_frame
- [already-implemented] [Close Timeline Gaps with Magnetic Tracks](https://www.techsmith.com/learn/tutorials/camtasia/magnetic-tracks/) — track.magnetic property; operations/layout.py pack_track

### AI Video (6)

- [deferred: needs fixture] [Speed Up Editing with Camtasia Audiate](https://www.techsmith.com/learn/tutorials/camtasia/camtasia-audio-sync/) — Read-only Audiate transcript parsing is already implemented. Write-back requires the Audiate session JSON schema which is not present in any fixture and not publicly documented. Implementing blindly would produce invalid JSON; deferred pending a reference fixture.
- [not-applicable] [Introduction to AI Video Generation](https://www.techsmith.com/learn/tutorials/camtasia/introduction-ai-video/) — Cloud AI service; requires Camtasia backend
- [not-applicable] [Generate AI Avatars](https://www.techsmith.com/learn/tutorials/camtasia/ai-avatar/) — Cloud AI service; requires Camtasia backend
- [not-applicable] [Generate AI Voices from Text or a Script](https://www.techsmith.com/learn/tutorials/camtasia/text-to-speech/) — Cloud AI TTS service; library could insert resulting audio but generation itself is out of scope
- [not-applicable] [Generate a Script with AI](https://www.techsmith.com/learn/tutorials/camtasia/ai-script/) — Cloud AI service; out of scope
- [already-implemented] [Translate Your Script, Audio, and Captions](https://www.techsmith.com/learn/tutorials/camtasia/translate/) — Captions/SRT export exists; no translation pipeline. Could add extract/reimport helpers

### Edit Audio (8)

- [deferred: scope] [Recommended Audio Edits](https://www.techsmith.com/learn/tutorials/camtasia/recommended-audio-edits/) — Fundamental audio edits (gain, fade, mute, Emphasize, NoiseRemoval) are fully implemented. Dedicated normalization/compression/EQ would either require Python DSP (scipy/librosa, out of scope for a file-manipulation library) or typed effect wrappers for Camtasia effects that do not appear in any fixture. Deferred pending a reference fixture for any missing effect.
- [not-applicable] [Tips for Getting the Best Audio](https://www.techsmith.com/learn/tutorials/camtasia/best-audio-tips/) — Hardware/recording-technique advice; not a file-manipulation concern
- [already-implemented] [Set the Tone with Background Music](https://www.techsmith.com/learn/tutorials/camtasia/background-music/) — project.add_background_music with volume and fade keyframes
- [already-implemented] [Edit Audio](https://www.techsmith.com/learn/tutorials/camtasia/editing-audio/) — volume, gain, fade in/out, mute, strip_audio, normalize_audio
- [deferred: needs fixture] [Add Audio Effects](https://www.techsmith.com/learn/tutorials/camtasia/add-audio-effects/) — VST_NOISE_REMOVAL enum and categoryAudioEffects exist; no typed audio-effect wrapper classes yet
- [not-applicable] [Record Voice Narration](https://www.techsmith.com/learn/tutorials/camtasia/record-voice-narration/) — Recording audio is hardware capture; pycamtasia has add_voiceover_sequence for placing pre-recorded files

### Cursor Edits & Effects (5)

- [already-implemented] [Add Cursor Effects](https://www.techsmith.com/learn/tutorials/camtasia/cursor-effects/) — effects/cursor.py: CursorMotionBlur, CursorShadow, CursorPhysics, LeftClickScaling
- [already-implemented] [Introduction to Cursor Editing](https://www.techsmith.com/learn/tutorials/camtasia/cursor-editing-basics/) — ScreenVMFile exposes cursor_scale, cursor_opacity, cursor_motion_blur_intensity, cursor_shadow, cursor_physics, left_click_scaling
- [already-implemented] [Replace the Cursor](https://www.techsmith.com/learn/tutorials/camtasia/change-cursor/) — ScreenIMFile.cursor_image_path is read-only; no setter to replace the cursor image
- [already-implemented] [Customize the Cursor Path](https://www.techsmith.com/learn/tutorials/camtasia/customize-your-cursor-path/) — cursor_location_keyframes is read-only; no API to modify per-frame cursor positions
- [already-implemented] [Quickly Smooth Cursor Movements](https://www.techsmith.com/learn/tutorials/camtasia/cursor-smoothing/) — smooth_cursor_across_edit_duration is read-only; no setter to enable/configure smoothing

### Video Animations (7)

- [already-implemented] [Zoom In to Focus Attention](https://www.techsmith.com/learn/tutorials/camtasia/animations/) — project.add_zoom_to_region, timeline.add_zoom_pan / zoom_pan_keyframes, clip set_scale_keyframes/set_position_keyframes
- [already-implemented] [Add a Transition](https://www.techsmith.com/learn/tutorials/camtasia/video-transitions/) — timeline/transitions.py TransitionList with add, add_fade, add_card_flip, add_glitch, add_linear_blur, add_stretch, add_paint_arcs
- [already-implemented] [Animations In-Depth](https://www.techsmith.com/learn/tutorials/camtasia/animations-in-depth/) — animation_tracks, _add_visual_tracks_for_keyframes, _add_opacity_track, set_scale_keyframes, set_position_keyframes, fade_in/fade_out
- [deferred: needs fixture] [Add Movement to Any Object (Motion Paths)](https://www.techsmith.com/learn/tutorials/camtasia/motion-path/) — set_position_keyframes supports linear movement; no bezier/curved motion paths or easing presets
- [already-implemented] [Blur or Mask a Video](https://www.techsmith.com/learn/tutorials/camtasia/blur-mask-video/) — Mask effect with shape/opacity/blend/invert/rotation/size/position/corner-radius; BlurRegion (unregistered); add_motion_blur
- [already-implemented] [Animate Text & Images with Behaviors](https://www.techsmith.com/learn/tutorials/camtasia/animation-behaviors/) — effects/behaviors.py GenericBehaviorEffect with BehaviorPhase; callout add_behavior; templates/behavior_presets
- [already-implemented] [Create Stunning Animations with Media Mattes](https://www.techsmith.com/learn/tutorials/camtasia/animations-with-media-mattes/) — effects/visual.py MediaMatte; BaseClip.add_media_matte builder

### Viewer Engagement & Accessibility (5)

- [already-implemented] [Add Closed Captions to a Video](https://www.techsmith.com/learn/tutorials/camtasia/add-closed-captions/) — CaptionAttributes styling + SRT export; no API to add/edit individual caption entries on the timeline
- [deferred: needs fixture] [Add Dynamic Captions](https://www.techsmith.com/learn/tutorials/camtasia/dynamic-captions/) — Animated word-by-word caption overlays have no representation in any fixture project. Implementing the feature without seeing the actual JSON structure would produce speculative output that may not load in Camtasia. Deferred pending a reference fixture.
- [not-applicable] [Build Quizzes & Surveys](https://www.techsmith.com/learn/tutorials/camtasia/quizzing/) — Interactive player-runtime features; not .cmproj manipulation
- [not-applicable] [Add Hotspots (Interactive Videos)](https://www.techsmith.com/learn/tutorials/camtasia/add-interactive-hotspots-to-a-video/) — Player-runtime interactivity; not .cmproj manipulation

### Export & Share (5)

- [not-applicable] [Use Camtasia Videos in Your LMS](https://www.techsmith.com/learn/tutorials/camtasia/lms-options/) — LMS integration (SCORM/xAPI packaging) is deployment concern
- [not-applicable] [Export & Share Your Video](https://www.techsmith.com/learn/tutorials/camtasia/export-share/) — Video encoding/rendering requires the Camtasia engine; pycamtasia exports metadata only (EDL/CSV/SRT/JSON/report)
- [already-implemented] [Watermark Your Videos](https://www.techsmith.com/learn/tutorials/camtasia/video-watermark/) — project.add_watermark
- [not-applicable] [Batch Export Videos](https://www.techsmith.com/learn/tutorials/camtasia/batch-export/) — Batch video rendering/encoding; library cannot render video files
- [deferred: scope] [Export an Audio File](https://www.techsmith.com/learn/tutorials/camtasia/export-audio/) — The metadata export side (listing source paths for external tools to mix) is implemented via export_audio_clips(). Actual audio rendering/encoding requires an audio engine (ffmpeg/libav/similar) which is strictly out of scope for a project-file-manipulation library. Users are expected to feed the output of export_audio_clips() into their preferred encoder.

### Customizations & Branding (8)

- [deferred: needs fixture] [Reuse Media Across Projects (Library)](https://www.techsmith.com/learn/tutorials/camtasia/library/) — Cross-project media reuse is already supported via replace_media_source() and operations/template.py. The native .libzip Library format is an undocumented Camtasia-specific archive that would need to be reverse-engineered from real library bundles. Deferred pending reference archives.
- [not-applicable] [Customize Camtasia Editor](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia/) — UI preferences stored outside .cmproj files
- [already-implemented] [How to Use a Template](https://www.techsmith.com/learn/tutorials/camtasia/use-a-template/) — operations/template.py duplicate_project(clear_media=True); clone_project_structure; templates/
- [deferred: needs fixture] [Build a Video Template to Share](https://www.techsmith.com/learn/tutorials/camtasia/create-a-template/) — Template semantics are fully supported via operations/template.py (duplicate_project with clear_media, clone_project_structure). The wire format .camtemplate is an undocumented Camtasia-specific archive that would need reverse-engineering. Deferred pending reference archives.
- [already-implemented] [Build Your Color Palette (Themes)](https://www.techsmith.com/learn/tutorials/camtasia/themes/) — themeMappings exist in .cmproj but no API to define/apply/swap named color palettes
- [not-applicable] [Package & Share Camtasia Editor Resources](https://www.techsmith.com/learn/tutorials/camtasia/package-share-camtasia-resources/) — .campackage/.libzip bundling is an application packaging concern
- [not-applicable] [Customize Shortcuts](https://www.techsmith.com/learn/tutorials/camtasia/customize-camtasia-shortcuts/) — Keyboard shortcuts are Camtasia app preferences; not in .cmproj
- [deferred: needs fixture] [Create Custom Assets](https://www.techsmith.com/learn/tutorials/camtasia/create-custom-assets/) — Programmatic creation of callouts, lower thirds, and title cards is fully supported. The .campackage asset-sharing archive format is an undocumented Camtasia-specific wire format that would need reverse-engineering. Deferred pending reference archives.

### Projects (6)

- [already-implemented] [How to Make an Intro for a Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-intro/) — add_title_card, add_countdown, add_lower_third, TimelineBuilder.add_title, build_from_screenplay_file
- [not-applicable] [Create a Quick Tip Style Video](https://www.techsmith.com/learn/tutorials/camtasia/create-a-quick-tip-style-video-template/) — Content-style workflow tutorial, not a discrete feature
- [not-applicable] [How to Create a Software Tutorial](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-great-tutorial/) — Workflow tutorial; editing features already covered by existing modules
- [not-applicable] [How to Make an Explainer Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-explainer-video/) — Content-genre workflow tutorial; not a discrete feature
- [not-applicable] [How to Create a Product Walkthrough Video](https://www.techsmith.com/learn/tutorials/camtasia/how-to-create-a-product-walkthrough-video/) — Workflow tutorial, not a discrete feature
- [not-applicable] [How to Make a Software Demo](https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-a-software-demo/) — Workflow tutorial, not a discrete feature

## Deep Tutorial Analysis (detailed feature-level gaps)

_Each item below represents a specific feature/operation mentioned in an official TechSmith Camtasia tutorial that pycamtasia does not fully support. Verified by reading the full tutorial content and checking against source code. Supersedes the prior coarse-grained triage above._

### Add Audio Effects

Source: https://www.techsmith.com/learn/tutorials/camtasia/add-audio-effects/

- [ ] **Audio Compression effect missing (Ratio/Threshold/Gain/Variation)** `src/camtasia/effects/audio.py` — `AudioCompression class`
- [ ] **ClipSpeed audio effect missing (Speed/Duration)** `src/camtasia/effects/audio.py` — `ClipSpeed class`
- [ ] **Pitch effect missing (Mac — Pitch/Ease In/Out)** `src/camtasia/effects/audio.py` — `Pitch class`
- [ ] **audio-specific Fade In / Fade Out wrappers missing** `src/camtasia/timeline/clips/base.py` — `add_audio_fade_in / add_audio_fade_out`
- [ ] **NoiseRemoval Sensitivity and Reduction (Mac) params missing** `src/camtasia/effects/audio.py` — `NoiseRemoval.sensitivity / reduction`
- [ ] **EffectName enum missing AudioCompression/ClipSpeed/Pitch entries** `src/camtasia/types.py` — `EffectName members`
- [ ] **Emphasize ramp_position (Outside/Span/Inside) not exposed** `src/camtasia/timeline/clips/base.py` — `add_emphasize(ramp_position=, ramp_in=, ramp_out=)`

### Add Closed Captions to a Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/add-closed-captions/

- [ ] **Import captions from SRT/VTT/SAMI** `src/camtasia/export/captions.py` — `import_captions_srt`
- [ ] **Export captions as SRT/VTT/SAMI (not just markers)** `src/camtasia/export/srt.py` — `export_captions_as_srt`
- [ ] **Add a single caption entry to timeline** `src/camtasia/timeline/timeline.py` — `Timeline.add_caption(text, start, duration, track_name)`
- [ ] **Edit/remove caption by index** `src/camtasia/timeline/timeline.py` — `Timeline.edit_caption / remove_caption`
- [ ] **Split overlong caption ('Split' button)** `src/camtasia/timeline/timeline.py` — `Timeline.split_caption`
- [ ] **Merge adjacent captions** `src/camtasia/timeline/timeline.py` — `Timeline.merge_caption_with_next`
- [ ] **Caption vertical position / anchor** `src/camtasia/timeline/captions.py` — `CaptionAttributes.position / vertical_anchor`
- [ ] **Speech-to-text auto-caption generation** `src/camtasia/operations/` — `generate_captions_from_audio`
- [ ] **Sync script to audio playback (Windows workflow)** `src/camtasia/operations/` — `sync_script_to_captions`
- [ ] **Burned-in (open) captions export toggle** `src/camtasia/export/` — `export_video(caption_style='burned_in')`
- [ ] **ADA/accessibility compliance validator (line-length/duration/contrast)** `src/camtasia/validation.py` — `validate_caption_accessibility`
- [ ] **Default caption duration setting (Camtasia default 4s)** `src/camtasia/timeline/captions.py` — `CaptionAttributes.default_duration_seconds`

### Animate Text & Images with Behaviors

Source: https://www.techsmith.com/learn/tutorials/camtasia/animation-behaviors/

- [ ] **flyOut preset missing** `src/camtasia/templates/behavior_presets.py` — `PRESETS['flyOut']`
- [ ] **emphasize preset missing** `src/camtasia/templates/behavior_presets.py` — `PRESETS['emphasize']`
- [ ] **jiggle preset missing** `src/camtasia/templates/behavior_presets.py` — `PRESETS['jiggle']`
- [ ] **No classmethod factories on GenericBehaviorEffect to instantiate presets by name** `src/camtasia/effects/behaviors.py` — `GenericBehaviorEffect.from_preset(name, duration)`
- [ ] **BehaviorPhase lacks loop-phase fields as typed properties** `src/camtasia/effects/behaviors.py` — `seconds_per_loop/number_of_loops/delay_between_loops`
- [ ] **No enum/constants for movement/characterOrder values** `src/camtasia/effects/behaviors.py` — `Movement/CharacterOrder IntEnum`
- [ ] **During-phase style params not surfaced as typed properties** `src/camtasia/effects/behaviors.py` — `BehaviorPhase.opacity/jump/rotation/scale/shift`

### Zoom In to Focus Attention

Source: https://www.techsmith.com/learn/tutorials/camtasia/animations/

- [ ] **SmartFocus auto-animation on .trec recordings** `src/camtasia/project.py` — `apply_smart_focus`
- [ ] **SmartFocus at Time (Mac) - apply at playhead** `src/camtasia/project.py` — `apply_smart_focus_at_time`
- [ ] **Preset named animations (Scale Up/Down/To Fit/Custom) as first-class API** `src/camtasia/project.py` — `add_animation(preset=...)`
- [ ] **Zoom-n-Pan rectangle API (viewport rect vs scale+center)** `src/camtasia/timeline/timeline.py` — `add_zoom_n_pan_rect(x,y,w,h)`
- [ ] **Animation arrow ease-in/out parameters** `src/camtasia/project.py` — `add_zoom_to_region(ease_in, ease_out)`
- [ ] **Scale to Fit helper (reset zoom to entire canvas)** `src/camtasia/timeline/timeline.py` — `add_scale_to_fit`

### Animations In-Depth

Source: https://www.techsmith.com/learn/tutorials/camtasia/animations-in-depth/

- [ ] **Named easing presets (Exponential In/Out, Linear, Bounce, Spring, Auto) — code only accepts raw codes** `src/camtasia/timeline/clips/base.py` — `Easing enum + mapping in keyframe APIs`
- [ ] **Skew parameter keyframes and setter** `src/camtasia/timeline/clips/base.py` — `set_skew / set_skew_keyframes`
- [ ] **Rotation on X and Y axes (only Z exposed)** `src/camtasia/timeline/clips/base.py` — `rotation_x/rotation_y setters and keyframes`
- [ ] **Z-axis position (translation2) not exposed** `src/camtasia/timeline/clips/base.py` — `translation_z in move_to / set_position_keyframes`
- [ ] **Pixel-based Size with aspect-ratio lock** `src/camtasia/timeline/clips/base.py` — `set_size_pixels`
- [ ] **restore_animation alias matching UI 'Restore' button** `src/camtasia/timeline/clips/base.py` — `restore_animation alias for clear_animations + reset_transforms`
- [ ] **Animation arrow abstraction (named Animation object)** `src/camtasia/timeline/clips/base.py` — `add_animation(start, end, scale=, position=, rotation=, opacity=, easing=)`
- [ ] **Bounce and Spring easing codes + physics params** `src/camtasia/timeline/clips/base.py` — `interp whitelist expansion`
- [ ] **Edit-All-Animations mode** `src/camtasia/timeline/clips/base.py` — `apply_to_all_animations`

### Create Stunning Animations with Media Mattes

Source: https://www.techsmith.com/learn/tutorials/camtasia/animations-with-media-mattes/

- [ ] **MediaMatte.mode only 1/2 documented but Camtasia has 4 modes (Alpha, Alpha Invert, Luminosity, Luminosity Invert); fixtures use mode=3** `src/camtasia/effects/visual.py` — `MediaMatte.mode full enum coverage`
- [ ] **MatteMode enum not defined in types.py** `src/camtasia/types.py` — `MatteMode IntEnum`
- [ ] **add_media_matte lacks ease_in/ease_out parameters** `src/camtasia/timeline/clips/base.py` — `add_media_matte(..., ease_in_seconds, ease_out_seconds)`
- [ ] **Track-level matte attribute setter missing (right-click track -> Alpha/Luminosity/...)** `src/camtasia/timeline/track.py` — `Track.matte_mode property`
- [ ] **No documentation of compatible transparent media formats** `src/camtasia/timeline/clips/base.py` — `add_media_matte docstring`
- [ ] **add_media_matte default preset_name mismatches default matte_mode** `src/camtasia/timeline/clips/base.py` — `derive preset_name from matte_mode`

### annotations

Source: 

- [ ] **Sketch Motion Callout (animated drawing callout: sketch circle, sketch arrow) — no factory, no 'sketch' style anywhere in library** `annotations/callouts.py` — `sketch_motion_callout`
- [ ] **Sketch Motion draw-time property (how long the sketch animates on)** `annotations/callouts.py` — `sketch_motion_callout(..., draw_time=...)`
- [ ] **Line annotation (tutorial lists 'Arrows & Lines' — only arrow() exists)** `annotations/callouts.py` — `line`
- [ ] **Ellipse / circle shape annotation (schema has 'shape-ellipse' but no factory in shapes.py)** `annotations/shapes.py` — `ellipse`
- [ ] **Additional shapes shown in Shapes subtab (polygon, rounded-rectangle, triangle, speech bubble) — only rectangle() exposed** `annotations/shapes.py` — `polygon / rounded_rectangle / triangle`
- [ ] **Shadow (hasDropShadow) on callout/shape annotations — hardcoded to 0.0 in square/keystroke, not exposed as parameter** `annotations/callouts.py` — `square(..., drop_shadow=True)`
- [ ] **Corner-radius on shape/square callouts — hardcoded to 0.0, not exposed** `annotations/shapes.py` — `rectangle(..., corner_radius=...)`
- [ ] **Callout tail for speech-bubble style — tail-x/tail-y hardcoded, not parameterized** `annotations/callouts.py` — `square(..., tail=(x,y))`
- [ ] **Italic / underline / strikethrough text properties — _text_attributes always writes 0 and callers cannot override** `annotations/callouts.py` — `text(..., italic=..., underline=..., strikethrough=...)`
- [ ] **Lower-third / title preset callout helpers — templates/lower_third.py exists but no public annotation factory in camtasia.annotations** `annotations/__init__.py` — `lower_third / title`
- [ ] **Gradient fill for callouts/shapes — FillStyle.Gradient exists but no gradient-stop parameters accepted** `annotations/callouts.py` — `square(..., gradient_stops=...)`
- [ ] **Favorites / preset annotations (save/load custom annotation for reuse)** `annotations/__init__.py` — `save_as_favorite / load_favorite`

### 4 Ways to Visualize Your Audio

Source: https://www.techsmith.com/learn/tutorials/camtasia/audio-visualizers/

- [ ] **Audio visualizer feature entirely absent from library (no 'visualizer'/'waveform' code)** `src/camtasia/effects/` — `AudioVisualizer effect class with type/style/color parameters`
- [ ] **No helper to add visualizer to audio clip** `src/camtasia/timeline/clips/audio.py` — `add_audio_visualizer`

### Set the Tone with Background Music

Source: https://www.techsmith.com/learn/tutorials/camtasia/background-music/

- [ ] **General volume keyframes (not just fade-in/out)** `src/camtasia/timeline/clips/audio.py` — `set_volume_keyframes`
- [ ] **Loop music to fill timeline duration** `src/camtasia/project.py` — `add_background_music(loop=True)`

### Basic Edits After Recording

Source: https://www.techsmith.com/learn/tutorials/camtasia/basic-video-edits/

- [ ] **Timeline selection API (in/out range)** `src/camtasia/timeline/track.py` — `set_selection / clear_selection`
- [ ] **cut/copy/paste on selection** `src/camtasia/timeline/track.py` — `cut_selection / copy_selection / paste_at`
- [ ] **undo/redo on timeline operations** `src/camtasia/timeline/track.py` — `undo / redo command history`
- [ ] **trim_head/trim_tail on BaseClip** `src/camtasia/timeline/clips/base.py` — `trim_head / trim_tail`
- [ ] **ripple_delete by timeline range (only supports clip_id currently)** `src/camtasia/operations/layout.py` — `ripple_delete_range(track, start, end)`

### Blur or Mask a Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/blur-mask-video/

- [ ] **BlurRegion not registered via @register_effect and unverified against fixtures** `src/camtasia/effects/visual.py` — `@register_effect('BlurRegion') decorator`
- [ ] **BlurRegion missing Tint color RGB (only color-alpha exposed)** `src/camtasia/effects/visual.py` — `BlurRegion.color property`
- [ ] **BlurRegion missing Shape parameter (Oval vs Rectangle)** `src/camtasia/effects/visual.py` — `BlurRegion.shape property`
- [ ] **BlurRegion missing Feather/edge-softness slider** `src/camtasia/effects/visual.py` — `BlurRegion.feather or mask_blend`
- [ ] **BlurRegion missing Opacity slider** `src/camtasia/effects/visual.py` — `BlurRegion.opacity`
- [ ] **BlurRegion missing Ease In/Ease Out controls** `src/camtasia/effects/visual.py` — `BlurRegion.ease_in/ease_out`
- [ ] **BlurRegion missing positional/dimension params for moving-blur keyframes** `src/camtasia/effects/visual.py` — `BlurRegion.mask_width/height/position_x/position_y`
- [ ] **MaskShape enum not defined (shape 0/1 mapping to Oval/Rectangle not semantic)** `src/camtasia/types.py` — `MaskShape IntEnum (RECTANGLE=0, OVAL=1)`
- [ ] **No animate_to helper for Mask/BlurRegion keyframes** `src/camtasia/effects/visual.py` — `Mask.animate_to(time, x, y, w, h)`

### Speed Up Editing with Camtasia Audiate

Source: https://www.techsmith.com/learn/tutorials/camtasia/camtasia-audio-sync/

- [ ] **Auto-detect and remove filler words (Suggested Edits)** `src/camtasia/audiate/transcript.py` — `Transcript.detect_filler_words / remove_filler_words`
- [ ] **Detect and shorten pauses** `src/camtasia/audiate/transcript.py` — `Transcript.detect_pauses / shorten_pauses`
- [ ] **Apply Audiate edits back to Camtasia timeline (Edit Timeline vs Edit Media Only)** `src/camtasia/operations/sync.py` — `sync_audiate_edits_to_timeline(mode=...)`
- [ ] **Resolve linked Camtasia media by caiCamtasiaSessionId (link/unlink)** `src/camtasia/audiate/project.py` — `AudiateProject.find_linked_media / unlink`
- [ ] **Generate SRT from Audiate transcript** `src/camtasia/audiate/transcript.py` — `Transcript.to_srt`
- [ ] **Smart Scenes segmentation metadata** `src/camtasia/audiate/project.py` — `AudiateProject.smart_scenes`
- [ ] **Send Camtasia media to a new .audiate project** `src/camtasia/operations/sync.py` — `send_media_to_audiate`
- [ ] **Text-based deletion propagating to timeline** `src/camtasia/operations/sync.py` — `delete_words_from_timeline`

### Replace the Cursor

Source: https://www.techsmith.com/learn/tutorials/camtasia/change-cursor/

- [ ] **Replace-scope selector (Current/Similar/All)** `src/camtasia/timeline/clips/screen_recording.py` — `replace_cursor(path, scope='current'|'similar'|'all')`
- [ ] **Built-in cursor library / Cursor Type enumeration** `src/camtasia/timeline/clips/screen_recording.py` — `CursorType enum + set_cursor_type`
- [ ] **Hide cursor (No Cursor option)** `src/camtasia/timeline/clips/screen_recording.py` — `hide_cursor()`
- [ ] **Import custom cursor from image file** `src/camtasia/timeline/clips/screen_recording.py` — `import_custom_cursor(image_path)`
- [ ] **Unpack Rev Media prerequisite for cursor editing** `src/camtasia/timeline/clips/screen_recording.py` — `unpack_rev_media`
- [ ] **ROADMAP.md stale — incorrectly says cursor_image_path has no setter** `ROADMAP.md` — `update line — setter does exist`

### Speed Up & Slow Down Video Clips

Source: https://www.techsmith.com/learn/tutorials/camtasia/clip-speed/

- [ ] **ClipSpeed as named Visual Effect (no add_clip_speed / 'ClipSpeed' effectName producer)** `src/camtasia/timeline/clips/base.py` — `apply_clip_speed_effect`
- [ ] **Duration-based speed adjustment (set_speed_by_duration)** `src/camtasia/timeline/clips/base.py` — `set_speed_by_duration(target_seconds)`

### Create the Illusion of 3D Perspective (Corner Pinning)

Source: https://www.techsmith.com/learn/tutorials/camtasia/corner-pinning/

- [ ] **Derived position/skew/rotation accessors on CornerPin** `src/camtasia/effects/visual.py` — `CornerPin.position / skew / rotation derived properties`
- [ ] **Corner Pin Mode enable/toggle flag** `src/camtasia/effects/visual.py` — `CornerPin.enabled boolean`
- [ ] **Helper to animate pinned corners via keyframes** `src/camtasia/effects/visual.py` — `CornerPin.add_keyframe(time, corner, x, y)`
- [ ] **CornerPin parameter names unverified against real fixture** `tests/fixtures/ and effects/visual.py` — `add corner-pinning fixture and verify`
- [ ] **Snap control** `src/camtasia/effects/visual.py` — `CornerPin.snap_enabled`

### Build a Video Template to Share

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-a-template/

- [ ] **No save_as_template producing .camtemplate file** `src/camtasia/operations/template.py` — `save_as_template`
- [ ] **No export_camtemplate operation** `src/camtasia/operations/template.py` — `export_camtemplate`
- [ ] **No import_camtemplate / new_from_template** `src/camtasia/operations/template.py` — `new_from_template`
- [ ] **PlaceholderMedia missing 'title' property (canvas-visible title distinct from note)** `src/camtasia/timeline/clips/placeholder.py` — `PlaceholderMedia.title`
- [ ] **No Track.add_placeholder convenience** `src/camtasia/timeline/track.py` — `Track.add_placeholder(time, duration, title, note)`

### Create Custom Assets

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-custom-assets/

- [ ] **Save grouped media as reusable custom asset** `src/camtasia/timeline/clips/group.py` — `Group.save_as_asset`
- [ ] **Favorite annotations/callouts for reuse** `src/camtasia/annotations/callouts.py` — `Callout.add_to_favorites`
- [ ] **Export asset library as .campackage archive** `src/camtasia/export/` — `export_campackage`
- [ ] **Custom asset library management (add/list/reuse)** `src/camtasia/library.py` — `AssetLibrary.add_asset / list_assets`
- [ ] **Quick Property Editor (link/unlink/label/assign_theme/toggle visible on group)** `src/camtasia/timeline/clips/group.py` — `Group.quick_properties`

### Create Vertical Videos

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-vertical-videos/

- [ ] **No vertical aspect presets (9:16 FHD, 9:16 HD, 4:5, 1:1)** `src/camtasia/project.py` — `set_vertical_preset / CanvasPreset enum`
- [ ] **No auto-reframe / SmartFocus-for-vertical API** `src/camtasia/timeline/timeline.py` — `auto_reframe(target_aspect, focus)`
- [ ] **No Crop visual effect / crop_to_aspect / fit_to_canvas helper** `src/camtasia/effects/visual.py` — `Crop class + Clip.crop_to_aspect / fit_to_canvas`
- [ ] **No safe-zone presets for social platforms** `src/camtasia/safe_zones.py` — `SafeZone presets + Project.get_safe_zone(platform)`
- [ ] **set_canvas_size does not rescale/reposition existing clips** `src/camtasia/project.py` — `set_canvas_size(..., rescale_clips=True, strategy='cover'|'contain')`

### Create a Video from a Script

Source: https://www.techsmith.com/learn/tutorials/camtasia/create-video-from-script/

- [ ] **No screenplay text parser (builder consumes pre-parsed Screenplay)** `src/camtasia/screenplay.py` — `parse_screenplay / from_text`
- [ ] **No paragraph-to-scene mapping helper** `src/camtasia/screenplay.py` — `Section.from_paragraphs`
- [ ] **No scene/chapter markers emitted per section** `src/camtasia/builders/screenplay_builder.py` — `add marker per section`
- [ ] **No VO-to-screen-recording alignment on visual track** `src/camtasia/builders/screenplay_builder.py` — `video-track placement`
- [ ] **No on-screen captions generated from script lines** `src/camtasia/builders/screenplay_builder.py` — `_emit_captions_for_vo`
- [ ] **Single default_pause used for both inter-VO and inter-scene** `src/camtasia/builders/screenplay_builder.py` — `section_pause distinct from vo_pause`
- [ ] **No VO duration/alignment validation against audio length** `src/camtasia/builders/screenplay_builder.py` — `_validate_vo_alignment`
- [ ] **Audio resolver case-sensitive / rigid prefix** `src/camtasia/builders/screenplay_builder.py` — `case-insensitive flexible _find_audio_file`

### Introduction to Cursor Editing

Source: https://www.techsmith.com/learn/tutorials/camtasia/cursor-editing-basics/

- [ ] **No cursor elevation/always-on-top property** `src/camtasia/timeline/clips/screen_recording.py` — `ScreenVMFile.cursor_elevation`
- [ ] **No keyframe support for cursor_scale over time** `src/camtasia/timeline/clips/screen_recording.py` — `set_cursor_scale_keyframes`
- [ ] **No keyframe support for cursor_opacity over time** `src/camtasia/timeline/clips/screen_recording.py` — `set_cursor_opacity_keyframes`
- [ ] **No hide_cursor / show_cursor wrappers** `src/camtasia/timeline/clips/screen_recording.py` — `hide_cursor / show_cursor`
- [ ] **No 'No Cursor' image replacement at specific keyframe** `src/camtasia/timeline/clips/screen_recording.py` — `set_no_cursor_at(time)`

### Add Cursor Effects

Source: https://www.techsmith.com/learn/tutorials/camtasia/cursor-effects/

- [ ] **CursorColor effect missing** `src/camtasia/effects/cursor.py` — `class CursorColor: fill_color, outline_color`
- [ ] **CursorGlow effect missing** `src/camtasia/effects/cursor.py` — `class CursorGlow: color, opacity, radius`
- [ ] **CursorHighlight effect missing** `src/camtasia/effects/cursor.py` — `class CursorHighlight: size, color, opacity`
- [ ] **CursorIsolation effect missing** `src/camtasia/effects/cursor.py` — `class CursorIsolation: size, feather`
- [ ] **CursorMagnify effect missing** `src/camtasia/effects/cursor.py` — `class CursorMagnify: scale, size`
- [ ] **CursorPathCreator effect missing** `src/camtasia/effects/cursor.py` — `class CursorPathCreator: keyframes`
- [ ] **CursorSmoothing effect missing** `src/camtasia/effects/cursor.py` — `class CursorSmoothing: level`
- [ ] **CursorSpotlight effect missing** `src/camtasia/effects/cursor.py` — `class CursorSpotlight: size, opacity, blur, color`
- [ ] **CursorGradient effect missing** `src/camtasia/effects/cursor.py` — `class CursorGradient: color, size, opacity`
- [ ] **CursorLens effect missing** `src/camtasia/effects/cursor.py` — `class CursorLens: scale, size`
- [ ] **CursorNegative effect missing** `src/camtasia/effects/cursor.py` — `class CursorNegative: size, feather`
- [ ] **ClickBurst1-4 (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickBurst1..4 / RightClickBurst1..4`
- [ ] **ClickZoom (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickZoom / RightClickZoom`
- [ ] **ClickRings (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickRings / RightClickRings`
- [ ] **ClickRipple (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickRipple / RightClickRipple`
- [ ] **RightClickScaling (mirror of LeftClickScaling) missing** `src/camtasia/effects/cursor.py` — `RightClickScaling`
- [ ] **ClickScope (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickScope / RightClickScope`
- [ ] **ClickSound (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickSound / RightClickSound`
- [ ] **ClickTarget (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickTarget / RightClickTarget`
- [ ] **ClickWarp (left & right) effects missing** `src/camtasia/effects/cursor.py` — `LeftClickWarp / RightClickWarp`

### Quickly Smooth Cursor Movements

Source: https://www.techsmith.com/learn/tutorials/camtasia/cursor-smoothing/

- [ ] **No smooth_cursor toggle/property to enable/disable CursorSmoothing** `src/camtasia/timeline/clips/screen_recording.py` — `ScreenVMFile.smooth_cursor boolean`
- [ ] **cursor_track_level lacks setter** `src/camtasia/timeline/clips/screen_recording.py` — `cursor_track_level setter`
- [ ] **No restore_original_path to clear custom cursorLocation keyframes** `src/camtasia/timeline/clips/screen_recording.py` — `restore_original_path`

### Customize the Cursor Path

Source: https://www.techsmith.com/learn/tutorials/camtasia/customize-your-cursor-path/

- [ ] **No per-keyframe Line Type (straight vs curved/bezier) in set_cursor_location_keyframes** `src/camtasia/timeline/clips/screen_recording.py` — `set_cursor_location_keyframes(line_types=...)`
- [ ] **No bezier tangent handle control for cursor path points** `src/camtasia/timeline/clips/screen_recording.py` — `bezier handles param`
- [ ] **No per-point easing dropdown equivalent (only global 'linr')** `src/camtasia/timeline/clips/screen_recording.py` — `per-point easing`
- [ ] **No add_cursor_point(time,x,y) helper** `src/camtasia/timeline/clips/screen_recording.py` — `add_cursor_point`
- [ ] **No delete_cursor_point helper** `src/camtasia/timeline/clips/screen_recording.py` — `delete_cursor_point`
- [ ] **No move_cursor_point helper** `src/camtasia/timeline/clips/screen_recording.py` — `move_cursor_point`
- [ ] **No split_cursor_path operation** `src/camtasia/timeline/clips/screen_recording.py` — `split_cursor_path`
- [ ] **No extend_cursor_path operation** `src/camtasia/timeline/clips/screen_recording.py` — `extend_cursor_path`
- [ ] **No smooth_cursor_path (simplify jitter) operation** `src/camtasia/timeline/clips/screen_recording.py` — `smooth_cursor_path`
- [ ] **No straighten_cursor_path operation** `src/camtasia/timeline/clips/screen_recording.py` — `straighten_cursor_path`
- [ ] **No restore_cursor_path (revert to original recorded)** `src/camtasia/timeline/clips/screen_recording.py` — `restore_cursor_path`
- [ ] **No CursorPathCreator for non-TREC media** `src/camtasia/timeline/clips/screen_recording.py` — `add_cursor_path_creator`
- [ ] **cursor_location_keyframes setter not provided** `src/camtasia/timeline/clips/screen_recording.py` — `cursor_location_keyframes setter`

### Provide Context with Device Frames

Source: https://www.techsmith.com/learn/tutorials/camtasia/device-frames/

- [ ] **No built-in device frame Type presets / enum (tutorial has Type dropdown)** `src/camtasia/builders/device_frame.py` — `DeviceFrameType enum / preset catalog`
- [ ] **No integration with TechSmith asset library / 'Download More' frames** `src/camtasia/builders/device_frame.py` — `library/preset-name resolver`
- [ ] **Implemented as image overlay rather than Camtasia's native DeviceFrame visualEffect on the clip** `src/camtasia/builders/device_frame.py` — `emit visualEffects DeviceFrame entry on wrapped_clip`
- [ ] **No auto-fit/snap of clip to canvas** `src/camtasia/builders/device_frame.py` — `add_device_frame fit_to_canvas param`
- [ ] **No remove_device_frame helper (tutorial's X icon)** `src/camtasia/builders/device_frame.py` — `remove_device_frame`
- [ ] **No orientation/rotation parameter** `src/camtasia/builders/device_frame.py` — `orientation param`

### Add a Dynamic Background

Source: https://www.techsmith.com/learn/tutorials/camtasia/dynamic-backgrounds/

- [ ] **No high-level add_dynamic_background(asset_name=...) API — only add_gradient_background** `src/camtasia/builders/` — `add_dynamic_background(asset_name, duration, colors)`
- [ ] **No named-asset catalog for dynamic background shader assets** `src/camtasia/` — `DynamicBackgroundAsset enum / catalog`
- [ ] **No explicit loop-flag or seamless-loop API on add_gradient_background** `src/camtasia/builders/` — `add_gradient_background(..., seamless_loop=True)`
- [ ] **No wrapper for Lottie-based dynamic backgrounds (source handles Color000 padded keys but no public helper)** `src/camtasia/builders/` — `add_lottie_background`
- [ ] **No mapping of tutorial's UI property labels to SourceEffect parameter keys (Color0-3, MidPoint, Speed)** `src/camtasia/effects/source.py` — `documented property name aliases`

### Add Dynamic Captions

Source: https://www.techsmith.com/learn/tutorials/camtasia/dynamic-captions/

- [ ] **Dynamic Caption Style presets / library** `src/camtasia/timeline/captions.py` — `DynamicCaptionStyle class + apply_dynamic_style`
- [ ] **Auto-generate dynamic captions from audio transcript** `src/camtasia/audiate/transcript.py` — `Transcript.to_dynamic_caption_clip`
- [ ] **Word-by-word highlight animation per transcript timing** `src/camtasia/timeline/captions.py` — `DynamicCaptionClip.active_word_at(t)`
- [ ] **Per-caption styling distinct from timeline-wide CaptionAttributes** `src/camtasia/timeline/clips/callout.py` — `DynamicCaptionClip.text_properties`
- [ ] **Save custom style as Dynamic Caption preset** `src/camtasia/templates/behavior_presets.py` — `save_dynamic_caption_preset`
- [ ] **Transcript word editing: add/delete/convert-to-gap** `src/camtasia/audiate/transcript.py` — `Transcript.add_word/delete_word/convert_to_gap`
- [ ] **Per-word transcription timing drag** `src/camtasia/audiate/transcript.py` — `Transcript.set_word_timing`
- [ ] **Transcript gap indicators** `src/camtasia/audiate/transcript.py` — `Transcript.gaps property`
- [ ] **Dynamic caption canvas position/size handles** `src/camtasia/timeline/clips/callout.py` — `DynamicCaptionClip.canvas_rect`
- [ ] **Extend caption duration with transcript rescoping** `src/camtasia/timeline/clips/base.py` — `DynamicCaptionClip.set_duration with rescope`
- [ ] **Preserve transcription edits when style deleted/swapped** `src/camtasia/timeline/clips/audio.py` — `AudioClip.dynamic_caption_transcription persistence`

### Edit Zoom Recordings

Source: https://www.techsmith.com/learn/tutorials/camtasia/edit-zoom-recording/

- [ ] **Import Zoom cloud recording via OAuth** `src/camtasia/project.py` — `Project.import_zoom_recording`
- [ ] **Remove/hide gallery view track** `src/camtasia/timeline/timeline.py` — `Timeline.remove_gallery_view`
- [ ] **Active speaker tracking (separate stream)** `src/camtasia/timeline/timeline.py` — `Timeline.add_speaker_track`
- [ ] **Chat overlay from Zoom chat transcript** `src/camtasia/timeline/timeline.py` — `Timeline.add_chat_overlay`
- [ ] **Zoom-specific metadata (meeting ID, host, topic, date)** `src/camtasia/media_bin/media_bin.py` — `Media.zoom_metadata`

### Edit Audio

Source: https://www.techsmith.com/learn/tutorials/camtasia/editing-audio/

- [ ] **Silence range of audio (right-click > Silence Audio)** `src/camtasia/timeline/clips/base.py` — `silence_audio(start, end)`
- [ ] **Separate/strip audio from video clip** `src/camtasia/timeline/clips/base.py` — `separate_video_and_audio`
- [ ] **Audio-specific fade_in/fade_out (current fade methods animate opacity)** `src/camtasia/timeline/clips/base.py` — `audio_fade_in / audio_fade_out`
- [ ] **Multi-point audio point API (add/move/remove volume keyframes)** `src/camtasia/timeline/clips/base.py` — `add_audio_point / remove_all_audio_points`
- [ ] **Mix-to-Mono setter missing (attribute exists, no dedicated setter)** `src/camtasia/timeline/clips/audio.py` — `mix_to_mono setter`
- [ ] **set_volume_fade supports only single start->end; no multi-keyframe volume envelope** `src/camtasia/timeline/clips/base.py` — `set_volume_keyframes`

### Enhance Your Video Overview

Source: https://www.techsmith.com/learn/tutorials/camtasia/enhance-video/

- [ ] **Gesture Effects (tap/swipe/pinch for iOS recordings, Mac only)** `src/camtasia/effects/visual.py` — `class GestureEffect with @register_effect('GestureTap'|'GestureSwipe'|'GesturePinch')`
- [ ] **Interactive Hotspot effect (clickable regions)** `src/camtasia/effects/visual.py` — `class Hotspot with @register_effect('Hotspot') — url, action, pause, javascript params`
- [ ] **Zoom-n-Pan as a first-class effect** `src/camtasia/effects/visual.py` — `class ZoomNPan with scale, positionX, positionY parameters`
- [ ] **Device Frame as a registered visual effect** `src/camtasia/effects/visual.py` — `class DeviceFrame with @register_effect('DeviceFrame') — frame_type parameter`
- [ ] **ChromaKey and CornerPin lack fixture verification** `src/camtasia/effects/visual.py` — `add fixture-backed tests and remove unverified warnings`

### Export an Audio File

Source: https://www.techsmith.com/learn/tutorials/camtasia/export-audio/

- [ ] **Export standalone audio file (mp3/m4a/wav) from project timeline** `src/camtasia/export/audio.py` — `export_audio(project, out_path, format=...)`
- [ ] **File-type/format selection (mp3/m4a/wav)** `src/camtasia/export/audio.py` — `export_audio(format literal)`
- [ ] **Mixed export of enabled audio tracks** `src/camtasia/export/audio.py` — `mix enabled tracks in export_audio`
- [ ] **Per-track / solo audio export honoring enabled flag** `src/camtasia/export/audio.py` — `export_audio_clips(solo_track=...)`
- [ ] **Public API export in export/__init__.py for audio functions** `src/camtasia/export/__init__.py` — `export export_audio/export_audio_clips`

### Freeze Video Clips with Extend Frame

Source: https://www.techsmith.com/learn/tutorials/camtasia/extend-frame/

- [ ] **ripple_extend operation (extend clip + push following clips forward)** `src/camtasia/operations/layout.py` — `ripple_extend(track, clip_id, extend_seconds)`
- [ ] **Extend clip to absolute target duration** `src/camtasia/timeline/track.py` — `extend_clip_to(clip_id, target_duration)`
- [ ] **freeze_at_clip_start convenience** `src/camtasia/timeline/track.py` — `freeze_at_clip_start`
- [ ] **freeze_at_clip_end convenience** `src/camtasia/timeline/track.py` — `freeze_at_clip_end`
- [ ] **add_exported_frame (exports a frame as image on new track)** `src/camtasia/timeline/track.py` — `add_exported_frame`
- [ ] **extend_clip has no ripple option** `src/camtasia/timeline/track.py` — `extend_clip(..., ripple=False)`

### Add Video Filters

Source: https://www.techsmith.com/learn/tutorials/camtasia/filters/

- [ ] **Range controls (shadowRampStart/End, highlightRampStart/End, channel) written by add_lut_effect but not typed on LutEffect** `src/camtasia/effects/visual.py` — `LutEffect.shadow_ramp_start/end, highlight_ramp_start/end, channel`
- [ ] **Range blend preset dropdown selection has no API** `src/camtasia/effects/visual.py` — `LutEffect.range_preset`
- [ ] **Ease In / Ease Out (Mac) transition seconds not exposed** `src/camtasia/effects/visual.py` — `LutEffect.ease_in / LutEffect.ease_out`
- [ ] **Add Preset button (save customized LUT) has no API** `src/camtasia/timeline/clips/base.py` — `save_lut_preset`
- [ ] **LUT filename dropdown has no enum/catalog** `src/camtasia/types.py` — `LutPreset enum`

### How to Make an Intro for a Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/how-to-make-an-intro/

- [ ] **Import .libzip archive into a new library** `src/camtasia/project.py` — `import_libzip_library`
- [ ] **Ripple-replace logo asset inside intro group's Left Logo subgroup** `src/camtasia/timeline/track.py` — `ripple_replace_media / replace_in_group`
- [ ] **Edit intro group properties (BG1/BG2 gradient, text font/size/color)** `src/camtasia/timeline/track.py` — `set_group_property / edit_intro_properties`
- [ ] **Save customized timeline group back to library as reusable asset** `src/camtasia/project.py` — `save_timeline_group_to_library`
- [ ] **Access/modify nested intro subgroups (Cloud overlay opacity, Right Text spacing)** `src/camtasia/timeline/track.py` — `get_nested_subgroup / set_opacity`
- [ ] **add_intro lacks template_name/library_asset linkage** `src/camtasia/builders/video_production.py` — `add_intro(template_name=..., library_asset=...)`

### Remove A Color (Green Screen)

Source: https://www.techsmith.com/learn/tutorials/camtasia/how-to-remove-a-color/

- [ ] **Hue slider parameter not exposed on ChromaKey effect** `src/camtasia/effects/visual.py` — `ChromaKey.hue property`

### Import & Manage Your Project Media

Source: https://www.techsmith.com/learn/tutorials/camtasia/import-manage-media/

- [ ] **Rename media in bin** `src/camtasia/media_bin/media_bin.py` — `Media.rename / identity setter`
- [ ] **Delete unused media (not on timeline)** `src/camtasia/media_bin/media_bin.py` — `MediaBin.delete_unused / unused_media property`
- [ ] **Sort media by field** `src/camtasia/media_bin/media_bin.py` — `MediaBin.sorted(key, reverse)`
- [ ] **Create proxy video** `src/camtasia/media_bin/media_bin.py` — `Media.create_proxy`
- [ ] **Delete proxy video** `src/camtasia/media_bin/media_bin.py` — `Media.delete_proxy`
- [ ] **Create reverse video** `src/camtasia/media_bin/media_bin.py` — `Media.reverse`
- [ ] **Import folder of media** `src/camtasia/media_bin/media_bin.py` — `MediaBin.import_folder`
- [ ] **Import multiple files at once** `src/camtasia/media_bin/media_bin.py` — `MediaBin.import_many(paths)`

### Import Presentation Slides

Source: https://www.techsmith.com/learn/tutorials/camtasia/import-powerpoint-slides/

- [ ] **No direct .pptx file import** `src/camtasia/builders/slide_import.py` — `import_powerpoint(project, pptx_path)`
- [ ] **No automatic slide-to-image extraction from PPTX** `src/camtasia/builders/slide_import.py` — `_extract_slides_as_images via python-pptx or LibreOffice`
- [ ] **Default per-slide duration not sourced from project settings** `src/camtasia/builders/slide_import.py` — `use project.settings.default_image_duration`
- [ ] **No automatic timeline markers from slide titles** `src/camtasia/builders/slide_import.py` — `add slide_titles param that emits markers`
- [ ] **No append-to-current-end placement (always starts at 0)** `src/camtasia/builders/slide_import.py` — `cursor from track.end_time()`

### Reuse Media Across Projects (Library)

Source: https://www.techsmith.com/learn/tutorials/camtasia/library/

- [ ] **No Library panel/model abstraction** `src/camtasia/library/library.py` — `Library class + Libraries container`
- [ ] **No add-asset-to-library API** `src/camtasia/library/library.py` — `Library.add_asset(clip, name, use_canvas_size)`
- [ ] **No add-timeline-selection-to-library** `src/camtasia/library/library.py` — `Library.add_timeline_selection`
- [ ] **No insert-library-asset-on-timeline API** `src/camtasia/timeline/timeline.py` — `Timeline.add_library_asset`
- [ ] **No create-custom-library API** `src/camtasia/library/library.py` — `Libraries.create(name, start_from=None)`
- [ ] **No library folder / organization API** `src/camtasia/library/library.py` — `Library.create_folder / move`
- [ ] **No .libzip import** `src/camtasia/library/libzip.py` — `import_libzip`
- [ ] **No .libzip export** `src/camtasia/library/libzip.py` — `export_libzip`
- [ ] **No default vs custom library distinction** `src/camtasia/library/library.py` — `Libraries.default / is_default`
- [ ] **No Import Media to Library operation** `src/camtasia/library/library.py` — `Library.import_media`
- [ ] **No bridge MediaBin -> Library** `src/camtasia/media_bin/media_bin.py` — `MediaBin.add_to_library`

### Close Timeline Gaps with Magnetic Tracks

Source: https://www.techsmith.com/learn/tutorials/camtasia/magnetic-tracks/

- [ ] **Enabling magnetic on a track does not auto-close existing gaps** `src/camtasia/timeline/track.py` — `Track.magnetic setter should call pack_track when set to True`
- [ ] **No automatic ripple-insert when dropping media between clips on magnetic track** `src/camtasia/timeline/track.py` — `Track.add_clip should ripple_insert when self.magnetic`
- [ ] **No automatic ripple-close when moving clips on magnetic track** `src/camtasia/timeline/track.py` — `Track.move_clip should re-pack track when magnetic`
- [ ] **No snap-to-clip-edge (only snap_to_grid exists)** `src/camtasia/operations/layout.py` — `snap_to_clip_edge(track, tolerance)`
- [ ] **No all-tracks magnetic toggle on Timeline** `src/camtasia/timeline/timeline.py` — `Timeline.set_all_magnetic(value)`
- [ ] **Groups-on-magnetic-tracks-keep-spaces rule not honored** `src/camtasia/operations/layout.py` — `pack_track preserve spacing for Group clips`

### Add Markers & Video Table of Contents

Source: https://www.techsmith.com/learn/tutorials/camtasia/markers-and-table-of-contents/

- [ ] **Rename an existing marker in place** `src/camtasia/timeline/markers.py` — `MarkerList.rename(old_name, new_name)`
- [ ] **Move/reposition existing marker without delete+add** `src/camtasia/timeline/markers.py` — `MarkerList.move(old_time, new_time)`
- [ ] **Promote timeline marker to media marker (attach to clip)** `src/camtasia/timeline/track.py` — `Track.promote_marker_to_media`
- [ ] **Demote media marker to timeline marker** `src/camtasia/timeline/track.py` — `Track.demote_marker_to_timeline`
- [ ] **Export Smart Player TOC manifest (XML/JSON sidecar)** `src/camtasia/export/toc.py` — `export_toc`
- [ ] **Export chapters in WebVTT/MP4 atom/YouTube list formats** `src/camtasia/export/chapters.py` — `export_chapters(format=...)`
- [ ] **Navigate next/prev marker from a time** `src/camtasia/timeline/markers.py` — `MarkerList.next_after/prev_before`
- [ ] **Remove single marker by name** `src/camtasia/timeline/markers.py` — `MarkerList.remove_by_name`
- [ ] **Auto-generate slide markers from presentation metadata** `src/camtasia/operations/slide_markers.py` — `mark_slides_from_presentation`

### Edit Microsoft Teams & Other Meeting Recordings

Source: https://www.techsmith.com/learn/tutorials/camtasia/meeting-recordings/

- [ ] **Import Teams/Zoom/Meet MP4 as first-class meeting recording workflow** `src/camtasia/media_bin/media_bin.py` — `import_meeting_recording(path, source=...)`
- [ ] **Dedicated Zoom cloud importer** `src/camtasia/media_bin/media_bin.py` — `import_zoom_cloud_recording`
- [ ] **Auto-detect speakers / per-speaker segmentation** `src/camtasia/audiate/transcript.py` — `detect_speakers`
- [ ] **Trim intro/outro helper** `src/camtasia/operations/` — `trim_meeting_intro_outro`
- [ ] **Extract per-speaker audio tracks from mixed recording** `src/camtasia/timeline/clips/audio.py` — `extract_speaker_audio_tracks`
- [ ] **Split gallery-view recording into per-speaker clips** `src/camtasia/timeline/clips/screen_recording.py` — `split_gallery_into_speaker_clips`
- [ ] **One-shot Suggested Edits helper (filler+pause removal)** `src/camtasia/audiate/project.py` — `apply_suggested_edits`

### Add Movement to Any Object (Motion Paths)

Source: https://www.techsmith.com/learn/tutorials/camtasia/motion-path/

- [ ] **No dedicated MotionPath visual effect class** `src/camtasia/effects/visual.py` — `@register_effect('MotionPath') class`
- [ ] **No Auto Orient / rotate-along-path property** `src/camtasia/effects/visual.py` — `MotionPath.auto_orient`
- [ ] **No per-motion-point Line Type control (angle/curve/combination)** `src/camtasia/timeline/clips/base.py` — `set_position_keyframes_with_line_type`
- [ ] **No bezier control-point / tangent handle API** `src/camtasia/timeline/clips/base.py` — `set_position_bezier_handles`
- [ ] **No add_motion_point helper** `src/camtasia/timeline/clips/base.py` — `add_motion_point(time, x, y, line_type)`
- [ ] **InterpolationType enum missing easi/easo/bezi members** `src/camtasia/types.py` — `InterpolationType.EASE_IN/EASE_OUT/BEZIER`
- [ ] **No high-level apply_motion_path wrapper combining MotionPath effect + position keyframes** `src/camtasia/timeline/clips/base.py` — `apply_motion_path(points, easing, auto_orient, line_type)`

### Recommended Audio Edits

Source: https://www.techsmith.com/learn/tutorials/camtasia/recommended-audio-edits/

- [ ] **Audio compression effect not wrapped** `src/camtasia/timeline/clips/base.py` — `add_compression(threshold,ratio,attack,release,makeup_gain)`
- [ ] **Equalization not wrapped** `src/camtasia/timeline/clips/base.py` — `add_equalizer(bands)`
- [ ] **Breath removal operation** `src/camtasia/operations/` — `remove_breaths(clip, threshold_db, min_duration)`
- [ ] **Silence trim operation** `src/camtasia/operations/` — `trim_silences(clip, threshold_db, min_silence_ms)`

### Build Your First Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/record-edit-share/

- [ ] **No library asset import (intros, templates, graphics, music)** `src/camtasia/project.py` — `import_from_library / add_library_asset`
- [ ] **No Camtasia Rev AI auto-styling presets** `src/camtasia/project.py` — `apply_rev_layout / apply_rev_style`
- [ ] **No AI Noise Removal effect helper** `src/camtasia/project.py` — `add_ai_noise_removal`
- [ ] **No canvas preview / render frame-at-time** `src/camtasia/project.py` — `render_canvas_preview / preview_frame`
- [ ] **No intro/template asset insertion from bundled library** `src/camtasia/operations/template.py` — `insert_intro_template`

### Move Multiple Clips at Once

Source: https://www.techsmith.com/learn/tutorials/camtasia/ripple-move/

- [ ] **ripple_move on single track (shift one clip and all clips to its right)** `src/camtasia/operations/layout.py` — `ripple_move(track, clip_id, delta_seconds)`
- [ ] **ripple_move across multiple tracks** `src/camtasia/operations/layout.py` — `ripple_move_multi(tracks, clip_ids_per_track, delta_seconds)`

### Join Clips Together

Source: https://www.techsmith.com/learn/tutorials/camtasia/stitch-media/

- [ ] **No unstitch/split StitchedMedia back into segments** `src/camtasia/timeline/track.py` — `Track.unstitch_clip(clip_id)`
- [ ] **join_clips does not validate same-source media** `src/camtasia/timeline/track.py` — `add same-src check to join_clips`
- [ ] **join_clips does not validate adjacency** `src/camtasia/timeline/track.py` — `add adjacency check to join_clips`
- [ ] **No Track.stitch_adjacent convenience** `src/camtasia/timeline/track.py` — `stitch_adjacent(clip_ids)`
- [ ] **No auto-stitch-on-cut behavior** `src/camtasia/operations/` — `post-cut hook to re-stitch adjacent same-source segments`

### Build Your Color Palette (Themes)

Source: https://www.techsmith.com/learn/tutorials/camtasia/themes/

- [ ] **No .camtheme export/import (file-based theme sharing)** `src/camtasia/themes.py` — `export_theme / import_theme`
- [ ] **No Theme.logo_path attribute** `src/camtasia/themes.py` — `Theme.logo_path`
- [ ] **No theme manager / named registry** `src/camtasia/themes.py` — `ThemeManager.create/rename/delete`
- [ ] **apply_theme does not handle 'annotation background' slot distinct from fill** `src/camtasia/themes.py` — `annotation-background mapping`
- [ ] **No add_annotation_from_theme helper** `src/camtasia/themes.py` — `add_annotation_from_theme`
- [ ] **No stroke-width/stroke-style mapping in apply_theme** `src/camtasia/themes.py` — `apply_theme stroke-width`
- [ ] **Theme has fixed slots; no Add Color / dynamic accent-N support** `src/camtasia/themes.py` — `Theme.add_color / dynamic slots`

### 3 Keys to the Camtasia Editor Timeline

Source: https://www.techsmith.com/learn/tutorials/camtasia/timeline-key-concepts/

- [ ] **track_height property missing (trackHeight stored in metadata but no getter/setter)** `src/camtasia/timeline/track.py` — `Track.track_height property`
- [ ] **playhead position property missing (DocPrefPlayheadTime stored but not exposed)** `src/camtasia/timeline/timeline.py` — `Timeline.playhead_seconds`
- [ ] **timeline UI zoom level property missing** `src/camtasia/timeline/timeline.py` — `Timeline.ui_zoom_level`

### Translate Your Script, Audio, and Captions

Source: https://www.techsmith.com/learn/tutorials/camtasia/translate/

- [ ] **Translate script to target language (overwrites transcript)** `src/camtasia/audiate/project.py` — `AudiateProject.translate_script(target_language)`
- [ ] **Generate TTS audio from translated script** `src/camtasia/audiate/project.py` — `AudiateProject.generate_audio(voice, apply_to_entire_project=True)`
- [ ] **Generate AI video avatar for translated audio** `src/camtasia/audiate/project.py` — `AudiateProject.generate_avatar`
- [ ] **Export translated captions to .srt per language** `src/camtasia/export/captions.py` — `export_captions_multilang`
- [ ] **Supported-language enumeration** `src/camtasia/audiate/project.py` — `SUPPORTED_TRANSLATION_LANGUAGES`
- [ ] **Multi-language package export** `src/camtasia/export/captions.py` — `export_multilang_package`
- [ ] **Writable project language (currently read-only)** `src/camtasia/audiate/project.py` — `AudiateProject.language setter`
- [ ] **Save-as helper for language-suffixed copies** `src/camtasia/audiate/project.py` — `save_as_translation(language_code)`

### How to Use a Template

Source: https://www.techsmith.com/learn/tutorials/camtasia/use-a-template/

- [ ] **No replace_placeholder supporting Ripple Replace / Clip Speed / From Start/End modes** `src/camtasia/operations/template.py` — `replace_placeholder(placeholder, new_media, mode=...)`
- [ ] **No .camtemplate import/install** `src/camtasia/operations/template.py` — `install_camtemplate / import_template`
- [ ] **No new_project_from_template(name)** `src/camtasia/operations/template.py` — `new_project_from_template`
- [ ] **No Template Manager (list/rename/delete installed templates)** `src/camtasia/operations/template.py` — `TemplateManager`
- [ ] **PlaceholderMedia.set_source raises TypeError; no replace_with(media, mode) convenience** `src/camtasia/timeline/clips/placeholder.py` — `PlaceholderMedia.replace_with`

### Remove a Background from Your Video

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-background-removal/

- [ ] **AI Background Removal visual effect not implemented (distinct from ChromaKey/MediaMatte)** `src/camtasia/effects/visual.py` — `@register_effect('BackgroundRemoval') class with intensity/threshold/edge-softness/invert parameters`
- [ ] **No convenience add_background_removal() helper on BaseClip** `src/camtasia/timeline/clips/base.py` — `add_background_removal near add_media_matte`
- [ ] **BACKGROUND_REMOVAL missing from types enum and schema effect-name enum** `src/camtasia/types.py` — `BACKGROUND_REMOVAL constant`
- [ ] **ChromaKey effect marked unverified — no fixture-backed parameter validation** `src/camtasia/effects/visual.py` — `verify ChromaKey parameters against fixture`

### Explore the Timeline

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-editing/

- [ ] **Timeline UI zoom level + fit-to-project** `src/camtasia/timeline/timeline.py` — `zoom_level / fit_to_project`
- [ ] **Per-track and global track height** `src/camtasia/timeline/track.py` — `Track.track_height + Timeline.track_height_scale`
- [ ] **Detach/Reattach Timeline (Ctrl+3)** `src/camtasia/timeline/timeline.py` — `detached / detach / reattach`
- [ ] **J/K/L variable-speed playback transport** `src/camtasia/timeline/timeline.py` — `playback_rate / play / pause`
- [ ] **Track enabled (eye icon) runtime on/off distinct from lock** `src/camtasia/timeline/track.py` — `Track.enabled`
- [ ] **Quiz/Marker view show-hide toggles** `src/camtasia/timeline/markers.py` — `markers_view_visible / quiz_view_visible`
- [ ] **Track scroll position** `src/camtasia/timeline/timeline.py` — `Timeline.scroll_offset`

### Add a Transition

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-transitions/

- [ ] **Gradient Wipe transition preset missing** `src/camtasia/timeline/transitions.py` — `add_gradient_wipe`
- [ ] **Card Swipe transition preset missing** `src/camtasia/timeline/transitions.py` — `add_card_swipe`
- [ ] **Cube Rotate transition preset missing** `src/camtasia/timeline/transitions.py` — `add_cube_rotate`
- [ ] **Swap transition preset missing** `src/camtasia/timeline/transitions.py` — `add_swap`
- [ ] **Snapshot transition preset missing** `src/camtasia/timeline/transitions.py` — `add_snapshot`

### Watermark Your Videos

Source: https://www.techsmith.com/learn/tutorials/camtasia/video-watermark/

- [ ] **scale parameter on add_watermark** `src/camtasia/project.py` — `add_watermark(scale=...)`
- [ ] **x_offset parameter on add_watermark** `src/camtasia/project.py` — `add_watermark(x_offset=...)`
- [ ] **y_offset parameter on add_watermark** `src/camtasia/project.py` — `add_watermark(y_offset=...)`
- [ ] **Text watermark variant (copyright/website)** `src/camtasia/project.py` — `add_text_watermark`
- [ ] **builders/video_production.py add_watermark does not expose scale/position/text** `src/camtasia/builders/video_production.py` — `add_watermark`

### Visual Effects Overview

Source: https://www.techsmith.com/learn/tutorials/camtasia/visual-effects/

- [ ] **Color Tint (two-color light/dark tint)** `src/camtasia/effects/visual.py` — `add @register_effect("ColorTint") class with light-color/dark-color RGBA parameters`
- [ ] **Colorize (single color overlay)** `src/camtasia/effects/visual.py` — `add @register_effect("Colorize") class with color RGBA + amount/intensity parameters`
- [ ] **Sepia (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("Sepia") class`
- [ ] **Border (colored border around media)** `src/camtasia/effects/visual.py` — `add @register_effect("Border") class with color RGBA + thickness parameters`
- [ ] **CRT Monitor (scanlines + curvature)** `src/camtasia/effects/visual.py` — `add @register_effect("CRTMonitor") class with scanline/curvature/intensity parameters`
- [ ] **Cursor Path Creator** `src/camtasia/effects/cursor.py` — `add @register_effect("CursorPathCreator") class`
- [ ] **Device Frame effect (distinct from builders/device_frame.py overlay)** `src/camtasia/effects/visual.py` — `add @register_effect("DeviceFrame") class with frame-id parameter`
- [ ] **Keystroke effect (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("Keystroke") class`
- [ ] **Interactive Hotspot** `src/camtasia/effects/visual.py` — `add @register_effect("Hotspot") class with url/action/pause parameters`
- [ ] **Mosaic / pixelate (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("Mosaic") class with pixel-size parameter`
- [ ] **Outline Edges (line-drawing)** `src/camtasia/effects/visual.py` — `add @register_effect("OutlineEdges") class with threshold/intensity parameters`
- [ ] **Reflection effect** `src/camtasia/effects/visual.py` — `add @register_effect("Reflection") class with opacity/distance/falloff parameters`
- [ ] **Static Noise (TV static)** `src/camtasia/effects/visual.py` — `add @register_effect("StaticNoise") class with intensity parameter`
- [ ] **Tiling (repeat pattern)** `src/camtasia/effects/visual.py` — `add @register_effect("Tiling") class with scale/positionX/positionY/opacity parameters`
- [ ] **Torn Edge** `src/camtasia/effects/visual.py` — `add @register_effect("TornEdge") class with jaggedness/margin parameters`
- [ ] **Window Spotlight (Mac)** `src/camtasia/effects/visual.py` — `add @register_effect("WindowSpotlight") class`
- [ ] **Vignette** `src/camtasia/effects/visual.py` — `add @register_effect("Vignette") class with amount/falloff/color parameters`
- [ ] **Background Removal (AI, non-green-screen) distinct from ChromaKey** `src/camtasia/effects/visual.py` — `add @register_effect("BackgroundRemoval") class`
- [ ] **Freeze Region (freeze a sub-region of the clip)** `src/camtasia/effects/visual.py` — `add @register_effect("FreezeRegion") class with positionX/positionY/width/height parameters`
- [ ] **Motion Path as visual effect** `src/camtasia/effects/visual.py` — `add @register_effect("MotionPath") class with path keyframes`
- [ ] **BlurRegion defined but not registered** `src/camtasia/effects/visual.py` — `add @register_effect("BlurRegion") decorator to existing class after fixture verification`

_Total: 357 concrete gaps across 54 tutorials._

## High-Level API Improvement Ideas (from demo production)

- [already-implemented] VideoProductionBuilder — `builders/video_production.py` fluent builder for assembling complete video productions
- [already-implemented] ScreenRecordingSync
- [already-implemented] import_media() format validation and auto-conversion
- [already-implemented] ProgressiveDisclosure helper
- [already-implemented] Project.clean_inherited_state()
- [already-implemented] MarkerList.clear() and MarkerList.replace()
- [already-implemented] Project.remove_orphaned_media()
- [already-implemented] Recap/tile layout helper

## Feature Gaps (discovered during adversarial review & integration testing)

### Clip API
- [already-implemented] `BaseClip.unmute()` — reverses `mute()` on all clip types including Group/StitchedMedia/UnifiedMedia
- [already-implemented] `UnifiedMedia.remove_all_effects()` clears effects on both video/audio sub-clips
- [already-implemented] `UnifiedMedia.has_effects/effect_count/effect_names` aggregate from video+audio sub-clips
- [already-implemented] `Callout.text` setter should update `textAttributes` `rangeEnd` to match new text length
- [already-implemented] `BaseClip.add_keyframe()` creates `animationTracks.visual` entries for visual parameters (translation/scale/rotation/crop/opacity)
- [already-implemented] `set_position_keyframes` / `set_scale_keyframes` / `set_rotation_keyframes` / `set_crop_keyframes` create `animationTracks.visual` entries
- [already-implemented] `add_progressive_disclosure(replace_previous=True)` already implemented

### Track API
- [already-implemented] `clip_after()` docstring clarified as at-or-after; `clip_strictly_after()` added as strictly-after variant
- [already-implemented] `insert_gap()` and `shift_all_clips()` transitions handled that may become invalid
- [already-implemented] `merge_adjacent_clips()` doesn't verify clips are actually adjacent before merging
- [already-implemented] `set_segment_speeds()` uses float accumulation for `mediaStart` — should use Fraction
- [already-implemented] `split_clip()` uses raw `Fraction(orig_scalar)` instead of `_parse_scalar()` — inconsistent precision

### Timeline API
- [already-implemented] `clips_of_type()` is O(n²) and misattributes nested clips to `None` track
- [already-implemented] `shift_all()` doesn't shift transition or effect `start` times
- [already-implemented] `Timeline.insert_gap()` / `remove_gap()` shift timeline markers (transitions use clip IDs and don't need adjustment)
- [already-implemented] `flatten_to_track()` warns when source tracks have transitions that will be dropped
- [already-implemented] `build_section_timeline()` helper exists in timeline.py

### Validation
- [already-implemented] Validate `timeline.id` exists and doesn't collide with clip IDs
- [already-implemented] Validate `GenericBehaviorEffect` has required `in`/`center`/`out` phases
- [already-implemented] Validate overlapping clips on same track (Camtasia tracks are single-occupancy)
- [already-implemented] Flag explicit `null` in transition `leftMedia`/`rightMedia` (format says omit, not null)

### Effects
- [already-implemented] Typed wrapper classes added for LutEffect, Emphasize, Spotlight, ColorAdjustment, BlendModeEffect, MediaMatte — all registered with effect_from_dict
- [already-implemented] `BlurRegion` export is intentional — class docstring warns it is unregistered and unverified against real projects
- [already-implemented] `DropShadow.enabled` / `CursorShadow.enabled` docstrings clarify that setting only updates defaultValue, not existing keyframes

### Export
- [already-implemented] EDL exporter recurses into Groups/StitchedMedia (opt-out via include_nested=False)
- [already-implemented] CSV and report (JSON + markdown) exporters recurse into Groups/StitchedMedia with timeline-absolute positions
- [already-implemented] EDL `UnifiedMedia` source is always `AX` — should use video sub-clip's source
- [already-implemented] SRT exporter warns when no markers to export
- [already-implemented] `timeline_json` now includes effects, transitions, and per-clip metadata (opt-out via kwargs; bumped version to 1.1)

### Builders
- [already-implemented] `timeline_builder.add_title()` ignores `subtitle` parameter (dead code)
- [already-implemented] `tile_layout.add_grid` auto-fits images to cell size by default (opt-out via fit_to_cell=False)
- [already-implemented] `screenplay_builder._find_audio_file()` only searches `.wav` — should support `.mp3`, `.m4a`

### Schema
- [already-implemented] Schema `effect.effectName` enum no longer includes behavior names (moved to GenericBehaviorEffect only)
- [already-implemented] Schema `effect` definition doesn't require `bypassed` (format reference says required)
- [already-implemented] Non-schema transition names (`FadeThroughColor`, `SlideUp`, etc.) documented via docstring warnings

### Behavior Presets
- [ ] Preset values don't fully match real TechSmith samples (ongoing refinement)
- [already-implemented] `reveal` preset start value documented; clamped by get_behavior_preset() for short clips. Needs real-Camtasia verification to tune further.
- [already-implemented] `BehaviorInnerName` enum missing `'fading'` phase name
- [already-implemented] `pulsating` center phase `offsetBetweenCharacters` should be `49392000` (not `0`)

### Infrastructure
- [already-implemented] `media_bin.import_media()` appends _1/_2/... suffix on directory collision
- [already-implemented] `media_bin._visual_track_to_json()` uses `sampleRate=0` for video (should be frame rate)
- [already-implemented] `media_bin` visual/audio track JSONs already include `tag: 0` field
- [already-implemented] `scalar_to_string()` return type annotation is `str | int` and docstring explains the int return
- [already-implemented] `parse_scalar()` docstring documents the 10_000 denominator cap tradeoff
- [already-implemented] `history.py` `undo()`/`redo()` docstrings warn about stale nested references (already present)

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
