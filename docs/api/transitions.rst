Transitions
===========

Transition effects applied between adjacent clips on the same track.  Add a
transition with :meth:`~camtasia.timeline.track.Track.add_transition`, passing
the transition name (see :class:`~camtasia.types.TransitionType`), the left and
right clip IDs, and a duration in ticks.  Transitions are automatically
cascade-deleted when either neighbouring clip is removed.

.. seealso::

   :doc:`/guides/cookbook`
      Recipes that demonstrate adding transitions between clips.

   :doc:`clips`
      Clip types that transitions connect.

.. automodule:: camtasia.timeline.transitions
   :members:
   :undoc-members:
   :show-inheritance:
