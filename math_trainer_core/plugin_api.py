from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class PluginInfo:
    plugin_id: str
    name: str
    description: str

class IPluginFactory(Protocol):
    @staticmethod
    def PluginInfo() -> PluginInfo: ...

    @staticmethod
    def PluginConfig() -> dict[str, Any]: ...

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> Plugin: ...

class AnswerResult(Enum):
    CORRECT = auto()
    WRONG = auto()
    INVALID_INPUT = auto()

@dataclass(frozen=True)
class QuestionResult:
    result: AnswerResult
    display_answer_text: str

class Question(Protocol):
    def read_question(self) -> str: ...
    def answer_question(self, answer: str) -> QuestionResult: ...

class Plugin(Protocol):
    def make_question(self) -> Question: ...
