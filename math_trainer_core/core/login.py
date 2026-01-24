from __future__ import annotations

from ..api_types import LoginScreen, LoginView, AuthResult, UserProfile, TrainingSelectScreen
from .training_select_impl import TrainingSelectImpl
from .user import create_user, login, load_all_users, total_score


class LoginImpl(LoginScreen):
    def __init__(self) -> None:
        self._view = LoginView(highscore=_load_highscores())

    @property
    def view(self) -> LoginView:
        return self._view

    def Start(self, user_profile: UserProfile | None = None) -> TrainingSelectScreen:
        return TrainingSelectImpl.start(user_profile)

    def Login(self, name: str) -> AuthResult:
        return login(name)

    def CreateUser(self, name: str) -> AuthResult:
        return create_user(name)


def _load_highscores() -> dict[str, int]:
    highscores: dict[str, int] = {}
    for profile in load_all_users():
        highscores[profile.name] = total_score(profile)
    return highscores
