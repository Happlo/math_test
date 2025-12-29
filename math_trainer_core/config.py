from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class TrainerConfig:
    num_questions: int
    question_time_limit_ms: Optional[int] = None
    plugin_id: str
    plugin_overrides: Mapping[str, Any]