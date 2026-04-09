# Working with Transcripts

pycamtasia can parse word-level transcripts from two sources: TechSmith Audiate and WhisperX. Both produce a `Transcript` object with the same API — a list of `Word` objects with start/end timestamps.

## From Audiate

Audiate is TechSmith's companion app for recording and transcribing voiceovers. The `.audiate` file uses the same JSON schema as Camtasia `.tscproj` files, with transcription data stored as keyframes.

```python
from camtasia.audiate import AudiateProject

project = AudiateProject('path/to/file.audiate')
for word in project.transcript.words:
    print(f"{word.start:.2f}s: {word.text}")
```

`AudiateProject` also exposes:

- `project.language` — language code (e.g. `'en'`)
- `project.audio_duration` — total audio length in seconds
- `project.source_audio_path` — resolved path to the source audio file
- `project.session_id` — UUID for linking back to a Camtasia session

## From WhisperX

WhisperX is a free, locally-run speech recognition model that produces word-level timestamps. Install it separately (`pip install whisperx`).

```python
import whisperx
from camtasia.audiate import Transcript

model = whisperx.load_model('large-v3', 'cpu', compute_type='int8')
audio = whisperx.load_audio('voiceover.wav')
result = model.transcribe(audio, batch_size=4, language='en')
model_a, metadata = whisperx.load_align_model(language_code='en', device='cpu')
result = whisperx.align(result['segments'], model_a, metadata, audio, 'cpu')

transcript = Transcript.from_whisperx_result(result)
print(f"{len(transcript.words)} words, duration: {transcript.duration:.1f}s")
```

The alignment step (`whisperx.align`) is critical — it produces the word-level timestamps that pycamtasia needs. Without it, you only get segment-level timing.

## Transcript API

Once you have a `Transcript`, the API is the same regardless of source:

### Properties

- `transcript.words` — list of `Word` objects
- `transcript.full_text` — all words joined by spaces
- `transcript.duration` — time of the last word's end (seconds)

### find_phrase

Find the first word where a phrase begins:

```python
word = transcript.find_phrase("click the submit button")
if word:
    print(f"Found at {word.start:.2f}s")
```

Matching is case-insensitive and checks consecutive words.

### words_in_range

Get all words within a time window:

```python
segment = transcript.words_in_range(10.0, 20.0)
for w in segment:
    print(f"  {w.start:.2f}s: {w.text}")
```

### Word fields

Each `Word` has:

| Field | Type | Description |
|-------|------|-------------|
| `text` | `str` | The word text |
| `start` | `float` | Start time in seconds |
| `end` | `float \| None` | End time in seconds (None if unavailable) |
| `word_id` | `str` | Unique identifier |

## Audiate vs WhisperX

Both produce similar quality transcripts. The main differences:

| | Audiate | WhisperX |
|---|---------|----------|
| Cost | Paid (TechSmith subscription) | Free / open source |
| Runs | Cloud | Locally (CPU or GPU) |
| Integration | Native `.audiate` file | Requires alignment step |
| Languages | Multiple | Multiple (large-v3) |

WhisperX with the `large-v3` model produces comparable word-level accuracy to Audiate. If you're already using Audiate for recording, use its transcript directly. Otherwise, WhisperX is a solid free alternative.
