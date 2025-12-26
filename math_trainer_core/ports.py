from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from enum import Enum, auto


@dataclass(frozen=True)
class Question:
    display_question: str
    correct_answer: int
    display_answer_text: str


class Progress(Enum):
    PENDING = auto()
    CORRECT = auto()
    WRONG = auto()

@dataclass(frozen=True)
class ViewState:
    question_text: str
    feedback_text: str
    streak: int
    progress: list[Progress]
    input_enabled: bool

class IRandom(Protocol):
    def randint(self, lo: int, hi: int) -> int: ...


class IOperatorPlugin(Protocol):
    def plugin_id(self) -> str: ...
    def name(self) -> str: ...
    def description(self) -> str: ...

    # key/value defaults (your requirement)
    def config_defaults(self) -> dict[str, Any]: ...

    # optional: ui hints (still key/value-ish)
    # example values: {"max_sum": {"type":"int","min":2,"max":50,"label":"Max summa"}}
    def config_spec(self) -> dict[str, dict[str, Any]]: ...

    # produce question using merged config
    def make_question(self, rng: IRandom, config: Mapping[str, Any]) -> Question: ...
