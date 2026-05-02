"""REV-api_consistency-001: duration_formatted vs total_duration_formatted overlap.

Both properties exist on Project, but for durations < 1 hour they return
identical output (M:SS). For durations >= 1 hour, duration_formatted
silently overflows (e.g. '90:00' instead of '1:30:00').
"""
# This is a conceptual repro — requires a project file to run.
# Demonstrates the confusing overlap:
#
#   project.duration_formatted      -> '5:30'   (MM:SS, no hours support)
#   project.total_duration_formatted -> '5:30'   (M:SS, with hours support)
#
# For a 90-minute project:
#   project.duration_formatted      -> '90:00'  (wrong — no hours)
#   project.total_duration_formatted -> '1:30:00' (correct)
#
# The two properties have near-identical names but different formatting
# capabilities, creating confusion about which to use.

# Simulated demonstration:
total_seconds_short = 330.0  # 5:30
total_seconds_long = 5400.0  # 1:30:00

# duration_formatted logic (MM:SS only):
minutes = int(total_seconds_long // 60)
remaining = int(total_seconds_long % 60)
duration_formatted = f'{minutes}:{remaining:02d}'
print(f'duration_formatted for 90min: {duration_formatted}')  # '90:00' — misleading

# total_duration_formatted logic (HH:MM:SS):
hours = int(total_seconds_long // 3600)
minutes2 = int((total_seconds_long % 3600) // 60)
remaining2 = int(total_seconds_long % 60)
total_duration_formatted = f'{hours}:{minutes2:02d}:{remaining2:02d}'
print(f'total_duration_formatted for 90min: {total_duration_formatted}')  # '1:30:00'

assert duration_formatted != total_duration_formatted, \
    "For long durations, the two properties diverge silently"
