"""Tests for Project.normalize_audio, mute_track, and solo_track."""


class TestNormalizeAudio:
    def test_empty_project_returns_zero(self, project):
        assert project.normalize_audio() == 0

    def test_normalizes_audio_clips(self, project):
        track = project.timeline.get_or_create_track('Audio')
        # Add a source bin entry for the audio clip
        project._data.setdefault('sourceBin', []).append({
            'id': 900, 'src': './audio.wav', 'rect': [0, 0, 0, 0],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 44100], 'type': 1, 'editRate': 44100,
                              'trackRect': [0, 0, 0, 0], 'sampleRate': 44100,
                              'bitDepth': 16, 'numChannels': 2}],
        })
        clip = track.add_audio(900, start_seconds=0, duration_seconds=1.0)
        clip.gain = 0.5
        count = project.normalize_audio(target_gain=0.8)
        assert count == 1
        assert clip.gain == 0.8

    def test_default_target_gain(self, project):
        track = project.timeline.get_or_create_track('Audio')
        project._data.setdefault('sourceBin', []).append({
            'id': 901, 'src': './audio2.wav', 'rect': [0, 0, 0, 0],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 44100], 'type': 1, 'editRate': 44100,
                              'trackRect': [0, 0, 0, 0], 'sampleRate': 44100,
                              'bitDepth': 16, 'numChannels': 2}],
        })
        clip = track.add_audio(901, start_seconds=0, duration_seconds=1.0)
        clip.gain = 0.3
        project.normalize_audio()
        assert clip.gain == 1.0

    def test_skips_non_audio_clips(self, project):
        track = project.timeline.get_or_create_track('Video')
        project._data.setdefault('sourceBin', []).append({
            'id': 902, 'src': './video.mp4', 'rect': [0, 0, 1920, 1080],
            'lastMod': '20260101T000000',
            'sourceTracks': [{'range': [0, 900], 'type': 0, 'editRate': 30,
                              'trackRect': [0, 0, 1920, 1080], 'sampleRate': 30,
                              'bitDepth': 32, 'numChannels': 0}],
        })
        track.add_video(902, start_seconds=0, duration_seconds=1.0)
        # VMFile clips are not audio, so count should be 0
        count = project.normalize_audio()
        assert count == 0


class TestMuteTrack:
    def test_mute_existing_track(self, project):
        project.timeline.get_or_create_track('Narration')
        assert project.mute_track('Narration') is True
        track = project.timeline.find_track_by_name('Narration')
        assert track.audio_muted is True

    def test_mute_nonexistent_track(self, project):
        assert project.mute_track('NoSuchTrack') is False

    def test_mute_is_idempotent(self, project):
        project.timeline.get_or_create_track('Music')
        project.mute_track('Music')
        project.mute_track('Music')
        track = project.timeline.find_track_by_name('Music')
        assert track.audio_muted is True


class TestSoloTrack:
    def test_solo_existing_track(self, project):
        project.timeline.get_or_create_track('Track A')
        project.timeline.get_or_create_track('Track B')
        project.timeline.get_or_create_track('Track C')
        assert project.solo_track('Track B') is True
        for track in project.timeline.tracks:
            if track.name == 'Track B':
                assert track.audio_muted is False
            else:
                assert track.audio_muted is True

    def test_solo_nonexistent_track(self, project):
        assert project.solo_track('Ghost') is False

    def test_solo_unmutes_target_mutes_others(self, project):
        project.timeline.get_or_create_track('Solo')
        project.timeline.get_or_create_track('Other')
        # Pre-mute the target
        project.mute_track('Solo')
        target = project.timeline.find_track_by_name('Solo')
        assert target.audio_muted is True
        # Solo should unmute it
        project.solo_track('Solo')
        assert target.audio_muted is False
        other = project.timeline.find_track_by_name('Other')
        assert other.audio_muted is True
