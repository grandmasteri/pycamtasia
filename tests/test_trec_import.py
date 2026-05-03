from __future__ import annotations

from pathlib import Path

import pytest

pymediainfo = pytest.importorskip('pymediainfo')

from camtasia.media_bin.trec_probe import probe_trec  # noqa: E402 — must be after importorskip guard

# External test data: stage a .cmproj with recordings/ to enable these tests.
# See docs/development/publishing.md for integration test setup.
_TREC_PROJECT = Path('/tmp/Anomaly Detection Demo (v3).cmproj/recordings')
_TREC_FILES = list(_TREC_PROJECT.rglob('*.trec')) if _TREC_PROJECT.is_dir() else []

_skip_no_trec = pytest.mark.skipif(
    not _TREC_FILES,
    reason=f'No .trec files in {_TREC_PROJECT} — stage a Camtasia project to enable',
)


class TestProbeTrec:
    @_skip_no_trec
    def test_probe_returns_metadata(self):
        result = probe_trec(_TREC_FILES[0])
        assert 'rect' in result
        assert 'sourceTracks' in result
        assert result['rect'][2] > 0  # width > 0
        assert result['rect'][3] > 0  # height > 0

    @_skip_no_trec
    def test_probe_has_video_track(self):
        result = probe_trec(_TREC_FILES[0])
        video_tracks = [t for t in result['sourceTracks'] if t['type'] == 0]
        assert video_tracks  # at least one video track
        assert video_tracks[0]['tag'] == 1  # screen recording

    @_skip_no_trec
    def test_probe_has_audio_track(self):
        result = probe_trec(_TREC_FILES[0])
        audio_tracks = [t for t in result['sourceTracks'] if t['type'] == 2]
        assert audio_tracks  # at least one audio track

    def test_probe_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            probe_trec('/nonexistent/file.trec')
