from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from ..api_types import (
    TrainingSelectScreen,
    TrainingGridScreen,
    TrainingGridView,
    CellProgress,
    GridMove,
    QuestionScreen,
)
from ..plugin_api import Plugin, PluginInfo, Difficulty, Chapters
from .question_impl import start_question_session


_DEFAULT_INFINITE_LEVELS = 25
_TIME_LIMITS_MS = [20000, 15000, 10000, 7000, 5000]
_DEFAULT_REQUIRED_STREAK = 5


def _level_count_for_mode(mode: Difficulty | Chapters) -> int:
    if isinstance(mode, Chapters):
        return max(1, len(mode.chapters))
    max_level = max(0, int(mode.max_level))
    if max_level == 0:
        return _DEFAULT_INFINITE_LEVELS
    return max_level + 1


def _grid_dimensions(level_count: int) -> Tuple[int, int]:
    width = max(1, level_count)
    height = max(1, len(_TIME_LIMITS_MS))
    return width, height


@dataclass(frozen=True)
class _GridConfig:
    title: str
    mode: Difficulty | Chapters
    level_count: int
    width: int
    height: int
    time_limits_ms: List[int]


class TrainingGridImpl(TrainingGridScreen):
    def __init__(
        self,
        plugin: Plugin,
        info: PluginInfo,
        parent_select: TrainingSelectScreen,
        title: str | None = None,
    ):
        self._plugin = plugin
        self._info = info
        self._parent_select = parent_select

        level_count = _level_count_for_mode(info.mode)
        width, height = _grid_dimensions(level_count)
        self._config = _GridConfig(
            title=title or info.name,
            mode=info.mode,
            level_count=level_count,
            width=width,
            height=height,
            time_limits_ms=list(_TIME_LIMITS_MS),
        )
        self._required_streak = max(1, info.required_streak or _DEFAULT_REQUIRED_STREAK)

        self._current_x = 0
        self._current_y = 0
        self._unlocked: set[tuple[int, int]] = {(0, 0)}
        self._max_streak: dict[tuple[int, int], int] = {}

        self._view = TrainingGridView(
            title=self._config.title,
            grid=[],
            current_x=self._current_x,
            current_y=self._current_y,
            hint="",
        )
        self._rebuild_view()

    @property
    def view(self) -> TrainingGridView:
        return self._view

    def move(self, event: GridMove) -> TrainingGridScreen:
        dx, dy = 0, 0
        if event == GridMove.LEFT:
            dx = -1
        elif event == GridMove.RIGHT:
            dx = 1
        elif event == GridMove.UP:
            dy = -1
        elif event == GridMove.DOWN:
            dy = 1

        nx = self._current_x + dx
        ny = self._current_y + dy
        if not self._is_valid_coord(nx, ny):
            return self
        if not self._is_unlocked_or_completed((nx, ny)):
            return self

        self._current_x = nx
        self._current_y = ny
        self._rebuild_view()
        return self

    def enter(self) -> QuestionScreen:
        level_index = self._difficulty_index(self._current_x)
        time_limit_ms = self._time_limit_for_row(self._current_y)
        coord = (self._current_x, self._current_y)
        initial_highest = self._max_streak.get(coord, 0)
        inner = start_question_session(
            plugin=self._plugin,
            level_index=level_index,
            parent_grid=self,
            streak_to_advance_mastery=self._required_streak,
            initial_highest_streak=initial_highest,
            time_limit_ms=time_limit_ms,
        )
        return _QuestionWrapper(inner=inner, grid=self, coord=coord)

    def escape(self) -> TrainingSelectScreen:
        return self._parent_select

    def record_streak(self, coord: tuple[int, int], streak: int) -> None:
        if not self._is_valid_coord(coord[0], coord[1]):
            return
        prev = self._max_streak.get(coord, 0)
        if streak <= prev:
            return
        self._max_streak[coord] = streak
        if self._mastery_level(coord) > 0:
            self._unlock_adjacent(coord)
        self._rebuild_view()

    # ------------------------------------------------------------------ helpers

    def _is_valid_coord(self, x: int, y: int) -> bool:
        if x < 0 or y < 0 or x >= self._config.width or y >= self._config.height:
            return False
        return x < self._config.level_count

    def _difficulty_index(self, x: int) -> int:
        return max(0, min(x, self._config.level_count - 1))

    def _time_limit_for_row(self, y: int) -> int:
        if self._config.time_limits_ms:
            return self._config.time_limits_ms[min(y, len(self._config.time_limits_ms) - 1)]
        return _TIME_LIMITS_MS[-1]

    def _mastery_level(self, coord: tuple[int, int]) -> int:
        return self._max_streak.get(coord, 0) // self._required_streak

    def _is_unlocked_or_completed(self, coord: tuple[int, int]) -> bool:
        return coord in self._unlocked or self._mastery_level(coord) > 0

    def _unlock_adjacent(self, coord: tuple[int, int]) -> None:
        x, y = coord
        for nx, ny in ((x + 1, y), (x, y + 1)):
            if self._is_valid_coord(nx, ny) and (nx, ny) not in self._unlocked:
                if self._mastery_level((nx, ny)) == 0:
                    self._unlocked.add((nx, ny))

    def _level_label(self, index: int) -> str:
        if isinstance(self._config.mode, Chapters):
            chapters = self._config.mode.chapters
            if 0 <= index < len(chapters):
                return chapters[index]
            return f"Chapter {index + 1}"
        return f"Level {index + 1}"

    def _build_hint(self) -> str:
        index = self._difficulty_index(self._current_x)
        label = self._level_label(index)
        time_limit_ms = self._time_limit_for_row(self._current_y)
        time_text = f"{time_limit_ms / 1000:.1f}s"
        if isinstance(self._config.mode, Chapters):
            header = f"Chapter {index + 1}/{self._config.level_count}: {label}"
        else:
            if isinstance(self._config.mode, Difficulty) and self._config.mode.max_level == 0:
                header = f"{label}"
            else:
                header = f"{label} ({index + 1}/{self._config.level_count})"
        return f"{header} — Time limit: {time_text}. Arrows to move, Enter to start, Esc to go back"

    def _rebuild_view(self) -> None:
        grid: List[List[CellProgress]] = []
        for y in range(self._config.height):
            row: List[CellProgress] = []
            for x in range(self._config.width):
                if x >= self._config.level_count:
                    row.append(CellProgress.LOCKED)
                    continue
                coord = (x, y)
                if x == self._current_x and y == self._current_y:
                    row.append(CellProgress.CURRENT)
                elif self._mastery_level(coord) > 0:
                    row.append(CellProgress.COMPLETED)
                elif coord in self._unlocked:
                    row.append(CellProgress.AVAILABLE)
                else:
                    row.append(CellProgress.LOCKED)
            grid.append(row)

        self._view.grid = grid
        self._view.current_x = self._current_x
        self._view.current_y = self._current_y
        self._view.hint = self._build_hint()


class _QuestionWrapper(QuestionScreen):
    def __init__(self, inner: QuestionScreen, grid: TrainingGridImpl, coord: tuple[int, int]):
        self._inner = inner
        self._grid = grid
        self._coord = coord

    @property
    def view(self):
        return self._inner.view

    @property
    def possible_events(self):
        return self._inner.possible_events

    def handle(self, event):
        self._inner = self._inner.handle(event)
        self._grid.record_streak(self._coord, self._inner.view.highest_streak)
        return self

    def escape(self) -> TrainingGridScreen:
        return self._grid
