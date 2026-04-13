from camtasia.timing import seconds_to_ticks


def test_statistics_empty_project(project):
    stats = project.statistics()
    assert stats['total_clips'] == 0
    assert stats['clips_by_type'] == {}
    assert stats['total_media'] == 0
    assert stats['media_by_type'] == {}
    assert stats['total_transitions'] == 0
    assert stats['total_markers'] == 0
    assert stats['duration_seconds'] == 0.0
    assert stats['empty_tracks'] == stats['total_tracks']


def test_statistics_with_clips(project):
    track = project.timeline.get_or_create_track('Test')
    track.add_clip('VMFile', None, 0, seconds_to_ticks(5.0))
    track.add_clip('AMFile', None, 0, seconds_to_ticks(3.0))
    track.add_clip('VMFile', None, seconds_to_ticks(5.0), seconds_to_ticks(2.0))

    stats = project.statistics()
    assert stats['total_clips'] == 3
    assert stats['clips_by_type'] == {'VMFile': 2, 'AMFile': 1}


def test_statistics_canvas(project):
    stats = project.statistics()
    assert stats['canvas'] == {'width': project.width, 'height': project.height}


def test_statistics_with_markers(project):
    project.timeline.add_marker('M1', 1.0)
    project.timeline.add_marker('M2', 5.0)

    stats = project.statistics()
    assert stats['total_markers'] == 2


class TestStatisticsWithMedia:
    def test_statistics_media_by_type(self, project):
        from pathlib import Path
        wav = Path(__file__).parent / 'fixtures' / 'empty.wav'
        project.import_media(wav)
        actual_stats = project.statistics()
        assert actual_stats['total_media'] >= 1
        assert 'Audio' in actual_stats['media_by_type']


def test_info_returns_comprehensive_dict(project):
    info = project.info()
    # Stats keys
    assert 'total_tracks' in info
    assert 'total_clips' in info
    assert 'canvas' in info
    # Structural / validation keys
    assert 'validation_errors' in info
    assert 'validation_warnings' in info
    assert 'structural_issues' in info
    # Project metadata keys
    assert 'has_screen_recording' in info
    assert 'title' in info
    assert 'author' in info
    assert 'frame_rate' in info
    assert 'sample_rate' in info


def test_info_includes_validation(project):
    info = project.info()
    assert isinstance(info['validation_errors'], list)
    assert isinstance(info['validation_warnings'], list)
    assert isinstance(info['structural_issues'], list)


def test_health_check_healthy(project):
    result = project.health_check()
    assert result['healthy'] is True
    assert result['errors'] == []
    assert result['warnings'] == []
    assert result['structural_issues'] == []
    assert isinstance(result['statistics'], dict)
    assert 'total_clips' in result['statistics']


def test_health_check_with_issues(project):
    from unittest.mock import patch, PropertyMock
    from camtasia.validation import ValidationIssue

    fake_issues = [
        ValidationIssue('error', 'bad clip'),
        ValidationIssue('warning', 'missing file'),
    ]
    with patch.object(project, 'validate', return_value=fake_issues):
        result = project.health_check()

    assert result['healthy'] is False
    assert result['errors'] == ['bad clip']
    assert result['warnings'] == ['missing file']
    assert isinstance(result['statistics'], dict)