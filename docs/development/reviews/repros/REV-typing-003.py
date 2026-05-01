"""REV-typing-003: library/ and media_bin/ __init__.py missing __all__.

Under mypy --strict, re-exports without __all__ are not considered public.
This causes attr-defined errors in every module that imports from these
subpackages (project.py, extras.py, clips/group.py).

Repro: run `python -m mypy --strict src/camtasia/project.py`.
"""
# These imports trigger attr-defined errors under --strict:
from camtasia.library import Library, LibraryAsset, Libraries, import_libzip
from camtasia.media_bin import Media, MediaBin, MediaType
