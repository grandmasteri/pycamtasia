Effects
=======

Effects modify the visual or audible output of a clip.  The
:class:`~camtasia.effects.base.Effect` base class wraps a raw effect dict and
exposes :attr:`~camtasia.effects.base.Effect.name`,
:attr:`~camtasia.effects.base.Effect.parameters`, and helpers like
:meth:`~camtasia.effects.base.Effect.get_parameter` /
:meth:`~camtasia.effects.base.Effect.set_parameter`.  Concrete subclasses are
organised into five categories: **visual** effects
(:class:`~camtasia.effects.visual.DropShadow`,
:class:`~camtasia.effects.visual.Glow`, :class:`~camtasia.effects.visual.Mask`,
etc.), **audio** effects
(:class:`~camtasia.effects.audio.NoiseRemoval`,
:class:`~camtasia.effects.audio.Equalizer`), **source** effects
(:class:`~camtasia.effects.source.SourceEffect` — shader-level parameters like
gradients and colours), **cursor** effects
(:class:`~camtasia.effects.cursor.CursorShadow`,
:class:`~camtasia.effects.cursor.CursorSmoothing`, click visualisations), and
**behavior** effects
(:class:`~camtasia.effects.behaviors.GenericBehaviorEffect` — text animation
presets).

Each concrete effect class is registered with the
:func:`~camtasia.effects.base.register_effect` decorator, which maps an
``effectName`` string to a Python class.  The
:func:`~camtasia.effects.base.effect_from_dict` factory uses this registry to
return the correct subclass when deserialising project JSON.  Effect parameters
follow the plain scalar format — a flat dict with ``defaultValue``, ``type``,
and ``interp`` keys.

.. rubric:: Example — apply DropShadow and Glow to a clip

.. code-block:: python

   from camtasia import load_project

   project = load_project("demo.cmproj")

   # Grab the first clip on track 0
   track = list(project.timeline.tracks)[0]
   clip = list(track.clips)[0]

   # Add visual effects using L2 convenience methods
   clip.add_drop_shadow(blur=10, opacity=0.6)
   clip.add_glow(radius=20.0, intensity=0.5)

   print(f"Effects on clip: {clip.effect_names}")

   project.save()

.. seealso::

   :doc:`/guides/cookbook`
      Recipes for applying and configuring effects.

.. automodule:: camtasia.effects.base
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.effects.visual
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.effects.cursor
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.effects.source
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.effects.audio
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.effects.audio_visualizer
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.effects.behaviors
   :members:
   :undoc-members:
   :show-inheritance:
