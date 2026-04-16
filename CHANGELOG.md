# Changelog

All notable changes to pycamtasia are documented in this file.

## [Unreleased]

## [7.2.0] (2026-04-16)

15 rounds of adversarial code review. 100+ bugs found and fixed. Test count: 2126 → 2676 (+550 tests). 100% coverage maintained.

### Added

#### Cross-Track Grouping
- `group_clips_across_tracks()` — group clips spanning multiple tracks into a single group clip

#### Comprehensive Validation
- `validate_all()` — unified validation entry point covering structural integrity, schema conformance, and semantic checks

#### Fraction-Based Scalar Arithmetic
- All time scalars now use `Fraction`-based arithmetic for lossless rational precision throughout the pipeline

### Changed

#### GenericBehaviorEffect Inheritance
- `GenericBehaviorEffect` now inherits from `Effect`, unifying the behavior/effect class hierarchy

#### IntEncodedTime Removed
- `IntEncodedTime` class removed; all encoded-time logic consolidated into `Fraction`-based scalars

#### Schema Relaxed
- JSON Schema loosened for `version` and `parameter` types to accept values observed in real-world TechSmith projects

#### Template Pre-Flattened
- Built-in templates are now pre-flattened for direct Camtasia compatibility, eliminating runtime flattening overhead

#### Integer Tick Accumulator
- Segment speed calculations now use an integer tick accumulator to prevent floating-point drift across segments

### Testing & Reliability
- 2676 tests, 100% line coverage
- Parallel test execution via `pytest-xdist` — **14 seconds** vs 4+ minutes sequential
- 15 rounds of adversarial code review (100+ bugs fixed)
- All 93 TechSmith sample projects pass schema validation

## [7.1.0] (2026-04-14)

7 rounds of adversarial code review. 63+ bugs found and fixed. Test count: 1825 → 2126 (+301 tests). 100% coverage maintained.

### Added

#### JSON Schema & Format Reference
- Camtasia `.tscproj` JSON Schema — built from 93 TechSmith sample projects with strict enum validation
- Camtasia format reference document — comprehensive field-level documentation of the `.tscproj` structure

### Fixed

#### Fabricated Enum Values
- Replaced invented enum strings with values validated against TechSmith samples across effects, transitions, behaviors, and clip types

#### Inverted mediaDuration Formula
- Corrected mediaDuration calculation that had numerator and denominator swapped, producing wrong durations at non-1× speeds

#### Missing Required Fields
- Added required fields omitted from serialized output (detected via JSON Schema validation against real projects)

#### Wrong Parameter Keys
- Fixed parameter key names that diverged from Camtasia's actual format (e.g., camelCase vs hyphenated, misspelled keys)

#### Additional Fixes (63+ total across 7 review rounds)
- Enum values, parameter formats, default values, and serialization logic corrected throughout the codebase
- All fixes verified against TechSmith sample corpus and JSON Schema

### Testing & Reliability
- 2126 tests, 100% line coverage
- JSON Schema validation integrated into test suite
- All 93 TechSmith sample projects pass schema validation

## [7.0.0] (2026-04-14)

390 commits. Test count: 925 → 1825 (+900 tests, +97%). 100% coverage maintained throughout.

### Added

#### Screenplay & High-Level Workflow
- `parse_screenplay()` — markdown screenplay parser for structured VO/pause/image blocks
- `ScreenplayBuilder` — automated VO+pause timeline assembly from parsed screenplays
- `build_from_screenplay()` pipeline complete (parser + builder)

#### Clip API
- `BaseClip.clone()` — deep copy a clip with new ID allocation
- `Track.replace_clip()` — replace a clip in-place with transition cascade cleanup
- **Transforms**: `move_to(x, y)`, `scale_to(factor)`, `scale_to_xy(sx, sy)`, `crop()`, `rotation` property
- **Keyframes**: `add_keyframe(time, value)`, `clear_keyframes()`
- **Animation**: `fade_in(duration)`, `fade_out(duration)`, `fade(in, out)`, `set_opacity(value)`
- **Effects**: `add_drop_shadow(offset, blur, opacity)`, `add_round_corners(radius)`, `add_glow()`
- **Source effect**: `clip.source_effect` property for accessing source-level effects
- **Time range**: `clip.set_time_range(start_seconds, duration_seconds)` — set start and duration in one call
- **Copy effects**: `clip.copy_effects_from(source)` — copy all effects from another clip
- **Audio convenience** (AMFile): `is_muted` property, `set_gain()` with validation, `normalize_gain()` for LUFS loudness normalization
- **Speed**: `set_speed()` with input validation (positive, non-zero)
- Transforms consolidated into shared `BaseClip` base class

#### Track API
- `track.clear()` — remove all clips from a track
- `track.mute()` / `track.unmute()` — audio mute convenience
- `track.hide()` / `track.show()` — visibility convenience
- `track.duplicate_clip(clip_id, offset_seconds)` — duplicate with nested ID remapping
- `track.move_clip(clip_id, new_start_seconds)` — reposition a clip
- `track.find_clip(clip_id)` — locate a clip by ID
- `track.trim_clip(clip_id, trim_start, trim_end)` — trim clip from start/end
- `track.extend_clip(clip_id, extend_seconds)` — extend clip duration
- `track.swap_clips(clip_id_a, clip_id_b)` — swap positions of two clips
- `track.gaps()` — find gaps between clips on a track
- `track.overlaps()` — find overlapping clip pairs
- `track.total_duration_seconds` — total duration of all clips on track
- `track.__iter__` / `track.__contains__` — iterate clips, test membership
- `track.add_lower_third()` — now supports `font_weight`, `scale`, `template_ident` kwargs
- `track.add_screen_recording()` — add screen recording clips
- `track.add_group()` — create group clips

#### Timeline API
- `timeline.next_clip_id()` — project-wide safe clip ID allocator
- `timeline.reorder_tracks(order)` — reorder all tracks by index list
- `timeline.move_track(from_index, to_index)` — move a track to a new position
- `timeline.shift_all(seconds)` — shift all clips on all tracks by a time offset
- `timeline.validate_structure()` — structural integrity checks returning list of issues
- `timeline.total_duration_seconds` — total timeline duration property
- `timeline.clips_in_range(start, end)` — time-based clip search
- `timeline.clips_of_type(clip_type)` — type-based filtering
- `timeline.audio_clips`, `timeline.image_clips`, `timeline.video_clips` — convenience properties
- `timeline.move_track_to_front(index)` / `timeline.move_track_to_back(index)`
- `timeline.find_clip(clip_id)` — search all tracks for a clip
- `timeline.find_track(name)` — locate a track by name
- `timeline.remove_empty_tracks()` — prune empty tracks

#### Project API
- `project.width`, `project.height` — canvas dimension properties
- `project.import_shader(path)` — import `.tscshadervid` shader files
- `project.summary()` — human-readable project overview
- `project.statistics()` — comprehensive project metrics dict
- `project.validate()` — validation with rules for duplicate clip IDs and track indices
- `project.info()` — project metadata dict (dimensions, track count, clip count, duration)
- `project.compact()` — remove unused media, empty tracks, and orphaned references
- `project.copy_to(dest_path)` — copy project bundle to a new location
- `project.total_duration_seconds` — total project duration property

#### Operations (new modules)
- **Layout** (`camtasia.operations.layout`): `pack_track()`, `ripple_insert()`, `ripple_delete()`, `snap_to_grid()`
- **Batch** (`camtasia.operations.batch`): `apply_to_clips()`, `apply_to_track()`, `apply_to_all_tracks()`, `set_opacity_all()`, `fade_all()`, `scale_all()`, `move_all()`
- **Cleanup** (`camtasia.operations.cleanup`): `remove_orphaned_media()`, `remove_empty_tracks()`, `compact_project()`
- **Diff** (`camtasia.operations.diff`): `diff_projects()`, `ProjectDiff` with `has_changes` and `summary()`
- **Speed** wrappers: `rescale_project()`, `set_audio_speed()`
- **Sync**: `plan_sync()`, `match_marker_to_transcript()`, `SyncSegment`
- **Template**: `clone_project_structure()`, `replace_media_source()`, `duplicate_project()`
- **Merge** (`camtasia.operations.merge`): `merge_tracks()` — combine tracks from multiple projects

#### Export (new modules)
- **SRT** (`camtasia.export.srt`): `export_markers_as_srt()` — export timeline markers as SRT subtitles
- **Report** (`camtasia.export.report`): `export_project_report()` — JSON or Markdown project reports
- **Timeline JSON** (`camtasia.export.timeline_json`): `export_timeline_json()`, `load_timeline_json()` — portable timeline representation
- **EDL** (`camtasia.export.edl`): `export_edl()` — Edit Decision List export for video editor interop

#### Builders (new modules)
- **TimelineBuilder** (`camtasia.builders.timeline_builder`): cursor-based fluent API for video assembly — `add_audio()`, `add_image()`, `add_title()`, `add_pause()`, `advance()`, `seek()`
- **CalloutBuilder** (`camtasia.timeline.clips.callout`): fluent API for styled text callouts — `font()`, `color()`, `position()`, `size()`, `alignment()`

#### Effects
- `MediaMatte` effect class — matte/mask effect for compositing
- `Glow` effect class added to public API
- `SourceEffect` creation support

#### Group Clips
- `group.is_screen_recording` — detect `.trec`-backed groups
- `group.internal_media_src` — access internal media source path
- `group.set_internal_segment_speeds()` — per-segment speed control

#### CaptionAttributes
- `CaptionAttributes` class for caption styling configuration
- Properties: `enabled`, `font_name`, `font_size`, `background_color`, `foreground_color`, `lang`, `alignment`, `opacity`, `background_enabled`

#### Behaviors
- `get_behavior_preset(preset_name, duration_ticks)` — preset-based callout animations
- Replaces broken `add_behavior()` with validated Camtasia-compatible templates

#### Media
- `media.duration_seconds` — duration property on media bin entries

#### Core Infrastructure
- Native `.trec` import via `probe_trec()` — pymediainfo-based stream probing for screen recordings
- Behavior presets — `get_behavior_preset()` for callout animations (text reveal, fade, fly-in, etc.)
- Parameter flattening on save (`_flatten_parameters()`) for Camtasia v10 compatibility
- `RGBA` and `hex_rgb` exported from top-level `camtasia` package
- `Project.save()` now emits `warnings.warn()` instead of `print()` for validation issues

#### Python Protocols
- `__eq__`, `__hash__`, `__len__`, `__repr__` implemented on all major types (clips, tracks, markers, transitions, effects, media)

#### Input Validation
- Crop values validated (0.0–1.0 range)
- Opacity validated (0.0–1.0 range)
- Speed validated (positive, non-zero)
- Audio gain validated in `set_gain()`
- Clip type validated on add operations

#### Documentation
- Module-level docstrings added to `color`, `annotations.types`, `cli`, `frame_stamp`, `timeline.track_media`, `timeline.clips.unified`, and ~85 public methods
- Docstrings on all property setters
- README updated with full feature list and API reference
- ROADMAP updated with completed items
- CHANGELOG created

### Fixed
- Cascade bugs: `remove_clip`, `clear`, `split_clip`, `move_clip`, `duplicate_clip`, `ripple_delete`, `pack_track`, `set_internal_segment_speeds` all cascade-delete transitions referencing affected clips
- Parameter key names: Mask (hyphens), RoundCorners (hyphens), SourceEffect (radial gradient support)
- `merge_tracks`: recursive Group internal ID/src remapping
- `set_shader_colors`: variable color count for radial/four-corner gradients
- `snap_to_grid`: negative start time clamping
- `add_behavior`: replaced broken GenericBehaviorEffect with preset-based implementation using validated Camtasia templates
- Effect parameter format: correct flattening for Camtasia v10 compatibility
- Infinite loop in `flatten_to_track` when processing nested groups

### Changed
- `add_behavior()` requires using preset names from `get_behavior_preset()`. Custom behavior parameters are not supported — use Camtasia's GUI for non-preset behaviors, or copy behavior data from a reference project.
- `assert len(...)` anti-patterns replaced with content assertions across test suite
- Type annotations added to test files
- Template cleanup: reduced template size from 265MB to 12KB
- Restructured `swap_clips` error handling for 100% coverage in CI

### Testing & Reliability
- TechSmith library fixture with validation of 28 sample assets
- 3 additional Hypothesis invariant tests (trim, extend, swap)
- Added `validate()` transition reference checking
- Hypothesis property-based invariant tests (6 tests)
- Camtasia integration test suite (11 tests, 10 passing)
- Added `pytest-xdist` for parallel test execution
- Added `pytest-timeout` for test safety
- Round-trip tests for real `.trec`-containing projects
- 100% coverage maintained across all 390 commits
