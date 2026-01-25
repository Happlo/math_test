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
class PlusQuestion:
    a: int
    b: int
    _FIGURE_SPACE = "\u2007"

    def _format_number(self, value: int) -> str:
        return str(value)

    def _pad_left(self, text: str, width: int) -> str:
        pad_len = max(0, width - len(text))
        return f"{self._FIGURE_SPACE * pad_len}{text}"

    def _format_stacked(self, answer: int | None = None) -> str:
        width = max(len(self._format_number(self.a)), len(self._format_number(self.b)))
        if answer is not None:
            width = max(width, len(self._format_number(answer)))

        top = f"{self._FIGURE_SPACE}{self._FIGURE_SPACE}{self._pad_left(self._format_number(self.a), width)}"
        bottom = f"+{self._FIGURE_SPACE}{self._pad_left(self._format_number(self.b), width)}"
        lines = [top, bottom]

        if answer is not None:
            lines.append(f"={self._FIGURE_SPACE}{self._pad_left(self._format_number(answer), width)}")

        return "\n".join(lines)

    def read_question(self) -> str:
        return self._format_stacked()

    def answer_question(self, answer: str) -> QuestionResult:
        correct = self.a + self.b

        try:
            value = int("".join(answer.split()))
        except ValueError:
            # Core will typically show its own "invalid input" message,
            # but we still provide the correct answer here.
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=self._format_stacked(answer=correct),
            )

        if value == correct:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=self._format_stacked(answer=correct),
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=self._format_stacked(answer=correct),
        )

    def reveal_answer(self) -> QuestionResult:
        """
        Used when time expires (or question is ended without an answer).
        Plugin does not know about timers, just shows the correct result.
        """
        correct = self.a + self.b
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=self._format_stacked(answer=correct),
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
        a = random.randint(2, max_sum -2)
        b = random.randint(2, max_sum - a)

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
