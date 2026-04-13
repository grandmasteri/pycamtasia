# pycamtasia Roadmap

Planned improvements and feature ideas. Open a GitHub Issue to discuss or contribute.

## Bugs

- [x] **`fade_in()` + `fade_out()` creates animation collision** — Calling `clip.fade_in(0.5)` followed by `clip.fade_out(0.5)` creates two separate `animationTracks.visual` segments, which Camtasia rejects as an "Animation Collision". Users should be able to call these independently and have them merge into a single animation track. Workaround: use `clip.fade(0.5, 0.5)` which handles this correctly. Fix: `fade_out()` should check for an existing opacity animation track and merge into it rather than appending a new segment.
- [x] **`add_gradient_background()` creates orphaned shader files on re-run** — Each call creates a new `.tscshadervid` file in the media directory (gradient-bg-40, gradient-bg-41, etc.). When the assembly script is re-run and the old gradient clip is removed from the timeline, the shader file remains in the project bundle as an orphan, causing Camtasia to show a "Missing files" warning. Fix: before creating a new shader, check if a gradient source already exists in the bin (`find_media_by_suffix('.tscshadervid')`). If found, reuse that source ID. Also consider a `cleanup_orphaned_media()` method that removes source bin entries and files not referenced by any timeline clip.

## Media Import

- [x] **Native `.trec` import** — Use a Python media library (pymediainfo or PyAV) to probe `.trec` multi-track containers and build correct source bin entries with all stream metadata (screen video, camera video, mic audio, system audio). Currently `.trec` files can only be used by starting from an existing Camtasia project.
- [x] **Replace ffprobe subprocess calls** — `import_media()` duration and dimension detection currently shells out to `ffprobe`. Replace with a Python library (pymediainfo or PyAV) for cleaner dependency management.
- [x] **Auto-detect image dimensions** — ~~`import_media()` sets `rect: [0,0,0,0]` for images.~~ Fixed: uses ffprobe to detect width/height.
- [x] **Audio source metadata accuracy** — Our ffprobe-based import sets approximate values for `editRate`, `sampleRate`, `numChannels`, `bitDepth`, and `range`. Camtasia corrects these on open. Use a proper media library for exact values.

## Timeline

- [x] **Seconds-based setters for clip position** — `clip.start_seconds` and `clip.duration_seconds` are read-only. Users have to call `clip.start = seconds_to_ticks(x)` which leaks the tick abstraction. Add writable `start_seconds` and `duration_seconds` properties.
- [x] **Group clip creation API** — Provide an L2 method to create Group clips (used by Camtasia Rev recordings) with proper UnifiedMedia children, rather than requiring manual `_data` manipulation.
- [x] **`track.split_clip(clip_id, split_at_seconds)`** — Split a clip into two halves at a given timeline position. Returns (left_clip, right_clip) with correct durations, mediaStart offsets, and new sequential IDs. Handles Group clips by deep-copying internal tracks.
- [x] **Speed change API for screen recordings** — Apply speed scalars to `.trec`-backed clips, handling the Group/UnifiedMedia structure correctly.
- [x] **Gain/mute API** — ~~No way to mute clip audio.~~ Fixed: `BaseClip.gain` property and `mute()` method.
- [x] **Track reorder API** — `timeline.move_track()`, `reorder_tracks()`, `move_track_to_front()`, `move_track_to_back()`.
- [x] **Project-wide clip ID allocator** — `timeline.next_clip_id()` for safe ID generation across all tracks.
- [x] **Clip search** — `track.find_clip()` and `timeline.find_clip()` for locating clips by ID.

## Export

- [x] **Exported frame (freeze frame) API** — Extract a frame from a video clip at a given timestamp and insert it as a still image on the timeline.

## Quality of Life

- [x] **Validate project before save** — Check for common issues (zero-range sources, missing media files, invalid clip references) before writing to disk.
- [x] **pymediainfo as optional dependency** — Add to `pyproject.toml` extras so users can `pip install pycamtasia[media]`.
- [x] **Parameter flattening on save** — ~~Camtasia v10 converts dict parameters to bare scalars.~~ Fixed: `_flatten_parameters()` runs on save.
- [x] **Clip metadata defaults** — ~~Missing v10 metadata fields.~~ Fixed: `add_clip()` includes all defaults.
- [x] **Image clip `trimStartSum`** — ~~Missing field.~~ Fixed: included in `add_image()`.
- [x] **Fade animation hold segment** — ~~Only 2 segments.~~ Fixed: 3 segments (fade-in, hold, fade-out).
- [x] **Source path `./` prefix** — ~~Missing prefix.~~ Fixed: `import_media()` prefixes with `./` and sets metaData filename.
- [x] **Audio clip attributes** — ~~Missing v10 attributes.~~ Fixed: `add_audio()` includes gain, mixToMono, loudnessNormalization, sourceFileOffset, channelNumber.
- [x] **NSJSONSerialization-compatible save** — ~~`save()` wrote compact JSON causing .trec parser crashes.~~ Fixed: matching Camtasia's formatting with scalar array collapsing, expanded empty objects, and `-Infinity` replacement.
- [x] **Python protocols** — `__eq__`, `__hash__`, `__len__`, `__repr__` on all major types.
- [x] **Input validation** — Validation on crop, opacity, speed, and clip type arguments.
- [x] **Keyframe API** — `clip.add_keyframe()`, `clip.clear_keyframes()` for custom animation.
- [x] **Shader import** — `project.import_shader()` for adding `.tscshadervid` files.
- [x] **Lower third kwargs** — `track.add_lower_third()` supports `font_weight`, `scale`, `template_ident`.
- [x] **Marker consolidation** — Two separate Marker classes exist; unify into a single implementation.
- [x] **Type annotations on `color.py`** — Add full type hints to the color module.
- [x] **Round-trip `.trec` tests** — Load/save/validate round-trip tests for `.trec`-containing projects.

## High-Level API (Screenplay-Driven Workflow)

- [x] **`proj.add_progressive_disclosure(images, durations, fade_in=0.5)`** — Takes a list of image source IDs and durations, places each on a SEPARATE track so they accumulate visually (each new image appears on top of previous ones). Returns the list of created clips. Handles fade-in animations automatically.
- [x] **`track.add_title(text, preset, start_seconds, duration_seconds)`** — Add a title callout using a named preset (e.g., `"right_angle_lower_third"`, `"centered"`, `"subtitle"`). Presets define font, size, position, alignment, and animation. Internally replicates the exact Camtasia JSON structure observed in real projects. Eliminates the need to manually set `_data["def"]` fields and `_data["parameters"]["translation0"]`.
- [x] **`track.add_lower_third(title, subtitle, start_seconds, duration_seconds)`** — Add a right-angle lower third title overlay with customizable title/subtitle text, colors, and duration. Uses a JSON template with correct Camtasia v10 structure.
- [x] **`proj.add_voiceover_sequence(vo_files, pauses)`** — Takes a list of voiceover file paths and pause durations, imports them, places them sequentially on an audio track. Returns a dict mapping filenames to timeline positions and durations.
- [x] **`proj.add_four_corner_gradient(shader_path, duration)`** — Import and place the 4-corner animated gradient shader background. Distinct from `add_gradient_background()` which creates a simple 2-color gradient.
- [x] **`proj.build_from_screenplay(screenplay_path)`** — Parse a screenplay markdown file with VO block IDs and automatically build the entire timeline. The ultimate high-level API for the video production pipeline.

## Future

- [x] **Fix `add_behavior`** — ~~GenericBehaviorEffect requires preset-specific attributes.~~ Fixed: replaced with preset-based implementation using validated Camtasia templates.
- [ ] **Lottie animation support** — Import Lottie JSON animations as timeline elements for motion graphics overlays.
- [x] **Caption/subtitle API** — `CaptionAttributes` class for caption styling (font, color, alignment, opacity, background).
- [x] **EDL export** — `export_edl()` for Edit Decision List export to video editors.
- [x] **Project merge** — `merge_tracks()` for combining timelines from multiple projects.
- [x] **Clip manipulation** — `trim_clip()`, `extend_clip()`, `swap_clips()`, `copy_effects_from()`, `set_time_range()`.
- [x] **Project utilities** — `Project.compact()`, `Project.copy_to()`, `Project.info()`.
- [x] **Timeline utilities** — `Timeline.shift_all()`, `Timeline.validate_structure()`.
- [x] **Track analysis** — `gaps()`, `overlaps()`, `total_duration_seconds`, `__iter__`, `__contains__`.

## Testing

- [x] **Camtasia open-in-app integration test** — Automate launching Camtasia via CLI and checking stderr for exceptions as a CI validation step.
- [x] **Round-trip test for `.trec` projects** — Load a .trec-containing project, save, and verify Camtasia opens without crashes.
