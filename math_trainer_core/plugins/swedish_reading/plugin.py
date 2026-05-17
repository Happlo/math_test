from __future__ import annotations

from dataclasses import dataclass
import json
import random
import string
from pathlib import Path

from ..plugin_api import (
    AnswerInput,
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


_WORDS_FILE = "words.json"
_PUNCTUATION = str.maketrans("", "", string.punctuation + "…“”’")


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parent


def _normalize(text: str) -> str:
    return " ".join(text.lower().translate(_PUNCTUATION).split())


def _load_word_chapters() -> list[tuple[str, list[str]]]:
    with (_plugin_dir() / _WORDS_FILE).open(encoding="utf-8") as f:
        raw = json.load(f)

    chapters: list[tuple[str, list[str]]] = []
    for name, words in raw.items():
        clean_words = [str(word).strip() for word in words if str(word).strip()]
        if clean_words:
            chapters.append((str(name), clean_words))

    if not chapters:
        raise RuntimeError(f"No words found in {_WORDS_FILE}")

    return chapters


@dataclass(frozen=True)
class SwedishReadingQuestion:
    word: str

    def read_question(self) -> QuestionContent:
        return QuestionContent(question_text=f"Läs ordet:\n\n{self.word}")

    def answer_question(self, answer: str) -> QuestionResult:
        normalized_answer = _normalize(answer)
        expected = _normalize(self.word)
        if not normalized_answer:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"Läs ordet: {self.word}",
            )

        if normalized_answer == expected:
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"Rätt: {self.word}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Jag hörde: {answer}\nRätt ord: {self.word}",
        )

    def reveal_answer(self) -> QuestionResult:
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Rätt ord: {self.word}",
        )


class SwedishReadingPlugin(Plugin):
    def __init__(self, chapters: list[tuple[str, list[str]]]):
        self._chapters = chapters
        self._remaining_by_chapter: dict[int, list[str]] = {}

    def reset(self) -> None:
        self._remaining_by_chapter.clear()

    def make_question(self, difficulty_or_chapter: int) -> Question:
        chapter_idx = max(0, min(int(difficulty_or_chapter), len(self._chapters) - 1))
        words = self._remaining_by_chapter.get(chapter_idx)
        if not words:
            words = list(self._chapters[chapter_idx][1])
            random.shuffle(words)
            self._remaining_by_chapter[chapter_idx] = words

        return SwedishReadingQuestion(word=words.pop())


class SwedishReadingPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        chapters = _load_word_chapters()
        return PluginInfo(
            id="swedish_reading",
            name="Lästräning",
            description="Läs svenska ord högt.",
            mode=[
                Chapter(name=name, required_streak=len(words))
                for name, words in chapters
            ],
            icon=EmojiIcon("📖"),
            required_streak=None,
            answer_input=AnswerInput.SPEECH_TO_TEXT,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return SwedishReadingPlugin(chapters=_load_word_chapters())


PLUGIN_FACTORY: PluginFactory = SwedishReadingPluginFactory
