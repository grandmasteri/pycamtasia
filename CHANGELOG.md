# Changelog

All notable changes to pycamtasia are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-30

Initial public release on PyPI.

### Added

pycamtasia is a Python library for reading, writing, and manipulating TechSmith
Camtasia project files (`.cmproj` / `.tscproj`) without launching the Camtasia
desktop application. It wraps the underlying JSON format with typed Python
classes, enabling programmatic video assembly via scripts.

Highlights of the public API at initial release:

- **Project I/O** — load, save, validate, and roundtrip `.cmproj` bundles
  (Camtasia 2024+, schema version 10)
- **Timeline model** — `Timeline`, `Track`, `Marker`, `Transition` with full
  mutation, undo/redo via JSON Patch, and cascade-delete semantics
- **Clips** — `AMFile` (audio), `VMFile` (video), `IMFile` (image), `Callout`
  (text overlay), `Group`, `StitchedMedia`, `UnifiedMedia`, `ScreenVMFile` /
  `ScreenIMFile` (screen recordings), `PlaceholderMedia` (templates)
- **Effects** — typed `@register_effect` classes across visual, audio,
  behavior, and source categories; ~80 effects including `DropShadow`, `Glow`,
  `Mask`, `BlurRegion`, `ColorAdjustment`, `LutEffect`, `CornerPin`,
  `ChromaKey`, `MediaMatte`, `MotionPath`, `BackgroundRemoval`, `Crop`,
  `GestureTap` / `Swipe` / `Pinch`, `Hotspot`, `ZoomNPan`, `DeviceFrame`,
  `FreezeRegion`, `Vignette`, `Reflection`, `StaticNoise`, `Tiling`, `Sepia`,
  `CRTMonitor`, `Mosaic`, `OutlineEdges`, `ColorTint`, `Colorize`, `Border`,
  33 cursor and click effects, `AudioCompression`, `Pitch`, `NoiseRemoval`,
  `Equalizer`, `AudioVisualizer`, `GenericBehaviorEffect` with typed
  `BehaviorPhase`
- **Annotations** — callouts (text, square, arrow, highlight, keystroke,
  sketch-motion, line), shapes (rectangle, ellipse, triangle), gradient fills,
  italic/underline/strikethrough, drop shadows, corner radii, favorites
- **Builders** — `TimelineBuilder`, `ScreenplayBuilder`,
  `VideoProductionBuilder`, `add_device_frame`, `add_dynamic_background`,
  `add_lottie_background`, `import_slide_images` / `import_powerpoint`, tile
  layouts
- **Audiate integration** — `AudiateProject` with transcript editing
  (add/delete/convert-to-gap/set-timing), filler-word / pause detection,
  translate/TTS/avatar stubs, SRT export, `apply_suggested_edits`,
  `sync_audiate_edits_to_timeline`
- **Captions** — `CaptionAttributes` with vertical anchor, dynamic caption
  styles (with default presets), word-by-word highlighting, per-caption
  styling, add/edit/remove/split/merge captions, SRT / VTT / SAMI import and
  export, multi-language export, burned-in stub, accessibility validator
- **Canvas & vertical video** — `VerticalPreset` enum (9:16 FHD/HD, 4:5,
  1:1), `SafeZone` presets for Instagram Reels / YouTube Shorts / TikTok
- **Templates** — save/import/install `.camtemplate`, `TemplateManager`,
  `PlaceholderMedia.replace_with` in 4 modes (ripple, clip-speed, from-start,
  from-end)
- **Library module** — `Library`, `Libraries`, `LibraryAsset`, add timeline
  selections / group clips to a library, `.libzip` import and export, nested
  folders
- **Operations** — `ripple_insert`, `ripple_delete`, `ripple_delete_range`,
  `ripple_extend`, `ripple_move`, `ripple_move_multi`, `ripple_replace_in_group`,
  `pack_track`, `snap_to_grid`, `snap_to_clip_edge`, `merge_tracks`,
  `rescale_project`, `set_audio_speed`, `apply_sync`, `plan_sync`,
  `auto_stitch_on_track`, `mark_slides_from_presentation`
- **Exports** — JSON report, EDL, CSV, SRT markers, SRT / VTT captions,
  multi-language captions, `export_audio`, `export_audio_clips`,
  `export_campackage`, `export_toc`, `export_chapters` (WebVTT / MP4 / YouTube)
- **Themes** — `Theme` with logo, export/import, `ThemeManager`, annotation
  background slots, dynamic accent colors, `add_annotation_from_theme`
- **Media Bin** — import single/many/folder, rename, sorted, delete-unused,
  proxy video lifecycle, reverse video, zoom recording metadata, bridge to
  Library
- **Cursor editing** — `ScreenIMFile` cursor path editing (add/delete/move/
  split/smooth/straighten/restore points, per-point bezier handles, per-point
  easing, `CursorPathCreator` for non-TREC media), `CursorType` enum, replace
  cursor with scope, hide/show cursor, cursor visibility / elevation
  properties
- **Validation** — `validate_all`, `validate_caption_accessibility`,
  `Project.validate()`
- **CLI** — `pytsc` command exposing common operations
- **Type safety** — full type hints throughout, `py.typed` marker, mypy
  strict-clean

### Infrastructure

- 100% line coverage (4931 tests, enforced in CI via `--cov-fail-under=100`)
- Parallel test execution via `pytest-xdist`
- ruff + mypy gates in CI across Python 3.10 – 3.13
- Sphinx docs with Furo theme, cross-linked to source
- MIT licensed

[Unreleased]: https://github.com/grandmasteri/pycamtasia/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/grandmasteri/pycamtasia/releases/tag/v0.1.0
