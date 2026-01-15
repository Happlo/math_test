from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import random

from ..plugin_api import (
    AnswerResult,
    Plugin,
    Question,
    PluginInfo,
    QuestionResult,
)


@dataclass(frozen=True)
class MinusConfig:
    max_value: int = 10
    allow_negative: bool = False


@dataclass(frozen=True)
class MinusQuestion(Question):
    a: int
    b: int

    def read_question(self) -> str:
        return f"{self.a} - {self.b} ="

    def answer_question(self, answer: str) -> QuestionResult:
        correct = self.a - self.b
        display = f"{self.a} - {self.b} = {correct}"

        try:
            value = int(answer.strip())
        except ValueError:
            return QuestionResult(AnswerResult.INVALID_INPUT, display)

        if value == correct:
            return QuestionResult(AnswerResult.CORRECT, display)

        return QuestionResult(AnswerResult.WRONG, display)


class MinusPlugin(Plugin):
    def __init__(self, cfg: MinusConfig):
        self._cfg = cfg

    def make_question(self) -> Question:
        max_value = max(0, int(self._cfg.max_value))
        allow_negative = bool(self._cfg.allow_negative)

        a = random.randint(0, max_value)
        b = random.randint(0, max_value) if allow_negative else random.randint(0, a)

        return MinusQuestion(a=a, b=b)


class MinusPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="minus",
            name="Subtraktion",
            description="Träna på minus (val för negativa svar).",
        )

    @staticmethod
    def PluginConfig() -> dict[str, Any]:
        cfg = MinusConfig()
        return {
            "max_value": cfg.max_value,
            "allow_negative": cfg.allow_negative,
        }

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> Plugin:
        defaults = MinusPluginFactory.PluginConfig()
        merged = {**defaults, **dict(config)}

        cfg = MinusConfig(
            max_value=int(merged["max_value"]),
            allow_negative=bool(merged["allow_negative"]),
        )
        return MinusPlugin(cfg)


#PLUGIN_FACTORY = MinusPluginFactory
