# Audio-Video Sync from Transcript

You have a voiceover recording and a separate screen recording. You want to assemble them into a Camtasia project where the video segments are speed-adjusted to match the narration timing. This guide walks through the labeled-markers workflow.

## The approach

1. Record voiceover and screen recording separately
2. Add labeled markers to the screen recording at key sync points (e.g., "selecting a batch run", "click into details")
3. Generate word-level timestamps from the voiceover using WhisperX or Audiate (see {doc}`transcripts`)
4. Use `plan_sync()` to match markers to transcript words and calculate per-segment speed adjustments

The key insight: markers on the video timeline describe *what's happening on screen*, and the transcript describes *when the narrator says those words*. By matching them, you get the speed scalar needed for each video segment.

## Full pipeline

```python
from camtasia.audiate import Transcript
from camtasia.operations import plan_sync
from camtasia.timing import seconds_to_ticks

# Get transcript from WhisperX (see Transcripts guide)
transcript = Transcript.from_whisperx_result(whisperx_output)

# Define markers: (label, video_time_in_ticks)
# These come from the markers you placed on the screen recording
markers = [
    ("selecting a batch run", seconds_to_ticks(5.0)),
    ("click into details", seconds_to_ticks(30.0)),
    ("review the results", seconds_to_ticks(55.0)),
]

# Plan the sync — returns one SyncSegment per gap between markers
segments = plan_sync(markers, transcript.words)
for seg in segments:
    print(f"Video {seg.video_start_ticks}-{seg.video_end_ticks}: "
          f"scalar={float(seg.scalar):.3f}")
```

## How marker matching works

`match_marker_to_transcript()` does case-insensitive substring matching against the full transcript text. Given a marker label like "selecting a batch run", it:

1. Joins all transcript words into a single string
2. Searches for the label as a substring
3. Returns the start timestamp of the matching word

If the full label isn't found, it falls back to matching just the first word. This handles cases where the narrator's phrasing differs slightly from the marker label.

```python
from camtasia.operations import match_marker_to_transcript

# words is a list of dicts: [{"word": "...", "start": 0.0, "end": 0.5}, ...]
audio_time = match_marker_to_transcript("selecting a batch run", words)
if audio_time is not None:
    print(f"Narrator says this at {audio_time:.2f}s")
```

## What SyncSegment contains

Each `SyncSegment` represents the gap between two consecutive markers:

| Field | Description |
|-------|-------------|
| `video_start_ticks` | Segment start on the video timeline (ticks) |
| `video_end_ticks` | Segment end on the video timeline (ticks) |
| `audio_start_seconds` | Corresponding audio start (seconds) |
| `audio_end_seconds` | Corresponding audio end (seconds) |
| `scalar` | Camtasia scalar as a `Fraction` |

The `scalar` is `video_duration_ticks / audio_duration_ticks`. Use it to set the speed of the corresponding video clip in the Camtasia project:

- `scalar > 1` → video segment is longer than audio → video plays slower
- `scalar < 1` → video segment is shorter than audio → video plays faster
- `scalar = 1` → already in sync

## Tips

- Place markers at natural transition points in the screen recording — moments where you switch context or perform a distinct action
- Use descriptive marker labels that match what the narrator says. The fuzzy matching is simple substring search, so closer labels work better
- You need at least 2 markers to get any segments (segments span the gaps between consecutive markers)
- The `transcript.words` property returns `Word` objects, but `plan_sync()` expects the raw dict format from WhisperX (`{"word": ..., "start": ..., "end": ...}`). Use `transcript.words` with the `Word` dataclass attributes if you need to convert

```{note}
This is the V3 sync workflow. It replaces earlier approaches that tried to match audio and video automatically. The labeled-markers approach gives you explicit control over sync points.
```
