from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Protocol, Union, List


# ---------------------------------------------------------------------------
# Shared progress / timing
# ---------------------------------------------------------------------------

class Progress(Enum):
    PENDING = auto()
    CORRECT = auto()
    WRONG = auto()
    TIMED_OUT = auto()


@dataclass
class QuestionTime:
    time_per_question_ms: int
    time_left_ms: int


# ---------------------------------------------------------------------------
# Question screen
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RefreshEvent:
    """Timer tick – core should update time / timeout."""
    pass


@dataclass(frozen=True)
class AnswerEvent:
    """User submitted an answer."""
    text: str


@dataclass(frozen=True)
class NextEvent:
    """User wants to proceed after feedback."""
    pass


QuestionEvent = Union[RefreshEvent, AnswerEvent, NextEvent]


@dataclass
class QuestionView:
    question_text: str
    feedback_text: str
    current_streak: int
    highest_streak: int
    streak_to_advance_mastery: int
    mastery_level: int
    score: int
    progress: List[Progress]
    question_idx: int
    input_enabled: bool
    time: Optional[QuestionTime]


class QuestionScreen(Protocol):
    @property
    def view(self) -> QuestionView:
        ...

    @property
    def possible_events(self) -> List[type[QuestionEvent]]:
        ...

    def handle(self, event: QuestionEvent) -> QuestionScreen:
        """
        Always stays within the question flow (answer / refresh / next).
        """
        ...

    def escape(self) -> TrainingGridScreen:
        """
        Always possible: leave questions and go back to training grid.
        """
        ...


# ---------------------------------------------------------------------------
# Training grid screen
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Unlocked:
    mastery_level: int


@dataclass(frozen=True)
class Locked:
    pass


CellProgress = Union[Locked, Unlocked]


@dataclass
class TrainingGridView:
    title: str
    # 2D grid: grid[y][x]
    grid: dict[tuple[int, int], CellProgress]
    current_x: int
    current_y: int
    hint: str

class GridMove(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()


class TrainingGridScreen(Protocol):
    @property
    def view(self) -> TrainingGridView:
        ...

    def move(self, event: GridMove) -> TrainingGridScreen:
        """
        Move around in the grid (left/right/up/down), but stay in grid mode.
        """
        ...

    def enter(self) -> QuestionScreen:
        """
        Always possible: start questions for the currently selected cell.
        """
        ...

    def escape(self) -> TrainingSelectScreen:
        """
        Always possible: go back to training selection.
        """
        ...


# ---------------------------------------------------------------------------
# Training select screen (ladder)
# ---------------------------------------------------------------------------

class SelectMove(Enum):
    UP = auto()
    DOWN = auto()

@dataclass
class TrainingItemView:
    training_id: str
    label: str
    description: str
    icon_text: str  # GUI maps this to emoji or pixmap


@dataclass
class TrainingSelectView:
    title: str
    items: List[TrainingItemView]
    selected_index: int


class TrainingSelectScreen(Protocol):
    @property
    def view(self) -> TrainingSelectView:
        ...

    def move(self, event: SelectMove) -> TrainingSelectScreen:
        """
        Move up/down in the ladder, but stay in training-select.
        """
        ...

    def enter(self) -> TrainingGridScreen:
        """
        Always possible: enter the grid for the selected training.
        """
        ...
