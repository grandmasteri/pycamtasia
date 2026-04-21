"""Tests for caption extract/reimport (export/captions.py)."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import pytest

from camtasia import Project
from camtasia.export import CaptionEntry, export_captions, import_captions


@pytest.fixture
def project_with_subtitles():
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    proj.add_subtitle_track([
        (0.0, 2.0, 'Hello world'),
        (2.0, 3.0, 'Line two'),
        (5.0, 1.0, 'Short line'),
    ])
    return proj


def test_export_captions_creates_json(project_with_subtitles, tmp_path):
    out = tmp_path / 'captions.json'
    export_captions(project_with_subtitles, out)
    entries = json.loads(out.read_text())
    assert len(entries) == 3
    assert entries[0]['text'] == 'Hello world'
    assert entries[0]['start_seconds'] == 0.0
    assert entries[0]['duration_seconds'] == 2.0


def test_export_captions_raises_on_missing_track(project_with_subtitles, tmp_path):
    out = tmp_path / 'captions.json'
    with pytest.raises(KeyError, match='No track named'):
        export_captions(project_with_subtitles, out, track_name='Nonexistent')


def test_import_captions_updates_text(project_with_subtitles, tmp_path):
    out = tmp_path / 'captions.json'
    export_captions(project_with_subtitles, out)
    # Translate: swap text
    data = json.loads(out.read_text())
    data[0]['text'] = 'Bonjour le monde'
    data[1]['text'] = 'Ligne deux'
    out.write_text(json.dumps(data))
    count = import_captions(project_with_subtitles, out)
    assert count == 3
    track = project_with_subtitles.timeline.find_track_by_name('Subtitles')
    texts = [c._data.get('def', {}).get('text') for c in track.clips]
    assert 'Bonjour le monde' in texts
    assert 'Ligne deux' in texts


def test_import_captions_overwrite_false_strict_count(project_with_subtitles, tmp_path):
    out = tmp_path / 'captions.json'
    data = [{'start_seconds': 0.0, 'duration_seconds': 2.0, 'text': 'one'}]
    out.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='differs from'):
        import_captions(project_with_subtitles, out, overwrite=False)


def test_import_captions_raises_on_missing_track(project_with_subtitles, tmp_path):
    out = tmp_path / 'captions.json'
    out.write_text('[]')
    with pytest.raises(KeyError, match='No track named'):
        import_captions(project_with_subtitles, out, track_name='Nonexistent')


def test_caption_entry_dataclass():
    e = CaptionEntry(start_seconds=0.0, duration_seconds=1.0, text='hi')
    assert e.text == 'hi'


def test_export_captions_skips_non_callout_clips(tmp_path):
    """Non-Callout clips on the caption track are skipped."""
    tmp = Path(tempfile.mkdtemp()) / 'test.cmproj'
    proj = Project.new(str(tmp))
    track = proj.timeline.get_or_create_track('Subtitles')
    # Add a non-callout clip (e.g., an image)
    src_id = proj.media_bin.next_id()
    proj._data.setdefault('sourceBin', []).append({
        '_type': 'IMFile', 'id': src_id, 'src': './media/fake.png',
        'sourceTracks': [{'range': [0, 1], 'type': 0, 'editRate': 30,
            'trackRect': [0, 0, 1, 1], 'sampleRate': 30, 'bitDepth': 24,
            'numChannels': 0, 'integratedLUFS': 100.0, 'peakLevel': -1.0,
            'metaData': '', 'tag': 0}],
        'lastMod': 'X', 'loudnessNormalization': False,
        'rect': [0, 0, 1, 1], 'metadata': {'timeAdded': ''},
    })
    track.add_clip('IMFile', src_id, 0, 705600000)
    out = tmp_path / 'captions.json'
    export_captions(proj, out)
    entries = json.loads(out.read_text())
    # Non-callout should be skipped; no captions found
    assert entries == []


def test_import_captions_nonmatching_timing_skipped(project_with_subtitles, tmp_path):
    """Entries with timing that doesn't match any existing callout are skipped."""
    out = tmp_path / 'captions.json'
    export_captions(project_with_subtitles, out)
    data = json.loads(out.read_text())
    # Add an entry with non-matching timing
    data.append({'start_seconds': 99.0, 'duration_seconds': 1.0, 'text': 'orphan'})
    out.write_text(json.dumps(data))
    count = import_captions(project_with_subtitles, out)
    # Only the 3 matching entries updated; orphan skipped
    assert count == 3
