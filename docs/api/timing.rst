Timing
======

Camtasia uses a tick-based internal clock running at 705,600,000 ticks per
second (``EDIT_RATE``).  The :mod:`camtasia.timing` module converts between
ticks and wall-clock seconds and provides :class:`~fractions.Fraction`-based
scalar helpers so that speed changes remain exact — no floating-point drift.
Use :func:`~camtasia.timing.speed_to_scalar` and
:func:`~camtasia.timing.scalar_to_speed` for all speed ↔ scalar conversions.

.. seealso::

   :doc:`/guides/speed-change`
      Applying speed changes while keeping visuals in sync.

   :doc:`/guides/type-safety`
      Why pycamtasia uses ``Fraction`` instead of ``float`` for timing math.

.. automodule:: camtasia.timing
   :members:
   :undoc-members:
   :show-inheritance:
