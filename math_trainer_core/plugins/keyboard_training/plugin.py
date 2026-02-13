from __future__ import annotations

from dataclasses import dataclass
import random

from math_trainer_core.api_types import PictureWithText
from math_trainer_core.core.picture_helper import PictureRef, download_picture
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


_KEYBOARD_IMAGE_URL = (
    "https://raw.githubusercontent.com/frippz/wasd-iso-sv-aek2/refs/heads/master/WASD-ISO-SV-AEKII-light.png"
)
# Ordered by increasing difficulty (rough touch-typing progression).
_ALPHABET = "JFKDLSÖAHGEIRUWOTYQPÅZXCVBNMÄ,."


def _make_prompt(letters: str) -> str:
    return "Titta inte på tangentbordet.\nSkriv: " + letters


@dataclass(frozen=True)
class KeyboardTrainingQuestion:
    letters: str

    def _picture(self) -> PictureWithText:
        picture_path = download_picture(PictureRef(url=_KEYBOARD_IMAGE_URL))
        return PictureWithText(picture=picture_path, optional_text=None)

    def read_question(self) -> QuestionContent:
        return QuestionContent(
            question_text=_make_prompt(self.letters),
            optional_pictures=[self._picture()],
        )

    def answer_question(self, answer: str) -> QuestionResult:
        normalized = "".join(answer.split()).upper()
        if len(normalized) != len(self.letters):
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=_make_prompt(self.letters),
            )

        if normalized == self.letters:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=_make_prompt(self.letters),
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=_make_prompt(self.letters),
        )

    def reveal_answer(self) -> QuestionResult:
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=_make_prompt(self.letters),
        )


class KeyboardTrainingPlugin(Plugin):
    def make_question(self, difficulty: int) -> Question:
        level = max(0, int(difficulty))
        pick_count = min(len(_ALPHABET), 4 + (level * 2))
        letter_count = random.randint(3, 3 + level)
        pool = _ALPHABET[:pick_count]
        letters = "".join(random.choice(pool) for _ in range(letter_count))
        return KeyboardTrainingQuestion(letters=letters)


class KeyboardTrainingPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="keyboard_training",
            name="Tangentbordsträning",
            description="Träna på att skriva bokstäver utan att titta på tangentbordet.",
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("⌨️"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return KeyboardTrainingPlugin()


PLUGIN_FACTORY: PluginFactory = KeyboardTrainingPluginFactory
