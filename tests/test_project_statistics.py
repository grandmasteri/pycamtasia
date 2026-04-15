from camtasia.timing import seconds_to_ticks


class TestStatistics:
    def test_empty_project_keys(self, project):
        stats = project.statistics()
        expected_keys = {
            'title', 'duration_seconds', 'duration_formatted', 'resolution',
            'track_count', 'clip_count', 'group_count', 'effect_count',
            'transition_count', 'media_count', 'empty_tracks', 'clip_density',
        }
        assert set(stats.keys()) == expected_keys

    def test_empty_project_values(self, project):
        stats = project.statistics()
        assert stats['clip_count'] == 0
        assert stats['group_count'] == 0
        assert stats['effect_count'] == 0
        assert stats['transition_count'] == 0
        assert stats['media_count'] == 0
        assert stats['duration_seconds'] == 0.0
        assert stats['empty_tracks'] == stats['track_count']
        assert stats['clip_density'] == 0.0

    def test_resolution_format(self, project):
        stats = project.statistics()
        assert stats['resolution'] == f'{project.width}x{project.height}'

    def test_title(self, project):
        project.title = 'My Video'
        assert project.statistics()['title'] == 'My Video'

    def test_duration_formatted(self, project):
        stats = project.statistics()
        assert stats['duration_formatted'] == project.total_duration_formatted

    def test_with_clips(self, project):
        track = project.timeline.get_or_create_track('Test')
        track.add_clip('VMFile', None, 0, seconds_to_ticks(5.0))
        track.add_clip('AMFile', None, 0, seconds_to_ticks(3.0))
        stats = project.statistics()
        assert stats['clip_count'] == 2

    def test_effect_count(self, project):
        track = project.timeline.get_or_create_track('FX')
        clip = track.add_clip('VMFile', None, 0, seconds_to_ticks(5.0))
        clip._data['effects'] = [{'effectName': 'blur'}, {'effectName': 'glow'}]
        stats = project.statistics()
        assert stats['effect_count'] == 2

    def test_media_count(self, project):
        from pathlib import Path
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        project.import_media(wav)
        assert project.statistics()['media_count'] >= 1

    def test_empty_tracks_count(self, project):
        project.timeline.get_or_create_track('Empty1')
        project.timeline.get_or_create_track('Empty2')
        stats = project.statistics()
        assert stats['empty_tracks'] >= 2


class TestToMarkdownReport:
    def test_returns_string(self, project):
        report = project.to_markdown_report()
        assert isinstance(report, str)

    def test_contains_heading(self, project):
        project.title = 'Demo'
        report = project.to_markdown_report()
        assert '# Project Report: Demo' in report

    def test_untitled_fallback(self, project):
        project.title = ''
        report = project.to_markdown_report()
        assert '(untitled)' in report

    def test_contains_all_metrics(self, project):
        report = project.to_markdown_report()
        for label in ['Duration', 'Resolution', 'Tracks', 'Clips', 'Groups',
                       'Effects', 'Transitions', 'Media files', 'Empty tracks',
                       'Clip density']:
            assert label in report, f'Missing metric: {label}'

    def test_markdown_table_structure(self, project):
        report = project.to_markdown_report()
        assert '| Metric | Value |' in report
        assert '|--------|-------|' in report

    def test_values_match_statistics(self, project):
        track = project.timeline.get_or_create_track('V')
        track.add_clip('VMFile', None, 0, seconds_to_ticks(10.0))
        stats = project.statistics()
        report = project.to_markdown_report()
        assert stats['resolution'] in report
        assert str(stats['clip_count']) in report

    def test_clip_density_formatted(self, project):
        report = project.to_markdown_report()
        # clip_density should appear as a float with 2 decimal places
        assert '0.00' in report


class TestInfoUsesNewStatistics:
    """Ensure info() returns the comprehensive dict."""

    def test_info_has_clip_count(self, project):
        info = project.info()
        assert 'clip_count' in info

    def test_info_has_resolution(self, project):
        info = project.info()
        assert 'resolution' in info

    def test_info_has_file_path(self, project):
        info = project.info()
        assert 'file_path' in info
        assert isinstance(info['file_path'], str)

    def test_info_has_version(self, project):
        info = project.info()
        assert 'version' in info

    def test_info_has_frame_rate(self, project):
        info = project.info()
        assert 'frame_rate' in info
        assert info['frame_rate'] == project.frame_rate

    def test_info_has_sample_rate(self, project):
        info = project.info()
        assert 'sample_rate' in info
        assert info['sample_rate'] == project.sample_rate

    def test_info_has_authoring_client(self, project):
        info = project.info()
        assert 'authoring_client' in info

    def test_info_has_has_screen_recording(self, project):
        info = project.info()
        assert 'has_screen_recording' in info
        assert info['has_screen_recording'] is False

    def test_info_has_validation_issues(self, project):
        info = project.info()
        assert 'validation_issues' in info
        assert isinstance(info['validation_issues'], int)


class TestHealthCheckUsesNewStatistics:
    """Ensure health_check() still works with the new statistics shape."""

    def test_health_check_statistics_key(self, project):
        result = project.health_check()
        assert 'clip_count' in result['statistics']
        assert 'resolution' in result['statistics']
