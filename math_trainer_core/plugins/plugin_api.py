from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, List, Union
from pathlib import Path

from ..api_types import QuestionContent

@dataclass(frozen=True)
class Chapter:
    name: str
    # Optional override for how many correct answers in a row are required
    # to "advance" mastery chapter. If None, core uses its own default.
    required_streak: int | None = None

Chapters = List[Chapter]
@dataclass(frozen=True)
class Difficulty:
    max_level: int  # 0 for infinite
    # Optional override for how many correct answers in a row are required
    # to "advance" mastery chapter. If None, core uses its own default.
    required_streak: int | None = None

Mode = Union[Chapters, Difficulty]

@dataclass(frozen=True)
class EmojiIcon:
    """
    Icon rendered as text/emoji, e.g. '🧠' or '➕'.
    """
    symbol: str


@dataclass(frozen=True)
class FileIcon:
    """
    Icon loaded from disk, e.g. a PNG or SVG file.
    """
    path: Path


PluginIcon = Union[EmojiIcon, FileIcon]

class AnswerButton(Enum):
    SPACE = auto()
    ENTER = auto()


@dataclass(frozen=True)
class PluginInfo:
    id: str
    name: str
    description: str
    mode: Mode
    icon: PluginIcon
    # Optional override for how many correct answers in a row are required
    # to "clear" a level/session. If None, core uses its own default.
    required_streak: int | None = None
    # Space and enter are used by default as accepted answer buttons.
    # This can be overridden by the plugin if needed.
    accepted_answer_buttons: List[AnswerButton] | None = None

class AnswerResult(Enum):
    CORRECT = auto()
    WRONG = auto()
    INVALID_INPUT = auto()

@dataclass(frozen=True)
class QuestionResult:
    result: AnswerResult
    display_answer_text: str


class Question(Protocol):
    def read_question(self) -> QuestionContent: ...
    def answer_question(self, answer: str) -> QuestionResult: ...
    def reveal_answer(self) -> QuestionResult: ...

class Plugin(Protocol):
    def make_question(self, difficulty_or_chapter: int) -> Question: ...

class PluginFactory(Protocol):
    @staticmethod
    def PluginInfo() -> PluginInfo: ...

    @staticmethod
    def CreatePlugin() -> Plugin: ...
