from __future__ import annotations

from pathlib import Path

from camtasia.builders.video_production import VideoProductionBuilder

FIXTURES = Path(__file__).parent / 'fixtures'


class TestVideoProductionBuilder:
    def test_empty_build(self, project):
        builder = VideoProductionBuilder(project)
        result = builder.build()
        assert result['sections'] == 0
        assert result['has_intro'] is False
        assert result['has_outro'] is False
        assert result['has_background_music'] is False
        assert result['has_watermark'] is False

    def test_add_intro(self, project):
        builder = VideoProductionBuilder(project)
        ret = builder.add_intro(title='Hello', subtitle='World', duration=3.0)
        assert ret is builder  # fluent
        result = builder.build()
        assert result['has_intro'] is True
        assert project.clip_count > 0

    def test_add_intro_no_subtitle(self, project):
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Solo Title', duration=2.0)
        result = builder.build()
        assert result['has_intro'] is True

    def test_add_section(self, project):
        builder = VideoProductionBuilder(project)
        ret = builder.add_section('Architecture')
        assert ret is builder  # fluent
        result = builder.build()
        assert result['sections'] == 1

    def test_add_section_with_images(self, project):
        # Use .wav as a stand-in for image (import_media detects by extension)
        # Create a dummy PNG for the test
        dummy_png = project.file_path / 'test.png'
        dummy_png.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        builder = VideoProductionBuilder(project)
        builder.add_section('Visuals', images=[dummy_png])
        result = builder.build()
        assert result['sections'] == 1

    def test_add_section_with_voiceover(self, project):
        builder = VideoProductionBuilder(project)
        wav = FIXTURES / 'empty.wav'
        builder.add_section('Narrated', voiceover=wav)
        result = builder.build()
        assert result['sections'] == 1
        # Voiceover should be imported into media bin
        assert project.media_count > 0

    def test_add_section_with_screen_recording(self, project):
        builder = VideoProductionBuilder(project)
        wav = FIXTURES / 'empty.wav'
        # Use .wav as stand-in since .trec requires pymediainfo
        builder.add_section('Demo', screen_recording=wav)
        result = builder.build()
        assert result['sections'] == 1
        # Screen recording should create a video clip, not audio
        screen_track = project.timeline.get_or_create_track('Screen Recording')
        clips = list(screen_track.clips)
        assert len(clips) >= 1
        assert clips[0]._data['_type'] == 'VMFile'

    def test_add_outro(self, project):
        builder = VideoProductionBuilder(project)
        ret = builder.add_outro(text='Goodbye', duration=4.0)
        assert ret is builder  # fluent
        result = builder.build()
        assert result['has_outro'] is True

    def test_add_background_music(self, project):
        # Need some content first so duration > 0
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Test', duration=5.0)
        ret = builder.add_background_music(FIXTURES / 'empty.wav', volume=0.2)
        assert ret is builder  # fluent
        result = builder.build()
        assert result['has_background_music'] is True

    def test_add_watermark(self, project):
        dummy_png = project.file_path / 'watermark.png'
        dummy_png.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Test', duration=5.0)
        ret = builder.add_watermark(dummy_png, opacity=0.5)
        assert ret is builder  # fluent
        result = builder.build()
        assert result['has_watermark'] is True

    def test_multiple_sections_ordered(self, project):
        builder = VideoProductionBuilder(project)
        builder.add_section('Part 1')
        builder.add_section('Part 2')
        builder.add_section('Part 3')
        result = builder.build()
        assert result['sections'] == 3

    def test_full_pipeline(self, project):
        dummy_png = project.file_path / 'logo.png'
        dummy_png.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        builder = VideoProductionBuilder(project)
        builder.add_intro(title='Full Demo', subtitle='v2.0', duration=3.0)
        builder.add_section('Intro Section')
        builder.add_section('Main Content', voiceover=FIXTURES / 'empty.wav')
        builder.add_outro(text='Thanks for watching!', duration=4.0)
        builder.add_background_music(FIXTURES / 'empty.wav', volume=0.25)
        builder.add_watermark(dummy_png, opacity=0.2)
        result = builder.build()
        assert result['sections'] == 2
        assert result['has_intro'] is True
        assert result['has_outro'] is True
        assert result['has_background_music'] is True
        assert result['has_watermark'] is True
        assert result['total_duration'] > 0

    def test_fluent_chaining(self, project):
        """All methods return self for chaining."""
        builder = VideoProductionBuilder(project)
        result = (
            builder
            .add_intro(title='Chain', duration=2.0)
            .add_section('S1')
            .add_outro(text='End')
            .build()
        )
        assert result['sections'] == 1
        assert result['has_intro'] is True
        assert result['has_outro'] is True

    def test_import_from_builders_package(self):
        from camtasia.builders import VideoProductionBuilder as VPB
        assert VPB is VideoProductionBuilder
