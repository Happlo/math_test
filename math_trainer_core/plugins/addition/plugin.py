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
            # Core will typically show its own "invalid input" message,
            # but we still provide the correct answer here.
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
        """
        Used when time expires (or question is ended without an answer).
        Plugin does not know about timers, just shows the correct result.
        """
        correct = self.a + self.b
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"{self.a} + {self.b} = {correct}",
        )


# Plugin implementation --------------------------------------------------------


class PlusPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        # Interpret difficulty_or_chapter as a difficulty level.
        # Level 0: sums up to 10
        # Level 1: sums up to 15
        # Level 2: sums up to 20
        # etc.
        level = max(0, int(difficulty_or_chapter))
        base_max_sum = 10
        increment = 5
        max_sum = base_max_sum + level * increment

        # Keep operands in range [0, max_sum], ensuring a + b <= max_sum
        a = random.randint(0, max_sum)
        b = random.randint(0, max_sum - a)

        return PlusQuestion(a=a, b=b)


class PlusPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="plus",
            name="Addition",
            description="Practice addition with increasing difficulty.",
            mode=Difficulty(max_level=0),  # 0 = infinite difficulty levels
            icon=EmojiIcon("➕"),
            required_streak=None,  # let core use its default
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return PlusPlugin()


PLUGIN_FACTORY: PluginFactory = PlusPluginFactory
