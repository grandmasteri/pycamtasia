import pytest

from camtasia.screenplay import parse_screenplay

SAMPLE = """\
## Introduction

[VO-1.1]:** "Welcome to the tutorial"

PAUSE 1.0 second

![overview](images/overview.png)

## Main Content

[VO-2.1]:** "Let's dive into the details"

TRANSITION: fade to black

PAUSE 1.5 seconds

### Sub Section

[VO-3.1]:** "Here is a subsection"
"""


@pytest.fixture
def screenplay(tmp_path):
    f = tmp_path / "test.md"
    f.write_text(SAMPLE)
    return parse_screenplay(f)


def test_parse_sections(screenplay):
    assert [s.title for s in screenplay.sections] == ["Introduction", "Main Content", "Sub Section"]


def test_parse_vo_blocks(screenplay):
    assert [b.id for b in screenplay.vo_blocks] == ["1.1", "2.1", "3.1"]
    assert screenplay.vo_blocks[0].text == "Welcome to the tutorial"
    assert screenplay.vo_blocks[1].section == "Main Content"


def test_parse_pauses(screenplay):
    pauses = [p for s in screenplay.sections for p in s.pauses]
    assert [p.duration_seconds for p in pauses] == [1.0, 1.5]


def test_parse_transitions(screenplay):
    transitions = [t for s in screenplay.sections for t in s.transitions]
    assert [t.name for t in transitions] == ["fade to black"]


def test_parse_images(screenplay):
    assert len(screenplay.all_images) == 1
    img = screenplay.all_images[0]
    assert img.alt == "overview"
    assert img.path == "images/overview.png"


def test_vo_blocks_property(screenplay):
    assert screenplay.vo_blocks == [b for s in screenplay.sections for b in s.vo_blocks]


def test_total_pauses(screenplay):
    assert screenplay.total_pauses == 2.5
