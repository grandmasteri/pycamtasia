# pycamtasia Roadmap

Planned improvements and feature ideas. Open a GitHub Issue to discuss or contribute.

## Bugs

- [x] **`fade_in()` + `fade_out()` creates animation collision** — Calling `clip.fade_in(0.5)` followed by `clip.fade_out(0.5)` creates two separate `animationTracks.visual` segments, which Camtasia rejects as an "Animation Collision". Users should be able to call these independently and have them merge into a single animation track. Workaround: use `clip.fade(0.5, 0.5)` which handles this correctly. Fix: `fade_out()` should check for an existing opacity animation track and merge into it rather than appending a new segment.
- [x] **`add_gradient_background()` creates orphaned shader files on re-run** — Each call creates a new `.tscshadervid` file in the media directory (gradient-bg-40, gradient-bg-41, etc.). When the assembly script is re-run and the old gradient clip is removed from the timeline, the shader file remains in the project bundle as an orphan, causing Camtasia to show a "Missing files" warning. Fix: before creating a new shader, check if a gradient source already exists in the bin (`find_media_by_suffix('.tscshadervid')`). If found, reuse that source ID. Also consider a `cleanup_orphaned_media()` method that removes source bin entries and files not referenced by any timeline clip.

## Media Import

- [ ] **Native `.trec` import** — Use a Python media library (pymediainfo or PyAV) to probe `.trec` multi-track containers and build correct source bin entries with all stream metadata (screen video, camera video, mic audio, system audio). Currently `.trec` files can only be used by starting from an existing Camtasia project.
- [ ] **Replace ffprobe subprocess calls** — `import_media()` duration and dimension detection currently shells out to `ffprobe`. Replace with a Python library (pymediainfo or PyAV) for cleaner dependency management.
- [x] **Auto-detect image dimensions** — ~~`import_media()` sets `rect: [0,0,0,0]` for images.~~ Fixed: uses ffprobe to detect width/height.
- [ ] **Audio source metadata accuracy** — Our ffprobe-based import sets approximate values for `editRate`, `sampleRate`, `numChannels`, `bitDepth`, and `range`. Camtasia corrects these on open. Use a proper media library for exact values.

## Timeline

- [x] **Seconds-based setters for clip position** — `clip.start_seconds` and `clip.duration_seconds` are read-only. Users have to call `clip.start = seconds_to_ticks(x)` which leaks the tick abstraction. Add writable `start_seconds` and `duration_seconds` properties.
- [ ] **Group clip creation API** — Provide an L2 method to create Group clips (used by Camtasia Rev recordings) with proper UnifiedMedia children, rather than requiring manual `_data` manipulation.
- [ ] **Speed change API for screen recordings** — Apply speed scalars to `.trec`-backed clips, handling the Group/UnifiedMedia structure correctly.
- [x] **Gain/mute API** — ~~No way to mute clip audio.~~ Fixed: `BaseClip.gain` property and `mute()` method.

## Export

- [ ] **Exported frame (freeze frame) API** — Extract a frame from a video clip at a given timestamp and insert it as a still image on the timeline.

## Quality of Life

- [ ] **Validate project before save** — Check for common issues (zero-range sources, missing media files, invalid clip references) before writing to disk.
- [ ] **pymediainfo as optional dependency** — Add to `pyproject.toml` extras so users can `pip install pycamtasia[media]`.
- [x] **Parameter flattening on save** — ~~Camtasia v10 converts dict parameters to bare scalars.~~ Fixed: `_flatten_parameters()` runs on save.
- [x] **Clip metadata defaults** — ~~Missing v10 metadata fields.~~ Fixed: `add_clip()` includes all defaults.
- [x] **Image clip `trimStartSum`** — ~~Missing field.~~ Fixed: included in `add_image()`.
- [x] **Fade animation hold segment** — ~~Only 2 segments.~~ Fixed: 3 segments (fade-in, hold, fade-out).
- [x] **Source path `./` prefix** — ~~Missing prefix.~~ Fixed: `import_media()` prefixes with `./` and sets metaData filename.
- [x] **Audio clip attributes** — ~~Missing v10 attributes.~~ Fixed: `add_audio()` includes gain, mixToMono, loudnessNormalization, sourceFileOffset, channelNumber.
- [x] **NSJSONSerialization-compatible save** — ~~`save()` wrote compact JSON causing .trec parser crashes.~~ Fixed: matching Camtasia's formatting with scalar array collapsing, expanded empty objects, and `-Infinity` replacement.

## Testing

- [ ] **Camtasia open-in-app integration test** — Automate launching Camtasia via CLI and checking stderr for exceptions as a CI validation step.
- [ ] **Round-trip test for .trec projects** — Load a .trec-containing project, save, and verify Camtasia opens without crashes.
