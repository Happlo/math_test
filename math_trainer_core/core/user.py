from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any

from ..api_types import Locked, Room, RoomGrid, RoomProgress, TrainingId, Unlocked, AuthError, AuthResult, UserProfile


_USERS_DIR = Path("users")

@dataclass
class StoredUserProfile:
    name: str
    items: dict[TrainingId, RoomGrid]


def save_user(profile: StoredUserProfile) -> None:
    _USERS_DIR.mkdir(parents=True, exist_ok=True)
    path = _USERS_DIR / f"{_sanitize_name(profile.name)}.json"
    payload = _profile_to_dict(profile)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_user(name: str) -> StoredUserProfile | None:
    path = _USERS_DIR / f"{_sanitize_name(name)}.json"
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _profile_from_dict(raw, fallback_name=name)


def _profile_to_dict(profile: StoredUserProfile) -> dict[str, Any]:
    items: dict[str, list[dict[str, Any]]] = {}
    for training_id, grid in profile.items.items():
        items[training_id] = [_entry_to_dict(room, status) for room, status in grid.items()]
    return {"name": profile.name, "items": items}


def _profile_from_dict(raw: dict[str, Any], fallback_name: str) -> StoredUserProfile:
    name = raw.get("name") or fallback_name
    items: dict[TrainingId, RoomGrid] = {}
    raw_items = raw.get("items", {})
    if isinstance(raw_items, dict):
        for training_id, entries in raw_items.items():
            grid: RoomGrid = {}
            if isinstance(entries, list):
                for entry in entries:
                    room, status = _entry_from_dict(entry)
                    if room is not None and status is not None:
                        grid[room] = status
            items[training_id] = grid
    return StoredUserProfile(name=name, items=items)


def _entry_to_dict(room: Room, status: RoomProgress) -> dict[str, Any]:
    payload = {
        "difficulty": room.difficulty,
        "time_pressure": room.time_pressure,
    }
    if isinstance(status, Unlocked):
        payload.update(
            {
                "state": "unlocked",
                "mastery_level": status.mastery_level,
                "score": status.score,
            }
        )
    else:
        payload["state"] = "locked"
    return payload


def _entry_from_dict(entry: dict[str, Any]) -> tuple[Room | None, RoomProgress | None]:
    if not isinstance(entry, dict):
        return None, None
    try:
        difficulty = int(entry.get("difficulty"))
        time_pressure = int(entry.get("time_pressure"))
    except (TypeError, ValueError):
        return None, None
    room = Room(difficulty=difficulty, time_pressure=time_pressure)
    state = entry.get("state")
    if state == "locked":
        return room, Locked()
    if state == "unlocked":
        mastery_level = _safe_int(entry.get("mastery_level"), default=0)
        score = _safe_int(entry.get("score"), default=0)
        return room, Unlocked(mastery_level=mastery_level, score=score)
    return None, None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _sanitize_name(name: str) -> str:
    cleaned = "".join(ch for ch in name.strip() if ch.isalnum() or ch in {"-", "_"})
    return cleaned or "player"


def normalize_name(name: str) -> str:
    return _sanitize_name(name)


def login(name: str) -> AuthResult:
    validated_name, error = _validate_name(name)
    if error is not None:
        return error
    stored = load_user(validated_name)
    if stored is None:
        return AuthError(message=f"User '{validated_name}' not found.")
    return UserProfile(name=stored.name)


def create_user(name: str) -> AuthResult:
    validated_name, error = _validate_name(name)
    if error is not None:
        return error
    if load_user(validated_name) is not None:
        return AuthError(message="User already exists.")
    stored = StoredUserProfile(name=validated_name, items={})
    save_user(stored)
    return UserProfile(name=validated_name)


def _validate_name(name: str) -> tuple[str, AuthError | None]:
    stripped = name.strip()
    if not stripped:
        return "", AuthError(message="Name cannot be empty.")
    normalized = normalize_name(stripped)
    if normalized != stripped:
        return "", AuthError(message="Name may contain only letters, numbers, '-' or '_'.")
    return stripped, None
