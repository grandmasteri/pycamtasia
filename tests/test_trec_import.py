from __future__ import annotations
import pytest
from pathlib import Path

pymediainfo = pytest.importorskip('pymediainfo')


class TestProbeTrec:
    def test_probe_returns_metadata(self):
        from camtasia.media_bin.trec_probe import probe_trec
        trec_files = list(Path('/tmp/Anomaly Detection Demo (v3).cmproj/recordings').rglob('*.trec'))
        if not trec_files:
            pytest.skip('No .trec files available')
        result = probe_trec(trec_files[0])
        assert 'rect' in result
        assert 'sourceTracks' in result
        assert result['rect'][2] > 0  # width > 0
        assert result['rect'][3] > 0  # height > 0

    def test_probe_has_video_track(self):
        from camtasia.media_bin.trec_probe import probe_trec
        trec_files = list(Path('/tmp/Anomaly Detection Demo (v3).cmproj/recordings').rglob('*.trec'))
        if not trec_files:
            pytest.skip('No .trec files available')
        result = probe_trec(trec_files[0])
        video_tracks = [t for t in result['sourceTracks'] if t['type'] == 0]
        assert video_tracks  # at least one video track
        assert video_tracks[0]['tag'] == 1  # screen recording

    def test_probe_has_audio_track(self):
        from camtasia.media_bin.trec_probe import probe_trec
        trec_files = list(Path('/tmp/Anomaly Detection Demo (v3).cmproj/recordings').rglob('*.trec'))
        if not trec_files:
            pytest.skip('No .trec files available')
        result = probe_trec(trec_files[0])
        audio_tracks = [t for t in result['sourceTracks'] if t['type'] == 2]
        assert audio_tracks  # at least one audio track

    def test_probe_nonexistent_raises(self):
        from camtasia.media_bin.trec_probe import probe_trec
        with pytest.raises(FileNotFoundError):
            probe_trec('/nonexistent/file.trec')


