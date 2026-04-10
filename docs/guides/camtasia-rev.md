# Camtasia Rev Recordings

Camtasia Rev is the screen recording feature built into Camtasia. When you record with Rev, Camtasia captures up to four streams — screen video, camera video, mic audio, and system audio — into a single `.trec` file (a QuickTime container) stored inside the `.cmproj` project bundle.

On the timeline, a Rev recording appears as a **Group** containing:

- **Track 0** — `VMFile` gradient background shader
- **Track 1** — `UnifiedMedia` with `ScreenVMFile` (screen) + `AMFile` (mic audio)
- **Track 2** *(if camera was enabled)* — `UnifiedMedia` with `VMFile` (camera) + `AMFile` (system audio)

The {class}`~camtasia.timeline.clips.UnifiedMedia` class bundles the video and audio children from the same source.

## UnifiedMedia properties

| Property | Type | Description |
|----------|------|-------------|
| `.video` | `BaseClip` | Video child (`ScreenVMFile` or `VMFile`) |
| `.audio` | `BaseClip` | Audio child (`AMFile`) |
| `.has_audio` | `bool` | Whether an audio track is present |
| `.is_screen_recording` | `bool` | `True` if video is `ScreenVMFile` |
| `.is_camera` | `bool` | `True` if video is `VMFile` (camera) |

## Finding Rev recordings in a project

```python
from camtasia import load_project
from camtasia.timeline.clips import UnifiedMedia

p = load_project('my_project.cmproj')
for track in p.timeline.tracks:
    for clip in track.clips:
        if isinstance(clip, Group):
            for inner_track in clip.tracks:
                for inner_clip in inner_track.clips:
                    if isinstance(inner_clip, UnifiedMedia):
                        if inner_clip.is_screen_recording:
                            print(f'Screen recording: video id={inner_clip.video.id}')
                            if inner_clip.has_audio:
                                print(f'Mic audio: id={inner_clip.audio.id}')
                        elif inner_clip.is_camera:
                            print(f'Camera: video id={inner_clip.video.id}')
```

## .trec stream layout

A `.trec` file can contain up to four streams. Use `ffprobe` to inspect them:

```bash
ffprobe -hide_banner recording.trec
```

Typical output for a Rev recording with camera enabled:

| Stream | Type | Bitrate | Channels | `-map` flag |
|--------|------|---------|----------|-------------|
| Screen video | Video (tscc2) | ~1450 kb/s | — | `0:v:0` |
| Camera video | Video (h264) | ~7139 kb/s | — | `0:v:1` |
| System audio | Audio (aac) | ~2 kb/s | Stereo | `0:a:0` |
| Mic audio | Audio (aac) | ~55 kb/s | Mono | `0:a:1` |

The mic audio stream is mono with a higher bitrate (~55 kb/s); system audio is stereo but very low bitrate (~2 kb/s). This makes it easy to tell them apart in `ffprobe` output.

## Extracting mic audio for transcription

To extract the mic audio as 16 kHz WAV (suitable for speech-to-text):

```bash
ffmpeg -i recording.trec -map 0:a:1 -acodec pcm_s16le -ar 16000 mic_audio.wav
```

`-map 0:a:1` selects the second audio stream (mic). Use `-map 0:a:0` for system audio instead.
