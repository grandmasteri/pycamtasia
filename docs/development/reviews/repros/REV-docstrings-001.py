"""Repro: remove_media docstring says 'By default, this will also remove
references to the removed media from tracks' but clear_tracks defaults to
False, meaning it raises ValueError if references exist.

The docstring contradicts the implementation.
"""
# Inspect the source directly:
import inspect
from camtasia.operations.media_ops import remove_media

sig = inspect.signature(remove_media)
print(f"clear_tracks default: {sig.parameters['clear_tracks'].default}")
# Output: clear_tracks default: False

doc = remove_media.__doc__
assert "By default, this will also remove references" in doc, "Docstring text not found"
assert sig.parameters['clear_tracks'].default is False, "Default is not False"

# Docstring claims default behavior removes references, but code raises
# ValueError when clear_tracks=False and references exist.
print("CONFIRMED: docstring contradicts implementation")
