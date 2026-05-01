Timeline
========

The :class:`~camtasia.timeline.timeline.Timeline` is the container for all
temporal content in a Camtasia project.  It owns an ordered list of
:class:`~camtasia.timeline.track.Track` objects (accessed via
:attr:`~camtasia.timeline.timeline.Timeline.tracks`), a
:class:`~camtasia.timeline.markers.MarkerList` of timeline-level markers, and
caption styling attributes.  Each track in turn holds clips, per-track
transitions (:class:`~camtasia.timeline.transitions.TransitionList`), and
per-track markers.  The timeline is always accessed through
:attr:`Project.timeline <camtasia.project.Project.timeline>` — it is never
constructed directly.

Tracks are stacked in visual order (track 0 is the bottom layer).  Iterating
``timeline.tracks`` yields :class:`~camtasia.timeline.track.Track` instances
from which you can read and modify clips, transitions, and markers.  The
:meth:`~camtasia.timeline.timeline.Timeline.add_marker` convenience method
creates a timeline-level marker at a given time in seconds.

.. rubric:: Example — inspect tracks and add a marker

.. code-block:: python

   from camtasia import load_project

   project = load_project("demo.cmproj")
   timeline = project.timeline

   # Print clip count per track
   for track in timeline.tracks:
       clips = list(track.clips)
       print(f"Track {track.index}: {len(clips)} clip(s)")

   # Add a timeline-level marker at 30 seconds
   marker = timeline.add_marker("Mid-point", 30.0)
   print(f"Added marker: {marker.name}")

   project.save()

.. seealso::

   :doc:`/guides/cookbook`
      Recipes for working with tracks, clips, and markers.

.. automodule:: camtasia.timeline.timeline
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.timeline.track
   :members:
   :undoc-members:
   :show-inheritance:
