Clips
=====

Every media item on the timeline is a clip.
:class:`~camtasia.timeline.clips.base.BaseClip` defines the common interface
shared by all clip types: ``start``, ``duration``, ``effects``, ``opacity``,
``clip_type``, and convenience methods such as
:meth:`~camtasia.timeline.clips.base.BaseClip.add_drop_shadow` and
:meth:`~camtasia.timeline.clips.base.BaseClip.add_glow`.  Concrete subclasses
map to the ``_type`` field in the project JSON.

.. list-table:: Clip types
   :header-rows: 1
   :widths: 25 75

   * - Class
     - Description
   * - :class:`~camtasia.timeline.clips.audio.AMFile`
     - Audio media file
   * - :class:`~camtasia.timeline.clips.video.VMFile`
     - Video media file
   * - :class:`~camtasia.timeline.clips.image.IMFile`
     - Image media file
   * - :class:`~camtasia.timeline.clips.screen_recording.ScreenVMFile`
     - Screen recording (video)
   * - :class:`~camtasia.timeline.clips.screen_recording.ScreenIMFile`
     - Screen recording (image)
   * - :class:`~camtasia.timeline.clips.stitched.StitchedMedia`
     - Stitched (concatenated) media
   * - :class:`~camtasia.timeline.clips.group.Group`
     - Compound clip with internal tracks
   * - :class:`~camtasia.timeline.clips.callout.Callout`
     - Text overlay / annotation
   * - :class:`~camtasia.timeline.clips.unified.UnifiedMedia`
     - Unified audio+video container
   * - :class:`~camtasia.timeline.clips.placeholder.PlaceholderMedia`
     - Placeholder for missing media

The :func:`~camtasia.timeline.clips.clip_from_dict` factory inspects the
``_type`` key and returns the appropriate subclass (falling back to
``BaseClip`` for unrecognised types).

.. rubric:: Example — find and modify clips by type

.. code-block:: python

   from camtasia import load_project
   from camtasia.timeline.clips import IMFile

   project = load_project("demo.cmproj")

   # Find all image clips across all tracks
   for track in project.timeline.tracks:
       for clip in track.clips:
           if isinstance(clip, IMFile):
               print(f"Image clip on track {track.index}, "
                     f"start={clip.start}, duration={clip.duration}")
               clip.add_drop_shadow(blur=8, opacity=0.4)

   project.save()

.. seealso::

   :doc:`/guides/cookbook`
      Recipes for adding, moving, and transforming clips.

.. automodule:: camtasia.timeline.clips.base
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.audio
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.video
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.image
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.screen_recording
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.stitched
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.group
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.callout
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.placeholder
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.clips.unified
   :members:
   :undoc-members:
   :show-inheritance:
