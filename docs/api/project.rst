Project
=======

The :class:`~camtasia.project.Project` class is the top-level entry point for
working with Camtasia ``.cmproj`` bundles.  A project owns a
:class:`~camtasia.timeline.timeline.Timeline`, a
:class:`~camtasia.media_bin.media_bin.MediaBin`, and an
:class:`~camtasia.authoring_client.AuthoringClient` (export settings).  Three
convenience functions cover the common workflows: :func:`~camtasia.project.load_project`
opens an existing bundle, :func:`~camtasia.project.new_project` copies the
built-in template to a new path, and :func:`~camtasia.project.use_project` is a
context manager that loads a project and saves it automatically on normal exit.

Calling :meth:`~camtasia.project.Project.save` writes the current in-memory
state back to the ``.tscproj`` JSON file inside the bundle, using Camtasia's
``NSJSONSerialization``-compatible formatting.  For reversible edits, wrap
mutations in the :meth:`~camtasia.project.Project.track_changes` context
manager — each block is recorded as a single undo step that can be reverted
with :meth:`~camtasia.project.Project.undo`.

.. rubric:: Example — load, edit, save

.. code-block:: python

   from camtasia import load_project

   # Open an existing project
   project = load_project("demo.cmproj")

   # Print basic info
   timeline = project.timeline
   print(f"Tracks: {timeline.track_count}")

   # Add a marker at the 5-second mark
   timeline.add_marker("Chapter 1", 5.0)

   # Use track_changes for undo support
   with project.track_changes("add marker"):
       timeline.add_marker("Chapter 2", 10.0)

   # Save to disk
   project.save()

.. seealso::

   :doc:`/guides/cookbook`
      Recipes for common project manipulation tasks.

   :doc:`/guides/undo-redo`
      How the undo/redo system works with ``track_changes()``.

.. automodule:: camtasia.project
   :members:
   :undoc-members:
   :show-inheritance:
