"""REV-api_consistency-003: add_gradient_background uses track_index: int
while every other Project.add_* method uses track_name: str.

This forces callers to know the track index (fragile, order-dependent)
instead of using the name-based API used everywhere else.
"""
# Conceptual repro — demonstrates the inconsistency:
#
# All other add_* methods on Project:
#   add_title_card(text, ..., track_name='Titles')
#   add_background_music(audio_path, ..., track_name='Background Music')
#   add_watermark(image_path, ..., track_name='Watermark')
#   add_image_sequence(paths, track_name='Images', ...)
#   add_voiceover_sequence_v2(paths, track_name='Voiceover', ...)
#   add_subtitle_track(entries, track_name='Subtitles', ...)
#   add_section_divider(text, ..., track_name='Section Dividers')
#   add_end_card(text, ..., track_name='End Card')
#   add_four_corner_gradient(path, ..., track_name='Background')
#
# But add_gradient_background uses:
#   add_gradient_background(duration, ..., track_index=1)
#
# This is the ONLY Project.add_* method that takes a track_index.
# If tracks are reordered, the index silently points to the wrong track.
