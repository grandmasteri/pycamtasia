"""REV-api_consistency-006: add_lower_third has incompatible signatures
between Project and Track.

Project.add_lower_third returns BaseClip (a simple callout).
Track.add_lower_third returns Group (a template-based lower third).

They have different parameter names (title_text vs title, subtitle_text
vs subtitle), different return types, and produce completely different
output structures.
"""
# Conceptual repro:
#
# Project.add_lower_third(
#     title_text='Name',        # <-- 'title_text'
#     subtitle_text='Role',     # <-- 'subtitle_text'
#     start_seconds=0.0,
#     duration_seconds=5.0,
#     track_name='Lower Thirds',
#     fade_seconds=0.5,
# ) -> BaseClip                 # Returns a simple callout
#
# Track.add_lower_third(
#     title='Name',             # <-- 'title' (different name!)
#     subtitle='Role',          # <-- 'subtitle' (different name!)
#     start_seconds=0.0,
#     duration_seconds=5.0,
#     title_color=None,
#     accent_color=None,
#     *,
#     font_weight=900,
#     scale=None,
#     template_ident='Right Angle Lower Third',
# ) -> Group                    # Returns a Group (different type!)
#
# Same method name, different parameter names, different return types,
# different visual output. This violates the principle of least surprise.
