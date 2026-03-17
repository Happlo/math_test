from __future__ import annotations

from dataclasses import dataclass
import random
import re

from math_trainer_core.api_types import PictureWithText
from math_trainer_core.core.picture_helper import PictureRef, download_picture
from ..plugin_api import (
    AnswerButton,
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


_TIME_RE = re.compile(r"^\s*(\d{1,2})\s*:\s*(\d{2})\s*$")


def _clock_url(hour: int, minute: int) -> str:
    return (
        "https://commons.wikimedia.org/wiki/Special:FilePath/"
        f"Reloj_H_{hour:02d}_{minute:02d}.svg"
    )


def _to_24_hour(hour: int, meridiem: str) -> int:
    if meridiem == "AM":
        return 0 if hour == 12 else hour
    return 12 if hour == 12 else hour + 12


def _format_time_24(hour_24: int, minute: int) -> str:
    return f"{hour_24}:{minute:02d}"


def _normalize_answer(value: str) -> str | None:
    match = _TIME_RE.match(value)
    if match is None:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2))

    if hour < 0 or hour > 23:
        return None
    if minute < 0 or minute > 59:
        return None

    return _format_time_24(hour, minute)


def _minute_choices(level: int) -> list[int]:
    if level <= 0:
        return [0]
    if level == 1:
        return [0, 30]
    if level == 2:
        return [0]
    if level == 3:
        return [0, 30]
    if level == 4:
        return [0, 15, 30, 45]
    if level == 5:
        return list(range(0, 60, 5))
    return list(range(60))


def _meridiem_choices(level: int) -> list[str]:
    if level <= 1:
        return ["AM"]
    return ["AM", "PM"]


@dataclass(frozen=True)
class ClockQuestion:
    hour: int
    minute: int
    meridiem: str

    def _answer_text(self) -> str:
        return f"Ratt svar: {self._correct_answer()}"

    def _correct_answer(self) -> str:
        return _format_time_24(_to_24_hour(self.hour, self.meridiem), self.minute)

    def read_question(self) -> QuestionContent:
        picture_paths: list[PictureWithText] = []
        try:
            picture_path = download_picture(
                PictureRef(url=_clock_url(self.hour, self.minute))
            )
            picture_paths = [PictureWithText(picture=picture_path, optional_text=None)]
        except Exception:
            picture_paths = []

        return QuestionContent(
            question_text=(
                "Vad visar klockan?\n"
                "Svara i digital 24-timmarsform.\n"
                f"Det ar {self.meridiem}."
            ),
            optional_pictures=picture_paths,
        )

    def answer_question(self, answer: str) -> QuestionResult:
        normalized = _normalize_answer(answer)
        if normalized is None:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=self._answer_text(),
            )

        correct = self._correct_answer()
        if normalized == correct:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=self._answer_text(),
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=self._answer_text(),
        )

    def reveal_answer(self) -> QuestionResult:
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=self._answer_text(),
        )


class ClockPlugin(Plugin):
    def make_question(self, difficulty_or_chapter: int) -> Question:
        level = max(0, int(difficulty_or_chapter))
        hour = random.randint(1, 12)
        minute = random.choice(_minute_choices(level))
        meridiem = random.choice(_meridiem_choices(level))
        return ClockQuestion(hour=hour, minute=minute, meridiem=meridiem)


class ClockPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="clock",
            name="Clock",
            description=(
                "Las en analog klocka och svara i digital 24-timmarsform. "
                "Svarighetsgraden okar fran hela timmar till valfri minut."
            ),
            mode=Difficulty(max_level=0),
            icon=EmojiIcon("🕒"),
            required_streak=None,
            accepted_answer_buttons=[AnswerButton.ENTER],
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return ClockPlugin()


PLUGIN_FACTORY: PluginFactory = ClockPluginFactory
