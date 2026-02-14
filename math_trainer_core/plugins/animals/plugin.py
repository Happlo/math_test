from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random

from math_trainer_core.api_types import PictureWithText
from math_trainer_core.core.picture_helper import PictureRef, download_picture

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


_CHAPTER_FILES: list[tuple[str, str]] = [
    ("Fisk", "fish.json"),
]


@dataclass(frozen=True)
class _AnimalEntry:
    answer: str
    picture_urls: list[str]


@dataclass(frozen=True)
class _ChapterData:
    name: str
    animals: list[_AnimalEntry]


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parent


def _normalize_answer(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _load_chapter_file(filename: str) -> list[_AnimalEntry]:
    path = _plugin_dir() / filename
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid chapter file format: {path}")

    animals: list[_AnimalEntry] = []
    for answer, urls in raw.items():
        if not isinstance(answer, str) or not answer.strip():
            continue
        if not isinstance(urls, list):
            continue
        picture_urls = [u.strip() for u in urls if isinstance(u, str) and u.strip()]
        if not picture_urls:
            continue
        animals.append(_AnimalEntry(answer=answer.strip(), picture_urls=picture_urls))

    if not animals:
        raise ValueError(f"Chapter has no usable entries: {path}")
    return animals


def _load_chapters() -> list[_ChapterData]:
    chapters: list[_ChapterData] = []
    for chapter_name, filename in _CHAPTER_FILES:
        chapters.append(
            _ChapterData(
                name=chapter_name,
                animals=_load_chapter_file(filename),
            )
        )
    if not chapters:
        raise ValueError("Animals plugin has no chapter files configured.")
    return chapters


@dataclass(frozen=True)
class AnimalsQuestion:
    prompt: str
    answer: str
    picture_urls: list[str]

    def read_question(self) -> QuestionContent:
        picture_paths: list[PictureWithText] = []
        for picture_url in random.sample(self.picture_urls, k=len(self.picture_urls)):
            try:
                picture_path = download_picture(PictureRef(url=picture_url))
                picture_paths = [PictureWithText(picture=picture_path, optional_text=None)]
                break
            except Exception:
                continue

        return QuestionContent(
            question_text=self.prompt,
            optional_pictures=picture_paths,
        )

    def answer_question(self, answer: str) -> QuestionResult:
        normalized = _normalize_answer(answer)
        if not normalized:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=f"Ratt svar: {self.answer}",
            )

        if normalized == _normalize_answer(self.answer):
            return QuestionResult(
                result=AnswerResult.CORRECT,
                display_answer_text=f"Ratt svar: {self.answer}",
            )

        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Ratt svar: {self.answer}",
        )

    def reveal_answer(self) -> QuestionResult:
        return QuestionResult(
            result=AnswerResult.WRONG,
            display_answer_text=f"Ratt svar: {self.answer}",
        )


class AnimalsPlugin(Plugin):
    def __init__(self, chapters: list[_ChapterData]):
        self._chapters = chapters
        self._chapter_cycles: list[list[_AnimalEntry]] = [[] for _ in chapters]
        self._chapter_positions: list[int] = [0 for _ in chapters]
        self._last_chapter_index: int | None = None
        for idx in range(len(self._chapters)):
            self._reshuffle_chapter(idx)

    def _reshuffle_chapter(self, chapter_index: int) -> None:
        cycle = list(self._chapters[chapter_index].animals)
        random.shuffle(cycle)
        self._chapter_cycles[chapter_index] = cycle
        self._chapter_positions[chapter_index] = 0

    def _next_animal(self, chapter_index: int) -> _AnimalEntry:
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
            raise RuntimeError("Animals plugin has no chapters.")

        chapter_index = max(0, min(int(difficulty_or_chapter), len(self._chapters) - 1))
        self._last_chapter_index = chapter_index
        chapter = self._chapters[chapter_index]
        animal = self._next_animal(chapter_index)

        return AnimalsQuestion(
            prompt=f"Vilket djur ar det pa bilden?\nKapitel: {chapter.name}",
            answer=animal.answer,
            picture_urls=list(animal.picture_urls),
        )


class AnimalsPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="animals",
            name="Animals",
            description="Gissa djuret pa bilden. Kapitel styr vilken JSON-fil som anvands.",
            mode=[
                Chapter(name=name, required_streak=len(_load_chapter_file(filename)))
                for name, filename in _CHAPTER_FILES
            ],
            icon=EmojiIcon("🐟"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return AnimalsPlugin(chapters=_load_chapters())


PLUGIN_FACTORY: PluginFactory = AnimalsPluginFactory
