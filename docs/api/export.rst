Export
======

The ``export`` package converts project data into interchange formats for
use outside Camtasia — edit decision lists, subtitle files, chapter markers,
reports, and portable project bundles.

.. list-table:: Format Support Matrix
   :header-rows: 1
   :widths: 30 30 20

   * - Format
     - Function
     - Output
   * - EDL (Edit Decision List)
     - :func:`~camtasia.export.export_edl`
     - ``.edl``
   * - CSV clip listing
     - :func:`~camtasia.export.export_csv`
     - ``.csv``
   * - SRT (markers)
     - :func:`~camtasia.export.export_markers_as_srt`
     - ``.srt``
   * - SRT (captions)
     - :func:`~camtasia.export.export_captions_srt`
     - ``.srt``
   * - VTT (import only)
     - :func:`~camtasia.export.import_captions_vtt`
     - —
   * - JSON report
     - :func:`~camtasia.export.export_project_report`
     - ``.json`` / ``.md``
   * - TOC (SmartPlayer / XML / JSON)
     - :func:`~camtasia.export.export_toc`
     - varies
   * - Chapters (WebVTT / MP4 / YouTube)
     - :func:`~camtasia.export.export_chapters`
     - varies
   * - ``.campackage`` bundle
     - :func:`~camtasia.export.export_campackage`
     - ``.campackage``
   * - Audio metadata (CSV / JSON)
     - :func:`~camtasia.export.export_audio`
     - ``.csv`` / ``.json``
   * - Timeline JSON snapshot
     - :func:`~camtasia.export.export_timeline_json`
     - ``.json``

Worked Example
--------------

Export a project report, caption SRT, and chapter file in one pass:

.. code-block:: python

   from pathlib import Path
   import camtasia
   from camtasia.export import (
       export_captions_srt,
       export_chapters,
       export_project_report,
   )

   project = camtasia.load_project("demo.cmproj")
   out = Path("exports")
   out.mkdir(exist_ok=True)

   export_project_report(project, out / "report.md")
   export_captions_srt(project, out / "captions.srt")
   export_chapters(project, out / "chapters.vtt", format="webvtt")

.. seealso::

   :doc:`media_bin` for importing media,
   :doc:`operations` for :func:`~camtasia.operations.cleanup.remove_orphaned_media`.

.. automodule:: camtasia.export.edl
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.csv_export
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.srt
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.report
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.timeline_json
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.audio
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.captions
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.campackage
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.toc
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: camtasia.export.chapters
   :members:
   :undoc-members:
   :show-inheritance:
