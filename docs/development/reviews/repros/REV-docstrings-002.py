"""Repro: remove_media docstring Args section omits the 'project' parameter.

The function signature is:
    def remove_media(project: Project, media_id: int, clear_tracks: bool = False)

But the Args section only documents media_id and clear_tracks.
"""
import inspect
from camtasia.operations.media_ops import remove_media

sig = inspect.signature(remove_media)
params = list(sig.parameters.keys())
print(f"Parameters: {params}")
# Output: Parameters: ['project', 'media_id', 'clear_tracks']

doc = remove_media.__doc__
assert "project" in params, "project not in signature"
assert "project:" not in doc and "project :" not in doc, "project IS documented (unexpected)"
print("CONFIRMED: 'project' parameter undocumented in Args section")
