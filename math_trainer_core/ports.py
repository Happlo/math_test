from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Protocol, Union


class Progress(Enum):
    PENDING = auto()
    CORRECT = auto()
    WRONG = auto()
    TIMED_OUT = auto()


@dataclass(frozen=True)
class ViewState:
    question_text: str
    feedback_text: str
    streak: int
    progress: list[Progress]
    input_enabled: bool
    remaining_ms: Optional[int]


class QuestionStep(Protocol):
    state: ViewState
    def answer(self, raw_answer: str) -> Step: ...
    def refresh(self) -> Step: ...


class FeedbackStep(Protocol):
    state: ViewState
    def next(self) -> Step: ...


@dataclass(frozen=True)
class Finished:
    state: ViewState


Step = Union[QuestionStep, FeedbackStep, Finished]
