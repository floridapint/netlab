from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LessonSpec:
    key: str
    number: int
    title: str
    short: str          # подпись в боковом меню
    subtitle: str       # описание на карточке и в шапке
    color: str
    theory: str
    scenarios: list = field(default_factory=list)      # классы Scenario
    interactive: list = field(default_factory=list)    # [(название, factory(parent))]
    practice: list = field(default_factory=list)       # [(название, factory(parent, on_solved))]
