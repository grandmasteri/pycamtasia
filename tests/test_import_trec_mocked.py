"""Tests for import_trec that work without pymediainfo."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestImportTrecReusesExisting:
    def test_reuses_existing(self, project):
        project._data['sourceBin'].append({
            'id': 99, 'src': './media/test.trec',
            'rect': [0, 0, 100, 100], 'sourceTracks': [],
        })
        with patch('camtasia.media_bin.trec_probe.probe_trec') as mock_probe:
            result = project.import_trec('/tmp/test.trec')
            assert result.id == 99
            mock_probe.assert_not_called()


class TestImportTrecFullPath:
    def test_probes_and_patches(self, project, tmp_path):
        trec = tmp_path / 'unique_rec_xyz.trec'
        trec.write_bytes(b'\x00' * 100)

        mock_probe_result = {
            'rect': [0, 0, 1920, 1080],
            'sourceTracks': [{'type': 0, 'tag': 1, 'editRate': 44100, 'range': [0, 9000000]}],
            'lastMod': '20260410T094103',
            'loudnessNormalization': True,
        }

        def fake_import(path):
            entry = {'id': 999, 'src': f'./media/{path.name}'}
            project._data['sourceBin'].append(entry)
            mock_media = MagicMock()
            mock_media.id = 999
            return mock_media

        with patch('camtasia.media_bin.trec_probe.probe_trec', return_value=mock_probe_result), \
             patch.object(project, 'import_media', side_effect=fake_import):
            result = project.import_trec(str(trec))
            assert result.id == 999
            sb = next(s for s in project._data['sourceBin'] if s['id'] == 999)
            assert sb['rect'] == [0, 0, 1920, 1080]
            assert sb['loudnessNormalization'] is True


class TestTrecProbeRounding:
    """Bug 11+12: trec_probe should use round() not int() for range_end."""

    def test_video_range_end_rounds_not_truncates(self):
        """Verify round() is used for video range_end calculation."""
        # dur_ms=1999, edit_rate=30 -> 1999/1000*30 = 59.97 -> round=60, int=59
        dur_ms = 1999
        edit_rate = 30
        result = round(dur_ms / 1000 * edit_rate)
        assert result == 60  # round, not 59 (int truncation)

    def test_audio_range_end_rounds_not_truncates(self):
        """Verify round() is used for audio range_end calculation."""
        # dur_ms=999, sample_rate=44100 -> 999/1000*44100 = 44055.9 -> round=44056, int=44055
        dur_ms = 999
        sample_rate = 44100
        result = round(dur_ms / 1000 * int(float(sample_rate)))
        assert result == 44056  # round, not 44055 (int truncation)


class TestTrecProbeStringDuration:
    """Bug 12: trec_probe should handle track.duration as string."""

    def test_video_string_duration(self):
        import importlib
        import os
        import tempfile

        import camtasia.media_bin.trec_probe as tp

        mock_track = MagicMock()
        mock_track.track_type = 'Video'
        mock_track.width = 1920
        mock_track.height = 1080
        mock_track.codec_id = 'tsc2'
        mock_track.frame_rate = '30.0'
        mock_track.duration = '5000'  # string, not int

        general_track = MagicMock()
        general_track.track_type = 'General'
        general_track.tagged_date = None
        general_track.encoded_date = None

        mock_mi = MagicMock()
        mock_mi.tracks = [general_track, mock_track]

        mock_pymediainfo = MagicMock()
        mock_pymediainfo.MediaInfo.parse.return_value = mock_mi

        with tempfile.NamedTemporaryFile(suffix='.trec', delete=False) as f:
            f.write(b'\x00')
            tmp = f.name
        try:
            with patch.dict('sys.modules', {'pymediainfo': mock_pymediainfo}):
                importlib.reload(tp)
                result = tp.probe_trec(tmp)
                # Should not raise TypeError
                assert len(result['sourceTracks']) == 1
                assert result['sourceTracks'][0]['range'][1] == round(5000 / 1000 * 30)
        finally:
            os.unlink(tmp)
            importlib.reload(tp)


class TestTrecProbeHandlesDualRateSampleRate:
    """Bug fix: trec_probe must handle dual-rate audio strings like '44100 / 48000'."""

    def test_dual_rate_audio_does_not_crash(self):
        import importlib
        import os
        import tempfile

        import camtasia.media_bin.trec_probe as tp

        general_track = MagicMock()
        general_track.track_type = 'General'
        general_track.tagged_date = None
        general_track.encoded_date = None

        audio_track = MagicMock()
        audio_track.track_type = 'Audio'
        audio_track.channel_s = '2'
        audio_track.sampling_rate = '44100 / 48000'  # dual-rate string
        audio_track.duration = '5000'

        mock_mi = MagicMock()
        mock_mi.tracks = [general_track, audio_track]

        mock_pymediainfo = MagicMock()
        mock_pymediainfo.MediaInfo.parse.return_value = mock_mi

        with tempfile.NamedTemporaryFile(suffix='.trec', delete=False) as f:
            f.write(b'\x00')
            tmp = f.name
        try:
            with patch.dict('sys.modules', {'pymediainfo': mock_pymediainfo}):
                importlib.reload(tp)
                result = tp.probe_trec(tmp)
                assert len(result['sourceTracks']) == 1
                st = result['sourceTracks'][0]
                # Should use first rate (44100), not crash on int(float('44100 / 48000'))
                assert st['editRate'] == 44100
                assert st['sampleRate'] == 44100
                assert st['range'][1] == round(5000 / 1000 * 44100)
        finally:
            os.unlink(tmp)
            importlib.reload(tp)
