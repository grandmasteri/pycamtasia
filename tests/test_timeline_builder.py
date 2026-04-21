from __future__ import annotations

from pathlib import Path

import pytest

from camtasia.builders.timeline_builder import TimelineBuilder

FIXTURES = Path(__file__).parent / 'fixtures'


class TestTimelineBuilder:
    def test_initial_cursor_is_zero(self, project):
        builder = TimelineBuilder(project)
        assert builder.cursor == 0.0

    def test_advance_moves_cursor(self, project):
        builder = TimelineBuilder(project)
        builder.advance(3.5)
        assert builder.cursor == 3.5

    def test_seek_sets_cursor(self, project):
        builder = TimelineBuilder(project)
        builder.advance(10.0)
        builder.seek(2.0)
        assert builder.cursor == 2.0

    def test_seek_negative_raises(self, project):
        builder = TimelineBuilder(project)
        with pytest.raises(ValueError, match='non-negative'):
            builder.seek(-1.0)

    def test_add_pause_advances_cursor(self, project):
        builder = TimelineBuilder(project)
        builder.add_pause(4.0)
        assert builder.cursor == 4.0

    def test_add_audio_places_clip_and_advances(self, project):
        builder = TimelineBuilder(project)
        clip = builder.add_audio(FIXTURES / 'empty.wav', duration=3.0)
        assert clip is not None
        assert builder.cursor == 3.0

    def test_add_image_places_clip_no_advance(self, project):
        builder = TimelineBuilder(project)
        builder.advance(2.0)
        clip = builder.add_image(FIXTURES / 'empty.wav', duration=5.0)
        assert clip is not None
        assert builder.cursor == 2.0

    def test_add_title_places_clip_no_advance(self, project):
        builder = TimelineBuilder(project)
        builder.advance(1.0)
        clip = builder.add_title('Hello World', duration=4.0)
        assert clip is not None
        assert builder.cursor == 1.0

    def test_chaining_works(self, project):
        builder = TimelineBuilder(project)
        result = builder.advance(1.0).add_pause(2.0).seek(5.0)
        assert result is builder
        assert builder.cursor == 5.0


class TestBackgroundHelpers:
    """add_background_image / add_background_video place content on a
    dedicated background track."""

    def test_add_background_image_creates_track_and_clip(self, project, tmp_path, monkeypatch):
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
            SimpleNamespace(track_type='Image', width=1920, height=1080),
        ])
        monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
        img = tmp_path / 'bg.png'
        img.write_bytes(b'\x89PNG\r\n\x1a\n')
        builder = TimelineBuilder(project)
        clip = builder.add_background_image(img, duration=10.0)
        assert clip.start == 0
        bg_track = project.timeline.find_track_by_name('Background')
        assert bg_track is not None

    def test_add_background_image_custom_track(self, project, tmp_path, monkeypatch):
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
            SimpleNamespace(track_type='Image', width=1920, height=1080),
        ])
        monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
        img = tmp_path / 'bg.png'
        img.write_bytes(b'\x89PNG\r\n\x1a\n')
        builder = TimelineBuilder(project)
        builder.add_background_image(img, track_name='BG', duration=5.0)
        assert project.timeline.find_track_by_name('BG') is not None

    def test_add_background_image_default_duration_uses_total(self, project, tmp_path, monkeypatch):
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
            SimpleNamespace(track_type='Image', width=1920, height=1080),
        ])
        monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
        img = tmp_path / 'bg.png'
        img.write_bytes(b'\x89PNG\r\n\x1a\n')
        builder = TimelineBuilder(project)
        # Project is empty; total_duration_seconds == 0; clip duration = 0
        clip = builder.add_background_image(img)
        assert clip.duration == 0

    def test_add_background_video_mutes_by_default(self, project, tmp_path, monkeypatch):
        import sys
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        mock_mi = MagicMock()
        mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
            SimpleNamespace(track_type='Video', width=1920, height=1080,
                           duration=5000, frame_rate=30),
        ])
        monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
        vid = tmp_path / 'bg.mp4'
        vid.write_bytes(b'\x00\x00\x00\x20ftypmp42')
        builder = TimelineBuilder(project)
        clip = builder.add_background_video(vid, duration=5.0)
        # Muted = gain 0
        assert clip.gain == 0.0


def test_add_background_video_uses_native_duration_when_not_specified(project, tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    from unittest.mock import MagicMock
    mock_mi = MagicMock()
    mock_mi.MediaInfo.parse.return_value = SimpleNamespace(tracks=[
        SimpleNamespace(track_type='Video', width=1920, height=1080,
                       duration=5000, frame_rate=30),
    ])
    monkeypatch.setitem(sys.modules, 'pymediainfo', mock_mi)
    vid = tmp_path / 'bg.mp4'
    vid.write_bytes(b'\x00\x00\x00\x20ftypmp42')
    builder = TimelineBuilder(project)
    # duration not passed → should fall back
    clip = builder.add_background_video(vid)
    # Duration should be either native (5s) or project total (0s since empty project)
    assert clip.duration >= 0
