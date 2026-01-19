from __future__ import annotations

from dataclasses import dataclass
from typing import List
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


_SWEDISH_ALPHABET = "abcdefghijklmnopqrstuvwxyzåäö"


@dataclass(frozen=True)
class AlphabetOrderQuestion:
    shown: List[str]
    correct_order: List[str]

    def read_question(self) -> str:
        shown = " ".join(self.shown)
        return f"Sätt bokstäverna i alfabetisk ordning:\n{shown}"

    def answer_question(self, answer: str) -> QuestionResult:
        raw = answer.strip().replace(" ", "")

        if len(raw) != len(self.correct_order):
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"Rätt ordning: {' '.join(self.correct_order)}",
            )

        given = list(raw)
        if given == self.correct_order:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"Rätt ordning: {' '.join(self.correct_order)}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Rätt ordning: {' '.join(self.correct_order)}",
        )

    def reveal_answer(self) -> QuestionResult:
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Rätt ordning: {' '.join(self.correct_order)}",
        )


class AlphabetOrderPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        level = max(0, int(difficulty_or_chapter))
        alphabet = _SWEDISH_ALPHABET

        num_chars = min(len(alphabet), 3 + level)
        num_chars = max(2, num_chars)

        chars = random.sample(list(alphabet), num_chars)
        correct = sorted(chars, key=alphabet.index)
        shuffled = chars[:]
        random.shuffle(shuffled)

        return AlphabetOrderQuestion(shown=shuffled, correct_order=correct)


class AlphabetOrderPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="alphabet_order_se",
            name="Alfabetisk ordning (svenska)",
            description="Sätt bokstäver i alfabetisk ordning (inkl. å, ä, ö).",
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("🔠"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return AlphabetOrderPlugin()


PLUGIN_FACTORY: PluginFactory = AlphabetOrderPluginFactory
