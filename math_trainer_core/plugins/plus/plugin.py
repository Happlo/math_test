from __future__ import annotations

from dataclasses import dataclass
import random

from ...plugin_api import (
    AnswerResult,
    Difficulty,
    EmojiIcon,
    Plugin,
    PluginFactory,
    PluginInfo,
    Question,
    QuestionResult,
)


@dataclass(frozen=True)
class PlusQuestion:
    a: int
    b: int

    def read_question(self) -> str:
        return f"{self.a} + {self.b} ="

    def answer_question(self, answer: str) -> QuestionResult:
        correct = self.a + self.b

        try:
            value = int(answer.strip())
        except ValueError:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"{self.a} + {self.b} = {correct}",
            )

        if value == correct:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"{self.a} + {self.b} = {correct}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"{self.a} + {self.b} = {correct}",
        )

    def reveal_answer(self) -> QuestionResult:
        correct = self.a + self.b
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"{self.a} + {self.b} = {correct}",
        )


class PlusPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        level = max(0, int(difficulty_or_chapter))
        max_sum = 10 + level * 5
        min_operand = 2

        if max_sum < min_operand * 2:
            max_sum = min_operand * 2

        a = random.randint(min_operand, max_sum - min_operand)
        b = random.randint(min_operand, max_sum - a)

        return PlusQuestion(a=a, b=b)


class PlusPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="plus_simple",
            name="Addition (simple)",
            description="Practice addition with small sums.",
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("➕"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return PlusPlugin()


PLUGIN_FACTORY: PluginFactory = PlusPluginFactory
