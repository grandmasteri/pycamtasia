import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VOBlock:
    id: str
    text: str
    section: str


@dataclass
class PauseMarker:
    duration_seconds: float
    description: str


@dataclass
class TransitionMarker:
    name: str


@dataclass
class ImageRef:
    alt: str
    path: str


@dataclass
class ScreenplaySection:
    title: str
    level: int
    vo_blocks: list[VOBlock] = field(default_factory=list)
    pauses: list[PauseMarker] = field(default_factory=list)
    transitions: list[TransitionMarker] = field(default_factory=list)
    images: list[ImageRef] = field(default_factory=list)


@dataclass
class Screenplay:
    sections: list[ScreenplaySection]

    @property
    def vo_blocks(self) -> list[VOBlock]:
        return [b for s in self.sections for b in s.vo_blocks]

    @property
    def total_pauses(self) -> float:
        return sum(p.duration_seconds for s in self.sections for p in s.pauses)

    @property
    def all_images(self) -> list[ImageRef]:
        return [i for s in self.sections for i in s.images]


_VO_RE = re.compile(r'\[VO-([\d.]+)\].*?:\*\*\s*"([^"]+)"')
_PAUSE_RE = re.compile(r'PAUSE[:\s*]+(\d+(?:\.\d+)?)\s*second')
_TRANSITION_RE = re.compile(r'TRANSITION:\s*(.+)')
_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
_SECTION_RE = re.compile(r'^(#{2,3})\s+(.+)', re.MULTILINE)


def parse_screenplay(path: str | Path) -> Screenplay:
    text = Path(path).read_text()
    splits = list(_SECTION_RE.finditer(text))
    sections: list[ScreenplaySection] = []

    for i, m in enumerate(splits):
        start = m.end()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
        chunk = text[start:end]
        title = m.group(2).strip()
        level = len(m.group(1))

        section = ScreenplaySection(
            title=title,
            level=level,
            vo_blocks=[VOBlock(id=v.group(1), text=v.group(2), section=title) for v in _VO_RE.finditer(chunk)],
            pauses=[PauseMarker(duration_seconds=float(p.group(1)), description=p.group(0)) for p in _PAUSE_RE.finditer(chunk)],
            transitions=[TransitionMarker(name=t.group(1).strip()) for t in _TRANSITION_RE.finditer(chunk)],
            images=[ImageRef(alt=img.group(1), path=img.group(2)) for img in _IMAGE_RE.finditer(chunk)],
        )
        sections.append(section)

    return Screenplay(sections=sections)
