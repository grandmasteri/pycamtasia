Media Bin
=========

The :class:`~camtasia.media_bin.MediaBin` is the project's **source bin** —
the registry of every media file (video, audio, image) that has been imported
into the ``.cmproj`` bundle.  Clips on the timeline reference media entries
by their integer ``id``; the bin itself stores the file path, native
dimensions, duration range, and source-track metadata for each entry.

Each entry is represented by a :class:`~camtasia.media_bin.Media` object.
Key properties include ``id`` (unique integer), ``source`` (relative path
inside the bundle), ``type`` (:class:`~camtasia.types.MediaType` — video,
audio, or image), ``range`` (start/stop tick tuple from the first source
track), and ``dimensions`` (width × height in pixels).

When you call :meth:`~camtasia.media_bin.MediaBin.import_media`, the file is
copied into the project's ``media/`` directory and a sourceBin entry is
created.  If `pymediainfo <https://pypi.org/project/pymediainfo/>`_ is
installed, dimensions, duration, and media type are detected automatically.
Without it you must pass ``media_type``, ``width``, ``height``, and
``duration`` explicitly.

Worked Example
--------------

.. code-block:: python

   from pathlib import Path
   import camtasia

   project = camtasia.load_project("demo.cmproj")
   media_bin = project.media_bin

   # Import a new video file (auto-detected with pymediainfo)
   media = project.import_media(Path("recording.mp4"))
   print(f"Imported: id={media.id}, type={media.type}, dims={media.dimensions}")

   # List all media entries and their types
   for entry in media_bin:
       print(f"  {entry.identity}: {entry.type}")

   # Place the imported media on a track
   track = project.timeline.get_or_create_track("Content")
   track.add_video(media.id, start_seconds=0, duration_seconds=10.0)

   # Remove media entries not referenced by any clip
   from camtasia.operations.cleanup import remove_orphaned_media
   removed = remove_orphaned_media(project)
   print(f"Removed {len(removed)} orphaned entries")

   project.save()

Library Bridge
--------------

:meth:`~camtasia.media_bin.MediaBin.add_to_library` bridges a media entry
into a :class:`~camtasia.library.Library` as a reusable asset.  This is the
connection point between the project-local source bin and the shared
``.libzip`` library format — useful when you want to promote imported media
into a library that can be shared across projects.

.. seealso::

   :doc:`library` for the Library / LibraryAsset API,
   :doc:`operations` for :func:`~camtasia.operations.cleanup.remove_orphaned_media`.

.. automodule:: camtasia.media_bin.media_bin
   :members:
   :undoc-members:
   :show-inheritance:
