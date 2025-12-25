from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class TrainerConfig:
    num_questions: int
    plugin_id: str
    plugin_overrides: Mapping[str, Any]