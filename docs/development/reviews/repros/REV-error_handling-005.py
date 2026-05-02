"""Repro: remove_media raises ValueError without identifying which references exist.

When clear_tracks=False and track references exist, the error message is:
  "Attempt to remove media from media-bin while references exist on tracks"

This doesn't say WHICH tracks or clips hold references, making it hard
for users to fix the issue.
"""
# Conceptual repro — requires a project with media on tracks.
# The error message at operations/media_ops.py:70 is:
#   raise ValueError("Attempt to remove media from media-bin while references exist on tracks")
#
# It should include: media_id, track names, and clip IDs that reference it.
print("Error message at operations/media_ops.py:70 lacks context:")
print('  raise ValueError("Attempt to remove media from media-bin while references exist on tracks")')
print("Should include: media_id, track name(s), clip ID(s)")
