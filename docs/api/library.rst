Library
=======

Custom asset collections that can be saved, shared, and reused across
projects.  The :mod:`~camtasia.library.library` module manages in-memory
library objects while :mod:`~camtasia.library.libzip` handles ``.libzip``
import/export.  Library assets — callouts, intros, lower thirds — plug into
the same effect system used by the timeline, so they can be applied to clips
just like built-in effects.

.. seealso::

   :doc:`effects`
      The effect system that library assets integrate with.

   :doc:`annotations`
      Callout and shape definitions that can be stored as library assets.

.. automodule:: camtasia.library.library
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.library.libzip
   :members:
   :undoc-members:
   :show-inheritance:
