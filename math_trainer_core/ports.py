from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Question:
    a: int
    b: int
    display: str
    correct_answer: int

@dataclass(frozen=True)
class ViewState:
    question_text: str
    feedback_text: str
    streak: int
    input_enabled: bool

class IRandom(Protocol):
    def randint(self, lo: int, hi: int) -> int: ...

class IOperatorPlugin(Protocol):
    # stable id for config: "plus", "minus", ...
    def plugin_id(self) -> str: ...

    # create a new question given constraints
    def make_question(self, rng: IRandom, max_value: int, allow_negative: bool) -> Question: ...
