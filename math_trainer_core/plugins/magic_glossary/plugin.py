from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random

from ..plugin_api import (
    AnswerButton,
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


_CHAPTER_FILES: list[tuple[str, str]] = [
    ("Grundord", "glossary_basics.json"),
]


@dataclass(frozen=True)
class _GlossaryEntry:
    english: str
    swedish: str


@dataclass(frozen=True)
class _ChapterData:
    name: str
    entries: list[_GlossaryEntry]


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parent


def _normalize_answer(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _load_chapter_file(filename: str) -> list[_GlossaryEntry]:
    path = _plugin_dir() / filename
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid glossary chapter file format: {path}")

    entries: list[_GlossaryEntry] = []
    for english, swedish in raw.items():
        if not isinstance(english, str) or not english.strip():
            continue
        if not isinstance(swedish, str) or not swedish.strip():
            continue
        entries.append(
            _GlossaryEntry(
                english=english.strip(),
                swedish=swedish.strip(),
            )
        )

    if not entries:
        raise ValueError(f"Glossary chapter has no usable entries: {path}")
    return entries


def _load_chapters() -> list[_ChapterData]:
    chapters: list[_ChapterData] = []
    for chapter_name, filename in _CHAPTER_FILES:
        chapters.append(
            _ChapterData(
                name=chapter_name,
                entries=_load_chapter_file(filename),
            )
        )
    if not chapters:
        raise ValueError("Magic glossary plugin has no chapter files configured.")
    return chapters


@dataclass(frozen=True)
class MagicGlossaryQuestion:
    chapter_name: str
    english: str
    swedish: str

    def read_question(self) -> QuestionContent:
        return QuestionContent(
            question_text=(
                "Skriv engelsk Magic-term for detta svenska ord:\n"
                f"{self.swedish}\n"
                f"Kapitel: {self.chapter_name}"
            )
        )

    def answer_question(self, answer: str) -> QuestionResult:
        normalized = _normalize_answer(answer)
        if not normalized:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"Ratt svar: {self.english}",
            )

        if normalized == _normalize_answer(self.english):
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"Ratt svar: {self.english}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Ratt svar: {self.english}",
        )

    def reveal_answer(self) -> QuestionResult:
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Ratt svar: {self.english}",
        )


class MagicGlossaryPlugin(Plugin):
    def __init__(self, chapters: list[_ChapterData]):
        self._chapters = chapters
        self._chapter_cycles: list[list[_GlossaryEntry]] = [[] for _ in chapters]
        self._chapter_positions: list[int] = [0 for _ in chapters]
        self._last_chapter_index: int | None = None
        for idx in range(len(self._chapters)):
            self._reshuffle_chapter(idx)

    def _reshuffle_chapter(self, chapter_index: int) -> None:
        cycle = list(self._chapters[chapter_index].entries)
        random.shuffle(cycle)
        self._chapter_cycles[chapter_index] = cycle
        self._chapter_positions[chapter_index] = 0

    def _next_entry(self, chapter_index: int) -> _GlossaryEntry:
        if self._chapter_positions[chapter_index] >= len(self._chapter_cycles[chapter_index]):
            self._reshuffle_chapter(chapter_index)
        pos = self._chapter_positions[chapter_index]
        self._chapter_positions[chapter_index] = pos + 1
        return self._chapter_cycles[chapter_index][pos]

    def reset(self) -> None:
        if self._last_chapter_index is None:
            return
        self._reshuffle_chapter(self._last_chapter_index)

    def make_question(self, difficulty_or_chapter: int) -> Question:
        if not self._chapters:
            raise RuntimeError("Magic glossary plugin has no chapters.")

        chapter_index = max(0, min(int(difficulty_or_chapter), len(self._chapters) - 1))
        self._last_chapter_index = chapter_index
        chapter = self._chapters[chapter_index]
        entry = self._next_entry(chapter_index)
        return MagicGlossaryQuestion(
            chapter_name=chapter.name,
            english=entry.english,
            swedish=entry.swedish,
        )


class MagicGlossaryPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="magic_glossary",
            name="Magic Glossary",
            description="Lara dig engelska Magic-termer med svenska ledtradar.",
            mode=[
                Chapter(name=name, required_streak=len(_load_chapter_file(filename)))
                for name, filename in _CHAPTER_FILES
            ],
            icon=EmojiIcon("🃏"),
            required_streak=None,
            accepted_answer_buttons=[AnswerButton.ENTER]
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return MagicGlossaryPlugin(chapters=_load_chapters())


PLUGIN_FACTORY: PluginFactory = MagicGlossaryPluginFactory

