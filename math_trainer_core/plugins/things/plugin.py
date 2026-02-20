from __future__ import annotations

from pathlib import Path

from ..plugin_api import (
    Chapter,
    EmojiIcon,
    Plugin,
    PluginFactory,
    PluginInfo,
)
from ..picture_text_shared import (
    PictureTextChapter,
    PictureTextChapterCycle,
    PictureTextQuestion,
    load_picture_text_chapters,
    load_picture_text_entries,
)


_CHAPTER_FILES: list[tuple[str, str]] = [
    ("Planeter", "planets.json"),
]


def _plugin_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_chapter_file(filename: str):
    return load_picture_text_entries(_plugin_dir() / filename)


def _load_chapters() -> list[PictureTextChapter]:
    return load_picture_text_chapters(_plugin_dir(), _CHAPTER_FILES)


class ThingsPlugin(Plugin):
    def __init__(self, chapters: list[PictureTextChapter]):
        self._cycle = PictureTextChapterCycle(chapters)

    def reset(self) -> None:
        self._cycle.reset_last_chapter()

    def make_question(self, difficulty_or_chapter: int):
        chapter, entry = self._cycle.next_for_chapter(difficulty_or_chapter)
        return PictureTextQuestion(
            prompt=f"Vilken planet ar det pa bilden?\nKapitel: {chapter.name}",
            answer=entry.answer,
            picture_urls=list(entry.picture_urls),
        )


class ThingsPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="things",
            name="Things",
            description="Gissa vilken sak det ar pa bilden. Startkapitel: planeter.",
            mode=[
                Chapter(name=name, required_streak=len(_load_chapter_file(filename)))
                for name, filename in _CHAPTER_FILES
            ],
            icon=EmojiIcon("🪐"),
            required_streak=None,
        )

    @staticmethod
    def CreatePlugin() -> Plugin:
        return ThingsPlugin(chapters=_load_chapters())


PLUGIN_FACTORY: PluginFactory = ThingsPluginFactory
