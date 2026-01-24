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
class PlaceValueQuestion:
    terms: list[int]
    stacked: bool

    def read_question(self) -> str:
        if not self.stacked:
            return f"{' + '.join(str(term) for term in self.terms)} ="
        return self._format_stacked()

    def _format_stacked(self, answer: int | None = None) -> str:
        width = max(len(str(term)) for term in self.terms)
        if answer is not None:
            width = max(width, len(str(answer)))

        lines = []
        for index, term in enumerate(self.terms):
            prefix = "+ " if index > 0 else "  "
            lines.append(f"{prefix}{str(term).rjust(width)}")

        if answer is not None:
            lines.append(f"= {str(answer).rjust(width)}")

        return "\n".join(lines)

    def _format_answer_text(self, correct: int) -> str:
        if not self.stacked:
            return f"{self.read_question()} {correct}"
        return self._format_stacked(answer=correct)

    def answer_question(self, answer: str) -> QuestionResult:
        correct = sum(self.terms)

        try:
            value = int(answer.strip())
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
        stacked = level < 5

        max_power = 2 + level
        min_terms = 2
        max_terms = min(3 + level // 2, max_power + 1)
        term_count = random.randint(min_terms, max_terms)

        powers = random.sample(range(max_power + 1), k=term_count)
        terms = [random.randint(1, 9) * (10**power) for power in powers]
        terms.sort(reverse=True)

        return PlaceValueQuestion(terms=terms, stacked=stacked)


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
