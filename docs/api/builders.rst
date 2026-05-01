Builders
========

The ``builders`` package provides high-level constructors that assemble
timelines from common production patterns.  Choose the builder that matches
your workflow:

.. list-table:: Builder Selection Guide
   :header-rows: 1
   :widths: 50 30

   * - I want to …
     - Use
   * - Place clips sequentially with a cursor
     - :class:`~camtasia.builders.TimelineBuilder`
   * - Assemble voiceover + slides from a screenplay
     - :func:`~camtasia.builders.build_from_screenplay`
   * - Full production with intro / sections / outro
     - :class:`~camtasia.builders.VideoProductionBuilder`
   * - Add a device frame overlay to a clip
     - :func:`~camtasia.builders.add_device_frame`
   * - Add a dynamic / Lottie background
     - :func:`~camtasia.builders.add_dynamic_background`
   * - Import PowerPoint slides onto the timeline
     - :func:`~camtasia.builders.import_powerpoint`

Worked Examples
---------------

**TimelineBuilder** — cursor-based sequential assembly:

.. code-block:: python

   from camtasia.builders import TimelineBuilder

   project = camtasia.load_project("demo.cmproj")
   builder = TimelineBuilder(project)
   builder.add_audio("intro.wav")
   builder.add_pause(1.0)
   builder.add_image("slide1.png", duration=5.0)
   builder.add_audio("main.wav")
   project.save()

**ScreenplayBuilder** — voiceover-driven assembly from a parsed screenplay:

.. code-block:: python

   from camtasia.builders import build_from_screenplay
   from camtasia.screenplay import parse_screenplay

   project = camtasia.load_project("demo.cmproj")
   screenplay = parse_screenplay("script.md")
   result = build_from_screenplay(
       project, screenplay, audio_dir="vo/",
       emit_scene_markers=True,
   )
   print(f"Placed {result['clips_placed']} clips")
   project.save()

**VideoProductionBuilder** — fluent chain for full productions:

.. code-block:: python

   from camtasia.builders import VideoProductionBuilder

   project = camtasia.load_project("demo.cmproj")
   (VideoProductionBuilder(project)
       .add_intro(title="Welcome", duration=3.0)
       .add_section("Demo", voiceover="demo.wav")
       .add_outro(text="Thanks!")
       .add_background_music("bg.mp3", volume=0.3)
       .build())
   project.save()

.. seealso::

   :doc:`operations` for post-assembly operations like
   :func:`~camtasia.operations.layout.pack_track`,
   :doc:`/guides/getting-started` for an end-to-end tutorial.

.. automodule:: camtasia.builders.timeline_builder
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.builders.screenplay_builder
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.builders.device_frame
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.builders.device_frame_library
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.builders.tile_layout
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.builders.slide_import
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.builders.dynamic_background
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.builders.video_production
   :members:
   :undoc-members:
   :show-inheritance:
