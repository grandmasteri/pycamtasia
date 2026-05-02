"""REV-edge_cases-013: save_dynamic_caption_preset allows path traversal in name."""
import tempfile
import os
from pathlib import Path
from camtasia.timeline.captions import (
    save_dynamic_caption_preset,
    load_dynamic_caption_preset,
    DynamicCaptionStyle,
)

style = DynamicCaptionStyle(name="test")

with tempfile.TemporaryDirectory() as tmpdir:
    presets_dir = Path(tmpdir) / "presets"
    
    # Path traversal in name
    try:
        path = save_dynamic_caption_preset(style, "../../etc/evil", presets_dir=presets_dir)
        print(f"CONFIRMED: path traversal accepted, wrote to: {path}")
        print(f"  File exists: {path.exists()}")
        print(f"  Resolved: {path.resolve()}")
        # Clean up
        if path.exists():
            path.unlink()
            # Clean up parent dirs if created
    except Exception as e:
        print(f"Rejected: {type(e).__name__}: {e}")

    # Null byte in name
    try:
        path = save_dynamic_caption_preset(style, "test\x00evil", presets_dir=presets_dir)
        print(f"Null byte in name: wrote to {path}")
    except (ValueError, OSError) as e:
        print(f"Null byte rejected: {type(e).__name__}: {e}")

    # Empty name
    try:
        path = save_dynamic_caption_preset(style, "", presets_dir=presets_dir)
        print(f"Empty name: wrote to {path}")
        print(f"  File exists: {path.exists()}")
    except Exception as e:
        print(f"Empty name rejected: {type(e).__name__}: {e}")

    # Very long name
    try:
        long_name = "a" * 300
        path = save_dynamic_caption_preset(style, long_name, presets_dir=presets_dir)
        print(f"Long name (300 chars): wrote to {path}")
    except (OSError, Exception) as e:
        print(f"Long name rejected: {type(e).__name__}: {e}")
