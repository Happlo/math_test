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
class PlusConfig:
    max_sum: int = 20
    min_operand: int = 2


@dataclass(frozen=True)
class PlusQuestion(Question):
    a: int
    b: int

    def read_question(self) -> str:
        return f"{self.a} + {self.b} ="

    def answer_question(self, answer: str) -> QuestionResult:
        correct = self.a + self.b
        display = f"{self.a} + {self.b} = {correct}"

        try:
            value = int(answer.strip())
        except ValueError:
            return QuestionResult(AnswerResult.INVALID_INPUT, display)

        if value == correct:
            return QuestionResult(AnswerResult.CORRECT, display)

        return QuestionResult(AnswerResult.WRONG, display)


class PlusPlugin(Plugin):
    def __init__(self, cfg: PlusConfig):
        self._cfg = cfg

    def make_question(self) -> Question:
        max_sum = max(0, int(self._cfg.max_sum))
        min_op = max(0, int(self._cfg.min_operand))

        a = random.randint(min_op, max_sum - min_op)
        b = random.randint(min_op, max_sum - a)

        return PlusQuestion(a=a, b=b)


class PlusPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            plugin_id="plus",
            name="Addition",
            description="Träna på plus med max-summa.",
        )

    @staticmethod
    def PluginConfig() -> dict[str, Any]:
        cfg = PlusConfig()
        return {
            "max_sum": cfg.max_sum,
            "min_operand": cfg.min_operand,
        }

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> Plugin:
        defaults = PlusPluginFactory.PluginConfig()
        merged = {**defaults, **dict(config)}

        cfg = PlusConfig(
            max_sum=int(merged["max_sum"]),
            min_operand=int(merged["min_operand"]),
        )
        return PlusPlugin(cfg)


PLUGIN_FACTORY = PlusPluginFactory
