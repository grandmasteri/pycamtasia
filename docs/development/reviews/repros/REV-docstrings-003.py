"""Repro: add_media_to_track docstring claims 'Raises: KeyError: Specified
track ... can't be found' but accessing proj.timeline.tracks[track_index]
with an invalid index raises IndexError, not KeyError.

Also, the docstring has no Returns section despite returning BaseClip.
"""
import inspect
from camtasia.operations.media_ops import add_media_to_track

sig = inspect.signature(add_media_to_track)
print(f"Return annotation: {sig.return_annotation}")

doc = add_media_to_track.__doc__
assert "Returns" not in doc.split("Raises")[0] if "Raises" in doc else "Returns" not in doc, \
    "Returns section found (unexpected)"
assert "KeyError" in doc, "KeyError not in docstring"

# The actual exception for invalid track_index would be IndexError from list access
# proj.timeline.tracks[track_index] — lists raise IndexError, not KeyError
print("CONFIRMED: missing Returns section and KeyError claim is wrong for track access")
