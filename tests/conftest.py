from __future__ import annotations

import pytest
from pathlib import Path

try:
    import pymediainfo
    HAS_PYMEDIAINFO = True
except ImportError:
    HAS_PYMEDIAINFO = False

pymediainfo_required = pytest.mark.skipif(
    not HAS_PYMEDIAINFO,
    reason="pymediainfo not installed"
)

RESOURCES = Path(__file__).parent.parent / 'src' / 'camtasia' / 'resources'

@pytest.fixture
def project():
    from camtasia.project import load_project
    return load_project(RESOURCES / 'new.cmproj')

@pytest.fixture
def simple_video_path():
    return RESOURCES / 'simple-video.cmproj'

@pytest.fixture
def simple_video(simple_video_path):
    from camtasia.project import load_project
    return load_project(simple_video_path)

@pytest.fixture
def media_root():
    return RESOURCES / 'media'
