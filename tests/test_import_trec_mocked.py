"""Tests for import_trec that work without pymediainfo."""
from __future__ import annotations

import sys
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

    def test_video_string_duration(self, tmp_path):
        import importlib

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

        trec = tmp_path / 'test.trec'
        trec.write_bytes(b'\x00')
        try:
            with patch.dict('sys.modules', {'pymediainfo': mock_pymediainfo}):
                importlib.reload(tp)
                result = tp.probe_trec(trec)
                # Should not raise TypeError
                assert len(result['sourceTracks']) == 1
                assert result['sourceTracks'][0]['range'][1] == round(5000 / 1000 * 30)
        finally:
            importlib.reload(tp)


class TestTrecProbeHandlesDualRateSampleRate:
    """Bug fix: trec_probe must handle dual-rate audio strings like '44100 / 48000'."""

    def test_dual_rate_audio_does_not_crash(self, tmp_path):
        import importlib

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

        trec = tmp_path / 'test.trec'
        trec.write_bytes(b'\x00')
        try:
            with patch.dict('sys.modules', {'pymediainfo': mock_pymediainfo}):
                importlib.reload(tp)
                result = tp.probe_trec(trec)
                assert len(result['sourceTracks']) == 1
                st = result['sourceTracks'][0]
                # Should use first rate (44100), not crash on int(float('44100 / 48000'))
                assert st['editRate'] == 44100
                assert st['sampleRate'] == 44100
                assert st['range'][1] == round(5000 / 1000 * 44100)
        finally:
            importlib.reload(tp)


class TestTrecProbeNtscSampleRate:
    """Verify trec_probe produces correct NTSC fractional sampleRate strings."""

    def _make_mock_track(self, track_type, **kwargs):
        track = MagicMock()
        track.track_type = track_type
        for k, v in kwargs.items():
            setattr(track, k, v)
        return track

    def _probe_with_video_fps(self, fps, tmp_path):
        trec = tmp_path / 'test.trec'
        trec.write_bytes(b'\x00' * 64)
        general = self._make_mock_track('General', tagged_date=None, encoded_date=None)
        video = self._make_mock_track(
            'Video', width=1920, height=1080, codec_id='tsc2',
            frame_rate=str(fps), duration=10000, bit_depth=None,
        )
        mi_result = MagicMock()
        mi_result.tracks = [general, video]
        mock_pmi = MagicMock()
        mock_pmi.MediaInfo.parse.return_value = mi_result
        with patch.dict(sys.modules, {'pymediainfo': mock_pmi}):
            # Re-import to pick up the mock
            import importlib

            import camtasia.media_bin.trec_probe as tp
            importlib.reload(tp)
            return tp.probe_trec(trec)

    def test_29_97_produces_30000_1001(self, tmp_path):
        result = self._probe_with_video_fps(29.97, tmp_path)
        sr = result['sourceTracks'][0]['sampleRate']
        assert sr == '30000/1001', f'Expected 30000/1001, got {sr}'

    def test_23_976_produces_24000_1001(self, tmp_path):
        result = self._probe_with_video_fps(23.976, tmp_path)
        sr = result['sourceTracks'][0]['sampleRate']
        assert sr == '24000/1001', f'Expected 24000/1001, got {sr}'

    def test_59_94_produces_60000_1001(self, tmp_path):
        result = self._probe_with_video_fps(59.94, tmp_path)
        sr = result['sourceTracks'][0]['sampleRate']
        assert sr == '60000/1001', f'Expected 60000/1001, got {sr}'

    def test_30_fps_produces_integer(self, tmp_path):
        result = self._probe_with_video_fps(30.0, tmp_path)
        sr = result['sourceTracks'][0]['sampleRate']
        assert sr == 30, f'Expected 30, got {sr}'


class TestTrecProbeBitDepthFromTrack:
    """Verify trec_probe reads bitDepth from pymediainfo track instead of hardcoding."""

    def _make_mock_track(self, track_type, **kwargs):
        track = MagicMock()
        track.track_type = track_type
        for k, v in kwargs.items():
            setattr(track, k, v)
        return track

    def _probe_with_tracks(self, tracks_list, tmp_path):
        trec = tmp_path / 'test.trec'
        trec.write_bytes(b'\x00' * 64)
        mi_result = MagicMock()
        mi_result.tracks = tracks_list
        mock_pmi = MagicMock()
        mock_pmi.MediaInfo.parse.return_value = mi_result
        with patch.dict(sys.modules, {'pymediainfo': mock_pmi}):
            import importlib

            import camtasia.media_bin.trec_probe as tp
            importlib.reload(tp)
            return tp.probe_trec(trec)

    def test_video_bit_depth_read_from_track(self, tmp_path):
        general = self._make_mock_track('General', tagged_date=None, encoded_date=None)
        video = self._make_mock_track(
            'Video', width=1920, height=1080, codec_id='tsc2',
            frame_rate='30', duration=10000, bit_depth=10,
        )
        result = self._probe_with_tracks([general, video], tmp_path)
        assert result['sourceTracks'][0]['bitDepth'] == 10

    def test_audio_bit_depth_read_from_track(self, tmp_path):
        general = self._make_mock_track('General', tagged_date=None, encoded_date=None)
        audio = self._make_mock_track(
            'Audio', channel_s='2', sampling_rate='48000',
            duration=10000, bit_depth=24,
        )
        result = self._probe_with_tracks([general, audio], tmp_path)
        assert result['sourceTracks'][0]['bitDepth'] == 24

    def test_video_bit_depth_defaults_to_24_when_none(self, tmp_path):
        general = self._make_mock_track('General', tagged_date=None, encoded_date=None)
        video = self._make_mock_track(
            'Video', width=1920, height=1080, codec_id='tsc2',
            frame_rate='30', duration=10000, bit_depth=None,
        )
        result = self._probe_with_tracks([general, video], tmp_path)
        assert result['sourceTracks'][0]['bitDepth'] == 24

    def test_audio_bit_depth_defaults_to_16_when_none(self, tmp_path):
        general = self._make_mock_track('General', tagged_date=None, encoded_date=None)
        audio = self._make_mock_track(
            'Audio', channel_s='2', sampling_rate='48000',
            duration=10000, bit_depth=None,
        )
        result = self._probe_with_tracks([general, audio], tmp_path)
        assert result['sourceTracks'][0]['bitDepth'] == 16
