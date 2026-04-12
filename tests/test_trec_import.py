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


class TestImportTrecMocked:
    """Tests that work without pymediainfo by mocking the probe."""

    def test_import_trec_reuses_existing(self, project):
        """import_trec returns existing media if already imported."""
        # Manually add a media entry with the right name
        project._data['sourceBin'].append({
            'id': 99, 'src': './media/test.trec',
            'rect': [0, 0, 100, 100], 'sourceTracks': [],
        })
        from unittest.mock import patch
        with patch('camtasia.media_bin.trec_probe.probe_trec') as mock_probe:
            result = project.import_trec('/tmp/test.trec')
            # Should NOT call probe since media already exists
            # Actually find_media_by_name looks for stem 'test'
            # The source bin entry has src='./media/test.trec' -> identity='test'
            # So it should find it and return early
            assert result.id == 99
            mock_probe.assert_not_called()

    def test_import_trec_full_path(self, project, tmp_path):
        """import_trec probes and patches source bin entry."""
        from unittest.mock import patch, MagicMock

        trec = tmp_path / 'unique_rec_xyz.trec'
        trec.write_bytes(b'\x00' * 100)

        mock_probe_result = {
            'rect': [0, 0, 1920, 1080],
            'sourceTracks': [{'type': 0, 'tag': 1, 'editRate': 44100, 'range': [0, 9000000]}],
            'lastMod': '20260410T094103',
            'loudnessNormalization': True,
        }

        def fake_import(path):
            # Simulate import_media: add source bin entry and return Media
            entry = {'id': 999, 'src': f'./media/{path.name}'}
            project._data['sourceBin'].append(entry)
            mock_media = MagicMock()
            mock_media.id = 999
            return mock_media

        with patch('camtasia.media_bin.trec_probe.probe_trec', return_value=mock_probe_result):
            with patch.object(project, 'import_media', side_effect=fake_import):
                result = project.import_trec(str(trec))
                assert result.id == 999
                sb = next(s for s in project._data['sourceBin'] if s['id'] == 999)
                assert sb['rect'] == [0, 0, 1920, 1080]
                assert sb['loudnessNormalization'] is True
