from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

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
