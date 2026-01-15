from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set, Tuple

Coord = tuple[int, int]


@dataclass
class LevelState:
    unlocked: Set[Coord] = field(default_factory=set)
    completed: Set[Coord] = field(default_factory=set)
    max_streak: Dict[Coord, int] = field(default_factory=dict)
    current: Coord = (0, 0)


def create_initial_levels() -> LevelState:
    state = LevelState()
    state.unlocked.add((0, 0))
    state.current = (0, 0)
    return state


def can_move_to(state: LevelState, coord: Coord) -> bool:
    # Man får gå till upplåsta eller klara nivåer
    return coord in state.unlocked or coord in state.completed


def set_current(state: LevelState, coord: Coord) -> None:
    if can_move_to(state, coord):
        state.current = coord


def unlock_after_win(state: LevelState, coord: Coord) -> None:
    x, y = coord
    # Lås upp (x+1,y) och (x,y+1)
    for nx, ny in ((x + 1, y), (x, y + 1)):
        if (nx, ny) not in state.unlocked and (nx, ny) not in state.completed:
            state.unlocked.add((nx, ny))
