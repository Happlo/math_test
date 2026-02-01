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
    QuestionResult,
)


@dataclass(frozen=True)
class MultiplicationQuestion:
    a: int
    b: int

    def read_question(self) -> str:
        return f"{self.a} x {self.b} ="

    def answer_question(self, answer: str) -> QuestionResult:
        correct = self.a * self.b

        try:
            value = int(answer.strip())
        except ValueError:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"{self.a} x {self.b} = {correct}",
            )

        if value == correct:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"{self.a} x {self.b} = {correct}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"{self.a} x {self.b} = {correct}",
        )

    def reveal_answer(self) -> QuestionResult:
        correct = self.a * self.b
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"{self.a} x {self.b} = {correct}",
        )


class MultiplicationPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        # Level 0: 0-1 times 0-10
        # Level 1: 0-2 times 0-10
        # Level 2: 0-3 times 0-10
        # ...
        a = random.randint(0, difficulty_or_chapter + 1)
        b = random.randint(0, 10)
        return MultiplicationQuestion(a=a, b=b)


class MultiplicationPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="multiplication",
            name="Multiplikation",
            description="Träna multiplikation med ökande svårighetsgrad.",
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("✖"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return MultiplicationPlugin()


PLUGIN_FACTORY: PluginFactory = MultiplicationPluginFactory
