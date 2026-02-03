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
class PlaceValueQuestion:
    terms: list[int]

    _FIGURE_SPACE = "\u2007"

    def _format_number(self, value: int) -> str:
        return f"{value:,}".replace(",", self._FIGURE_SPACE)

    def _pad_left(self, text: str, width: int) -> str:
        pad_len = max(0, width - len(text))
        return f"{self._FIGURE_SPACE * pad_len}{text}"

    def read_question(self) -> QuestionContent:
        return QuestionContent(question_text=self._format_stacked())

    def _format_stacked(self, answer: int | None = None) -> str:
        width = max(len(self._format_number(term)) for term in self.terms)
        if answer is not None:
            width = max(width, len(self._format_number(answer)))

        lines = []
        for index, term in enumerate(self.terms):
            prefix = f"+{self._FIGURE_SPACE}" if index > 0 else f"{self._FIGURE_SPACE}{self._FIGURE_SPACE}"
            lines.append(f"{prefix}{self._pad_left(self._format_number(term), width)}")

        if answer is not None:
            lines.append(f"={self._FIGURE_SPACE}{self._pad_left(self._format_number(answer), width)}")

        return "\n".join(lines)

    def _format_answer_text(self, correct: int) -> str:
        return self._format_stacked(answer=correct)

    def answer_question(self, answer: str) -> QuestionResult:
        correct = sum(self.terms)

        try:
            value = int("".join(answer.split()))
        except ValueError:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=self._format_answer_text(correct),
            )

        if value == correct:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=self._format_answer_text(correct),
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=self._format_answer_text(correct),
        )

    def reveal_answer(self) -> QuestionResult:
        correct = sum(self.terms)
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=self._format_answer_text(correct),
        )


class PlaceValueAdditionPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        level = max(0, int(difficulty_or_chapter))

        max_power = 2 + level
        min_terms = 2
        max_terms = min(3 + level // 2, max_power + 1)
        term_count = random.randint(min_terms, max_terms)

        powers = random.sample(range(max_power + 1), k=term_count)
        terms = [random.randint(1, 9) * (10**power) for power in powers]
        terms.sort(reverse=True)

        return PlaceValueQuestion(terms=terms)


class PlaceValueAdditionPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="tio_potensaddition",
            name="Tio-potensaddition",
            description="Öva addition med tal byggda av olika tiopotenser.",
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("🔟"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return PlaceValueAdditionPlugin()


PLUGIN_FACTORY: PluginFactory = PlaceValueAdditionPluginFactory
