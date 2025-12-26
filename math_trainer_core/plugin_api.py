from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class PluginInfo:
    plugin_id: str
    name: str
    description: str


class IRandom(Protocol):
    def randint(self, lo: int, hi: int) -> int: ...


@dataclass(frozen=True)
class Question:
    display_question: str
    correct_answer: int
    display_answer_text: str


class IOperatorPlugin(Protocol):
    def make_question(self) -> Question: ...
