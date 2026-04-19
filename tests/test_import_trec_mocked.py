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
