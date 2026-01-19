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


_SWEDISH_ALPHABET = "abcdefghijklmnopqrstuvwxyzåäö"


@dataclass(frozen=True)
class NextCharQuestion:
    current_char: str
    expected_char: str

    def read_question(self) -> str:
        return f"Nästa bokstav efter '{self.current_char}' är:"

    def answer_question(self, answer: str) -> QuestionResult:
        raw = answer.strip()
        if not raw:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"Rätt svar: {self.expected_char}",
            )

        raw_char = raw[0]
        if raw_char == self.expected_char:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"Rätt svar: {self.expected_char}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Rätt svar: {self.expected_char}",
        )

    def reveal_answer(self) -> QuestionResult:
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Rätt svar: {self.expected_char}",
        )


class NextCharPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        level = max(0, int(difficulty_or_chapter))
        alphabet = _SWEDISH_ALPHABET

        base_max_index = 9
        step = 5
        max_index = min(len(alphabet) - 1, base_max_index + level * step)
        max_index = max(1, max_index)

        idx = random.randint(0, max_index - 1)
        current_char = alphabet[idx]
        expected_char = alphabet[idx + 1]

        return NextCharQuestion(current_char=current_char, expected_char=expected_char)


class NextCharPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="next_char_se",
            name="Nästa bokstav (svenska alfabetet)",
            description="Frågar efter nästa bokstav i svenska alfabetet (inkl. å, ä, ö).",
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("🔤"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return NextCharPlugin()


PLUGIN_FACTORY: PluginFactory = NextCharPluginFactory
