from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Protocol, Union

class Progress(Enum):
    PENDING = auto()
    CORRECT = auto()
    WRONG = auto()
    TIMED_OUT = auto()

@dataclass
class View:
    question_text: str
    feedback_text: str
    streak: int
    score: int
    progress: list[Progress]
    question_idx: int
    input_enabled: bool
    remaining_ms: Optional[int]


class QuestionState(Protocol):
    view: View
    def answer(self, raw_answer: str) -> State: ...
    def refresh(self) -> State: ...

class FeedbackState(Protocol):
    view: View
    def next(self) -> State: ...

class FinishedState:
    view: View

State = Union[QuestionState, FeedbackState, FinishedState]

@dataclass(frozen=True)
class Mode:
    mode_id: str
    name: str
    description: str

@dataclass(frozen=True)
class TrainerConfig:
    num_questions: int
    time_limit_ms: Optional[int] = None  # None/<=0 => no timer