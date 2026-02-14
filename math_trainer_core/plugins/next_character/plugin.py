from __future__ import annotations

from dataclasses import dataclass
import random

from ..plugin_api import (
    AnswerResult,
    Chapter,
    EmojiIcon,
    Plugin,
    PluginFactory,
    PluginInfo,
    Question,
    QuestionContent,
    QuestionResult,
)


_SWEDISH_ALPHABET = "abcdefghijklmnopqrstuvwxyzåäö"


@dataclass(frozen=True)
class NextCharQuestion:
    current_char: str
    expected_char: str

    def read_question(self) -> QuestionContent:
        return QuestionContent(
            question_text=f"Nästa bokstav efter '{self.current_char}' är:"
        )

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
        alphabet = _SWEDISH_ALPHABET
        idx = random.randint(0, len(alphabet) - 2)
        return NextCharQuestion(
            current_char=alphabet[idx],
            expected_char=alphabet[idx + 1],
        )


class NextCharPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="next_char_se",
            name="Nästa bokstav (svenska alfabetet)",
            description="Frågar efter nästa bokstav i svenska alfabetet (inkl. å, ä, ö).",
            mode=[Chapter(name="Standard")],
            icon=EmojiIcon("🔤"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return NextCharPlugin()


PLUGIN_FACTORY: PluginFactory = NextCharPluginFactory
