from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random

from math_trainer_core.api_types import PictureWithText
from math_trainer_core.core.picture_helper import PictureRef, download_picture
from .plugin_api import AnswerResult, QuestionContent, QuestionResult


@dataclass(frozen=True)
class PictureTextEntry:
    answer: str
    picture_urls: list[str]


@dataclass(frozen=True)
class PictureTextChapter:
    name: str
    entries: list[PictureTextEntry]


def normalize_text_answer(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def load_picture_text_entries(path: Path) -> list[PictureTextEntry]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid chapter file format: {path}")

    entries: list[PictureTextEntry] = []
    for answer, urls in raw.items():
        if not isinstance(answer, str) or not answer.strip():
            continue
        if not isinstance(urls, list):
            continue
        picture_urls = [u.strip() for u in urls if isinstance(u, str) and u.strip()]
        if not picture_urls:
            continue
        entries.append(PictureTextEntry(answer=answer.strip(), picture_urls=picture_urls))

    if not entries:
        raise ValueError(f"Chapter has no usable entries: {path}")
    return entries


def load_picture_text_chapters(
    plugin_dir: Path,
    chapter_files: list[tuple[str, str]],
) -> list[PictureTextChapter]:
    chapters: list[PictureTextChapter] = []
    for chapter_name, filename in chapter_files:
        chapters.append(
            PictureTextChapter(
                name=chapter_name,
                entries=load_picture_text_entries(plugin_dir / filename),
            )
        )

    if not chapters:
        raise ValueError("Picture-text plugin has no chapter files configured.")
    return chapters


@dataclass(frozen=True)
class PictureTextQuestion:
    prompt: str
    answer: str
    picture_urls: list[str]
    answer_label: str = "Ratt svar"

    def _answer_text(self) -> str:
        return f"{self.answer_label}: {self.answer}"

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
        normalized = normalize_text_answer(answer)
        if not normalized:
            return QuestionResult(
                result=AnswerResult.INVALID_INPUT,
                display_answer_text=self._answer_text(),
            )

        if normalized == normalize_text_answer(self.answer):
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


class PictureTextChapterCycle:
    def __init__(self, chapters: list[PictureTextChapter]):
        self._chapters = chapters
        self._chapter_cycles: list[list[PictureTextEntry]] = [[] for _ in chapters]
        self._chapter_positions: list[int] = [0 for _ in chapters]
        self._last_chapter_index: int | None = None
        for idx in range(len(self._chapters)):
            self._reshuffle_chapter(idx)

    def _reshuffle_chapter(self, chapter_index: int) -> None:
        cycle = list(self._chapters[chapter_index].entries)
        random.shuffle(cycle)
        self._chapter_cycles[chapter_index] = cycle
        self._chapter_positions[chapter_index] = 0

    def reset_last_chapter(self) -> None:
        if self._last_chapter_index is None:
            return
        self._reshuffle_chapter(self._last_chapter_index)

    def next_for_chapter(self, requested_index: int) -> tuple[PictureTextChapter, PictureTextEntry]:
        if not self._chapters:
            raise RuntimeError("Picture-text plugin has no chapters.")

        chapter_index = max(0, min(int(requested_index), len(self._chapters) - 1))
        self._last_chapter_index = chapter_index
        if self._chapter_positions[chapter_index] >= len(self._chapter_cycles[chapter_index]):
            self._reshuffle_chapter(chapter_index)

        pos = self._chapter_positions[chapter_index]
        self._chapter_positions[chapter_index] = pos + 1
        return self._chapters[chapter_index], self._chapter_cycles[chapter_index][pos]
