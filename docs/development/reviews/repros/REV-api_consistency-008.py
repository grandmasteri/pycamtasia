"""REV-api_consistency-008: add_voiceover_sequence and add_voiceover_sequence_v2
coexist with different signatures and return types.

add_voiceover_sequence returns dict[str, dict] (mapping filename to info).
add_voiceover_sequence_v2 returns list[BaseClip].

The _v2 suffix is an anti-pattern — it signals an unfinished migration.
Both are public API and exported.
"""
# Conceptual repro:
#
# result1 = project.add_voiceover_sequence(
#     vo_files=['a.wav', 'b.wav'],
#     pauses={'a.wav': 0.5},
#     track_name='Audio',
# )
# type(result1)  # dict[str, dict]  — keys are filenames
# result1['a.wav']['clip']  # the clip object
# result1['a.wav']['start']  # start time
#
# result2 = project.add_voiceover_sequence_v2(
#     audio_file_paths=['a.wav', 'b.wav'],
#     track_name='Voiceover',     # different default!
#     start_seconds=0.0,
#     gap_seconds=0.0,
# )
# type(result2)  # list[BaseClip]  — just clips, no metadata
#
# Different parameter names:
#   vo_files vs audio_file_paths
#   pauses (dict) vs gap_seconds (float)
#   track_name='Audio' vs track_name='Voiceover'
#
# Different return types:
#   dict[str, dict] vs list[BaseClip]
