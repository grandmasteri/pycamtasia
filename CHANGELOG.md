# Changelog

All notable changes to pycamtasia are documented in this file.

## Unreleased

26 commits. Test count: 925 → 1267 (+342 tests, +37%). 100% coverage maintained throughout.

### Core Infrastructure
- `timeline.next_clip_id()` — project-wide safe clip ID allocator
- `timeline.reorder_tracks(order)` — reorder all tracks by index list
- `timeline.move_track(from_index, to_index)` — move a track to a new position
- Parameter flattening on save (`_flatten_parameters()`) for Camtasia v10 compatibility
- `RGBA` and `hex_rgb` exported from top-level `camtasia` package
- `Project.save()` now emits `warnings.warn()` instead of `print()` for validation issues

### Clip API
- **Transforms**: `move_to(x, y)`, `scale_to(factor)`, `scale_to_xy(sx, sy)`, `crop()`, `rotation` property
- **Keyframes**: `add_keyframe(time, value)`, `clear_keyframes()`
- **Animation**: `fade_in(duration)`, `fade_out(duration)`, `fade(in, out)`, `set_opacity(value)`
- **Effects**: `add_drop_shadow(offset, blur, opacity)`, `add_round_corners(radius)`, `add_glow()`
- **Source effect**: `clip.source_effect` property for accessing source-level effects
- **Audio convenience** (AMFile): `is_muted` property, `set_gain()` with validation, `normalize_gain()` for LUFS loudness normalization
- **Speed**: `set_speed()` with input validation (positive, non-zero)
- Transforms consolidated into shared `BaseClip` base class

### Track API
- `track.clear()` — remove all clips from a track
- `track.mute()` / `track.unmute()` — audio mute convenience
- `track.hide()` / `track.show()` — visibility convenience
- `track.duplicate_clip(clip_id, offset_seconds)` — duplicate with nested ID remapping
- `track.move_clip(clip_id, new_start_seconds)` — reposition a clip
- `track.find_clip(clip_id)` — locate a clip by ID
- `track.add_lower_third()` — now supports `font_weight`, `scale`, `template_ident` kwargs
- `track.add_screen_recording()` — add screen recording clips
- `track.add_group()` — create group clips

### Timeline API
- `timeline.clips_in_range(start, end)` — time-based clip search
- `timeline.clips_of_type(clip_type)` — type-based filtering
- `timeline.audio_clips`, `timeline.image_clips`, `timeline.video_clips` — convenience properties
- `timeline.move_track_to_front(index)` / `timeline.move_track_to_back(index)`
- `timeline.find_clip(clip_id)` — search all tracks for a clip
- `timeline.find_track(name)` — locate a track by name
- `timeline.remove_empty_tracks()` — prune empty tracks

### Project API
- `project.width`, `project.height` — canvas dimension properties
- `project.import_shader(path)` — import `.tscshadervid` shader files
- `project.summary()` — human-readable project overview
- `project.statistics()` — comprehensive project metrics dict
- `project.validate()` — validation with rules for duplicate clip IDs and track indices

### Operations (new modules)
- **Layout** (`camtasia.operations.layout`): `pack_track()`, `ripple_insert()`, `ripple_delete()`, `snap_to_grid()`
- **Batch** (`camtasia.operations.batch`): `apply_to_clips()`, `apply_to_track()`, `apply_to_all_tracks()`, `set_opacity_all()`, `fade_all()`, `scale_all()`, `move_all()`
- **Cleanup** (`camtasia.operations.cleanup`): `remove_orphaned_media()`, `remove_empty_tracks()`, `compact_project()`
- **Diff** (`camtasia.operations.diff`): `diff_projects()`, `ProjectDiff` with `has_changes` and `summary()`
- **Speed** wrappers: `rescale_project()`, `set_audio_speed()`
- **Sync**: `plan_sync()`, `match_marker_to_transcript()`, `SyncSegment`
- **Template**: `clone_project_structure()`, `replace_media_source()`, `duplicate_project()`

### Export (new modules)
- **SRT** (`camtasia.export.srt`): `export_markers_as_srt()` — export timeline markers as SRT subtitles
- **Report** (`camtasia.export.report`): `export_project_report()` — JSON or Markdown project reports
- **Timeline JSON** (`camtasia.export.timeline_json`): `export_timeline_json()`, `load_timeline_json()` — portable timeline representation

### Builders (new modules)
- **TimelineBuilder** (`camtasia.builders.timeline_builder`): cursor-based fluent API for video assembly — `add_audio()`, `add_image()`, `add_title()`, `add_pause()`, `advance()`, `seek()`
- **CalloutBuilder** (`camtasia.timeline.clips.callout`): fluent API for styled text callouts — `font()`, `color()`, `position()`, `size()`, `alignment()`

### Python Protocols
- `__eq__`, `__hash__`, `__len__`, `__repr__` implemented on all major types (clips, tracks, markers, transitions, effects, media)

### Input Validation
- Crop values validated (0.0–1.0 range)
- Opacity validated (0.0–1.0 range)
- Speed validated (positive, non-zero)
- Audio gain validated in `set_gain()`
- Clip type validated on add operations

### Group Clips
- `group.is_screen_recording` — detect `.trec`-backed groups
- `group.internal_media_src` — access internal media source path
- `group.set_internal_segment_speeds()` — per-segment speed control

### Effects
- `Glow` effect class added to public API
- `SourceEffect` creation support

### Media
- `media.duration_seconds` — duration property on media bin entries

### Documentation
- Module-level docstrings added to `color`, `annotations.types`, `cli`, `frame_stamp`, `timeline.track_media`, `timeline.clips.unified`, and ~85 public methods
- Docstrings on all property setters
- README updated with full feature list and API reference
- ROADMAP updated with completed items
- CHANGELOG created

### Test Quality
- `assert len(...)` anti-patterns replaced with content assertions across test suite
- Type annotations added to test files
- Round-trip tests for real `.trec`-containing projects
- 100% coverage maintained across all 26 commits
