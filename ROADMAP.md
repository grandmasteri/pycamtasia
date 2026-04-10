# pycamtasia Roadmap

Planned improvements and feature ideas. Open a GitHub Issue to discuss or contribute.

## Media Import

- [ ] **Native `.trec` import** — Use a Python media library (pymediainfo or PyAV) to probe `.trec` multi-track containers and build correct source bin entries with all stream metadata (screen video, camera video, mic audio, system audio). Currently `.trec` files can only be used by starting from an existing Camtasia project.
- [ ] **Replace ffprobe subprocess calls** — The `import_media()` duration detection currently shells out to `ffprobe`. Replace with a Python library (pymediainfo or PyAV) for cleaner dependency management.
- [ ] **Auto-detect image dimensions** — `import_media()` sets `rect: [0,0,0,0]` for images. Use Pillow or similar to read actual dimensions.

## Timeline

- [ ] **Group clip creation API** — Provide an L2 method to create Group clips (used by Camtasia Rev recordings) with proper UnifiedMedia children, rather than requiring manual `_data` manipulation.
- [ ] **Speed change API for screen recordings** — Apply speed scalars to `.trec`-backed clips, handling the Group/UnifiedMedia structure correctly.

## Export

- [ ] **Exported frame (freeze frame) API** — Extract a frame from a video clip at a given timestamp and insert it as a still image on the timeline.

## Quality of Life

- [ ] **Validate project before save** — Check for common issues (zero-range sources, missing media files, invalid clip references) before writing to disk.
- [ ] **pymediainfo as optional dependency** — Add to `pyproject.toml` extras so users can `pip install pycamtasia[media]`.
- [ ] **Parameter flattening on save** — Camtasia v10 converts dict parameters (`{type, defaultValue, interp}`) to bare scalars on save. Our code still writes dicts for some parameters.
- [ ] **Clip metadata defaults** — Add `audiateLinkedSession`, `clipSpeedAttribute`, `colorAttribute`, `effectApplied` to new clips to match Camtasia's native output.
- [ ] **Image clip `trimStartSum`** — Camtasia adds this field; include it in `add_image()`.
- [ ] **Fade animation hold segment** — Camtasia uses 3 animationTracks segments (fade-in, hold, fade-out) vs our 2. Add the hold segment for full compatibility.
