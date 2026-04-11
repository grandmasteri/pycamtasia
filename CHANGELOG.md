# Changelog

All notable changes to pycamtasia are documented in this file.

## Unreleased

### Clip Transforms & Animation
- `clip.move_to(x, y)` — reposition clip on canvas
- `clip.scale_to(factor)` — uniform scale
- `clip.scale_to_xy(sx, sy)` — non-uniform scale
- `clip.crop(left, top, right, bottom)` — crop with input validation
- `clip.rotation` — rotation property (degrees)
- `clip.fade_in(duration)`, `clip.fade_out(duration)`, `clip.fade(in, out)` — fade animations
- `clip.set_opacity(value)` — static opacity with validation
- `clip.add_keyframe(time, value)` — custom keyframe insertion
- `clip.clear_keyframes()` — remove all keyframes

### Clip Effects (Convenience Methods)
- `clip.add_drop_shadow(offset, blur, opacity)`
- `clip.add_round_corners(radius)`
- `clip.add_glow()`

### Track API
- `track.clear()` — remove all clips from a track
- `track.add_lower_third()` — now supports `font_weight`, `scale`, `template_ident` kwargs
- `track.add_screen_recording()` — add screen recording clips
- `track.add_group()` — create group clips
- `track.find_clip(clip_id)` — locate a clip by ID

### Timeline API
- `timeline.move_track(from_index, to_index)` — move a track to a new position
- `timeline.reorder_tracks(order)` — reorder all tracks by index list
- `timeline.move_track_to_front(index)` — move track to top
- `timeline.move_track_to_back(index)` — move track to bottom
- `timeline.find_clip(clip_id)` — search all tracks for a clip
- `timeline.next_clip_id()` — project-wide safe clip ID allocator

### Project
- `project.width`, `project.height` — canvas dimension properties
- `project.import_shader(path)` — import `.tscshadervid` shader files

### Group Clips
- `group.is_screen_recording` — detect `.trec`-backed groups
- `group.internal_media_src` — access internal media source path
- `group.set_internal_segment_speeds()` — per-segment speed control

### Media
- `media.duration_seconds` — duration property on media bin entries

### Python Protocols
- `__eq__`, `__hash__`, `__len__`, `__repr__` implemented on all major types (clips, tracks, markers, transitions, effects, media)

### Input Validation
- Crop values validated (0.0–1.0 range)
- Opacity validated (0.0–1.0 range)
- Speed validated (positive, non-zero)
- Clip type validated on add operations

### Effects
- `Glow` effect class added to public API

### Internal
- `BaseClip` transforms consolidated into shared base class
- Test count: 1079
