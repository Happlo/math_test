from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

from ..api_types import (
    TrainingSelectScreen,
    TrainingGridScreen,
    TrainingGridView,
    Room,
    RoomProgress,
    Locked,
    Unlocked,
    GridMove,
    QuestionScreen,
    RoomGrid,
    TrainingId,
)
from ..plugins.plugin_api import Plugin, PluginInfo, Difficulty, Chapters, AnswerButton, Chapter
from .question_impl import start_question_session, QuestionImpl
from .user import save_user, StoredUserProfile


_DEFAULT_INFINITE_LEVELS = 25
_MAX_MASTERY_LEVEL = 10
_TIME_LIMITS_MS: list[Optional[int]] = [
    None,
    60000,
    30000,
    15000,
    10000,
    7000,
    5000,
    4000,
    3000,
    2000,
    1000,
    500,
]
_DEFAULT_REQUIRED_STREAK = 5
_DEFAULT_ANSWER_BUTTONS = [AnswerButton.SPACE, AnswerButton.ENTER]


def _level_count_for_mode(mode: Difficulty | Chapters) -> int:
    if isinstance(mode, list):
        return max(1, len(mode))
    max_level = max(0, int(mode.max_level))
    if max_level == 0:
        return _DEFAULT_INFINITE_LEVELS
    return max_level + 1


def _grid_dimensions(level_count: int) -> Tuple[int, int]:
    width = max(1, level_count)
    height = max(1, len(_TIME_LIMITS_MS))
    return width, height


def _format_time_limit(time_limit_ms: Optional[int]) -> str:
    if time_limit_ms is None:
        return "No timer"
    seconds = time_limit_ms / 1000.0
    if time_limit_ms % 1000 == 0:
        return f"{int(seconds)}s"
    return f"{seconds:.1f}s"


def _required_streak_for_level(
    mode: Difficulty | Chapters,
    level_index: int,
    plugin_required_streak: int | None,
) -> int:
    if isinstance(mode, list):
        if 0 <= level_index < len(mode):
            chapter = mode[level_index]
            if isinstance(chapter, Chapter) and chapter.required_streak is not None:
                return max(1, int(chapter.required_streak))
    else:
        if mode.required_streak is not None:
            return max(1, int(mode.required_streak))
    if plugin_required_streak is not None:
        return max(1, int(plugin_required_streak))
    return _DEFAULT_REQUIRED_STREAK


@dataclass(frozen=True)
class _GridConfig:
    title: str
    mode: Difficulty | Chapters
    level_count: int
    width: int
    height: int
    time_limits_ms: List[Optional[int]]


class TrainingGridImpl(TrainingGridScreen):
    def __init__(
        self,
        plugin: Plugin,
        info: PluginInfo,
        parent_select: TrainingSelectScreen,
        title: str | None = None,
        user_profile: StoredUserProfile | None = None,
        training_id: TrainingId | None = None,
    ):
        self._plugin = plugin
        self._info = info
        self._parent_select = parent_select
        self._profile = user_profile
        self._training_id = training_id

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
        self._current_x = 1
        self._current_y = 1
        origin = Room(difficulty=1, time_pressure=1)
        self._unlocked: set[Room] = {origin}
        self._mastery_levels: dict[Room, int] = {}

        initial_progress = None
        if self._profile is not None and self._training_id is not None:
            initial_progress = self._profile.items.get(self._training_id)
        if initial_progress:
            self._load_progress(initial_progress)

        self._view = TrainingGridView(
            title=self._config.title,
            grid={},
            current_x=self._current_x,
            current_y=self._current_y,
            hint="",
        )
        self._rebuild_view()
        self._sync_profile()

    def accepted_answer_buttons(self) -> List[AnswerButton]:
        buttons = self._info.accepted_answer_buttons
        if buttons is None:
            return list(_DEFAULT_ANSWER_BUTTONS)
        return list(buttons)

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
        next_room = Room(difficulty=nx, time_pressure=ny)
        if not self._is_valid_room(next_room):
            return self
        if not self._is_unlocked_or_completed(next_room):
            return self

        self._current_x = nx
        self._current_y = ny
        self._rebuild_view()
        return self

    def enter(self) -> QuestionScreen:
        level_index = self._difficulty_index(self._current_x)
        required_streak = _required_streak_for_level(
            mode=self._config.mode,
            level_index=level_index,
            plugin_required_streak=self._info.required_streak,
        )
        time_limit_ms = self._time_limit_for_row(self._current_y)
        coord = Room(difficulty=self._current_x, time_pressure=self._current_y)
        initial_highest = self._mastery_levels.get(coord, 0) * required_streak
        inner = start_question_session(
            plugin=self._plugin,
            level_index=level_index,
            streak_to_advance_mastery=required_streak,
            initial_highest_streak=initial_highest,
            time_limit_ms=time_limit_ms,
        )
        return _QuestionWrapper(inner=inner, grid=self, coord=coord)

    def escape(self) -> TrainingSelectScreen:
        return self._parent_select

    def record_mastery(self, coord: Room, mastery_level: int) -> None:
        if not self._is_valid_room(coord):
            return
        mastery_level = min(mastery_level, _MAX_MASTERY_LEVEL)
        prev = self._mastery_levels.get(coord, 0)
        if mastery_level <= prev:
            return
        self._mastery_levels[coord] = mastery_level
        if mastery_level > 0:
            self._unlock_adjacent(coord)
            self._backfill_mastery(coord, mastery_level)
        self._rebuild_view()
        self._sync_profile()

    # ------------------------------------------------------------------ helpers

    def _is_valid_room(self, room: Room) -> bool:
        if (
            room.difficulty < 1
            or room.time_pressure < 1
            or room.difficulty > self._config.width
            or room.time_pressure > self._config.height
        ):
            return False
        return room.difficulty <= self._config.level_count

    def _difficulty_index(self, x: int) -> int:
        return max(0, min(x - 1, self._config.level_count - 1))

    def _time_limit_for_row(self, y: int) -> Optional[int]:
        if self._config.time_limits_ms:
            y_index = max(0, y - 1)
            return self._config.time_limits_ms[min(y_index, len(self._config.time_limits_ms) - 1)]
        return _TIME_LIMITS_MS[-1]

    def _mastery_level(self, coord: Room) -> int:
        return self._mastery_levels.get(coord, 0)

    def _is_unlocked_or_completed(self, coord: Room) -> bool:
        return coord in self._unlocked or self._mastery_level(coord) > 0

    def _unlock_adjacent(self, coord: Room) -> None:
        x, y = coord.difficulty, coord.time_pressure
        for nx, ny in ((x + 1, y), (x, y + 1)):
            neighbor = Room(difficulty=nx, time_pressure=ny)
            if self._is_valid_room(neighbor) and neighbor not in self._unlocked:
                if self._mastery_level(neighbor) == 0:
                    self._unlocked.add(neighbor)

    def _backfill_mastery(self, coord: Room, mastery_level: int) -> None:
        for x in range(1, coord.difficulty + 1):
            for y in range(1, coord.time_pressure + 1):
                room = Room(difficulty=x, time_pressure=y)
                if not self._is_valid_room(room):
                    continue
                if room not in self._unlocked:
                    self._unlocked.add(room)
                prev = self._mastery_levels.get(room, 0)
                if mastery_level > prev:
                    self._mastery_levels[room] = mastery_level

    def _level_label(self, index: int) -> str:
        if isinstance(self._config.mode, list):
            chapters = self._config.mode
            if 0 <= index < len(chapters):
                return chapters[index].name
            return f"Chapter {index + 1}"
        return f"Level {index + 1}"

    def _build_hint(self) -> str:
        index = self._difficulty_index(self._current_x)
        label = self._level_label(index)
        time_limit_ms = self._time_limit_for_row(self._current_y)
        time_text = _format_time_limit(time_limit_ms)
        if isinstance(self._config.mode, list):
            header = f"Chapter {index + 1}/{self._config.level_count}: {label}"
        else:
            if isinstance(self._config.mode, Difficulty) and self._config.mode.max_level == 0:
                header = f"{label}"
            else:
                header = f"{label} ({index + 1}/{self._config.level_count})"
        return f"{header} — Time limit: {time_text}. Arrows to move, Enter to start, Esc to go back"

    def _rebuild_view(self) -> None:
        grid: dict[Room, RoomProgress] = {}
        locked_neighbors: set[Room] = set()
        for room in self._unlocked:
            x, y = room.difficulty, room.time_pressure
            for nx, ny in ((x + 1, y), (x, y + 1)):
                neighbor = Room(difficulty=nx, time_pressure=ny)
                if self._is_valid_room(neighbor) and neighbor not in self._unlocked:
                    locked_neighbors.add(neighbor)
        for y in range(1, self._config.height + 1):
            for x in range(1, self._config.width + 1):
                if x > self._config.level_count:
                    continue
                room = Room(difficulty=x, time_pressure=y)
                mastery = self._mastery_level(room)
                if (
                    room in self._unlocked
                    or mastery > 0
                    or (x == self._current_x and y == self._current_y)
                ):
                    score = room.difficulty * room.time_pressure * mastery
                    grid[room] = Unlocked(mastery_level=mastery, score=score)
                elif room in locked_neighbors:
                    grid[room] = Locked()

        self._view.grid = grid
        self._view.current_x = self._current_x
        self._view.current_y = self._current_y
        self._view.hint = self._build_hint()

    def _load_progress(self, progress: RoomGrid) -> None:
        self._unlocked.clear()
        self._mastery_levels.clear()
        for room, status in progress.items():
            if not self._is_valid_room(room):
                continue
            if isinstance(status, Unlocked):
                self._unlocked.add(room)
                if status.mastery_level > 0:
                    self._mastery_levels[room] = status.mastery_level
        self._unlocked.add(Room(difficulty=1, time_pressure=1))
        for room in list(self._mastery_levels.keys()):
            self._unlock_adjacent(room)

    def _sync_profile(self) -> None:
        if self._profile is None or self._training_id is None:
            return
        snapshot: RoomGrid = {}
        rooms = set(self._unlocked)
        rooms.update({room for room, mastery in self._mastery_levels.items() if mastery > 0})
        for room in rooms:
            if not self._is_valid_room(room):
                continue
            mastery = self._mastery_levels.get(room, 0)
            score = room.difficulty * room.time_pressure * mastery
            snapshot[room] = Unlocked(mastery_level=mastery, score=score)
        self._profile.items[self._training_id] = snapshot
        save_user(self._profile)


class _QuestionWrapper(QuestionScreen):
    def __init__(self, inner, grid: TrainingGridImpl, coord: Room):
        self._inner: QuestionImpl = inner
        self._grid = grid
        self._coord: Room = coord

    @property
    def view(self):
        return self._inner.view

    @property
    def possible_events(self):
        return self._inner.possible_events

    @property
    def accepted_answer_buttons(self):
        return self._grid.accepted_answer_buttons()

    def handle(self, event):
        self._inner = self._inner.handle(event)
        return self

    def escape(self) -> TrainingGridScreen:
        self._grid.record_mastery(self._coord, self._inner.view.mastery_level)
        return self._grid
