# pycamtasia Roadmap

Planned improvements and feature ideas. Open a GitHub Issue to discuss or contribute.

## Media Import

- [ ] **Native `.trec` import** — Use a Python media library (pymediainfo or PyAV) to probe `.trec` multi-track containers and build correct source bin entries with all stream metadata (screen video, camera video, mic audio, system audio). Currently `.trec` files can only be used by starting from an existing Camtasia project.
- [ ] **Replace ffprobe subprocess calls** — `import_media()` duration and dimension detection currently shells out to `ffprobe`. Replace with a Python library (pymediainfo or PyAV) for cleaner dependency management.
- [x] **Auto-detect image dimensions** — ~~`import_media()` sets `rect: [0,0,0,0]` for images.~~ Fixed: uses ffprobe to detect width/height.
- [ ] **Audio source metadata accuracy** — Our ffprobe-based import sets approximate values for `editRate`, `sampleRate`, `numChannels`, `bitDepth`, and `range`. Camtasia corrects these on open. Use a proper media library for exact values.

## Timeline

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
