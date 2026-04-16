# Camtasia .tscproj Format Reference

This document is the definitive reference for the Camtasia project file format (`.tscproj`). It is derived from analysis of real TechSmith sample projects and is intended for engineers and AI agents working with the pycamtasia library.

---

## Overview

A `.tscproj` file is a JSON document (UTF-8, no BOM). The file is the root of a Camtasia project package directory. Media assets (recordings, images, audio) live alongside the `.tscproj` file or in subdirectories. All time values are integers in **edit-rate units** where `editRate = 705600000` ticks per second (i.e., 1 second = 705,600,000 ticks). This is the universal time base for the entire project.

The format has evolved across Camtasia versions. The `version` field at the top level indicates the schema version (e.g., `"6.0"`, `"8.0"`, `"10.0"`). Older files (version 6.x) use slightly different metadata conventions (plain scalars instead of typed objects in some places).

---

## 1. Top-Level Keys

```json
{
  "title": "",
  "description": "",
  "author": "",
  "targetLoudness": -18.0,
  "shouldApplyLoudnessNormalization": true,
  "videoFormatFrameRate": 60,
  "audioFormatSampleRate": 44100,
  "allowSubFrameEditing": false,
  "width": 1920.0,
  "height": 1080.0,
  "version": "10.0",
  "editRate": 705600000,
  "authoringClientName": { ... },
  "sourceBin": [ ... ],
  "timeline": { ... },
  "duration": 0,
  "metadata": { ... }
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `title` | string | yes | Project title (often empty) |
| `description` | string | yes | Project description (often empty) |
| `author` | string | yes | Author name (often empty) |
| `targetLoudness` | number | yes | Target loudness in LUFS, e.g. `-18.0` |
| `shouldApplyLoudnessNormalization` | bool | yes | Whether to normalize audio loudness |
| `videoFormatFrameRate` | int | yes | Output frame rate (e.g. `30`, `60`) |
| `audioFormatSampleRate` | int | yes | Output audio sample rate (e.g. `44100`, `48000`) |
| `allowSubFrameEditing` | bool | yes | Whether sub-frame editing is enabled |
| `width` | number | yes | Canvas width in pixels (e.g. `1920.0`) |
| `height` | number | yes | Canvas height in pixels (e.g. `1080.0`) |
| `version` | string | yes | Schema version string (e.g. `"8.0"`, `"10.0"`) |
| `editRate` | int | yes | **Always `705600000`**. Ticks per second for all time values |
| `authoringClientName` | object | yes | Info about the Camtasia version that created the file |
| `sourceBin` | array | yes | All media assets referenced by the project |
| `timeline` | object | yes | The main timeline containing all tracks and clips |
| `duration` | int | no | Total project duration (sometimes `0`, computed from timeline) |
| `metadata` | object | no | Arbitrary key-value project metadata (autosave path, canvas zoom, etc.) |

### `authoringClientName`

```json
{
  "name": "Camtasia",
  "platform": "Mac",
  "version": "2026.0.7"
}
```

Older files (version 6.x) use a top-level `clientName` string and `ident` string instead of `authoringClientName`.

---

## 2. `sourceBin` — Media Asset Registry

`sourceBin` is an array of **source bin entries**, one per media file referenced by the project. Each entry describes a file on disk and its tracks (video, audio, image).

```json
{
  "id": 1,
  "src": "./recordings/screen-recording-001.trec",
  "rect": [0, 0, 2560, 1440],
  "lastMod": "20260408T013807",
  "loudnessNormalization": true,
  "sourceTracks": [ ... ],
  "effectDef": [ ... ],
  "metadata": {
    "timeAdded": "20260408T014425.056345"
  }
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | int | yes | Unique integer ID. Referenced by clips in the timeline via `src` |
| `src` | string | yes | Relative path to the media file from the project directory |
| `rect` | [x, y, w, h] | yes | Bounding rect of the media: `[0, 0, width, height]` |
| `lastMod` | string | yes | Last-modified timestamp of the file (`YYYYMMDDTHHmmss`) |
| `loudnessNormalization` | bool | yes | Whether loudness normalization applies to this asset |
| `sourceTracks` | array | yes | One entry per track (video/audio/image) in the file |
| `effectDef` | array | no | Parameter definitions for shader/Lottie assets (see below) |
| `metadata` | object | yes | Contains `timeAdded` (ISO timestamp when added to project, includes fractional seconds in `.%f` format, e.g. `"20260408T014425.056345"`) and optionally `previewImageTime` |

### `sourceTracks` Entry

Each source track describes one stream within the media file.

```json
{
  "range": [0, 139004],
  "type": 0,
  "editRate": 600,
  "trackRect": [0, 0, 2560, 1440],
  "sampleRate": "61531/5000",
  "bitDepth": 24,
  "numChannels": 0,
  "integratedLUFS": 100.0,
  "peakLevel": -1.0,
  "tag": 1,
  "metaData": "screen-recording-001.trec;...",
  "parameters": {}
}
```

| Key | Type | Description |
|-----|------|-------------|
| `range` | [start, end] | Frame/sample range in the source file's native edit rate |
| `type` | int | `0` = video, `1` = image/still, `2` = audio |
| `editRate` | int or string | Native edit rate of this track (frames/sec for video, samples/sec for audio). Can be a rational string like `"30000/1001"` for NTSC content |
| `trackRect` | [x, y, w, h] | Dimensions of this track |
| `sampleRate` | number or string | Frame rate or sample rate (may be a rational string like `"61531/5000"`) |
| `bitDepth` | int | Bit depth (0 for images) |
| `numChannels` | int | Audio channels (0 for video/image) |
| `integratedLUFS` | number | Integrated loudness; `100.0` means not measured |
| `peakLevel` | number | Peak level; `-1.0` means not measured |
| `tag` | int | Optional tag (0 = default, 1 = screen recording) |
| `metaData` | string | Semicolon-separated metadata string (file name + codec GUIDs for `.trec` files) |
| `parameters` | object | Additional parameters (usually empty `{}`) |

**Track type values:**
- `0` — Video track (screen recording, camera, animation)
- `1` — Image/still track (PNG, JPEG)
- `2` — Audio track (WAV, MP3, embedded audio in `.trec`)

### `effectDef` (Shader/Lottie Assets Only)

Present on `.tscshadervid` (shader video) and `.json` (Lottie animation) source bin entries. Defines the parameters that can be customized via `sourceEffect` on clips.

```json
{
  "name": "Color0",
  "type": "Color",
  "defaultValue": [0.368, 0.047, 0.733, 1.0],
  "scalingType": 3,
  "unitType": 0,
  "userInterfaceType": 6
}
```

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | Parameter name (referenced in `sourceEffect.parameters` with `-red`/`-green`/`-blue`/`-alpha` suffixes for Color type) |
| `type` | string | `"Color"`, `"double"`, `"string"`, `"Position"` |
| `defaultValue` | any | Default value (array for Color/Position, number for double, string for string) |
| `maxValue` | any | Maximum value (for numeric types) |
| `minValue` | any | Minimum value (for numeric types) |
| `scalingType` | int | How the value scales (0=linear, 3=color) |
| `unitType` | int | Unit type (0=none, 1=percentage) |
| `userInterfaceType` | int | UI widget type (0=slider, 6=color picker) |

---

## 3. `timeline` — The Main Timeline

The timeline contains all tracks, clips, effects, and transitions that make up the video.

```
timeline
├── id: int
├── sceneTrack
│   └── scenes: [...]
│       └── csml
│           └── tracks: [...]
├── trackAttributes: [...]
├── captionAttributes: {...}
├── gain: number
├── legacyAttenuateAudioMix: bool
└── backgroundColor: [r, g, b, a]
```

### Top-Level Timeline Keys

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | int | yes | Unique ID for the timeline object |
| `sceneTrack` | object | yes | Contains the `scenes` array |
| `trackAttributes` | array | yes | Per-track display attributes (one per top-level track) |
| `captionAttributes` | object | no | Caption/subtitle settings |
| `gain` | number | yes | Master audio gain (usually `1.0`) |
| `legacyAttenuateAudioMix` | bool | yes | Legacy audio mixing flag |
| `backgroundColor` | [r,g,b,a] | yes | Canvas background color (0-255 per channel) |

### Scene Hierarchy

```
sceneTrack.scenes[0].csml.tracks → array of Track objects
```

In practice, there is always exactly **one scene** in the `scenes` array. The `csml` object within the scene contains the `tracks` array, which holds all top-level timeline tracks.

---

## 4. Track Structure

Each track in the `tracks` array represents a timeline lane. Tracks are ordered by `trackIndex` (0-based, bottom-to-top in the visual stack — track 0 is the lowest layer).

### Track Object (Top-Level)

```json
{
  "trackIndex": 0,
  "medias": [ ... ],
  "transitions": [ ... ],
  "parameters": {},
  "ident": "",
  "audioMuted": false,
  "videoHidden": false,
  "magnetic": false,
  "matte": 0,
  "solo": false,
  "metadata": {
    "IsLocked": "False",
    "WinTrackHeight": "56",
    "trackHeight": "54"
  }
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `trackIndex` | int | yes | 0-based index of this track |
| `medias` | array | yes | Array of clip objects on this track |
| `transitions` | array | no | Array of transition objects between clips |
| `parameters` | object | no | Track-level parameters (usually empty `{}`) |
| `ident` | string | yes | Track identifier (usually empty `""`) |
| `audioMuted` | bool | yes | Whether audio is muted on this track |
| `videoHidden` | bool | yes | Whether video is hidden on this track |
| `magnetic` | bool | yes | Whether clips snap together |
| `matte` | int | yes | Matte mode: `0`=none, `1`=alpha matte, `2`=luma matte |
| `solo` | bool | yes | Whether this track is soloed |
| `metadata` | object | no | UI metadata (lock state, track height) |

### `trackAttributes` (Timeline-Level)

The `trackAttributes` array at the timeline level mirrors the top-level tracks. Each entry has the same shape as the track-level attributes (`ident`, `audioMuted`, `videoHidden`, `magnetic`, `matte`, `solo`, `metadata`).

---

## 5. Clip Types (`_type` Values)

Every clip in a `medias` array has a `_type` field that determines its structure. Here are all observed types:

### Common Clip Fields (All Types)

These fields appear on **every** clip regardless of type:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | int | yes | Globally unique integer ID |
| `_type` | string | yes | Clip type discriminator |
| `start` | int | yes | Start position on the timeline (edit-rate ticks) |
| `duration` | int | yes | Duration on the timeline (edit-rate ticks) |
| `mediaStart` | int/number | yes | Start position within the source media |
| `mediaDuration` | int/number | yes | Duration within the source media |
| `scalar` | number/string | yes | Speed scalar. `1` = normal speed. Can be a rational string like `"4509/4825"`. **`scalar = 1/speed`**: a scalar < 1 means faster playback, scalar > 1 means slower playback |
| `parameters` | object | yes | Transform and property parameters |
| `effects` | array | yes | Array of applied effects |
| `metadata` | object | yes | Arbitrary metadata (see below) |
| `animationTracks` | object | yes | Animation keyframe tracks (see below) |

**Speed/duration relationship:** `mediaDuration = duration / scalar = duration * speed`. When a clip is sped up (e.g., 2× speed → scalar = 0.5), the `mediaDuration` is larger than `duration` because more source media is consumed in less timeline time.

### `VMFile` — Video Media File

A video clip referencing a source bin entry.

| Key | Type | Description |
|-----|------|-------------|
| `src` | int | Source bin entry `id` |
| `trackNumber` | int | Which track within the source file (0=first video, 1=second video, etc.) |
| `attributes.ident` | string | Display name of the clip |
| `sourceEffect` | object | Optional: source-level effect for shader/Lottie assets |

### `ScreenVMFile` — Screen Recording Video

Same as `VMFile` but specifically for screen recording tracks. Has additional cursor parameters:

| Key | Type | Description |
|-----|------|-------------|
| `cursorScale` | parameter | Cursor size multiplier |
| `cursorOpacity` | parameter | Cursor opacity (0.0-1.0) |
| `cursorTrackLevel` | parameter | Cursor tracking level (v10+) |
| `smoothCursorAcrossEditDuration` | int | `0` = disabled |

### `ScreenIMFile` — Screen Recording Frame (Still)

A single frame extracted from a screen recording, used as a still image within a `StitchedMedia`. Has `cursorLocation` parameter with point keyframes for cursor position, and `cursorImagePath` for the cursor image.

### `AMFile` — Audio Media File

An audio-only clip.

| Key | Type | Description |
|-----|------|-------------|
| `src` | int | Source bin entry `id` |
| `trackNumber` | int | Audio track index within the source |
| `channelNumber` | string | Channel mapping, e.g. `"0,1"` for stereo, `"0"` for mono |
| `attributes.gain` | number | Audio gain (usually `1.0`) |
| `attributes.mixToMono` | bool | Whether to mix to mono |
| `attributes.loudnessNormalization` | bool | Whether loudness normalization is applied |
| `attributes.sourceFileOffset` | int | Offset into the source file |

### `IMFile` — Image File

A still image clip.

| Key | Type | Description |
|-----|------|-------------|
| `src` | int | Source bin entry `id` |
| `trackNumber` | int | Always `0` |
| `trimStartSum` | int | Accumulated trim from the start |
| `attributes.ident` | string | Display name |

Note: For images, `mediaDuration` is typically `1` (one frame) while `duration` is the display time on the timeline.

### `Callout` — Annotations, Shapes, and Text

The most versatile clip type. Used for text overlays, shapes, buttons, blurs, and more.

| Key | Type | Description |
|-----|------|-------------|
| `def` | object | **Required.** The callout definition (shape, text, colors, etc.) |
| `attributes.ident` | string | Display name |
| `attributes.autoRotateText` | bool | Whether text auto-rotates |

#### `def` Object (Callout Definition)

| Key | Type | Description |
|-----|------|-------------|
| `kind` | string | `"remix"`, `"TypeWinBlur"`, or other callout kinds |
| `shape` | string | `"text"`, `"text-rectangle"`, `"shape-rectangle"`, etc. |
| `style` | string | `"bold"`, `"basic"`, `"urban"`, `"abstract"`, etc. |
| `text` | string | Text content (for text callouts) |
| `font` | object | Font settings: `name`, `weight`, `size`, `tracking`, `color-red/green/blue` |
| `textAttributes` | object | Rich text attributes with per-character formatting (see §14) |
| `width` | number | Width in pixels |
| `height` | number | Height in pixels |
| `fill-color-red/green/blue/opacity` | number | Fill color (0.0-1.0 per channel) |
| `stroke-color-red/green/blue/opacity` | number | Stroke color |
| `stroke-width` | number | Stroke width in pixels |
| `corner-radius` | number | Corner radius for rounded shapes |
| `fill-style` | string | `"solid"`, `"gradient"` |
| `stroke-style` | string | `"solid"` |
| `horizontal-alignment` | string | `"left"`, `"center"`, `"right"` |
| `vertical-alignment` | string | `"top"`, `"center"`, `"bottom"` |
| `resize-behavior` | string | `"resizeText"`, `"resizeCallout"` |
| `word-wrap` | number | `1.0` = enabled |
| `line-spacing` | number | Line spacing adjustment |
| `enable-ligatures` | number | `1.0` = enabled |
| `blur-invert` | number | For blur callouts (`TypeWinBlur`) |
| `intensity` | number | For blur callouts |

**Note:** `def` values for color properties can themselves be animated parameter objects (with `type`, `defaultValue`, `keyframes`) — this is unusual but observed in real projects. Any `def` property can potentially be an animated parameter object rather than a plain scalar.

### `Group` — Grouped Clips

A container that holds multiple tracks of child clips. Groups can be nested.

| Key | Type | Description |
|-----|------|-------------|
| `tracks` | array | Array of child track objects (same structure as top-level tracks) |
| `attributes` | object | Group attributes (see §8) |

Groups do **not** have `src`, `trackNumber`, or `def`. They have their own `parameters`, `effects`, `metadata`, and `animationTracks` like any clip.

**Required Group `parameters`** (verified from real Camtasia before/after diff — Groups MUST have these):
- `geometryCrop0`, `geometryCrop1`, `geometryCrop2`, `geometryCrop3` — crop values (typically `0`)
- `volume` — audio volume (typically `1.0`)

**Required Group `metadata`** keys:
- `clipSpeedAttribute` — whether clip speed has been modified
- `colorAttribute` — clip color label in the UI
- `effectApplied` — name of the last applied effect (or `"none"`)
- `isOpen` — whether the group is expanded in the UI

Omitting these causes Camtasia to reject or silently repair the project file on load.

### `UnifiedMedia` — Linked Video+Audio

A container that pairs a video sub-clip with an audio sub-clip from the same source.

| Key | Type | Description |
|-----|------|-------------|
| `video` | object | A `VMFile` sub-clip |
| `audio` | object | An `AMFile` sub-clip |

The `UnifiedMedia` itself has `start`, `duration`, `mediaStart`, `mediaDuration`, `scalar`, and `metadata`, but the `video` and `audio` sub-clips have their own independent `effects`, `parameters`, and timing.

### `StitchedMedia` — Spliced Clips

A container for multiple sub-clips from the same source that have been split/trimmed. Used when a recording is cut into segments.

| Key | Type | Description |
|-----|------|-------------|
| `minMediaStart` | number | Minimum media start across all sub-clips (usually `0` or `0.0`) |
| `medias` | array | Array of sub-clips (typically `ScreenVMFile` or `AMFile`) |
| `attributes` | object | Same as `AMFile` attributes (ident, gain, etc.) |

The `StitchedMedia` wrapper has its own `parameters` (with transform, cursor settings) and `effects` that apply to all sub-clips. Each sub-clip in `medias` has its own `start`, `duration`, `mediaStart`, `mediaDuration` relative to the stitched media's internal timeline.

---

## 6. Effect Structure

Effects are applied to clips via the `effects` array. There are two kinds: **standard effects** and **behavior effects** (see §11).

### Standard Effect

```json
{
  "effectName": "DropShadow",
  "bypassed": false,
  "category": "categoryVisualEffects",
  "parameters": {
    "angle": 5.49778714378214,
    "enabled": 1,
    "offset": 25.0,
    "blur": 8.0,
    "opacity": 0.4,
    "color-red": 0.1216,
    "color-green": 0.1216,
    "color-blue": 0.1216,
    "color-alpha": 1.0
  },
  "metadata": {
    "effectIndex": "0",
    "presetName": "Tasteful"
  },
  "start": 5386080000,
  "leftEdgeMods": [ ... ]
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `effectName` | string | yes | Effect identifier (e.g. `"DropShadow"`, `"RoundCorners"`, `"Mask"`, `"MotionBlur"`, `"LutEffect"`, `"Emphasize"`, `"Spotlight"`, `"ColorAdjustment"`, `"BlendModeEffect"`, `"MediaMatte"`, `"SourceEffect"`) |
| `bypassed` | bool | yes | Whether the effect is disabled |
| `category` | string | yes | `"categoryVisualEffects"`, `"categoryAudioEffects"`, `"categoryCursorEffects"`, `"categoryClickEffects"`, or `""` (for SourceEffect) |
| `parameters` | object | yes | Effect-specific parameters (see §12 for value formats) |
| `metadata` | object | no | Optional metadata (`effectIndex`, `presetName`) |
| `start` | int | no | Effect start time (for effects that don't span the full clip, e.g. Spotlight) |
| `leftEdgeMods` | array | no | Edge modifications for fade-in behavior on effects |

### Observed Effect Names

| Effect | Category | Key Parameters |
|--------|----------|----------------|
| `DropShadow` | visual | `angle`, `offset`, `blur`, `opacity`, `color-*`, `enabled` |
| `RoundCorners` | visual | `radius`, `top-left`, `top-right`, `bottom-left`, `bottom-right` |
| `Mask` | visual | `mask-shape`, `mask-opacity`, `mask-blend`, `mask-invert`, `mask-rotation`, `mask-width`, `mask-height`, `mask-positionX`, `mask-positionY`, `mask-cornerRadius` |
| `MotionBlur` | visual | `intensity` |
| `LutEffect` | visual | `lutSource`, `lut_intensity`, `channel`, `shadowRampStart/End`, `highlightRampStart/End` |
| `Spotlight` | visual | `brightness`, `concentration`, `opacity`, `positionX/Y`, `directionX/Y`, `color-*` |
| `ColorAdjustment` | visual | `brightness`, `contrast`, `saturation`, `channel`, `shadowRampStart/End`, `highlightRampStart/End` |
| `BlendModeEffect` | visual | `mode`, `intensity`, `invert`, `channel` |
| `MediaMatte` | visual | `matteMode`, `intensity`, `trackDepth` |
| `Emphasize` | audio | `emphasizeAmount`, `emphasizeRampPosition`, `emphasizeRampInTime`, `emphasizeRampOutTime` |
| `SourceEffect` | (empty) | Dynamic parameters from `effectDef` (e.g. `Color0-red`, `sourceFileType`) |
| `CursorMotionBlur` | cursor | `intensity` |
| `CursorShadow` | cursor | `angle`, `offset`, `blur`, `opacity`, `color-*`, `enabled` |
| `CursorPhysics` | cursor | `intensity`, `tilt` |
| `LeftClickScaling` | click | `scale`, `speed` |

### `leftEdgeMods`

Used on effects like `Spotlight` to create a fade-in at the effect's start:

```json
{
  "group": "Video",
  "duration": 705600000,
  "parameters": [
    { "name": "opacity", "func": "FadeFromValueFunc", "value": 1.0 }
  ]
}
```

---

## 7. Transition Structure

Transitions appear in the `transitions` array on a track. They define visual transitions between clips.

```json
{
  "name": "FadeThroughBlack",
  "duration": 705600000,
  "leftMedia": 31,
  "rightMedia": null,
  "attributes": {
    "Color-blue": 0.0,
    "Color-green": 0.0,
    "Color-red": 0.0,
    "bypass": false,
    "reverse": false,
    "trivial": false,
    "useAudioPreRoll": true,
    "useVisualPreRoll": true
  }
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | yes | Transition type: `"FadeThroughBlack"`, `"SlideRight"`, `"SlideLeft"`, etc. |
| `duration` | int | yes | Transition duration in edit-rate ticks (typically `705600000` = 1 second) |
| `leftMedia` | int | conditional | ID of the clip on the left side of the transition |
| `rightMedia` | int | conditional | ID of the clip on the right side of the transition |
| `attributes` | object | yes | Transition attributes |

**Rules:**
- A transition has either `leftMedia`, `rightMedia`, or both — never neither.
- `leftMedia` only → transition at the **end** of that clip (fade-out / out-transition)
- `rightMedia` only → transition at the **start** of that clip (fade-in / in-transition)
- Both → transition **between** two adjacent clips (cross-dissolve)
- The absent side is set to `null` (not omitted)

### Transition Attributes

| Key | Type | Description |
|-----|------|-------------|
| `bypass` | bool | Whether the transition is disabled |
| `reverse` | bool | Whether to play the transition in reverse |
| `trivial` | bool | Whether this is a trivial/simple transition |
| `useAudioPreRoll` | bool | Whether to use audio pre-roll |
| `useVisualPreRoll` | bool | Whether to use visual pre-roll |
| `Color-red/green/blue` | number | Color parameter (for color-based transitions like `FadeThroughBlack`) |

---

## 8. Group Structure

Groups (`_type: "Group"`) are containers that hold nested tracks of child clips. They are the primary mechanism for creating complex, reusable assets (lower thirds, title cards, buttons, etc.).

### Group-Specific Keys

| Key | Type | Description |
|-----|------|-------------|
| `tracks` | array | Array of child tracks (same structure as top-level tracks, with `trackIndex`, `medias`, track attributes) |
| `attributes.ident` | string | Group name (e.g. `"BigMotionBrackets"`, `"Subscribe Bell"`, `"Left Bracket"`) |
| `attributes.widthAttr` | number | Logical width of the group in pixels |
| `attributes.heightAttr` | number | Logical height of the group in pixels |
| `attributes.maxDurationAttr` | int | Maximum duration (v10+, optional) |
| `attributes.gain` | number | Audio gain for the group |
| `attributes.mixToMono` | bool | Whether to mix audio to mono |
| `attributes.assetProperties` | array | Theme-mappable asset property definitions |

### `assetProperties`

Defines which child clips are theme-mappable and how:

```json
{
  "type": 0,
  "name": "Title",
  "objects": [10],
  "themeMappings": {
    "font-color": "foreground-1"
  }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `type` | int | `0` = text, `1` = shape/visual, `2` = logo/image |
| `name` | string | Human-readable name for this asset property |
| `objects` | array | Array of clip IDs (ints) or objects like `{"media": 46, "property": "Color000"}` |
| `themeMappings` | object | Maps theme roles to theme slots (e.g. `"font-color": "foreground-1"`, `"fill": "accent-1"`) |

### Group Nesting

Groups can be deeply nested. A common pattern from TechSmith samples:

**Internal Group track keys:** Each track inside a Group's `tracks` array has the following keys: `audioMuted`, `ident`, `magnetic`, `matte`, `medias`, `parameters`, `solo`, `trackIndex`, `videoHidden`. These match the top-level track structure but do **not** include `transitions` or `metadata`.

**Cross-track grouping:** When clips from multiple source tracks are grouped, the Group preserves empty source tracks. For example, if a Group contains clips from tracks 0 and 2, track 1 will still exist inside the Group with an empty `medias` array.

```
Group "BigMotionBrackets" (top-level asset)
├── Track 0: Callout (title text)
├── Track 1: Group "Left Bracket"
│   ├── Track 0: Group "Group 2" (bracket shape + fill)
│   │   ├── Track 0: Callout (stroke rectangle)
│   │   └── Track 1: Callout (fill rectangle)
│   └── Track 1: Callout (background fill)
└── Track 2: Group "Right Bracket" (mirror of Left Bracket)
```

---

## 9. `UnifiedMedia` Structure

`UnifiedMedia` pairs a video and audio sub-clip from the same source file, keeping them linked.

```json
{
  "id": 34,
  "_type": "UnifiedMedia",
  "video": {
    "id": 35,
    "_type": "VMFile",
    "src": 3,
    "trackNumber": 1,
    "parameters": { ... },
    "effects": [ ... ],
    "start": 0,
    "duration": 10172400000,
    "mediaStart": 787920000,
    "mediaDuration": 10172400000,
    "scalar": 1,
    "animationTracks": {}
  },
  "audio": {
    "id": 36,
    "_type": "AMFile",
    "src": 3,
    "trackNumber": 2,
    "channelNumber": "0,1",
    "attributes": { ... },
    "effects": [ ... ],
    "start": 0,
    "duration": 10172400000,
    "mediaStart": 787920000,
    "mediaDuration": 10172400000,
    "scalar": 1,
    "animationTracks": {}
  },
  "start": 0,
  "duration": 10172400000,
  "mediaStart": 787920000,
  "mediaDuration": 10172400000,
  "scalar": 1,
  "metadata": { ... }
}
```

The `video` sub-clip can have visual effects (DropShadow, RoundCorners, Mask, LutEffect). The `audio` sub-clip can have audio effects (Emphasize). The outer `UnifiedMedia` has its own `start`/`duration` that should match the sub-clips.

**Important:** Effects belong on the `video` and `audio` children, **not** on the outer `UnifiedMedia` wrapper. The wrapper's `effects` array should be empty. Placing effects on the wrapper instead of the children will cause them to be ignored or produce unexpected behavior.

---

## 10. `StitchedMedia` Structure

`StitchedMedia` represents a single logical clip composed of multiple spliced segments from the same source. Created when a recording is split/trimmed.

```json
{
  "id": 15,
  "_type": "StitchedMedia",
  "minMediaStart": 0.0,
  "attributes": {
    "ident": "recording-name",
    "gain": 1.0,
    "mixToMono": false,
    "loudnessNormalization": true,
    "sourceFileOffset": 0
  },
  "parameters": {
    "translation0": { ... },
    "scale0": { ... },
    "volume": 1.0,
    "cursorScale": 5.0,
    "smoothCursorAcrossEditDuration": 0
  },
  "medias": [
    { "_type": "AMFile", "start": 0, "duration": 126514080000, "mediaStart": 0, ... },
    { "_type": "AMFile", "start": 126514080000, "duration": 109074000000, "mediaStart": 130465440000, ... }
  ],
  "effects": [ ... ],
  "start": 227120880000,
  "duration": 72947280000,
  "mediaStart": 232212960000,
  "mediaDuration": 72947280000,
  "scalar": 1
}
```

The `medias` array contains the sub-clips in order. Each sub-clip's `start` is relative to the StitchedMedia's internal timeline. The outer `mediaStart`/`mediaDuration` define which portion of the stitched sequence is visible.

---

## 11. Behavior Effects (`GenericBehaviorEffect`)

Behavior effects are text/callout animation behaviors with three phases: **in**, **center**, and **out**. They are identified by `_type: "GenericBehaviorEffect"` in the effects array.

```json
{
  "_type": "GenericBehaviorEffect",
  "effectName": "pulsating",
  "bypassed": false,
  "start": 0,
  "duration": 5433120000,
  "in": { ... },
  "center": { ... },
  "out": { ... },
  "metadata": {
    "presetName": "Sliding",
    "default-behavior-center-style": "fading",
    "default-behavior-out-direction": { "type": "int", "value": 2 }
  }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `_type` | string | Always `"GenericBehaviorEffect"` |
| `effectName` | string | Behavior name: `"popUp"`, `"pulsating"`, `"reveal"`, `"sliding"` |
| `bypassed` | bool | Whether the behavior is disabled |
| `start` | int | Start time relative to the clip |
| `duration` | int | Duration of the behavior |
| `in` | object | Entry animation phase |
| `center` | object | Sustain/loop animation phase |
| `out` | object | Exit animation phase |
| `metadata` | object | Optional preset info |

### Phase Structure (`in`, `center`, `out`)

Each phase has `attributes` and optionally `parameters`:

```json
{
  "attributes": {
    "name": "sliding",
    "type": 0,
    "characterOrder": 7,
    "offsetBetweenCharacters": 35280000,
    "suggestedDurationPerCharacter": 705600000,
    "overlapProportion": "11/20",
    "movement": 16,
    "springDamping": 5.0,
    "springStiffness": 50.0,
    "bounceBounciness": 0.45
  },
  "parameters": {
    "direction": {
      "type": "int",
      "valueBounds": { "minValue": 0, "maxValue": 3, "defaultValue": 0 },
      "uiHints": { "userInterfaceType": 2, "unitType": 0 },
      "keyframes": [{ "endTime": 0, "time": 0, "value": 0, "duration": 0 }]
    }
  }
}
```

**Phase attribute names observed:** `"grow"`, `"shrink"`, `"hinge"`, `"shifting"`, `"sliding"`, `"reveal"`, `"pulsate"`, `"tremble"`, `"none"`, `"fading"`

**Phase `attributes` keys:**

| Key | Type | Description |
|-----|------|-------------|
| `name` | string | Animation style name |
| `type` | int | `0` = whole-object, `1` = per-character |
| `characterOrder` | int | Character animation order (0-7) |
| `offsetBetweenCharacters` | int | Delay between characters (edit-rate ticks) |
| `suggestedDurationPerCharacter` | int | Duration per character animation |
| `overlapProportion` | number/string | Overlap between character animations (can be rational like `"3/4"`) |
| `movement` | int | Movement amount/direction |
| `springDamping` | number | Spring physics damping |
| `springStiffness` | number | Spring physics stiffness |
| `bounceBounciness` | number | Bounce physics bounciness |
| `secondsPerLoop` | number/string | Loop duration (center phase) |
| `numberOfLoops` | int | Number of loops (`-1` = infinite) |
| `delayBetweenLoops` | int | Delay between loops |

---

## 12. Parameter Formats

Parameters appear in `parameters` objects on clips, effects, and groups. A parameter value can be in two formats:

### Plain Scalar

```json
"translation0": 199.0,
"volume": 1.0,
"smoothCursorAcrossEditDuration": 0
```

A simple number (or int, or string). This is the static value with no animation.

### Animated Parameter Object

```json
"translation0": {
  "type": "double",
  "defaultValue": 175.0,
  "interp": "eioe",
  "keyframes": [
    {
      "endTime": 470400000,
      "time": 0,
      "value": -320.0,
      "interp": "eioe",
      "duration": 470400000
    }
  ],
  "valueBounds": {
    "minValue": 0,
    "maxValue": 3,
    "defaultValue": 0
  },
  "uiHints": {
    "userInterfaceType": 0,
    "unitType": 0
  }
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `type` | string | yes | `"double"`, `"int"`, `"bool"`, `"point"`, `"textAttributeList"` |
| `defaultValue` | any | yes | The base/rest value when no keyframe is active |
| `interp` | string | no | Default interpolation for the parameter |
| `keyframes` | array | no | Array of keyframe objects |
| `valueBounds` | object | no | Min/max/default bounds for the value |
| `uiHints` | object | no | UI display hints |

### Common Parameter Keys

| Parameter | Description |
|-----------|-------------|
| `translation0` | X position offset (pixels) |
| `translation1` | Y position offset (pixels) |
| `translation2` | Z position offset |
| `scale0` | X scale factor |
| `scale1` | Y scale factor |
| `rotation0/1/2` | Rotation around X/Y/Z axes (radians) |
| `shear0/1/2` | Shear transforms |
| `anchor0/1/2` | Anchor point offsets |
| `geometryCrop0` | Crop from left |
| `geometryCrop1` | Crop from top |
| `geometryCrop2` | Crop from right |
| `geometryCrop3` | Crop from bottom |
| `sourceCrop0/1/2/3` | Source-level crop (older format) |
| `opacity` | Visual opacity (0.0-1.0) |
| `volume` | Audio volume (0.0-1.0+) |

---

## 13. Keyframe Format

```json
{
  "endTime": 470400000,
  "time": 0,
  "value": -320.0,
  "interp": "eioe",
  "duration": 470400000
}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `endTime` | int | yes | End time of the keyframe transition (edit-rate ticks, relative to clip's media timeline) |
| `time` | int | yes | Start time of the keyframe transition |
| `value` | any | yes | Target value at `time` (the value being animated **to** at `endTime` is the `defaultValue` or next keyframe) |
| `duration` | int | yes | Duration of the transition (`endTime - time`) |
| `interp` | string | no | Interpolation type for this specific keyframe |

### Interpolation Types

| Value | Description |
|-------|-------------|
| `"linr"` | Linear interpolation |
| `"eioe"` | Ease-in/ease-out (smooth) |
| `"sprg"` | Spring physics |
| `"bnce"` | Bounce physics |

**Note:** `time` and `endTime` are relative to the clip's internal media timeline, not the project timeline. They can be negative (for animations that start before the clip's visible portion).

### Point Keyframes

For `type: "point"` parameters (e.g., `cursorLocation`):

```json
{
  "endTime": -7053530400,
  "time": -7053530400,
  "value": [-371, -673, 0],
  "duration": 0
}
```

The `value` is a `[x, y, z]` array.

---

## 14. `captionAttributes` Structure

Located at `timeline.captionAttributes`:

```json
{
  "enabled": true,
  "fontName": "Arial",
  "fontSize": 32,
  "backgroundColor": [0, 0, 0, 191],
  "foregroundColor": [255, 255, 255, 255],
  "lang": "en",
  "alignment": 0,
  "defaultFontSize": true,
  "opacity": 0.5,
  "backgroundEnabled": true,
  "backgroundOnlyAroundText": true
}
```

| Key | Type | Description |
|-----|------|-------------|
| `enabled` | bool | Whether captions are enabled |
| `fontName` | string | Caption font name |
| `fontSize` | int | Caption font size |
| `backgroundColor` | [r,g,b,a] | Background color (0-255) |
| `foregroundColor` | [r,g,b,a] | Text color (0-255) |
| `lang` | string | Language code (e.g. `"en"`) |
| `alignment` | int | Text alignment (0=center) |
| `defaultFontSize` | bool | Whether using default font size |
| `opacity` | number | Background opacity |
| `backgroundEnabled` | bool | Whether background is shown |
| `backgroundOnlyAroundText` | bool | Whether background wraps text only |

---

## 15. Key Conventions

### Time Units

**All time values** in the project are in edit-rate ticks where `editRate = 705600000` ticks per second. To convert:
- Ticks to seconds: `ticks / 705600000`
- Seconds to ticks: `seconds * 705600000`
- 1 frame at 30fps = `705600000 / 30 = 23520000` ticks

### Hyphenated Parameter Keys

Effect parameters frequently use **hyphens** in key names:
- `color-red`, `color-green`, `color-blue`, `color-alpha`
- `fill-color-red`, `fill-color-green`, `fill-color-blue`, `fill-color-opacity`
- `stroke-color-red`, `stroke-color-green`, `stroke-color-blue`
- `mask-shape`, `mask-opacity`, `mask-blend`, `mask-width`, `mask-height`
- `top-left`, `top-right`, `bottom-left`, `bottom-right`
- `text-stroke-width`, `text-stroke-color-red`
- `fill-style`, `stroke-style`
- `horizontal-alignment`, `vertical-alignment`
- `resize-behavior`, `word-wrap`

SourceEffect parameters for Color-type effectDefs use the pattern: `{ColorName}-red`, `{ColorName}-green`, `{ColorName}-blue`, `{ColorName}-alpha` (e.g., `Color0-red`, `Color000-blue`).

### ID Allocation

All `id` values are globally unique positive integers, allocated sequentially. The timeline itself gets an `id`, and every clip (including sub-clips inside Groups, UnifiedMedia, and StitchedMedia) gets its own `id`.

### Metadata Conventions

Clip `metadata` objects contain a mix of:
- **Typed values:** `{ "type": "bool", "value": false }` or `{ "type": "double", "value": 1080.0 }` or `{ "type": "int", "value": 84 }` or `{ "type": "color", "value": [0,0,0,0] }`
- **Plain strings:** `"effectApplied": "none"`, `"default-scale": "1"`
- **Default-prefixed keys:** `"default-translation0"`, `"default-scale0"`, `"default-width"`, `"default-height"` — store the original/default values before user modifications
- **Effect defaults:** `"default-MotionBlur-intensity": "1"`, `"default-SourceEffect-Color0": "(255,0,0,255)"`

Common metadata keys:
- `clipSpeedAttribute` — whether clip speed has been modified
- `effectApplied` — name of the last applied effect (or `"none"`)
- `lockAspectRatio` — whether aspect ratio is locked
- `isOpen` — whether a group is expanded in the UI
- `audiateLinkedSession` — Audiate integration session ID
- `AppliedThemeId` — UUID of the applied theme
- `colorAttribute` — clip color label in the UI

### `animationTracks`

The `animationTracks` object on clips defines animation regions (where keyframe animations are active):

```json
"animationTracks": {
  "visual": [
    {
      "endTime": 470400000,
      "duration": 470400000,
      "range": [0, 470400000],
      "interp": "eioe"
    },
    {
      "endTime": 10172400000,
      "duration": 294000000,
      "range": [9878400000, 294000000],
      "interp": "linr"
    }
  ]
}
```

Each entry in the `visual` array defines a time range where animation is active. The `range` is `[startTime, duration]`. Empty `animationTracks: {}` means no animations.

### `textAttributes` (Rich Text)

The `textAttributes` field in callout `def` objects stores per-character formatting:

```json
{
  "type": "textAttributeList",
  "keyframes": [{
    "endTime": 0,
    "time": 0,
    "value": [
      {"name": "fontName", "rangeStart": 0, "rangeEnd": 16, "value": "Source Sans Pro", "valueType": "string"},
      {"name": "fontSize", "rangeStart": 0, "rangeEnd": 16, "value": 115.0, "valueType": "double"},
      {"name": "fgColor", "rangeStart": 0, "rangeEnd": 16, "value": "(35,40,47,255)", "valueType": "color"},
      {"name": "fontWeight", "rangeStart": 0, "rangeEnd": 16, "value": 700, "valueType": "int"},
      {"name": "fontItalic", "rangeStart": 0, "rangeEnd": 16, "value": 1, "valueType": "int"},
      {"name": "kerning", "rangeStart": 0, "rangeEnd": 16, "value": 0.0, "valueType": "double"},
      {"name": "underline", "rangeStart": 0, "rangeEnd": 16, "value": 0, "valueType": "int"},
      {"name": "strikethrough", "rangeStart": 0, "rangeEnd": 16, "value": 0, "valueType": "int"}
    ],
    "duration": 0
  }]
}
```

Each entry in the `value` array applies a text attribute to a character range (`rangeStart` to `rangeEnd`). The `valueType` can be `"string"`, `"double"`, `"int"`, or `"color"` (formatted as `"(r,g,b,a)"` with 0-255 values).

### Scalar and Rational Numbers

The `scalar` field (and some other values) can be:
- An integer: `1`
- A float: `1.0`
- A rational string: `"4509/4825"`, `"49/64"`, `"69/142"`

Similarly, `mediaDuration` can be a rational string: `"60540480000/23"`.

### Version Differences

| Feature | v6.0 | v8.0 | v10.0 |
|---------|------|------|-------|
| Top-level client info | `clientName` string | `authoringClientName` object | `authoringClientName` object |
| Metadata values | Plain scalars | Mix of typed and plain | Mostly typed objects |
| `sourceCrop` params | Present | Present | Removed (use `geometryCrop` only) |
| `tag` on sourceTracks | Absent | Absent | Present |
| `cursorTrackLevel` | Absent | Absent | Present |
| `colorAttribute` in metadata | Absent | Absent | Present |
| `ScreenIMFile` type | Absent | Absent | Present |
| `maxDurationAttr` on Groups | Absent | Absent | Present |
