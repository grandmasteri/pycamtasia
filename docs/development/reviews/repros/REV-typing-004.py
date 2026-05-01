"""REV-typing-004: 31 unused `# type: ignore` comments across the codebase.

These comments suppress errors that no longer exist, adding noise and
hiding future real issues. Under `--strict --warn-unused-ignores` (which
--strict enables), mypy flags all 31.

Repro: run `python -m mypy src/camtasia --strict 2>&1 | grep unused-ignore`.

Affected files (sample):
  - effects/visual.py:114, 124
  - effects/cursor.py:46, 53
  - timeline/clips/base.py:310, 315, 327, 335, 337, 350, 425, 483
  - timeline/track.py:55, 58, 847, 2635, 2651, 2671, 2691
  - project.py:44
  - builders/slide_import.py:31
  - export/captions.py:187
  - media_bin/media_bin.py:695
  - cli.py:206, 207
"""
