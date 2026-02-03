from __future__ import annotations

from dataclasses import dataclass
import random

from ..plugin_api import (
    AnswerResult,
    Difficulty,
    EmojiIcon,
    Plugin,
    PluginFactory,
    PluginInfo,
    Question,
    QuestionContent,
    QuestionResult,
)


@dataclass(frozen=True)
class MinusQuestion:
    a: int
    b: int

    def read_question(self) -> QuestionContent:
        return QuestionContent(question_text=f"{self.a} - {self.b} =")

    def answer_question(self, answer: str) -> QuestionResult:
        correct = self.a - self.b

        try:
            value = int(answer.strip())
        except ValueError:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"{self.a} - {self.b} = {correct}",
            )

        if value == correct:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"{self.a} - {self.b} = {correct}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"{self.a} - {self.b} = {correct}",
        )

    def reveal_answer(self) -> QuestionResult:
        correct = self.a - self.b
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"{self.a} - {self.b} = {correct}",
        )


class MinusPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        level = max(0, int(difficulty_or_chapter))
        max_value = 10 + level * 5
        allow_negative = level >= 3

        a = random.randint(0, max_value)
        b = random.randint(0, max_value) if allow_negative else random.randint(0, a)

        return MinusQuestion(a=a, b=b)


class MinusPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="minus",
            name="Subtraktion",
            description="Trana pa minus (negativa svar pa hogre nivaer).",
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("➖"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return MinusPlugin()


PLUGIN_FACTORY: PluginFactory = MinusPluginFactory
