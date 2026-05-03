Operations
==========

The ``operations`` package provides high-level functions that coordinate
changes across multiple clips, tracks, and media entries.  Each module
targets a single concern — pick the one that matches your goal:

.. list-table:: Operation Decision Matrix
   :header-rows: 1
   :widths: 50 30

   * - I want to …
     - Module
   * - Change playback speed
     - :mod:`~camtasia.operations.speed`
   * - Sync timeline to a transcript
     - :mod:`~camtasia.operations.sync`
   * - Tidy up (remove orphans, compact)
     - :mod:`~camtasia.operations.cleanup`
   * - Diff two projects
     - :mod:`~camtasia.operations.diff`
   * - Move / reorder / pack clips
     - :mod:`~camtasia.operations.layout`
   * - Apply a function to many clips at once
     - :mod:`~camtasia.operations.batch`
   * - Create projects from templates
     - :mod:`~camtasia.operations.template`
   * - Add / remove media programmatically
     - :mod:`~camtasia.operations.media_ops`
   * - Insert slide markers from a presentation
     - :mod:`~camtasia.operations.slide_markers`
   * - Generate or sync captions
     - :mod:`~camtasia.operations.captions`
   * - Stitch adjacent clips on a track
     - :mod:`~camtasia.operations.stitch`
   * - Sync Audiate edits back to timeline
     - :mod:`~camtasia.operations.sync`
   * - Merge tracks from another project
     - :mod:`~camtasia.operations.merge`
   * - Sync screen recording to audio
     - :mod:`~camtasia.operations.recording_sync`

Worked Examples
---------------

**Normalise audio speed to 1×** — useful after recording at a non-standard
rate:

.. code-block:: python

   import camtasia
   from camtasia.operations.speed import set_audio_speed

   project = camtasia.load_project("demo.cmproj")
   factor = set_audio_speed(project._data, target_speed=1.0)
   print(f"Applied stretch factor: {factor}")
   project.save()

**Pack a track end-to-end** — close all gaps between clips:

.. code-block:: python

   import camtasia
   from camtasia.operations.layout import pack_track

   project = camtasia.load_project("demo.cmproj")
   track = project.timeline.find_track_by_name("Content")
   pack_track(track, gap_seconds=0.5)
   project.save()

.. seealso::

   :doc:`/guides/speed-change` for a full speed-change walkthrough,
   :doc:`builders` for timeline assembly from scratch.

.. automodule:: camtasia.operations.speed
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.sync
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.template
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.diff
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.batch
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.layout
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.cleanup
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.merge
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.recording_sync
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.stitch
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.slide_markers
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.captions
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.operations.media_ops
   :members:
   :undoc-members:
   :show-inheritance:
