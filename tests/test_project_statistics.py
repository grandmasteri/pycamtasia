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
