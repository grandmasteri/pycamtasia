"""REV-api_consistency-005: font_color parameter type is inconsistent.

Most methods use tuple[float, float, float] (RGB), but add_text_watermark
uses tuple[float, float, float, float] (RGBA). Meanwhile, Track.add_lower_third
uses title_color: tuple[int, int, int, int] (RGBA 0-255 ints).

A user copying a color value from one method to another will get wrong results.
"""
# Conceptual repro:
#
# Project.add_title_card:
#   font_color: tuple[float, float, float] = (1.0, 1.0, 1.0)  # RGB floats
#
# Project.add_subtitle_track:
#   font_color: tuple[float, float, float] = (1.0, 1.0, 1.0)  # RGB floats
#
# Project.add_caption:
#   font_color: tuple[float, float, float] = (1.0, 1.0, 1.0)  # RGB floats
#
# Project.add_text_watermark:
#   font_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)  # RGBA floats
#
# Track.add_lower_third:
#   title_color: tuple[int, int, int, int] | None = None  # RGBA 0-255 ints!
#
# Three different color representations in the same library:
#   1. RGB float tuple (3 elements)
#   2. RGBA float tuple (4 elements)
#   3. RGBA int tuple (4 elements, 0-255 range)

# If a user tries to pass a color from add_title_card to add_lower_third:
font_color_from_title = (1.0, 1.0, 1.0)  # RGB float
# title_color expects (255, 255, 255, 255)  # RGBA int
# Passing (1.0, 1.0, 1.0) would be interpreted as near-black (1, 1, 1)
