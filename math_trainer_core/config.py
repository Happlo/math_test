from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TrainerConfig:
    num_questions: int
    max_value: int
    operator_plugin: str     # e.g. "plus" or "minus"
    allow_negative: bool = False
